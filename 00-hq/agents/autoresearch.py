#!/usr/bin/env python3
"""Autoresearch for Kalpa's agents: playbooks are the "weights", Vigil's pass rate is the loss.

Method credit: chrisworsey55/atlas-gic (MIT licence), architecture/autoresearch.md and its
"Darwinian weights". Re-implemented from the written description; no code copied.

Each cycle (OFF by default; nothing calls this file yet, see README.md "Autoresearch"):
  1. Score every agent: Vigil pass rate over its last N attempts, read from the task queues
     00-hq/tasks/<world>.json that runner.py writes (each FIX adds 1 to `tries`; a PASS moves
     the task to "review"/"done").
  2. Darwinian weights, once per UTC day: start 1.0, clamp [0.3, 2.5]; top quartile x1.05,
     bottom quartile x0.95. (For the decision layer / Kingdom view; runner.py ignores them today.)
  3. Judge pending experiments: after N new Vigil attempts by that agent, KEEP the change if
     its pass rate beat the baseline, else REVERT it. No new attempts for 14 days = revert.
  4. Pick the worst agent (lowest rate, enough attempts, no pending experiment, not changed in
     the last 5 days) and record ONE proposed playbook line as a PENDING experiment.

Hard rules (checked in code, every refusal is logged):
  * A change can only ADD one line to that agent's overlay. The vendored playbooks and the
    KALPA RULES in runner.py are never edited, so they can never be removed.
  * A line that tries to weaken rules or game Vigil (ignore/override/skip, "PASS", links,
    secrets) is refused.
  * Max one change per agent per experiment, one pending experiment per agent.
Everything goes to 00-hq/agents/autoresearch-ledger.json (`log` is append-only).
Standard library only, no network, no LLM calls.

  python3 00-hq/agents/autoresearch.py --dry-run           # print what it would do (default)
  python3 00-hq/agents/autoresearch.py --write             # do it and save the ledger
  python3 00-hq/agents/autoresearch.py --write --propose "Mark every price UNVERIFIED unless it is in the repo files."
"""
from __future__ import annotations

import argparse, glob, json, os, re, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(HERE, "autoresearch-ledger.json")
sys.path.insert(0, HERE)
from runner import RULES  # noqa: E402  (stdlib-only module, no side effects on import)

W_MIN, W_MAX, W_START, UP, DOWN = 0.3, 2.5, 1.0, 1.05, 0.95
DEFAULTS = {"last_n": 10, "eval_runs": 5, "min_attempts": 3, "cooldown_days": 5, "stale_days": 14}
PASSED = {"review", "done"}
CREDIT = "Method: chrisworsey55/atlas-gic (MIT) autoresearch + Darwinian weights; Kalpa re-implementation."

# Vigil-note theme -> one targeted line (used when no --propose line is given)
THEMES = [
    (r"unverified|invent|made.?up|fabricat|source", "Before you finish, mark every number, price, date or claim that is not in the REPO FILES as UNVERIFIED."),
    (r"telugu|hindi|language|script|tenglish|hinglish", "Write in exactly the languages the task names, each in its own script, and check both before you finish."),
    (r"unfinish|incomplete|missing|placeholder|todo|plan instead", "Deliver every part the task title lists, complete and ready to use; no plans, placeholders or TODOs."),
    (r"personal data|phone|email|name of", "Use no real person's name, phone or email; use placeholders like {name}."),
    (r"#ad|asci|affiliate|disclos", "Put #ad on every affiliate link or paid mention."),
    (r"long|too many|list|5 items|short", "Keep lists to 5 items at most and sentences short."),
]
GENERIC = "Re-read the task title and the REPO FILES once more before you finish, and fix anything that does not match them."

# Refuse lines that could weaken the rules or game the checker.
BANNED = re.compile(
    r"\b(ignore|disregard|override|bypass|skip|forget|relax|loosen|drop|remove|delete|no longer|"
    r"don'?t need|do not need|need not|not required|optional|exception|jailbreak|pretend)\b"
    r"|\bPASS\b|https?://|www\.|api[_ ]?key|token|password|otp\b|secret", re.I)
MAX_LINE = 240


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------- reading what runner.py records
def load_tasks(root: str = ROOT) -> list[dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(root, "00-hq/tasks/*.json"))):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        out += [t for t in (data if isinstance(data, list) else data.get("tasks", [])) if isinstance(t, dict)]
    return out


def task_state(t: dict) -> tuple[int, bool]:
    """(Vigil FIX count, passed?) for one task."""
    return int(t.get("tries", 0) or 0), t.get("status") in PASSED


def attempts(tasks: list[dict], agent: str) -> list[int]:
    """The agent's Vigil outcomes, oldest first: 0 = FIX, 1 = PASS (fixes come before the pass)."""
    seq = []
    for t in sorted((t for t in tasks if t.get("owner") == agent), key=lambda t: (t.get("updated", ""), t.get("id", ""))):
        fixes, ok = task_state(t)
        seq += [0] * fixes + ([1] if ok else [])
    return seq


def score_agents(tasks: list[dict], last_n: int = DEFAULTS["last_n"]) -> dict[str, dict]:
    """{agent: {rate, n, passes}} over each agent's last `last_n` attempts. Agents with 0 attempts are left out."""
    scores = {}
    for agent in sorted({t["owner"] for t in tasks if t.get("owner")}):
        seq = attempts(tasks, agent)[-last_n:]
        if seq:
            scores[agent] = {"rate": sum(seq) / len(seq), "n": len(seq), "passes": sum(seq)}
    return scores


# ---------------------------------------------------------------- Darwinian weights
def darwin_update(weights: dict[str, float], scores: dict[str, dict]) -> dict[str, float]:
    new = {a: min(max(float(w), W_MIN), W_MAX) for a, w in weights.items()}
    for a in scores:
        new.setdefault(a, W_START)
    ranked = sorted(scores, key=lambda a: (scores[a]["rate"], a))
    if len(ranked) < 2 or scores[ranked[0]]["rate"] == scores[ranked[-1]]["rate"]:
        return new
    k = max(1, len(ranked) // 4)
    for a in ranked[:k]:
        new[a] = max(W_MIN, new[a] * DOWN)
    for a in ranked[-k:]:
        new[a] = min(W_MAX, new[a] * UP)
    return new


# ---------------------------------------------------------------- safety checks
def check_line(line: str, existing: list[str] = ()) -> list[str]:
    """Problems with a proposed playbook line; empty list = allowed."""
    probs = []
    if not isinstance(line, str) or not line.strip():
        return ["empty line"]
    if "\n" in line.strip() or "\r" in line:
        probs.append("must be exactly one line")
    if len(line) > MAX_LINE:
        probs.append(f"longer than {MAX_LINE} characters")
    m = BANNED.search(line)
    if m:
        probs.append(f"could weaken Kalpa rules or game Vigil ('{m.group(0)}')")
    if line.strip() in (e.strip() for e in existing):
        probs.append("already in the playbook overlay")
    return probs


def rules_intact(prompt: str) -> bool:
    """True if every line of runner.RULES is still inside `prompt` word for word."""
    return all(l.strip() in prompt for l in RULES.splitlines() if l.strip())


def overlay(ledger: dict, agent: str) -> list[str]:
    """Lines the agent should get on top of its playbook: kept lines + the pending trial line."""
    lines = list(ledger.get("overlays", {}).get(agent, []))
    lines += [e["change"]["line"] for e in ledger.get("experiments", [])
              if e["agent"] == agent and e["status"] == "pending"]
    return lines


def compose(base_prompt: str, agent: str, ledger: dict) -> str:
    """How runner.py should use the overlay once switched on. Never removes anything."""
    lines = overlay(ledger, agent)
    if not lines:
        return base_prompt
    out = base_prompt + "\n\nLEARNED NOTES (autoresearch, additive; KALPA RULES above always win):\n" + \
        "\n".join(f"- {l}" for l in lines)
    if RULES in base_prompt and not rules_intact(out):
        raise AssertionError("KALPA RULES text went missing")
    return out


# ---------------------------------------------------------------- ledger
def new_ledger() -> dict:
    return {"version": 1, "credit": CREDIT, "weights": {}, "last_weight_day": None,
            "overlays": {}, "experiments": [], "log": []}


def load_ledger(path: str = LEDGER) -> dict:
    if not os.path.exists(path):
        return new_ledger()
    with open(path, encoding="utf-8") as f:
        led = json.load(f)
    for k, v in new_ledger().items():
        led.setdefault(k, v)
    return led


def save_ledger(led: dict, path: str = LEDGER) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(led, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def log(led: dict, at: datetime, event: str, **kw) -> str:
    led["log"].append({"at": iso(at), "event": event, **kw})
    detail = ", ".join(f"{k}={v}" for k, v in kw.items())
    return f"{event}: {detail}"


# ---------------------------------------------------------------- experiments
def snapshot(tasks: list[dict], agent: str) -> dict:
    return {t["id"]: list(task_state(t)) for t in tasks if t.get("owner") == agent and t.get("id")}


def new_outcomes(exp: dict, tasks: list[dict]) -> tuple[int, int]:
    """(passes, attempts) the agent made since the experiment started."""
    p = n = 0
    for t in tasks:
        if t.get("owner") != exp["agent"] or not t.get("id"):
            continue
        fixes, ok = task_state(t)
        f0, ok0 = exp["snapshot"].get(t["id"], [0, False])
        df, dp = max(0, fixes - f0), int(ok and not ok0)
        p, n = p + dp, n + df + dp
    return p, n


def propose_line(tasks: list[dict], agent: str, existing: list[str]) -> str:
    notes = " ".join(t.get("vigil_notes", "") for t in tasks if t.get("owner") == agent).lower()
    ranked = sorted(THEMES, key=lambda th: -len(re.findall(th[0], notes)))
    for pat, line in ranked:
        if re.search(pat, notes) and line not in existing:
            return line
    return GENERIC if GENERIC not in existing else ""


def choose_worst(scores: dict, led: dict, at: datetime, min_attempts: int, cooldown_days: int):
    busy, recent = set(), set()
    for e in led["experiments"]:
        if e["status"] == "pending":
            busy.add(e["agent"])
        if at - parse(e["started"]) < timedelta(days=cooldown_days):
            recent.add(e["agent"])
    pool = [a for a, s in scores.items() if s["n"] >= min_attempts and a not in busy | recent and s["rate"] < 1.0]
    return min(pool, key=lambda a: (scores[a]["rate"], -scores[a]["n"], a)) if pool else None


def start_experiment(led: dict, tasks: list[dict], agent: str, line: str, baseline: dict, at: datetime) -> tuple[bool, str]:
    if any(e["agent"] == agent and e["status"] == "pending" for e in led["experiments"]):
        return False, log(led, at, "refused", agent=agent, why="already has a pending experiment (one change per agent)")
    probs = check_line(line, overlay(led, agent))
    if probs:
        return False, log(led, at, "refused", agent=agent, line=line, why="; ".join(probs))
    exp = {"id": f"AR{len(led['experiments']) + 1:03d}", "agent": agent, "status": "pending",
           "change": {"op": "add", "line": line.strip()}, "baseline": baseline,
           "snapshot": snapshot(tasks, agent), "started": iso(at)}
    led["experiments"].append(exp)
    return True, log(led, at, "started", id=exp["id"], agent=agent, line=exp["change"]["line"],
                     baseline_rate=round(baseline["rate"], 3), baseline_n=baseline["n"])


def evaluate(led: dict, tasks: list[dict], at: datetime, eval_runs: int, stale_days: int) -> list[str]:
    msgs = []
    for e in led["experiments"]:
        if e["status"] != "pending":
            continue
        p, n = new_outcomes(e, tasks)
        if n >= eval_runs:
            rate = p / n
            keep = rate > e["baseline"]["rate"] and not check_line(e["change"]["line"])
            e.update(status="kept" if keep else "reverted", decided=iso(at), result={"rate": rate, "n": n})
            if keep:
                led["overlays"].setdefault(e["agent"], []).append(e["change"]["line"])
            msgs.append(log(led, at, e["status"], id=e["id"], agent=e["agent"], rate=round(rate, 3), n=n,
                            baseline=round(e["baseline"]["rate"], 3)))
        elif at - parse(e["started"]) > timedelta(days=stale_days):
            e.update(status="reverted", decided=iso(at), result={"rate": (p / n) if n else None, "n": n})
            msgs.append(log(led, at, "reverted", id=e["id"], agent=e["agent"], why=f"stale: {n} attempts in {stale_days} days"))
        else:
            msgs.append(f"waiting: {e['id']} {e['agent']} has {n}/{eval_runs} new attempts")
    return msgs


def run_cycle(led: dict, tasks: list[dict], at: datetime, *, propose: str | None = None, **cfg) -> list[str]:
    c = {**DEFAULTS, **cfg}
    scores = score_agents(tasks, c["last_n"])
    msgs = [f"scores (last {c['last_n']} attempts): " + (", ".join(
        f"{a} {s['passes']}/{s['n']}" for a, s in sorted(scores.items(), key=lambda kv: kv[1]['rate'])) or "none")]
    day = at.strftime("%Y-%m-%d")
    if led.get("last_weight_day") != day:
        before = dict(led["weights"])
        led["weights"] = darwin_update(led["weights"], scores)
        led["last_weight_day"] = day
        moved = {a: round(w, 4) for a, w in led["weights"].items() if before.get(a, W_START) != w}
        msgs.append(log(led, at, "weights", moved=moved or "none"))
    else:
        msgs.append(f"weights: already updated today ({day})")
    msgs += evaluate(led, tasks, at, c["eval_runs"], c["stale_days"])
    worst = choose_worst(scores, led, at, c["min_attempts"], c["cooldown_days"])
    if not worst:
        msgs.append(f"no new experiment: no agent with >= {c['min_attempts']} attempts, below 100%, free and out of cooldown")
        return msgs
    line = propose if propose is not None else propose_line(tasks, worst, overlay(led, worst))
    if not line:
        msgs.append(log(led, at, "refused", agent=worst, why="no new line to propose"))
        return msgs
    msgs.append(start_experiment(led, tasks, worst, line, scores[worst], at)[1])
    return msgs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="print what would happen, save nothing (default)")
    g.add_argument("--write", action="store_true", help="run the cycle and save the ledger")
    ap.add_argument("--propose", help="the one line to try on the worst agent (else picked from Vigil notes)")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--ledger", default=LEDGER)
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=int, default=v)
    a = ap.parse_args(argv)
    led = load_ledger(a.ledger)
    msgs = run_cycle(led, load_tasks(a.root), now_utc(), propose=a.propose,
                     **{k: getattr(a, k) for k in DEFAULTS})
    print(("DRY RUN (nothing saved)" if not a.write else f"WRITE -> {os.path.relpath(a.ledger, a.root)}"))
    for m in msgs:
        print(" -", m)
    if a.write:
        save_ledger(led, a.ledger)
    return 0


if __name__ == "__main__":
    sys.exit(main())
