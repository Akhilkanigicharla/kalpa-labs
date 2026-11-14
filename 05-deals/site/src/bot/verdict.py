"""Telugu deal verdict (roadmap A214): "is this deal real?" from our own maths.

Three checks, each optional, at least one needed on every product post:
  history     price vs our own recorded prices (last 90 days, 3+ points)
  emi         true EMI cost, same reducing-balance formula as the site's EMI calculator
  card_offer  bank card instant-discount maths (percent with cap, or flat; minimum order)
Standard library only. Raises post.GateError on bad input so a wrong verdict never posts.
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from statistics import median

import post

HERE = Path(__file__).resolve().parent
HISTORY_DAYS = 90
MIN_POINTS = 3
HEAD = "తీర్పు / Verdict:"


def _rupees(n: float) -> str:
    return f"₹{round(n):,}"


def _int(v, field: str, did: str, lo: int = 0, hi: int = 10**8) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise post.GateError(f"{did}: {field} must be a whole number {lo}-{hi}")
    return v


def _num(v, field: str, did: str, lo: float, hi: float) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
        raise post.GateError(f"{did}: {field} must be a number {lo}-{hi}")
    return float(v)


def history_line(did: str, price: int, history, source, today: date) -> str:
    """Price vs our own log. source = 'own-log' (team typed prices seen in their browser) or an https page."""
    src = str(source or "").strip()
    if src != "own-log" and not src.startswith("https://"):
        raise post.GateError(f"{did}: history_source must be 'own-log' or an https:// page (never scraped data)")
    if not isinstance(history, list):
        raise post.GateError(f"{did}: history must be a list of {{date, price}}")
    pts = []
    for h in history:
        try:
            d = date.fromisoformat(str(h["date"]))
        except (KeyError, TypeError, ValueError):
            raise post.GateError(f"{did}: history dates must be YYYY-MM-DD") from None
        p = _int(h.get("price"), "history price", did, 1)
        if today - timedelta(days=HISTORY_DAYS) <= d < today:
            pts.append(p)
    if len(pts) < MIN_POINTS:
        raise post.GateError(f"{did}: history needs {MIN_POINTS}+ prices from the last {HISTORY_DAYS} days")
    low, mid = min(pts), median(pts)
    if price <= low:
        return f"గత {HISTORY_DAYS} రోజుల్లో అతి తక్కువ ధర (ఇంతకు ముందు కనిష్ఠం {_rupees(low)}). మంచి డీల్."
    if price <= mid:
        return f"సాధారణ ధర {_rupees(mid)} కంటే తక్కువ, కానీ కనిష్ఠం {_rupees(low)}. పర్వాలేదు."
    return f"సాధారణ ధర {_rupees(mid)} కంటే ఎక్కువ. తొందర వద్దు, ఆగండి."


def emi_cost(price: int, months: int, rate_pa: float, fee: int, gst_pct: float) -> dict:
    """Reducing-balance EMI (as fin.ts emi()); GST charged on interest + processing fee."""
    r = rate_pa / 1200
    monthly = price / months if r == 0 else price * r * (1 + r) ** months / ((1 + r) ** months - 1)
    interest = monthly * months - price
    gst = (interest + fee) * gst_pct / 100
    total = price + interest + fee + gst
    return {"monthly": round(monthly), "total": round(total), "extra": round(total - price)}


def emi_line(did: str, price: int, e) -> str:
    if not isinstance(e, dict):
        raise post.GateError(f"{did}: emi must be {{months, rate_pa, fee}}")
    months = _int(e.get("months"), "emi months", did, 3, 60)
    rate = _num(e.get("rate_pa"), "emi rate_pa", did, 0, 45)
    fee = _int(e.get("fee", 0), "emi fee", did, 0, 100000)
    gst = _num(e.get("gst_pct", 18), "emi gst_pct", did, 0, 28)
    c = emi_cost(price, months, rate, fee, gst)
    line = (f"EMI నిజ ఖర్చు: నెలకు {_rupees(c['monthly'])} × {months} నెలలు, వడ్డీ+ఫీ+GST కలిపి "
            f"మొత్తం {_rupees(c['total'])}")
    if c["extra"] > 0:
        return line + f" (నగదు ధర కంటే {_rupees(c['extra'])} ఎక్కువ)."
    return line + " (నగదు ధరకు సమానం; బ్యాంకు నిబంధనలు చూడండి)."


def card_line(did: str, price: int, o) -> str:
    if not isinstance(o, dict) or not str(o.get("bank", "")).strip():
        raise post.GateError(f"{did}: card_offer needs bank and pct+cap or flat")
    bank = str(o["bank"]).strip()
    min_order = _int(o.get("min_order", 0), "card_offer min_order", did)
    if "flat" in o:
        save = _int(o["flat"], "card_offer flat", did, 1)
    else:
        pct = _num(o.get("pct"), "card_offer pct", did, 1, 50)
        cap = _int(o.get("cap"), "card_offer cap", did, 1)
        save = min(price * pct / 100, cap)
    if price < min_order:
        return f"{bank} కార్డ్ ఆఫర్ కనీసం {_rupees(min_order)} కొనుగోలుకే; ఈ ధరకు వర్తించదు."
    save = min(save, price)
    return f"{bank} కార్డ్‌తో {_rupees(save)} తగ్గింపు → మీరు కట్టేది {_rupees(price - save)}."


def lines(d: dict, today: date) -> list[str]:
    """Verdict lines for a product deal. GateError if no check is given or any input is wrong."""
    did = d["id"]
    try:
        price = int(str(d.get("price", "")).replace(",", "").lstrip("₹").strip())
    except ValueError:
        raise post.GateError(f"{did}: verdict needs a whole rupee price") from None
    out = []
    if "history" in d:
        out.append(history_line(did, price, d["history"], d.get("history_source"), today))
    if "emi" in d:
        out.append(emi_line(did, price, d["emi"]))
        calc = os.environ.get("DEALS_CALC_URL", "").rstrip("/")
        if calc.startswith("https://"):
            out.append(f"మీ EMI మీరే లెక్కించండి / Check it: {calc}/te/emi/")
    if "card_offer" in d:
        out.append(card_line(did, price, d["card_offer"]))
    if not out:
        raise post.GateError(f"{did}: add a verdict (history, emi or card_offer); we post only checked deals")
    return [HEAD, *out]


# ---------- commission weighting (rates from Amazon's own fee page) ----------

def load_rates(path: Path = HERE / "rates.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rate_for(d: dict, rates: dict) -> float:
    """Commission % for ranking. Only stores with a checked fee table count; unknown = 0."""
    table = rates.get("stores", {}).get(str(d.get("store", "")).strip().lower())
    if not table:
        return 0.0
    return float(table.get(str(d.get("category", "")).strip().lower(), table.get("other", 0)))
