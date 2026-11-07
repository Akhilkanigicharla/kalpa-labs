#!/usr/bin/env python3
"""A143: Kalpa daily brief + alerts (GitHub Actions, 9 PM IST). Replaces the n8n CEO update after the n8n trial ended.

Alerts come FIRST: n8n down / trial or quota ended, website or chat not answering, failing Actions runs.
Then: commits and roadmap ticks in the last 24 h.
Sends to Akhil's PRIVATE Telegram chat (CEO_CHAT_ID). Never to a channel or group: ids starting with "-" are refused,
because TELEGRAM_CHAT_ID is the public deals channel (3 Nov 2026 mistake). Without a token it prints (dry run).
Standard library only. Run: python3 00-hq/tools/daily_brief.py [--dry-run]
"""
import glob, json, os, re, subprocess, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
SITE = os.environ.get("KL_SITE_URL", "https://kalpalabs.dpdns.org/")
CHAT = os.environ.get("KL_CHAT_URL", "https://kalpalabs.app.n8n.cloud/webhook/7b78c6c8-78e2-4a03-8b95-76167aa4d63b/chat")
N8N_SELF = os.environ.get("N8N_SELF_URL", "")  # self-hosted n8n base URL (A146), checked at /healthz when set
BAD_WORDS = re.compile(r"trial has ended|trial ended|upgrade now|quota|rate limit|insufficient|payment required|suspended", re.I)


def http(url, data=None, timeout=20):
    """Returns (status, body text). status 0 = could not connect."""
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "kalpa-daily-brief"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(20000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(20000).decode("utf-8", "replace")
    except Exception as e:  # DNS, timeout, TLS
        return 0, str(e)[:200]


def classify(name, status, body, want=None):
    """One check → alert text, or None when healthy."""
    if status == 0:
        return f"{name}: not reachable ({body[:80]})"
    m = BAD_WORDS.search(body or "")
    if m:
        return f"{name}: provider says “{m.group(0)}” (HTTP {status}): account or plan problem, needs Akhil"
    if status in (401, 403):
        return f"{name}: HTTP {status}, a key or login stopped working"
    if status == 429:
        return f"{name}: HTTP 429, free quota or rate limit hit"
    if status >= 400:
        return f"{name}: HTTP {status}"
    if want and want not in (body or ""):
        return f"{name}: answered but the page looks wrong (missing “{want}”)"
    return None


def failing_runs(repo, token, since):
    if not (repo and token):
        return []
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/actions/runs?per_page=50&status=failure",
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "kalpa-daily-brief"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            runs = json.load(r).get("workflow_runs", [])
    except Exception as e:
        return [f"could not read Actions runs ({str(e)[:60]})"]
    names = sorted({r["name"] for r in runs if r.get("created_at", "") >= since})
    return [f"Actions failing: {n}" for n in names]


def private_chat(chat_id):
    """Private chats have positive numeric ids; channels and groups are negative (-100…)."""
    return str(chat_id).isdigit()


def git_lines(args):
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=30).stdout.strip().splitlines()
    except Exception:
        return []


WORLDS = {"HQ": "HQ", "b1": "BotBhai", "b2": "JobCard", "b3": "Exam kits", "b4": "Tab Lifeboat",
          "b5": "Telugu Deals", "b6": "Ledger Peaks", "b7": "Trading Lab"}
NOISE = re.compile(r"^(agents\(|claim |log[: ]|token row|merge )", re.I)


def real_commits(subjects):
    """Drop robot/bookkeeping commits so the brief shows real work."""
    return [c for c in subjects if not NOISE.match(c)]


def progress(roadmap, task_counts, today, days=7):
    """Per world: items finished in the last `days`, in progress, open; plus agent drafts awaiting review."""
    import datetime as _dt
    since = today - _dt.timedelta(days=days - 1)
    out = [f"📦 Worlds, last {days} days (finished · in progress · open):"]
    for w, name in WORLDS.items():
        rows = re.findall(r"^- \[(.)\] \*\*(A\d+)\*\* " + w + r" · ([^\n]*)", roadmap, re.M)
        done = [(i, t) for m, i, t in rows if m == "x" and (d := re.search(r"\(done (\d{4}-\d\d-\d\d)", t))
                and since.isoformat() <= d.group(1) <= today.isoformat()]
        wip = sum(1 for m, _, _ in rows if m == "~")
        opn = sum(1 for m, _, _ in rows if m == " ")
        out.append(f"• {w} {name}: {len(done)} done · {wip} in progress · {opn} open")
        out += [f"   ✔ {i} {re.sub(r'\s*\(done.*', '', t)[:70]}" for i, t in done[:3]]
    out.append(f"🤖 Free-model drafts waiting for review: {task_counts.get('review', 0)}")
    return out


def build(now, checks, runs, commits, ticks, extra=None):
    alerts = [a for a in checks if a] + runs
    out = [f"🌳 Kalpa daily brief · {now:%a %d %b, %I:%M %p} IST", ""]
    if alerts:
        out += ["⚠️ ALERTS (fix first)"] + [f"• {a}" for a in alerts] + [""]
    else:
        out += ["✅ No alerts: website, chat and automations answered.", ""]
    out += ["💰 Revenue: ₹0 (no payments switched on yet)", ""]
    out += [f"🛠 Code changes (24 h): {len(commits)}"] + [f"• {c[:90]}" for c in commits[:5]]
    if ticks:
        out += ["", f"✔️ Roadmap items finished today: {', '.join(ticks)}"]
    if extra:
        out += [""] + extra
    return "\n".join(out)[:3900], alerts


def main(argv):
    dry = "--dry-run" in argv
    now = datetime.now(IST)
    since_iso = (now - timedelta(hours=24)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    checks = [classify("Website", *http(SITE), want="Kalpa"),
              classify("Website chat (Kalpa Bhai)", *http(CHAT, {"action": "sendMessage", "sessionId": "health-check", "chatInput": "ping"}, timeout=40))]
    if N8N_SELF:
        checks.append(classify("Self-hosted n8n", *http(N8N_SELF.rstrip("/") + "/healthz")))
    runs = failing_runs(os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN"), since_iso)
    commits = real_commits(git_lines(["log", "--since=24 hours ago", "--pretty=%s"]))
    today = now.strftime("%Y-%m-%d")
    ticks = sorted(set(re.findall(r"\*\*(A\d+)\*\*[^\n]*\(done " + today, open("00-hq/ROADMAP.md", encoding="utf-8").read()))) if os.path.exists("00-hq/ROADMAP.md") else []
    road = open("00-hq/ROADMAP.md", encoding="utf-8").read() if os.path.exists("00-hq/ROADMAP.md") else ""
    counts = {}
    for f in glob.glob("00-hq/tasks/*.json"):
        for t in json.load(open(f, encoding="utf-8")):
            counts[t.get("status", "")] = counts.get(t.get("status", ""), 0) + 1
    text, alerts = build(now, checks, runs, commits, ticks, progress(road, counts, now.date()))
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("CEO_CHAT_ID", "")
    if not private_chat(chat):
        print("refusing to send: CEO_CHAT_ID is not a private chat", file=sys.stderr)
        return 1
    if dry or not (tok and chat):
        print(text)
        if not dry:
            print("\n(dry run: TELEGRAM_BOT_TOKEN not set)")
        return 0
    status, body = http(f"https://api.telegram.org/bot{tok}/sendMessage", {"chat_id": chat, "text": text, "disable_web_page_preview": True})
    if status != 200:
        print(f"telegram send failed: HTTP {status}", file=sys.stderr)  # never print the token
        return 1
    print(f"sent ({len(alerts)} alerts)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
