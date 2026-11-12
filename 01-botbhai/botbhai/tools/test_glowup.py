"""A199 glow-up test: permission gate, clean room paths, GPS/EXIF stripped, hostile text escaped,
then a demo rebuild must pass the 20 SEO checks, the 390 px tap sweep (light + dark) and the 3-width compare."""
import json, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
BOT = HERE.parent
sys.path.insert(0, str(BOT / "glowup"))
import glowup  # noqa: E402
from PIL import Image  # noqa: E402

TESTS = BOT.parent.parent / "00-hq" / "site" / "tests"
fails = []
ok = lambda cond, msg: None if cond else fails.append(msg)


def make_owner(d):
    (d / "media").mkdir(parents=True)
    ex = Image.Exif()
    ex[0x010F] = "PhoneMaker"; ex[0x0110] = "Model X"; ex[0x0112] = 6  # make, model, rotate 90
    ex.get_ifd(0x8825).update({1: "N", 2: (17.0, 25.0, 30.0), 3: "E", 4: (78.0, 26.0, 50.0)})  # Hyderabad GPS
    Image.new("RGB", (2400, 1600), (190, 120, 60)).save(d / "media" / "front.jpg", exif=ex)
    Image.new("RGB", (900, 900), (40, 90, 60)).save(d / "media" / "inside.jpg", exif=ex)
    Image.new("RGBA", (500, 500), (0, 0, 0, 0)).save(d / "media" / "logo.png")
    owner = {
        "business": "Sri Lakshmi Venkateswara Unisex Beauty Parlour & Bridal Studio 💇‍♀️ <script>alert(1)</script>",
        "type": "salon", "phone": "+91 98765 43210", "address": "Plot 12, Road No. 36, Jubilee Hills, Hyderabad 500033",
        "hours": "Mon–Sat 10:00–20:00", "areas": ["Jubilee Hills", "Banjara Hills"], "site_url": "https://glow.example",
        "old_site": (d / "old.html").as_uri(),
        "headline": "Bridal makeup, hair and skin care since 2009 ✨",
        "about": "We are a family salon.\n\nవధువు మేకప్ మా ప్రత్యేకత. Supercalifragilisticexpialidociouslylongwordwithoutanyspacesatall" * 1,
        "services": [{"name": "Haircut", "price": "₹300"}, {"name": "Bridal makeup <b>HD</b>", "price": "₹15,000 onwards"}],
        "faqs": [{"q": "Do you take walk-ins?", "a": "Yes, but booking on WhatsApp is faster."}],
        "logo": "logo.png", "photos": [{"file": "front.jpg", "alt": "Salon front"}, "inside.jpg"],
        "permission": {"signed_by": "Owner Name", "date": "2026-11-12", "form_version": "glowup-permission v1", "owns_content": True},
    }
    (d / "owner.json").write_text(json.dumps(owner, ensure_ascii=False))
    (d / "old.html").write_text("<html><body style='font:12px Times'><table width=1000><tr><td><h1>Old site</h1></td></tr></table></body></html>")
    return owner


def expect_error(d, owner, change, what):
    bad = json.loads(json.dumps(owner)); change(bad)
    (d / "owner.json").write_text(json.dumps(bad, ensure_ascii=False))
    try:
        glowup.build(d, d / "x")
        fails.append(f"no error for {what}")
    except glowup.GlowupError:
        pass
    (d / "owner.json").write_text(json.dumps(owner, ensure_ascii=False))


tmp = pathlib.Path(tempfile.mkdtemp())
try:
    owner = make_owner(tmp / "owner")
    o = tmp / "owner"
    expect_error(o, owner, lambda b: b.pop("permission"), "missing permission")
    expect_error(o, owner, lambda b: b["permission"].update(withdrawn=True), "withdrawn permission")
    expect_error(o, owner, lambda b: b.update(logo="https://competitor.example/logo.png"), "a web link as logo")
    expect_error(o, owner, lambda b: b.update(photos=["../../etc/passwd"]), "path outside media/")
    expect_error(o, owner, lambda b: b.update(site_url=""), "missing site_url without --draft")
    expect_error(o, owner, lambda b: b.update(services=[]), "no services")

    out = tmp / "out"
    rep = glowup.build(o, out)
    ok(rep["gps_removed"] == 2, f"GPS should be found and removed in 2 photos, got {rep['gps_removed']}")
    for f in (out / "site" / "img").iterdir():
        with Image.open(f) as im:
            ok(not im.getexif() and not im.info.get("exif") and not im.info.get("xmp"), f"metadata left in {f.name}")
            ok(max(im.size) <= glowup.MAX_SIDE, f"{f.name} not resized: {im.size}")
    with Image.open(out / "site" / "img" / "photo-1.jpg") as im:
        ok(im.size == (1067, 1600), f"photo not turned upright from EXIF orientation: {im.size}")
    page = (out / "site" / "index.html").read_text()
    ok("<script>alert(1)" not in page and "&lt;script&gt;" in page, "hostile business name not escaped")
    ok("<b>HD</b>" not in page, "hostile service name not escaped")
    ok("competitor" not in page and "http://" not in page.replace("http://www.w3.org", ""), "outside link in page")
    ok('fetchpriority="high"' in page and 'width="1067"' in page, "cover image needs size + priority")

    seo = subprocess.run([sys.executable, str(TESTS / "test_seo.py"), str(out / "site"), "https://glow.example"], capture_output=True, text=True)
    ok(seo.returncode == 0, "SEO checks failed: " + (seo.stdout + seo.stderr)[-600:])

    try:
        import playwright  # noqa: F401
        sys.path.insert(0, str(BOT / "glowup"))
        import compare
        srv, url = compare.serve(out / "site")
        try:
            tap = subprocess.run([sys.executable, str(TESTS / "test_tap_sweep.py"), url], capture_output=True, text=True, timeout=300)
        finally:
            srv.shutdown()
        ok(tap.returncode == 0, "tap sweep failed: " + tap.stdout[-600:])
        shots = compare.run(o, out / "site", out / "compare")
        ok(len(shots) == 6 and (out / "compare" / "compare.html").exists(), f"compare made {len(shots)} shots")
        with Image.open(out / "compare" / "after-360.png") as im:
            ok(im.size[0] == 360, f"360 px shot is {im.size[0]} px wide (page scrolls sideways?)")
    except ImportError:
        print("(glow-up tap sweep + compare skipped: needs Python Playwright)")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

for f in fails:
    print("FAIL", f)
print("PASS glow-up" if not fails else f"{len(fails)} glow-up problem(s)")
sys.exit(1 if fails else 0)
