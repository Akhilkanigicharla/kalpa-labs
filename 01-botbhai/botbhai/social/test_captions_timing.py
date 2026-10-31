# A99 check: real speech clips (Telugu, Hindi, English) get captions timed to within 0.5 s.
# Run: python3 social/test_captions_timing.py [te hi en]   (needs faster-whisper + ffmpeg; downloads the models once)
# Fixtures: fixtures/captions/<lang>.opus = 1.0 s silence + FLEURS clip 1 + 2.0 s silence + FLEURS clip 2
# (Google FLEURS, CC BY 4.0; see fixtures/captions/README.md). Ground truth = where the sound is, measured
# from the audio itself (20 ms energy frames), so the check doesn't trust Whisper or its VAD to grade themselves.
# Telugu is checked in script mode only (captions.py refuses Telugu without the script).
# In CI set REQUIRE_WHISPER=1 so a missing faster-whisper fails instead of skipping.
import json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from social import captions as cc

TOL = 0.5
FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "captions"

try:
    import faster_whisper  # noqa: F401
    import numpy as np
except ImportError:
    if os.environ.get("REQUIRE_WHISPER"):
        raise
    print("(captions timing test skipped: pip install faster-whisper==1.2.1)")
    sys.exit(0)


def speech_edges(audio, start_s, end_s, rate=16000, frame=0.02):
    """First and last frame with sound between start_s and end_s: energy above 10% of the clip's peak RMS and
    above 3x its background noise (10th-percentile frame), so room noise at the end of a recording isn't speech."""
    seg = audio[int(start_s * rate):int(end_s * rate)]
    n = int(frame * rate)
    rms = np.sqrt(np.mean(seg[: len(seg) // n * n].reshape(-1, n) ** 2, axis=1))
    on = np.nonzero(rms > max(0.1 * rms.max(), 3 * np.percentile(rms, 10)))[0]
    return start_s + on[0] * frame, start_s + (on[-1] + 1) * frame


meta = json.loads((FIX / "fleurs.json").read_text(encoding="utf-8"))
langs = sys.argv[1:] or list(cc.LANGS)
for lang in langs:
    m = meta[lang]
    c1, c2 = m["clips"]
    audio = cc.load_audio(FIX / f"{lang}.opus")
    a_end = m["lead_s"] + c1["seconds"]
    b_start = a_end + m["gap_s"]
    on1, off1 = speech_edges(audio, m["lead_s"], a_end)
    on2, off2 = speech_edges(audio, b_start, b_start + c2["seconds"])
    script = c1["text"] + "\n" + c2["text"]
    modes = [("script", script)] if lang == "te" else [("whisper", ""), ("script", script)]
    for mode, text in modes:
        words = cc.timed_words(audio, lang, text)
        assert words, f"{lang}: no words"
        cs = cc.cues(words, lang)
        first2 = min((c for c in cs if c["start"] >= a_end), key=lambda c: c["start"], default=None)
        last1 = max((c for c in cs if c["start"] < a_end), key=lambda c: c["start"])
        errs = {"clip1 start": cs[0]["start"] - on1, "clip1 end": last1["end"] - off1,
                "clip2 start": (first2["start"] - on2) if first2 else 99, "clip2 end": cs[-1]["end"] - off2}
        print(f"{lang} {mode:7s} cues={len(cs):2d} " + " ".join(f"{k}={v:+.2f}s" for k, v in errs.items()))
        bad = {k: v for k, v in errs.items() if abs(v) > TOL}
        assert not bad, f"{lang} {mode}: captions off by more than {TOL} s: {bad}"
        mid = (a_end + b_start) / 2
        assert not any(c["start"] < mid < c["end"] for c in cs), f"{lang} {mode}: a caption stays up through the silence"
        assert all(len(c["lines"]) <= 2 for c in cs)

print("captions timing test passed (within 0.5 s): " + ", ".join(langs))
