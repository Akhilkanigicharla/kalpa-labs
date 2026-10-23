#!/usr/bin/env python3
"""How many tokens did this Claude session use? Sums the session transcript(s) in ~/.claude/projects
and appends one row to 00-hq/log/tokens.csv. This is the session's own count, not the account meter:
Anthropic's weekly % is only visible to Akhil in the app (Settings > Usage).
Usage: python3 00-hq/tools/run_tokens.py "<label>"   (label = e.g. "Build sprint A74")"""
import csv, datetime, glob, json, os, sys

KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")

def totals(paths):
    t = dict.fromkeys(KEYS, 0); t["turns"] = 0; seen = set()
    for p in paths:
        for line in open(p, encoding="utf-8", errors="ignore"):
            try: m = json.loads(line).get("message") or {}
            except ValueError: continue
            u, mid = m.get("usage"), m.get("id")
            if not isinstance(u, dict) or mid in seen: continue  # one row per API call (streamed parts repeat the id)
            seen.add(mid); t["turns"] += 1
            for k in KEYS: t[k] += int(u.get(k) or 0)
    return t

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "session"
    paths = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
    t = totals(paths)
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, "00-hq", "log", "tokens.csv")
    new = not os.path.exists(out)
    ist = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M")
    with open(out, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["ist", "label", "api_calls", "output", "input", "cache_write", "cache_read"])
        w.writerow([ist, label, t["turns"], t["output_tokens"], t["input_tokens"], t["cache_creation_input_tokens"], t["cache_read_input_tokens"]])
    print(f"{label}: {t['turns']} calls, output {t['output_tokens']:,}, new input {t['input_tokens'] + t['cache_creation_input_tokens']:,}, cached reads {t['cache_read_input_tokens']:,}")

if __name__ == "__main__":
    main()
