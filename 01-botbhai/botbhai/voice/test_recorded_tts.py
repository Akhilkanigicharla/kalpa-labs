# Run: python3 voice/test_recorded_tts.py  (stdlib only: no torch, no model download, no network, no keys)
# A56 check (offline part): sample text loading, speaker prompts, output names, provider switch.
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import recorded_tts as R

HERE = os.path.dirname(os.path.abspath(__file__))


def raises(fn, *a):
    try:
        fn(*a)
    except ValueError:
        return True
    return False


# 1. The shipped samples file: exactly 3 Telugu + 1 English, recommended speakers, unique ids.
items = R.load_lines(os.path.join(HERE, "samples.txt"))
langs = [i["lang"] for i in items]
assert langs.count("te") == 3 and langs.count("en") == 1 and len(items) == 4, langs
assert len({i["id"] for i in items}) == 4
assert all(i["speaker"] in R.SPEAKERS[i["lang"]]["recommended"] for i in items)
assert all(any("ఀ" <= ch <= "౿" for ch in i["text"]) for i in items if i["lang"] == "te"), "Telugu lines must be in Telugu script"
print("  ✓ samples.txt: 3 Telugu + 1 English lines, recommended speakers, Telugu script")

# 2. Parsing rules: comments/blank lines skipped, bad rows rejected with a clear error.
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "t.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# comment\n\n a1 | te | Prakash |  నమస్కారం  \n")
    assert R.load_lines(p) == [{"id": "a1", "lang": "te", "speaker": "Prakash", "text": "నమస్కారం"}]
    for bad in ("x | te | Prakash", "x | ta | Prakash | hi", "x | te | Mary | hi", "x | te | Prakash |  ",
                "../x | te | Prakash | hi", "x | en | Mary | " + "a" * (R.MAX_CHARS + 1)):
        assert raises(R.parse_line, bad, 1), bad
    with open(p, "w", encoding="utf-8") as f:
        f.write("a | en | Mary | one\na | en | Mary | two\n")
    assert raises(R.load_lines, p), "duplicate ids must fail"
    with open(p, "w", encoding="utf-8") as f:
        f.write("# nothing\n")
    assert raises(R.load_lines, p), "empty file must fail"
print("  ✓ parser skips comments, rejects missing fields, unknown language/speaker, bad ids, long text, duplicates")

# 3. Speaker prompt: names the speaker (Parler needs the exact name) and asks for clean studio audio.
desc = R.describe("Lalitha")
assert desc.startswith("Lalitha's voice") and "very clear audio" in desc and "close up" in desc
assert "slow" in R.describe("Prakash", pace="slow") and "slow" not in desc
assert raises(R.describe, "Nobody")
print("  ✓ speaker prompt names the voice and asks for 'very clear audio'")

# 4. Output names: stable, lowercase, safe for artifacts.
assert R.out_name({"id": "te-1-voicenote", "lang": "te", "speaker": "Lalitha"}) == "te-1-voicenote-te-lalitha.wav"
names = [R.out_name(i) for i in items]
assert len(set(names)) == 4 and all(n == n.lower() and n.endswith(".wav") for n in names)
print("  ✓ output names: <id>-<lang>-<speaker>.wav")

# 5. Provider switch: recorded voice defaults to free Parler; Sarvam only when asked; anything else is an error.
assert R.provider({}) == "parler" and R.provider({"RECORDED_TTS": "Sarvam "}) == "sarvam"
assert raises(R.provider, {"RECORDED_TTS": "elevenlabs"})
assert R.speaker_for("te-IN", "male") == "Prakash" and R.speaker_for("te", "female") == "Lalitha"
assert R.speaker_for("hi-IN", "female") == "Divya" and R.speaker_for("xx", "female") == "Mary"
assert R.MODEL_ID == "ai4bharat/indic-parler-tts"
print("  ✓ RECORDED_TTS switch (parler default, sarvam optional) and per-language speaker pick")

# 6. Dry run lists planned files without importing torch or parler_tts.
with tempfile.TemporaryDirectory() as d:
    planned = R.main(["--text", os.path.join(HERE, "samples.txt"), "--out", d, "--dry-run"])
    assert len(planned) == 4 and all(x.startswith(d) and x.endswith(".wav") for x in planned)
    assert "torch" not in sys.modules and "parler_tts" not in sys.modules and os.listdir(d) == []
print("  ✓ --dry-run plans 4 WAVs with no model download")
print("RECORDED TTS TESTS PASSED")
