"""Kalpa engineering standard checker: runs the machine-checkable rows of
00-hq/design/ENGINEERING-CHECKS.md (107 items) against every world's web code.

Usage:
  python3 00-hq/tools/eng_check.py            # all worlds, table + exit 1 on any FAIL
  python3 00-hq/tools/eng_check.py botbhai    # one world
  python3 00-hq/tools/eng_check.py --md       # also write <world>/design/eng-check.md

What it checks (per world, where it applies):
  security headers  HSTS, nosniff, Referrer-Policy, X-Frame-Options or frame-ancestors, Permissions-Policy, CSP
                    (netlify.toml [[headers]], public/_headers, or <meta http-equiv> for GitHub Pages)
  clickjacking      frame-ancestors 'none' / X-Frame-Options DENY (meta can't do this: GitHub Pages is flagged WARN)
  inline JS vs CSP  inline <script> or on*= handlers that a strict CSP would block
  404 page          a custom 404 exists
  links             target=_blank without rel=noopener; plain http:// links
  secrets           API-key-looking strings in files shipped to the browser
  XSS sinks         innerHTML / document.write / eval with non-constant input in browser JS
  rate limiting     every server function that takes requests mentions a limit or 429
  timeouts          every server fetch() has a timeout or AbortSignal
  input caps        server functions cap input length
  budget            largest page + its JS under 250 KB
Items that need a person or a running system (load test, pen test, backups...) stay in the md file as "manual".
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORLDS = {
    # name: (web folder shipped to browsers, header config files, server function folders, folder for eng-check.md)
    "hq-site": ("00-hq/site", ["00-hq/site/netlify.toml"], ["00-hq/site/netlify/functions"], "00-hq/design"),
    "botbhai": ("01-botbhai/botbhai/web", ["01-botbhai/botbhai/netlify.toml"], ["01-botbhai/botbhai/core/functions"], "01-botbhai/design"),
    "jobcard": ("02-jobcard/web", ["02-jobcard/netlify.toml"], ["02-jobcard/bot/functions"], "02-jobcard/design"),
    "extension-site": ("04-extensions/site", [], [], "04-extensions/design"),
    "extension": ("04-extensions/src/entrypoints", [], [], "04-extensions/design"),
    # Python worlds (no public pages): secrets, timeouts, shell and eval checks only
    "kits": ("03-kits", [], [], "03-kits/design"),
    "finops": ("06-finops/src", [], [], "06-finops/design"),
    "trading": ("07-trading/src", [], [], "07-trading/design"),
    "finops-site": ("06-finops/site/_dist", ["06-finops/site/_dist/_headers"], ["06-finops/src/api"], "06-finops/design"),  # built output: run 06-finops/site/build.py first
    "deals": ("05-deals/site/dist", ["05-deals/site/public/_headers"], ["05-deals/site/functions"], "05-deals/design"),  # built output: run `npm run build` first
}
SKIP = re.compile(r"(node_modules|/dist/|/_dist/|/vendor/|\.test\.|/tests?/|/fixtures/)")
# innerHTML uses read line by line by a person; re-review when these files change a lot (12 Nov 2026)
REVIEWED = {"app.js": "i18n text from our own dictionary + constant markup",
            "app.mjs": "every value goes through esc()",
            "index.src.html": "fmt() escapes first; tables use esc()",
            "widget.js": "constant SVG markup"}
KEY = re.compile(r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9-]{20,}|-----BEGIN (RSA )?PRIVATE KEY)")


def files(folder, exts):
    base = ROOT / folder
    if not base.exists():
        return []
    return [p for p in base.rglob("*") if p.suffix in exts and p.is_file() and not SKIP.search("/" + str(p.relative_to(base)))]


PY = {"kits", "finops", "trading"}


def run_py(name):
    web = WORLDS[name][0]
    res = []
    add = lambda item, ok, note="", warn=False: res.append((item, "PASS" if ok else ("WARN" if warn else "FAIL"), note))
    py = files(web, {".py", ".js", ".gs", ".yml", ".json"})
    leaks = [str(p.relative_to(ROOT)) for p in py if KEY.search(p.read_text(encoding="utf-8", errors="ignore"))]
    add("Secrets Management (no keys in code)", not leaks, ", ".join(leaks[:3]) or "keys only from environment / GitHub secrets")
    nt = []
    for p in py:
        if p.suffix != ".py":
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"requests\.(get|post|put|delete|request)\(", src):
            call = src[m.start(): src.find(")", m.start()) + 200]
            if "timeout" not in call.split("\n\n")[0][:600]:
                nt.append(p.name); break
        if re.search(r"shell\s*=\s*True", src):
            add(f"Command Injection: {p.name}", False, "subprocess with shell=True")
        if re.search(r"(?<![\w.])eval\(|(?<![\w.])exec\(", src):
            add(f"eval/exec: {p.name}", False, "dynamic code")
        if re.search(r"urlopen\((?![^)]*timeout)", src):
            nt.append(p.name)
    add("Timeouts (every HTTP call has timeout=)", not nt, ", ".join(sorted(set(nt))[:5]))
    return res


def run(name):
    if name in PY:
        return run_py(name)
    web, confs, fns, _ = WORLDS[name]
    res = []  # (item, status, note)
    add = lambda item, ok, note="", warn=False: res.append((item, "PASS" if ok else ("WARN" if warn else "FAIL"), note))
    pages = files(web, {".html", ".astro"})
    js = files(web, {".js", ".mjs", ".ts", ".tsx", ".astro", ".html"})
    conf = "\n".join((ROOT / c).read_text(encoding="utf-8") for c in confs if (ROOT / c).exists())
    meta = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in pages)
    meta += "\n".join(f"Referrer-Policy {m}" for m in re.findall(r'<meta name="referrer" content="([^"]+)"', meta))
    hdr = conf + "\n" + "\n".join(f"Referrer-Policy {m}" for m in re.findall(r'<meta name="referrer" content="([^"]+)"', meta)) + "\n" + "\n".join(re.findall(r'<meta http-equiv="([^"]+)" content="([^"]+)"', meta) and
                                  [" ".join(m) for m in re.findall(r'<meta http-equiv="([^"]+)" content="([^"]+)"', meta)] or [])
    is_ext = name == "extension"
    if not is_ext:
        for h in ("Strict-Transport-Security", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"):
            add(f"Security Headers: {h}", h.lower() in hdr.lower(), ("in " if h.lower() in hdr.lower() else "missing in ") + (confs[0] if confs else "page meta"),
                warn=not confs and h != "Referrer-Policy")
        csp = re.search(r'Content-Security-Policy(?:\s*=\s*"|:\s*|\s+)([^"\n]*script-src[^"\n]*)', hdr, re.I)
        add("Content Security Policy", bool(csp), csp.group(1)[:60] if csp else "no CSP")
        click = ("frame-ancestors" in hdr) or re.search(r"X-Frame-Options", conf, re.I)
        add("Clickjacking", bool(click), "frame-ancestors / X-Frame-Options" if click else
            ("GitHub Pages can't send this header; needs a host with headers" if not confs else "missing"), warn=not confs)
        strict = csp and "unsafe-inline" not in csp.group(1).split("script-src")[-1].split(";")[0]
        inline = [p for p in pages if re.search(r"<script(?![^>]*\bsrc=)(?![^>]*(application/ld\+json|application/json|type=\"module\" src))[^>]*>\s*\S", p.read_text(encoding="utf-8", errors="ignore"))]
        add("Inline JS vs CSP", not inline, (f"{len(inline)} page(s) with inline script: " + ", ".join(p.name for p in inline[:4]) +
            ("; CSP allows it for now, move scripts to files" if not strict else "; strict CSP will BLOCK these")) if inline else "none",
            warn=bool(inline) and bool(csp) and not strict)
        handlers = [p.name for p in pages if re.search(r"\son(click|load|error|submit|change|input)=\"", p.read_text(encoding="utf-8", errors="ignore"))]
        add("Inline on*= handlers", not handlers, ", ".join(handlers[:4]))
        spa = re.search(r'from = "/\*"\s*\n\s*to = "/index\.html"\s*\n\s*status = 200', conf)
        has404 = bool(spa) or any(p.name.startswith("404") for p in pages) or (ROOT / web / "404.html").exists() or (ROOT / web / "pages/404.astro").exists()
        add("Custom 404 page", has404, "single-page app: unknown paths open the app" if spa else "" if has404 else "add a 404 page")
    blank = [p.name for p in pages if re.search(r'target="_blank"(?![^>]*rel="[^"]*noopener)', p.read_text(encoding="utf-8", errors="ignore"))]
    add("target=_blank has rel=noopener", not blank, ", ".join(blank[:4]))
    plain = [p.name for p in pages if re.search(r'(href|src)="http://(?!localhost|127\.)', p.read_text(encoding="utf-8", errors="ignore"))]
    add("Encryption in Transit (no http:// links)", not plain, ", ".join(plain[:4]))
    leaks = [str(p.relative_to(ROOT)) for p in js if KEY.search(p.read_text(encoding="utf-8", errors="ignore"))]
    add("Secrets Management (no keys in browser code)", not leaks, ", ".join(leaks[:3]))
    sinks = []
    for p in js:
        for m in re.finditer(r"(\.innerHTML\s*[+]?=\s*(?![`'\"][^`'\"$]*[`'\"]\s*;)|document\.write\(|\beval\()", p.read_text(encoding="utf-8", errors="ignore")):
            sinks.append(p.name)
            break
    todo = sorted(set(x for x in sinks if x not in REVIEWED))
    add("XSS sinks (innerHTML/eval with variables)", not todo, ("review: " + ", ".join(todo[:5])) if todo else
        ("reviewed: " + "; ".join(f"{x}: {REVIEWED[x]}" for x in sorted(set(sinks))) if sinks else ""), warn=bool(todo))
    for fdir in fns:
        for f in files(fdir, {".js", ".mjs", ".ts"}):
            src = f.read_text(encoding="utf-8", errors="ignore")
            if f.name.startswith("_") or not re.search(r"(export default|exports\.handler|export (async )?function (handler|onRequest))", src):
                continue
            rel = str(f.relative_to(ROOT))
            if "fetch(" in src:
                add(f"Timeouts: {rel}", bool(re.search(r"AbortSignal\.timeout|AbortController|timeout", src)), "fetch without timeout")
            sched = re.search(r'\[functions\."' + re.escape(f.stem) + r'"\]\s*\n\s*schedule', conf) or re.search(r"config\s*=\s*\{\s*schedule", src)
            if sched:
                add(f"Rate Limiting: {rel}", True, "scheduled job, no public caller")
            else:
                hook = bool(re.search(r"webhook|hub\.verify|x-hub-signature|secret_token|X-Telegram", src, re.I))
                add(f"Rate Limiting: {rel}", bool(re.search(r"429|rate.?limit|limited\(", src, re.I)),
                    "webhook: platform-signed, rate set by sender" if hook else "no limit", warn=hook)
            add(f"Input caps: {rel}", bool(re.search(r"\.length\s*>\s*\d{2,}|slice\(0,\s*\d+|substring\(0,\s*\d+|413|max(Len|Length)", src)), "no input length cap", warn=True)
    if pages:
        big = max(pages, key=lambda p: p.stat().st_size)
        size = big.stat().st_size + sum(p.stat().st_size for p in files(web, {".js", ".mjs"}) if p.parent == big.parent)
        add("Performance Budgets (page + JS < 250 KB)", size < 250_000, f"{big.name}: {size // 1024} KB")
    return res


def write_md(name, res):
    rows = {r[0].split(":")[0]: r for r in res}
    items = [l.split("|")[2].strip() for l in (ROOT / "00-hq/design/ENGINEERING-CHECKS.md").read_text().splitlines() if re.match(r"\| \d+ \|", l)]
    out = [f"# Engineering checks: {name}", "", "Standard: `00-hq/design/ENGINEERING-CHECKS.md` (107) + `UX-PATTERNS.md` (20) + `SEO-CHECKS.md` (20).",
           "Machine rows come from `python3 00-hq/tools/eng_check.py " + name + " --md`; the rest are filled by hand.", "",
           "## Automatic checks", "", "| Check | Result | Note |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in res]
    out += ["", "## All 107 items (fill: done / not relevant + why / missing + roadmap id)", "", "| # | Item | Status |", "|---|---|---|"]
    for i, it in enumerate(items, 1):
        hit = next((r for k, r in rows.items() if k.lower().startswith(it.lower()[:14])), None)
        out.append(f"| {i} | {it} | {'auto: ' + hit[1] if hit else 'manual'} |")
    path = ROOT / WORLDS[name][3] / ("eng-check.md" if name not in ("extension-site",) else "eng-check-site.md")
    if name == "hq-site":
        path = ROOT / "00-hq/design/eng-check-site.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(WORLDS)
    bad = 0
    for n in names:
        res = run(n)
        fails = [r for r in res if r[1] == "FAIL"]
        warns = [r for r in res if r[1] == "WARN"]
        bad += len(fails)
        print(f"{n:15} {len(res) - len(fails) - len(warns)} pass, {len(warns)} warn, {len(fails)} fail")
        for r in fails + warns:
            print(f"   {r[1]} {r[0]}  {r[2]}")
        if "--md" in sys.argv:
            write_md(n, res)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
