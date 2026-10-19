"""Turn-taking and voice settings for the phone agent (A06, from research a2 + Deep Scan v2).

- Silero VAD stop_secs 0.2: speech end is noticed fast, so barge-in works.
- smart-turn v3.2 (bundled in Pipecat, BSD-2, 8.7 MB ONNX, CPU) decides if the caller has
  finished. Its silence fallback is capped at 1.2 s (Pipecat's default is 3 s; Telugu is not
  in smart-turn's training data, so a misjudged turn used to wait up to 3 s).
- The VAD lives in the user aggregator, NOT the transport (a2 found that the transport VAD
  disabled interruptions in Pipecat 1.12).
- Sarvam TTS speaks the client's main language (te-IN / hi-IN / en-IN); Pipecat defaults to en-IN.
"""
from __future__ import annotations

VAD_STOP_SECS = 0.2
TURN_STOP_SECS = 1.2
LANGS = {"te": "te-IN", "hi": "hi-IN", "en": "en-IN"}


STT_MODEL = "saaras:v4"  # needed for keyterms (Pipecat 1.13 + docs.sarvam.ai keyterms page, checked 19 Oct 2026)
MAX_KEYTERMS, MAX_KEYTERM_CHARS = 50, 64


def stt_keyterms(cfg: dict) -> list[str]:
    """Words callers will say that generic STT mishears: business name, client extras (staff, landmarks),
    services, and the address areas. One phrase per item, no commas, max 50 x 64 chars, no duplicates.
    Keyterms only bias recognition; they never force a word into the transcript."""
    raw = [cfg.get("business", "")] + list(cfg.get("keyterms") or [])
    raw += [c.get("name", "") for c in cfg.get("catalog") or []]
    raw += [p for p in str(cfg.get("address", "")).split(",")[1:] if not any(ch.isdigit() for ch in p)]
    out, seen = [], set()
    for term in raw:
        term = " ".join(str(term).replace(",", " ").split())[:MAX_KEYTERM_CHARS].strip()
        if term and term.lower() not in seen:
            seen.add(term.lower()); out.append(term)
    return out[:MAX_KEYTERMS]


def tts_language(cfg: dict) -> str:
    code = str(cfg.get("voice_language") or cfg.get("language") or "en").lower()[:2]
    return code if code in LANGS else "en"


def user_params():
    """LLMUserAggregatorParams with our VAD + smart-turn settings (needs pipecat installed)."""
    from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
    from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.audio.vad.vad_analyzer import VADParams
    from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
    from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import TurnAnalyzerUserTurnStopStrategy
    from pipecat.turns.user_turn_strategies import UserTurnStrategies
    return LLMUserAggregatorParams(
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=VAD_STOP_SECS)),
        user_turn_strategies=UserTurnStrategies(stop=[TurnAnalyzerUserTurnStopStrategy(
            turn_analyzer=LocalSmartTurnAnalyzerV3(params=SmartTurnParams(stop_secs=TURN_STOP_SECS)))]))


def pipecat_language(cfg: dict):
    from pipecat.transcriptions.language import Language
    return {"te": Language.TE, "hi": Language.HI, "en": Language.EN}[tts_language(cfg)]
