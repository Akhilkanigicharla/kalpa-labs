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
    area = re.sub(r"[^A-Za-z]", "", (cfg.get("areas") or ["Hyderabad"])[0])
    biz = re.sub(r"[^A-Za-z0-9]", "", cfg.get("business", ""))[:24]
    tags = [area, "Hyderabad"] + NICHE_TAG.get(cfg.get("setup", ""), []) + [biz]
    out = []
    for t in tags:
        if t and t not in out:
            out.append(t)
    return ["#" + t for t in out[:n]]


def cta(cfg: dict) -> str:
    return f"📲 Book on WhatsApp: wa.me/{cfg.get('whatsapp', '')}"


def write(slot: dict, cfg: dict, i: int = 0) -> dict:
    """Return the copy for one slot: caption, slides (carousel), script (reel), story text, alt text, needs."""
    setup, biz, service, p = cfg.get("setup", "salon"), cfg.get("business", ""), slot["service"], slot["pillar"]
    faqs = [f for f in cfg.get("faqs", []) if f.get("a")]
    fest = slot.get("festival")
    needs: list[str] = []
    price = _price(cfg, service)
    if p == "festival" and fest:
        head = f"{fest} is almost here! Get festival-ready at {biz}."
        body = f"Festive weeks fill fast. Book your {service} slot early."
        slides = [f"{fest} is coming", f"Book {service} early", "Slots fill fast", "Book on WhatsApp"]
    elif p == "tip":
        tip = _plain(faqs[i % len(faqs)]["a"]) if faqs else f"Ask us anything about {service}."
        head = f"Quick tip from our team ✨"
        body = tip[:260]
        slides = ["Quick tip", tip[:90], f"Need help? We're at {cfg.get('address', 'Hyderabad').split(',')[0]}", "Book on WhatsApp"]
    elif p == "work":
        head = (f"Inside {service}: take a quick look." if setup == "realestate"
                else f"Fresh from our {'studio' if setup == 'salon' else 'class' if setup == 'examkits' else 'floor'} today: {service}.")
        body = "Real work, real people. Tell us what you'd like next."
        needs.append("photo: " + WORK_IDEA.get(setup, "a real photo of {service}").format(service=service))
        slides = [service, "Before", "After", "Book on WhatsApp"]
    elif p == "proof":
        head = "What our customers say 💬"
        body = "\"[paste a real review here, with the customer's OK]\""
        needs.append("review: a real customer review and their permission to share it")
        slides = ["Customer love", "[real review]", f"— a {biz} customer", "Book on WhatsApp"]
    elif p == "offer":
        offer = next((_plain(f["a"]) for f in faqs if f.get("id") in ("offers", "offer", "trial", "visit")), None)
        head = f"{service}{f' at {price}' if price else ''} 👇"
        body = offer[:240] if offer else f"Message us to book {service}. We confirm in seconds."
        slides = [service, price or "Ask for today's price", (offer or "Book in 30 seconds")[:80], "Book on WhatsApp"]
    else:  # team
        head = f"Meet the people behind {biz} 🙌"
        body = "Friendly, trained and on time. Come say hi!"
        needs.append("photo: " + TEAM_IDEA.get(setup, "your team at work"))
        slides = ["Meet the team", "Trained & friendly", "On time, every time", "Book on WhatsApp"]
    te = TE_LINE.get(p, "").replace("{fest}", TE_FESTIVAL.get(fest or "", fest or ""))
    tags = " ".join(hashtags(cfg))
    caption = f"{head}\n\n{body}\n\n{te}\n\n{cta(cfg)}\n\n{tags}".strip()
    if setup == "realestate":
        rera = cfg.get("rera_number")
        caption += f"\n\nTG RERA: {rera}" if rera else ""
        if not rera:
            needs.append("rera: the project's TG RERA registration number (required in every property ad)")
    script = None
    if slot["kind"] == "reel":
        script = [{"sec": "0-2", "on_screen": slides[0], "shot": "hook: the result first"},
                  {"sec": "2-5", "on_screen": slides[1], "shot": "the process, 3 quick cuts"},
                  {"sec": "5-7", "on_screen": "Book on WhatsApp", "shot": "logo + number"}]
    story = f"{slides[0]} · {slides[1]}" if slot["kind"] == "story" else None
    return {"caption": caption, "headline": head, "slides": slides, "script": script, "story": story,
            "alt": f"{biz}: {head}", "needs": needs, "telugu": te}
