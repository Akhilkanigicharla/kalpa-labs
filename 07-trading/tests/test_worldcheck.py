import json
from datetime import date

import numpy as np
import pandas as pd

from src import worldcheck as W

RSS = """﻿<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>
<item><title><![CDATA[RBI to conduct VRRR auction]]></title></item>
<item><title>Second</title></item><item><title>Third</title></item><item><title>Fourth</title></item>
</channel></rss>"""


def series(n=400, start=100.0, drift=0.0, seed=0, end="2026-11-13"):
    idx = pd.bdate_range(end=end, periods=n)
    r = np.random.default_rng(seed).normal(drift, 0.01, n)
    return pd.Series(start * np.cumprod(1 + r), index=idx)


def test_flags_fire_on_the_pre_registered_rules():
    falling = series(drift=-0.002)                    # S&P well below its 200-day average
    calm_vix = pd.Series(15.0, index=falling.index)
    calm_vix.iloc[-1] = 30.0                          # fear spike
    y = pd.Series(np.linspace(4.0, 5.2, 400), index=falling.index)      # +0.2 pt per ~63 bars... make it big:
    y.iloc[-64:] = np.linspace(4.5, 5.2, 64)
    fx = pd.Series(np.linspace(85, 90, 400), index=falling.index)
    fx.iloc[-64:] = np.linspace(88, 92, 64)
    oil = pd.Series(60.0, index=falling.index)
    oil.iloc[-64:] = np.linspace(60, 85, 64)
    f = W.flags_from({"S&P 500": falling, "India VIX": calm_vix, "US 10Y yield": y, "USD/INR": fx, "Brent oil": oil})
    assert f["Global trend"][0] and f["Fear"][0] and f["Dollar squeeze"][0] and f["Oil shock"][0]
    calm = W.flags_from({"S&P 500": series(drift=0.002), "India VIX": pd.Series(15.0, index=falling.index),
                         "US 10Y yield": pd.Series(4.0, index=falling.index),
                         "USD/INR": pd.Series(85.0, index=falling.index), "Brent oil": oil.iloc[:-64]})
    assert not any(v for v, _ in calm.values())


def test_rss_and_events_and_report_never_crash(tmp_path):
    assert W.parse_rss(RSS) == ["RBI to conduct VRRR auction", "Second", "Third"]
    ev = tmp_path / "e.json"
    ev.write_text(json.dumps({"events": [{"date": "2026-12-04", "name": "RBI"}, {"date": "2027-02-05", "name": "late"},
                                         {"date": "2026-11-01", "name": "past"}]}), encoding="utf-8")

    def fetch(t):
        if t == "^HSI":
            raise ConnectionError("down")
        return series(seed=hash(t) % 100)

    rep = W.build(date(2026, 11, 25), fetch=fetch, get=lambda url: RSS, events_file=ev)
    txt = rep.text()
    assert [e["name"] for e in rep.events] == ["RBI"]
    assert "Hang Seng (ConnectionError)" in txt and "alerts only" in txt and "Not investment advice" in txt
    assert "Latest Fed news" in txt and "Nifty 50" in txt and "Risk flags on:" in txt
    bad = W.build(date(2026, 11, 25), fetch=lambda t: (_ for _ in ()).throw(OSError()), get=lambda u: "<bad",
                  events_file=tmp_path / "missing.json")
    assert "Could not load" in bad.text()


def test_real_events_file_has_two_sources_each():
    data = json.loads(W.EVENTS_FILE.read_text(encoding="utf-8"))
    for e in data["events"]:
        date.fromisoformat(e["date"])
        assert len(e["sources"]) >= 2
