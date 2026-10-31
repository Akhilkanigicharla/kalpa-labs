"""
A99 Auto captions on Reels, free (replaces CapCut).

Voice-over (or the Reel's own audio) -> faster-whisper (MIT, CPU) word timings -> 2-line cues
-> an ASS subtitle file in the Kalpa look -> ffmpeg burns it into the MP4 (libass).
Telugu, Hindi and English. Every timing is snapped to where speech really is (Silero VAD, bundled in
faster-whisper), because Whisper's word ends drift into pauses. When the script is known (`--script`,
the same text voiceover.py spoke) the script's words are shown and placed by character position on a
character -> time curve: Whisper's words for English and Hindi, the speech segments themselves for Telugu
(Whisper's Telugu spelling and word times were unusable in tests on 2026-10-31, so Telugu needs --script).

Run:  python3 social/captions.py --video out/reel.mp4 --lang te --script script.txt --out out/reel-cc.mp4
      python3 social/captions.py --audio out/voice-en.wav --lang en --srt out/voice-en.srt   # captions only
Runs in the "Social captions" GitHub Action (CPU, free runner); nothing is published.
Only the standard library is imported at the top; faster-whisper and numpy load on first use.
"""
import argparse
import bisect
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

LANGS = ("te", "en", "hi")
MODELS = {"te": "large-v3-turbo", "en": "small", "hi": "small"}  # te: only if transcribe() is called directly
MAX_LINE = {"te": 32, "hi": 34, "en": 28}  # code points per line at 72 px (Indic marks take no width); all fit 1080 px, tested
MAX_LINES = 2
MAX_CUE_S = 4.0     # a cue is cut after this long, so the eye can keep up
GAP_S = 0.6         # a pause this long always starts a new cue
HOLD_S = 0.1        # a cue stays this long after its last word (never into the next cue)
FONTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "00-hq" / "design" / "fonts"
FONT = {"te": "Anek Telugu", "hi": "Anek Devanagari", "en": "Anek Latin"}
# Kalpa tokens (00-hq/design/tokens.css): dark-theme --bg (box) and --fg (text)
INK, TEXT = "#0F1912", "#ECE7D8"
_SENT_END = re.compile(r"[.!?।]$")


class Word:
    __slots__ = ("start", "end", "text")

    def __init__(self, start, end, text):
        self.start, self.end, self.text = float(start), float(end), text.strip()

    def __repr__(self):
        return f"Word({self.start:.2f},{self.end:.2f},{self.text!r})"


# ---------- audio + transcription (heavy imports live here) ----------

def load_audio(path):
    """Any audio/video file -> 16 kHz mono float32 via ffmpeg (no PyAV)."""
    import numpy as np
    ff = shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg is needed")
    raw = subprocess.run([ff, "-nostdin", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def transcribe(audio, lang: str, model: str = "") -> list[Word]:
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    from faster_whisper import WhisperModel
    m = WhisperModel(model or MODELS[lang], device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio if not isinstance(audio, (str, pathlib.Path)) else load_audio(audio),
                           language=lang, word_timestamps=True, vad_filter=True)
    return [Word(w.start, w.end, w.word) for s in segs for w in (s.words or []) if w.word.strip()]


def speech(audio, rate: int = 16000) -> list[tuple[float, float]]:
    """Speech segments in seconds (Silero VAD from faster-whisper, tight padding)."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    return [(t["start"] / rate, t["end"] / rate)
            for t in get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=300, speech_pad_ms=60))]


# ---------- pure parts (unit-tested without the model) ----------

def snap(words: list[Word], segs: list[tuple[float, float]]) -> list[Word]:
    """Clamp each word into the speech segments it touches (or the nearest one), so no word sits in silence."""
    if not segs:
        return words
    out = []
    for w in words:
        touch = [g for g in segs if g[0] < w.end and g[1] > w.start]
        if not touch:
            touch = [min(segs, key=lambda g: min(abs(g[0] - w.end), abs(g[1] - w.start)))]
        s, e = max(w.start, touch[0][0]), min(w.end, touch[-1][1])
        if e <= s:  # word lay wholly in silence: put it at the near edge of the nearest segment
            g = touch[0]
            s, e = (g[0], min(g[0] + 0.2, g[1])) if w.end <= g[0] else (max(g[1] - 0.2, g[0]), g[1])
        out.append(Word(s, e, w.text))
    # Whisper often ends the last word of a phrase early: stretch it to the end of its speech segment
    for i, w in enumerate(out):
        g = next((g for g in segs if g[0] <= w.end <= g[1]), None)
        nxt = out[i + 1].start if i + 1 < len(out) else float("inf")
        if g and nxt >= g[1] and g[1] - w.end <= 0.8:
            w.end = g[1]
    return out


def segment_anchors(segs: list[tuple[float, float]], chars_per_s: float = 15.0) -> list[Word]:
    """Speech segments as stand-in words whose length grows with duration (timing source when Whisper can't be trusted)."""
    return [Word(a, b, "x" * max(1, round((b - a) * chars_per_s))) for a, b in segs if b > a]


def align_script(script: str, heard: list[Word]) -> list[Word]:
    """Put the script's words on the heard timeline. Sentence breaks in the script are first matched to
    pauses in the audio (nearest by character position), then each part is placed by character position."""
    words = script.split()
    if not words:
        raise ValueError("script is empty")
    if not heard:
        raise ValueError("no speech found in the audio")
    # script parts: a new part after a line break or a sentence end
    parts, cur = [], []
    for line in script.strip().splitlines():
        for w in line.split():
            cur.append(w)
            if _SENT_END.search(w):
                parts.append(cur); cur = []
        if cur:
            parts.append(cur); cur = []
    frac = lambda items, n: sum(len(x) for x in items[:n]) / max(1, sum(len(x) for x in items))  # noqa: E731
    texts = [w.text for w in heard]
    pauses = [i for i in range(1, len(heard)) if heard[i].start - heard[i - 1].end >= GAP_S]
    breaks = [sum(len(p) for p in parts[:j]) for j in range(1, len(parts))]  # word index where a part starts
    cuts, last = [], 0
    if len(pauses) == len(breaks):  # one pause per sentence break: pair them in order
        pauses, cuts = [], list(zip(pauses, breaks))
    for i in pauses:  # otherwise pair each pause with the nearest unused script break after the previous cut
        fp = frac(texts, i)
        cand = [b for b in breaks if b > last]
        if not cand:
            break
        b = min(cand, key=lambda b: abs(frac(words, b) - fp))
        if abs(frac(words, b) - fp) < 0.25:
            cuts.append((i, b)); last = b
    out, hi, wi = [], 0, 0
    for i, b in cuts + [(len(heard), len(words))]:
        out += _place(words[wi:b], heard[hi:i])
        hi, wi = i, b
    return out


def _place(words: list[str], heard: list[Word]) -> list[Word]:
    """Each word at its character position on the heard character -> time curve."""
    total = sum(len(w.text) for w in heard)
    xs, ts, c = [], [], 0
    for w in heard:
        xs.append(c / total); ts.append(w.start)
        c += len(w.text)
        xs.append(c / total); ts.append(w.end)

    def at(f, start):
        # at a pause both times share one position: a word start takes the later one, a word end the earlier
        i = (bisect.bisect_right if start else bisect.bisect_left)(xs, f)
        if start and i > 0 and xs[i - 1] == f:
            return ts[i - 1]
        if not start and i < len(xs) and xs[i] == f:
            return ts[i]
        if i <= 0:
            return ts[0]
        if i >= len(xs):
            return ts[-1]
        x0, x1, t0, t1 = xs[i - 1], xs[i], ts[i - 1], ts[i]
        return t0 if x1 == x0 else t0 + (t1 - t0) * (f - x0) / (x1 - x0)

    stotal = sum(len(w) for w in words)
    out, c = [], 0
    for w in words:
        s = at(c / stotal, True)
        c += len(w)
        out.append(Word(s, max(at(c / stotal, False), s + 0.05), w))
    return out


def wrap(words: list[str], max_line: int) -> list[str]:
    """Words -> at most 2 lines, balanced, each <= max_line where possible."""
    text = " ".join(words)
    if len(text) <= max_line or len(words) == 1:
        return [text]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = (max(len(a), len(b)) > max_line, abs(len(a) - len(b)))
        if best is None or score < best[0]:
            best = (score, [a, b])
    return best[1]


def fits(words: list[str], max_line: int) -> bool:
    lines = wrap(words, max_line)
    return len(lines) <= MAX_LINES and all(len(x) <= max_line for x in lines)


def cues(words: list[Word], lang: str = "en") -> list[dict]:
    """Group timed words into cues of <= 2 lines; new cue on a long pause, a sentence end or 4 s."""
    max_line = MAX_LINE.get(lang, 26)
    out, cur = [], []
    for w in words:
        if cur and (w.start - cur[-1].end >= GAP_S or _SENT_END.search(cur[-1].text)
                    or w.end - cur[0].start > MAX_CUE_S or not fits([x.text for x in cur + [w]], max_line)):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    res = []
    for i, ws in enumerate(out):
        end = ws[-1].end + HOLD_S
        if i + 1 < len(out):
            end = min(end, out[i + 1][0].start)
        res.append({"start": ws[0].start, "end": max(end, ws[-1].end), "lines": wrap([x.text for x in ws], max_line)})
    return res


def _ts(t: float, sep: str, cs: bool) -> str:
    t = max(t, 0.0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    if cs:  # ASS: h:mm:ss.cc
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"


def srt(cs: list[dict]) -> str:
    return "".join(f"{i}\n{_ts(c['start'], ',', False)} --> {_ts(c['end'], ',', False)}\n" + "\n".join(c["lines"]) + "\n\n"
                   for i, c in enumerate(cs, 1))


def _ass_colour(hexc: str, alpha: int = 0) -> str:
    r, g, b = (int(hexc.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def ass(cs: list[dict], lang: str = "en", w: int = 1080, h: int = 1920) -> str:
    """Kalpa look: Anek bold, light text on a dark box (BorderStyle 3), centred in the lower third above the footer bar."""
    style = (f"Style: Kalpa,{FONT[lang]},72,{_ass_colour(TEXT)},{_ass_colour(TEXT)},{_ass_colour(INK, 0x30)},"
             f"{_ass_colour(INK, 0x30)},-1,0,0,0,100,100,0,0,3,18,0,2,80,80,300,1")
    head = ("[Script Info]\nScriptType: v4.00+\nWrapStyle: 2\nScaledBorderAndShadow: yes\n"
            f"PlayResX: {w}\nPlayResY: {h}\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            f"MarginL, MarginR, MarginV, Encoding\n{style}\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    esc = lambda s: s.replace("\\", "").replace("{", "(").replace("}", ")")  # noqa: E731 (no override tags from text)
    return head + "".join(f"Dialogue: 0,{_ts(c['start'], '.', True)},{_ts(c['end'], '.', True)},Kalpa,,0,0,0,,"
                          + r"\N".join(esc(x) for x in c["lines"]) + "\n" for c in cs)


def burn(video, ass_text: str, out) -> pathlib.Path | None:
    """Burn the captions into the MP4 (audio copied). Returns None if ffmpeg is missing or fails."""
    ff = shutil.which("ffmpeg")
    if not ff:
        return None
    out = pathlib.Path(out)
    with tempfile.TemporaryDirectory() as d:
        sub = pathlib.Path(d) / "cc.ass"
        sub.write_text(ass_text, encoding="utf-8")
        vf = f"ass={sub}:fontsdir={FONTS_DIR}"
        r = subprocess.run([ff, "-nostdin", "-v", "error", "-y", "-i", str(video), "-vf", vf, "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20", "-c:a", "copy", str(out)],
                           capture_output=True, text=True)
    return out if r.returncode == 0 and out.exists() else None


def timed_words(audio, lang: str, script: str = "", model: str = "") -> list[Word]:
    """The words to show, with times snapped to real speech."""
    segs = speech(audio)
    if lang == "te":
        if not script.strip():
            raise ValueError("Telugu captions need --script (Whisper's Telugu spelling is not good enough to show)")
        return align_script(script, segment_anchors(segs))
    heard = snap(transcribe(audio, lang, model), segs)
    return align_script(script, heard) if script.strip() else heard


def main(argv=None):
    ap = argparse.ArgumentParser(description="Auto captions for a Reel (faster-whisper + ffmpeg, free)")
    ap.add_argument("--lang", required=True, choices=LANGS)
    ap.add_argument("--video", help="Reel MP4 to caption (its audio is used unless --audio is given)")
    ap.add_argument("--audio", help="voice-over WAV (from voiceover.py)")
    ap.add_argument("--script", help="text file with the words that were spoken (shown instead of Whisper's spelling)")
    ap.add_argument("--model", default="", help="faster-whisper model (default per language)")
    ap.add_argument("--out", help="captioned MP4")
    ap.add_argument("--srt", help="also write captions as SRT")
    a = ap.parse_args(argv)
    src = a.audio or a.video
    if not src:
        ap.error("give --video or --audio")
    words = timed_words(load_audio(src), a.lang, pathlib.Path(a.script).read_text(encoding="utf-8") if a.script else "",
                        a.model)
    cs = cues(words, a.lang)
    if a.srt:
        pathlib.Path(a.srt).write_text(srt(cs), encoding="utf-8")
    if a.video and a.out:
        res = burn(a.video, ass(cs, a.lang), a.out)
        print(res or "ffmpeg failed; captions not burned")
        return 0 if res else 1
    print(srt(cs), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
