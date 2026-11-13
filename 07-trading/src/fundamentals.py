"""Fundamental scorecard for one Indian stock (reel 13 Nov 2026: FinEdge "How to fundamentally
analyse any stock" worksheet).

The worksheet's checkpoints, turned into checks a machine can repeat:
  revenue growth, profitability (net margin + operating-margin trend), ROE / ROCE, debt,
  cash-flow quality (free cash flow vs profit), promoter holding + pledging, valuation vs
  peers, margin of safety, red flags.

Thresholds are SCREENING DEFAULTS, not advice. Where the worksheet gives a number we use it
("ROE consistently > 20%" is its example of a strong business); the rest are common rules of
thumb, marked `rule_of_thumb` in THRESHOLDS so nobody mistakes them for facts. Change them in
one place. Inputs come from the company's own annual reports / exchange filings (NSE/BSE),
typed in by hand or loaded from a file: this module never scrapes anything.

Use: score(Company(...)) -> Report with a 0-100 score, a pass/watch/fail per check, and the
plain-English reason for each. The trading lab's gate still decides anything that trades.
"""
from __future__ import annotations

from dataclasses import dataclass, field

THRESHOLDS = {
    # name: (value, source)
    "revenue_cagr_min": (0.10, "rule_of_thumb"),
    "roe_min": (0.20, "FinEdge worksheet example: 'consistently > 20%'"),
    "roce_min": (0.15, "rule_of_thumb"),
    "debt_equity_max": (0.50, "rule_of_thumb"),
    "fcf_to_profit_min": (0.70, "rule_of_thumb: most profit should turn into free cash"),
    "promoter_min": (0.40, "rule_of_thumb"),
    "pledge_max": (0.0, "FinEdge worksheet: 'stable (no pledging)'"),
    "pe_vs_peer_max": (1.20, "rule_of_thumb: up to 20% above peer P/E"),
    "margin_of_safety_min": (0.15, "rule_of_thumb: buy 15%+ below your own fair value"),
}


@dataclass
class Company:
    name: str
    revenue: list[float]              # oldest -> newest, same units each year (e.g. Rs crore)
    net_profit: list[float]
    operating_margin: list[float]     # fractions, e.g. 0.188
    roe: list[float]
    roce: list[float]
    debt_equity: float
    free_cash_flow: list[float]
    promoter_holding: list[float]     # fractions, oldest -> newest
    promoter_pledged: float = 0.0     # fraction of promoter shares pledged
    pe: float | None = None
    peer_pe: float | None = None
    price: float | None = None
    fair_value: float | None = None   # YOUR estimate (e.g. DCF); None skips margin of safety


@dataclass
class Check:
    name: str
    status: str   # "pass" | "watch" | "fail" | "skip"
    why: str


@dataclass
class Report:
    company: str
    score: int
    checks: list[Check] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)

    def table(self) -> str:
        rows = [f"{self.company}: {self.score}/100", ""]
        rows += [f"- [{c.status.upper():5}] {c.name}: {c.why}" for c in self.checks]
        if self.red_flags:
            rows += ["", "Red flags:"] + [f"- {r}" for r in self.red_flags]
        rows += ["", "Screening only, not investment advice."]
        return "\n".join(rows)


def _t(key: str) -> float:
    return THRESHOLDS[key][0]


def cagr(series: list[float]) -> float:
    if len(series) < 2 or series[0] <= 0 or series[-1] <= 0:
        raise ValueError("CAGR needs 2+ positive values")
    return (series[-1] / series[0]) ** (1 / (len(series) - 1)) - 1


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def _validate(c: Company):
    n = len(c.revenue)
    if n < 2:
        raise ValueError("need at least 2 years of revenue")
    for nm in ("net_profit", "operating_margin", "roe", "roce", "free_cash_flow"):
        if len(getattr(c, nm)) != n:
            raise ValueError(f"{nm} must have {n} years like revenue")
    if not c.promoter_holding:
        raise ValueError("promoter_holding needs at least one value")


def score(c: Company) -> Report:
    _validate(c)
    checks: list[Check] = []
    flags: list[str] = []

    g = cagr(c.revenue)
    checks.append(Check("Revenue growth", "pass" if g >= _t("revenue_cagr_min") else "watch" if g > 0 else "fail",
                        f"{_pct(g)} a year over {len(c.revenue) - 1} years"))
    if any(b < a for a, b in zip(c.revenue, c.revenue[1:])):
        flags.append("Revenue fell in at least one year")

    margins_up = c.operating_margin[-1] >= c.operating_margin[0]
    losses = [p for p in c.net_profit if p <= 0]
    prof = "fail" if losses else "pass" if margins_up else "watch"
    checks.append(Check("Profitability", prof,
                        f"operating margin {_pct(c.operating_margin[0])} -> {_pct(c.operating_margin[-1])}"
                        + (f"; {len(losses)} loss year(s)" if losses else "")))

    roe_ok = min(c.roe) >= _t("roe_min")
    roce_ok = min(c.roce) >= _t("roce_min")
    checks.append(Check("ROE / ROCE", "pass" if roe_ok and roce_ok else "watch" if c.roe[-1] >= _t("roe_min") or roce_ok else "fail",
                        f"lowest ROE {_pct(min(c.roe))}, lowest ROCE {_pct(min(c.roce))}"))

    de = c.debt_equity
    checks.append(Check("Debt", "pass" if de <= _t("debt_equity_max") else "watch" if de <= 1.0 else "fail",
                        f"debt/equity {de:.2f}x"))

    tot_profit = sum(c.net_profit)
    conv = sum(c.free_cash_flow) / tot_profit if tot_profit > 0 else 0.0
    checks.append(Check("Cash-flow quality", "pass" if conv >= _t("fcf_to_profit_min") else "watch" if conv >= 0.4 else "fail",
                        f"free cash flow = {_pct(conv)} of profit over the period"))
    if c.free_cash_flow[-1] < c.free_cash_flow[0] and c.net_profit[-1] > c.net_profit[0]:
        flags.append("Profit rising while free cash flow falls")

    ph = c.promoter_holding
    falling = ph[-1] < ph[0]
    pledged = c.promoter_pledged > _t("pledge_max")
    pstat = "fail" if pledged and c.promoter_pledged > 0.2 else "watch" if pledged or falling or ph[-1] < _t("promoter_min") else "pass"
    checks.append(Check("Promoter holding", pstat,
                        f"{_pct(ph[-1])} held" + (f", {_pct(c.promoter_pledged)} pledged" if pledged else ", no pledge")
                        + (", falling" if falling else "")))
    if pledged:
        flags.append("Promoter shares are pledged")

    if c.pe and c.peer_pe:
        rel = c.pe / c.peer_pe
        checks.append(Check("Valuation vs peers", "pass" if rel <= 1.0 else "watch" if rel <= _t("pe_vs_peer_max") else "fail",
                            f"P/E {c.pe:.1f} vs peer {c.peer_pe:.1f} ({rel:.2f}x)"))
    else:
        checks.append(Check("Valuation vs peers", "skip", "P/E or peer P/E missing"))

    if c.price and c.fair_value:
        mos = 1 - c.price / c.fair_value
        checks.append(Check("Margin of safety", "pass" if mos >= _t("margin_of_safety_min") else "watch" if mos >= 0 else "fail",
                            f"price {_pct(mos)} below your fair value" if mos >= 0 else f"price {_pct(-mos)} ABOVE your fair value"))
    else:
        checks.append(Check("Margin of safety", "skip", "no fair-value estimate given"))

    pts = {"pass": 1.0, "watch": 0.5, "fail": 0.0}
    scored = [c_ for c_ in checks if c_.status != "skip"]
    s = round(100 * sum(pts[c_.status] for c_ in scored) / len(scored)) - 5 * len(flags)
    return Report(c.name, max(0, min(100, s)), checks, flags)
