# Deep scan v2: open-source voice AI for BotBhai (Telugu / Hindi / English, phone + WhatsApp voice notes)

Scanned 2026-10-13 by Deep-Scan Agent 3. This builds on `a2-voice.md` (same day) and goes wider.

**Sources.** I found candidates through the GitHub topic pages (voice-assistant, text-to-speech, speech-recognition, voice-agent, vad and indic, sorted by stars) and through Hugging Face searches for Telugu and Indic TTS and ASR (sorted by likes). Stars and last-push dates come from the ecosyste.ms API. Weight licences come from the Hugging Face API tags **and** a manual read of each model card's licence section, because several cards tag one licence and then restrict it in the text. Sarvam prices come from sarvam.ai/api-pricing on 2026-10-13.

> **Key point: the code licence and the weights licence are often different.** Six of the most-liked Telugu-capable TTS models are **non-commercial**, even where the code is Apache or MIT: OmniVoice, Fish S2-Pro, Higgs TTS 3, Sooktam-2, Rumik-oss-1 and MMS-TTS. Moshi is CC-BY (allowed, with attribution). The LiveKit turn detector is restricted to LiveKit.

## Top 30 (frameworks, turn-taking, STT, TTS)

Commercial OK? means we can use it in a product sold to clients. ✅ = yes, ⚠️ = check first, ❌ = no.

| # | Repo / model | Kind | Stars / HF likes | Last commit | Code licence | Weights licence | Commercial OK? | Telugu evidence | Latency / hardware | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) 1.12 | Voice agent framework | 16.3k | 2026-10-10 | BSD-2 | n/a | ✅ | Ships Sarvam STT/TTS services and maps `te-IN` | Frame pipeline, ~ms overhead | **ADOPT** (already in use; use more of it) |
| 2 | [pipecat-ai/smart-turn](https://github.com/pipecat-ai/smart-turn) v3.2 | End-of-turn audio model (bundled in Pipecat) | 1.6k / 210 | 2026-01-29 | BSD-2 | BSD-2 | ✅ | Telugu is not in the training data. a2 measured 6/8 on Telugu, see §Tried | ~47 ms on 1 CPU thread; 8.7 MB ONNX | **ADOPT** |
| 3 | [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | VAD (bundled in Pipecat) | 10.4k | 2026-09-29 | MIT | MIT | ✅ | Language-agnostic | <1 ms per 32 ms chunk on CPU | **ADOPT** |
| 4 | [livekit/agents](https://github.com/livekit/agents) | Framework | 14.6k | 2026-10-06 | Apache-2.0 | turn-detector: "livekit-model-license" (LiveKit only) | ✅ code / ❌ turn model off LiveKit | Has Sarvam plugin | Comparable to Pipecat | LEARN (switching gains nothing) |
| 5 | [TEN-framework/ten-framework](https://github.com/TEN-framework/ten-framework) | Framework | 11.2k | 2026-10-04 | Apache-2.0 + extra conditions | — | ❌ (may not compete with Agora) | — | — | AVOID |
| 6 | [TEN-framework/ten-vad](https://github.com/TEN-framework/ten-vad) | VAD | 2.3k | 2026-02-02 | "other" (Apache + Agora conditions) | same | ⚠️ | — | Faster than Silero on paper | AVOID (licence; Silero is enough) |
| 7 | [bolna-ai/bolna](https://github.com/bolna-ai/bolna) | India-built voice agent (Plivo, Exotel, Vobiz) | 0.8k | 2026-10-09 | MIT | n/a | ✅ | Sarvam language detection, Hindi voicemail prompt | — | **LEARN** (copy ideas: language follow, voicemail) |
| 8 | [dograh-hq/dograh](https://github.com/dograh-hq/dograh) | Self-hosted Vapi alternative (Pipecat fork) | 5.8k | 2026-10-08 | BSD-2 | n/a | ✅ | Plivo / Vobiz | — | LEARN |
| 9 | [PatterAI/Patter](https://github.com/PatterAI/Patter) | "Phone number for agents" SDK | 1.1k | 2026-10-03 | MIT | n/a | ✅ | — | — | LEARN (young) |
| 10 | [vocodedev/vocode-core](https://github.com/vocodedev/vocode-core) | Framework | 3.8k | 2024-11-15 | MIT | n/a | ✅ | — | — | AVOID (inactive) |
| 11 | [kyutai-labs/moshi](https://github.com/kyutai-labs/moshi) | Full-duplex speech-to-speech | 11.2k / 260 | 2026-09-09 | Apache-2.0 / MIT | CC-BY-4.0 | ✅ (credit Kyutai) | English only | Needs a GPU (7B) | AVOID for India |
| 12 | [kyutai-labs/unmute](https://github.com/kyutai-labs/unmute) + delayed-streams-modeling | STT/TTS wrapper around any LLM | 1.5k / 3.0k | 2026-09-09 | MIT / Apache | CC-BY-4.0 | ✅ | English and French only | Needs a GPU | LEARN (their semantic VAD idea) |
| 13 | [fixie-ai/ultravox](https://huggingface.co/fixie-ai/ultravox-v0_5-llama-3_1-8b) | Speech-in LLM | (repo moved) / 37 | HF 2026-10-09 | MIT | MIT + **Llama 3.1 licence** | ⚠️ | Tagged Hindi; no Telugu | Needs a GPU (8B) | AVOID for now |
| 14 | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Whisper on CTranslate2 | 25.8k | 2026-10-12 | MIT | MIT (Whisper) | ✅ | Whisper Telugu WER is poor (often over 40% on IndicVoices) | `small` on CPU about 1× real time: too slow for calls | LEARN (offline voice-note fallback only) |
| 15 | [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Whisper in C++ | 54.2k | 2026-10-06 | MIT | MIT | ✅ | Same Whisper Telugu weakness | Fast on CPU, accuracy-bound | LEARN |
| 16 | [ai4bharat/indic-conformer-600m-multilingual](https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual) | ASR, 22 Indian languages | 83 / 224 | 2026-10-08 (HF) | MIT | MIT (gated, auto-approve) | ✅ | **Best open Telugu ASR**: trained on IndicVoices, which includes Telugu | 600M parameters; CPU is too slow for live calls | **LEARN** (self-host fallback if Sarvam STT costs grow) |
| 17 | [ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large](https://huggingface.co/ai4bharat/indicconformer_stt_te_hybrid_ctc_rnnt_large) | Telugu-only ASR | 10 likes | 2024-11-04 | MIT (NeMo) | MIT | ✅ | Telugu-specific | About 120M parameters; CTC on CPU is feasible | LEARN (cheapest self-host Telugu STT) |
| 18 | [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | Offline ASR/TTS/VAD runtime (ONNX) | 15.1k | 2026-10-05 | Apache-2.0 | depends on the model | ✅ runtime | Can run IndicConformer exports | Fast on CPU | LEARN (runtime for self-host) |
| 19 | [k2-fsa/OmniVoice](https://huggingface.co/k2-fsa/OmniVoice) | 600-language zero-shot TTS | 14.4k / 1,518 | 2026-10-06 | Apache-2.0 | **CC-BY-NC** (states "due to Emilia") | ❌ | Telugu tag | RTF 0.025 on a GPU | AVOID (non-commercial) |
| 20 | [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) | TTS, 21 languages, voice described in text | 5.6k (parler) / 410 | HF 2026-10-06 | Apache-2.0 | Apache-2.0 | ✅ | Official Telugu speakers ("Prakash", "Lalitha") | 0.9B parameters; GPU needed for live use | **LEARN** (free offline voice notes on Colab GPU) |
| 21 | [ai4bharat/IndicF5](https://huggingface.co/ai4bharat/IndicF5) | Voice-cloning TTS, 11 languages | 128 / 300 | 2025-09-24 | **no LICENSE file** | MIT | ⚠️ (code unclear; cloning needs consent) | Telugu included | GPU | LEARN |
| 22 | [SPRINGLab/Indic-Mio](https://huggingface.co/SPRINGLab/Indic-Mio) | Indic TTS (IIT-M SPRING Lab) | – / 29 | HF 2026-05-27 | — | Apache-2.0 | ✅ | Telugu tag; not evaluated | Unknown | Watch |
| 23 | [kenpath/svara-tts-v1](https://huggingface.co/kenpath/svara-tts-v1) | Orpheus-style TTS, 19 languages | – / 62 | HF 2025-10-27 | Apache-2.0 | Apache tag, **but built on Llama-3.2-3B** | ⚠️ (Llama terms) | Telugu included | 3B; GPU | LEARN |
| 24 | [bosonai/higgs-tts-3-4b](https://huggingface.co/bosonai/higgs-tts-3-4b) | Expressive TTS, 100+ languages | 8.4k (higgs-audio) / 805 | HF 2026-09-04 | Apache (v2 repo) | **Research and non-commercial** (creator-use grant only) | ❌ for a product | Telugu tag | 4B; GPU | AVOID in the product. Akhil's own videos (7-streams content) are OK with credit |
| 25 | [fishaudio/s2-pro](https://huggingface.co/fishaudio/s2-pro) | TTS, 80+ languages | 33.0k (fish-speech) / 1,417 | 2026-10-12 | "other" | **Fish Audio research licence, non-commercial** | ❌ | Telugu tag | 4.4B; GPU | AVOID |
| 26 | [bharatgenai/sooktam2](https://huggingface.co/bharatgenai/sooktam2) | Indian "sovereign" TTS, 12 languages | – / 38 | HF 2026-03-16 | — | **BharatGen non-commercial** | ❌ | Telugu included | GPU | AVOID (watch for a commercial release) |
| 27 | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | Tiny TTS | 9.2k / 7,228 | 2025-08-06 | Apache-2.0 | Apache-2.0 | ✅ | **No Telugu** (has Hindi) | Faster than real time on CPU | LEARN (Hindi/English-only fallback) |
| 28 | [sesame/csm-1b](https://huggingface.co/sesame/csm-1b) | Conversational TTS | 14.7k / 2,476 | 2025-05-27 | Apache-2.0 | Apache-2.0 (gated) | ✅ | English only | 1B; GPU | AVOID for India |
| 29 | [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) (multilingual) | TTS with cloning | 26.8k / 1,838 | 2026-07-21 | MIT | MIT | ✅ | Hindi yes; **no Telugu** | GPU recommended | LEARN |
| 30 | [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) / [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) / [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice) | Big multilingual TTS | 38.4k / 13.7k / 54.6k | 2026 | Apache / Apache / MIT | Apache / Apache / MIT | ✅ | No Telugu in their language lists | GPU | AVOID for Telugu (watch) |

**Also screened.** Each is listed with its reason.
- **GPL, AGPL or non-commercial: never inside the product.**
  - piper1-gpl (GPL-3)
  - ChatTTS (AGPL-3, Chinese and English only)
  - MMS-TTS / MMS-1B / seamless-m4t-v2 (CC-BY-NC)
  - rumik-oss-1 (CC-BY-NC)
  - coqui-TTS (MPL-2.0 and dead since 2024)
  - bodhan-ai indic-speak / indic-transcribe ("other", gated)
- **Licence or terms risks**
  - SenseVoice: model licence is "other" (FunASR model licence), and it has no Telugu.
  - edge-tts: unofficial Microsoft endpoint, against its terms for a product.
- **Inactive, archived or too large**
  - rhasspy/piper (archived)
  - parler-tts (inactive since 12/2024)
  - pipecat-flows (archived, merged into Pipecat)
  - GPT-SoVITS, CosyVoice and Index-TTS (Chinese-first; Index-TTS has a bilibili licence)
  - huggingface/speech-to-speech (13.4k, Apache, English demo pipeline)
  - RealtimeSTT and RealtimeTTS (MIT, desktop-oriented)
  - FireRedVAD (Apache, 100+ languages; worth watching as a Silero alternative)
  - KittenTTS and Supertonic (English only; Supertonic is OpenRAIL)

## Sarvam is the paid baseline (₹ per call minute)
Sarvam list prices: STT ₹30 per hour (≈ ₹0.50/min) and Bulbul v3 TTS ₹3 per 1,000 characters.
- A 3-minute salon call has about 3 min of caller audio and about 900 characters of bot speech: STT ≈ ₹1.5 + TTS ≈ ₹2.7.
- **About ₹4.2 per call before telephony.** Groq Llama 3.3 70B adds about ₹0.1. Plivo or Exotel adds about ₹0.5–0.8 per minute.
- No open model that we can self-host for free gives *commercially licensed, real-time Telugu TTS on CPU* today. The only commercially clean Telugu TTS weights are Indic Parler-TTS (Apache) and IndicF5 (MIT weights). Both need a GPU to keep up with a live call.

## Recommended stacks

**(a) Best free (₹0 software; for demos and WhatsApp voice notes)**
- Pipecat 1.12 with Silero VAD and smart-turn v3.2 (both bundled, CPU).
- **LLM:** Groq free tier, Llama 3.3 70B.
- **Live-call demos:** Gemini Live (`VOICE_ENGINE=gemini_live`) on the free tier. It is speech-to-speech and speaks Telugu and Hindi. Its free tier trains on our data, so use it for **demos only**, never for client calls.
- **Voice notes:** Indic Parler-TTS (Apache-2.0) run in batches on a free Colab or Kaggle GPU. This is good enough for "async" WhatsApp replies, not for live calls.
- **Self-hosted Telugu STT fallback:** IndicConformer (MIT) through sherpa-onnx or NeMo. It needs a GPU or a slow CPU queue.

**(b) Best quality per ₹ (production; this is BotBhai today, fixed)**
- Pipecat 1.12 with Silero VAD (`stop_secs` 0.2) and smart-turn v3.2 (`stop_secs` 1.2).
- **Sarvam saaras STT** with `codemix` mode, auto language ID and `language=unknown`.
- **Groq Llama 3.3 70B.**
- **Sarvam Bulbul v3 TTS** with the language set per client and *following the caller's detected language*.
- Plivo or Exotel for telephony.
- Total ≈ ₹1.4/min of AI cost plus ₹0.5–0.8/min of telephony.
- Nothing open beats Sarvam on Telugu naturalness per ₹ without a GPU bill. A GPU (for example a T4 at about ₹25–35/hour) only pays off above roughly 8–10 busy call-hours a day.

## Tried it (CPU only, 13 Oct 2026)

Published packages only: `pipecat-ai[sarvam,groq,google,silero,websocket]==1.12.0` in a fresh venv (628 MB). No cloned repo code was executed; no API keys were used.

| What | Result |
|---|---|
| Silero VAD (bundled) | Loads in 0.11 s; `VADParams(stop_secs=0.2)` applied |
| smart-turn v3.2 (`smart-turn-v3.2-cpu.onnx`, bundled) | Loads in 0.08 s; **105 ms per 8-second window** on 1 CPU thread in this sandbox (the model card says ~47 ms on a faster CPU). Fine for a turn decision. |
| Pipecat 1.12 default | Already uses smart-turn v3 as the stop strategy, but with a **3 s** silence fallback; Telugu is not in smart-turn's training data, so a misjudged Telugu turn could wait 3 s |
| Our `agent.py` before A06 | Put the VAD on the transport (a2: this disables barge-in in 1.12) and never set a TTS language, so Telugu/Hindi replies went through the **en-IN** voice path |
| Sarvam settings in 1.12 | `SarvamTTSService.Settings` has a `language` field (default `Language.EN`); `te`, `hi` map to `te-IN`, `hi-IN` |
| Whole agent | `import agent` succeeds in the venv with the pinned FastAPI/uvicorn |

Not tested here (needs a phone line and paid Sarvam minutes): real Telugu calls. That is the CEO-side pilot.

## What was built (A06)

| File | Change |
|---|---|
| `botbhai/voice/turns.py` (new) | `user_params()`: Silero VAD 0.2 s + smart-turn v3.2 with a 1.2 s cap, inside `LLMUserAggregatorParams`; `pipecat_language(cfg)` from the client's `voice_language` (te/hi/en) |
| `botbhai/voice/agent.py` | Transport VAD removed (barge-in back on); aggregator gets `T.user_params()`; Sarvam TTS gets the client's language |
| `botbhai/voice/prompt.py` | `voice_profile()` now returns `language` (te-IN / hi-IN / en-IN) |
| `botbhai/voice/test_turns.py` (new) | Checks the real Pipecat objects carry 0.2 s / 1.2 s / language, that `agent.py` has no transport VAD, and smart-turn latency < 500 ms; added to `tools/test-all.sh` (runs when pipecat is installed) |

Check: `cd botbhai/voice && python test_prompt.py && python test_turns.py` in a venv with pipecat → both pass.
