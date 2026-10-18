#!/usr/bin/env python3
"""Deal Poster Bot (b5.W1.3, roadmap A18).

Reads queue.csv and posts due deals to the Telegram channel with plain Bot API
calls (Python standard library only, nothing to install).

Safety first:
  * Dry run is the default. It only prints. A real post needs --live AND the
    TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID environment variables, which Akhil
    sets as GitHub secrets himself. This file never stores or logs the token.
  * Disclosure Gate (ASCI, PLAN.md §3b): every post must carry "#ad" in its
    first two lines, plus the Telugu/English affiliate label.
  * Price rule (Amazon Associates): a price is shown only with its "as of"
    time and "may change"; a price checked more than 24 h before posting is
    refused.
  * No loan, insurance, mutual-fund or broker posts or links (no ARN, RBI LSP
    or IRDAI status), no "guaranteed returns" claims.

Queue columns: id, post_at, text, link, price, price_as_of
  post_at / price_as_of: "YYYY-MM-DD HH:MM" in IST. price and price_as_of may be blank.

Usage:
  python post.py                 # dry run: show what is due now
  python post.py --now "2026-10-19 09:00"
  python post.py --live          # really post (needs the two secrets)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
HERE = Path(__file__).resolve().parent
DISCLOSURE = "#ad · affiliate link / అనుబంధ లింక్"
MAY_CHANGE = "may change / ధర మారవచ్చు"
MAX_PRICE_AGE = timedelta(hours=24)
MAX_LATE = timedelta(hours=6)  # a slot missed by more than this is skipped, not posted late
TELEGRAM_LIMIT = 4096

# Words and hosts we must never promote (PLAN.md §3b). Lower-case.
BANNED_WORDS = [
    "loan", "insurance", "mutual fund", "demat", "stock tip", "trading account",
    "guaranteed return", "assured return", "lic policy",
    "లోన్", "రుణం", "ఇన్సూరెన్స్", "బీమా", "మ్యూచువల్ ఫండ్",
]
BANNED_HOSTS = [
    "zerodha.com", "groww.in", "upstox.com", "angelone.in", "paytmmoney.com",
    "dhan.co", "5paisa.com", "icicidirect.com", "kotaksecurities.com",
    "policybazaar.com", "acko.com", "digit.insure", "insurancedekho.com",
    "bankbazaar.com", "paisabazaar.com", "kreditbee.in", "moneyview.in",
    "navi.com", "kissht.com", "mpokket.in", "cred.club",
]
REQUIRED_COLUMNS = ["id", "post_at", "text", "link", "price", "price_as_of"]


class GateError(ValueError):
    """A post broke a compliance rule and must not go out."""


@dataclass
class Deal:
    id: str
    post_at: datetime
    text: str
    link: str
    price: str = ""
    price_as_of: datetime | None = None


def parse_ist(value: str) -> datetime:
    value = value.strip()
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    except ValueError:
        raise GateError(f"time {value!r} must look like 2026-10-19 08:30 (IST)") from None


def load_queue(path: Path) -> list[Deal]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise GateError(f"queue.csv is missing columns: {', '.join(missing)}")
        deals = []
        for row in reader:
            if not (row.get("id") or "").strip():
                continue
            deals.append(Deal(
                id=row["id"].strip(),
                post_at=parse_ist(row["post_at"]),
                text=(row["text"] or "").replace("\\n", "\n").strip(),
                link=(row["link"] or "").strip(),
                price=(row["price"] or "").strip(),
                price_as_of=parse_ist(row["price_as_of"]) if (row["price_as_of"] or "").strip() else None,
            ))
    ids = [d.id for d in deals]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise GateError(f"duplicate ids in queue.csv: {', '.join(dupes)}")
    return deals


def load_sent(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.split("\t")[0].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def format_when(t: datetime) -> str:
    hour = t.hour % 12 or 12
    minute = f":{t.minute:02d}" if t.minute else ""
    return f"{t.day} {t:%b}, {hour}{minute} {'am' if t.hour < 12 else 'pm'}"


def compose(deal: Deal) -> str:
    """Build the final message. The gate checks this exact text."""
    lines = [deal.text]
    if deal.price:
        if deal.price_as_of is None:
            raise GateError(f"{deal.id}: price given without price_as_of")
        amount = deal.price.lstrip("₹").replace(",", "").strip()
        if not re.fullmatch(r"\d+(\.\d{1,2})?", amount):
            raise GateError(f"{deal.id}: price {deal.price!r} is not a number")
        rupees = f"₹{int(float(amount)):,}" if float(amount).is_integer() else f"₹{float(amount):,.2f}"
        lines.append(f"{rupees} as of {format_when(deal.price_as_of)}; {MAY_CHANGE}")
    lines.append(deal.link)
    return "\n".join(lines)


def host_of(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def check(deal: Deal, message: str, now: datetime) -> None:
    """Disclosure Gate. Raises GateError with the first broken rule."""
    first_two = "\n".join(message.splitlines()[:2])
    if not re.search(r"(^|\s)#ad\b", first_two, flags=re.IGNORECASE):
        raise GateError(f"{deal.id}: '#ad' must be in the first 2 lines")
    if DISCLOSURE.split(" · ")[1] not in first_two:
        raise GateError(f"{deal.id}: first 2 lines must say '{DISCLOSURE}'")
    if not deal.link.startswith("https://") or not host_of(deal.link):
        raise GateError(f"{deal.id}: link must be a full https:// address")
    low = message.lower()
    for word in BANNED_WORDS:
        if word in low:
            raise GateError(f"{deal.id}: '{word}' posts are not allowed (no ARN/RBI/IRDAI status)")
    for url in re.findall(r"https?://\S+", message):
        h = host_of(url)
        if any(h == b or h.endswith("." + b) for b in BANNED_HOSTS):
            raise GateError(f"{deal.id}: links to {h} are not allowed")
    if re.search(r"₹\s?\d", deal.text):
        raise GateError(f"{deal.id}: put the price in the price column so it gets its 'as of' time")
    if deal.price:
        if deal.price_as_of > now:
            raise GateError(f"{deal.id}: price_as_of is in the future")
        if now - deal.price_as_of > MAX_PRICE_AGE:
            raise GateError(f"{deal.id}: price is older than 24 h; re-check it before posting")
        if MAY_CHANGE not in message:
            raise GateError(f"{deal.id}: price line must say it may change")
    if len(message) > TELEGRAM_LIMIT:
        raise GateError(f"{deal.id}: message longer than Telegram's {TELEGRAM_LIMIT} characters")


def due(deals: list[Deal], sent: set[str], now: datetime) -> tuple[list[Deal], list[Deal]]:
    """Split unsent deals whose time has come into (to_post, too_late)."""
    to_post, too_late = [], []
    for d in sorted(deals, key=lambda d: d.post_at):
        if d.id in sent or d.post_at > now:
            continue
        (too_late if now - d.post_at > MAX_LATE else to_post).append(d)
    return to_post, too_late


def telegram_send(token: str, chat_id: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=20) as r:
        reply = json.loads(r.read().decode())
    if not reply.get("ok"):
        raise RuntimeError(f"Telegram said no: {reply.get('description', 'unknown error')}")
    return reply


def run(queue: Path, sent_path: Path, now: datetime, live: bool, send=None, out=print) -> dict:
    """One pass. Returns counts. `send(text)` is injected by tests; live mode uses Telegram."""
    deals = load_queue(queue)
    sent = load_sent(sent_path)
    to_post, too_late = due(deals, sent, now)
    result = {"posted": [], "dry_run": [], "refused": [], "skipped_late": [d.id for d in too_late]}
    for d in too_late:
        out(f"SKIP {d.id}: slot {format_when(d.post_at)} missed by more than {MAX_LATE}")
    for d in to_post:
        try:
            message = compose(d)
            check(d, message, now)
        except GateError as e:
            result["refused"].append(d.id)
            out(f"REFUSED {e}")
            continue
        if not live:
            result["dry_run"].append(d.id)
            out(f"DRY RUN {d.id}:\n{message}\n---")
            continue
        send(message)
        with open(sent_path, "a", encoding="utf-8") as f:
            f.write(f"{d.id}\t{now.isoformat(timespec='minutes')}\n")
        result["posted"].append(d.id)
        out(f"POSTED {d.id}")
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Post due deals from queue.csv to Telegram.")
    p.add_argument("--queue", type=Path, default=HERE / "queue.csv")
    p.add_argument("--sent", type=Path, default=HERE / "sent.log")
    p.add_argument("--now", help='pretend time, "YYYY-MM-DD HH:MM" IST')
    p.add_argument("--live", action="store_true", help="really post (needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
    a = p.parse_args(argv)
    now = parse_ist(a.now) if a.now else datetime.now(IST).replace(second=0, microsecond=0)
    send = None
    if a.live:
        token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        if not token or not chat:
            print("Live mode needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID secrets. Staying in dry run.")
            a.live = False
        else:
            send = lambda text: telegram_send(token, chat, text)  # noqa: E731
    try:
        r = run(a.queue, a.sent, now, a.live, send)
    except GateError as e:
        print(f"QUEUE ERROR {e}")
        return 2
    print(f"done: {len(r['posted'])} posted, {len(r['dry_run'])} dry-run, "
          f"{len(r['refused'])} refused, {len(r['skipped_late'])} skipped late")
    return 1 if r["refused"] else 0


if __name__ == "__main__":
    sys.exit(main())
