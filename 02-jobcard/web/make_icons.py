#!/usr/bin/env python3
"""JobCard PWA icons on the Kalpavruksha tokens: river (--l2) tile, fruit-gold ring, canopy-green centre.
Run: python3 02-jobcard/web/make_icons.py (Pillow). Drawn at 4x and scaled down for smooth edges."""
import pathlib
from PIL import Image, ImageDraw
L2, GOLD, HERO = "#2F6F78", "#C38E12", "#1D3A25"  # 00-hq/design/tokens.css (light)
OUT = pathlib.Path(__file__).resolve().parent / "icons"

def icon(size, ring_r, dot_r, maskable):
    k = 4; s = size * k; c = s // 2
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if maskable: d.rectangle((0, 0, s, s), fill=L2)                       # full bleed: the OS crops the shape
    else: d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=L2)
    d.ellipse((c - ring_r * k, c - ring_r * k, c + ring_r * k, c + ring_r * k), fill=GOLD)
    d.ellipse((c - dot_r * k, c - dot_r * k, c + dot_r * k, c + dot_r * k), fill=HERO)
    return im.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    big = icon(512, 184, 66, False)          # same geometry as the first set (ring 72..441, dot 190..323)
    big.save(OUT / "icon-512.png"); big.resize((192, 192), Image.LANCZOS).save(OUT / "icon-192.png")
    icon(512, 148, 52, True).save(OUT / "maskable-512.png")  # inside the 80% safe zone
    print("icons written →", OUT)
