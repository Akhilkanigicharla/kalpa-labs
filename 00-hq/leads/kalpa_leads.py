#!/usr/bin/env python3
"""
Kalpa Leads: one lead finder for all 8 Kalpa worlds (HQ + b1-b7).

Pipeline (all free, no paid API, no account):
  1. Source   : OpenStreetMap via Overpass (ODbL)  and/or  a seed list of URLs Akhil types in (--urls file).
  2. Fetch    : Crawl4AI (Apache-2.0) renders each organisation's OWN website in headless Chromium,
                robots.txt checked, one domain at a time, 1 s pause. Picked over ScrapeGraphAI in the
                19 Oct 2026 bake-off (00-hq/research/lead-scraper-bakeoff-2026-10-19.md).
  3. Contacts : deterministic, no AI. Reuses BotBhai's enrich.extract (schema.org + mailto/tel/wa.me/socials/booking).
  4. Qualify  : optional free AI step on the pruned page text (~1-2k tokens):
                  --llm nuextract  -> NuExtract3 4B (Apache-2.0) running locally via llama.cpp: no key, no limit
                  --llm openrouter -> free model via OpenRouter (key from OPENROUTER_API_KEY env; Akhil sets it)
                  --llm none       -> skip (default)
  5. Score    : per-world keyword signals + "gap" bonuses (e.g. no online booking -> BotBhai pitch).
Output: a CSV per world. Lead lists contain business contact data (DPDP): keep them private
(GitHub Actions artifact), never commit them, never auto-message anyone (TRAI / WhatsApp opt-in rules).

Never used as sources: Google Maps, Justdial, Instagram, Facebook, LinkedIn, IndiaMART, consumers' numbers.

Usage:
  python kalpa_leads.py --world b1 --city Hyderabad --max 40 --out leads
  python kalpa_leads.py --world b6 --urls seeds/b6.txt --llm nuextract --out leads
  python kalpa_leads.py --world all --from-osm-json saved.json --html-dir fixtures/  (offline test mode)
"""
import argparse, asyncio, csv, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "01-botbhai", "botbhai", "leadfinder"))
import enrich as E          # noqa: E402  (BotBhai's tested contact extractor)
import leadfinder as LF     # noqa: E402  (Overpass helpers)

WORLDS = json.load(open(os.path.join(HERE, "worlds.json"), encoding="utf-8"))
WORLD_IDS = [k for k in WORLDS if not k.startswith("_")]
UA = "KalpaLabs-LeadFinder/1.0 (+https://github.com/Akhilkanigicharla)"
BANNED_HOSTS = re.compile(r"(^|\.)(google\.[a-z.]+|goo\.gl|justdial\.com|instagram\.com|facebook\.com|fb\.com|linkedin\.com|indiamart\.com|sulekha\.com)$", re.I)
COLS = ["world", "score", "name", "website", "email", "phone", "whatsapp_link", "instagram", "facebook", "online_booking",
        "schema_type", "category", "address", "source", "fetched", "ai_summary", "ai_fields", "signals_hit", "why", "status", "notes"]

# ---------- sources ----------
def norm_url(u):
    u = (u or "").strip()
    if not u: return ""
    if not re.match(r"https?://", u, re.I): u = "https://" + u
    return u

def banned(url):
    host = urllib.parse.urlparse(url).hostname or ""
    return bool(BANNED_HOSTS.search(host))

def from_osm(world, city, osm_json=None, limit=200):
    tags = WORLDS[world].get("osm") or []
    if not tags: return []
    res = json.load(open(osm_json, encoding="utf-8")) if osm_json else LF.overpass(LF.build_query(city, tags))
    rows, seen = [], set()
    for el in res.get("elements", []):
        t = el.get("tags", {}); name = (t.get("name") or "").strip()
        if not name or name.lower() in seen: continue
        seen.add(name.lower())
        addr = ", ".join(x for x in [t.get("addr:street"), t.get("addr:suburb"), t.get("addr:city")] if x)
        rows.append({"world": world, "name": name, "website": norm_url(t.get("website") or t.get("contact:website")),
                     "phone": LF.phone_of(t), "email": t.get("email") or t.get("contact:email", ""),
                     "category": t.get("shop") or t.get("amenity") or t.get("office") or t.get("craft") or t.get("leisure") or "",
                     "address": addr, "source": f"OpenStreetMap {el.get('type')}/{el.get('id')} (ODbL)"})
    rows.sort(key=lambda r: (not r["website"], r["name"]))  # sites first: we can qualify them
    return rows[:limit]

def from_urls(world, path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"): continue
        name, _, url = line.partition("|") if "|" in line else ("", "", line)
        url = norm_url(url.strip() or name.strip())
        rows.append({"world": world, "name": name.strip() if "|" in line else urllib.parse.urlparse(url).hostname or url,
                     "website": url, "source": f"seed list ({os.path.basename(path)})"})
    return rows

# ---------- fetch (Crawl4AI) ----------
async def crawl(urls, delay=1.0, timeout_ms=45000):
    """Return {url: {"ok", "html", "md", "status", "error"}}. robots.txt is checked by Crawl4AI itself."""
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    try: from crawl4ai.content_filter_strategy import PruningContentFilterLXML as PruningContentFilter
    except ImportError: from crawl4ai.content_filter_strategy import PruningContentFilter
    cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, check_robots_txt=True, page_timeout=timeout_ms,
                           markdown_generator=DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.5)))
    out = {}
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, user_agent=UA, verbose=False)) as c:
        for u in urls:
            try:
                r = await c.arun(u, config=cfg)
                md = (r.markdown.fit_markdown or r.markdown.raw_markdown) if (r.success and r.markdown) else ""
                out[u] = {"ok": bool(r.success), "html": r.html or "", "md": md or "", "status": r.status_code,
                          "error": "" if r.success else (r.error_message or "failed")[:120]}
            except Exception as e:  # one bad site never stops the run
                out[u] = {"ok": False, "html": "", "md": "", "status": None, "error": type(e).__name__}
            await asyncio.sleep(delay)
    return out

def from_html_dir(urls, html_dir):
    """Offline mode for tests: fixtures/<host>.html stands in for the live site."""
    out = {}
    for u in urls:
        p = os.path.join(html_dir, (urllib.parse.urlparse(u).hostname or "x") + ".html")
        if os.path.exists(p):
            h = open(p, encoding="utf-8").read()
            out[u] = {"ok": True, "html": h, "md": re.sub(r"<[^>]+>", " ", h), "status": 200, "error": ""}
        else:
            out[u] = {"ok": False, "html": "", "md": "", "status": 404, "error": "no fixture"}
    return out

# ---------- qualify (free AI, optional) ----------
def prompt_text(world, md, limit=6000):
    return f"Organisation website text (for Kalpa world: {WORLDS[world]['looking_for']}):\n\n{md[:limit]}"

class NuExtract:
    """NuExtract3 4B GGUF (Apache-2.0, numind) on CPU via llama.cpp. No key, no rate limit."""
    def __init__(self, gguf=None, ctx=4096, threads=None):
        from llama_cpp import Llama
        import jinja2
        self.llm = Llama(model_path=gguf or os.environ.get("NUEXTRACT_GGUF", "NuExtract3-Q4_K_M.gguf"),
                         n_ctx=ctx, n_threads=threads or os.cpu_count(), verbose=False)
        tpl = self.llm.metadata.get("tokenizer.chat_template", "")
        tpl = re.sub(r"\{%-?\s*(end)?generation\s*-?%\}", "", tpl)  # HF-only tag, not plain Jinja
        self.tpl = jinja2.Environment(loader=jinja2.BaseLoader(), trim_blocks=False).from_string(tpl)

    def extract(self, world, md):
        msgs = [{"role": "user", "content": [{"type": "text", "text": prompt_text(world, md, 5000)}]}]
        prompt = self.tpl.render(messages=msgs, add_generation_prompt=True, enable_thinking=False,
                                 template=json.dumps(WORLDS[world]["template"], indent=4))
        r = self.llm.create_completion(prompt, max_tokens=400, temperature=0.2)
        return parse_json(r["choices"][0]["text"])

class OpenRouter:
    """Free OpenRouter model. Key comes only from the environment (GitHub/n8n secret set by Akhil)."""
    URL = "https://openrouter.ai/api/v1/chat/completions"
    def __init__(self, model=None):
        self.key = os.environ.get("OPENROUTER_API_KEY", "")
        if not self.key: raise SystemExit("OPENROUTER_API_KEY is not set (Akhil adds it as a secret; never paste it in chat)")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3.5-super-vl:free")
    def extract(self, world, md):
        ask = (f"Fill this JSON template from the website text. Use null when unknown. Reply with JSON only.\n"
               f"Template: {json.dumps(WORLDS[world]['template'])}\n\n{prompt_text(world, md, 6000)}")
        body = json.dumps({"model": self.model, "temperature": 0.2, "messages": [{"role": "user", "content": ask}]}).encode()
        req = urllib.request.Request(self.URL, data=body, headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return parse_json(json.load(r)["choices"][0]["message"]["content"])

JUNK_EMAIL = re.compile(r"(temp\.domains|domaincatch|sentry|wixpress|example[.@]|mysite\.com|godaddy|hostinger|@sh\d+\.)", re.I)
ROLE = re.compile(r"^(info|contact|hello|hi|support|care|sales|enquir\w*|inquir\w*|partners?|partnerships?|business|admin|office|team|help"
                  r"|bookings?|reservations?|marketing|media|press|corporate\w*|customercare|feedback|dpo|grievances?|apihelp|enterprise)\b", re.I)

def best_email(html, url, current=""):
    """Prefer an address on the organisation's own domain; drop hosting/parking/template addresses."""
    host = (urllib.parse.urlparse(url).hostname or "").lower().removeprefix("www.")
    base = host.split(".")[-2] if host.count(".") >= 1 else host
    found = [e for e in dict.fromkeys(([current] if current else []) + E.EMAIL.findall(html or "")) if e and not E.SKIP_EMAIL.search(e) and not JUNK_EMAIL.search(e)]
    own = [e for e in found if base and base in e.split("@")[-1].lower()]
    role = [e for e in found if ROLE.match(e)]  # off-domain: only role inboxes (info@, care.x@), never a person's own address (DPDP)
    return (own or role or [""])[0]

def parse_json(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip().strip("`")
    text = re.sub(r"^json\s*", "", text)
    m = re.search(r"\{.*\}", text, re.S)
    try: return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError: return {}

# ---------- score ----------
def score(world, row, md):
    w = WORLDS[world]; s = 0; hits = []
    if row.get("website"): s += 20
    if row.get("email") or row.get("phone") or row.get("whatsapp_link"): s += 25   # we can reach them
    low = (md or "").lower()
    for word, pts in w.get("signals", {}).items():
        if word in low: s += pts; hits.append(word)
    gaps = []
    for field, pts in w.get("gap_if_missing", {}).items():
        val = row.get(field, "")
        if row.get("fetched") == "yes" and (not val or val == "no"): s += pts; gaps.append(field)
    if row.get("fetched", "").startswith("blocked"): s -= 10
    row["signals_hit"] = ", ".join(hits)
    row["why"] = (f"{w['name']} fit"
                  + (f"; matched: {', '.join(hits[:4])}" if hits else "")
                  + (f"; gap: no {', no '.join(g.replace('_', ' ') for g in gaps)}" if gaps else ""))
    return max(0, min(100, s))

# ---------- run ----------
def run(world, rows, pages, llm=None, max_ai=30):
    ai_done = 0
    for r in rows:
        r.setdefault("world", world); r.setdefault("status", "new"); r.setdefault("notes", "")
        url = r.get("website", "")
        md = ""
        if url and banned(url):
            r["fetched"] = "skipped: banned source"; r["website"] = ""
        elif url and url in pages:
            p = pages[url]
            if p["ok"]:
                info = E.extract(p["html"])
                for k, v in info.items():
                    if v and not r.get(k): r[k] = v
                r["email"] = best_email(p["html"], url, r.get("email", ""))
                md = p["md"]; r["fetched"] = "yes"
            else:
                r["fetched"] = "blocked by robots.txt" if "robots" in p["error"].lower() else f"error: {p['error'][:60]}"
        else:
            r["fetched"] = "no website"
        if llm and md and ai_done < max_ai:
            ai_done += 1  # failed calls still use free quota, so they count
            try:
                fields = llm.extract(world, md)
                r["ai_fields"] = json.dumps(fields, ensure_ascii=False)
                r["ai_summary"] = str(fields.get("what_they_do") or fields.get("provider") or "")[:200]
            except Exception as e:
                r["ai_fields"] = f"error: {type(e).__name__}"
        r["score"] = score(world, r, md)
    rows.sort(key=lambda r: -int(r["score"]))
    return rows

def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", default="b1", help="hq, b1..b7 or all")
    ap.add_argument("--city", default="Hyderabad")
    ap.add_argument("--urls", help="seed file: one URL (or 'Name|URL') per line")
    ap.add_argument("--max", type=int, default=40, help="max organisations per world")
    ap.add_argument("--llm", choices=["none", "nuextract", "openrouter"], default="none")
    ap.add_argument("--max-ai", type=int, default=30, help="max AI qualifications per world")
    ap.add_argument("--out", default="leads", help="output folder")
    ap.add_argument("--from-osm-json", help="offline: saved Overpass JSON instead of the live API")
    ap.add_argument("--html-dir", help="offline: fixtures/<host>.html instead of live websites")
    ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args(argv)
    worlds = WORLD_IDS if a.world == "all" else [a.world]
    for w in worlds:
        if w not in WORLDS: raise SystemExit(f"unknown world {w}; use one of {', '.join(WORLD_IDS)} or all")
    os.makedirs(a.out, exist_ok=True)
    llm = NuExtract() if a.llm == "nuextract" else OpenRouter() if a.llm == "openrouter" else None
    summary = []
    for w in worlds:
        seed = a.urls or (os.path.join(HERE, "seeds", f"{w}.txt") if os.path.exists(os.path.join(HERE, "seeds", f"{w}.txt")) else None)
        rows = []
        if not a.urls and WORLDS[w].get("osm"):
            try: rows = from_osm(w, a.city, a.from_osm_json, a.max)
            except SystemExit as e: print(f"[{w}] OpenStreetMap unavailable: {e}")
        if seed:
            have = {r.get("website") for r in rows}
            rows += [r for r in from_urls(w, seed) if r["website"] not in have]
        rows = rows[:a.max]
        if not rows:
            print(f"[{w}] no sources: {WORLDS[w]['name']} needs a seed list (--urls)" if not WORLDS[w].get("osm") else f"[{w}] nothing found")
            continue
        urls = sorted({r["website"] for r in rows if r.get("website") and not banned(r["website"])})
        t = time.time()
        pages = from_html_dir(urls, a.html_dir) if a.html_dir else (asyncio.run(crawl(urls, a.delay)) if urls else {})
        rows = run(w, rows, pages, llm, a.max_ai)
        path = os.path.join(a.out, f"{w}-leads.csv"); write_csv(path, rows)
        ok = sum(1 for r in rows if r.get("fetched") == "yes")
        reach = sum(1 for r in rows if r.get("email") or r.get("phone") or r.get("whatsapp_link"))
        summary.append((w, len(rows), ok, reach, round(time.time() - t)))
        print(f"[{w}] {len(rows)} organisations, {ok} sites read, {reach} reachable -> {path}")
    with open(os.path.join(a.out, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("| World | Organisations | Sites read | Reachable | Seconds |\n|---|---|---|---|---|\n")
        for s in summary: f.write(f"| {WORLDS[s[0]]['name']} | {s[1]} | {s[2]} | {s[3]} | {s[4]} |\n")
        f.write("\nSources: OpenStreetMap (© OpenStreetMap contributors, ODbL) and each organisation's own website. "
                "Private list: do not share, do not message anyone without consent.\n")
    return summary

if __name__ == "__main__":
    main()
