"""Crypto (VDA) costs and Indian tax for track B backtests and paper runs (A153 §2).

Tax facts (A153 table, two sources each, 6 Nov 2026): gains on virtual digital assets
are taxed at a flat 30% (+4% health & education cess, surcharge ignored here); only the
cost of acquisition is deductible (exchange fees are NOT); a loss on one trade cannot
be set off against any other gain, even another crypto gain, nor carried forward; 1%
TDS is withheld on every sale (old Act s.194S / s.115BBH, renumbered in the Income-tax
Act 2025: have the CA confirm section numbers). TDS is a CREDIT against the year's tax:
it only moves cash earlier, and any excess comes back as a refund after filing.

The model taxes each sell on its own gain (average-cost basis), and settles tax minus
TDS at each financial-year end (31 March) and at the end of the run. Not tax advice.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# PLACEHOLDER, unverified: fill from the chosen exchange's own fee page before live use.
EXCHANGE_FEE = 0.001      # 0.1% of value per side
GST_ON_FEE = 0.18         # GST on exchange fee (verify on the exchange's fee page)
TDS_RATE = 0.01
TAX_RATE = 0.30
CESS = 0.04


def fee(value: float, rate: float = EXCHANGE_FEE, gst: float = GST_ON_FEE) -> float:
    return abs(value) * rate * (1 + gst)


def tds(sell_value: float, rate: float = TDS_RATE) -> float:
    return sell_value * rate


def trade_tax(gain: float, rate: float = TAX_RATE, cess: float = CESS) -> float:
    """Tax on ONE sell. Losses give zero tax and no set-off against anything."""
    return max(0.0, gain) * rate * (1 + cess)


@dataclass
class TaxBook:
    """Running tax position for one financial year at a time."""
    rate: float = TAX_RATE
    cess: float = CESS
    tax_accrued: float = 0.0      # this FY, not yet settled
    tds_accrued: float = 0.0      # this FY, credit
    tax_paid: float = 0.0         # all time, net of TDS credit already used
    gains: list[float] = field(default_factory=list)

    def on_sell(self, gain: float, tds_amount: float) -> float:
        self.gains.append(gain)
        t = trade_tax(gain, self.rate, self.cess)
        self.tax_accrued += t
        self.tds_accrued += tds_amount
        return t

    def settle(self) -> float:
        """Year-end: returns cash to pay (+) or refund (-) = tax - TDS credit."""
        due = self.tax_accrued - self.tds_accrued
        self.tax_paid += self.tax_accrued
        self.tax_accrued = self.tds_accrued = 0.0
        return due

    @property
    def outstanding(self) -> float:
        return self.tax_accrued - self.tds_accrued


def fy(ts) -> int:
    """Indian financial year label: FY starting 1 April of the returned year."""
    return ts.year if ts.month >= 4 else ts.year - 1


def backtest_after_tax(close: pd.Series, weight: pd.Series, capital: float = 5_000.0, *,
                       fee_rate: float = EXCHANGE_FEE, min_change: float = 0.01,
                       cess: float = CESS) -> dict:
    """Long-only, fractional-unit simulation of a target-weight series on crypto.

    Weight decided at close t trades at close t+1 (no look-ahead). Reports pre-tax and
    after-tax ending capital, fees, TDS withheld and tax paid, plus buy-and-hold on the
    same days with the same costs and tax.
    """
    close = close.astype(float)
    w = weight.reindex(close.index).fillna(0.0).clip(0.0, 1.0).shift(1).fillna(0.0)
    cash, units, basis = float(capital), 0.0, 0.0
    tb, fees, tds_total, trades, cur_w = TaxBook(cess=cess), 0.0, 0.0, 0, 0.0
    cur_fy = fy(close.index[0])
    for ts, px in close.items():
        if fy(ts) != cur_fy:
            cash -= tb.settle()
            cur_fy = fy(ts)
        eq = cash + units * px
        tw = float(w.loc[ts])
        if abs(tw - cur_w) <= min_change:
            continue
        target_units = tw * eq / px
        du = target_units - units
        if du > 0:
            val = du * px
            f = fee(val, fee_rate)
            if val + f > cash:
                val = max(0.0, cash / (1 + fee_rate * (1 + GST_ON_FEE)))
                f, du = fee(val, fee_rate), val / px
            basis = (units * basis + val) / (units + du) if units + du > 0 else 0.0
            units += du
            cash -= val + f
        else:
            sell = min(units, -du)
            val = sell * px
            f, t = fee(val, fee_rate), tds(val)
            tb.on_sell(sell * (px - basis), t)
            cash += val - f - t
            units -= sell
            tds_total += t
            if units <= 1e-12:
                units, basis = 0.0, 0.0
        fees += f
        trades += 1
        cur_w = tw
    last = float(close.iloc[-1])
    pre_tax = cash + units * last + tb.tds_accrued          # TDS is a credit, not a cost
    # liquidate at the end for an after-tax number
    if units > 0:
        val = units * last
        f, t = fee(val, fee_rate), tds(val)
        tb.on_sell(units * (last - basis), t)
        cash += val - f - t
        fees += f
        tds_total += t
    cash -= tb.settle()
    bh = buy_and_hold_after_tax(close, capital, fee_rate=fee_rate, cess=cess)
    return {"capital": capital, "pre_tax_end": round(pre_tax, 2), "after_tax_end": round(cash, 2),
            "after_tax_return": round(cash / capital - 1, 4), "fees": round(fees, 2),
            "tds_withheld": round(tds_total, 2), "tax_paid": round(tb.tax_paid, 2), "trades": trades,
            "losing_sells": sum(1 for g in tb.gains if g < 0),
            "bh_after_tax_end": bh["after_tax_end"], "bh_after_tax_return": bh["after_tax_return"]}


def buy_and_hold_after_tax(close: pd.Series, capital: float = 5_000.0, *,
                           fee_rate: float = EXCHANGE_FEE, cess: float = CESS) -> dict:
    """Buy on the first close, sell on the last, with fee, TDS and 30% tax (+cess)."""
    p0, p1 = float(close.iloc[0]), float(close.iloc[-1])
    buy_val = capital / (1 + fee_rate * (1 + GST_ON_FEE))
    units = buy_val / p0
    sell_val = units * p1
    end = sell_val - fee(sell_val, fee_rate) - trade_tax(sell_val - buy_val, cess=cess)
    return {"after_tax_end": round(end, 2), "after_tax_return": round(end / capital - 1, 4)}
