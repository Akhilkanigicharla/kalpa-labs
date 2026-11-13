"""Kronos out-of-sample test on Nifty daily (Akhil approved running Kronos code, 13 Nov 2026).
Rules fixed before running: data after Kronos' release only (from 1 Aug 2025), lookback 400 days,
predict next close (mean of 10 samples), hold NIFTYBEES only when the prediction is above today's
close, otherwise the liquid ETF (4.7%/yr). Delivery costs on each switch."""
import sys
import time
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/kronos-test/lib")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
import yfinance as yf  # noqa: E402
from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: E402

torch.manual_seed(0)
np.random.seed(0)
tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
mdl = Kronos.from_pretrained("NeoQuasar/Kronos-small")
P = KronosPredictor(mdl, tok, device="cpu", max_context=512)

d = yf.Ticker("^NSEI").history(start="2023-06-01", end="2026-11-14", auto_adjust=True)
d.index = pd.DatetimeIndex(d.index).tz_localize(None)
df = d.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
df["volume"] = df["volume"].replace(0, np.nan).ffill().fillna(1.0)
df["amount"] = df["volume"] * df["close"]
test_days = [i for i, t in enumerate(df.index) if t >= pd.Timestamp("2025-08-01") and i >= 400 and i < len(df) - 1]
print("test days", len(test_days), df.index[test_days[0]].date(), df.index[test_days[-1]].date())

LB, B = 400, 16
preds = {}
t0 = time.time()
for k in range(0, len(test_days), B):
    chunk = test_days[k:k + B]
    xs = [df.iloc[i - LB + 1:i + 1].reset_index(drop=True) for i in chunk]
    xt = [pd.Series(df.index[i - LB + 1:i + 1]) for i in chunk]
    yt = [pd.Series([df.index[i + 1]]) for i in chunk]
    out = P.predict_batch(xs, xt, yt, pred_len=1, T=1.0, top_p=0.9, sample_count=10, verbose=False)
    for i, o in zip(chunk, out):
        preds[i] = float(o["close"].iloc[0])
    if k == 0:
        print(f"first batch {time.time() - t0:.1f}s")
print(f"done in {time.time() - t0:.0f}s")

c = df["close"]
rows = [(df.index[i + 1], preds[i] > c.iloc[i], c.iloc[i + 1] / c.iloc[i] - 1, preds[i] / c.iloc[i] - 1) for i in test_days]
r = pd.DataFrame(rows, columns=["day", "up", "ret", "pred_ret"]).set_index("day")
acc = (r.up == (r.ret > 0)).mean()
base = (r.ret > 0).mean()
cash = 1.047 ** (1 / 252) - 1
switch = r.up.astype(int).diff().abs().fillna(1)
bot = np.where(r.up, r.ret, cash) - switch * 0.0012 / 2
eqb, eqh = (1 + pd.Series(bot, index=r.index)).cumprod(), (1 + r.ret).cumprod()
corr = np.corrcoef(r.pred_ret, r.ret)[0, 1]
print(f"direction accuracy {acc:.1%}; market rose on {base:.1%} of days (= accuracy of always saying 'up')")
print(f"correlation of predicted vs actual next-day move: {corr:+.3f}")
print(f"days long {r.up.mean():.0%}, switches {int(switch.sum())}")
print(f"Kronos daily bot: {(eqb.iloc[-1] - 1) * 100:+.2f}%  worst fall {((eqb / eqb.cummax() - 1).min()) * 100:.1f}%")
print(f"Hold Nifty:       {(eqh.iloc[-1] - 1) * 100:+.2f}%  worst fall {((eqh / eqh.cummax() - 1).min()) * 100:.1f}%")
r.to_csv("daily_preds.csv")
