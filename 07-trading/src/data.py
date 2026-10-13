"""Daily bars with a local Parquet cache and validation. Q7.2.

Data never goes in git (07-trading/data/ is git-ignored). Tests use synthetic
data only (`synthetic_prices`). Live fetching uses yfinance (Apache-2.0) with
NSE symbols ending in `.NS`; an optional fallback fetcher can be passed in.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
COLUMNS = ["open", "high", "low", "close", "volume"]

Fetcher = Callable[[str, str | None, str | None], pd.DataFrame]


class DataError(ValueError):
    pass


def nse_symbol(symbol: str) -> str:
    """'TCS' -> 'TCS.NS'; indices (^NSEI) and already-suffixed symbols are kept."""
    s = symbol.strip().upper()
    return s if s.startswith("^") or "." in s else f"{s}.NS"


def _yf_fetch(symbol: str, start: str | None, end: str | None) -> pd.DataFrame:
    import yfinance as yf  # imported lazily so tests need no network
    df = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=True, actions=False)
    return df


def normalise(df: pd.DataFrame) -> pd.DataFrame:
    out = df.rename(columns=str.lower).copy()
    missing = [c for c in COLUMNS if c not in out.columns]
    if "volume" in missing:
        out["volume"] = 0.0
        missing.remove("volume")
    if missing:
        raise DataError(f"missing columns: {missing}")
    out = out[COLUMNS]
    idx = pd.DatetimeIndex(out.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    out.index = idx.normalize()
    out.index.name = "date"
    return out.astype(float)


def validate(df: pd.DataFrame, *, max_gap_days: int = 7, jump: float = 0.40) -> list[str]:
    """Return a list of problems (empty list = clean).

    - NaNs, duplicate or unsorted dates
    - prices <= 0, high < low, close outside [low, high]
    - gaps longer than `max_gap_days` calendar days. Real NSE closures can reach 6
      days (1 Oct -> 7 Oct 2014: Gandhi Jayanti + Dussehra + weekend + Bakri Id), so
      7 is the default; anything longer means missing data.
    - one-day moves larger than `jump` (unadjusted split/bonus). NSE circuit limits
      cap most stocks at 20%, so 40% almost always means a corporate action.
    """
    problems: list[str] = []
    if df.empty:
        return ["empty frame"]
    if df[COLUMNS[:4]].isna().any().any():
        problems.append(f"NaN prices: {int(df[COLUMNS[:4]].isna().sum().sum())}")
    if df.index.has_duplicates:
        problems.append(f"duplicate dates: {int(df.index.duplicated().sum())}")
    if not df.index.is_monotonic_increasing:
        problems.append("dates not sorted")
    if (df[COLUMNS[:4]] <= 0).any().any():
        problems.append("price <= 0")
    if (df["high"] < df["low"]).any():
        problems.append("high < low")
    bad_close = (df["close"] > df["high"] * 1.0001) | (df["close"] < df["low"] * 0.9999)
    if bad_close.any():
        problems.append(f"close outside high/low: {int(bad_close.sum())}")
    gaps = df.index.to_series().diff().dt.days.dropna()
    if (gaps > max_gap_days).any():
        first = gaps[gaps > max_gap_days].index[0].date()
        problems.append(f"gap > {max_gap_days} days: {int((gaps > max_gap_days).sum())} (first {first})")
    rets = df["close"].pct_change().abs().dropna()
    if (rets > jump).any():
        first = rets[rets > jump].index[0].date()
        problems.append(f"jump > {jump:.0%}: {int((rets > jump).sum())} (first {first}); split not adjusted?")
    return problems


def get_daily(symbol: str, start: str | None = None, end: str | None = None, *,
              cache_dir: Path | str | None = None, fetcher: Fetcher | None = None,
              fallback: Fetcher | None = None, refresh: bool = False,
              strict: bool = True) -> pd.DataFrame:
    """Daily OHLCV for an NSE symbol, cached as Parquet.

    Raises DataError when validation finds problems and `strict` is True.
    """
    sym = nse_symbol(symbol)
    cache = Path(cache_dir) if cache_dir else DATA_DIR
    path = cache / f"{sym.replace('^', 'IDX_')}.parquet"
    df: pd.DataFrame | None = None
    if path.exists() and not refresh:
        df = pd.read_parquet(path)
    else:
        last_err: Exception | None = None
        for fn in [f for f in (fetcher or _yf_fetch, fallback) if f is not None]:
            try:
                raw = fn(sym, start, end)
                if raw is not None and len(raw):
                    df = normalise(raw)
                    break
            except Exception as e:  # network, symbol, schema
                last_err = e
        if df is None:
            raise DataError(f"no data for {sym}: {last_err}")
        cache.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)
    if start:
        df = df[df.index >= pd.Timestamp(start)]
    if end:
        df = df[df.index < pd.Timestamp(end)]
    problems = validate(df)
    if problems and strict:
        raise DataError(f"{sym}: " + "; ".join(problems))
    return df


def synthetic_prices(n: int = 2520, *, seed: int = 0, mu: float = 0.08, sigma: float = 0.18,
                     start: str = "2006-01-02", regime_days: int = 0,
                     regime_drift: float = 0.0, start_price: float = 100.0) -> pd.DataFrame:
    """Synthetic daily OHLCV on business days (no real market data).

    `regime_days` > 0 adds persistent random up/down drift regimes of that average
    length with annual drift +/- `regime_drift`. That plants a trend a time-series
    momentum rule can find (a positive control); with regime_days=0 the series is a
    pure random walk where no rule should pass (negative control).
    """
    rng = np.random.default_rng(seed)
    dt = 1 / 252
    drift = np.full(n, mu)
    if regime_days > 0:
        state, i = 1.0, 0
        while i < n:
            length = max(20, int(rng.exponential(regime_days)))
            drift[i:i + length] += state * regime_drift
            state, i = -state, i + length
    rets = (drift - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * rng.standard_normal(n)
    close = start_price * np.exp(np.cumsum(rets))
    open_ = np.r_[start_price, close[:-1]] * np.exp(0.002 * rng.standard_normal(n))
    hi = np.maximum(open_, close) * (1 + np.abs(0.005 * rng.standard_normal(n)))
    lo = np.minimum(open_, close) * (1 - np.abs(0.005 * rng.standard_normal(n)))
    idx = pd.bdate_range(start, periods=n, name="date")
    vol = rng.integers(100_000, 1_000_000, n).astype(float)
    return pd.DataFrame({"open": open_, "high": hi, "low": lo, "close": close, "volume": vol}, index=idx)
