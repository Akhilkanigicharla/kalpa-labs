# Run: python3 00-hq/marketing/test_marketing.py  (offline; renders one week for one world)
import datetime as dt, json, pathlib, re, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run as M
from PIL import Image
from social import compliance as C, copywriter, plan

START = dt.date(2026, 10, 19)
TOKENS = (M.HQ / "design" / "tokens.css").read_text()
LIGHT = dict(re.findall(r"--(l\d):(#[0-9A-Fa-f]{6})", TOKENS.split("@media")[0]))

ws = M.worlds()
assert set(ws) == {"hq", "b1", "b2", "b3", "b4", "b5", "b6", "b7"}, ws
for w in ws:
    cfg = M.load(w)
    accent = cfg["theme"][1].upper()
    assert accent in {v.upper() for v in LIGHT.values()}, f"{w}: colour {accent} is not a Kalpa --lN token"
    assert all(pathlib.Path(f).exists() for f in cfg["fonts"].values()), w
    assert "[add link]" in cfg["cta"]["url"] or cfg["cta"]["url"].startswith("https://"), "links are real or clearly pending"
print(f"  ✓ {len(ws)} brand profiles: Kalpa --lN colours, Kalpa fonts present, links real or pending")

# every enabled world: a month of posts, all compliant except the pending-link / needs-real-content holds
for w in ws:
    cfg = M.load(w)
    m = M.build(w, START, 4, pathlib.Path(tempfile.mkdtemp()), render=False)
    if w == "b7":
        assert m is None, "Trading Lab must never post (SEBI)"
        continue
    assert len(m["items"]) == 20, w
    for it in m["items"]:
        other = [b for b in it["check"]["blocked"] if "placeholder" not in b]
        assert not other, (w, it["id"], other)
        assert "wa.me/" not in it["caption"], "Kalpa's own posts link to the product, not a WhatsApp number"
        assert cfg["cta"]["label"] in it["caption"]
    if cfg.get("affiliate"):
        assert all("#ad" in it["caption"].lower() for it in m["items"]), "affiliate posts carry #ad (ASCI)"
    if cfg.get("telugu") is False:
        assert all(not it["telugu"] for it in m["items"])
print("  ✓ a month for each world; only pending links / real photos / reviews hold posts; b7 never posts; #ad on affiliate")

# world-specific compliance
fin = M.load("b6")
assert not C.check("Get 100% DPDP compliant in a week https://x", setup="finops", cfg=fin)["ok"]
assert not C.check("ISO 42001 certified pack https://x", setup="finops", cfg=fin)["ok"]
assert not C.check("Save 40% on AI bills https://x", setup="finops", cfg=fin)["ok"]
assert C.check("Track AI cost per customer in rupees https://x", setup="finops", cfg={})["ok"]
assert not C.check("Buy NIFTY above 24000, target 24500 https://x", setup="trading", cfg={})["ok"]
assert not C.check("Great deal https://x", setup="deals", cfg={"affiliate": True})["ok"]
assert C.check("Great deal #ad https://x", setup="deals", cfg={"affiliate": True})["ok"]
assert C.check("Never lose a tab again https://x", setup="extensions", cfg={})["warnings"]
assert not C.check("Try it: [add link]", setup="kits", cfg={})["ok"]
print("  ✓ world rules: finops (no compliance/certification/savings claims), trading (no tips), deals (#ad), extensions, pending links")

# with a real link the posts that need nothing else are ready
live = M.load("b4")
live["cta"]["url"] = "https://chromewebstore.google.com/example"
s0 = plan.month_plan(live, START, 1)
ok = [C.check(copywriter.write(s, live, i)["caption"], setup="extensions", cfg=live)["ok"] for i, s in enumerate(s0)]
assert any(ok), "once the link is real, tip/offer posts pass"
print("  ✓ adding the real link releases the posts that need nothing else")

# rendering in the Kalpa look (one world, one week)
out = pathlib.Path(tempfile.mkdtemp())
m = M.build("b6", START, 1, out)
files = [out / "b6" / f for it in m["items"] for f in it["files"] if f.endswith(".jpg")]
assert files and all(Image.open(f).size in ((1080, 1350), (1080, 1920)) for f in files)
px = Image.open(files[0]).convert("RGB").getpixel((1060, 20))
want = tuple(int(LIGHT["l5"][i:i + 2], 16) for i in (1, 3, 5))
assert all(abs(a - b) <= 3 for a, b in zip(px, want)), (px, want)  # JPEG may shift a channel by 1-2
print("  ✓ Ledger Peaks renders 1080x1350 / 1080x1920 in its --l5 gold")
print("MARKETING TEAM TESTS PASSED")
