#!/usr/bin/env python3
"""CLAUDE.md rule 5 for BotBhai web: run the Kalpa tap sweep (00-hq/site/tests/test_tap_sweep.py: 390 px, light + dark,
nothing covered or off-screen, taps at least 44 px) on every built screen in web/dist. Run after build.py; needs Playwright."""
import functools, http.server, pathlib, subprocess, sys, threading

here = pathlib.Path(__file__).resolve()
dist = here.parents[1] / "web" / "dist"
sweep = here.parents[3] / "00-hq" / "site" / "tests" / "test_tap_sweep.py"
PAGES = ["index.html", "dashboard.html?demo=1", "inbox.html?demo=1", "inbox.html?demo=1&open=919812345678", "billing.html?demo=1"]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(dist)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}/"
bad = []
for page in PAGES:
    r = subprocess.run([sys.executable, str(sweep), base + page], capture_output=True, text=True, timeout=300)
    last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    print(f"  {page}: {last}")
    if r.returncode or "PASS" not in last:
        bad.append(page); print("\n".join(l for l in r.stdout.splitlines() if l.startswith("FAIL"))[:2000])
srv.shutdown()
sys.exit(f"tap sweep failed: {bad}" if bad else 0)
