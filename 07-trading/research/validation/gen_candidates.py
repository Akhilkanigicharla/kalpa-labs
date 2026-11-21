"""Regenerate all 27 candidate strategies (unit R) from best_combo_gold for CSCV/PBO trials. Research only."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import best_combo_gold as b
t0 = time.time()
fr = b.frames()
out = []
for k, fn in b.candidates(fr).items():
    t = fn()
    if len(t):
        out.append(t.assign(strategy=k))
pd.concat(out).to_csv(Path(__file__).parent / "candidates_r.csv", index=False)
print("done", len(out), round(time.time() - t0), "s")
