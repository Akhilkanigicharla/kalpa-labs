"""Indian trading charges (2026) for simulated fills. Q7.3.

Every rate below carries a source and the date we checked it. The gate refuses to
run at zero cost, and a test fails if any rate is older than 90 days (Cost Modeller
validator in PLAN.md). This is a charges calculator, not advice.

Units: all values in rupees. Rates are fractions of turnover (0.001 = 0.1%).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

CHECKED = "2026-10-13"
SRC_ZERODHA = "https://zerodha.com/charges/"
SRC_EXCH = ("https://support.zerodha.com/category/account-opening/resident-individual/"
            "ri-charges/articles/exchange-transaction-charges")
SRC_STT_2026 = ("https://www.5paisa.com/news/stt-hike-on-fo-to-take-effect-from-april-1-"
                "amid-rising-options-activity")

# name -> (value, unit/notes, source, checked)
RATES: dict[str, tuple[float, str, str, str]] = {
    # Securities Transaction Tax (Finance Act; F&O rates raised 1 Apr 2026)
    "stt_delivery":        (0.001,     "0.1% on buy AND sell", SRC_ZERODHA, CHECKED),
    "stt_intraday_sell":   (0.00025,   "0.025% sell side only", SRC_ZERODHA, CHECKED),
    "stt_futures_sell":    (0.0005,    "0.05% sell side (was 0.02% before 1 Apr 2026)", SRC_STT_2026, CHECKED),
    "stt_options_sell":    (0.0015,    "0.15% of premium, sell side (was 0.1%)", SRC_STT_2026, CHECKED),
    # Exchange transaction charges (NSE figure includes IPFT)
    "nse_txn_equity":      (0.0000307, "0.00307% of turnover, incl. IPFT", SRC_EXCH, CHECKED),
    "bse_txn_equity":      (0.0000375, "0.00375% (Rs 375/crore)", SRC_EXCH, CHECKED),
    "nse_txn_futures":     (0.0000183, "0.00183%", SRC_ZERODHA, CHECKED),
    "nse_txn_options":     (0.0003553, "0.03553% of premium", SRC_ZERODHA, CHECKED),
    # SEBI turnover fee: Rs 10 per crore
    "sebi_fee":            (10 / 1e7,  "Rs 10 per crore, both sides", SRC_ZERODHA, CHECKED),
    # Stamp duty (Indian Stamp Act, uniform since 1 Jul 2020), buy side only
    "stamp_delivery_buy":  (0.00015,   "0.015% buy side", SRC_ZERODHA, CHECKED),
    "stamp_intraday_buy":  (0.00003,   "0.003% buy side", SRC_ZERODHA, CHECKED),
    "stamp_futures_buy":   (0.00002,   "0.002% buy side", SRC_ZERODHA, CHECKED),
    "stamp_options_buy":   (0.00003,   "0.003% of premium, buy side", SRC_ZERODHA, CHECKED),
    # GST on brokerage + exchange charges + SEBI fee (not on STT or stamp)
    "gst":                 (0.18,      "18%", SRC_ZERODHA, CHECKED),
    # Depository charge per scrip per sell day (Zerodha: 3.5 CDSL + 9.5 broker + 2.34 GST)
    "dp_per_scrip_sell":   (15.34,     "Rs 15.34 incl. GST, Zerodha; broker-specific", SRC_ZERODHA, CHECKED),
}


def rate(name: str) -> float:
    return RATES[name][0]


def stale_rates(today: date | None = None, max_age_days: int = 90) -> list[str]:
    """Names of rates whose check date is older than max_age_days."""
    today = today or date.today()
    return [k for k, (_, _, _, d) in RATES.items()
            if (today - date.fromisoformat(d)).days > max_age_days]


@dataclass
class Charges:
    brokerage: float = 0.0
    stt: float = 0.0
    exchange: float = 0.0
    sebi: float = 0.0
    stamp: float = 0.0
    gst: float = 0.0
    dp: float = 0.0

    @property
    def total(self) -> float:
        return (self.brokerage + self.stt + self.exchange + self.sebi
                + self.stamp + self.gst + self.dp)

    def rounded(self) -> dict[str, float]:
        d = {k: round(v, 2) for k, v in self.__dict__.items()}
        d["total"] = round(self.total, 2)
        return d


def _brokerage_capped(value: float, pct: float = 0.0003, cap: float = 20.0) -> float:
    return min(value * pct, cap) if value > 0 else 0.0


def delivery(buy_value: float, sell_value: float, *, exchange: str = "NSE",
             brokerage_per_order: float = 0.0, scrips_sold: int | None = None) -> Charges:
    """Equity delivery (CNC). Zero brokerage by default (Zerodha/most discount brokers)."""
    txn = rate("nse_txn_equity") if exchange == "NSE" else rate("bse_txn_equity")
    turnover = buy_value + sell_value
    c = Charges()
    c.brokerage = brokerage_per_order * ((buy_value > 0) + (sell_value > 0))
    c.stt = rate("stt_delivery") * turnover
    c.exchange = txn * turnover
    c.sebi = rate("sebi_fee") * turnover
    c.stamp = rate("stamp_delivery_buy") * buy_value
    c.gst = rate("gst") * (c.brokerage + c.exchange + c.sebi)
    if scrips_sold is None:
        scrips_sold = 1 if sell_value > 0 else 0
    c.dp = rate("dp_per_scrip_sell") * scrips_sold
    return c


def intraday(buy_value: float, sell_value: float, *, exchange: str = "NSE") -> Charges:
    txn = rate("nse_txn_equity") if exchange == "NSE" else rate("bse_txn_equity")
    turnover = buy_value + sell_value
    c = Charges()
    c.brokerage = _brokerage_capped(buy_value) + _brokerage_capped(sell_value)
    c.stt = rate("stt_intraday_sell") * sell_value
    c.exchange = txn * turnover
    c.sebi = rate("sebi_fee") * turnover
    c.stamp = rate("stamp_intraday_buy") * buy_value
    c.gst = rate("gst") * (c.brokerage + c.exchange + c.sebi)
    return c


def futures(buy_value: float, sell_value: float) -> Charges:
    turnover = buy_value + sell_value
    c = Charges()
    c.brokerage = _brokerage_capped(buy_value) + _brokerage_capped(sell_value)
    c.stt = rate("stt_futures_sell") * sell_value
    c.exchange = rate("nse_txn_futures") * turnover
    c.sebi = rate("sebi_fee") * turnover
    c.stamp = rate("stamp_futures_buy") * buy_value
    c.gst = rate("gst") * (c.brokerage + c.exchange + c.sebi)
    return c


def options(buy_premium: float, sell_premium: float, orders: int = 2) -> Charges:
    turnover = buy_premium + sell_premium
    c = Charges()
    c.brokerage = 20.0 * orders
    c.stt = rate("stt_options_sell") * sell_premium
    c.exchange = rate("nse_txn_options") * turnover
    c.sebi = rate("sebi_fee") * turnover
    c.stamp = rate("stamp_options_buy") * buy_premium
    c.gst = rate("gst") * (c.brokerage + c.exchange + c.sebi)
    return c


def delivery_side_rates() -> tuple[float, float]:
    """Proportional cost of a delivery BUY and a delivery SELL as fractions of value
    (excludes the fixed DP charge, which backtests add per sell)."""
    common = rate("stt_delivery") + rate("nse_txn_equity") + rate("sebi_fee")
    gst = rate("gst") * (rate("nse_txn_equity") + rate("sebi_fee"))
    return common + gst + rate("stamp_delivery_buy"), common + gst


def delivery_cost_fraction(buy_turnover: float, sell_turnover: float,
                           capital: float = 100_000.0, sells: float = 0.0) -> float:
    """Cost as a fraction of capital for given buy/sell turnover (fractions of capital)."""
    b, s = delivery_side_rates()
    return b * buy_turnover + s * sell_turnover + rate("dp_per_scrip_sell") * sells / capital
