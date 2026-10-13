"""Built-in, dependency-free PII recognizers for Indian LLM logs.

Each recognizer is a context-free regex plus a validator (checksum or shape
rule). Values are normalised before hashing so the same number written as
"7260 1815 9082" and "726018159082" dedupes to one hash.

Algorithms used here are public: Verhoeff (1969) for Aadhaar, Luhn (ISO/IEC
7812) for cards, and the GSTN mod-36 check character for GSTIN.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterator

# ---------------------------------------------------------------- validators

_VD = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_VP = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def verhoeff_ok(digits: str) -> bool:
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _VD[c][_VP[i % 8][int(ch)]]
    return c == 0


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        x = int(ch)
        if i % 2:
            x *= 2
            if x > 9:
                x -= 9
        total += x
    return total % 10 == 0


_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gstin_ok(g: str) -> bool:
    g = g.upper()
    if len(g) != 15 or not 1 <= int(g[:2]) <= 99:
        return False
    total = 0
    for i, ch in enumerate(g[:14]):
        p = _B36.index(ch) * (1 if i % 2 == 0 else 2)
        total += p // 36 + p % 36
    return g[14] == _B36[(36 - total % 36) % 36]


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def _aadhaar_ok(v: str) -> bool:
    d = _digits(v)
    return len(d) == 12 and d[0] not in "01" and verhoeff_ok(d)


def _card_ok(v: str) -> bool:
    d = _digits(v)
    if not 13 <= len(d) <= 19 or len(set(d)) == 1:
        return False
    return d[0] in "23456" and luhn_ok(d)  # Visa/MC/RuPay/Amex/Discover ranges


# --------------------------------------------------------------- recognizers

# Common UPI handles (NPCI PSP list subset). Restricting the handle keeps
# "user@localhost" style strings out.
UPI_HANDLES = (
    "okaxis okhdfcbank okicici oksbi ybl ibl axl paytm pthdfc ptaxis ptsbi ptyes upi apl "
    "yapl rapl abfspay axisbank axisb hdfcbank icici sbi kotak kbl yesbank yesbankltd "
    "idfcbank idfcfirst federal fbl indus barodampay boi pnb unionbankofindia uboi cnrb "
    "airtel jio freecharge mobikwik ikwik amazonpay waaxis wahdfcbank waicici wasbi "
    "slice jupiteraxis fam timecosmos naviaxis superyes"
).split()


@dataclass(frozen=True)
class Recognizer:
    entity: str
    pattern: re.Pattern
    validate: Callable[[str], bool]
    normalise: Callable[[str], str]


def _mobile_norm(v: str) -> str:
    return "+91" + _digits(v)[-10:]


RECOGNIZERS: list[Recognizer] = [
    Recognizer(
        "EMAIL",
        re.compile(r"(?<![\w.+-])[A-Za-z0-9][A-Za-z0-9._%+-]{0,63}@"
                   r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}(?![\w-])"),
        lambda v: True,
        lambda v: v.lower(),
    ),
    Recognizer(
        "GSTIN",
        re.compile(r"(?<![A-Za-z0-9])\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z](?![A-Za-z0-9])"),
        gstin_ok,
        lambda v: v.upper(),
    ),
    Recognizer(
        "CARD",
        re.compile(r"(?<![\w-])\d{4}([ -]?)\d{4}\1\d{4}\1\d{1,7}(?![\w-])"),
        _card_ok,
        _digits,
    ),
    Recognizer(
        "AADHAAR",
        re.compile(r"(?<![\w])(?<![0-9a-fA-F]-)[2-9]\d{3}([ -]?)\d{4}\1\d{4}(?![\w]|-\w)"),
        _aadhaar_ok,
        _digits,
    ),
    Recognizer(
        "IN_MOBILE",
        re.compile(r"(?<![\w+])(?:\+91[ -]?|0)?[6-9]\d{4}[ -]?\d{5}(?![\w]|-\w)"),
        lambda v: True,
        _mobile_norm,
    ),
    Recognizer(
        "PAN",
        re.compile(r"(?<![A-Za-z0-9])[A-Z]{3}[ABCFGHJLPT][A-Z]\d{4}[A-Z](?![A-Za-z0-9])"),
        lambda v: True,
        lambda v: v.upper(),
    ),
    Recognizer(
        "IFSC",
        re.compile(r"(?<![A-Za-z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Za-z0-9])"),
        lambda v: True,
        lambda v: v.upper(),
    ),
    Recognizer(
        "UPI_ID",
        re.compile(r"(?<![\w.+-])[A-Za-z0-9][A-Za-z0-9._-]{1,255}@(" + "|".join(UPI_HANDLES)
                   + r")(?![\w.@-])", re.IGNORECASE),
        lambda v: True,
        lambda v: v.lower(),
    ),
]

ENTITIES = [r.entity for r in RECOGNIZERS]


@dataclass(frozen=True)
class Finding:
    entity: str
    start: int
    end: int
    norm: str  # normalised value; used only for hashing, never written out


def find(text: str) -> Iterator[Finding]:
    """Yield non-overlapping findings. Earlier recognizers win overlaps
    (so the PAN inside a GSTIN is not counted twice)."""
    taken: list[tuple[int, int]] = []
    out: list[Finding] = []
    for rec in RECOGNIZERS:
        for m in rec.pattern.finditer(text):
            s, e = m.span()
            if any(s < te and ts < e for ts, te in taken):
                continue
            v = m.group(0)
            if not rec.validate(v):
                continue
            taken.append((s, e))
            out.append(Finding(rec.entity, s, e, rec.normalise(v)))
    out.sort(key=lambda f: f.start)
    yield from out
