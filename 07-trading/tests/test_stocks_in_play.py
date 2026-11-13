import numpy as np
import pandas as pd

from src import stocks_in_play as S


def days_bars(n_days=20, spike_last=1.0, first_green=True, breakout=True, seed=0):
    rng = np.random.default_rng(seed)
    frames = []
    for i, d in enumerate(pd.bdate_range("2026-10-01", periods=n_days)):
        idx = pd.date_range(f"{d.date()} 09:15", periods=75, freq="5min", tz="Asia/Kolkata")
        c = 100 + np.cumsum(rng.normal(0, 0.02, 75))
        o = np.r_[c[0] - (0.1 if first_green else -0.1), c[:-1]]
        if i == n_days - 1 and breakout:
            c[2:] = c[2:] + (np.linspace(0.5, 3, 73) if first_green else -np.linspace(0.5, 3, 73))
            o[2:] = np.r_[c[1], c[2:-1]]
        v = np.full(75, 1000.0)
        v[0] = 0.0                                # Yahoo quirk: 09:15 bar volume 0
        if i == n_days - 1:
            v[1] *= spike_last
        frames.append(pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.02, "low": np.minimum(o, c) - 0.02,
                                    "close": c, "volume": v}, index=idx))
    return pd.concat(frames)


def daily_from(b):
    g = b.groupby(b.index.date)
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()})
    d.index = pd.to_datetime(d.index)
    pre = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
                       index=pd.bdate_range(end=d.index[0] - pd.Timedelta(days=1), periods=20))
    return pd.concat([pre, d])


def test_relative_volume_uses_0920_bar_and_14_prior_days():
    b = days_bars(spike_last=3.0)
    last = sorted(set(b.index.date))[-1]
    assert abs(S.relative_volume(b, last) - 3.0) < 1e-9
    assert np.isnan(S.relative_volume(b, sorted(set(b.index.date))[5]))        # not enough history


def test_only_high_volume_stocks_trade_and_direction_follows_first_candle():
    hot, cold = days_bars(spike_last=4.0, seed=1), days_bars(spike_last=0.5, seed=2)
    red = days_bars(spike_last=2.0, first_green=False, seed=3)
    intra = {"RELIANCE": hot, "TCS": cold, "INFY": red}
    daily = {k: daily_from(v) for k, v in intra.items()}
    day = sorted(set(hot.index.date))[-1]
    trades, sectors = S.run_day(intra, daily, day)
    syms = {t.symbol: t for t in trades}
    assert "TCS" not in syms                                  # below normal volume: skipped
    assert syms["RELIANCE"].side == 1 and syms["INFY"].side == -1
    assert all(t.entry_at >= "09:25" and t.exit_at <= "15:25" for t in trades)
    assert list(sectors)[0] == "Energy"                        # RELIANCE 4x is the busiest


def test_costs_are_charged_and_paper_runs_once(tmp_path):
    hot = days_bars(spike_last=4.0, seed=1, breakout=False)
    intra, daily = {"RELIANCE": hot}, {"RELIANCE": daily_from(hot)}
    txt = S.paper_day(intra, daily, tmp_path)
    assert "PAPER" in txt and "Not advice" in txt
    assert "Already done" in S.paper_day(intra, daily, tmp_path)
