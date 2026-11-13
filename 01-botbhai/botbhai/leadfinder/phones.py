"""A208: keep only business numbers in lead lists. Indian mobile numbers can be a person's own phone
(DPDP personal data, TRAI rules on unsolicited calls), so every mobile is withheld, whatever source listed it.
Landlines (STD code + number) and toll-free numbers are business lines and are kept."""
import re

def classify(raw):
    """Return (kind, number): kind is 'landline', 'tollfree', 'mobile' or 'unknown'; number is digits with +91."""
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("1800") or d.startswith("1860"): return "tollfree", d
    if d.startswith("91") and len(d) == 12: d = d[2:]
    elif d.startswith("0") and len(d) == 11: d = d[1:]
    if len(d) != 10: return "unknown", ""
    if d[0] in "6789": return "mobile", "+91" + d
    return "landline", "+91" + d

def business_phone(*values):
    """First landline/toll-free number among the values (each may hold several, split by ; , or /).
    Returns (number, withheld) where withheld counts mobile or unreadable numbers dropped."""
    withheld = 0
    for v in values:
        for part in re.split(r"[;,/]", v or ""):
            if not part.strip(): continue
            kind, num = classify(part)
            if kind in ("landline", "tollfree"): return num, withheld
            withheld += 1
    return "", withheld

# A208 part 2: a mobile written inside free text (address, name, email). Only a run of 10 digits that starts 6-9,
# with at most single spaces/hyphens between digits and an optional +91/91/0 prefix, counts. House numbers like
# "1-2-3/4" and pincodes like 500072 never form such a run, so they stay.
MOBILE_RUN = re.compile(r"(?<![\d])(?:(?:\+?91|0)[\s-]?)?[6-9](?:[\s-]?\d){9}(?![\d])")

def has_mobile(text):
    return bool(MOBILE_RUN.search(text or ""))

def scrub_mobiles(text):
    """(text with each mobile replaced by '[number withheld]', how many were replaced)."""
    return MOBILE_RUN.subn("[number withheld]", text or "")
