"""SEO checks (00-hq/design/SEO-CHECKS.md) for any static Kalpa site folder.

  python3 00-hq/site/tests/test_seo.py                       # 00-hq/site, https://kalpalabs.dpdns.org
  python3 00-hq/site/tests/test_seo.py <folder> <base-url> [--live]

Checks every public .html page in the folder (404.html is checked but must be noindex and is left out of the sitemap).
--live also requests each external link once (checks 12). Exit 1 on any FAIL.
"""
import json, re, sys, urllib.request, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://kalpalabs.dpdns.org"
PRIVATE = {"404.html"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self._in_title, self.meta, self.links, self.heads = "", False, {}, [], []
        self.imgs, self.ids, self.hrefs, self.srcs, self.ldjson, self._ld = [], set(), [], [], [], None
        self.canonical = []

    def handle_starttag(self, tag, a):
        a = {k: (v or "") for k, v in a}
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "title" and not self.title:  # only the page title, not an <svg><title>
            self._in_title = True
        elif tag == "meta":
            k = (a.get("name") or a.get("property") or "").lower()
            if k:
                self.meta[k] = a.get("content", "")
        elif tag == "link":
            if a.get("rel", "").lower() == "canonical":
                self.canonical.append(a.get("href", ""))
            if a.get("href"):
                self.srcs.append(a["href"])
        elif re.fullmatch(r"h[1-6]", tag):
            self.heads.append(int(tag[1]))
        elif tag == "img":
            self.imgs.append(a)
            self.srcs.append(a.get("src", ""))
        elif tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        elif tag == "script":
            if a.get("src"):
                self.srcs.append(a["src"])
            if a.get("type") == "application/ld+json":
                self._ld = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._ld is not None:
            self.ldjson.append(self._ld)
            self._ld = None

    def handle_data(self, d):
        if self._in_title:
            self.title += d
        if self._ld is not None:
            self._ld += d


def parse(path):
    p = Page()
    p.feed(path.read_text(encoding="utf-8"))
    p.raw = path.read_text(encoding="utf-8")
    return p


def check_page(name, p, base, folder):
    out = []
    fail = lambda n, msg: out.append(f"FAIL [{n}] {name}: {msg}")
    robots = p.meta.get("robots", "").lower()
    if name in PRIVATE:
        if "noindex" not in robots:
            fail(3, "404 page must be noindex")
        return out
    if "noindex" in robots:
        fail(3, "public page has noindex")
    url = base + ("/" if name == "index.html" else "/" + name.removesuffix(".html"))
    if len(p.canonical) != 1 or not p.canonical[0].startswith("https://"):
        fail(4, f"needs exactly one https canonical (found {p.canonical})")
    elif p.canonical[0].rstrip("/") != url.rstrip("/"):
        fail(4, f"canonical {p.canonical[0]} should be {url}")
    t = p.title.strip()
    if not 30 <= len(t) <= 60:
        fail(5, f"title is {len(t)} chars (30-60): {t!r}")
    d = p.meta.get("description", "")
    if not 70 <= len(d) <= 160:
        fail(6, f"description is {len(d)} chars (70-160)")
    if p.heads.count(1) != 1:
        fail(7, f"{p.heads.count(1)} <h1> tags")
    for a, b in zip(p.heads, p.heads[1:]):
        if b > a + 1:
            fail(8, f"heading jumps h{a} -> h{b}")
            break
    for img in p.imgs:
        if "alt" not in img:
            fail(9, f"<img src={img.get('src')!r}> has no alt")
        if not (img.get("width") and img.get("height")):
            fail(13, f"<img src={img.get('src')!r}> needs width and height")
    if not p.ldjson:
        fail(10, "no JSON-LD schema")
    types = set()
    for block in p.ldjson:
        try:
            data = json.loads(block)
        except ValueError as e:
            fail(10, f"JSON-LD does not parse: {e}")
            continue
        items = data.get("@graph", [data]) if isinstance(data, dict) else data
        types |= {i.get("@type") for i in items if isinstance(i, dict)}
    org_types = {"Organization", "LocalBusiness", "BeautySalon", "HealthAndBeautyBusiness", "ExerciseGym", "SportsActivityLocation",
                 "RealEstateAgent", "EducationalOrganization", "Store", "ProfessionalService"}
    if name == "index.html" and p.ldjson and not ("WebSite" in types and types & org_types):
        fail(10, f"home needs Organization + WebSite schema (found {sorted(t for t in types if t)})")
    for h in p.hrefs:
        if h.startswith("#") and len(h) > 1 and h[1:] not in p.ids:
            fail(11, f"anchor {h} has no target")
        elif h.startswith("/") and not h.startswith("//"):
            target = folder / h.lstrip("/").split("#")[0].split("?")[0]
            if h != "/" and not (target.exists() or target.with_suffix(".html").exists()):
                fail(11, f"internal link {h} has no file")
    for s in p.srcs + p.hrefs:
        if s.startswith("http://"):
            fail(16, f"insecure link {s}")
    for k in ("og:title", "og:description", "og:url", "og:image", "twitter:card"):
        if not p.meta.get(k):
            fail(18, f"missing {k}")
    og = p.meta.get("og:image", "")
    if og.startswith(base):
        f = folder / og[len(base):].lstrip("/")
        if not f.exists():
            fail(18, f"og:image file {f.name} missing")
        elif f.stat().st_size > 300_000:
            fail(18, f"og:image is {f.stat().st_size // 1000} KB (max 300)")
    if "width=device-width" not in p.meta.get("viewport", ""):
        fail(15, "no mobile viewport meta")
    if len(p.raw.encode()) > 300_000:
        fail(14, f"HTML is {len(p.raw.encode()) // 1000} KB (max 300)")
    return out


def check_site(folder, base, live=False):
    folder, out = Path(folder), []
    pages = sorted(f for f in folder.glob("*.html"))
    if not pages:
        return [f"FAIL [0] no .html pages in {folder}"]
    public = [f.name for f in pages if f.name not in PRIVATE]
    robots = folder / "robots.txt"
    if not robots.exists():
        out.append("FAIL [2] robots.txt missing")
    else:
        r = robots.read_text()
        if f"Sitemap: {base}/sitemap.xml" not in r:
            out.append("FAIL [2] robots.txt must name the sitemap")
        if re.search(r"^Disallow:\s*/\s*$", r, re.M):
            out.append("FAIL [2] robots.txt blocks the whole site")
    sm = folder / "sitemap.xml"
    if not sm.exists():
        out.append("FAIL [1] sitemap.xml missing")
    else:
        locs = [e.text for e in ET.parse(sm).iter() if e.tag.endswith("loc")]
        want = {base + ("/" if n == "index.html" else "/" + n.removesuffix(".html")) for n in public}
        if set(locs) != want:
            out.append(f"FAIL [1] sitemap lists {sorted(locs)}, expected {sorted(want)}")
        if not all(l.startswith("https://") for l in locs):
            out.append("FAIL [1] sitemap URLs must be https")
    llms = folder / "llms.txt"
    if not llms.exists() or not llms.read_text().startswith("# "):
        out.append("FAIL [20] llms.txt missing or has no '# Title' first line")
    for f in pages:
        out += check_page(f.name, parse(f), base, folder)
    for img in list(folder.rglob("*.png")) + list(folder.rglob("*.jpg")) + list(folder.rglob("*.webp")):
        if img.stat().st_size > 300_000 and "test" not in img.parts:
            out.append(f"FAIL [13] {img.name} is {img.stat().st_size // 1000} KB")
    if live:
        seen = set()
        for f in pages:
            for h in parse(f).hrefs:
                if h.startswith("https://") and not h.startswith(base) and h not in seen:
                    seen.add(h)
                    try:
                        req = urllib.request.Request(h, method="HEAD", headers={"User-Agent": "KalpaSEOCheck/1.0"})
                        code = urllib.request.urlopen(req, timeout=15).status
                    except urllib.error.HTTPError as e:
                        code = e.code
                    except Exception:
                        code = 0
                    if code >= 400 and code not in (403, 405, 429) or code == 0:
                        out.append(f"FAIL [12] {h} answered {code}")
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    folder = Path(args[0]) if args else ROOT
    base = (args[1] if len(args) > 1 else BASE).rstrip("/")
    problems = check_site(folder, base, "--live" in argv)
    for p in problems:
        print(p)
    print("PASS SEO checks" if not problems else f"{len(problems)} SEO problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
