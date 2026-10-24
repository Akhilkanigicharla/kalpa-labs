# Run: python3 social/test_social.py  (offline: no network, no tokens; Reel MP4 checked only when ffmpeg exists)
import datetime as dt, json, pathlib, shutil, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from PIL import Image
from social import analyst, approve, compliance as C, copywriter, design, plan, publish, team

START = dt.date(2026, 10, 15)

# 1. Strategist: 4 weeks = 12 feed posts + 8 stories, sorted, weekly format mix, festivals, nothing before the start.
for setup in ["salon", "gym", "realestate", "examkits"]:
    cfg = plan.load_setup(setup)
    slots = plan.month_plan(cfg, START, 4)
    assert len(slots) == 20, (setup, len(slots))
    assert [s["date"] + s["time"] for s in slots] == sorted(s["date"] + s["time"] for s in slots)
    assert all(s["date"] >= START.isoformat() for s in slots)
    assert len({s["id"] for s in slots}) == 20
    kinds = [s["kind"] for s in slots]
    assert kinds.count("reel") == kinds.count("carousel") == kinds.count("post") == 4 and kinds.count("story") == 8
    assert {s["festival"] for s in slots if s["pillar"] == "festival"} >= {"Dussehra"}, setup
    feed = [s["pillar"] for s in slots if s["kind"] != "story" and s["pillar"] != "festival"]
    assert feed.count("offer") <= 3, ("selling should stay a minority", setup, feed)
seq = plan._pillar_sequence(12, plan.PILLARS)
assert all(a != b for a, b in zip(seq, seq[1:])) and seq.count("tip") == 4, seq
print("  ✓ strategist: 20 slots/4 weeks, 1 reel + 1 carousel + 1 post + 2 stories a week, festival hooks, no repeats")

# 2. Copywriter + compliance on every slot of every setup.
for setup in ["salon", "gym", "realestate", "examkits"]:
    cfg = plan.load_setup(setup)
    for i, s in enumerate(plan.month_plan(cfg, START, 4)):
        c = copywriter.write(s, cfg, i)
        assert len(c["caption"]) <= 2200 and "wa.me/" in c["caption"]
        assert 3 <= c["caption"].count("#") <= 5, c["caption"]
        assert c["telugu"] and c["headline"]
        r = C.check(c["caption"], setup=setup, cfg=cfg)
        assert not any("guarantee" in b or "fairness" in b or "cure" in b for b in r["blocked"]), (setup, r)
        if s["pillar"] == "proof":
            assert not r["ok"] and c["needs"], "fake reviews must never go out"
        if s["kind"] == "reel":
            assert len(c["script"]) == 3
re_cfg = plan.load_setup("realestate")
c = copywriter.write({"id": "x", "kind": "post", "pillar": "offer", "service": re_cfg["catalog"][0]["name"], "festival": None}, re_cfg)
assert not C.check(c["caption"], setup="realestate")["ok"] and any("rera" in n for n in c["needs"])
re_ok = plan.load_setup("realestate", {"rera_number": "P02400001234"})
c = copywriter.write({"id": "x", "kind": "post", "pillar": "offer", "service": re_ok["catalog"][0]["name"], "festival": None}, re_ok)
assert C.check(c["caption"], setup="realestate")["ok"] and "TG RERA: P02400001234" in c["caption"]
ip = [copywriter.write(s, cfg, i) for i, s in enumerate(plan.month_plan(plan.load_setup("salon"), START, 4))]
assert all(c["image_prompt"] is None for c, s in zip(ip, plan.month_plan(plan.load_setup("salon"), START, 4)) if s["pillar"] in ("work", "proof", "team"))
tip = next(c["image_prompt"] for c in ip if c["image_prompt"])
assert all(k in tip for k in ("Subject:", "Scene:", "Format:", "Avoid:")) and "faces" in tip
print("  ✓ image prompts: structured fields for tip/offer/festival only; never for real work, reviews or team")
print("  ✓ copywriter: captions ≤2,200 chars, 3-5 hashtags, WhatsApp CTA, Telugu line; reviews/RERA wait for the owner")

BAD = {"Guaranteed results in 1 sitting": "guarantee", "100% selection in TSPSC": "100%", "Permanent hair removal": "permanent",
       "Our oil cures hair fall": "cure", "Fairness facial offer": "fairness", "Lose 10 kg in 30 days": "weight",
       "Assured returns on your plot": "assured", "Pre-launch price, book now": "pre-launch", "No side effects, miracle glow": "miracle"}
for text, why in BAD.items():
    r = C.check(text + " wa.me/91", setup="salon")
    assert not r["ok"], (text, r)
assert not C.check("Diwali glow facial, Rs 999 wa.me/1", setup="salon", paid_partnership=True)["ok"]
assert C.check("Diwali glow facial, Rs 999 #ad wa.me/1", setup="salon", paid_partnership=True)["ok"]
assert C.check("Haircut " + "#a " * 7 + " wa.me/1")["warnings"]
assert not C.check("x" * 2201 + " wa.me/1")["ok"]
assert C.check("AIR 12 topper from our batch wa.me/1", setup="examkits")["warnings"]
assert C.check("Glowing skin tips for Diwali. Book: wa.me/91900", setup="salon")["ok"]
print(f"  ✓ compliance: {len(BAD)} banned claim types blocked (ASCI, DMR Act, CCPA coaching, RERA), #ad rule, limits")

# 3. Designer: Instagram-ready JPEG sizes, carousel slide count, emoji/₹ never drawn as boxes, owner photo used.
out = pathlib.Path(tempfile.mkdtemp())
cfg = plan.load_setup("salon")
slots = {s["kind"]: s for s in plan.month_plan(cfg, START, 1)}
copies = {k: copywriter.write(s, cfg, 0) for k, s in slots.items()}
files = design.render(slots["carousel"], copies["carousel"], cfg, out)
assert len(files) == 4 and all(Image.open(f).size == design.FEED and Image.open(f).format == "JPEG" for f in files)
post = design.render(slots["post"], copies["post"], cfg, out)
assert Image.open(post[0]).size == design.FEED
story = design.render(slots["story"], copies["story"], cfg, out)
assert Image.open(story[0]).size == design.STORY
assert design.clean("Beard trim at ₹150 👇 ✨") == "Beard trim at Rs 150"
photo = out / "owner.jpg"
Image.new("RGB", (1600, 1200), (10, 200, 30)).save(photo)
withp = design.render(slots["post"], copies["post"], cfg, out / "p", {slots["post"]["id"]: str(photo)})
assert Image.open(withp[0]).getpixel((540, 200))[1] > 150, "owner photo should fill the top of the frame"
if shutil.which("ffmpeg"):
    reel = design.render(slots["reel"], copies["reel"], cfg, out)
    assert reel[-1].suffix == ".mp4" and reel[-1].stat().st_size > 10_000
    print("  ✓ designer: 1080x1350 feed, 1080x1920 story, 4-slide carousel, owner photo, Reel MP4")
else:
    print("  ✓ designer: 1080x1350 feed, 1080x1920 story, 4-slide carousel, owner photo (Reel skipped: no ffmpeg)")

# 4. Approval over WhatsApp.
P = approve.parse_reply
assert P("OK", 5)["approve_all"] and P("Sare 👍", 5)["approve_all"] and P("avunu", 5)["approve_all"]
r = P("skip 3, rest ok", 5)
assert r["skip"] == [3] and r["approve_all"]
r = P("change 2: make it about bridal makeup", 5)
assert r["change"] == {2: "make it about bridal makeup"} and not r["approve_all"]
assert P("skip 2 and 4", 5)["skip"] == [2, 4] and P("skip 9", 5)["skip"] == []
assert P("photo 4", 5)["photo"] == [4] and P("what is this?", 5)["unknown"]
items = [{"needs": []}, {"needs": ["photo: x"]}, {"needs": []}, {"needs": [], "check": {"ok": False, "blocked": ["x"]}}]
st = [i["status"] for i in approve.apply(items, P("skip 3, rest ok", 4))]
assert st == ["approved", "held", "skipped", "held"], st
print("  ✓ approval: OK/sare/avunu, skip N, change N: note, photo N; items missing a photo/review or failing checks stay held")

# 5. Publisher: dry run makes the documented Graph API calls; never posts unapproved or blocked items.
dry = publish.DryRun(status_sequence=("IN_PROGRESS", "FINISHED"))
pub = publish.Publisher("17840000", "https://cdn.example/s/", page_id="1010", transport=dry)
res = pub.publish({"id": "W1-carousel", "kind": "carousel", "caption": "hi", "status": "approved", "files": ["a.jpg", "b.jpg", "c.jpg"]})
paths = [p for _, p, _ in dry.calls]
assert paths[0] == "17840000/content_publishing_limit" and paths.count("17840000/media") == 4
assert paths[-2] == "17840000/media_publish" and paths[-1] == "1010/photos" and res["media_id"].startswith("pub")
car = [p for m, p, q in dry.calls if m == "POST" and q.get("media_type") == "CAROUSEL"][0]
assert car == "17840000/media"
dry2 = publish.DryRun()
publish.Publisher("1", "https://cdn.example/", transport=dry2).publish({"id": "r", "kind": "reel", "caption": "c", "status": "approved", "files": ["r-1.jpg", "r.mp4"]})
assert any(q.get("media_type") == "REELS" and q["video_url"].endswith("r.mp4") for _, _, q in dry2.calls)
for bad in [{"status": "held"}, {"status": "approved", "check": {"ok": False, "blocked": ["x"]}}]:
    try:
        pub.publish({"id": "z", "kind": "post", "files": ["a.jpg"], **bad}); raise AssertionError("must refuse")
    except publish.GraphError:
        pass
for seq, quota in [(("ERROR",), 0), (("FINISHED",), 100)]:
    try:
        publish.Publisher("1", "https://x/", transport=publish.DryRun(seq, quota=quota)).publish(
            {"id": "e", "kind": "post", "status": "approved", "files": ["a.jpg"]}); raise AssertionError("must fail")
    except publish.GraphError:
        pass
try:
    publish.Publisher("1", "https://x/", dry_run=False); raise AssertionError("live run without token must refuse")
except publish.GraphError:
    pass
its = [{"id": "a", "status": "approved", "date": "2026-10-19", "time": "19:30"}, {"id": "b", "status": "approved", "date": "2026-10-21", "time": "19:00"},
       {"id": "c", "status": "held", "date": "2026-10-18", "time": "10:00"}]
assert [i["id"] for i in publish.due(its, "2026-10-20 08:00")] == ["a"]
print("  ✓ publisher: container -> status poll -> media_publish (+FB Page), Reels, quota check; refuses held/blocked/ERROR/no-token")

# 6. Analyst: moves weight toward the pillar that earned saves/shares, keeps a floor.
rows = [{"id": "t", "pillar": "tip", "kind": "carousel", "reach": 400, "saved": 40, "shares": 12, "likes": 30},
        {"id": "o", "pillar": "offer", "kind": "post", "reach": 300, "saved": 1, "shares": 0, "likes": 5},
        {"id": "w", "pillar": "work", "kind": "reel", "reach": 900, "saved": 10, "shares": 5, "likes": 60}]
nw = analyst.new_weights(rows)
assert nw["tip"] > plan.PILLARS["tip"] and nw["offer"] < plan.PILLARS["offer"] and min(nw.values()) >= 0.04
assert abs(sum(nw.values()) - 1) < 0.01 and analyst.new_weights([]) == plan.PILLARS
rep = analyst.report(rows)
assert "1,600 people" in rep and "Reels reached the most" in rep and "'tip'" in rep, rep
print("  ✓ analyst: saves/shares-weighted score, 50/50 blend, floor; plain-English weekly report")

# 7. Whole team end to end (no rendering for speed, then one rendered week).
o = pathlib.Path(tempfile.mkdtemp())
m = team.build("gym", START, 4, o, render=False)
assert len(m["items"]) == 20 and (o / "plan.csv").exists() and json.loads((o / "manifest.json").read_text())["items"]
msg = (o / "approval.txt").read_text()
assert "Nothing posts without your OK" in msg and "⚠️ Needs" in msg
assert team.main(["--out", str(o), "--reply", "ok"]) == 0
m2 = json.loads((o / "manifest.json").read_text())
assert {i["status"] for i in m2["items"]} <= {"approved", "held"} and any(i["status"] == "approved" for i in m2["items"])
assert all(i["status"] == "held" for i in m2["items"] if i["needs"] or not i["check"]["ok"])
o2 = pathlib.Path(tempfile.mkdtemp())
m3 = team.build("examkits", START, 1, o2)
assert all((o2 / f).exists() for i in m3["items"] for f in i["files"])
print("  ✓ team: plan.csv + manifest.json + approval.txt + media; owner 'ok' approves only ready, compliant items")
# --- A96 walkthrough: listing photos -> 9:16 Reel with a camera move per photo ---
from PIL import Image as _Im
from social import walkthrough as wk
cfg_re = json.loads((pathlib.Path(__file__).resolve().parents[1] / "setups" / "realestate" / "bot.config.json").read_text())
ph = pathlib.Path(tempfile.mkdtemp())
for k in range(5):
    _Im.new("RGB", (1600, 1200), (40 * k, 120, 200 - 30 * k)).save(ph / f"{k:02d}.jpg")
try:
    wk.photos_in(ph); raise AssertionError("5 photos must be refused")
except ValueError:
    pass
_Im.new("RGB", (900, 1600), (200, 180, 90)).save(ph / "05.png")
(ph / "notes.txt").write_text("not a photo")
pics = wk.photos_in(ph)
assert len(pics) == 6 and pics[0].name == "00.jpg"
caps = wk.captions_for(6, ["Living room", "Kitchen", " "], "3 BHK, Kondapur")
assert caps[0] == "3 BHK, Kondapur · Living room" and caps[1] == "Kitchen" and caps[5] == ""
assert wk.card(pics[0], caps[0], cfg_re, "1/6").size == (1080, 1920)
g = wk.filtergraph(6, 1.0)
assert g.count("zoompan") == 6 and "concat=n=6" in g and "on/30" in g  # pan uses frames-per-photo
wo = pathlib.Path(tempfile.mkdtemp()) / "walk.mp4"
if shutil.which("ffmpeg"):
    mp4 = wk.build(pics, caps, cfg_re, wo, seconds_each=0.5)
    assert mp4 and mp4.stat().st_size > 10_000 and len(list((wo.with_suffix("")).glob("[0-9]*.jpg"))) == 6
print("  ✓ walkthrough: 6-12 photos only, captions in order, 9:16 cards, one camera move per photo, MP4")
# --- YouTube helper (rules from the MIT youtube-agent-skill) ---
from social import youtube as yt
segs = [{"start": t, "end": t + 9, "text": f"part {t} of the home tour"} for t in range(0, 300, 9)]
ch = yt.chapters_from(segs, 300)
assert ch[0][0] == 0 and len(ch) >= 3 and yt.validate_chapters(ch, 300) == []
assert yt.chapter_text(ch).startswith("00:00 Part 0") and yt.stamp(3725) == "1:02:05"
bad = yt.validate_chapters([(5, "Intro"), (12, "Kitchen")], 20)
assert any("00:00" in e for e in bad) and any("at least 3" in e for e in bad) and any("shorter" in e for e in bad)
tc = yt.title_check("3 BHK walkthrough in Kondapur | price, parking, sunlight, schools")
assert tc["ok"] and tc["desktop_cut"] and len(tc["mobile_cut"]) == 40 and not yt.title_check("x" * 101)["ok"]
assert sum(len(t) + 1 for t in yt.tags_fit(["kondapur flats"] * 60)) <= 501
dsc = yt.description(cfg_re, "Walk through a 3 BHK.", ch, affiliate=True)
assert dsc.startswith("Affiliate") and "00:00" in dsc and cfg_re.get("business", "") in dsc and len(dsc) <= 5000
print("  ✓ youtube: valid chapters from a transcript, title cut points, 500-char tags, description with CTA + disclosure")
# --- A97: posting time learned from the owner's insights CSV ---
vd = pathlib.Path(tempfile.mkdtemp())
lines = ["Publish time,Post type,Views,Account"]
for d in range(1, 6):  # 10 reels: 19:30 ones get ~400 views, 08:xx ones ~1500
    lines.append(f"2026-09-{d:02d} 19:30,IG reel,{400 + d},instagram")
    lines.append(f"2026-09-{d + 10:02d} 08:15,IG reel,\"1,{500 + d}\",instagram")
for d in range(1, 4):
    lines.append(f"2026-09-{d:02d} 11:00,IG image,900,instagram")
(vd / "views.csv").write_text("\n".join(lines) + "\n")
vrows = analyst.read_views_csv(vd / "views.csv")
assert len(vrows) == 13 and vrows[1]["views"] == 1501 and vrows[1]["hour"] == 8
now = {"reel": "19:30", "carousel": "19:00", "post": "11:00", "story": "10:00"}
bt = analyst.best_times(vrows, now)
assert bt["reel"] == "08:00" and bt["post"] == "11:00" and bt["carousel"] == "19:00"   # reel moved; others < 8 posts
assert analyst.best_times(vrows[:7], now) == now                                       # under 8 posts: nothing changes
assert analyst.best_times(vrows, now, "facebook") == now                                # other channel: no data
reel_slots = [s for s in plan.month_plan(cfg_re, START, 1, times=bt) if s["kind"] == "reel"]
assert reel_slots and all(s["time"] == "08:00" for s in reel_slots)
print("  ✓ best time: insights CSV moves the Reel slot to its best hour; under 8 posts or other channel, nothing changes")
print("SOCIAL TEAM TESTS PASSED")
