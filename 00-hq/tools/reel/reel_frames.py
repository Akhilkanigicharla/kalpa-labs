#!/usr/bin/env python3
"""Read a Facebook/Instagram video frame by frame, from a file Akhil gives us (never a URL: CLAUDE.md rule 4).

Makes, in OUT/:
  frames/f_0012.4s.jpg   one frame per scene change + one every --every seconds (deduped, max --max)
  sheet_01.jpg ...       contact sheets, 3x4 frames with timestamps, so Claude reads 12 frames per image
  report.md              timeline: speech (Whisper, te/hi/en) + on-screen text (Tesseract eng+tel+hin) per frame
  report.json            the same, for code

Free and offline after setup: ffmpeg, Tesseract (Apache-2.0), faster-whisper (MIT) + Whisper "small" (MIT).
Run: /home/claude/venv-reel/bin/python 00-hq/tools/reel/reel_frames.py VIDEO --out DIR
"""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".3gp"}
TESSDATA = os.environ.get("TESSDATA_PREFIX", "/home/claude/tessdata")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def check_input(path):
    s = str(path)
    if re.match(r"^[a-z]+://", s, re.I):
        raise SystemExit("Give a video FILE, not a link. We never download from Instagram/Facebook (CLAUDE.md rule 4). "
                         "Save or screen-record the video on the phone and attach it.")
    p = Path(s)
    if not p.is_file():
        raise SystemExit(f"No such file: {s}")
    if p.suffix.lower() not in VIDEO_EXT:
        raise SystemExit(f"Not a video file ({p.suffix}). Use one of: {', '.join(sorted(VIDEO_EXT))}")
    return p


def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                          "-of", "json", str(p)], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), None)
    if not v:
        raise SystemExit("This file has no video track.")
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    return {"duration": float(j["format"].get("duration", 0)), "width": v.get("width"), "height": v.get("height"),
            "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else 0,
            "audio": any(s.get("codec_type") == "audio" for s in j.get("streams", []))}


def pick_times(p, duration, every, scene, max_frames):
    """Scene-change times from ffmpeg + a steady tick every `every` s; merged, deduped (<0.4 s apart), capped evenly."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-vf", f"select='gt(scene,{scene})',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    scenes = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    ticks = [round(i * every, 2) for i in range(int(duration // every) + 1)] if every > 0 else []
    times = []
    for t in sorted(set([0.0] + scenes + ticks)):
        if t <= max(duration - 0.05, 0) and (not times or t - times[-1] >= 0.4):
            times.append(round(t, 2))
    if len(times) > max_frames:
        step = len(times) / max_frames
        times = [times[int(i * step)] for i in range(max_frames)]
    return times, len(scenes)


def grab(p, t, dest):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", str(p), "-frames:v", "1",
                    "-vf", "scale='min(720,iw)':-2", "-q:v", "3", str(dest)], check=True)


def ocr(img):
    if not shutil.which("tesseract"):
        return ""
    langs = "+".join(l for l in ("eng", "tel", "hin") if Path(TESSDATA, f"{l}.traineddata").exists()) or "eng"
    r = subprocess.run(["tesseract", str(img), "-", "-l", langs, "--psm", "11"], capture_output=True, text=True,
                       env={**os.environ, "TESSDATA_PREFIX": TESSDATA})
    words = [w for w in re.split(r"\s+", r.stdout) if len(re.sub(r"\W", "", w)) >= 2]
    return " ".join(words)[:400]


def sheets(frames, out, cols=3, rows=4, w=300):
    font = ImageFont.truetype(FONT, 22) if Path(FONT).exists() else ImageFont.load_default()
    made, per = [], cols * rows
    for k in range(0, len(frames), per):
        chunk = frames[k:k + per]
        thumbs = []
        for f in chunk:
            im = Image.open(f["file"]).convert("RGB")
            im = im.resize((w, int(im.height * w / im.width)))
            ImageDraw.Draw(im).rectangle((0, 0, 92, 30), fill=(30, 42, 31))
            ImageDraw.Draw(im).text((6, 3), f"{f['t']:.1f}s", fill=(232, 182, 74), font=font)
            thumbs.append(im)
        h = max(t.height for t in thumbs)
        sheet = Image.new("RGB", (cols * w + (cols + 1) * 6, rows * h + (rows + 1) * 6), (242, 238, 227))
        for i, t in enumerate(thumbs):
            sheet.paste(t, (6 + (i % cols) * (w + 6), 6 + (i // cols) * (h + 6)))
        name = out / f"sheet_{k // per + 1:02d}.jpg"
        sheet.save(name, quality=82)
        made.append(name.name)
    return made


def transcribe(p, model_name, model_dir):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None, "faster-whisper not installed"
    import numpy as np
    # decode with ffmpeg ourselves (16 kHz mono float), so we do not depend on PyAV's version
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    m = WhisperModel(model_name, device="cpu", compute_type="int8", download_root=model_dir)
    segs, info = m.transcribe(np.frombuffer(raw, dtype=np.float32), vad_filter=True, beam_size=5)
    return [{"start": round(s.start, 1), "end": round(s.end, 1), "text": s.text.strip()} for s in segs], \
        f"{info.language} ({info.language_probability:.0%})"


def build(video, out, every=1.0, scene=0.25, max_frames=60, audio=True, model="small", model_dir="/home/claude/whisper"):
    p = check_input(video)
    out = Path(out); (out / "frames").mkdir(parents=True, exist_ok=True)
    meta = probe(p)
    times, n_scenes = pick_times(p, meta["duration"], every, scene, max_frames)
    frames, last = [], None
    for t in times:
        f = out / "frames" / f"f_{t:07.1f}s.jpg"
        grab(p, t, f)
        if not f.exists():
            continue
        text = ocr(f)
        frames.append({"t": t, "file": str(f), "text": text if text != last else ""})
        last = text or last
    speech, lang = (transcribe(p, model, model_dir) if audio and meta["audio"] else (None, "no audio track" if audio else "skipped"))
    rep = {"video": p.name, **meta, "scene_changes": n_scenes, "frames": len(frames), "sheets": sheets(frames, out),
           "speech_language": lang, "speech": speech or [], "timeline": frames}
    (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    lines = [f"# {p.name}", "",
             f"{meta['duration']:.1f} s · {meta['width']}x{meta['height']} · {meta['fps']} fps · {n_scenes} scene changes · "
             f"{len(frames)} frames · speech: {lang}", "", "Contact sheets: " + ", ".join(rep["sheets"]), "", "## Timeline"]
    for f in frames:
        said = " ".join(s["text"] for s in rep["speech"] if f["t"] <= s["start"] < f["t"] + max(every, 0.5))
        bits = [b for b in (f"on screen: {f['text']}" if f["text"] else "", f"said: {said}" if said else "") if b]
        lines.append(f"- **{f['t']:.1f}s** `{Path(f['file']).name}`" + (" · " + " · ".join(bits) if bits else ""))
    if rep["speech"]:
        lines += ["", "## Full speech"] + [f"- {s['start']}–{s['end']}s: {s['text']}" for s in rep["speech"]]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    return rep


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("video"); a.add_argument("--out", required=True)
    a.add_argument("--every", type=float, default=1.0, help="seconds between steady frames (0 = scene changes only)")
    a.add_argument("--scene", type=float, default=0.25, help="scene-change threshold 0-1")
    a.add_argument("--max", type=int, default=60, help="max frames")
    a.add_argument("--no-audio", action="store_true"); a.add_argument("--model", default="small")
    x = a.parse_args()
    r = build(x.video, x.out, x.every, x.scene, x.max, not x.no_audio, x.model)
    print(f"{r['frames']} frames, {len(r['sheets'])} sheets, speech: {r['speech_language']} → {x.out}/report.md")
