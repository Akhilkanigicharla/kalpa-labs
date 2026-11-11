"""
A196 Sound effects for Kalpa reels, free (our own cue planner; idea only from Real SFX, no code copied).

Voice-over WAV -> word timings (captions.timed_words: faster-whisper + VAD, or the script placed on them)
-> cue plan from the words (numbers pop, prices chime, list steps whoosh, warnings thud, "done" clicks)
-> each sound rendered once: our own numpy recipes (synth_render), or earshot when it is installed (MIT,
Leon Lin, github.com/Leonxlnx/earshot @ 4ac3d2a, git only, never the unrelated PyPI "earshot"), or for --real KIND="query" a CC0 recording from Openverse (no key)
-> an SFX stem placed sample-exact (each take's own onset, or a whoosh's peak, lands on its word)
-> ffmpeg mixes stem + voice and makes a 1080x1920 test MP4; credits.txt lists every non-earshot sound.
Checks written to report.json: every cue within 1 frame (30 fps) of its word, measured back from the stem
and from the MP4's own audio, and the voice stays clear (each cue at least 10 dB under the voice around it).

Run:  python3 social/sfx.py --voice out/voice-en.wav --lang en --script s.txt --out out/sfx [--real chime="cash register"]
Runs in the "Social voice-over" GitHub Action; nothing is published.
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

import numpy as np

SR = 48000
FPS = 30
FRAME_S = 1 / FPS
MIN_GAP_S = 0.8      # never two cues closer than this
MAX_CUES = 12
CLEAR_DB = -10.0     # each cue must sit at least this far under the voice around it
EARSHOT = "earshot @ 4ac3d2a (MIT, Leon Lin, github.com/Leonxlnx/earshot)"

# kind, earshot sound id, level vs voice (dB, from K068), sync point, trigger words (EN + TE + HI), first match wins
RULES = [
    ("chime", "mallet/glock", -15, "onset", r"^(₹.*|rs\.?|rupees?|rupay\S*|రూపాయ\S*|रुपय\S*|रुपये|/month|per\s?month)$"),
    ("thud", "knock/wood", -12, "onset", r"^(mistakes?|warning|never|problems?|risk\S*|lose|lost|missed|జాగ్రత్త|సమస్య\S*|गलती|समस्या)$"),
    ("whoosh", "whoosh_fast/crisp", -16, "peak", r"^(first|second|third|step|next|finally|మొదట\S*|తర్వాత|पहला|पहले|अगला)$"),
    ("click", "knock/snap", -16, "onset", r"^(done|ready|booked|confirmed|saved|free|అయిపోయింది|బుక్\S*|बुक|हो)$"),
    ("pop", "ui_pop/soft", -14, "onset", r"(\d|^(two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|lakh|crore|percent|%|"
     r"రెండు|మూడు|నాలుగు|ఐదు|दो|तीन|चार|पांच|पाँच)$)"),
]


def norm(text: str) -> str:
    return re.sub(r"[\s\"'“”‘’!?,.:;()]+$|^[\s\"'“”‘’(]+", "", text.strip().lower())


def plan_cues(words) -> list[dict]:
    """Words (objects with .start/.end/.text) -> cues [{t, kind, word}] in time order, spaced and capped."""
    out = []
    for w in sorted(words, key=lambda w: w.start):
        t = norm(w.text)
        for kind, _sid, _db, _al, pat in RULES:
            if t and re.search(pat, t):
                if not out or w.start - out[-1]["t"] >= MIN_GAP_S:
                    out.append({"t": round(float(w.start), 3), "kind": kind, "word": w.text.strip()})
                break
        if len(out) >= MAX_CUES:
            break
    return out


def rule(kind: str):
    return next(r for r in RULES if r[0] == kind)


# ---------- audio helpers (ffmpeg in, stdlib wave out) ----------
def read_audio(path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def write_wav(path, x: np.ndarray):
    import wave
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1), f.setsampwidth(2), f.setframerate(SR), f.writeframes(pcm.tobytes())


def db(x: float) -> float:
    return 20 * np.log10(max(x, 1e-9))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def active_rms(x: np.ndarray, frame: int = SR // 50) -> float:
    """RMS over the loud 20 ms frames only (speech or the body of a sound, not silence)."""
    n = len(x) // frame
    if n == 0:
        return rms(x)
    fr = np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1))
    keep = fr[fr > fr.max() * 0.1]
    return float(np.sqrt(np.mean(keep ** 2)))


def sync_point(take: np.ndarray, align: str) -> int:
    """Sample index the cue lands on: onset (first sample over 10% of peak) or peak (loudest 5 ms)."""
    a = np.abs(take)
    if align == "peak":
        w = SR // 200
        env = np.convolve(a, np.ones(w) / w, mode="same")
        return int(np.argmax(env))
    return int(np.argmax(a > a.max() * 0.1))


# ---------- sources ----------
OWN = "Kalpa Labs' own synthesised sounds (social/sfx.py synth_render, no third-party audio)"


def synth_render(sound_id: str, out: pathlib.Path) -> pathlib.Path:
    """Our own small recipes per cue kind (used until earshot is installed): numpy only, deterministic."""
    kind = next((r[0] for r in RULES if r[1] == sound_id), sound_id)
    rng = np.random.default_rng(1)

    def t_(d):
        return np.arange(int(d * SR)) / SR

    def band(x, lo, hi):  # FFT band-pass
        f = np.fft.rfftfreq(len(x), 1 / SR)
        return np.fft.irfft(np.fft.rfft(x) * ((f >= lo) & (f <= hi)), len(x))

    if kind == "whoosh":
        t = t_(0.35)
        x = band(rng.standard_normal(len(t)), 600, 5000) * np.sin(np.pi * t / 0.35) ** 2
    elif kind == "chime":
        t = t_(0.5)
        x = (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 2349 * t)) * np.exp(-t * 9)
    elif kind == "thud":
        t = t_(0.25)
        x = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 18)
    elif kind == "click":
        t = t_(0.04)
        x = band(rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 150)
    else:  # pop
        t = t_(0.12)
        x = np.sin(2 * np.pi * (900 - 2500 * t) * t) * np.exp(-t * 35)
    x *= np.minimum(t / 0.002, 1)  # 2 ms attack, no click at the start
    write_wav(out, 0.7 * x / max(np.abs(x).max(), 1e-9))
    return out


def auto_render():
    """earshot when installed (MIT, git commit 4ac3d2a), else our own synth. Returns (render function, credit label)."""
    return (earshot_render, EARSHOT) if shutil.which("earshot") else (synth_render, OWN)


def earshot_render(sound_id: str, out: pathlib.Path) -> pathlib.Path:
    exe = shutil.which("earshot")
    if not exe:
        raise RuntimeError("earshot not installed (uv tool install git+https://github.com/Leonxlnx/earshot@4ac3d2a)")
    subprocess.run([exe, "sfx", "render", sound_id, "-o", str(out), "--seed", "1"], check=True,
                   capture_output=True, timeout=300)
    return out


def openverse_cc0(query: str, out: pathlib.Path, fetch=None) -> dict:
    """First CC0 audio hit on Openverse (no key, 200 requests/day anonymous; checked 2026-11-12) -> file + credit."""
    fetch = fetch or (lambda url: urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "KalpaLabs-sfx/1.0"}), timeout=30).read())
    q = urllib.parse.urlencode({"q": query, "license": "cc0", "page_size": 5})
    data = json.loads(fetch(f"https://api.openverse.org/v1/audio/?{q}"))
    for r in data.get("results", []):
        if (r.get("license") or "").lower() != "cc0" or not r.get("url"):
            continue
        out.write_bytes(fetch(r["url"]))
        return {"file": str(out), "title": r.get("title", ""), "creator": r.get("creator", ""),
                "licence": "CC0 1.0", "source": r.get("foreign_landing_url") or r["url"]}
    raise LookupError(f"no CC0 audio on Openverse for {query!r}")


def load_take(path, max_s: float = 1.2) -> np.ndarray:
    x = read_audio(path)
    start = max(0, int(np.argmax(np.abs(x) > np.abs(x).max() * 0.02)) - SR // 200)  # drop leading silence
    x = x[start: start + int(max_s * SR)]
    fade = min(len(x), SR // 50)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x


def get_takes(kinds, tmp: pathlib.Path, real: dict, render=synth_render, fetch=None):
    """kind -> (take samples, credit or None). --real kinds come from Openverse; earshot is the fallback."""
    takes, notes = {}, []
    for kind in sorted(set(kinds)):
        credit = None
        if kind in real:
            try:
                credit = openverse_cc0(real[kind], tmp / f"{kind}.real", fetch)
                takes[kind] = (load_take(credit["file"]), credit)
                continue
            except Exception as e:  # network or no hit: the cue still gets a sound
                notes.append(f"{kind}: Openverse failed ({type(e).__name__}); used the synthesised sound")
        takes[kind] = (load_take(render(rule(kind)[1], tmp / f"{kind}.wav")), credit)
    return takes, notes


# ---------- place, mix, check ----------
def build_stem(voice: np.ndarray, cues: list[dict], takes: dict):
    """Place each take so its sync point lands on the cue time, at the rule's level under the voice."""
    stem = np.zeros(len(voice) + SR * 2)
    v_level = active_rms(voice)
    placed = []
    for c in cues:
        take, _ = takes[c["kind"]]
        _k, _sid, level_db, align, _p = rule(c["kind"])
        g = local_voice(voice, c["t"], v_level) * 10 ** (level_db / 20) / max(active_rms(take), 1e-9)
        sp = sync_point(take, align)
        start = int(round(c["t"] * SR)) - sp
        lo = max(0, -start)
        seg = take[lo:] * g
        stem[start + lo: start + lo + len(seg)] += seg
        placed.append({**c, "start": (start + lo) / SR, "sync_off": (sp - lo) / SR, "gain_db": round(db(g), 1)})
    return stem[: len(voice)], placed


def measure_sync(stem: np.ndarray, placed: list[dict], takes: dict, search_s: float = 0.1) -> list[float]:
    """Find each take back in the stem by cross-correlation; return |found sync - word time| in seconds."""
    errs = []
    for p in placed:
        take = takes[p["kind"]][0] * 10 ** (p["gain_db"] / 20)
        guess = int(round((p["t"] - p["sync_off"]) * SR))
        lo, hi = max(0, guess - int(search_s * SR)), guess + int(search_s * SR) + len(take)
        win = stem[lo:hi]
        if len(win) < len(take):
            errs.append(float("inf"))
            continue
        corr = np.correlate(win, take, mode="valid")
        found = (lo + int(np.argmax(corr))) / SR
        errs.append(abs(found + p["sync_off"] - p["t"]))
    return errs


def local_voice(voice: np.ndarray, t: float, v_all: float) -> float:
    """Voice level over the 0.5 s from t (never below half its overall level, so a pause doesn't hide a cue)."""
    a, b = int(t * SR), int((t + 0.5) * SR)
    return max(active_rms(voice[a:b]), v_all * 0.5)


def clarity(voice: np.ndarray, stem: np.ndarray, placed: list[dict]) -> list[float]:
    """Per cue: stem level minus voice level (dB) over the 0.5 s from the cue."""
    v_all = active_rms(voice)
    return [round(db(active_rms(stem[int(p["t"] * SR): int((p["t"] + 0.5) * SR)]))
                  - db(local_voice(voice, p["t"], v_all)), 1) for p in placed]


def ffmpeg_mix(voice_wav, stem_wav, mix_wav, mp4):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice_wav), "-i", str(stem_wav), "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]", "-map", "[a]",
                    "-ar", str(SR), str(mix_wav)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0E1A2B:s=1080x1920:r={FPS}",
                    "-i", str(mix_wav), "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(mp4)], check=True)


def av_offset(ref: np.ndarray, got: np.ndarray, max_s: float = 0.25) -> float:
    """Seconds the MP4's audio sits after the reference mix (cross-correlation over the first 5 s)."""
    n, m = min(len(ref), 5 * SR), int(max_s * SR)
    a, b = ref[:n], np.concatenate([np.zeros(m), got[: n + m], np.zeros(m)])
    corr = np.correlate(b, a, mode="valid")
    return (int(np.argmax(corr)) - m) / SR


def credits(takes: dict, notes: list[str], label: str = OWN) -> str:
    extra = ("; its CC0-fitted recipes are credited in github.com/Leonxlnx/earshot/blob/4ac3d2a/docs/CREDITS_FIT.md"
             if label == EARSHOT else "")
    lines = ["Sound effects credits (Kalpa Labs reel)", f"Synthesised sounds: {label}{extra}", ""]
    for kind, (_t, c) in sorted(takes.items()):
        if c:
            lines.append(f"{kind}: \"{c['title']}\" by {c['creator']}, {c['licence']}, {c['source']}")
    return "\n".join(lines + [f"note: {n}" for n in notes]) + "\n"


def run(voice_path, words, out_dir, real=None, render=None, fetch=None, make_mp4=True) -> dict:
    render, label = (render, getattr(render, "label", OWN)) if render else auto_render()
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    voice = read_audio(voice_path)
    cues = plan_cues(words)
    if not cues:
        raise ValueError("no cue words found in the script (numbers, prices, steps, warnings, done)")
    with tempfile.TemporaryDirectory() as tmp:
        takes, notes = get_takes([c["kind"] for c in cues], pathlib.Path(tmp), real or {}, render, fetch)
        stem, placed = build_stem(voice, cues, takes)
    write_wav(out / "voice.wav", voice)
    write_wav(out / "sfx-stem.wav", stem)
    errs = measure_sync(stem, placed, takes)
    clear = clarity(voice, stem, placed)
    rep = {"cues": [{**p, "err_ms": round(e * 1000, 1), "under_voice_db": c} for p, e, c in zip(placed, errs, clear)],
           "max_err_ms": round(max(errs) * 1000, 1), "frame_ms": round(FRAME_S * 1000, 1),
           "max_under_voice_db": max(clear), "notes": notes, "sounds": label}
    ok = rep["max_err_ms"] <= rep["frame_ms"] and rep["max_under_voice_db"] <= CLEAR_DB
    if make_mp4:
        ffmpeg_mix(out / "voice.wav", out / "sfx-stem.wav", out / "mix.wav", out / "reel-sfx.mp4")
        rep["mp4_audio_offset_ms"] = round(av_offset(read_audio(out / "mix.wav"), read_audio(out / "reel-sfx.mp4")) * 1000, 1)
        ok = ok and abs(rep["mp4_audio_offset_ms"]) <= rep["frame_ms"]
    rep["pass"] = bool(ok)
    (out / "credits.txt").write_text(credits(takes, notes, label), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sound effects under a reel voice-over (earshot + Openverse CC0, free)")
    ap.add_argument("--voice", required=True, help="voice-over WAV (voiceover.py)")
    ap.add_argument("--lang", required=True, choices=("te", "en", "hi"))
    ap.add_argument("--script", help="text file with the spoken words (needed for te)")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--real", action="append", default=[], metavar='KIND="query"',
                    help="use a CC0 Openverse recording for this cue kind (chime, thud, whoosh, click, pop)")
    a = ap.parse_args(argv)
    real = dict(r.split("=", 1) for r in a.real)
    if set(real) - {r[0] for r in RULES}:
        ap.error(f"--real kinds must be one of {[r[0] for r in RULES]}")
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from captions import load_audio, timed_words
    words = timed_words(load_audio(a.voice), a.lang,
                        pathlib.Path(a.script).read_text(encoding="utf-8") if a.script else "")
    rep = run(a.voice, words, a.out, real)
    print(json.dumps({k: rep[k] for k in rep if k != "cues"}, ensure_ascii=False), f"cues={len(rep['cues'])}")
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
