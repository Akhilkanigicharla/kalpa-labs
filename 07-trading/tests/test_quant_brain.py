"""A280 Quant Brain: 25 intraday agents + master. Synthetic 5-min bars only, no network."""
import numpy as np
import pandas as pd

from src import quant_brain as Q


def _bars(seed, days=15):
    rng = np.random.default_rng(seed)
    idx = []
    for d in pd.bdate_range("2026-08-03", periods=days):
        idx += list(pd.date_range(d + pd.Timedelta("9h15min"), d + pd.Timedelta("15h25min"), freq="5min"))
    idx = pd.DatetimeIndex(idx)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, len(idx))))
    o = np.r_[c[0], c[:-1]]
    hi, lo = np.maximum(o, c) * 1.001, np.minimum(o, c) * 0.999
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c,
                         "volume": rng.integers(1_000, 50_000, len(idx)).astype(float)}, index=idx)


def _world():
    feat = {t: Q.features(_bars(i)) for i, t in enumerate(["NIFTYBEES", "AAA", "BBB", "CCC"])}
    return feat, Q.market_context(feat)


def _trades(n_per_day=40, days=12, net=10.0):
    ds = list(pd.bdate_range("2026-08-03", periods=days).date)
    rows = []
    for d in ds:
        for k in range(n_per_day):
            t = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=20 + k)
            rows.append({"agent": Q.AGENTS[k % 3].name, "day": d, "t_in": t, "sym": "AAA", "side": 1,
                         "qty": 100, "buy": 100.0, "sell": 100.0 + net / 100, "gross": net, "charges": 0.0,
                         "net": net})
    return pd.DataFrame(rows), ds


def test_25_unique_agents():
    assert len(Q.AGENTS) == 25 and len({a.name for a in Q.AGENTS}) == 25


def test_agents_trade_with_charges_and_close_same_day():
    feat, m = _world()
    tr = Q.all_trades(feat, m)
    assert len(tr) > 0
    assert (tr.charges > 0).all()
    assert (pd.to_datetime(tr.t_in).dt.date == tr.day).all()      # never held overnight
    assert (pd.to_datetime(tr.t_out).dt.time <= pd.Timestamp("15:25").time()).all()


def test_allocation_uses_only_past_days():
    tr, ds = _trades()
    day = ds[Q.SCORE_DAYS]
    w1 = Q.allocation(tr, ds, day)
    future = tr.copy()
    future.loc[future.day >= day, "net"] = -1e6                       # wreck today and later
    w2 = Q.allocation(future, ds, day)
    pd.testing.assert_series_equal(w1, w2)
    assert (w1 <= Q.CAP_AGENT + 1e-12).all() and w1.sum() <= 1 + 1e-12


def test_no_money_for_losers_and_warmup():
    tr, ds = _trades(net=-10.0)
    assert Q.allocation(tr, ds, ds[Q.SCORE_DAYS]).empty
    tr2, ds2 = _trades()
    assert Q.allocation(tr2, ds2, ds2[Q.SCORE_DAYS - 1]).empty          # not enough history yet


def test_master_respects_25_trade_limit_and_day_loss_cap():
    tr, ds = _trades(n_per_day=40)
    day = ds[Q.SCORE_DAYS]
    w = Q.allocation(tr, ds, day)
    assert len(Q.master_day(tr, w, day)) <= Q.MAX_TRADES_DAY
    bad = tr.copy()
    bad.loc[bad.day == day, "sell"] = 90.0                           # every trade today loses
    md = Q.master_day(bad, w, day)
    assert md.net.sum() > Q.DAY_LOSS_CAP - 2_000                      # stops soon after the cap
    assert len(md) < Q.MAX_TRADES_DAY
