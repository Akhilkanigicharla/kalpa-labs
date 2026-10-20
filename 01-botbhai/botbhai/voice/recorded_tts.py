"""
Recorded (not live) voice for Kalpa: reel voice-overs, course narration, BotBhai WhatsApp voice notes.

Free provider (default): ai4bharat Indic Parler-TTS, Apache-2.0, gated on Hugging Face (accept terms + HF_TOKEN).
  Model card checked 2026-10-20: https://huggingface.co/ai4bharat/indic-parler-tts
Optional paid provider: Sarvam bulbul:v3 (set RECORDED_TTS=sarvam and SARVAM_API_KEY).
Live phone calls do NOT use this file (agent.py keeps Sarvam streaming TTS).

Text file format, one line per clip ("#" lines are comments):
    <id> | <lang te|en|hi> | <speaker> | <text>

Run:  python recorded_tts.py --text samples.txt --out out            (needs requirements-parler.txt + HF_TOKEN)
      python recorded_tts.py --text samples.txt --out out --dry-run  (stdlib only, lists the files it would make)
Only the standard library is imported at the top, so tests never pull torch or download the model.
"""
import argparse
import io
import os
import re
import sys

MODEL_ID = "ai4bharat/indic-parler-tts"
MAX_CHARS = 480  # same cap as BotBhai voice notes; long text should be split into several lines
# From the model card speaker table (2026-10-20). "recommended" first: female, then male.
SPEAKERS = {
    "te": {"recommended": ["Lalitha", "Prakash"], "available": ["Prakash", "Lalitha", "Kiran"]},
    "en": {"recommended": ["Mary", "Thoma"], "available": ["Thoma", "Mary", "Swapna", "Dinesh", "Meera", "Jatin", "Aakash", "Sneha", "Kabir", "Tisha",
                                                            "Chingkhei", "Thoiba", "Priya", "Tarun", "Gauri", "Nisha", "Raghav", "Kavya", "Ravi", "Vikas", "Riya"]},
    "hi": {"recommended": ["Divya", "Rohit"], "available": ["Rohit", "Divya", "Aman", "Rani"]},
}
ALL_SPEAKERS = {s for v in SPEAKERS.values() for s in v["available"]}
PROVIDERS = ("parler", "sarvam")
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")


def parse_line(line: str, n: int) -> dict:
    parts = [p.strip() for p in line.split("|", 3)]
    if len(parts) != 4:
        raise ValueError(f"line {n}: need 'id | lang | speaker | text'")
    cid, lang, speaker, text = parts
    if not _ID.match(cid):
        raise ValueError(f"line {n}: id '{cid}' must be lowercase letters, digits or '-'")
    if lang not in SPEAKERS:
        raise ValueError(f"line {n}: language '{lang}' not in {sorted(SPEAKERS)}")
    if speaker not in SPEAKERS[lang]["available"]:
        raise ValueError(f"line {n}: speaker '{speaker}' is not a {lang} voice {SPEAKERS[lang]['available']}")
    if not text or len(text) > MAX_CHARS:
        raise ValueError(f"line {n}: text must be 1-{MAX_CHARS} characters")
    return {"id": cid, "lang": lang, "speaker": speaker, "text": text}


def load_lines(path: str) -> list:
    items = []
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            if raw.strip() and not raw.lstrip().startswith("#"):
                items.append(parse_line(raw, n))
    if not items:
        raise ValueError(f"{path}: no lines to render")
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate ids")
    return items


def describe(speaker: str, pace: str = "moderate") -> str:
    """Parler voice prompt. The card says: name the speaker and say 'very clear audio' for the best quality."""
    if speaker not in ALL_SPEAKERS:
        raise ValueError(f"unknown Parler speaker '{speaker}'")
    return (f"{speaker}'s voice is warm and friendly, delivered at a {pace} pace with a natural pitch. "
            "The recording is very clear audio, with the speaker's voice sounding close up and no background noise.")


def out_name(item: dict) -> str:
    return f"{item['id']}-{item['lang']}-{item['speaker'].lower()}.wav"


def provider(env=os.environ) -> str:
    p = (env.get("RECORDED_TTS") or "parler").strip().lower()
    if p not in PROVIDERS:
        raise ValueError(f"RECORDED_TTS must be one of {PROVIDERS}, got '{p}'")
    return p


def speaker_for(lang: str, gender: str = "female") -> str:
    rec = SPEAKERS.get(str(lang).lower()[:2], SPEAKERS["en"])["recommended"]
    return rec[1] if gender == "male" else rec[0]


_model = None


def _load():
    """Load model + tokenizers once (about 3.8 GB download on first use, then cached)."""
    global _model
    if _model is None:
        import torch  # noqa: F401  (heavy imports only when really rendering)
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
        model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL_ID).to("cpu")
        _model = (model, AutoTokenizer.from_pretrained(MODEL_ID), AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path))
    return _model


def parler_wav(text: str, speaker: str, seed: int = 7) -> bytes:
    """Render one clip on CPU and return WAV bytes."""
    import soundfile as sf
    import torch
    model, tok, desc_tok = _load()
    torch.manual_seed(seed)
    d = desc_tok(describe(speaker), return_tensors="pt")
    p = tok(text, return_tensors="pt")
    with torch.inference_mode():
        audio = model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask,
                               prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
    buf = io.BytesIO()
    sf.write(buf, audio.cpu().numpy().squeeze(), model.config.sampling_rate, format="WAV")
    return buf.getvalue()


def main(argv=None) -> list:
    ap = argparse.ArgumentParser(description="Render recorded voice clips with Indic Parler-TTS (free, CPU).")
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    items = load_lines(a.text)
    paths = [os.path.join(a.out, out_name(i)) for i in items]
    if a.dry_run:
        for p in paths:
            print("would render", p)
        return paths
    os.makedirs(a.out, exist_ok=True)
    for item, path in zip(items, paths):
        with open(path, "wb") as f:
            f.write(parler_wav(item["text"], item["speaker"]))
        print("rendered", path, os.path.getsize(path), "bytes", flush=True)
    return paths


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        sys.exit(f"error: {e}")
