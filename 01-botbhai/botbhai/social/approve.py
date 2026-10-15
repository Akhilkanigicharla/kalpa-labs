"""Owner approval on WhatsApp: nothing is published until the owner says OK.

The weekly batch arrives as one WhatsApp message (inside the 24-hour customer-service window the owner opened by
messaging BotBhai, or as an approved utility template). The owner replies in plain words:
  "ok" / "sare" / "haan" / "avunu"  -> approve everything that has no open needs
  "skip 3"                          -> drop item 3
  "change 2: make it about bridal"  -> send item 2 back to the copywriter with that note
  "photo 4" + an attached photo     -> use the owner's photo for item 4 (handled by the webhook)
"""
from __future__ import annotations

import re

YES = r"(ok|okay|yes|approve|approved|sare|sarey|haan|han|avunu|done|👍)"


def batch_message(items: list[dict], cfg: dict, week: str) -> str:
    lines = [f"📅 *{cfg.get('business', '')}: posts for {week}*", ""]
    for n, it in enumerate(items, 1):
        need = f"\n   ⚠️ Needs: {'; '.join(x.split(': ', 1)[-1] for x in it.get('needs', []))}" if it.get("needs") else ""
        blocked = f"\n   ⛔ Held: {'; '.join(it['check']['blocked'])}" if it.get("check") and it["check"]["blocked"] else ""
        lines.append(f"{n}. {it['date']} {it['time']} · {it['kind'].upper()} · {it['headline']}{need}{blocked}")
    lines += ["", "Reply *OK* to approve all, *skip 3* to drop one, *change 2: your note* to edit,",
              "or send a photo with *photo 4* to use your own picture. Nothing posts without your OK."]
    return "\n".join(lines)


def parse_reply(text: str, n_items: int) -> dict:
    """Returns {approve_all, skip: [..], change: {n: note}, photo: [..], unknown: bool}."""
    t = (text or "").strip().lower()
    out = {"approve_all": False, "skip": [], "change": {}, "photo": [], "unknown": False}
    if re.fullmatch(rf"\s*(?:{YES}[\s.!,]*)+(all)?[\s.!]*", t):
        out["approve_all"] = True
        return out
    for m in re.finditer(r"\b(skip|drop|remove|vaddu)\s+((?:\d+\s*(?:,|and|&)?\s*)+)", t):
        out["skip"] += [int(x) for x in re.findall(r"\d+", m.group(2)) if 1 <= int(x) <= n_items]
    for m in re.finditer(r"\b(change|edit|marchu)\s+(\d+)\s*[:\-]\s*([^\n]+?)(?=\s*\b(?:skip|change|photo|ok)\b|$)", t):
        k = int(m.group(2))
        if 1 <= k <= n_items:
            out["change"][k] = m.group(3).strip()
    out["photo"] = [int(x) for x in re.findall(r"\bphoto\s+(\d+)", t) if 1 <= int(x) <= n_items]
    if re.search(rf"(^|\s){YES}(\s|$)", t) and (out["skip"] or out["change"] or out["photo"]):
        out["approve_all"] = True  # "skip 3, rest ok"
    out["unknown"] = not (out["approve_all"] or out["skip"] or out["change"] or out["photo"])
    return out


def apply(items: list[dict], reply: dict) -> list[dict]:
    """Mark each item approved / skipped / needs_change. Items with open needs or blocked checks stay held."""
    for n, it in enumerate(items, 1):
        if n in reply["skip"]:
            it["status"] = "skipped"
        elif n in reply["change"]:
            it["status"], it["note"] = "needs_change", reply["change"][n]
        elif reply["approve_all"] and not it.get("needs") and (not it.get("check") or it["check"]["ok"]):
            it["status"] = "approved"
        elif it.get("status") in (None, "draft"):
            it["status"] = "held"
    return items
