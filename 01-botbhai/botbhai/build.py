"""Builds the BotBhai web app (customer chat + voice + owner dashboard).
   python3 build.py            → all four setups (sales demo)
   python3 build.py salon      → one industry site (what a salon client gets)
Also refreshes setups/*/bot.config.json for the Python voice agent."""
import json, os, pathlib, re, shutil, subprocess, sys
root = pathlib.Path(__file__).parent
only = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("SETUP", "")).strip()
setups = [only] if only else ["salon", "realestate", "gym", "examkits"]
cfgs = json.loads(subprocess.check_output(["node", "-e", """
const { SETUPS } = require('./setups/index.js');
process.stdout.write(JSON.stringify(SETUPS));"""], cwd=root))
for k, c in cfgs.items():
    c2 = {x: y for x, y in c.items() if x != "quizBank"}
    (root / "setups" / k / "bot.config.json").write_text(json.dumps(c2, indent=2, ensure_ascii=False), encoding="utf-8")
register = "\n".join(f"BotBhai.register({json.dumps(cfgs[s], ensure_ascii=False)});" for s in setups)
page = (root / "web" / "index.src.html").read_text(encoding="utf-8").replace("/*ENGINE*/", (root / "core" / "engine.js").read_text(encoding="utf-8") + "\n" + register)
dist = root / "web" / "dist"; dist.mkdir(parents=True, exist_ok=True)
head = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
# Served page: the engine + page script go to app.js so the CSP needs no 'unsafe-inline' for scripts (netlify.toml).
# artifact.html (pasted into a Claude artifact, never linked from the site) keeps them inline.
scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
assert len(scripts) == 2, "index.src.html: expected the engine script and the page script"
(dist / "app.js").write_text("\n;\n".join(x.strip("\n") for x in scripts) + "\n", encoding="utf-8")
served = page.replace("<script>" + scripts[0] + "</script>", "").replace("<script>" + scripts[1] + "</script>", '<script src="app.js"></script>')
(dist / "index.html").write_text(head + served + "</body></html>", encoding="utf-8")
(dist / "artifact.html").write_text(page, encoding="utf-8")
shutil.copy(root / "web" / "widget.js", dist / "widget.js")
for js in ("inbox.js", "dashboard.js", "billing.js"): shutil.copy(root / "web" / js, dist / js)  # page scripts (no inline JS: CSP)
shutil.copy(root / "web" / "inbox.html", dist / "inbox.html")  # shared inbox (A04); calls /.netlify/functions/inbox
shutil.copy(root / "web" / "dashboard.html", dist / "dashboard.html")  # owner dashboard (A10); calls /.netlify/functions/leads
shutil.copy(root / "web" / "billing.html", dist / "billing.html")  # Kalpa billing (A05); calls /.netlify/functions/billing
subprocess.check_call(["node", str(root / "tools" / "sample_invoice.js"), str(dist / "invoice-sample.html")])  # sample invoice page
subprocess.check_call([sys.executable, str(root / "tools" / "cards.py"), "--all-demo", "--out", str(dist / "cards" / "demo")], stdout=subprocess.DEVNULL)
print("built", ", ".join(setups), "+ smile cards →", dist)
