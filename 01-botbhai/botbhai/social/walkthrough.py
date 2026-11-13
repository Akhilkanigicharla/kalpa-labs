"""Listing photos -> walkthrough Reel (A96). Free: Pillow + ffmpeg, no AI video service.

Idea from a real-estate "AI social team" reel that used a paid photos-to-video tool. Here each photo gets a
slow camera move (zoom in, zoom out, pan left, pan right, in turn), a short room caption in Kalpa colours,
the business + WhatsApp footer, and an optional voice-over track (any MP3/WAV, e.g. from a free TTS).

    python3 -m social.walkthrough --setup realestate --photos listing/ --rooms "Living room,Kitchen,Master bed" \
        --title "3 BHK, Kondapur" --out out/walk.mp4 [--voice voice.mp3]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageOps

from .design import DEFAULT_FONTS, STORY, _font, _wrap, clean, palette, save_jpeg

MIN_PHOTOS, MAX_PHOTOS = 6, 12
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}
# one move per photo, in turn; zoompan expressions on a 1080x1920 frame (z = zoom, x/y = top-left of the view)
MOVES = {
    "zoom_in": ("min(1+0.0012*on,1.12)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "zoom_out": ("max(1.12-0.0012*on,1)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pan_left": ("1.12", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
    "pan_right": ("1.12", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
}
ORDER = list(MOVES)


def photos_in(folder: pathlib.Path) -> list[pathlib.Path]:
    """Photos in name order (owners number them 01.jpg, 02.jpg ...). Raises if fewer than 6 or more than 12."""
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in PHOTO_EXT)
    if not MIN_PHOTOS <= len(files) <= MAX_PHOTOS:
        raise ValueError(f"need {MIN_PHOTOS}-{MAX_PHOTOS} photos, found {len(files)} in {folder}")
    return files


def layer(caption: str, cfg: dict, index: str = "") -> Image.Image:
    """Transparent 9:16 layer: slim caption band, photo counter and footer. It stays still while the photo moves."""
    W, H = STORY
    bg, accent, deep = palette(cfg)
    F = {**DEFAULT_FONTS, **(cfg.get("fonts") or {})}
    img = Image.new("RGBA", STORY, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    caption = clean(caption)
    if caption:
        f, lines = _wrap(d, caption, F["display"], 78, W - 180, max_lines=2)
        bh = 60 + len(lines) * int(f.size * 1.1)
        top = H - 110 - 70 - bh
        d.rounded_rectangle((50, top, W - 50, top + bh), radius=28, fill=(*deep, 225))
        d.rectangle((50, top + 24, 62, top + bh - 24), fill=(*accent, 255))  # accent bar = world colour
        y = top + 30
        for line in lines:
            d.text((90, y), line, font=f, fill=(255, 255, 255, 255))
            y += int(f.size * 1.1)
    if index:
        d.rounded_rectangle((W - 170, 60, W - 50, 120), radius=30, fill=(*deep, 200))
        d.text((W - 110, 90), index, font=_font(F["bold"], 34), fill=(255, 255, 255, 255), anchor="mm")
    d.rectangle((0, H - 110, W, H), fill=(*deep, 255))
    d.text((70, H - 55), cfg.get("business", "").upper()[:34], font=_font(F["bold"], 40), fill=(255, 255, 255, 255), anchor="lm")
    foot = cfg["cta"]["url"] if cfg.get("cta") else f"WhatsApp {cfg.get('phone', '')}"
    d.text((W - 70, H - 55), foot, font=_font(F["body"], 32), fill=(255, 255, 255, 255), anchor="rm")
    return img


def card(photo: pathlib.Path, caption: str, cfg: dict, index: str = "") -> Image.Image:
    """Still preview of one scene (photo filling 9:16 + the layer), also used as the Reel cover."""
    img = ImageOps.fit(ImageOps.exif_transpose(Image.open(photo)).convert("RGB"), STORY, Image.LANCZOS)
    img.paste(lay := layer(caption, cfg, index), (0, 0), lay)
    return img


def captions_for(n: int, rooms: list[str], title: str = "") -> list[str]:
    """One caption per photo: the title on the first, then the room names in order; blanks if rooms run out."""
    rooms = [clean(r) for r in rooms if r.strip()]
    caps = [rooms[i] if i < len(rooms) else "" for i in range(n)]
    if title:
        caps[0] = f"{clean(title)}" + (f" · {caps[0]}" if caps[0] else "")
    return caps


def filtergraph(count: int, seconds_each: float, fps: int = 30) -> str:
    """Inputs come in pairs: photo 2i, layer PNG 2i+1."""
    n = int(seconds_each * fps)
    parts = []
    for i in range(count):
        z, x, y = (e.replace("{n}", str(n)) for e in MOVES[ORDER[i % len(ORDER)]])
        # upscale first so the zoom does not shimmer; zoompan emits n frames from one still
        parts.append(f"[{2 * i}:v]scale=2160:3840,"
                     f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1080x1920:fps={fps},setsar=1[p{i}]")
        parts.append(f"[p{i}][{2 * i + 1}:v]overlay=0:0:format=auto[v{i}]")  # still layer over the moving photo
    parts.append("".join(f"[v{i}]" for i in range(count)) + f"concat=n={count}:v=1:a=0,format=yuv420p[out]")
    return ";".join(parts)


def build(photos: list[pathlib.Path], captions: list[str], cfg: dict, out: pathlib.Path,
          voice: pathlib.Path | None = None, seconds_each: float = 2.5) -> pathlib.Path | None:
    """Write the walkthrough MP4. Returns None when ffmpeg is missing or fails (frames are still saved)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_suffix("")
    pairs = []
    for i, (p, c) in enumerate(zip(photos, captions)):
        idx = f"{i + 1}/{len(photos)}"
        save_jpeg(card(p, c, cfg, idx), work / f"{i + 1:02d}.jpg")  # covers / preview stills
        lay = work / f"layer-{i + 1:02d}.png"
        layer(c, cfg, idx).save(lay)
        flat = save_jpeg(ImageOps.fit(ImageOps.exif_transpose(Image.open(p)).convert("RGB"), STORY, Image.LANCZOS),
                         work / f"photo-{i + 1:02d}.jpg")  # upright 9:16 (ffmpeg ignores phone EXIF rotation)
        pairs += [flat, lay]
    ff = shutil.which("ffmpeg")
    if not ff:
        return None
    cmd = [ff, "-y", "-loglevel", "error"]
    for f in pairs:
        cmd += ["-i", str(f)]
    if voice:
        cmd += ["-i", str(voice)]
    cmd += ["-filter_complex", filtergraph(len(photos), seconds_each), "-map", "[out]"]
    if voice:
        cmd += ["-map", f"{len(pairs)}:a", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-movflags", "+faststart", "-r", "30", str(out)]
    try:
        subprocess.run(cmd, check=True, timeout=600)
    except (subprocess.SubprocessError, OSError):
        return None
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Listing photos -> 9:16 walkthrough Reel (free, ffmpeg)")
    ap.add_argument("--setup", required=True, help="setups/<name>/bot.config.json for colours, business, WhatsApp")
    ap.add_argument("--photos", required=True, type=pathlib.Path, help="folder with 6-12 photos, in name order")
    ap.add_argument("--rooms", default="", help="comma-separated captions, one per photo")
    ap.add_argument("--title", default="", help="first caption, e.g. '3 BHK, Kondapur'")
    ap.add_argument("--voice", type=pathlib.Path, help="optional voice-over MP3/WAV")
    ap.add_argument("--out", required=True, type=pathlib.Path)
    a = ap.parse_args(argv)
    cfg = json.loads((pathlib.Path(__file__).resolve().parents[1] / "setups" / a.setup / "bot.config.json").read_text())
    photos = photos_in(a.photos)
    mp4 = build(photos, captions_for(len(photos), a.rooms.split(","), a.title), cfg, a.out, a.voice)
    print(mp4 or "ffmpeg missing or failed; frames saved next to --out")


if __name__ == "__main__":
    main()
