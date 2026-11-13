#!/usr/bin/env python3
"""A146: bond GitHub with the self-hosted n8n (runs in GitHub Actions; the API key never leaves GitHub secrets).

1. Creates n8n credentials from GitHub secrets (Groq, OpenRouter, Telegram) once, so Akhil does not re-type keys.
2. Imports/updates every workflow in 00-hq/n8n-selfhost/workflows/*.json (matched by name) and activates it.
Env: N8N_SELF_URL, N8N_SELF_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, TELEGRAM_BOT_TOKEN. Standard library only.
"""
import glob, json, os, sys, urllib.request, urllib.error

BASE = os.environ.get("N8N_SELF_URL", "").rstrip("/") + "/api/v1"
KEY = os.environ.get("N8N_SELF_API_KEY", "")
HERE = os.path.dirname(os.path.abspath(__file__))

CREDS = [  # (n8n credential name, type, data builder, env var)
    ("Kalpa Groq", "groqApi", lambda v: {"apiKey": v}, "GROQ_API_KEY"),
    ("Kalpa OpenRouter", "openRouterApi", lambda v: {"apiKey": v}, "OPENROUTER_API_KEY"),
    ("Kalpa Telegram", "telegramApi", lambda v: {"accessToken": v}, "TELEGRAM_BOT_TOKEN"),
    ("Kalpa Groq header", "httpHeaderAuth", lambda v: {"name": "Authorization", "value": "Bearer " + v}, "GROQ_API_KEY"),
    ("Kalpa OpenRouter header", "httpHeaderAuth", lambda v: {"name": "Authorization", "value": "Bearer " + v}, "OPENROUTER_API_KEY"),
    ("Kalpa Gemini header", "httpHeaderAuth", lambda v: {"name": "Authorization", "value": "Bearer " + v}, "GEMINI_API_KEY"),
]


def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"X-N8N-API-KEY": KEY, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def existing_credentials():
    """Our credentials by name. If one of OUR names (Kalpa …) exists twice, the older copies are deleted (4 Nov duplicates)."""
    st, body = api("GET", "/credentials?limit=250")
    if st != 200:
        return None
    ours = {c[0] for c in CREDS}
    out = {}
    for c in sorted(body.get("data", []), key=lambda c: c.get("createdAt", ""), reverse=True):  # newest first
        name = c["name"]
        if name not in out:
            out[name] = c["id"]
        elif name in ours:
            st2, _ = api("DELETE", f"/credentials/{c['id']}")
            print(f"duplicate {name} (older copy) deleted: HTTP {st2}")
    return out


def sync_credentials():
    have = existing_credentials()
    ids = {}
    for name, ctype, build, env in CREDS:
        if have is not None and name in have:
            ids[name] = have[name]; print(f"credential ok: {name}"); continue
        if have is None and os.environ.get("KL_CREATE_CREDS") != "yes":
            print(f"credential {name}: cannot list credentials on this n8n; run with create_credentials=yes once"); continue
        if not os.environ.get(env):
            print(f"credential {name}: GitHub secret {env} missing, skipped"); continue
        st, body = api("POST", "/credentials", {"name": name, "type": ctype, "data": build(os.environ[env])})
        print(f"credential {name}: HTTP {st}" + ("" if st < 300 else f" {body.get('error', '')[:160]}"))
        if st < 300:
            ids[name] = body.get("id")
    return ids


def sync_workflows(cred_ids):
    st, body = api("GET", "/workflows?limit=250")
    if st != 200:
        print(f"cannot list workflows: HTTP {st} {body}"); return 1
    have = {w["name"]: w["id"] for w in body.get("data", [])}
    bad = 0
    for path in sorted(glob.glob(os.path.join(HERE, "workflows", "*.json"))):
        wf = json.load(open(path, encoding="utf-8"))
        need = {ref.get("name") for n in wf["nodes"] for ref in (n.get("credentials") or {}).values()}
        missing = sorted(x for x in need if x not in cred_ids)
        if missing:  # never replace a working workflow with one whose keys are not in n8n yet
            print(f"workflow {wf['name']}: waiting for credential(s) {', '.join(missing)} (add the GitHub secret, then re-run)")
            continue
        for node in wf["nodes"]:  # point credential references at this instance's ids
            for ctype, ref in (node.get("credentials") or {}).items():
                if ref.get("name") in cred_ids:
                    ref["id"] = cred_ids[ref["name"]]
        payload = {k: wf[k] for k in ("name", "nodes", "connections", "settings")}
        if wf["name"] in have:
            wid = have[wf["name"]]; st, res = api("PUT", f"/workflows/{wid}", payload)
        else:
            st, res = api("POST", "/workflows", payload); wid = res.get("id")
        ok = st < 300
        if ok and wf.get("active", True):
            st2, res2 = api("POST", f"/workflows/{wid}/activate")
            ok = st2 < 300
            if not ok:
                res = res2
        print(f"workflow {wf['name']}: {'ok' if ok else 'FAILED ' + str(res)[:200]}")
        bad += not ok
    return bad


def show_runs(limit=15):
    """Print the latest executions (workflow, status, start) so a sprint can prove a scheduled run happened."""
    st, wfs = api("GET", "/workflows?limit=250")
    st2, ex = api("GET", f"/executions?limit={limit}")
    if st != 200 or st2 != 200:
        print(f"cannot read runs: HTTP {st}/{st2}"); return 1
    names = {w["id"]: w["name"] for w in wfs.get("data", [])}
    for e in ex.get("data", []):
        print(f"run {names.get(e.get('workflowId'), e.get('workflowId'))} | {e.get('status')} | {e.get('startedAt')}")
    return 0


if __name__ == "__main__":
    if not (BASE.startswith("http") and KEY):
        print("N8N_SELF_URL / N8N_SELF_API_KEY not set"); sys.exit(1)
    if "--runs" in sys.argv:
        sys.exit(show_runs())
    sys.exit(1 if sync_workflows(sync_credentials()) else 0)
