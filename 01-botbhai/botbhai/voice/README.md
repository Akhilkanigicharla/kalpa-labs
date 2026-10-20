# BotBhai voice

Two kinds of voice live here.

| Kind | Used for | Engine | Cost |
|---|---|---|---|
| Live calls | Phone receptionist (`agent.py`, Pipecat) | Sarvam STT + streaming TTS | Paid per minute, Pro plan only |
| Recorded voice | Reel voice-overs, course narration, WhatsApp voice notes | `recorded_tts.py`: ai4bharat Indic Parler-TTS (default) or Sarvam (optional) | ₹0 on a CPU (GitHub Actions) |

## Recorded voice (A56)

- Model: [`ai4bharat/indic-parler-tts`](https://huggingface.co/ai4bharat/indic-parler-tts), Apache-2.0, 0.9B parameters. The download is gated: accept the terms on Hugging Face and use a READ token (`HF_TOKEN`). Library: [`huggingface/parler-tts`](https://github.com/huggingface/parler-tts), Apache-2.0, pinned to a commit in `requirements-parler.txt`. Both checked 2026-10-20.
- Voices (from the model card speaker table): Telugu Lalitha (female) and Prakash (male), with Kiran also available; English Mary and Thoma; Hindi Divya and Rohit.
- Switch: `RECORDED_TTS=parler` (default) or `RECORDED_TTS=sarvam` (paid, needs `SARVAM_API_KEY`). The voice server Docker image sets `sarvam` because it has no torch. Free voice notes there need `requirements-parler.txt` installed and a test.
- Text file: one clip per line, `id | lang | speaker | text`, with at most 480 characters. See `samples.txt`.
- Samples: run the manual workflow **Telugu voice samples** (`.github/workflows/telugu-voice.yml`). It renders the 4 lines in `samples.txt` on a CPU and uploads `telugu-voice-samples` (WAV files, kept 14 days). Rendering on a CPU is slow (minutes per clip). That is fine for batch jobs but not for live calls.
- Tests (stdlib only, no download): `python3 voice/test_recorded_tts.py`. They are part of `tools/test-all.sh`.
- AI voice disclosure: label reels and voice notes as AI-generated where the platform asks (YouTube or Instagram "synthetic content").
