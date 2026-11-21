"""A327: line-by-line Python copy of the MT5 mix engine's last-bar logic (ea/phase5/EA_XAUUSD/Execution/CMixEngine.mqh).
Used by tests/test_mix_port.py to prove the MQL5 port gives the same setups as the research code it came from.
Keep this file and CMixEngine.mqh in step: a change in one must be made in the other."""
import numpy as np
import pandas as pd

def bars(d):
    o,h,l,c = (d[x].values.astype(float) for x in ("open","high","low","close"))
    tr = np.r_[h[0]-l[0], np.maximum(h[1:]-l[1:], np.maximum(abs(h[1:]-c[:-1]), abs(l[1:]-c[:-1])))]
    a = pd.Series(tr).rolling(14).mean().fillna(-1).values
    ee = pd.Series(c).ewm(span=9, adjust=False).mean().values
    return o,h,l,c,a,ee

def levels(o,c,k=2):
    out=[]
    for i in range(1,len(c)):
        ca = np.sign(c[i-1]-o[i-1]); cb = np.sign(c[i]-o[i])
        if ca==1 and cb==-1: kind=-1
        elif ca==-1 and cb==1: kind=1
        else: continue
        p=i-1; lo,hi=p-k,p+k+1
        if lo<0 or hi>len(c): continue
        w=c[lo:hi]
        if (kind==-1 and c[p]<w.max()) or (kind==1 and c[p]>w.min()): continue
        out.append((max(i,p+k), c[p], kind, p))
    return out

def fresh_last(B):
    o,h,l,c,a,ee=B; last=len(c)-1
    if a[last]<0: return None
    for known,price,kind,origin in levels(o,c):
        if known>last: continue
        role = 1 if kind==1 else -1
        fresh_now = (known==last and role==1)
        for t in range(known+1,last+1):
            if role==1:
                if c[t]<price: role=-1
            else:
                if c[t]>price:
                    role=1
                    if t==last: fresh_now=True
        if not fresh_now or c[last]<=price: continue
        if not (c[last]>ee[last] and ee[last]>ee[last-1]): return None
        return (price, price-1.0*a[last])
    return None

def qm_last(B):
    o,h,l,c,a,ee=B; last=len(c)-1; L=levels(o,c)
    for known,price,kind,origin in L:
        if kind!=1: continue
        brk=next((t for t in range(known+1,len(c)) if c[t]<o[t] and c[t]<price),None)
        if brk is None: continue
        mids=[x for x in L if x[2]==-1 and origin<x[3] and x[0]<=brk]
        if not mids: continue
        ap=mids[-1][1]
        up=next((t for t in range(brk+1,len(c)) if c[t]>o[t] and c[t]>ap),None)
        if up!=last or a[up]<0: continue
        head=l[brk:up+1].min()
        if head>=price or c[up]<=price: continue
        if not (c[up]>ee[up] and ee[up]>ee[up-1]): continue
        return (price, head-0.1*a[up])
    return None


def ema9_last(B):
    o,h,l,c,a,ee=B; last=len(c)-1
    L=sorted(levels(o,c), key=lambda x:x[0]); act=[]; j=0
    for t in range(15,last+1):
        while j<len(L) and L[j][0]<t:
            act.append([L[j][1], 1 if L[j][2]==1 else -1, True]); j+=1
        if a[t]<0: continue
        sig=None
        for Lv in act:
            p,role,fresh=Lv
            if role==-1:
                if c[t]>p: Lv[1],Lv[2]=1,True; continue
                if h[t]>=p:
                    if fresh and sig is None and c[t]<ee[t] and ee[t]<ee[t-1]: sig=(-1, max(h[t],p)+0.25*a[t])
                    Lv[2]=False
            else:
                if c[t]<p: Lv[1],Lv[2]=-1,True; continue
                if l[t]<=p:
                    if fresh and sig is None and c[t]>ee[t] and ee[t]>ee[t-1]: sig=(1, min(l[t],p)-0.25*a[t])
                    Lv[2]=False
        if len(act)>400: act=act[-400:]
        if t==last: return sig
    return None
