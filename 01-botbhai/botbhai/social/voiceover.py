"""
A98 Social Team voice-over, free (replaces ElevenLabs).

Script text + language (te, en, hi) -> one WAV that `walkthrough.py --voice` lays under the Reel.
Rendering reuses voice/recorded_tts.py (ai4bharat Indic Parler-TTS, Apache-2.0, CPU, gated on HF:
needs HF_TOKEN). Long scripts are split at sentence ends into chunks of at most MAX_CHARS, each
chunk is rendered, then the chunks are joined with a short pause (stdlib `wave`, no extra library).

Run:  python3 social/voiceover.py --lang te --text "..." --out out/voice-te.wav
      python3 social/voiceover.py --lang en --script script.txt --out out/voice-en.wav --dry-run
Then: python3 social/walkthrough.py ... --voice out/voice-te.wav
Runs in the "Social voice-over" GitHub Action (CPU, free runner); nothing is published.
Only the standard library is imported at the top, so tests never pull torch or the model.
"""
import argparse
import io
import pathlib
import re
import sys
import wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "voice"))
import recorded_tts as rt  # noqa: E402

LANGS = ("te", "en", "hi")
MAX_CHARS = rt.MAX_CHARS
GAP_MS = 250
MAX_SCRIPT = 3000  # about 3 minutes of speech; a Reel needs far less
_END = re.compile(r"(?<=[.!?।])\s+|\n+")


def split_script(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Sentence-sized chunks, each <= max_chars. Over-long sentences are cut at spaces."""
    text = (text or "").strip()
    if not text:
        raise ValueError("script is empty")
    if len(text) > MAX_SCRIPT:
        raise ValueError(f"script is {len(text)} characters; keep it under {MAX_SCRIPT}")
    pieces = []
    for s in (p.strip() for p in _END.split(text)):
        while len(s) > max_chars:
            cut = s.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            pieces.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            pieces.append(s)
    chunks, cur = [], ""
    for p in pieces:
        if cur and len(cur) + 1 + len(p) > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def join_wavs(clips: list[bytes], gap_ms: int = GAP_MS) -> bytes:
    """Concatenate WAV clips (same rate/channels/width) with gap_ms of silence between them."""
    if not clips:
        raise ValueError("no audio to join")
    params, frames = None, []
    for i, c in enumerate(clips):
        with wave.open(io.BytesIO(c)) as w:
            p = (w.getnchannels(), w.getsampwidth(), w.getframerate())
            if params and p != params:
                raise ValueError(f"clip {i + 1} has format {p}, expected {params}")
            params = p
            frames.append(w.readframes(w.getnframes()))
    ch, width, rate = params
    silence = b"\x00" * (int(rate * gap_ms / 1000) * ch * width)
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(silence.join(frames))
    return out.getvalue()


def seconds(wav: bytes) -> float:
    with wave.open(io.BytesIO(wav)) as w:
        return w.getnframes() / w.getframerate()


def pick_speaker(lang: str, speaker: str | None = None, gender: str = "female") -> str:
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}, got '{lang}'")
    if not speaker:
        return rt.speaker_for(lang, gender)
    if speaker not in rt.SPEAKERS[lang]["available"]:
        raise ValueError(f"speaker '{speaker}' is not a {lang} voice; use one of {rt.SPEAKERS[lang]['available']}")
    return speaker


def render(text: str, lang: str, out: pathlib.Path, speaker: str | None = None,
           gender: str = "female", tts=None) -> pathlib.Path:
    """Write one WAV voice-over. `tts(text, speaker) -> WAV bytes`; defaults to Indic Parler-TTS."""
    voice = pick_speaker(lang, speaker, gender)
    chunks = split_script(text)
    tts = tts or rt.parler_wav
    wav = join_wavs([tts(c, voice) for c in chunks])
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(wav)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Script text -> WAV voice-over for walkthrough.py (free, CPU)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="the script itself")
    src.add_argument("--script", type=pathlib.Path, help="a UTF-8 text file with the script")
    ap.add_argument("--lang", required=True, choices=LANGS)
    ap.add_argument("--speaker", help="a voice from voice/recorded_tts.py SPEAKERS (default: recommended)")
    ap.add_argument("--gender", choices=("female", "male"), default="female")
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--dry-run", action="store_true", help="show the chunks and voice, render nothing")
    a = ap.parse_args(argv)
    text = a.text if a.text is not None else a.script.read_text(encoding="utf-8")
    if a.dry_run:
        voice = pick_speaker(a.lang, a.speaker, a.gender)
        for i, c in enumerate(split_script(text), 1):
            print(f"chunk {i} ({len(c)} chars, {voice}): {c[:60]}")
        return None
    path = render(text, a.lang, a.out, a.speaker, a.gender)
    print(f"voice-over {path} {seconds(path.read_bytes()):.1f} s", flush=True)
    return path


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        sys.exit(f"error: {e}")
