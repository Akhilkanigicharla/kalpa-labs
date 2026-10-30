# Run: python3 social/test_voiceover.py  (offline: the TTS model is mocked; ffmpeg part runs only when ffmpeg exists)
import io, pathlib, shutil, subprocess, sys, tempfile, wave
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from social import voiceover as vo

RATE = 16000


def fake_wav(n_sec=0.5, rate=RATE):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"\x01\x00" * int(rate * n_sec))
    return b.getvalue()


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except ValueError:
        return True
    return False


# 1. Splitting: short script = one chunk; long Telugu script = several chunks, none over the cap, no text lost.
assert vo.split_script("Hello. Welcome!") == ["Hello. Welcome!"]
te = "నమస్కారం! ఈ 3 BHK ఇల్లు కొండాపూర్‌లో ఉంది. " * 30
chunks = vo.split_script(te)
assert len(chunks) > 1 and all(len(c) <= vo.MAX_CHARS for c in chunks), [len(c) for c in chunks]
assert " ".join(chunks).split() == te.split()
hi = "यह घर बहुत सुंदर है। आज ही देखें।"
assert vo.split_script(hi, max_chars=20) == ["यह घर बहुत सुंदर है।", "आज ही देखें।"]
long_word_run = "a " * 400  # no sentence end at all: cut at spaces
assert all(len(c) <= vo.MAX_CHARS for c in vo.split_script(long_word_run))
assert raises(vo.split_script, "   ") and raises(vo.split_script, "x" * (vo.MAX_SCRIPT + 1))
print("  ✓ split: sentence chunks under the cap, nothing lost, empty/too long refused")

# 2. Join: lengths add up with the pauses; mismatched formats refused.
two = vo.join_wavs([fake_wav(0.5), fake_wav(1.0)])
assert abs(vo.seconds(two) - (1.5 + vo.GAP_MS / 1000)) < 0.01
assert raises(vo.join_wavs, [fake_wav(0.5), fake_wav(0.5, rate=22050)]) and raises(vo.join_wavs, [])
print("  ✓ join: one WAV, pauses between chunks, format mismatch refused")

# 3. Voices: recommended per language, unknown language or wrong-language voice refused.
assert vo.pick_speaker("te") == "Lalitha" and vo.pick_speaker("te", gender="male") == "Prakash"
assert vo.pick_speaker("en") == "Mary" and vo.pick_speaker("hi", "Rohit") == "Rohit"
assert raises(vo.pick_speaker, "ta") and raises(vo.pick_speaker, "te", "Mary")
print("  ✓ voices: te/en/hi recommended voices, wrong voice or language refused")

# 4. Render with a mocked model: one call per chunk, right voice, a real WAV on disk.
calls = []
def tts(text, speaker):
    calls.append((text, speaker)); return fake_wav(0.4)
tmp = pathlib.Path(tempfile.mkdtemp())
out = vo.render(te, "te", tmp / "v" / "te.wav", tts=tts)
assert out.exists() and len(calls) == len(chunks) and {s for _, s in calls} == {"Lalitha"}
assert abs(vo.seconds(out.read_bytes()) - (0.4 * len(chunks) + vo.GAP_MS / 1000 * (len(chunks) - 1))) < 0.01
calls.clear()
vo.render("A sunny 2 BHK in Gachibowli. Call us today.", "en", tmp / "en.wav", speaker="Thoma", tts=tts)
assert [s for _, s in calls] == ["Thoma"]
print("  ✓ render: te + en WAVs, one model call per chunk, chosen voice used")

# 5. CLI dry run touches nothing; the WAV works as walkthrough --voice (audio stream in the MP4).
assert vo.main(["--lang", "en", "--text", "Hi there.", "--out", str(tmp / "dry.wav"), "--dry-run"]) is None
assert not (tmp / "dry.wav").exists()
if shutil.which("ffmpeg") and shutil.which("ffprobe"):
    from PIL import Image
    from social import plan, walkthrough as wk
    photos = []
    for i in range(6):
        p = tmp / f"p{i}.jpg"; Image.new("RGB", (640, 480), (40 * i, 120, 90)).save(p); photos.append(p)
    voice = tmp / "voice.wav"; voice.write_bytes(fake_wav(3.0))
    cfg = plan.load_setup("realestate")
    mp4 = wk.build(photos, wk.captions_for(6, ["Hall"], "Test"), cfg, tmp / "walk.mp4", voice, seconds_each=1.0)
    assert mp4 and mp4.exists()
    kinds = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(mp4)],
                           capture_output=True, text=True).stdout.split()
    assert "audio" in kinds and "video" in kinds, kinds
    print("  ✓ walkthrough --voice: MP4 has the voice-over audio track")
else:
    print("  (walkthrough audio check skipped: no ffmpeg)")
shutil.rmtree(tmp)
print("voiceover: all checks passed")
