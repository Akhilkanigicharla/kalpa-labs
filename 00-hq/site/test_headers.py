#!/usr/bin/env python3
"""Security-header check for every Kalpa Labs website (engineering checklist: web security headers).

    python3 00-hq/site/test_headers.py          # stdlib only, no network, no build needed

Reads each site's netlify.toml / _headers (or <meta> CSP for pages that ship as files or on GitHub Pages) and asserts:
HSTS (1 year + subdomains), nosniff, strict-origin-when-cross-origin, a Permissions-Policy that grants only what the
page needs, clickjacking protection (frame-ancestors 'none' + X-Frame-Options DENY) except the BotBhai chat page that
client sites frame on purpose, and a CSP whose script-src never has 'unsafe-inline'/'unsafe-eval'. It also checks the
pages themselves: no inline <script> or on*= handlers where the CSP has no hash for them, and that hashes are current.
The same policies are loaded in Chromium with zero CSP violations by 00-hq/site/tests/csp_browser.py.
"""
import base64, hashlib, html.parser, importlib.util, pathlib, re, sys, tomllib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HSTS = "max-age=31536000; includeSubDomains"

# site name -> (config file, folder whose HTML that config serves, mic allowed?)
NETLIFY = {
    "HQ site": ("00-hq/site/netlify.toml", "00-hq/site", False),
    "BotBhai": ("01-botbhai/botbhai/netlify.toml", "01-botbhai/botbhai/web", None),   # per-path, see test below
    "JobCard": ("02-jobcard/netlify.toml", "02-jobcard/web", True),
    "Jyotish": ("02-jobcard/apps/jyotish/netlify.toml", "02-jobcard/apps/jyotish", False),
    "Photo Studio": ("02-jobcard/apps/photo-studio/netlify.toml", "02-jobcard/apps/photo-studio", False),
    "Bhasha Kids": ("02-jobcard/apps/bhasha-kids/netlify.toml", "02-jobcard/apps/bhasha-kids", True),
}
HEADERS_FILES = {"Calculators (b5)": ("05-deals/site/public/_headers", "05-deals/site/dist", False)}
BOTBHAI_FRAMED = {"/", "/index.html"}                      # chat page opened by widget.js on client sites
BOTBHAI_OWNER = ["inbox", "dashboard", "billing", "invoice-sample", "artifact"]


def netlify_rules(path):
    """[(for, {header-lower: value})] from a netlify.toml."""
    data = tomllib.loads((ROOT / path).read_text())
    return [(r["for"], {k.lower(): " ".join(str(v).split()) for k, v in r.get("values", {}).items()}) for r in data.get("headers", [])]


def headers_file_rules(text):
    """[(path, {header-lower: value})] from a Netlify / Cloudflare Pages _headers file."""
    rules, cur = [], None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        if not line[0].isspace(): cur = (line.strip(), {}); rules.append(cur); continue
        k, _, v = line.strip().partition(":"); cur[1][k.strip().lower()] = v.strip()
    return rules


def headers_for(rules, path):
    """Headers Netlify sends for a path, refusing paths where two rules set the same header (Netlify may merge them)."""
    out = {}
    for pat, vals in rules:
        rx = "^" + re.escape(pat).replace(r"\*", ".*") + "$"
        if re.match(rx, path):
            for k, v in vals.items():
                assert k not in out or out[k] == v, f"{path}: two rules set {k}; Netlify could merge them"
                out[k] = v
    return out


def csp(value):
    """{directive: [sources]} of a CSP string."""
    d = {}
    for part in value.split(";"):
        bits = part.split()
        if bits: d[bits[0].lower()] = bits[1:]
    return d


def sha(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


class Page(html.parser.HTMLParser):
    """Inline scripts (run, not JSON data), inline styles, on*= handlers and target=_blank links without noopener."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False); self.scripts, self.styles, self.handlers, self.blank, self.meta_csp = [], [], [], [], None
        self._in = None; self._buf = []; self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.handlers += [f"{tag} {k}" for k, _ in attrs if k.startswith("on")]
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or "") and "noreferrer" not in (a.get("rel") or ""): self.blank.append(a.get("href"))
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy": self.meta_csp = a.get("content")
        if tag == "script" and "src" not in a and (a.get("type") or "text/javascript") in ("text/javascript", "module", "application/javascript"): self._in = "script"; self._buf = []
        if tag == "style": self._in = "style"; self._buf = []
    def handle_data(self, data):
        if self._in: self._buf.append(data)
    def handle_entityref(self, name):
        if self._in: self._buf.append(f"&{name};")
    def handle_charref(self, name):
        if self._in: self._buf.append(f"&#{name};")
    def handle_endtag(self, tag):
        if self._in and tag == self._in:
            (self.scripts if tag == "script" else self.styles).append("".join(self._buf)); self._in = None


class Common:
    def assert_basics(self, name, h, mic):
        self.assertEqual(h.get("strict-transport-security"), HSTS, name)
        self.assertEqual(h.get("x-content-type-options"), "nosniff", name)
        self.assertEqual(h.get("referrer-policy"), "strict-origin-when-cross-origin", name)
        pp = h.get("permissions-policy", "")
        self.assertIn("camera=()", pp, f"{name}: no page needs the camera API (photo-studio uses a file picker)")
        self.assertIn("geolocation=()", pp, name)
        self.assertIn("microphone=(self)" if mic else "microphone=()", pp, name)

    def assert_csp(self, name, value, framed=False):
        c = csp(value)
        for d in ("default-src", "script-src", "object-src", "base-uri", "frame-ancestors", "form-action"):
            self.assertIn(d, c, f"{name}: CSP has no {d}")
        for bad in ("'unsafe-inline'", "'unsafe-eval'", "*", "http:", "https:", "data:"):
            self.assertNotIn(bad, c["script-src"], f"{name}: script-src allows {bad}")
        self.assertEqual(c["object-src"], ["'none'"], name)
        self.assertEqual(c["base-uri"], ["'none'"], name)
        if framed: self.assertEqual(c["frame-ancestors"], ["'self'", "https:"], name)
        else: self.assertEqual(c["frame-ancestors"], ["'none'"], name)

    def assert_page(self, name, f, allowed_hashes=()):
        p = Page(f.read_text(errors="ignore"))
        self.assertEqual(p.handlers, [], f"{name} {f.name}: inline on*= handlers need 'unsafe-inline'; use addEventListener")
        for s in p.scripts:
            self.assertIn(sha(s), allowed_hashes, f"{name} {f.name}: inline <script> not allowed by the CSP; move it to a .js file")
        self.assertEqual(p.blank, [], f"{name} {f.name}: target=_blank without rel=noopener")
        return p


class NetlifySites(unittest.TestCase, Common):
    def test_simple_sites(self):
        for name, (cfg, folder, mic) in NETLIFY.items():
            if name == "BotBhai": continue
            with self.subTest(site=name):
                h = headers_for(netlify_rules(cfg), "/index.html")
                self.assert_basics(name, h, mic)
                self.assertEqual(h.get("x-frame-options"), "DENY", name)
                self.assert_csp(name, h["content-security-policy"])
                for f in sorted((ROOT / folder).glob("*.html")):
                    p = self.assert_page(name, f)
                    if p.meta_csp:  # page also carries a meta CSP for file:// use: the header must be at least as strict for scripts
                        self.assertNotIn("'unsafe-inline'", csp(p.meta_csp).get("script-src", []), f.name)

    def test_hq_style_unsafe_inline_is_documented(self):
        # style-src 'unsafe-inline' only where the page/script writes style="" attributes; the toml must say why
        for name, (cfg, _, _) in NETLIFY.items():
            text = (ROOT / cfg).read_text()
            if "'unsafe-inline'" in text:
                self.assertTrue(re.search(r"#[^\n]*'unsafe-inline'", text) and re.search(r'#[^\n]*style=""', text), f"{name}: say why style needs it")

    def test_botbhai(self):
        cfg, folder, _ = NETLIFY["BotBhai"]; rules = netlify_rules(cfg)
        for path in sorted(BOTBHAI_FRAMED):
            h = headers_for(rules, path)
            self.assert_basics(f"BotBhai {path}", h, mic=True)
            self.assertNotIn("x-frame-options", h, "the chat page is framed by widget.js on client sites")
            self.assert_csp(f"BotBhai {path}", h["content-security-policy"], framed=True)
        for page in BOTBHAI_OWNER:
            for path in (f"/{page}", f"/{page}.html"):
                h = headers_for(rules, path)
                self.assert_basics(f"BotBhai {path}", h, mic=False)
                self.assertEqual(h.get("x-frame-options"), "DENY", path)
                self.assert_csp(f"BotBhai {path}", h["content-security-policy"])
        # every page the build ships has a rule; source pages carry no inline script
        built = {p.stem for p in (ROOT / folder).glob("*.html") if p.name != "index.src.html"} | {"index", "invoice-sample", "artifact"}
        self.assertEqual(built - set(BOTBHAI_OWNER) - {"index"}, set(), "a new BotBhai page needs its own CSP rule")
        for f in (ROOT / folder).glob("*.html"):
            if f.name != "index.src.html": self.assert_page("BotBhai", f)  # index.src.html: build.py moves its scripts to app.js
        dist = ROOT / folder / "dist"
        if (dist / "index.html").exists():  # built by build.py (test-all.sh builds it): engine + page JS are in app.js
            for f in dist.glob("*.html"):
                if f.name == "artifact.html": continue
                allowed = [x for x in csp(headers_for(rules, "/" + f.name)["content-security-policy"])["script-src"] if x.startswith("'sha256-")]
                self.assert_page("BotBhai dist", f, allowed)
        import subprocess  # the invoice Print script hash in netlify.toml must match core/billing.js
        h = subprocess.check_output(["node", "-p", "require('./core/billing.js').PRINT_HASH"], cwd=ROOT / "01-botbhai/botbhai", text=True).strip()
        self.assertIn(h, csp(headers_for(rules, "/invoice-sample.html")["content-security-policy"])["script-src"])
        src = (ROOT / folder / "index.src.html").read_text()
        self.assertIn("FRAMED ? null", src, "owner (token) view must not run inside a frame")


class HeadersFileSites(unittest.TestCase, Common):
    def test_calculators(self):
        for name, (path, dist, mic) in HEADERS_FILES.items():
            h = headers_for(headers_file_rules((ROOT / path).read_text()), "/index.html")
            self.assert_basics(name, h, mic)
            self.assertEqual(h.get("x-frame-options"), "DENY")
            self.assert_csp(name, h["content-security-policy"])
            self.assertNotIn("'unsafe-inline'", csp(h["content-security-policy"])["style-src"])
            conf = (ROOT / "05-deals/site/astro.config.mjs").read_text()
            self.assertIn('inlineStylesheets: "never"', conf); self.assertIn("assetsInlineLimit: 0", conf)
            for f in (ROOT / dist).rglob("*.html"):  # present after `npm run build`
                p = self.assert_page(name, f)
                self.assertEqual(p.styles, [], f"{f}: inline <style> is blocked by this CSP")

    def test_seo_client_sites(self):
        spec = importlib.util.spec_from_file_location("seo_bot", ROOT / "01-botbhai/botbhai/seo/seo_bot.py")
        seo = importlib.util.module_from_spec(spec); spec.loader.exec_module(seo)
        h = headers_for(headers_file_rules(seo.headers_file()), "/index.html")
        self.assert_basics("SEO site", h, mic=False)
        self.assertEqual(h.get("x-frame-options"), "DENY")
        c = csp(h["content-security-policy"]); self.assert_csp("SEO site", h["content-security-policy"])
        self.assertEqual(c["script-src"], ["'none'"])
        self.assertIn(sha(seo.CSS), c["style-src"], "the hash of the page's one <style> must be in style-src")
        self.assertNotIn("'unsafe-inline'", c["style-src"])


class FilePages(unittest.TestCase, Common):
    """Pages with no server headers: the meta CSP is all there is."""
    def test_exam_kit_phone_pages(self):
        pages = sorted((ROOT / "03-kits/engine/dist").glob("*/*-tracker.html"))
        self.assertTrue(pages)
        for f in pages:
            with self.subTest(page=f.name):
                p = Page(f.read_text())
                self.assertTrue(p.meta_csp, f"{f.name}: no meta CSP")
                c = csp(p.meta_csp)
                self.assertEqual(c["default-src"], ["'none'"])
                self.assertEqual(c["script-src"], [sha(s) for s in p.scripts], "script hash stale: rerun kit_engine.py")
                self.assertEqual(c["style-src"], [sha(s) for s in p.styles], "style hash stale: rerun kit_engine.py")
                self.assert_page("kit", f, [sha(s) for s in p.scripts])
                self.assertNotIn(' style="', f.read_text())

    def test_tab_lifeboat_site(self):
        b = (ROOT / "04-extensions/site/build.mjs").read_text()
        m = re.search(r'Content-Security-Policy" content="([^"]+)"', b); self.assertTrue(m, "build.mjs must inject a meta CSP")
        c = csp(m.group(1)); self.assertEqual(c["default-src"], ["'none'"]); self.assertNotIn("script-src", c)
        self.assertIn('name="referrer" content="strict-origin-when-cross-origin"', b)
        for f in (ROOT / "04-extensions/site").glob("*.html"):
            p = self.assert_page("Tab Lifeboat", f); self.assertEqual(p.styles, [])
            self.assertNotIn(' style="', f.read_text())


class Parsers(unittest.TestCase):
    def test_overlap_is_refused(self):
        with self.assertRaises(AssertionError):
            headers_for([("/*", {"content-security-policy": "a"}), ("/x", {"content-security-policy": "b"})], "/x")

    def test_inline_script_is_caught(self):
        p = Page('<script type="application/ld+json">{}</script><script>alert(1)</script><a target="_blank" href="x">x</a><b onclick="x()"></b>')
        self.assertEqual(p.scripts, ["alert(1)"]); self.assertEqual(p.blank, ["x"]); self.assertEqual(p.handlers, ["b onclick"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
