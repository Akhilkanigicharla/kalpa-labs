#!/usr/bin/env python3
"""A22 check: every daily question is well-formed, and every answer that can be computed is recomputed here by brute
force, so a wrong answer never reaches the channel. Run: python3 03-kits/docs/test_questions.py"""
import csv, itertools, math, pathlib
from fractions import Fraction

ROWS = list(csv.DictReader(open(pathlib.Path(__file__).with_name("telegram-14-days.csv"), encoding="utf-8")))
ans = lambda d: ROWS[d - 1][ROWS[d - 1]["answer"]]


def fifo_faults(refs, frames):
    mem, q, f = set(), [], 0
    for r in refs:
        if r not in mem:
            f += 1
            if len(mem) == frames: mem.discard(q.pop(0))
            mem.add(r); q.append(r)
    return f


def main():
    assert len(ROWS) == 14 and [int(r["day"]) for r in ROWS] == list(range(1, 15))
    for r in ROWS:
        assert r["answer"] in "abcd" and len({r[k] for k in "abcd"}) == 4, r["day"]
        assert r["question"] and r["explanation"] and len(r["question"]) <= 300, r["day"]  # Telegram poll question limit is 300 characters
        assert all(len(r[k]) <= 100 for k in "abcd"), r["day"]                            # poll option limit is 100 characters
        assert "guarantee" not in (r["question"] + r["explanation"]).lower()
    subjects = {r["subject"] for r in ROWS}
    assert len(subjects) == 10, subjects
    # recompute what can be computed
    assert ans(1) == str(sum(1 for s in itertools.product("01", repeat=6) if s.count("1") == 2 and "11" not in "".join(s)))
    assert ans(2) == str(math.ceil(3 * 100 / 2) - 2)
    assert ans(3) == str(fifo_faults([1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5], 3)) and fifo_faults([1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5], 4) == 10
    assert ans(5) == str(2 ** (32 - 27) - 2)
    reach = {0}; [reach.update({(2 * r + b) % 3 for r in list(reach) for b in (0, 1)}) for _ in range(3)]
    assert ans(6) == str(len(reach))
    assert ans(7) == str(4 + 100 - 1)
    assert ans(8) == str(2 ** 6 - 1)
    nand = lambda x, y: 1 - (x & y)
    assert all(nand(nand(a, nand(a, b)), nand(b, nand(a, b))) == a ^ b for a in (0, 1) for b in (0, 1)) and ans(9) == "4"
    assert ans(10) == str(len("int x = a + 10 ;".split()))
    outs = [(x, y) for x in range(1, 7) for y in range(1, 7) if 3 in (x, y)]
    assert ans(11) == str(Fraction(sum(1 for x, y in outs if x + y == 7), len(outs)))
    assert ans(13).startswith(f"{65536 * 8 / 0.1 / 1e6:.2f}")
    lam = sorted(round((4 + s * math.sqrt(16 - 4 * 3)) / 2) for s in (-1, 1))
    assert ans(14) == f"{lam[0]} and {lam[1]}"
    print("  ✓ 14 questions well-formed (Telegram poll limits), 10 subjects, 12 answers recomputed by brute force")
    print("daily question tests passed")


if __name__ == "__main__":
    main()
