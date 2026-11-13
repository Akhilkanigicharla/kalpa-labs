import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,"/home/claude/akhilkanigicharla/kalpa-labs/07-trading")
import pandas as pd, numpy as np, glob
from src import smc
files=sorted(glob.glob("D_*.parquet"))
real,mom,rows=[],[],[]
rng=np.random.default_rng(1)
for f in files:
    df=pd.read_parquet(f); df.columns=[c.lower() for c in df.columns]; df=df[df.index>="2012-01-01"]
    d=smc._ohlc(df); z=smc.fvg(df)
    t=smc.simulate(df,z); t["date"]=d.index[t.entry_bar.values] if len(t) else []; t["sym"]=f; real.append(t)
    # momentum-matched placebo: bars whose 2-bar move is as strong as the real FVG bars but with NO gap
    c=d.close.values; h=d.high.values; lo=d.low.values
    mv=np.r_[np.nan,np.nan,c[2:]/c[:-2]-1]
    nogap=[i for i in range(30,len(d)-30) if not lo[i]>h[i-2]]
    real_mv=[mv[x.known_at] for x in z]
    pz=[]
    if nogap:
        mvn=np.array([mv[i] for i in nogap]); order=np.argsort(mvn); sorted_mv=mvn[order]
        for x in z:
            k=np.searchsorted(sorted_mv,mv[x.known_at]); k=int(np.clip(k+rng.integers(-20,21),0,len(order)-1))
            j=nogap[order[k]]; base=c[x.known_at]
            pz.append(smc.Zone(j,c[j]*x.top/base,c[j]*x.bottom/base,c[j]*x.stop/base,"mom"))
    m=smc.simulate(df,pz); mom.append(m)
    # buy-and-hold of this stock for comparison per day
    rows.append((f,(c[-1]/c[0])**(252/len(c))-1))
R=pd.concat(real,ignore_index=True); M=pd.concat(mom,ignore_index=True)
print(f"real FVG: {len(R)} trades, avg {R.ret.mean()*100:+.3f}%/trade, win {(R.ret>0).mean():.1%}, avg hold {(R.exit_bar-R.entry_bar+1).mean():.1f} days")
print(f"momentum-matched no-gap twins: {len(M)} trades, avg {M.ret.mean()*100:+.3f}%/trade, win {(M.ret>0).mean():.1%}")
b=[rng.choice(R.ret.values,len(R)).mean()-rng.choice(M.ret.values,len(M)).mean() for _ in range(2000)]
print(f"   real minus momentum twin: {np.mean(b)*100:+.3f}% (95% {np.percentile(b,2.5)*100:+.3f}..{np.percentile(b,97.5)*100:+.3f}%)")
for a,bnd in (("2012","2018-12-31"),("2019","2026-12-31")):
    x=R[(R.date>=a)&(R.date<=bnd)]
    print(f"   {a}-{bnd[:4]}: {len(x)} trades avg {x.ret.mean()*100:+.3f}% win {(x.ret>0).mean():.1%}")
hold_days=(R.exit_bar-R.entry_bar+1).mean()
bh=np.mean([r for _,r in rows])
print(f"per trading day while in a trade: {R.ret.mean()/hold_days*100:+.3f}%  vs buy-and-hold avg stock {( (1+bh)**(1/252)-1)*100:+.3f}% per day ({bh*100:.1f}%/yr)")
print("exit reasons:",R.reason.value_counts(normalize=True).round(2).to_dict())
R.to_parquet("fvg_trades.parquet")
