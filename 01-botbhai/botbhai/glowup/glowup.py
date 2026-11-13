"""Website glow-up (A199): rebuild a BotBhai customer's OWN old website as a fast Kalpa-design page.

Clean room by design:
  * builds only from the owner's folder: owner.json + media/ (text, photos and logo the owner gave us);
  * refuses to run without a signed permission record (owner.json "permission", form in docs/glowup-permission.md);
  * never fetches anything: photo/logo paths must be plain files inside media/, no URLs, no "..";
  * every photo is re-encoded with Pillow so GPS, camera and other EXIF/XMP data is gone (idea from ExifCleaner, our own code).

  python3 glowup/glowup.py --owner <folder> --out <dir>         # writes <dir>/site
  python3 glowup/glowup.py --owner <folder> --out <dir> --draft # preview without a real site_url
"""
import argparse, html, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "seo"))
import seo_bot  # noqa: E402  (reuse the Kalpa client-site CSS, schema and share card)
from PIL import Image, ImageOps  # noqa: E402

MAX_SIDE, MAX_PHOTOS, MAX_TEXT = 1600, 12, 2000
PERMISSION_KEYS = ("signed_by", "date", "form_version", "owns_content")


class GlowupError(ValueError):
    pass


def _text(v, limit=MAX_TEXT):
    v = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(v or "")).strip()
    return v[:limit]


def check_permission(o):
    p = o.get("permission") or {}
    missing = [k for k in PERMISSION_KEYS if not p.get(k)]
    if missing:
        raise GlowupError("no signed permission (missing: " + ", ".join(missing) + "); get docs/glowup-permission.md signed first")
    if p.get("withdrawn"):
        raise GlowupError("permission was withdrawn: do not build, delete the owner's files")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(p["date"])):
        raise GlowupError("permission date must be YYYY-MM-DD")


def media_path(folder, rel):
    rel = str(rel or "")
    if re.match(r"^[a-z]+:", rel, re.I) or rel.startswith(("/", "\\")) or ".." in rel.replace("\\", "/").split("/"):
        raise GlowupError(f"{rel!r}: only files the owner gave us, inside media/ (no links, no other folders)")
    p = (folder / "media" / rel).resolve()
    if not p.is_file() or (folder / "media").resolve() not in p.parents:
        raise GlowupError(f"{rel!r}: file not found in the owner's media/ folder")
    return p


def clean_image(src, dst, max_side=MAX_SIDE):
    """Re-encode without any metadata. Turns the photo upright first (EXIF orientation), then drops EXIF/GPS/XMP/ICC text."""
    with Image.open(src) as im:
        had_gps = bool(im.getexif().get_ifd(0x8825)) if hasattr(im, "getexif") else False
        im = ImageOps.exif_transpose(im)
        im.thumbnail((max_side, max_side))
        alpha = im.mode in ("RGBA", "LA", "P")
        clean = Image.new("RGBA" if alpha else "RGB", im.size)
        clean.paste(im.convert("RGBA" if alpha else "RGB"))  # pixels only: info/exif are not copied
        dst = dst.with_suffix(".png" if alpha else ".jpg")
        clean.save(dst, **({"optimize": True} if alpha else {"quality": 82, "optimize": True, "progressive": True}))
        return dst, clean.size, had_gps


def build(folder, out, draft=False):
    folder, out = pathlib.Path(folder), pathlib.Path(out)
    o = json.loads((folder / "owner.json").read_text(encoding="utf-8"))
    check_permission(o)
    setup = o.get("type", "salon")
    if setup not in seo_bot.SCHEMA_TYPE:
        raise GlowupError(f"type must be one of {', '.join(seo_bot.SCHEMA_TYPE)}")
    site_url = _text(o.get("site_url"), 200).rstrip("/")
    if not site_url.startswith("https://"):
        if not draft:
            raise GlowupError("site_url is missing: the new page needs its real https address (or use --draft)")
        site_url = seo_bot.PLACEHOLDER_URL
    biz = _text(o.get("business"), 120)
    if not biz:
        raise GlowupError("business name is missing")
    phone = _text(o.get("phone"), 20)
    services = [{"name": _text(s.get("name"), 80), "price": _text(s.get("price"), 40)} for s in o.get("services", [])[:30] if _text(s.get("name"))]
    if not services:
        raise GlowupError("add at least one service from the owner's old site")
    site, img_dir = out / "site", out / "site" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    report = {"photos": [], "gps_removed": 0}
    def add_image(rel, name, side=MAX_SIDE):
        dst, size, gps = clean_image(media_path(folder, rel), img_dir / name, side)
        report["photos"].append(dst.name); report["gps_removed"] += gps
        return f"img/{dst.name}", size
    logo = add_image(o["logo"], "logo", 320) if o.get("logo") else None
    photos = []
    for i, ph in enumerate(o.get("photos", [])[:MAX_PHOTOS]):
        rel, alt = (ph, "") if isinstance(ph, str) else (ph.get("file"), ph.get("alt", ""))
        src, size = add_image(rel, f"photo-{i + 1}")
        photos.append((src, size, _text(alt, 140) or f"{biz} photo {i + 1}"))

    cfg = {"business": biz, "phone": phone, "whatsapp": re.sub(r"\D", "", phone), "address": _text(o.get("address"), 200),
           "hours": _text(o.get("hours"), 120), "areas": [_text(a, 60) for a in o.get("areas", [])[:8]] or ["Hyderabad"],
           "catalogTitle": _text(o.get("services_title"), 60) or "Services and prices", "catalog": services, "faqs": [],
           "site_url": site_url, "cover_photo": photos[0][0] if photos else ""}
    e = html.escape
    img = lambda s, w_h, alt, cls="": (f'<img src="{s}" width="{w_h[0]}" height="{w_h[1]}" alt="{e(alt)}" loading="lazy" decoding="async"'
                                       + (f' class="{cls}"' if cls else "") + ">")
    paras = "".join(f"<p>{e(_text(p))}</p>" for p in (o.get("about") or "").split("\n\n") if _text(p))
    faqs = "".join(f"<h3>{e(_text(f.get('q'), 160))}</h3><p>{e(_text(f.get('a')))}</p>" for f in o.get("faqs", [])[:10] if f.get("q"))
    gallery = "".join(f"<figure>{img(s, wh, alt)}</figure>" for s, wh, alt in photos[1:])
    body = ((f'<header class="gl-head">{img(logo[0], logo[1], biz + " logo", "gl-logo")}' if logo else '<header class="gl-head">')
            + f"<h1>{e(biz)}</h1></header>"
            + (f"<p class='gl-lead'>{e(_text(o.get('headline'), 200))}</p>" if o.get("headline") else "")
            + f"<p class='muted'>{e(cfg['address'])} · {e(phone)}<br>{e(cfg['hours'])}</p>"
            + (img(photos[0][0], photos[0][1], photos[0][2], "gl-cover").replace(' loading="lazy"', ' fetchpriority="high"') if photos else "")
            + (f"<h2>About us</h2>{paras}" if paras else "")
            + f"<h2>{e(cfg['catalogTitle'])}</h2>{seo_bot.services_table(cfg)}"
            + (f"<h2>Photos</h2><div class='gl-grid'>{gallery}</div>" if gallery else "")
            + (f"<h2>Questions</h2>{faqs}" if faqs else "")
            + f"<h2>Find us</h2><p>{e(cfg['address'])}<br>Areas: {e(', '.join(cfg['areas']))}</p>"
            + "<p class='muted gl-foot'>Text, photos and logo belong to " + e(biz) + ". Page by Kalpa Labs.</p>")
    css = ("<style>main{overflow-wrap:anywhere}.gl-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.gl-head h1{margin:0;overflow-wrap:anywhere;min-width:0}"
           ".gl-logo{width:64px;height:64px;object-fit:contain;margin:0;background:var(--panel);border:1px solid var(--rule)}"
           ".gl-lead{font-size:20px;line-height:1.4}.gl-cover{width:100%;aspect-ratio:3/2;object-fit:cover}"
           ".gl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}.gl-grid figure{margin:0}"
           ".gl-grid img{width:100%;aspect-ratio:1;object-fit:cover;margin:0}.gl-foot{margin-top:40px;font-size:14px}</style>")
    short = biz if len(biz) <= 40 else biz[:39].rstrip() + "…"
    title = f"{short}, {cfg['areas'][0]}"[:60]
    desc = (f"{_text(o.get('headline'), 90)} {short} in {cfg['areas'][0]}: prices, timings and WhatsApp booking.").strip()[:158]
    page = seo_bot.page(setup, cfg, title, desc, body, site_url + "/").replace("</head>", css + "</head>", 1)
    if not cfg["whatsapp"]:
        page = re.sub(r'<a class="wa"[^>]*>.*?</a>', "", page)
    (site / "index.html").write_text(page, encoding="utf-8")
    nf = seo_bot.page(setup, cfg, f"Page not found · {biz}", "This page does not exist.",
                      f"<h1>Page not found</h1><p><a href='/'>Go to the {e(biz)} home page</a></p>", site_url + "/404.html")
    (site / "404.html").write_text(nf.replace("<head>", '<head><meta name="robots" content="noindex">', 1), encoding="utf-8")
    (site / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                      f"<url><loc>{e(site_url)}/</loc></url></urlset>")
    (site / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n")
    (site / "favicon.svg").write_text(seo_bot.favicon(cfg))
    if not photos:
        (site / "og.png").write_bytes(seo_bot.og_card_png())
    (site / "llms.txt").write_text(f"# {biz}\n\n> {cfg['address']}. {cfg['hours']}. Phone/WhatsApp {phone}.\n\n## {cfg['catalogTitle']}\n"
                                   + "\n".join(f"- {s['name']}: {s['price']}" for s in services) + "\n", encoding="utf-8")
    (out / "glowup-report.json").write_text(json.dumps({"business": biz, "permission": o["permission"], **report}, ensure_ascii=False, indent=1))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True); ap.add_argument("--out", required=True); ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    try:
        r = build(a.owner, a.out, a.draft)
    except GlowupError as err:
        sys.exit(f"glow-up stopped: {err}")
    print(f"glow-up page → {a.out}/site · {len(r['photos'])} images cleaned · GPS removed from {r['gps_removed']}")
