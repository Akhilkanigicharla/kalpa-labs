"""Compliance checker: every caption is checked before the owner sees it and again before publishing.

Sources (see research/social-team.md):
- ASCI Code and its influencer guidelines: no misleading or unverifiable claims; paid partnerships carry a clear label.
- ASCI guidelines on skin-lightening/fairness advertising: no "fair = better" messages.
- Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954: no claims to cure or treat diseases.
- CCPA Guidelines for Prevention of Misleading Advertisement in the Coaching Sector (13 Nov 2024): no "100% selection"
  or guaranteed-job claims; toppers only with written consent.
- RERA Act 2016 / TG RERA: every project ad shows its RERA registration number (TG RERA fined a developer
  ₹7.59 lakh in June 2026 for an ad without it).
- Instagram: 3-5 hashtags; captions up to 2,200 characters.
"""
from __future__ import annotations

import re

BLOCK = [  # (pattern, reason) - these never go out
    (r"\b(guarantee[ds]?|guaranteed)\b", "guarantees are unverifiable claims (ASCI)"),
    (r"\b100\s*%\s*(result|results|selection|success|job|placement|guaranteed|cure)", "'100%' result/selection claims (ASCI, CCPA coaching guidelines)"),
    (r"\bpermanent(ly)?\b.*\b(hair|result|removal|fix)\b", "'permanent' results are unverifiable (ASCI)"),
    (r"\b(cure[sd]?|treat(s|ment)? for|heals?)\b.*\b(hair\s*fall|dandruff|acne|baldness|diabetes|pcos|thyroid|obesity)\b", "disease cure/treatment claims (Drugs and Magic Remedies Act)"),
    (r"\b(fairness|whiten(ing)?|skin\s*lighten(ing)?|fair\s*skin)\b", "fairness/whitening messages (ASCI skin-tone guidelines)"),
    (r"\b(no side effects?|miracle|magic)\b", "absolute or miracle claims (ASCI)"),
    (r"\b(lose|loss of)\s*\d+\s*(kg|kilos?)\s*(in|within)\s*\d+\s*(day|days|week|weeks)\b", "rapid weight-loss promises (ASCI)"),
    (r"\b(assured|confirmed)\s*(job|selection|returns?)\b", "assured selection/returns claims (CCPA, RERA)"),
    (r"\b(pre[-\s]?launch)\b", "pre-launch sales before RERA registration are not allowed (TG RERA)"),
]


BY_SETUP = {  # extra blocks per Kalpa world (pattern, reason)
    "finops": [(r"\b(100\s*%|fully|guaranteed)\s*(dpdp|iso|eu ai act)?\s*complian(t|ce)\b", "compliance can't be guaranteed; say 'evidence pack' (ASCI)"),
               (r"\b(certified|certification)\b", "we are not a certification body; never imply certification (ASCI)"),
               (r"\bsave\s*\d+\s*%", "savings % needs real client data behind it (ASCI substantiation)")],
    "trading": [(r"\b(buy|sell|target|stop\s*-?loss|entry|exit|call|tip|multibagger)\b", "SEBI: no buy/sell calls or tips from an unregistered entity"),
                (r"\b(returns?|profit|cagr|income)\b", "SEBI: no return or profit claims")],
    "deals": [(r"\blowest\s+price\s+(ever|guaranteed)\b", "'lowest price ever' is unverifiable (ASCI)")],
    "extensions": [],
    "kits": [(r"\b(crack|clear)\s+(gate|upsc|tspsc)\s+(for sure|guaranteed)", "exam success can't be promised (CCPA coaching guidelines)")],
}


def check(caption: str, *, setup: str = "salon", paid_partnership: bool = False, cfg: dict | None = None) -> dict:
    """Returns {ok, blocked: [reasons], warnings: [reasons]}."""
    t = caption or ""
    cfg = cfg or {}
    paid_partnership = paid_partnership or bool(cfg.get("affiliate"))
    low = t.lower()
    blocked = [why for pat, why in BLOCK + BY_SETUP.get(setup, []) if re.search(pat, low)]
    if cfg.get("enabled") is False:
        blocked.append(f"posting is switched off for this brand: {cfg.get('disabled_reason', 'see its profile')}")
    if setup == "extensions" and re.search(r"\bnever\s+(lose|loses|lost)\b", low):
        warnings_pre = ["'never lose' is absolute: prefer 'backs up every 5 minutes' (ASCI)"]
    else:
        warnings_pre = []
    warnings = list(warnings_pre)
    tags = re.findall(r"(?<!\w)#\w+", t)
    if len(tags) > 5:
        warnings.append(f"{len(tags)} hashtags; Instagram suggests 3-5")
    if len(t) > 2200:
        blocked.append("caption longer than Instagram's 2,200-character limit")
    if "wa.me/" not in low and "whatsapp" not in low and "http" not in low and not (cfg.get("cta") and cfg["cta"]["url"].lower() in low):
        warnings.append("no call to action (WhatsApp or link)")
    if paid_partnership and not re.search(r"#(ad|collab|sponsored|partnership)\b", low):
        blocked.append("paid partnership without a clear #ad/#collab label (ASCI influencer guidelines)")
    if setup == "realestate" and re.search(r"\b(bhk|plot|villa|flat|apartment|project)\b", low) and not re.search(r"rera[:\s]+\S+", low):
        blocked.append("property ad without a TG RERA registration number (RERA Act 2016)")
    if setup == "examkits" and re.search(r"\b(topper|rank\s*\d+|air\s*\d+|selected)\b", low):
        warnings.append("topper/result claim: needs the student's written consent and the course they took (CCPA 2024)")
    if re.search(r"\b(before|after)\b", low) and setup in ("salon", "gym"):
        warnings.append("before/after: use real, unedited photos with the customer's written OK; results vary")
    if "[paste" in low or "[real" in low or "[add" in low:
        blocked.append("placeholder left in the caption (needs the owner's real content)")
    return {"ok": not blocked, "blocked": blocked, "warnings": warnings}
