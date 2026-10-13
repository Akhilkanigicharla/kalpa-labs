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

src = open(os.path.join(os.path.dirname(__file__), "agent.py")).read()
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
