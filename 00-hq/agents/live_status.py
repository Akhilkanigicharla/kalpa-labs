"""Live agent rooms for the CEO Room (Cloudflare D1 `kalpa-live`).

Builds one row per robot (worker agents from the world queues, Vigil, the Claude builder)
and one per GitHub Actions machine, then prints SQL that replaces the D1 tables.

  python3 00-hq/agents/live_status.py --sql   > /tmp/live.sql   # refresh D1 with this
  python3 00-hq/agents/live_status.py --json                    # inspect

GitHub runs come from the public API (repo is public; GITHUB_TOKEN used if set).
No secrets are read or printed.
"""
import datetime as dt, glob, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = "Akhilkanigicharla/kalpa-labs"
ROOMS = ["hq", "b1", "b2", "b3", "b4", "b5", "b6", "b7"]
STATE = {"todo": "queued", "doing": "working", "review": "needs review",
         "done": "done", "rejected": "redo"}
# Which room each GitHub workflow belongs to (default hq).
WF_ROOM = [(r"telugu|voice|botbhai|whatsapp", "b1"), (r"jobcard|b2", "b2"), (r"kit", "b3"),
           (r"lifeboat|tab", "b4"), (r"deal|b5", "b5"), (r"ledger|finops|b6", "b6"),
           (r"backtest|trading|b7", "b7")]
WORKING_MIN = 30  # a log entry newer than this means the Claude builder is working now


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_tasks(root=ROOT):
    out = {}
    for f in sorted(glob.glob(str(root / "00-hq/tasks/*.json"))):
        d = json.load(open(f))
        out[Path(f).stem] = d if isinstance(d, list) else d.get("tasks", [])
    return out


def worker_rows(tasks, agents_running=False):
    """One robot per (room, owner): its newest job decides its state."""
    rows = {}
    for room, items in tasks.items():
        for t in items:
            owner = t.get("owner") or "Agent"
            key = f"{room}:{owner.lower()}"
            when = t.get("updated") or t.get("created") or ""
            old = rows.get(key)
            # an open job (todo/doing) beats a finished one; otherwise the newest wins
            open_ = t.get("status") in ("todo", "doing")
            if old and (old["_open"] and not open_ or (old["_open"] == open_ and old["updated_at"] >= when)):
                continue
            state = STATE.get(t.get("status"), t.get("status") or "idle")
            if agents_running and t.get("status") == "todo":
                state = "working"
            rows[key] = {"id": key, "name": owner, "room": room, "team": "free-model agent",
                         "runs_as": "free models (GitHub Actions)", "state": state,
                         "task": (t.get("title") or "")[:140], "detail": t.get("id", ""),
                         "updated_at": when, "_open": open_}
    for r in rows.values():
        r.pop("_open")
    return sorted(rows.values(), key=lambda r: (ROOMS.index(r["room"]) if r["room"] in ROOMS else 99, r["name"]))


def claude_row(root=ROOT, t=None):
    t = t or now()
    logs = sorted(glob.glob(str(root / "00-hq/log/20*.md")))
    task, when = "No session logged yet", ""
    if logs:
        text = open(logs[-1], encoding="utf-8").read()
        heads = re.findall(r"^## (\d{1,2}:\d{2})\s*(.*)$", text, re.M)
        day = Path(logs[-1]).stem
        if heads:
            hh, title = heads[-1]
            task = re.sub(r"[*`]", "", title).strip()[:140] or "Build session"
            local = dt.datetime.strptime(f"{day} {hh}", "%Y-%m-%d %H:%M").replace(
                tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30)))
            when = iso(local)
    fresh = bool(when) and (t - dt.datetime.fromisoformat(when.replace("Z", "+00:00"))).total_seconds() < WORKING_MIN * 60
    return {"id": "hq:claude", "name": "Claude (builder)", "room": "hq", "team": "build", "runs_as": "Claude cloud session",
            "state": "working" if fresh else "idle", "task": task, "detail": "00-hq/log", "updated_at": when}


def vigil_row(tasks):
    checked = [t for items in tasks.values() for t in items if t.get("status") in ("review", "rejected", "done")]
    last = max((t.get("updated") or "" for t in checked), default="")
    return {"id": "hq:vigil", "name": "Vigil", "room": "hq", "team": "quality check", "runs_as": "free models (GitHub Actions)",
            "state": "idle", "task": f"Checked {len(checked)} drafts against Kalpa rules", "detail": "runner.py",
            "updated_at": last}


def wf_room(name):
    for pat, room in WF_ROOM:
        if re.search(pat, name or "", re.I):
            return room
    return "hq"


def fetch_runs(n=30):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/runs?per_page={n}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "kalpa-live"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("workflow_runs", [])


def run_rows(runs):
    """Latest run per workflow = one machine."""
    seen, out = set(), []
    for r in runs:
        name = r.get("name") or "workflow"
        if name in seen:
            continue
        seen.add(name)
        out.append({"id": str(r.get("workflow_id") or name), "workflow": name, "room": wf_room(name),
                    "status": r.get("status") or "", "conclusion": r.get("conclusion") or "",
                    "started_at": r.get("run_started_at") or r.get("created_at") or "",
                    "url": r.get("html_url") or ""})
    return out


def roles_on_paper(root=ROOT):
    try:
        out = subprocess.run(["node", "-e", "const r=require('./00-hq/agents/registry.js');const c={};"
                              "r.AGENTS.forEach(a=>c[a.unit]=(c[a.unit]||0)+1);console.log(JSON.stringify(c))"],
                             cwd=root, capture_output=True, text=True, timeout=20)
        return json.loads(out.stdout)
    except Exception:
        return {}


def q(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def to_sql(agents, runs, meta):
    """One DELETE + one multi-row INSERT per table (short D1 replies)."""
    def ins(table, rows, cols):
        if not rows:
            return []
        vals = ",\n".join("(" + ",".join(q(r[c]) for c in cols) + ")" for r in rows)
        return [f"INSERT INTO {table} VALUES\n{vals};"]
    s = ["DELETE FROM agents_live;", "DELETE FROM runs_live;", "DELETE FROM live_meta;"]
    s += ins("agents_live", agents, ("id", "name", "room", "team", "runs_as", "state", "task", "detail", "updated_at"))
    s += ins("runs_live", runs, ("id", "workflow", "room", "status", "conclusion", "started_at", "url"))
    s += ins("live_meta", [{"k": k, "v": v} for k, v in meta.items()], ("k", "v"))
    return "\n".join(s)


def build(root=ROOT, runs=None, t=None):
    tasks = load_tasks(root)
    runs = run_rows(runs or [])
    agents_running = any(r["status"] in ("in_progress", "queued") and re.search(r"agent", r["workflow"], re.I) for r in runs)
    agents = worker_rows(tasks, agents_running) + [vigil_row(tasks), claude_row(root, t)]
    meta = {"refreshed_at": iso(t or now())}
    for room, n in roles_on_paper(root).items():
        meta[f"roles_{room}"] = n
    return agents, runs, meta


def main(argv):
    try:
        raw = fetch_runs()
    except Exception as e:  # keep the robots even if GitHub is unreachable
        print(f"github runs unavailable: {type(e).__name__}", file=sys.stderr)
        raw = []
    agents, runs, meta = build(runs=raw)
    if "--json" in argv:
        print(json.dumps({"agents": agents, "runs": runs, "meta": meta}, indent=1))
    else:
        print(to_sql(agents, runs, meta))


if __name__ == "__main__":
    main(sys.argv[1:])
