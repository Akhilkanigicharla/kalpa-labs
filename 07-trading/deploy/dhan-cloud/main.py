"""Kalpa b7 live bot for Dhan Cloud: Rs 10,000 = Nifty trend Rs 5,000 + gold held Rs 5,000.

Runs once each trading morning (schedule it in Dhan Cloud for 09:20 IST, Mon-Fri). Same code, same rules
as the daily paper run in .github/workflows/paper-trade.yml; the only difference is real Dhan orders.
Dhan FAQ (14 Nov 2026): strategies on Dhan Cloud need no static IP; Python 3.11; requirements.txt is installed.

Every one of these must hold or the bot refuses and sends no order:
  * the Dhan token + client id: Dhan Cloud syncs the token into global variables itself (Dhan FAQ); Akhil adds
    LIVE_TRADING=YES and KALPA_GO=go as global variables (never in git);
  * KALPA_GATE_PASS=yes (Akhil's sign-off that the strategy passed the gate);
  * at least PAPER_DAYS_MIN paper days logged by the GitHub paper run (read from the public repo);
  * no KILL file in the repo's paper/track-A/flags/ (the phone kill switch): if present, no buys.
Safety inside the code: Rs 10,000 hard max, whole units, protective stop on every buy, daily/weekly loss caps,
one trade per symbol per day, never re-sends an order whose reply was lost.
Own money only, not advice to anyone (SEBI).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))            # the package ships src/ next to this file

RAW = "https://raw.githubusercontent.com/Akhilkanigicharla/kalpa-labs/main/07-trading/paper"
WORK = Path(os.environ.get("KALPA_WORK_DIR", HERE / "work"))
FLAGS, OUT = WORK / "flags", WORK / "out"
LEGS = [   # (label, runner args) mirrored from paper-trade.yml
    ("nifty-trend", ["--strategy", "tsmom", "--signal-symbol", "^NSEI", "--symbol", "NIFTYBEES",
                     "--capital", "5000", "--paper-state", str(WORK / "paper-A.json")]),
    ("gold-hold", ["--strategy", "hold", "--symbol", "GOLDBEES",
                   "--capital", "5000", "--paper-state", str(WORK / "paper-A-gold.json")]),
]


def fetch(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read() if r.status == 200 else None
    except Exception:
        return None


def prepare(env: dict) -> list[str]:
    """Write the flag files the runner checks, from Akhil's global variables + the repo. Returns problems."""
    FLAGS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    problems = []
    for name in ("GO", "GATE_PASS_A", "KILL"):
        (FLAGS / name).unlink(missing_ok=True)
    if env.get("KALPA_GO", "").strip().lower() == "go":
        (FLAGS / "GO").write_text("go\n", encoding="utf-8")
    if env.get("KALPA_GATE_PASS", "").strip().lower() == "yes":
        (FLAGS / "GATE_PASS_A").write_text("signed off by Akhil in Dhan Cloud variables\n", encoding="utf-8")
    kill = fetch(f"{RAW}/track-A/flags/KILL")
    if kill is not None:
        (FLAGS / "KILL").write_text(kill.decode("utf-8", "replace") or "kill\n", encoding="utf-8")
    for leg, path in (("track-A", "paper-A.json"), ("track-A-gold", "paper-A-gold.json")):
        data = fetch(f"{RAW}/{leg}/state-A.json")
        if data is None:
            problems.append(f"could not read the {leg} paper record from GitHub (no trade without it)")
            continue
        json.loads(data)                     # refuse garbage
        (WORK / path).write_bytes(data)
    return problems


def resolve_keys(env: dict) -> dict:
    """Dhan Cloud syncs the access token into the account's global variables by itself (Dhan FAQ, 14 Nov 2026),
    but its docs don't name the variable. Use KALPA_TOKEN_VAR / KALPA_CLIENT_VAR if Akhil sets them, else the
    first common name present. Values are copied, never printed."""
    def pick(override: str, names: tuple[str, ...]) -> str:
        for n in ((env.get(override),) if env.get(override) else ()) + names:
            if n and env.get(n):
                return env[n]
        return ""
    env["DHAN_ACCESS_TOKEN"] = pick("KALPA_TOKEN_VAR", ("DHAN_ACCESS_TOKEN", "ACCESS_TOKEN", "access_token", "DHAN_TOKEN"))
    env["DHAN_CLIENT_ID"] = pick("KALPA_CLIENT_VAR", ("DHAN_CLIENT_ID", "CLIENT_ID", "client_id", "dhanClientId"))
    return env


def main(env: dict | None = None) -> int:
    env = resolve_keys(dict(os.environ if env is None else env))
    problems = prepare(env)
    if problems:
        print("LIVE REFUSED:\n  - " + "\n  - ".join(problems))
        return 2
    from src.livetrade import runner
    worst = 0
    for label, args in LEGS:
        print(f"== {label}")
        rc = runner.main(["--track", "A", "--mode", "live", "--broker", "dhan", "--out", str(OUT),
                          "--flags", str(FLAGS), *args], env=env)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
