"""A321/A322: take-every-setup switch; the $3,100 rule is removed."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research"))
import ea_multitf_gold as mt  # noqa: E402
import ea_design_gold as e  # noqa: E402


def test_no_3100_rule():
    assert not hasattr(mt, "bias3100") and not hasattr(mt, "LEVEL")


def test_every_flag_resets_and_defaults_off():
    assert e.EVERY is False
