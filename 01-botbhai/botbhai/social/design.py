"""Designer: branded images and short Reels for each slot (Pillow + ffmpeg, both free).

Formats follow Instagram's publishing rules: JPEG only (Content Publishing API), 4:5 portrait feed images
(1080x1350), 9:16 stories and Reels (1080x1920), carousels up to 10 slides. When the owner sends a real photo
(recommended: real work beats graphics), it becomes the background and the text sits on a dark band.
Telugu is drawn with Noto Sans Telugu; Pillow needs libraqm for correct Telugu shaping (Pillow wheels ship it).
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = pathlib.Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
FEED, STORY = (1080, 1350), (1080, 1920)
THEMES = {  # same palettes as tools/cards.py (bg, accent, deep)
    "salon": ((255, 228, 236), (236, 72, 153), (88, 28, 63)),
    "gym": ((222, 247, 236), (16, 185, 129), (6, 60, 45)),
    "realestate": ((225, 236, 252), (37, 99, 235), (23, 37, 84)),
    "examkits": ((255, 243, 214), (234, 147, 8), (84, 52, 6)),
}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def _fit(draw, text, fname, size, max_w, min_size=36):
    f = _font(fname, size)
    while draw.textlength(text, font=f) > max_w and size > min_size:
        size -= 4
        f = _font(fname, size)
    return f, size


def _wrap(draw, text, fname, size, max_w, max_lines=4):
    f = _font(fname, size)
    for width in range(28, 8, -2):
        lines = textwrap.wrap(text, width) or [""]
        if all(draw.textlength(l, font=f) <= max_w for l in lines) and len(lines) <= max_lines:
            return f, lines
    return f, textwrap.wrap(text, 12)[:max_lines]


def clean(text: str) -> str:
    """Image-safe text: our fonts carry no emoji and Anton/Baloo have no ₹ glyph, so draw 'Rs' instead of tofu boxes."""
    t = (text or "").replace("₹", "Rs ").replace("Rs  ", "Rs ")
    t = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]", "", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def frame(text: str, sub: str, cfg: dict, size=FEED, telugu: str = "", photo: str | None = None, index: str = "") -> Image.Image:
    """One branded frame. `index` like '2/4' marks carousel slides."""
    text, sub = clean(text), clean(sub)
    telugu = re.sub(r"[!?.]", "", clean(telugu)).strip()  # Noto Sans Telugu subset has no Latin punctuation
    bg, accent, deep = THEMES.get(cfg.get("setup", "salon"), THEMES["salon"])
    W, H = size
    if photo and pathlib.Path(photo).exists():
        img = ImageOps.fit(Image.open(photo).convert("RGB"), size, Image.LANCZOS)
        band = Image.new("RGBA", (W, int(H * 0.42)), (*deep, 215))
        img.paste(band, (0, H - band.height), band)
        ink, y0 = (255, 255, 255), H - band.height + 60
    else:
        img = Image.new("RGB", size, bg)
        d = ImageDraw.Draw(img)
        d.ellipse((W - 520, -180, W + 160, 500), fill=accent)
        d.ellipse((-220, H - 420, 380, H + 180), fill=tuple(min(255, c + 30) for c in accent))
        ink, y0 = deep, int(H * 0.30)
    d = ImageDraw.Draw(img)
    f, lines = _wrap(d, text, "anton-latin-400-normal.woff", 104 if size == FEED else 120, W - 140)
    y = y0
    for line in lines:
        d.text((70, y), line, font=f, fill=ink)
        y += int(f.size * 1.08)
    if sub:
        fs, sublines = _wrap(d, sub, "baloo-2-latin-700-normal.woff", 46, W - 140, max_lines=3)
        y += 20
        for line in sublines:
            d.text((70, y), line, font=fs, fill=ink)
            y += int(fs.size * 1.25)
    if telugu:
        ft = _font("noto-sans-telugu-telugu-700-normal.woff", 44)
        tw = d.textlength(telugu, font=ft) + 48
        d.rounded_rectangle((70, y + 24, 70 + tw, y + 104), radius=22, fill=(255, 255, 255), outline=accent, width=4)
        d.text((70 + tw / 2, y + 64), telugu, font=ft, fill=deep, anchor="mm")
    # footer: business + WhatsApp, always readable
    fb = _font("baloo-2-latin-800-normal.woff", 40)
    d.rectangle((0, H - 110, W, H), fill=deep)
    d.text((70, H - 55), cfg.get("business", "").upper()[:34], font=fb, fill=(255, 255, 255), anchor="lm")
    d.text((W - 70, H - 55), f"WhatsApp {cfg.get('phone', '')}", font=_font("baloo-2-latin-700-normal.woff", 32),
           fill=(255, 255, 255), anchor="rm")
    if index:
        d.text((W - 70, 70), index, font=_font("baloo-2-latin-700-normal.woff", 36), fill=deep, anchor="ra")
    return img


def save_jpeg(img: Image.Image, path: pathlib.Path) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return path


def render(slot: dict, copy: dict, cfg: dict, out: pathlib.Path, photos: dict | None = None) -> list[pathlib.Path]:
    """Render the media for one slot. Returns the files (JPEGs, plus an MP4 for Reels when ffmpeg exists)."""
    photo = (photos or {}).get(slot["id"])
    sid = slot["id"]
    files: list[pathlib.Path] = []
    if slot["kind"] == "carousel":
        n = len(copy["slides"])
        for k, s in enumerate(copy["slides"]):
            files.append(save_jpeg(frame(s, copy["headline"] if k == 0 else "", cfg, FEED, copy["telugu"] if k == n - 1 else "",
                                         photo if k == 0 else None, f"{k + 1}/{n}"), out / f"{sid}-{k + 1}.jpg"))
    elif slot["kind"] in ("story", "reel"):
        slides = copy["slides"][:3] if slot["kind"] == "reel" else [copy["slides"][0]]
        for k, s in enumerate(slides):
            files.append(save_jpeg(frame(s, copy["slides"][k + 1] if slot["kind"] == "story" else "", cfg, STORY,
                                         copy["telugu"] if k == len(slides) - 1 else "", photo if k == 0 else None), out / f"{sid}-{k + 1}.jpg"))
        if slot["kind"] == "reel":
            mp4 = reel(files, out / f"{sid}.mp4")
            if mp4:
                files.append(mp4)
    else:
        files.append(save_jpeg(frame(copy["headline"], copy["slides"][1] if len(copy["slides"]) > 1 else "", cfg, FEED,
                                     copy["telugu"], photo), out / f"{sid}.jpg"))
    return files


def reel(frames: list[pathlib.Path], path: pathlib.Path, seconds_each: float = 2.4) -> pathlib.Path | None:
    """A 9:16 H.264 Reel from still frames with a slow zoom (ffmpeg). Returns None when ffmpeg isn't installed."""
    ff = shutil.which("ffmpeg")
    if not ff or not frames:
        return None
    fps = 30
    n = int(seconds_each * fps)
    inputs, filters = [], []
    for i, f in enumerate(frames):
        inputs += ["-i", str(f)]  # one still frame in; zoompan emits d frames from it (looping the input multiplies work)
        filters.append(f"[{i}:v]scale=1080:1920,zoompan=z='min(zoom+0.0009,1.06)':d={n}:s=1080x1920:fps={fps},setsar=1[v{i}]")
    concat = "".join(f"[v{i}]" for i in range(len(frames))) + f"concat=n={len(frames)}:v=1:a=0,format=yuv420p[out]"
    cmd = [ff, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters + [concat]), "-map", "[out]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-movflags", "+faststart", "-r", str(fps), str(path)]
    try:
        subprocess.run(cmd, check=True, timeout=180)
    except (subprocess.SubprocessError, OSError):
        return None
    return path
