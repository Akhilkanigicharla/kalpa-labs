"""A321: Akhil's $3,100 bias and the take-every-setup switch."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import ea_multitf_gold as mt  # noqa: E402
import ea_design_gold as e  # noqa: E402


def test_bias_shorts_above_longs_below():
    s = [dict(side=-1, trig=3500.0), dict(side=1, trig=3500.0), dict(side=1, trig=3050.0), dict(side=-1, trig=3050.0)]
    kept = mt.bias3100(s)
    assert [(k["side"], k["trig"]) for k in kept] == [(-1, 3500.0), (1, 3050.0)]


def test_every_flag_resets_and_defaults_off():
    assert e.EVERY is False
