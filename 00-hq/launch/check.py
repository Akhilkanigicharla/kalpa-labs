#!/usr/bin/env python3
"""Kalpa launch readiness board (A57). Standard library only.

Reads 00-hq/launch/readiness.json (the 5 launch offers + 6 production-grade
rules from 00-hq/SOFT-LAUNCH.md), runs every row's checks and prints a board.
A row is green only when all of its checks pass. Exit 0 = all green, 1 = any
red, 2 = bad config.

    python3 00-hq/launch/check.py            # board
    python3 00-hq/launch/check.py --json     # same data for the dashboard (A63)

Check kinds (the "checks" list of each row):
  roadmap  {"items": ["C02", ...]}           each item is [x] in 00-hq/ROADMAP.md
  audit    {"dir", "max_age_days"}           newest audit report has 0 open WRONG rows
                                             (a WRONG row is closed when every A/C id in
                                             its Fix cell is [x] in the roadmap)
  ci       {"repo", "workflow", "branch"}    latest completed run is "success";
                                             GitHub REST API, only if GITHUB_TOKEN is set,
                                             else "unknown" (red)
  smoke    {"path", "targets", "max_age_hours"}  results file written by the A61 workflow:
                                             {"at": ISO-8601, "results": [{"name", "ok", "detail"}]}
  fresh    {"path", "max_age_days"}          JSON file with an "at" stamp, not too old
  env      {"names": [...]}                  env vars present, checked by NAME only
  file     {"path", "contains": [...]}       file exists and holds each word (any case)
  cmd      {"run": [argv...], "timeout"}     local test command exits 0 (no shell)

Secrets: env values and GITHUB_TOKEN are never printed or stored.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IST = timezone(timedelta(hours=5, minutes=30))
KINDS = ("roadmap", "audit", "ci", "smoke", "fresh", "env", "file", "cmd")
AUDIT_NAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{4})\.md$")
ROADMAP_LINE = re.compile(r"^- \[(.)\] \*\*([A-Z]+\d+)\*\*", re.M)


class Ctx:
    def __init__(self, root, env, now, http=None):
        self.root, self.env, self.now = root, env, now
        self.http = http or http_get_json
        self._roadmap = None

    def path(self, rel):
        return os.path.join(self.root, rel)

    def roadmap(self):
        if self._roadmap is None:
            try:
                with open(self.path("00-hq/ROADMAP.md"), encoding="utf-8") as f:
                    self._roadmap = {m[1]: m[0] for m in ROADMAP_LINE.findall(f.read())}
            except OSError:
                self._roadmap = {}
        return self._roadmap


def http_get_json(url, token):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "kalpa-readiness",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def parse_time(s):
    t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=IST)


def age_text(delta):
    h = delta.total_seconds() / 3600
    return f"{h:.0f} h" if h < 48 else f"{h / 24:.0f} days"


# ---- checks: each returns (ok, reason) ----

def check_roadmap(spec, ctx):
    status = ctx.roadmap()
    if not status:
        return False, "00-hq/ROADMAP.md not readable"
    todo = [i for i in spec["items"] if status.get(i) != "x"]
    if todo:
        return False, "not done: " + ", ".join(
            i if i in status else i + " (not in roadmap)" for i in todo)
    return True, "done: " + ", ".join(spec["items"])


def check_audit(spec, ctx):
    d = ctx.path(spec.get("dir", "00-hq/audit"))
    names = sorted(n for n in os.listdir(d) if AUDIT_NAME.match(n)) if os.path.isdir(d) else []
    if not names:
        return False, "no audit report yet"
    newest = names[-1]
    y, mo, da, hm = AUDIT_NAME.match(newest).groups()
    at = datetime(int(y), int(mo), int(da), int(hm[:2]), int(hm[2:]), tzinfo=IST)
    max_age = spec.get("max_age_days")
    if max_age is not None and ctx.now - at > timedelta(days=max_age):
        return False, f"{newest} is {age_text(ctx.now - at)} old (max {max_age} days)"
    with open(os.path.join(d, newest), encoding="utf-8") as f:
        text = f.read()
    status = ctx.roadmap()
    open_rows = []
    verdict_col = fix_col = None
    for line in text.splitlines():
        if not line.startswith("|"):
            verdict_col = fix_col = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        low = [c.lower() for c in cells]
        if "verdict" in low:
            verdict_col = low.index("verdict")
            fix_col = low.index("fix") if "fix" in low else None
            continue
        if verdict_col is None or verdict_col >= len(cells) or "WRONG" not in cells[verdict_col]:
            continue
        fix = cells[fix_col] if fix_col is not None and fix_col < len(cells) else ""
        ids = re.findall(r"\b[AC]\d+\b", fix)
        pending = [i for i in ids if status.get(i) != "x"]
        if not ids or pending:
            open_rows.append(f"#{cells[0]} ({', '.join(pending) or 'no fix item'})")
    if open_rows:
        return False, f"{len(open_rows)} WRONG open in {newest}: " + "; ".join(open_rows)
    return True, f"0 WRONG open in {newest}"


def check_ci(spec, ctx):
    token = ctx.env.get("GITHUB_TOKEN")
    if not token:
        return False, "unknown: GITHUB_TOKEN not set"
    url = ("https://api.github.com/repos/{repo}/actions/workflows/{wf}/runs"
           "?branch={br}&status=completed&per_page=1&exclude_pull_requests=true").format(
        repo=spec["repo"], wf=spec["workflow"], br=spec.get("branch", "main"))
    try:
        runs = ctx.http(url, token).get("workflow_runs") or []
    except (urllib.error.URLError, OSError, ValueError) as e:
        return False, f"unknown: GitHub API error ({type(e).__name__})"
    if not runs:
        return False, "unknown: no completed run on " + spec.get("branch", "main")
    run = runs[0]
    sha = str(run.get("head_sha", ""))[:7]
    concl = run.get("conclusion")
    return concl == "success", f"{spec['workflow']} on {sha}: {concl}"


def load_json(ctx, rel):
    with open(ctx.path(rel), encoding="utf-8") as f:
        return json.load(f)


def check_smoke(spec, ctx):
    path = spec.get("path", "00-hq/launch/smoke-results.json")
    if not os.path.exists(ctx.path(path)):
        return False, "no smoke results yet"
    try:
        data = load_json(ctx, path)
        at = parse_time(data["at"])
        results = {r["name"]: r for r in data["results"]}
    except (ValueError, KeyError, TypeError) as e:
        return False, f"bad smoke results file ({type(e).__name__})"
    max_h = spec.get("max_age_hours", 12)
    if ctx.now - at > timedelta(hours=max_h):
        return False, f"smoke results {age_text(ctx.now - at)} old (max {max_h} h)"
    bad = []
    for t in spec["targets"]:
        r = results.get(t)
        if r is None:
            bad.append(t + ": no result")
        elif r.get("ok") is not True:
            bad.append(f"{t}: {r.get('detail') or 'failed'}")
    if bad:
        return False, "; ".join(bad)
    return True, f"{len(spec['targets'])} passed, {age_text(ctx.now - at)} ago"


def check_fresh(spec, ctx):
    path = spec["path"]
    if not os.path.exists(ctx.path(path)):
        return False, "missing " + path
    try:
        at = parse_time(load_json(ctx, path)["at"])
    except (ValueError, KeyError, TypeError) as e:
        return False, f"bad {path} ({type(e).__name__})"
    max_d = spec.get("max_age_days", 8)
    if ctx.now - at > timedelta(days=max_d):
        return False, f"{path} {age_text(ctx.now - at)} old (max {max_d} days)"
    return True, f"{path} {age_text(ctx.now - at)} old"


def check_env(spec, ctx):
    missing = [n for n in spec["names"] if not ctx.env.get(n)]
    if missing:
        return False, "env not set: " + ", ".join(missing)
    return True, f"{len(spec['names'])} env names set"


def check_file(spec, ctx):
    path = spec["path"]
    if not os.path.isfile(ctx.path(path)):
        return False, "missing " + path
    if not spec.get("contains"):
        return True, path + " present"   # existence only (PDF, xlsx, ...)
    with open(ctx.path(path), encoding="utf-8", errors="replace") as f:
        text = f.read().lower()
    lacks = [w for w in spec.get("contains", []) if w.lower() not in text]
    if lacks:
        return False, f"{path} lacks: " + ", ".join(lacks)
    return True, path + " has " + ", ".join(spec["contains"])


def check_cmd(spec, ctx):
    argv = [sys.executable if a == "python3" else a for a in spec["run"]]
    label = " ".join(spec["run"])
    try:
        p = subprocess.run(argv, cwd=ctx.root, capture_output=True, text=True,
                           timeout=spec.get("timeout", 120))
    except FileNotFoundError:
        return False, label + ": command not found"
    except subprocess.TimeoutExpired:
        return False, label + ": timed out"
    if p.returncode == 0:
        return True, label + ": passed"
    tail = (p.stdout + p.stderr).strip().splitlines()
    return False, f"{label}: exit {p.returncode}" + (f" ({tail[-1][:80]})" if tail else "")


CHECKS = {k: globals()["check_" + k] for k in KINDS}


def validate(cfg):
    rows = cfg.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("readiness.json needs a non-empty 'rows' list")
    seen = set()
    for r in rows:
        for key in ("id", "label", "kind", "checks"):
            if key not in r:
                raise ValueError(f"row {r.get('id', '?')} lacks '{key}'")
        if r["id"] in seen:
            raise ValueError("duplicate row id " + r["id"])
        seen.add(r["id"])
        if r["kind"] not in ("offer", "rule"):
            raise ValueError(f"row {r['id']}: kind must be offer or rule")
        if not r["checks"]:
            raise ValueError(f"row {r['id']}: no checks")
        for c in r["checks"]:
            if c.get("kind") not in CHECKS:
                raise ValueError(f"row {r['id']}: unknown check kind {c.get('kind')!r}")


def run_board(cfg, ctx):
    validate(cfg)
    rows = []
    for r in cfg["rows"]:
        checks = []
        for c in r["checks"]:
            try:
                ok, reason = CHECKS[c["kind"]](c, ctx)
            except (KeyError, OSError, ValueError, TypeError) as e:
                ok, reason = False, f"check error ({type(e).__name__}: {e})"
            checks.append({"kind": c["kind"], "ok": ok, "reason": reason})
        rows.append({"id": r["id"], "label": r["label"], "kind": r["kind"],
                     "ok": all(c["ok"] for c in checks), "checks": checks})
    green = sum(r["ok"] for r in rows)
    return {"generated_at": ctx.now.isoformat(timespec="seconds"), "green": green,
            "total": len(rows), "ok": green == len(rows), "rows": rows}


def render(board):
    mark = lambda ok: "✓" if ok else "✗"
    when = parse_time(board["generated_at"]).astimezone(IST).strftime("%d %b %Y %H:%M IST")
    out = [f"Kalpa launch readiness · {when} · {board['green']}/{board['total']} green"]
    for kind, title in (("offer", "Launch offers"), ("rule", "Production-grade rules")):
        out.append("")
        out.append(title)
        for r in (r for r in board["rows"] if r["kind"] == kind):
            out.append(f" {mark(r['ok'])} {r['id']:<3} {r['label']}")
            for c in r["checks"]:
                if not c["ok"]:
                    out.append(f"       ✗ {c['kind']}: {c['reason']}")
    out.append("")
    out.append("READY" if board["ok"] else f"NOT READY: {board['total'] - board['green']} red")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kalpa launch readiness board (A57)")
    ap.add_argument("--json", action="store_true", help="print the board as JSON")
    ap.add_argument("--config", default=os.path.join(HERE, "readiness.json"))
    ap.add_argument("--root", default=ROOT, help="repo root the checks read from")
    a = ap.parse_args(argv)
    try:
        with open(a.config, encoding="utf-8") as f:
            cfg = json.load(f)
        board = run_board(cfg, Ctx(a.root, os.environ, datetime.now(IST)))
    except (OSError, ValueError) as e:
        print(f"readiness config error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(board, ensure_ascii=False, indent=2) if a.json else render(board))
    return 0 if board["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
