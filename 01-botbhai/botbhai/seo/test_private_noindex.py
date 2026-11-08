"""A193: every private BotBhai screen, sales paper and PDF in web/dist gets an X-Robots-Tag noindex header in netlify.toml.
Public: only index.html and widget.js. Run: python3 seo/test_private_noindex.py (after build.py)."""
import fnmatch, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = {"index.html", "widget.js"}
toml = (ROOT / "netlify.toml").read_text()
rules = re.findall(r'for = "([^"]+)"\s*\[headers\.values\]\s*X-Robots-Tag = "noindex', toml)
missing = []
for f in (ROOT / "web/dist").rglob("*"):
    if f.is_dir():
        continue
    rel = "/" + f.relative_to(ROOT / "web/dist").as_posix()
    if rel.lstrip("/") in PUBLIC or not re.search(r"\.(html|pdf)$", rel):
        continue
    if not any(fnmatch.fnmatch(rel, r) for r in rules):
        missing.append(rel)
for m in missing:
    print("FAIL no noindex header for", m)
print("PASS private pages noindex" if not missing else f"{len(missing)} private file(s) could show up in Google")
sys.exit(1 if missing else 0)
