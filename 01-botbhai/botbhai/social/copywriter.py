"""Copywriter: captions, slide text, Reel scripts and story text for each planned slot.

Rules of thumb used (see research/social-team.md):
- English first line that works without "see more", one warm Telugu line, a clear WhatsApp call to action.
- 3 to 5 hashtags (Instagram's own creator guidance), local area tags first.
- Never invent facts: offers come from the owner's FAQ/config, reviews and photos must be real. When something real
  is needed, the item carries `needs` so the owner is asked for it during approval.
An optional LLM pass (Groq, owner's key) may polish wording later; the template output is always valid on its own.
"""
from __future__ import annotations

import re

TE_FESTIVAL = {"Sankranti": "సంక్రాంతి", "Holi": "హోలీ", "Women's Day": "మహిళా దినోత్సవం", "Ugadi": "ఉగాది",
               "Bathukamma": "బతుకమ్మ", "Dussehra": "దసరా", "Diwali": "దీపావళి", "Christmas": "క్రిస్మస్"}
TE_LINE = {"tip": "చిన్న టిప్, పెద్ద తేడా!", "work": "మా పని మీరే చూడండి 👀", "proof": "మా కస్టమర్ మాటల్లో ❤️",
           "offer": "ఇప్పుడే బుక్ చేయండి!", "team": "మా టీమ్‌ని కలవండి 🙌", "festival": "{fest} శుభాకాంక్షలు! 🎉"}
NICHE_TAG = {"salon": ["HyderabadSalon", "HairCareTips"], "gym": ["HyderabadFitness", "GymLife"],
             "realestate": ["HyderabadRealEstate", "HyderabadHomes"], "examkits": ["TSPSC", "CompetitiveExams"]}
WORK_IDEA = {"salon": "a before/after of a real {service} (customer's written OK)", "gym": "a member's form check during {service} training",
             "realestate": "a 20-second walk-through of {service}", "examkits": "a 30-second clip from today's {service} class"}
TEAM_IDEA = {"salon": "your stylist at work", "gym": "your trainer demonstrating a warm-up", "realestate": "your site visit team",
             "examkits": "your faculty at the board"}


def _plain(s: str) -> str:
    s = re.sub(r"[*_~]", "", str(s))
    s = re.sub(r"\s*Reply \*?\w+\*?.*$", "", s).strip()
    return s


def _price(cfg: dict, service: str) -> str | None:
    for c in cfg.get("catalog", []):
        if c.get("name") == service and c.get("price"):
            return c["price"]
    return None


def hashtags(cfg: dict, n: int = 5) -> list[str]:
    if cfg.get("hashtags"):
        return ["#" + re.sub(r"[^A-Za-z0-9]", "", t) for t in cfg["hashtags"]][:n]
    area = re.sub(r"[^A-Za-z]", "", (cfg.get("areas") or ["Hyderabad"])[0])
    biz = re.sub(r"[^A-Za-z0-9]", "", cfg.get("business", ""))[:24]
    tags = [area, "Hyderabad"] + NICHE_TAG.get(cfg.get("setup", ""), []) + [biz]
    out = []
    for t in tags:
        if t and t not in out:
            out.append(t)
    return ["#" + t for t in out[:n]]


def cta(cfg: dict) -> str:
    if cfg.get("cta"):
        return f"👉 {cfg['cta']['label']}: {cfg['cta']['url']}"
    return f"📲 Book on WhatsApp: wa.me/{cfg.get('whatsapp', '')}"


def cta_short(cfg: dict) -> str:
    return cfg.get("cta_short") or ("Link in bio" if cfg.get("cta") else "Book on WhatsApp")


SCENE = {"salon": "a bright, clean unisex salon in Hyderabad with warm wooden mirrors and plants",
         "gym": "a well-lit neighbourhood gym in Hyderabad with racks of dumbbells",
         "realestate": "a modern apartment balcony in west Hyderabad at golden hour",
         "examkits": "a tidy study desk with notebooks, a lamp and exam books"}
AI_OK = {"tip", "offer", "festival"}  # never AI images for work/proof/team: those must be real photos


def image_prompt(slot: dict, cfg: dict, headline: str) -> str | None:
    """A structured prompt for any free image model (atomic fields: subject, scene, lighting, composition, text,
    style, format, avoid), in the spirit of 'prompt as code' libraries such as freestylefly/awesome-gpt-image-2 (MIT).
    Only for illustrative pillars; real work, reviews and team posts need real photos."""
    if slot["pillar"] not in AI_OK:
        return None
    setup = cfg.get("setup", "salon")
    fmt = "9:16 vertical" if slot["kind"] in ("reel", "story") else "4:5 portrait"
    fest = f", subtle {slot['festival']} decorations (diyas, marigolds)" if slot.get("festival") else ""
    return "\n".join([
        f"Subject: {slot['service']} at {cfg.get('business', '')}, shown as an inviting still life, no faces",
        f"Scene: {cfg.get('scene') or SCENE.get(setup, 'a clean local business in Hyderabad')}{fest}",
        "Lighting: soft natural daylight, gentle shadows",
        "Composition: subject in the lower two-thirds, empty space at the top for a headline",
        f"Text: none in the image (headline '{_plain(headline)[:60]}' is added later)",
        "Style: realistic photo, warm and friendly, Indian context",
        f"Format: {fmt}",
        "Avoid: people's faces, before/after comparisons, logos of other brands, fake prices, any text",
    ])


def write(slot: dict, cfg: dict, i: int = 0) -> dict:
    """Return the copy for one slot: caption, slides (carousel), script (reel), story text, alt text, needs."""
    setup, biz, service, p = cfg.get("setup", "salon"), cfg.get("business", ""), slot["service"], slot["pillar"]
    faqs = [f for f in cfg.get("faqs", []) if f.get("a")]
    fest = slot.get("festival")
    needs: list[str] = []
    price = _price(cfg, service)
    go = cta_short(cfg)
    if p == "festival" and fest:
        head = f"{fest} is almost here! Get festival-ready at {biz}." if not cfg.get("festival_line") else f"Happy {fest} from {biz}!"
        body = (cfg.get("festival_line") or "Festive weeks fill fast. Book your {service} slot early.").format(service=service, fest=fest)
        slides = [f"{fest} is coming", f"Book {service} early" if not cfg.get("festival_line") else service, "Slots fill fast" if not cfg.get("festival_line") else f"Happy {fest}", go]
    elif p == "tip":
        tip = _plain(faqs[i % len(faqs)]["a"]) if faqs else f"Ask us anything about {service}."
        head = f"Quick tip from our team ✨"
        body = tip[:260]
        slides = ["Quick tip", tip[:90], f"Need help? We're at {cfg['address'].split(',')[0]}" if cfg.get("address") else f"More free tips from {biz}", go]
    elif p == "work":
        head = (cfg["work_head"].format(service=service) if cfg.get("work_head") else f"Inside {service}: take a quick look." if setup == "realestate"
                else f"Fresh from our {'studio' if setup == 'salon' else 'class' if setup == 'examkits' else 'floor'} today: {service}.")
        body = "Real work, real people. Tell us what you'd like next."
        needs.append("photo: " + (cfg.get("work_idea") or WORK_IDEA.get(setup, "a real photo of {service}")).format(service=service))
        slides = [service, "Before", "After", go] if not cfg.get("work_idea") else [service, "How it works", "Real screen, real data", go]
    elif p == "proof":
        head = "What our customers say 💬"
        body = "\"[paste a real review here, with the customer's OK]\""
        needs.append("review: a real customer review and their permission to share it")
        slides = ["Customer love", "[real review]", f"— a {biz} customer", go]
    elif p == "offer":
        offer = next((_plain(f["a"]) for f in faqs if f.get("id") in ("offers", "offer", "trial", "visit")), None)
        head = f"{service}{f' at {price}' if price else ''} 👇"
        body = offer[:240] if offer else (f"{cfg['cta']['label']} today." if cfg.get("cta") else f"Message us to book {service}. We confirm in seconds.")
        slides = [service, price or ("Details at the link" if cfg.get("cta") else "Ask for today's price"), (offer or ("Takes 2 minutes" if cfg.get("cta") else "Book in 30 seconds"))[:80], go]
    else:  # team
        head = f"Meet the people behind {biz} 🙌"
        body = "Friendly, trained and on time. Come say hi!"
        needs.append("photo: " + (cfg.get("team_idea") or TEAM_IDEA.get(setup, "your team at work")))
        slides = ["Meet the team", "Trained & friendly", "On time, every time", go] if not cfg.get("team_idea") else ["Meet the builder", "Made in Hyderabad", "Built in public", go]
    te = TE_LINE.get(p, "").replace("{fest}", TE_FESTIVAL.get(fest or "", fest or "")) if cfg.get("telugu", True) else ""
    if te and cfg.get("cta") and p == "offer":
        te = "ఇప్పుడే ప్రయత్నించండి!"  # "try it now" (not "book")
    tags = " ".join(hashtags(cfg))
    caption = "\n\n".join(x for x in (head, body, te, cta(cfg), cfg.get("disclaimer", ""), tags) if x)
    if cfg.get("affiliate") and "#ad" not in caption.lower():
        caption += " #ad"  # ASCI: affiliate links carry a clear label
    if setup == "realestate":
        rera = cfg.get("rera_number")
        caption += f"\n\nTG RERA: {rera}" if rera else ""
        if not rera:
            needs.append("rera: the project's TG RERA registration number (required in every property ad)")
    script = None
    if slot["kind"] == "reel":
        script = [{"sec": "0-2", "on_screen": slides[0], "shot": "hook: the result first"},
                  {"sec": "2-5", "on_screen": slides[1], "shot": "the process, 3 quick cuts"},
                  {"sec": "5-7", "on_screen": go, "shot": "logo + link" if cfg.get("cta") else "logo + number"}]
    story = f"{slides[0]} · {slides[1]}" if slot["kind"] == "story" else None
    return {"caption": caption, "headline": head, "slides": slides, "script": script, "story": story,
            "alt": f"{biz}: {head}", "needs": needs, "telugu": te, "image_prompt": image_prompt(slot, cfg, head)}
