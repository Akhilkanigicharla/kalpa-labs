import numpy as np
import pandas as pd

from src import smc


def frame(rows):
    idx = pd.bdate_range("2024-01-01", periods=len(rows))
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


def test_fvg_known_only_when_third_candle_closes():
    rows = [(100, 101, 99, 100), (100, 106, 100, 105), (105, 108, 102, 107)] + [(107, 108, 106, 107)] * 5
    z = smc.fvg(frame(rows))
    assert len(z) == 1 and z[0].known_at == 2 and z[0].bottom == 101 and z[0].top == 102


def test_fvg_detection_ignores_the_future():
    rng = np.random.default_rng(0)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.02, 300))
    df = frame([(c[i - 1] if i else c[0], max(c[i], c[i - 1] if i else c[0]) * 1.01,
                 min(c[i], c[i - 1] if i else c[0]) * 0.99, c[i]) for i in range(300)])
    early = [z.known_at for z in smc.fvg(df.iloc[:200])]
    full = [z.known_at for z in smc.fvg(df) if z.known_at < 200]
    assert early == full


def test_order_block_and_fib_zones():
    flat = [(100, 100.5, 99.5, 100)] * 30
    rows = flat + [(100, 100.2, 98.5, 99), (99, 110, 99, 109.5)] + [(109, 110, 108, 109)] * 10
    ob = smc.order_blocks(frame(rows))
    assert ob and ob[0].known_at == 31 and ob[0].bottom == 98.5
    up = [(106 - i, 107 - i, 105 - i, 105.5 - i) for i in range(6)] + [(100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(20)] + [(120 - i, 121 - i, 119 - i, 119.5 - i) for i in range(12)]
    fz = smc.fib(frame(up))
    assert fz and fz[0].bottom < fz[0].top and fz[0].stop < fz[0].bottom


def test_simulate_stop_first_and_costs():
    z = [smc.Zone(0, 100.0, 98.0, 97.0, "x")]
    rows = [(101, 102, 100.5, 101), (100.5, 110, 96, 100)] + [(100, 101, 99, 100)] * 5   # one bar hits stop and target
    t = smc.simulate(frame(rows), z, cost=0.0025)
    assert t.iloc[0].reason == "stop" and t.iloc[0].ret < -0.03


def test_placebo_keeps_shape_and_martingale_can_ruin():
    rng = np.random.default_rng(1)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.01, 400))
    df = frame([(x, x * 1.01, x * 0.99, x) for x in c])
    real = [smc.Zone(100, c[100] * 0.99, c[100] * 0.97, c[100] * 0.96, "x")]
    p = smc.placebo(df, real)[0]
    assert p.known_at != 100 and abs(p.top / c[p.known_at] - 0.99) < 1e-9
    losses = np.array([-0.7] * 6 + [0.1] * 10)       # a losing streak of large losses
    _, ruined = smc.martingale(losses, base_risk=0.1, max_steps=5)
    assert ruined
