"""A290: point-in-time Nifty 100 / 200 membership (parser, name mapping, walk back, and the committed files)."""
import csv
from datetime import date
from pathlib import Path

import pytest

from src import index_membership as im

NEW = """PRESS RELEASE
      These changes shall become effective from September 30, 2026 (close of September 29, 2026).
      A. Replacements on account of semi-annual review of broad market indices:
      1) Nifty 50
      The following company is being excluded:
        Sr. No.                         Company Name                                  Symbol
          1     Wipro Ltd.                                                         WIPRO
      The following company is being included:
        Sr. No.                         Company Name                                     Symbol
          1     BSE Ltd.                                                           BSE
      Note:
      1. BSE Ltd. (average free-float market capitalization Rs. 1,40,879 crores) has been included in Nifty 50 index
3) Nifty 100
The following companies are being excluded:
  Sr. No.                     Company Name              Symbol
    1     Oldco Ltd.                                OLDCO
The following companies are being included:
  Sr. No.                     Company Name              Symbol
    1     SRF Ltd.                                  SRF
The above replacements will also be applicable to Nifty100 Equal Weight index.
4) Nifty 100 Low Volatility 30
The following company is being included:
  Sr. No.                     Company Name              Symbol
    1     Notme Ltd.                                NOTME
"""

OLD = """The Index Maintenance Sub-Committee has decided to make the following changes in
various indices during its periodic review. These changes shall become effective from
March 25, 2011.
(1)    S&P CNX Nifty Index
The following company is being excluded:
  Sr. No. Company Name
    1     Suzlon Energy Ltd.
The following company is being included:
  Sr. No. Company Name
    1     Grasim Industries Ltd.
(2)    CNX Nifty Junior Index
The following companies are being excluded:
  Sr. No.   Company Name
    1       Corporation Bank
    2       Grasim Industries Ltd.
The following companies are being included:
  Sr. No.   Company Name
     1      Titan Industries Ltd.
"""


def ev(text, src="x"):
    return {(e.index, e.action, e.symbol or e.name) for e in im.parse_release(text, src)}


def test_new_layout_with_symbols_notes_and_lookalike_index():
    e = ev(NEW)
    assert ("N50", "out", "WIPRO") in e and ("N50", "in", "BSE") in e
    assert ("N100", "out", "OLDCO") in e and ("N100", "in", "SRF") in e      # 'SRF Ltd.' is not a 'Sr. No.' header
    assert not any(x[2] == "NOTME" for x in e)                                 # Nifty 100 Low Volatility 30 ignored
    assert len(e) == 4                                                         # the numbered note is not a row
    assert im.parse_release(NEW, "x")[0].eff == date(2026, 9, 30)


def test_old_layout_names_only():
    e = ev(OLD)
    assert e == {("N50", "out", "Suzlon Energy Ltd."), ("N50", "in", "Grasim Industries Ltd."),
                 ("NN50", "out", "Corporation Bank"), ("NN50", "out", "Grasim Industries Ltd."),
                 ("NN50", "in", "Titan Industries Ltd.")}


def test_dot_heading_inverted_table_and_ocr():
    dot = "effective from November 28, 2014\n2. CNX 100 index:\nThe following company is being excluded:\n" \
          "    1      Ranbaxy Laboratories Ltd.                 RANBAXY\n"
    assert ev(dot) == {("N100", "out", "RANBAXY")}
    inv = ("These changes shall become effective from August 30, 2024 (close of August 29, 2024).\n"
           "Tata Motors Ltd., 'A' Ordinary Shares -\nDVR (Symbol: TATAMTRDVR) shall be excluded from the following indices:\n"
           "   Sr. No.                          Index Name\n      1      Nifty 100\n      2      Nifty 200\n"
           "      3      Nifty Auto\n\nB. Something else\n")
    assert ev(inv) == {("N100", "out", "TATAMTRDVR"), ("N200", "out", "TATAMTRDVR")}
    ocr = (im.OCR_MARK + "\neffective from September 30, 2021\n3) NIFTY 100\nThe following companies are being excluded:\n"
           "| Sr. No. | Company Name Symbol\nMRF Ltd.\n| 4 _| Petronet LNG Ltd. PETRONET\n"
           "The following companies are being included:\nBank of Baroda BANKBARODA\n")
    assert ev(ocr) == {("N100", "out", "MRF Ltd."), ("N100", "out", "PETRONET"), ("N100", "in", "BANKBARODA")}


def test_resolver_names_and_symbol_changes():
    rs = im.Resolver([("Titan Company Ltd.", "TITAN"), ("LTIMindtree Ltd.", "LTIM")],
                     [("LTI", "LTIM", date(2022, 12, 5)), ("LTIM", "LTM", date(2026, 2, 27))])
    assert rs.resolve("", "LTI") == "LTM"                       # chain of symbol changes ends at today's symbol
    assert rs.resolve("Titan Industries Ltd.", "") == "TITAN"   # loose name key (industries / company dropped)
    assert rs.resolve("Patni Computer Systems Ltd.", "").startswith("NAME:")


def test_n100_derived_from_n50_and_next50_and_walk_back():
    evs = im.parse_release(OLD, "old")
    rs = im.Resolver([("Titan Company Ltd.", "TITAN"), ("Grasim Industries Ltd.", "GRASIM"),
                      ("Suzlon Energy Ltd.", "SUZLON"), ("Corporation Bank", "CORPBANK")], [])
    ch = im.net_changes(evs, lambda e: rs.resolve(e.name, e.symbol))
    n100 = ch[(date(2011, 3, 25), "N100")]
    assert n100 == {"in": {"TITAN"}, "out": {"SUZLON", "CORPBANK"}}          # Grasim moved inside the 100: no change
    today = {"TITAN", "GRASIM", "X"}
    mem, notes = im.walk_back(today, ch, "N100", date(2011, 12, 31), im.month_ends(date(2011, 1, 1), date(2011, 4, 30)))
    assert mem[date(2011, 4, 30)] == today
    assert mem[date(2011, 3, 31)] == today and mem[date(2011, 2, 28)] == {"GRASIM", "X", "SUZLON", "CORPBANK"}
    assert notes == []
    _, notes = im.walk_back({"GRASIM"}, ch, "N100", date(2011, 12, 31), [date(2011, 1, 31)])
    assert notes == ["2011-03-25 N100 undo-in TITAN: not a member"]


def test_month_ends():
    assert im.month_ends(date(2011, 1, 1), date(2011, 3, 15)) == [date(2011, 1, 31), date(2011, 2, 28)]


OUT = Path(__file__).resolve().parents[1] / "research" / "index_membership"


@pytest.mark.parametrize("ix,n", [("n50", 50), ("n100", 100), ("n200", 200)])
def test_committed_membership_covers_2011_to_2026_month_by_month(ix, n):
    rows = list(csv.DictReader(open(OUT / f"{ix}_monthly.csv")))
    months = [r["month_end"][:7] for r in rows]
    assert months[0] == "2011-01" and months[-1] >= "2026-10" and len(months) == len(set(months))
    assert all(abs(int(r["count"]) - n) <= 1 for r in rows)                   # 101 only while Tata Motors DVR was in
    assert all(len(r["members"].split()) == int(r["count"]) for r in rows)
    assert (OUT / f"{ix}_anomalies.txt").read_text().strip() == ""
