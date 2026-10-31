# Run: python3 social/test_captions.py  (offline: no model; the ffmpeg burn part runs only when ffmpeg exists)
import pathlib, shutil, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from social import captions as cc
from social.captions import Word


def raises(fn, *a):
    try:
        fn(*a)
    except ValueError:
        return True
    return False


# 1. Script alignment: script words keep their order, cover Whisper's span, and a pause in the audio stays a pause.
heard = [Word(1.0, 1.4, "chala"), Word(1.4, 2.0, "sandarbalu"), Word(5.0, 5.5, "adi"), Word(5.5, 6.0, "naku")]
al = cc.align_script("చాలా సందర్భాల్లో అది నాకు", heard)
assert [w.text for w in al] == ["చాలా", "సందర్భాల్లో", "అది", "నాకు"]
assert abs(al[0].start - 1.0) < 1e-6 and abs(al[-1].end - 6.0) < 0.2, al
assert all(a.start <= b.start for a, b in zip(al, al[1:])) and all(w.end > w.start for w in al)
assert al[2].start >= 4.5, f"word after the pause starts too early: {al[2]}"
# 1b. A sentence break in the script lands on the pause, even when the script's first sentence is much longer.
long_first = "one two three four five six seven eight nine ten. Last bit"
al = cc.align_script(long_first, [Word(0.0, 3.0, "abc"), Word(5.0, 8.0, "abcdefgh")])
assert al[9].end <= 3.0 + 1e-9 and al[10].start >= 5.0 - 1e-9, al
# 1c. Snap: a word that runs into silence is cut back to the speech; a word wholly in silence moves to the edge.
sn = cc.snap([Word(1.0, 3.5, "a"), Word(3.6, 3.9, "b")], [(0.9, 2.0), (4.0, 6.0)])
assert (sn[0].start, sn[0].end) == (1.0, 2.0) and (sn[1].start, sn[1].end) == (4.0, 4.2), sn
sn = cc.snap([Word(1.0, 1.5, "a"), Word(1.5, 2.2, "b")], [(0.9, 2.6)])
assert sn[0].end == 1.5 and sn[1].end == 2.6, "last word of a phrase is stretched to the end of the speech"
assert [w.text for w in cc.segment_anchors([(0, 1), (2, 2.5)])] == ["x" * 15, "x" * 8]
assert raises(cc.align_script, "  ", heard) and raises(cc.align_script, "a b", [])

# 2. Wrapping: short text = 1 line; longer = 2 balanced lines within the limit.
assert cc.wrap(["Hello", "there"], 28) == ["Hello there"]
two = cc.wrap("Welcome to this three bedroom home in Kondapur".split(), 28)
assert len(two) == 2 and all(len(x) <= 28 for x in two) and " ".join(two) == "Welcome to this three bedroom home in Kondapur"

# 3. Cues: never over 2 lines or the line limit; a long pause and a sentence end start a new cue; no overlaps.
ws, t = [], 0.0
for i, w in enumerate("Welcome to this three bedroom home in Kondapur. Bright morning sun, two car parks".split()):
    ws.append(Word(t, t + 0.35, w)); t += 0.4
ws.append(Word(t + 1.5, t + 1.9, "WhatsApp"))
cs = cc.cues(ws, "en")
assert all(len(c["lines"]) <= 2 and all(len(x) <= 28 for x in c["lines"]) for c in cs), cs
assert any(c["lines"][-1].endswith("Kondapur.") for c in cs), "sentence end must close a cue"
assert cs[-1]["lines"] == ["WhatsApp"], "a long pause must start a new cue"
assert all(a["end"] <= b["start"] + 1e-9 for a, b in zip(cs, cs[1:])), "cues overlap"
assert all(c["end"] - c["start"] <= cc.MAX_CUE_S + cc.HOLD_S for c in cs)
assert cc.cues([], "te") == []

# 4. SRT and ASS text: right timestamps, Kalpa fonts per language, text can't inject ASS override tags.
s = cc.srt([{"start": 1.25, "end": 3.5, "lines": ["a", "b"]}])
assert s == "1\n00:00:01,250 --> 00:00:03,500\na\nb\n\n", s
a = cc.ass([{"start": 61.2, "end": 62.0, "lines": ["{\\b1}x", "y"]}], "te")
assert "Anek Telugu" in a and "0:01:01.20,0:01:02.00" in a and r"(b1)x\Ny" in a and "{\\b1}" not in a
assert "Anek Devanagari" in cc.ass([], "hi") and "Anek Latin" in cc.ass([], "en")
for lang, fam in cc.FONT.items():  # the burn step finds these fonts by family name in the design folder
    assert any(cc.FONTS_DIR.glob(f"{fam.lower().replace(' ', '-')}-*-700-normal.woff")), f"{fam} font missing"
assert cc._ass_colour("#0F1912", 0x30) == "&H3012190F"

# 5. Burn: a 3 s test video gets captions drawn in the lower third (pixels change there, not at the top).
ff = shutil.which("ffmpeg")
if ff:
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        src = d / "in.mp4"
        subprocess.run([ff, "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=0x2F6F78:s=1080x1920:d=3",
                        "-f", "lavfi", "-i", "sine=f=440:d=3", "-shortest", "-pix_fmt", "yuv420p", str(src)], check=True)
        for lang, line in (("te", "మా సెలూన్‌కి స్వాగతం"), ("hi", "हमारे सैलून में स्वागत है"), ("en", "Welcome to our salon")):
            out = cc.burn(src, cc.ass([{"start": 0.5, "end": 2.5, "lines": [line]}], lang), d / f"out-{lang}.mp4")
            assert out and out.exists(), f"burn failed for {lang}"
            frames = []
            for t in ("0.1", "1.5"):
                frames.append(subprocess.run([ff, "-nostdin", "-v", "error", "-ss", t, "-i", str(out), "-frames:v", "1",
                                              "-vf", "scale=108:192,format=gray", "-f", "rawvideo", "-"],
                                             capture_output=True, check=True).stdout)
            diff = [abs(a - b) > 30 for a, b in zip(*frames)]
            lower = sum(diff[108 * 150:108 * 175]); top = sum(diff[:108 * 100])
            assert lower > 20 and top == 0, f"{lang}: captions not in the lower third (lower={lower}, top={top})"
            has_audio = subprocess.run([ff, "-nostdin", "-v", "error", "-i", str(out), "-map", "0:a", "-f", "null", "-"],
                                       capture_output=True).returncode == 0
            assert has_audio, "audio must be kept"
        # the longest allowed lines still fit inside the frame (no clipping at the sides)
        for lang, base in (("en", "Welcome to our salon in Kondapur "), ("te", "విదేశాల్లో ఒక గ్యాప్ ఇయర్ కోర్సులో చేరడం "),
                           ("hi", "हमारे सैलून में आपका स्वागत है जी आइए ")):
            line = (base * 3)[:cc.MAX_LINE[lang]]
            out = cc.burn(src, cc.ass([{"start": 0, "end": 3, "lines": [line, line]}], lang), d / f"wide-{lang}.mp4")
            px = subprocess.run([ff, "-nostdin", "-v", "error", "-ss", "1", "-i", str(out), "-frames:v", "1", "-vf",
                                 "format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
            cols = [x for x in range(1080) if any(px[y * 1080 + x] < 40 for y in range(1400, 1700, 4))]
            assert cols and cols[0] >= 40 and cols[-1] <= 1040, f"{lang}: caption box too wide ({cols[0]}..{cols[-1]})"
else:
    print("(burn test skipped: no ffmpeg)")

print("captions tests passed")
