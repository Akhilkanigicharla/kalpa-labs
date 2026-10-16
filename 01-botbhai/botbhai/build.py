"""Builds the BotBhai web app (customer chat + voice + owner dashboard).
   python3 build.py            → all four setups (sales demo)
   python3 build.py salon      → one industry site (what a salon client gets)
Also refreshes setups/*/bot.config.json for the Python voice agent."""
import json, os, pathlib, shutil, subprocess, sys
root = pathlib.Path(__file__).parent
only = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("SETUP", "")).strip()
setups = [only] if only else ["salon", "realestate", "gym", "examkits"]
cfgs = json.loads(subprocess.check_output(["node", "-e", """
const { SETUPS } = require('./setups/index.js');
process.stdout.write(JSON.stringify(SETUPS));"""], cwd=root))
for k, c in cfgs.items():
    c2 = {x: y for x, y in c.items() if x != "quizBank"}
    (root / "setups" / k / "bot.config.json").write_text(json.dumps(c2, indent=2, ensure_ascii=False))
register = "\n".join(f"BotBhai.register({json.dumps(cfgs[s], ensure_ascii=False)});" for s in setups)
page = (root / "web" / "index.src.html").read_text().replace("/*ENGINE*/", (root / "core" / "engine.js").read_text() + "\n" + register)
dist = root / "web" / "dist"; dist.mkdir(parents=True, exist_ok=True)
head = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
(dist / "index.html").write_text(head + page + "</body></html>")
(dist / "artifact.html").write_text(page)
shutil.copy(root / "web" / "widget.js", dist / "widget.js")
shutil.copy(root / "web" / "inbox.html", dist / "inbox.html")  # shared inbox (A04); calls /.netlify/functions/inbox
subprocess.check_call([sys.executable, str(root / "tools" / "cards.py"), "--all-demo", "--out", str(dist / "cards" / "demo")], stdout=subprocess.DEVNULL)
print("built", ", ".join(setups), "+ smile cards →", dist)
