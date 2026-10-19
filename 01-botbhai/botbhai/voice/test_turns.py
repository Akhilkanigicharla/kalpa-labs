# Run: python voice/test_turns.py  (needs: pip install -r voice/requirements.txt; no network, no keys)
# A06 check: turn-taking settings are really applied to Pipecat objects.
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import prompt as P
import turns as T

up = T.user_params()
assert up.vad_analyzer is not None and up.vad_analyzer.params.stop_secs == 0.2
stop = up.user_turn_strategies.stop
assert len(stop) == 1 and type(stop[0]).__name__ == "TurnAnalyzerUserTurnStopStrategy"
analyzer = stop[0]._turn_analyzer
assert type(analyzer).__name__ == "LocalSmartTurnAnalyzerV3" and analyzer.params.stop_secs == 1.2
print("  ✓ Silero VAD stop_secs 0.2, smart-turn v3.2 with a 1.2 s silence cap")

assert T.tts_language({"voice_language": "te"}) == "te" and T.tts_language({}) == "en"
assert str(T.pipecat_language({"voice_language": "hi"}).value).startswith("hi")
assert P.voice_profile({"id": "salon", "voice_language": "te"})["language"] == "te-IN"
from pipecat.services.sarvam.tts import SarvamTTSService
s = SarvamTTSService.Settings(model="bulbul:v3", voice="priya", language=T.pipecat_language({"voice_language": "te"}))
assert str(s.language.value) == "te"
print("  ✓ Sarvam TTS language follows the client's voice_language (te/hi/en)")

# Sarvam saaras:v4 keyterms (Pipecat 1.13): business words the caller will say, so STT hears them right.
# Limits from docs.sarvam.ai keyterms page + pipecat stt.py: max 50 terms, 64 chars each, one phrase per item.
for sid in ("salon", "gym", "realestate", "examkits"):
    cfg = P.load_setup(sid)
    kt = T.stt_keyterms(cfg)
    assert 0 < len(kt) <= 50 and all(0 < len(k) <= 64 and "," not in k for k in kt), (sid, kt)
    assert cfg["business"][:64] in kt and len(set(k.lower() for k in kt)) == len(kt), (sid, kt)
    assert any(c["name"][:64] in kt for c in cfg["catalog"]), sid
big = {"business": "B" * 80, "catalog": [{"name": f"Service number {i}, deluxe"} for i in range(80)], "keyterms": ["Ameerpet"]}
kt = T.stt_keyterms(big)
assert len(kt) == 50 and kt[0] == "B" * 64 and "Ameerpet" in kt and all("," not in k for k in kt)
from pipecat.services.sarvam.stt import SarvamSTTService
stt = SarvamSTTService(api_key="test-not-a-key", mode="codemix", keyterms=T.stt_keyterms(P.load_setup("salon")),
                       settings=SarvamSTTService.Settings(model=T.STT_MODEL))
assert T.STT_MODEL == "saaras:v4" and stt._keyterms and stt._settings.model == "saaras:v4"
print("  ✓ STT saaras:v4 with up to 50 business keyterms (names, services) per client")

src = open(os.path.join(os.path.dirname(__file__), "agent.py")).read()
assert "keyterms=T.stt_keyterms(cfg)" in src and 'model=T.STT_MODEL' in src
assert "vad_analyzer=SileroVADAnalyzer()" not in src and "user_params=T.user_params()" in src
assert "language=T.pipecat_language(cfg)" in src
print("  ✓ agent.py: no transport VAD (barge-in works), aggregator gets our params")

# latency of the end-of-turn model on CPU (synthetic 8 s audio at 16 kHz)
rng = np.random.default_rng(0)
audio = (rng.standard_normal(16000 * 8) * 0.05).astype(np.float32)
analyzer._predict_endpoint(audio)  # warm-up
t = time.perf_counter(); n = 20
for _ in range(n):
    out = analyzer._predict_endpoint(audio)
ms = (time.perf_counter() - t) / n * 1000
assert "prediction" in out and ms < 500, (out, ms)
print(f"  ✓ smart-turn v3.2 inference {ms:.0f} ms per 8 s window on 1 CPU thread")
print("voice turn tests passed")
