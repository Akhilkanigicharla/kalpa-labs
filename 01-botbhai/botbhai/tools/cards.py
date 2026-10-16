#!/usr/bin/env python3
"""
BotBhai "smile cards" — meme-style WhatsApp images that make reminders and follow-ups feel human.

Original artwork only: our own captions, shapes and open emoji (Noto Color Emoji, OFL/Apache) and
open fonts from the Kalpa "Kalamkari" design system (Rozha One, Anek Latin, Anek Telugu — SIL OFL, in 00-hq/design/fonts). No film stills, celebrity photos or
copyrighted meme templates, which would expose clients to copyright and personality-rights claims.

Usage:
  python tools/cards.py --setup salon --business "Glow Studio" --out web/dist/cards/glow-studio
  python tools/cards.py --all-demo            # every setup with sample names → web/dist/cards/demo
Each card is 1080×1080 PNG (WhatsApp image header / image message friendly, < 300 KB).
"""
import argparse, os, pathlib, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT.parent.parent / "00-hq" / "design" / "fonts"   # Kalamkari fonts, shared with every Kalpa UI
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
S = 1080

def _hex(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
# Kalamkari tokens (00-hq/design/tokens.css): cream ground, hero indigo, turmeric gold, madder teeth.
CREAM, HERO, GOLD, MADDER = _hex("#F6F2E8"), _hex("#1C2463"), _hex("#D3940A"), _hex("#B23A2C")
# palette per setup: (background, accent, deep). Accents are world/leaf tokens: madder, leaf, indigo, turmeric.
THEMES = {
    "salon": (CREAM, _hex("#B23A2C"), HERO),
    "gym": (CREAM, _hex("#2E7D4F"), HERO),
    "realestate": (CREAM, _hex("#2F4FB0"), HERO),
    "examkits": (CREAM, _hex("#C08304"), HERO),
}

def temple_border(d, y, flip=False, h=28):
    """The Kalamkari temple border: a band of turmeric dots over madder teeth (same as the CSS one, scaled ×2.8)."""
    step = 40
    for x in range(0, S + step, step):
        tip, base = (y + h, y) if not flip else (y, y + h)
        d.polygon([(x, base), (x + step // 2, tip), (x + step, base)], fill=MADDER)
    cy = y + (8 if not flip else h - 8)
    for x in range(step // 2, S, step):
        d.ellipse((x - 7, cy - 7, x + 7, cy + 7), fill=GOLD)

# occasion → (emoji, top caption, bottom caption, small line, optional Telugu line)
CARDS = {
    "salon": {
        "booking_confirmed": ("💇‍♀️", "SLOT BOOKED.", "GLOW-UP LOADING…", "See you soon at {business}", "మీ స్లాట్ రెడీ"),
        "day_before": ("⏰", "TOMORROW'S PLAN:", "GLOW UP. NO EXCUSES.", "Reply 1 to confirm · 2 to reschedule", None),
        "two_hours": ("💺", "THE CHAIR IS WARM.", "THE STYLIST IS READY. ARE YOU?", "See you in 2 hours", None),
        "after_visit": ("🤳", "NEW HAIR, WHO DIS?", "TELL GOOGLE HOW GOOD YOU LOOK", "A 10-second review means a lot to us", None),
        "winback": ("💌", "YOUR HAIR CALLED.", "IT MISSES US.", "15% off any service this month", "మళ్ళీ రండి"),
        "festival": ("🪁", "KITES UP.", "GLOW UP.", "Festive looks · book on WhatsApp", "సంక్రాంతి శుభాకాంక్షలు"),
    },
    "gym": {
        "booking_confirmed": ("💪", "TRIAL BOOKED.", "EXCUSES CANCELLED.", "Bring shoes + water bottle", None),
        "day_before": ("🦵", "TOMORROW:", "YOUR FUTURE SELF SAYS THANKS", "Reply 1 to confirm", None),
        "two_hours": ("👟", "SHOES? WATER?", "YOU? SEE YOU IN 2 HOURS", "{business}", None),
        "after_visit": ("🏋️", "ONE WORKOUT DOWN.", "ONLY 364 MORE TO GO", "Join this week at the trial-day price", None),
        "renew_7": ("📅", "YOUR PLAN ENDS SOON.", "YOUR GAINS DON'T HAVE TO.", "Reply RENEW for the payment link", None),
        "winback": ("🥺", "THE DUMBBELLS", "ASKED ABOUT YOU.", "2 weeks free when you come back", "మళ్ళీ మొదలెడదాం"),
    },
    "realestate": {
        "booking_confirmed": ("🏡", "SITE VISIT BOOKED.", "DREAM HOME: LOADING…", "Free pick-up available", None),
        "day_before": ("☕", "SITE VISIT TOMORROW.", "ZERO PRESSURE. JUST CHAI.", "Reply 1 to confirm", None),
        "after_visit": ("🔑", "PICTURED IT YET?", "FLOOR PLANS + EMI, ONE REPLY AWAY", "Reply YES and we'll send them", None),
        "winback": ("📈", "RENT IS A SUBSCRIPTION.", "OWNING IS AN UPGRADE.", "New launch prices · reply DETAILS", None),
        "festival": ("🪔", "GRUHA PRAVESHAM", "SEASON IS HERE", "Book a visit before the muhurtham", "గృహ ప్రవేశ శుభాకాంక్షలు"),
    },
    "examkits": {
        "booking_confirmed": ("📚", "DEMO CLASS BOOKED.", "RANK MODE: ON", "Bring a pen. Leave the fear.", None),
        "daily_question": ("🧠", "QUESTION OF THE DAY", "TOPPERS REPLY FIRST", "Reply A, B, C or D", "నేటి ప్రశ్న"),
        "day_before": ("✏️", "DEMO CLASS TOMORROW.", "BRING A PEN. LEAVE THE FEAR.", "Reply 1 to confirm", None),
        "after_visit": ("🎯", "ONE CLASS DOWN.", "YOUR RANK IS WAITING.", "Seats are filling · reply JOIN", None),
        "renew_7": ("🗓️", "FEE DUE SOON.", "FOCUS ON SYLLABUS, NOT DATES", "Reply PAY for the link", None),
    },
}

def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)

def emoji_image(ch, size):
    """Noto Color Emoji is a bitmap font that only renders at 109 px; draw there, then scale."""
    f = ImageFont.truetype(EMOJI_FONT, 109)
    tile = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    box = tile.getbbox() or (0, 0, 160, 160)
    tile = tile.crop(box)
    scale = size / max(tile.size)
    return tile.resize((max(1, int(tile.width * scale)), max(1, int(tile.height * scale))), Image.LANCZOS)

def meme_text(draw, text, y, size, fill=(255, 255, 255), stroke=HERO, max_w=S - 120):
    """Meme caption in Rozha One (display face, never bold): white with an indigo outline, auto-shrinks to fit."""
    f = font("rozha-one-latin-400-normal.woff", size)
    while draw.textlength(text, font=f) > max_w and size > 40:
        size -= 4; f = font("rozha-one-latin-400-normal.woff", size)
    lines = [text] if draw.textlength(text, font=f) <= max_w else textwrap.wrap(text, 18)
    for i, line in enumerate(lines):
        draw.text((S // 2, y + i * int(size * 1.08)), line, font=f, fill=fill, stroke_width=max(4, size // 14), stroke_fill=stroke, anchor="ma")
    return y + len(lines) * int(size * 1.08)

def make_card(setup, key, business):
    bg, accent, deep = THEMES[setup]
    emo, top, bottom, small, te = CARDS[setup][key]
    img = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(img)
    # soft background shapes (confetti dots + a big accent circle behind the emoji)
    for i, (x, y, r) in enumerate([(120, 260, 18), (960, 300, 26), (180, 760, 22), (900, 720, 14), (540, 170, 10), (80, 520, 12), (1000, 520, 16)]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=accent if i % 2 == 0 else deep)
    # medallion behind the emoji: a gold/madder rosette ring around the world colour (Kalamkari medallion badge)
    cx, cy, R = S // 2, 520, 236
    for k in range(16):
        d.pieslice((cx - R, cy - R, cx + R, cy + R), k * 22.5, (k + 1) * 22.5, fill=GOLD if k % 2 == 0 else MADDER)
    d.ellipse((cx - 210, cy - 210, cx + 210, cy + 210), fill=accent)
    d.ellipse((cx - 186, cy - 186, cx + 186, cy + 186), fill=tuple(min(255, c + 40) for c in accent))
    temple_border(d, 0); temple_border(d, S - 28, flip=True)
    e = emoji_image(emo, 300)
    img.paste(e, (S // 2 - e.width // 2, 520 - e.height // 2), e)
    # captions
    meme_text(d, top, 60, 120)
    meme_text(d, bottom, 780, 92)
    # footer pill: small line + business
    line = small.replace("{business}", business)
    f_small = font("anek-latin-latin-700-normal.woff", 38)
    w = d.textlength(line, font=f_small) + 70
    d.rounded_rectangle((S // 2 - w / 2, 905, S // 2 + w / 2, 965), radius=30, fill=deep)
    d.text((S // 2, 935), line, font=f_small, fill=(255, 255, 255), anchor="mm")
    d.text((S // 2, 1012), business.upper(), font=font("anek-latin-latin-700-normal.woff", 34), fill=deep, anchor="mm")
    if te:  # a Telugu sticker in the corner — local, warm, human
        ft = font("anek-telugu-telugu-700-normal.woff", 40)
        tw = d.textlength(te, font=ft) + 40
        sticker = Image.new("RGBA", (int(tw), 80), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sticker)
        sd.rounded_rectangle((0, 0, tw - 1, 79), radius=18, fill=(255, 255, 255), outline=GOLD, width=5)
        sd.text((tw / 2, 40), te, font=ft, fill=deep, anchor="mm")
        sticker = sticker.rotate(-8, expand=True, resample=Image.BICUBIC)
        img.paste(sticker, (S - sticker.width - 40, 250), sticker)
    return img

def build(setup, business, out):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    files = []
    for key in CARDS[setup]:
        p = out / f"{setup}-{key}.png"
        make_card(setup, key, business).save(p, optimize=True)
        files.append(p)
    return files

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", choices=list(CARDS)); ap.add_argument("--business", default="Your Business")
    ap.add_argument("--out", default=str(ROOT / "web" / "dist" / "cards" / "demo")); ap.add_argument("--all-demo", action="store_true")
    a = ap.parse_args()
    demo = {"salon": "Glow Studio", "gym": "IronPulse Fitness", "realestate": "Skyline Homes", "examkits": "Vidya Academy"}
    for setup in (CARDS if a.all_demo else [a.setup]):
        for f in build(setup, demo[setup] if a.all_demo else a.business, a.out):
            print(f, f"{os.path.getsize(f) // 1024} KB")
