"""Writes public/og.png (1200x630 share card for WhatsApp/LinkedIn, SEO check 18). Run: python3 scripts/og.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parents[1]
FONTS = HERE.parents[1] / "00-hq/site/fonts"
HERO, FG, MUTE, GOLD = "#1D3A25", "#F4EEDC", "#BFCDAE", "#C38E12"  # tokens.css --hero, --hero-fg, --hero-mute, --gold


def font(name, size, fallback="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"):
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        return ImageFont.truetype(fallback, size)


def main(out=HERE / "public/og.png"):
    im = Image.new("RGB", (1200, 630), HERO)
    d = ImageDraw.Draw(im)
    for x in range(0, 1200, 20):  # temple border, as on the site header
        d.ellipse((x + 6, 18, x + 14, 26), fill=GOLD)
    d.text((80, 150), "Free money calculators", font=font("rozha-one-latin-400-normal.woff", 84), fill=FG)
    d.text((80, 270), "Income tax 2026-27 · Salary · GST · SIP · EMI", font=font("anek-latin-latin-600-normal.woff", 44), fill=MUTE)
    d.text((80, 340), "Gratuity · FD · RD · PPF · in English and Telugu", font=font("anek-latin-latin-600-normal.woff", 44), fill=MUTE)
    d.text((80, 520), "Kalpa Labs · no sign-up, works on your phone", font=font("anek-latin-latin-600-normal.woff", 36), fill=GOLD)
    im.save(out, optimize=True)
    return out


if __name__ == "__main__":
    p = main()
    print(p.name, p.stat().st_size // 1000, "KB")
