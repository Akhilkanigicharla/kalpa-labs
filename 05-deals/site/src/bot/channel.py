#!/usr/bin/env python3
"""Telugu deals channel poster (b5, roadmap A58). Python standard library only.

Reads deals.json (filled by the team by hand, never scraped) and tips.json,
picks 3-5 deals a day into fixed IST slots, writes the Telugu post from a
template and posts it to the Telegram channel. Reuses post.py's Disclosure
Gate (ASCI #ad in the first 2 lines, price "as of" + "may change", no loan /
insurance / MF / broker words or links).

Added here:
  * RBI credit-card rules (PLAN.md §3b): EarnKaro/BankKaro links only, joining
    fee + annual fee + eligibility + issuer terms link + disclaimer on every
    card post, "free" only for lifetime-free cards, max 1 card post a day.
  * "No-cost EMI" wording is refused everywhere.
  * UTM tags on links (short links are left alone so redirects keep working).
  * Duplicate guard: state.json keeps posted ids/URLs; an id never repeats, a
    URL not within 30 days.
  * Dead-link guard: HEAD (then GET) with a timeout; a 404/410/unreachable link
    is skipped and the next deal takes the slot.
  * Weekly money tip (generic education, not advice) on Sundays.

Live posting needs ALL of: --live, the TELEGRAM_BOT_TOKEN and
TELEGRAM_CHAT_ID (or TELEGRAM_CHANNEL_ID) secrets, and DEALS_LIVE=go (Akhil's
"go", CLAUDE.md rule 9). Anything less is a dry run that only prints.

Usage:
  python3 channel.py --day 2026-10-25        # print a whole day's posts (dry run)
  python3 channel.py                          # dry run of what is due right now
  python3 channel.py --live                   # post what is due (needs the above)
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta
from pathlib import Path

import post

HERE = Path(__file__).resolve().parent
IST = post.IST
SLOTS = ["09:00", "12:30", "17:30", "20:00", "21:30"]  # IST; the workflow cron matches these
TIP_SLOT = "10:30"  # IST, Sundays only
GRACE = timedelta(hours=2)  # a slot missed by more than this is not posted late
MIN_PER_DAY = 3
MAX_CARDS_PER_DAY = 1
REPOST_AFTER = timedelta(days=30)
SECRET_NAMES = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_CHANNEL_ID"]
KINDS = {"product", "credit_card"}

# Card offers only through the issuer's affiliate channel (PLAN.md §3b).
CARD_HOSTS = ["earnkaro.com", "ekaro.in", "bankkaro.com"]
# Redirecting short links: adding query strings can break them, so no UTM.
SHORTLINK_HOSTS = ["ekaro.in", "amzn.to", "fkrt.it", "fktr.in", "bit.ly"]
UTM_SOURCE, UTM_MEDIUM = "telegram", "channel"
USER_AGENT = "KalpaDealsLinkCheck/1.0 (dead-link check before posting)"

CARD_DISCLAIMER = ("కార్డ్ ఆమోదం బ్యాంకు నిర్ణయం. బిల్లు పూర్తిగా కట్టకపోతే వడ్డీ, ఛార్జీలు పడతాయి. / "
                   "Approval is the bank's decision; interest and charges apply if the bill is not paid in full.")
TIP_HEAD = "వారపు డబ్బు చిట్కా / Weekly money tip"
TIP_FOOT = "సాధారణ సమాచారం మాత్రమే, ఆర్థిక సలహా కాదు / General information only, not financial advice."
FREE_WORDS = re.compile(r"\bfree\b|ఫ్రీ|ఉచిత", re.IGNORECASE)
NO_COST = re.compile(r"no[\s-]*cost|నో\s*కాస్ట్", re.IGNORECASE)


# ---------- files ----------

def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_deals(deals: list) -> None:
    """File-level errors stop the run. Field problems refuse only that deal (at the gate)."""
    if not isinstance(deals, list):
        raise post.GateError("deals.json needs a list under \"deals\"")
    seen = set()
    for d in deals:
        if not isinstance(d, dict) or not str(d.get("id", "")).strip():
            raise post.GateError(f"every deal needs an id: {d!r}")
        if d.get("kind") not in KINDS:
            raise post.GateError(f"{d['id']}: kind must be one of {sorted(KINDS)}")
        if d["id"] in seen:
            raise post.GateError(f"duplicate deal id {d['id']}")
        seen.add(d["id"])


def new_state() -> dict:
    return {"posted": [], "dead": [], "tips": []}


def load_state(path: Path) -> dict:
    if not path.exists():
        return new_state()
    state = new_state()
    state.update(load_json(path))
    return state


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------- links ----------

def _host(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def _on(host: str, hosts: list[str]) -> bool:
    return any(host == h or host.endswith("." + h) for h in hosts)


def normalise(url: str) -> str:
    """Same deal, same key: lower-case host, no utm_*, no fragment, no trailing slash."""
    p = urllib.parse.urlsplit(url.strip())
    query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not k.startswith("utm_")]
    path = p.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), path, urllib.parse.urlencode(query), ""))


def add_utm(url: str, deal_id: str, day: date) -> str:
    if _on(_host(url), SHORTLINK_HOSTS):
        return url
    p = urllib.parse.urlsplit(url)
    have = {k for k, _ in urllib.parse.parse_qsl(p.query, keep_blank_values=True)}
    tags = {"utm_source": UTM_SOURCE, "utm_medium": UTM_MEDIUM,
            "utm_campaign": f"deals-{day:%Y%m%d}", "utm_content": deal_id}
    extra = urllib.parse.urlencode({k: v for k, v in tags.items() if k not in have})
    query = "&".join(q for q in (p.query, extra) if q)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, query, p.fragment))


def link_status(url: str, timeout: float = 10, opener=urllib.request.urlopen) -> str:
    """'ok', 'dead' (404/410/unreachable) or 'unknown' (site blocks checks; still posted)."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with opener(req, timeout=timeout):
                return "ok"
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return "dead"
            if method == "HEAD":
                continue
            return "unknown"
        except (urllib.error.URLError, TimeoutError, OSError):
            return "dead"
    return "unknown"


# ---------- messages and gates ----------

def _money(value, field: str, deal_id: str) -> int:
    try:
        n = int(str(value).replace(",", "").lstrip("₹").strip())
    except ValueError:
        raise post.GateError(f"{deal_id}: {field} must be a whole rupee number") from None
    if n < 0:
        raise post.GateError(f"{deal_id}: {field} cannot be negative")
    return n


def _common_checks(deal_id: str, message: str) -> None:
    low = message.lower()
    for word in post.BANNED_WORDS:
        if word in low:
            raise post.GateError(f"{deal_id}: '{word}' is not allowed (no ARN/RBI/IRDAI status)")
    for url in re.findall(r"https?://\S+", message):
        if _on(_host(url), post.BANNED_HOSTS):
            raise post.GateError(f"{deal_id}: links to {_host(url)} are not allowed")
    if NO_COST.search(message):
        raise post.GateError(f"{deal_id}: do not write 'no-cost EMI' (RBI: interest-bearing EMI is not no-cost)")


def build(d: dict, now: datetime) -> str:
    """Telugu post for one deal, through post.py's Disclosure Gate. Raises GateError."""
    did, kind = d["id"], d["kind"]
    title = str(d.get("title_te", "")).strip()
    if not title:
        raise post.GateError(f"{did}: title_te (Telugu title) is missing")
    link = str(d.get("link", "")).strip()
    if not link.startswith("https://"):
        raise post.GateError(f"{did}: link must be a full https:// address")
    note = str(d.get("note_te", "")).strip()
    lines = [post.DISCLOSURE]
    fee_block = []
    if kind == "product":
        store = str(d.get("store", "")).strip()
        lines.append(f"నేటి డీల్ ({store}): {title}" if store else f"నేటి డీల్: {title}")
        if d.get("discount_pct") not in (None, ""):
            pct = d["discount_pct"]
            if not isinstance(pct, int) or not 1 <= pct <= 95:
                raise post.GateError(f"{did}: discount_pct must be a whole number 1-95")
            lines.append(f"MRP పై {pct}% తగ్గింపు")
        if d.get("coupon"):
            lines.append(f"కూపన్ కోడ్ / Coupon: {d['coupon']}")
    else:  # credit_card (RBI rules, PLAN.md §3b)
        if not _on(_host(link), CARD_HOSTS):
            raise post.GateError(f"{did}: card offers only through EarnKaro/BankKaro ({', '.join(CARD_HOSTS)})")
        for field in ("joining_fee", "annual_fee", "eligibility", "terms_url"):
            if str(d.get(field, "")).strip() == "":
                raise post.GateError(f"{did}: card post needs {field}")
        joining = _money(d["joining_fee"], "joining_fee", did)
        annual = _money(d["annual_fee"], "annual_fee", did)
        terms = str(d["terms_url"]).strip()
        if not terms.startswith("https://"):
            raise post.GateError(f"{did}: terms_url must be the issuer's https:// terms page")
        lifetime_free = d.get("lifetime_free") is True
        if lifetime_free and (joining or annual):
            raise post.GateError(f"{did}: lifetime_free needs joining_fee and annual_fee of 0")
        if not lifetime_free and FREE_WORDS.search(f"{title} {note}"):
            raise post.GateError(f"{did}: say 'free' only for lifetime-free cards")
        lines.append(f"క్రెడిట్ కార్డ్ ఆఫర్: {title}")
        if lifetime_free:
            fee_block.append("జాయినింగ్ ఫీ / Joining fee: ₹0 · వార్షిక ఫీ / Annual fee: ₹0 (లైఫ్‌టైమ్ ఫ్రీ / lifetime free)")
        else:
            fee_block += [f"జాయినింగ్ ఫీ / Joining fee: ₹{joining:,}", f"వార్షిక ఫీ / Annual fee: ₹{annual:,}"]
        fee_block += [f"అర్హత / Eligibility: {str(d['eligibility']).strip()}",
                      f"బ్యాంకు నిబంధనలు / Issuer terms: {terms}", CARD_DISCLAIMER]
    if note:
        lines.append(note)
    deal = post.Deal(id=did, post_at=now, text="\n".join(lines), link=add_utm(link, did, now.date()),
                     price=str(d.get("price", "")).strip() if kind == "product" else "",
                     price_as_of=post.parse_ist(d["price_as_of"]) if kind == "product" and d.get("price_as_of") else None)
    message = post.compose(deal)
    if fee_block:
        body, last = message.rsplit("\n", 1)
        message = "\n".join([body, *fee_block, last])
    post.check(deal, message, now)
    _common_checks(did, message)
    return message


def build_tip(t: dict) -> str:
    te, en = str(t.get("te", "")).strip(), str(t.get("en", "")).strip()
    if not te:
        raise post.GateError(f"tip {t.get('id')}: Telugu text missing")
    message = "\n".join(x for x in (TIP_HEAD, te, en, TIP_FOOT) if x)
    _common_checks(f"tip {t.get('id')}", message)
    if re.search(r"(^|\s)#ad\b", message, re.IGNORECASE):
        raise post.GateError(f"tip {t.get('id')}: tips are not ads; no affiliate content in tips")
    return message


# ---------- planning ----------

def _at(day: date, hhmm: str) -> datetime:
    return datetime.combine(day, time.fromisoformat(hhmm), tzinfo=IST)


def _fresh_for(d: dict, now: datetime) -> bool:
    if d.get("kind") != "product" or not d.get("price_as_of"):
        return True
    try:
        as_of = post.parse_ist(d["price_as_of"])
    except post.GateError:
        return True  # let the gate refuse it with a clear message
    return as_of <= now and now - as_of <= post.MAX_PRICE_AGE


def _eligible(d: dict, state: dict, now: datetime, live: bool, taken: set) -> bool:
    day = now.date()
    if d["id"] in taken or (live and d.get("sample")):
        return False
    if d["id"] in {x["id"] for x in state["dead"]}:
        return False
    url = normalise(str(d.get("link", "")))
    for p in state["posted"]:
        if p["id"] == d["id"]:
            return False
        if p["url"] == url and now - datetime.fromisoformat(p["at"]) < REPOST_AFTER:
            return False
    if d.get("date") and d["date"] != day.isoformat():
        return False
    if d.get("valid_until") and day.isoformat() > d["valid_until"]:
        return False
    return _fresh_for(d, now)


def _ranked(deals: list, day: date) -> list:
    order = {id(d): i for i, d in enumerate(deals)}
    return sorted(deals, key=lambda d: (d.get("date") != day.isoformat(), -int(d.get("priority", 0)), order[id(d)]))


def _cards_today(state: dict, day: date) -> int:
    return sum(1 for p in state["posted"] if p["kind"] == "credit_card" and p["slot"].startswith(day.isoformat()))


def _pass(deals, tips, state, now, send, check_link, out, live) -> dict:
    """One scheduler pass at `now`. send=None means dry run (state untouched)."""
    result = {"posted": [], "dry_run": [], "refused": [], "dead": [], "tips": []}
    day, refused, taken = now.date(), set(), set()
    done_slots = {p["slot"] for p in state["posted"]}
    for hhmm in SLOTS:
        slot = f"{day} {hhmm}"
        start = _at(day, hhmm)
        if slot in done_slots or not start <= now <= start + GRACE:
            continue
        cards = _cards_today(state, day) + sum(1 for d in deals if d["id"] in taken and d["kind"] == "credit_card")
        for d in _ranked(deals, day):
            if d["id"] in refused or not _eligible(d, state, now, live, taken):
                continue
            if d["kind"] == "credit_card" and cards >= MAX_CARDS_PER_DAY:
                continue
            try:
                message = build(d, now)
            except post.GateError as e:
                refused.add(d["id"])
                result["refused"].append(d["id"])
                out(f"REFUSED {e}")
                continue
            if check_link:
                status = check_link(str(d["link"]).strip())
                if status == "dead":
                    state["dead"].append({"id": d["id"], "url": normalise(d["link"]), "at": now.isoformat()})
                    result["dead"].append(d["id"])
                    out(f"DEAD LINK {d['id']}: skipped, next deal takes the {hhmm} slot")
                    continue
                if status != "ok":
                    out(f"NOTE {d['id']}: link could not be checked ({status}); posting anyway")
            taken.add(d["id"])
            if send is None:
                result["dry_run"].append(d["id"])
                out(f"DRY RUN {d['id']} @ {slot} IST:\n{message}\n---")
            else:
                send(message)
                state["posted"].append({"id": d["id"], "url": normalise(d["link"]), "kind": d["kind"],
                                        "slot": slot, "at": now.isoformat()})
                result["posted"].append({"id": d["id"], "kind": d["kind"], "slot": slot, "message": message})
            break
    _tip_pass(tips, state, now, send, out, result)
    return result


def _tip_pass(tips, state, now, send, out, result) -> None:
    day = now.date()
    start = _at(day, TIP_SLOT)
    if day.weekday() != 6 or not tips or not start <= now <= start + GRACE:
        return
    week = f"{day.isocalendar().year}-W{day.isocalendar().week:02d}"
    if any(t["week"] == week for t in state["tips"]):
        return
    used = {t["id"] for t in state["tips"]}
    first = day.isocalendar().week % len(tips)
    rotated = tips[first:] + tips[:first]
    for t in [t for t in rotated if t.get("id") not in used] or rotated:
        try:
            message = build_tip(t)
        except post.GateError as e:
            out(f"REFUSED {e}")
            continue
        if send is None:
            out(f"DRY RUN tip {t['id']} @ {day} {TIP_SLOT} IST:\n{message}\n---")
        else:
            send(message)
            state["tips"].append({"id": t["id"], "week": week, "at": now.isoformat()})
            result["tips"].append({"id": t["id"], "message": message})
        return


def run(deals, tips, state, now, send=None, check_link=None, out=print) -> dict:
    """Scheduled pass. Live (send given): checks links, updates state. Dry run: prints only."""
    live = send is not None
    return _pass(deals, tips, state, now, send, check_link if live else None, out, live)


def simulate_day(deals, tips, state, day: date, check_link=None, out=print) -> dict:
    """Walk every slot of `day` as if the cron fired on time. Sends nothing; updates `state` in memory."""
    times = sorted(SLOTS + ([TIP_SLOT] if day.weekday() == 6 else []))
    plan = {"deals": [], "tips": [], "refused": []}
    for hhmm in times:
        now = _at(day, hhmm)
        r = _pass(deals, tips, state, now, lambda m: None, check_link, out, live=False)
        plan["refused"] += r["refused"]
        for p in r["posted"]:
            plan["deals"].append(p)
            out(f"=== {hhmm} IST · {p['id']} ({p['kind']}) ===\n{p['message']}\n")
        for t in r["tips"]:
            plan["tips"].append(t)
            out(f"=== {hhmm} IST · weekly tip {t['id']} ===\n{t['message']}\n")
    if len(plan["deals"]) < MIN_PER_DAY:
        out(f"WARNING only {len(plan['deals'])} deals for {day}; add {MIN_PER_DAY}+ to deals.json")
    return plan


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Telugu deals channel poster (dry run unless live is fully allowed).")
    p.add_argument("--deals", type=Path, default=HERE / "deals.json")
    p.add_argument("--tips", type=Path, default=HERE / "tips.json")
    p.add_argument("--state", type=Path, default=HERE / "state.json")
    p.add_argument("--now", help='pretend time, "YYYY-MM-DD HH:MM" IST')
    p.add_argument("--day", help="print every post for this day (YYYY-MM-DD); never sends")
    p.add_argument("--live", action="store_true", help="post for real (also needs secrets + DEALS_LIVE=go)")
    p.add_argument("--check-links", action="store_true", help="dead-link check in dry runs too")
    a = p.parse_args(argv)
    try:
        deals = load_json(a.deals).get("deals", [])
        tips = load_json(a.tips).get("tips", []) if a.tips.exists() else []
        validate_deals(deals)
        state = load_state(a.state)
        check = link_status if a.check_links else None
        if a.day:
            plan = simulate_day(deals, tips, copy.deepcopy(state), date.fromisoformat(a.day), check)
            print(f"day {a.day}: {len(plan['deals'])} deals, {len(plan['tips'])} tip, "
                  f"{len(plan['refused'])} refused (dry run, nothing sent)")
            return 1 if plan["refused"] else 0
        now = post.parse_ist(a.now) if a.now else datetime.now(IST).replace(second=0, microsecond=0)
        send = None
        if a.live:
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            chat = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHANNEL_ID")
            if not token or not chat:
                print("Live needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID secrets. Staying in dry run.")
            elif os.environ.get("DEALS_LIVE") != "go":
                print("Live needs Akhil's go (repo variable DEALS_LIVE=go). Staying in dry run.")
            else:
                send = lambda text: post.telegram_send(token, chat, text)  # noqa: E731
                check = link_status
        # Live: link check always. Dry run: link check only with --check-links; state never changes.
        r = _pass(deals, tips, state, now, send, check, print, live=send is not None)
        if send is not None and (r["posted"] or r["dead"] or r["tips"]):
            save_state(a.state, state)
    except (post.GateError, ValueError, json.JSONDecodeError) as e:
        print(f"FILE ERROR {e}")
        return 2
    print(f"{now:%Y-%m-%d %H:%M} IST: {len(r['posted'])} posted, {len(r['dry_run'])} dry-run, "
          f"{len(r['tips'])} tip, {len(r['refused'])} refused, {len(r['dead'])} dead links")
    return 1 if r["refused"] else 0


if __name__ == "__main__":
    sys.exit(main())
