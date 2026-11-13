import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,"/home/claude/akhilkanigicharla/kalpa-labs/07-trading")
import pandas as pd, numpy as np, glob
from src import smc
files=sorted(glob.glob("D_*.parquet"))
res={k:[] for k in ("fvg","ob","fib")}; plc={k:[] for k in res}
for f in files:
    df=pd.read_parquet(f); df.columns=[c.lower() for c in df.columns]
    df=df[df.index>="2012-01-01"]
    for kind,fn in (("fvg",smc.fvg),("ob",smc.order_blocks),("fib",smc.fib)):
        z=fn(df)
        res[kind].append(smc.simulate(df,z))
        for s in range(3):
            plc[kind].append(smc.simulate(df,smc.placebo(df,z,seed=s)))
print(f"{len(files)} series (51 NSE stocks + Nifty), daily 2012-2026, long only, 0.25% round-trip cost, 2R target")
print(f"{'pattern':14} {'trades':>7} {'win':>6} {'avg/trade':>10} {'avg R':>7} {'profit f':>9}")
allr={}
for k in res:
    a=pd.concat(res[k],ignore_index=True); p=pd.concat(plc[k],ignore_index=True)
    sa,sp=smc.summarize(a),smc.summarize(p)
    allr[k]=a
    for lab,s in ((k,sa),(k+" placebo",sp)):
        print(f"{lab:14} {s['trades']:7} {s['win']:6.1%} {s['avg_ret']*100:+9.3f}% {s['avg_r']:+7.3f} {s['pf']:9.2f}")
    # difference test: bootstrap of mean ret real - placebo
    rng=np.random.default_rng(0); d=[]
    for _ in range(2000):
        d.append(rng.choice(a.ret.values,len(a)).mean()-rng.choice(p.ret.values,len(p)).mean())
    d=np.array(d); print(f"   real minus placebo per trade: {np.mean(d)*100:+.3f}% (95% range {np.percentile(d,2.5)*100:+.3f}% .. {np.percentile(d,97.5)*100:+.3f}%)")
pd.concat(allr.values()).to_parquet("smc_trades.parquet")
