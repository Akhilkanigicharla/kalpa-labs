//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — A327 strategy mix engine                |
//| File: Execution/CMixEngine.mqh                                    |
//|                                                                    |
//| Runs the 12 extra strategies of the A323 "best gold mix" next to  |
//| the EA's own EA+MSNR H1 strategy (research/best_combo_gold.py):   |
//|   MSNR fresh_v long H1/H2/H4, fresh_v short H2/H4,                |
//|   MSNR QM long H1/H2/H4, QM short H1/H4,                          |
//|   EMA9 + fresh MSNR rejection (both sides) H2/H4.                  |
//| Port rules (python file -> here):                                 |
//|   src/msnr.py levels/track/fresh_v/qm, research/msnr_gold_robust  |
//|   .filt (9 EMA filter), src/smc.simulate (limit at the level,     |
//|   wait/hold bars, 2R), research/gold_ema9_msnr.setups/run.        |
//|   Shorts = the long logic on the mirrored chart (1/price), exactly|
//|   as in research; prices are converted back with 1/x.             |
//| Each new closed bar of a strategy's timeframe: recompute setups   |
//| from the last inp_MixBars closed bars (same batch logic as python)|
//| and act only on a setup known at the LAST closed bar.             |
//| Risk: inp_MixRiskPct of equity per trade, x1.5 after that         |
//| strategy's last trade won, x0.75 after a loss (A325); total open  |
//| risk cap; no entries during the news blackout (A325); pending     |
//| orders cancelled when a blackout starts.                          |
//| Not compiled here (no MetaEditor in the build cloud).             |
//+------------------------------------------------------------------+
#ifndef CMIXENGINE_MQH
#define CMIXENGINE_MQH
#include "../Include/Defines.mqh"
#include <Trade/Trade.mqh>

input group    "=== A327 STRATEGY MIX ==="
input bool     inp_MixEnabled        = true;   // Trade the 12 extra mix strategies
input double   inp_MixRiskPct        = 0.40;   // % of equity risked per mix trade x strategy weight (A336 quant re-test scenario G)
input double   inp_MixMaxOpenRiskPct = 2.0;    // Max total risk of open mix trades + pendings (% equity). A335: 2% keeps a 3.7x gap (worst seen) at 7.4%, inside the 10% limit
input double   inp_MixSpikeAtr       = 3.0;    // A335: skip new entries if the last closed M15 bar was wider than this x ATR(M15)
input int      inp_MixBars           = 3000;   // Closed bars used to rebuild setups (port check: exact match from 2,000)
input double   inp_MixMaxLot         = 0.10;   // A336 (#3/#4): hard lot cap per mix order
input double   inp_MinStopUsd        = 1.50;   // A336 (#4): minimum stop distance for a mix order (price units, $ on XAUUSD)
input group    "=== A336 MIX STRATEGY WEIGHTS (risk x weight; 0 = off; quant re-test scenario G) ==="
input double   inp_W_FreshLongH1     = 1.0;    // MSNR fresh_v long H1
input double   inp_W_QmLongH1        = 0.5;    // MSNR qm long H1
input double   inp_W_QmShortH1       = 0.5;    // MSNR qm short H1
input double   inp_W_Ema9H2          = 0.0;    // EMA9 H2 (off)
input double   inp_W_FreshLongH2     = 1.0;    // MSNR fresh_v long H2
input double   inp_W_FreshShortH2    = 1.0;    // MSNR fresh_v short H2
input double   inp_W_QmLongH2        = 0.0;    // MSNR qm long H2 (off)
input double   inp_W_Ema9H4          = 0.0;    // EMA9 H4 (off)
input double   inp_W_FreshLongH4     = 0.5;    // MSNR fresh_v long H4
input double   inp_W_FreshShortH4    = 0.0;    // MSNR fresh_v short H4 (off)
input double   inp_W_QmLongH4        = 0.5;    // MSNR qm long H4
input double   inp_W_QmShortH4       = 0.0;    // MSNR qm short H4 (off)

#define MIX_N 12
#define MIX_FRESH 0
#define MIX_QM    1
#define MIX_EMA9  2

struct MixStrat
{
   string          name;
   ENUM_TIMEFRAMES tf;
   int             kind;
   int             side;      // +1 long, -1 short, 0 both (EMA9)
   int             wait;      // bars a limit order may wait
   int             hold;      // bars a trade may run
   datetime        last_bar;  // open time of the last processed closed bar
   double          last_r;    // R of this strategy's last closed trade (streak sizing)
   double          weight;    // A336: risk weight (0 = strategy off)
};

struct MixLv { int known; double price; int kind; int origin; };   // kind +1 V (support), -1 A (resistance)

struct MixBars
{
   double o[]; double h[]; double l[]; double c[]; double a[]; double e[];
   int    n;
};

class CMixEngine
{
private:
   MixStrat m_s[MIX_N];
   CTrade   m_trade;
   int      m_atr15;            // A335 spike check
   bool     m_ready;
   datetime m_last_news_check;
   //--- A336 gate cache (#5/#16) and per-ticket retry throttle (#25)
   datetime m_gate_time;
   bool     m_gate_ok;
   string   m_gate_why;
   string   m_gate_logged;
   ulong    m_thr_tk[32];
   datetime m_thr_t[32];
   int      m_thr_i;

   long Magic(int i) const { return Config.MagicNumber + MIX_MAGIC_OFFSET + i; }

   void Def(int i, string nm, ENUM_TIMEFRAMES tf, int kind, int side, int wait, int hold, double weight)
   {
      m_s[i].name = nm; m_s[i].tf = tf; m_s[i].kind = kind; m_s[i].side = side;
      m_s[i].wait = wait; m_s[i].hold = hold; m_s[i].last_bar = 0; m_s[i].last_r = 0.0;
      m_s[i].weight = MathMax(0.0, weight);
   }

   //--- closed bars oldest-first; mirror = 1/price (high<->low swap); ATR(14) simple mean; EMA9 span 9
   bool Load(ENUM_TIMEFRAMES tf, bool mirror, MixBars &b)
   {
      MqlRates r[];
      ArraySetAsSeries(r, false);
      int n = CopyRates(EA_SYMBOL, tf, 1, inp_MixBars, r);
      if(n < 60) return false;
      b.n = n;
      ArrayResize(b.o, n); ArrayResize(b.h, n); ArrayResize(b.l, n);
      ArrayResize(b.c, n); ArrayResize(b.a, n); ArrayResize(b.e, n);
      for(int i = 0; i < n; i++)
      {
         if(r[i].low <= 0) return false;
         if(!mirror) { b.o[i] = r[i].open; b.h[i] = r[i].high; b.l[i] = r[i].low; b.c[i] = r[i].close; }
         else        { b.o[i] = 1.0 / r[i].open; b.h[i] = 1.0 / r[i].low; b.l[i] = 1.0 / r[i].high; b.c[i] = 1.0 / r[i].close; }
      }
      double tr[]; ArrayResize(tr, n);
      for(int i = 0; i < n; i++)
      {
         double hl = b.h[i] - b.l[i];
         tr[i] = (i == 0) ? hl : MathMax(hl, MathMax(MathAbs(b.h[i] - b.c[i - 1]), MathAbs(b.l[i] - b.c[i - 1])));
      }
      double sum = 0.0;
      for(int i = 0; i < n; i++)
      {
         sum += tr[i];
         if(i >= 14) sum -= tr[i - 14];
         b.a[i] = (i >= 13) ? sum / 14.0 : -1.0;               // -1 = not available (python NaN)
      }
      // python: row 0's TR = high-low (pandas max skips the missing previous close), first ATR at i = 13
      double al = 2.0 / 10.0;
      b.e[0] = b.c[0];
      for(int i = 1; i < n; i++) b.e[i] = al * b.c[i] + (1.0 - al) * b.e[i - 1];
      return true;
   }

   //--- python src/msnr.levels(d, k=2)
   int Levels(const MixBars &b, MixLv &lv[], int k = 2)
   {
      ArrayResize(lv, 0);
      int m = 0;
      for(int i = 1; i < b.n; i++)
      {
         int ca = (b.c[i - 1] > b.o[i - 1]) ? 1 : (b.c[i - 1] < b.o[i - 1] ? -1 : 0);
         int cb = (b.c[i] > b.o[i]) ? 1 : (b.c[i] < b.o[i] ? -1 : 0);
         int kind = 0;
         if(ca == 1 && cb == -1) kind = -1;
         else if(ca == -1 && cb == 1) kind = 1;
         else continue;
         int p = i - 1, known = i;
         int lo = p - k, hi = p + k + 1;
         if(lo < 0 || hi > b.n) continue;
         bool key = true;
         for(int j = lo; j < hi && key; j++)
            if((kind == -1 && b.c[j] > b.c[p]) || (kind == 1 && b.c[j] < b.c[p])) key = false;
         if(!key) continue;
         known = MathMax(i, p + k);
         ArrayResize(lv, m + 1);
         lv[m].known = known; lv[m].price = b.c[p]; lv[m].kind = kind; lv[m].origin = p;
         m++;
      }
      return m;
   }

   bool EmaOk(const MixBars &b, int t) const { return t >= 1 && b.c[t] > b.e[t] && b.e[t] > b.e[t - 1]; }

   //--- fresh_v zone known at the last bar (first one in python order). Returns false if none.
   bool FreshZone(const MixBars &b, double &top, double &stop)
   {
      MixLv lv[];
      int m = Levels(b, lv);
      int last = b.n - 1;
      if(b.a[last] < 0) return false;
      for(int q = 0; q < m; q++)
      {
         if(lv[q].known > last) continue;
         int role = (lv[q].kind == 1) ? 1 : -1;
         bool fresh_now = (lv[q].known == last && role == 1);
         for(int t = lv[q].known + 1; t <= last; t++)
         {
            if(role == 1) { if(b.c[t] < lv[q].price) role = -1; }
            else          { if(b.c[t] > lv[q].price) { role = 1; if(t == last) fresh_now = true; } }
         }
         if(!fresh_now || b.c[last] <= lv[q].price) continue;
         if(!EmaOk(b, last)) return false;                     // filter applies to the zone's bar
         top  = lv[q].price;
         stop = lv[q].price - 1.0 * b.a[last];
         return true;
      }
      return false;
   }

   //--- qm zone known at the last bar
   bool QmZone(const MixBars &b, double &top, double &stop)
   {
      MixLv lv[];
      int m = Levels(b, lv);
      int last = b.n - 1;
      for(int q = 0; q < m; q++)
      {
         if(lv[q].kind != 1) continue;
         int brk = -1;
         for(int t = lv[q].known + 1; t < b.n; t++)
            if(b.c[t] < b.o[t] && b.c[t] < lv[q].price) { brk = t; break; }
         if(brk < 0) continue;
         int mid = -1;
         for(int r = 0; r < m; r++)
            if(lv[r].kind == -1 && lv[q].origin < lv[r].origin && lv[r].known <= brk) mid = r;
         if(mid < 0) continue;
         int up = -1;
         for(int t = brk + 1; t < b.n; t++)
            if(b.c[t] > b.o[t] && b.c[t] > lv[mid].price) { up = t; break; }
         if(up != last || b.a[up] < 0) continue;
         double head = b.l[brk];
         for(int t = brk; t <= up; t++) head = MathMin(head, b.l[t]);
         if(head >= lv[q].price || b.c[up] <= lv[q].price) continue;
         if(!EmaOk(b, up)) continue;
         top  = lv[q].price;
         stop = head - 0.1 * b.a[up];
         return true;
      }
      return false;
   }

   //--- research/gold_ema9_msnr.setups: signal at the last bar (side, stop). Real prices, both sides.
   bool Ema9Signal(const MixBars &b, int &side, double &stop)
   {
      MixLv lv[];
      int m = Levels(b, lv);
      double ap[]; int ar[]; bool af[];
      int na = 0, j = 0;
      int last = b.n - 1;
      // levels sorted by known (python sorts); Levels() emits by pair index, so sort
      for(int x = 1; x < m; x++)
      {
         MixLv key = lv[x]; int y = x - 1;
         while(y >= 0 && lv[y].known > key.known) { lv[y + 1] = lv[y]; y--; }
         lv[y + 1] = key;
      }
      for(int t = 15; t <= last; t++)
      {
         while(j < m && lv[j].known < t)
         {
            ArrayResize(ap, na + 1); ArrayResize(ar, na + 1); ArrayResize(af, na + 1);
            ap[na] = lv[j].price; ar[na] = (lv[j].kind == 1) ? 1 : -1; af[na] = true; na++; j++;
         }
         if(b.a[t] < 0) continue;
         bool got = false; int s = 0; double st = 0;
         for(int q = 0; q < na; q++)
         {
            double p = ap[q];
            if(ar[q] == -1)
            {
               if(b.c[t] > p) { ar[q] = 1; af[q] = true; continue; }
               if(b.h[t] >= p)
               {
                  if(af[q] && !got && b.c[t] < b.e[t] && b.e[t] < b.e[t - 1])
                  { got = true; s = -1; st = MathMax(b.h[t], p) + 0.25 * b.a[t]; }
                  af[q] = false;
               }
            }
            else
            {
               if(b.c[t] < p) { ar[q] = -1; af[q] = true; continue; }
               if(b.l[t] <= p)
               {
                  if(af[q] && !got && b.c[t] > b.e[t] && b.e[t] > b.e[t - 1])
                  { got = true; s = 1; st = MathMin(b.l[t], p) - 0.25 * b.a[t]; }
                  af[q] = false;
               }
            }
         }
         if(na > 400)                                         // python keeps the newest 400
         {
            int drop = na - 400;
            for(int q = 0; q < 400; q++) { ap[q] = ap[q + drop]; ar[q] = ar[q + drop]; af[q] = af[q + drop]; }
            na = 400;
            ArrayResize(ap, na); ArrayResize(ar, na); ArrayResize(af, na);
         }
         if(t == last && got) { side = s; stop = st; return true; }
      }
      return false;
   }

   //--- open positions / pendings of strategy i
   int Positions(int i)
   {
      int k = 0;
      for(int p = PositionsTotal() - 1; p >= 0; p--)
      {
         ulong tk = PositionGetTicket(p);
         if(tk && PositionGetString(POSITION_SYMBOL) == EA_SYMBOL && PositionGetInteger(POSITION_MAGIC) == Magic(i)) k++;
      }
      return k;
   }
   int Pendings(int i)
   {
      int k = 0;
      for(int p = OrdersTotal() - 1; p >= 0; p--)
      {
         ulong tk = OrderGetTicket(p);
         if(tk && OrderGetString(ORDER_SYMBOL) == EA_SYMBOL && OrderGetInteger(ORDER_MAGIC) == Magic(i)) k++;
      }
      return k;
   }

   double ValuePerPriceLot() const
   {
      double tv = SymbolInfoDouble(EA_SYMBOL, SYMBOL_TRADE_TICK_VALUE);
      double ts = SymbolInfoDouble(EA_SYMBOL, SYMBOL_TRADE_TICK_SIZE);
      return (ts > 0) ? tv / ts : 0.0;
   }

   //--- risk $ of all open mix positions + pendings
   double OpenRisk()
   {
      double vpp = ValuePerPriceLot(), risk = 0.0;
      for(int p = PositionsTotal() - 1; p >= 0; p--)
      {
         ulong tk = PositionGetTicket(p);
         if(!tk || PositionGetString(POSITION_SYMBOL) != EA_SYMBOL) continue;
         long mg = PositionGetInteger(POSITION_MAGIC);
         if(mg < Config.MagicNumber + MIX_MAGIC_OFFSET || mg >= Config.MagicNumber + MIX_MAGIC_OFFSET + MIX_N) continue;
         double sl = PositionGetDouble(POSITION_SL), op = PositionGetDouble(POSITION_PRICE_OPEN);
         if(sl <= 0)                                                         // A336 (#24): no SL = big risk
         {
            risk += AccountInfoDouble(ACCOUNT_EQUITY) * 0.01;
            Logger.Warn("MIX", StringFormat("open mix position %I64u has NO stop - counted as 1%% equity risk", tk));
            continue;
         }
         bool lng = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
         double d = lng ? op - sl : sl - op;
         if(d > 0) risk += d * PositionGetDouble(POSITION_VOLUME) * vpp;    // stop past entry = no risk left
      }
      for(int p = OrdersTotal() - 1; p >= 0; p--)
      {
         ulong tk = OrderGetTicket(p);
         if(!tk || OrderGetString(ORDER_SYMBOL) != EA_SYMBOL) continue;
         long mg = OrderGetInteger(ORDER_MAGIC);
         if(mg < Config.MagicNumber + MIX_MAGIC_OFFSET || mg >= Config.MagicNumber + MIX_MAGIC_OFFSET + MIX_N) continue;
         double osl = OrderGetDouble(ORDER_SL);
         if(osl <= 0) { risk += AccountInfoDouble(ACCOUNT_EQUITY) * 0.01; continue; }   // A336 (#24)
         risk += MathAbs(OrderGetDouble(ORDER_PRICE_OPEN) - osl) * OrderGetDouble(ORDER_VOLUME_CURRENT) * vpp;
      }
      return risk;
   }

   //--- lot for a stop distance; min lot used only if real risk stays <= 1.5x target, else 0 (skip)
   //    A336 (#3/#4): spread added to the stop distance, minimum stop distance, hard lot cap
   double Lot(int i, double dist, double &risk_usd)
   {
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      double mult = (m_s[i].last_r > 0.05) ? 1.5 : ((m_s[i].last_r < -0.05) ? 0.75 : 1.0);
      risk_usd = eq * inp_MixRiskPct / 100.0 * m_s[i].weight * mult * StageRiskMult();   // A335 + A336 weight
      if(risk_usd <= 0) return 0.0;
      double target = risk_usd;
      double vpp = ValuePerPriceLot();
      if(dist <= 0 || vpp <= 0) return 0.0;
      MqlTick tk;
      if(!SymbolInfoTick(EA_SYMBOL, tk)) return 0.0;
      double spread = MathMax(0.0, tk.ask - tk.bid);
      double min_dist = MathMax(inp_MinStopUsd, 3.0 * spread);
      if(dist < min_dist)
      {
         Logger.Info("MIX", StringFormat("%s skipped: stop %.2f < min %.2f", m_s[i].name, dist, min_dist));
         return 0.0;
      }
      double eff = dist + spread;
      double step = SymbolInfoDouble(EA_SYMBOL, SYMBOL_VOLUME_STEP);
      double vmin = SymbolInfoDouble(EA_SYMBOL, SYMBOL_VOLUME_MIN);
      double vmax = SymbolInfoDouble(EA_SYMBOL, SYMBOL_VOLUME_MAX);
      if(step <= 0) step = 0.01;
      double lot = MathFloor(risk_usd / (eff * vpp) / step + 1e-9) * step;
      if(lot < vmin)
      {
         if(vmin * eff * vpp <= 1.5 * target) lot = vmin;
         else return 0.0;
      }
      lot = MathMin(lot, inp_MixMaxLot);
      if(vmax > 0) lot = MathMin(lot, vmax);
      lot = MathFloor(lot / step + 1e-9) * step;
      if(lot < vmin) return 0.0;                                   // cap below the broker minimum
      risk_usd = lot * eff * vpp;
      return NormalizeDouble(lot, 2);
   }

   //--- A336 (#25): retry a failed delete/close of the same ticket at most every 10 s
   bool Throttled(ulong tk)
   {
      for(int k = 0; k < 32; k++)
         if(m_thr_tk[k] == tk) return (TimeCurrent() - m_thr_t[k] < 10);
      return false;
   }
   void MarkTry(ulong tk)
   {
      for(int k = 0; k < 32; k++)
         if(m_thr_tk[k] == tk) { m_thr_t[k] = TimeCurrent(); return; }
      m_thr_tk[m_thr_i] = tk; m_thr_t[m_thr_i] = TimeCurrent();
      m_thr_i = (m_thr_i + 1) % 32;
   }

   //--- A336 (#7): a pending of strategy i placed for this bar already exists (bar time in comment)
   bool PendingForBar(int i, datetime bar)
   {
      string tag = "|" + IntegerToString((long)bar);
      for(int p = OrdersTotal() - 1; p >= 0; p--)
      {
         ulong tk = OrderGetTicket(p);
         if(!tk || OrderGetString(ORDER_SYMBOL) != EA_SYMBOL || OrderGetInteger(ORDER_MAGIC) != Magic(i)) continue;
         if(StringFind(OrderGetString(ORDER_COMMENT), tag) >= 0) return true;
      }
      return false;
   }

   //--- A336 (#5/#6/#16): the mix passes the same guards as the main entry. Cached 1 s.
   //    Rollover, session hard rules (weekend / Monday grace / Friday cutoff), spread,
   //    circuit breaker, news guard (post-news buffer), cooldown, daily limits, calendar
   //    blackout (fail closed), spike/spread calm, weekend cut, account-size check.
   bool GateOk(string &why)
   {
      if(m_gate_time == TimeCurrent()) { why = m_gate_why; return m_gate_ok; }
      m_gate_time = TimeCurrent();
      bool ok = true;
      why = "";
      GuardContext c;
      PopulateGuardContext(c, Config.MagicNumber, PriceUtils.PipSize());
      GuardEvalResult r;
      if(ok) { r = GuardRollover.Evaluate(c);   if(r.status != GUARD_PASS) { ok = false; why = "rollover"; } }
      if(ok && GuardSession.IsHardClosed(c))   { ok = false; why = "session_closed"; }
      if(ok) { r = SpreadGuard.Evaluate(c);     if(r.status != GUARD_PASS) { ok = false; why = "spread"; } }
      if(ok) { r = GuardCircuitBrk.Evaluate(c); if(r.status != GUARD_PASS) { ok = false; why = "circuit_breaker"; } }
      if(ok) { r = GuardNews.Evaluate(c);       if(r.status != GUARD_PASS) { ok = false; why = "news_guard"; } }
      if(ok) { r = GuardCooldown.Evaluate(c);   if(r.status != GUARD_PASS) { ok = false; why = "cooldown"; } }
      if(ok && DailyStats.IsConsecLossPaused()) { ok = false; why = "consec_loss_pause"; }
      string w2;
      if(ok && NewEntryBlocked(w2))            { ok = false; why = w2; }
      if(ok && NewsBlackout(w2))               { ok = false; why = w2; }
      if(ok && !MarketCalm(w2))                { ok = false; why = "not_calm:" + w2; }
      m_gate_ok = ok; m_gate_why = why;
      return ok;
   }

   bool RoomFor(double risk_usd)
   {
      double cap = AccountInfoDouble(ACCOUNT_EQUITY) * inp_MixMaxOpenRiskPct / 100.0;
      return OpenRisk() + risk_usd <= cap;
   }

   //--- A335: no new entries while the spread is too wide or right after a spike bar
   bool MarketCalm(string &why)
   {
      why = "";
      MqlTick tk;
      if(!SymbolInfoTick(EA_SYMBOL, tk)) { why = "no_tick"; return false; }
      double spread = tk.ask - tk.bid;
      if(spread > Config.SpreadHardCap * PriceUtils.PipSize()) { why = StringFormat("spread %.2f", spread); return false; }
      double a[1];
      if(m_atr15 != INVALID_HANDLE && CopyBuffer(m_atr15, 0, 2, 1, a) == 1 && a[0] > 0)
      {
         double rng = iHigh(EA_SYMBOL, PERIOD_M15, 1) - iLow(EA_SYMBOL, PERIOD_M15, 1);
         if(rng > inp_MixSpikeAtr * a[0]) { why = StringFormat("spike bar %.2f > %.1fxATR", rng, inp_MixSpikeAtr); return false; }
      }
      else { why = "atr_unavailable"; return false; }          // A336 (#16): fail closed
      return true;
   }

   //--- A336 (#26): a limit order rejected for its filling mode is retried once with RETURN
   bool SendLimit(bool buy, double lot, double en, double sl, double tp, string cm)
   {
      bool ok = buy
         ? m_trade.BuyLimit(lot, NormalizeDouble(en, _Digits), EA_SYMBOL, NormalizeDouble(sl, _Digits), NormalizeDouble(tp, _Digits), ORDER_TIME_GTC, 0, cm)
         : m_trade.SellLimit(lot, NormalizeDouble(en, _Digits), EA_SYMBOL, NormalizeDouble(sl, _Digits), NormalizeDouble(tp, _Digits), ORDER_TIME_GTC, 0, cm);
      if(!ok && m_trade.ResultRetcode() == TRADE_RETCODE_INVALID_FILL)
      {
         m_trade.SetTypeFilling(ORDER_FILLING_RETURN);
         ok = buy
            ? m_trade.BuyLimit(lot, NormalizeDouble(en, _Digits), EA_SYMBOL, NormalizeDouble(sl, _Digits), NormalizeDouble(tp, _Digits), ORDER_TIME_GTC, 0, cm)
            : m_trade.SellLimit(lot, NormalizeDouble(en, _Digits), EA_SYMBOL, NormalizeDouble(sl, _Digits), NormalizeDouble(tp, _Digits), ORDER_TIME_GTC, 0, cm);
         m_trade.SetTypeFillingBySymbol(EA_SYMBOL);
      }
      return ok;
   }

   void Act(int i, datetime bar)
   {
      if(Positions(i) > 0 || Pendings(i) > 0) return;        // A336 (#7): one trade OR one pending per strategy
      if(PendingForBar(i, bar)) return;                       // A336 (#7): never twice for the same bar
      string why;
      if(!GateOk(why)) { Logger.Info("MIX", m_s[i].name + " skipped: " + why); return; }
      MixBars b;
      double top = 0, stop = 0;
      bool mirror = (m_s[i].side == -1);
      if(m_s[i].kind == MIX_EMA9)
      {
         if(!Load(m_s[i].tf, false, b)) return;
         int side = 0; double st = 0;
         if(!Ema9Signal(b, side, st)) return;
         MqlTick tk; if(!SymbolInfoTick(EA_SYMBOL, tk)) return;
         double en = (side == 1) ? tk.ask : tk.bid;
         double risk = (en - st) * side;
         if(risk <= 0.05 * b.a[b.n - 1]) return;               // python: gapped through the stop -> skip
         double tp = en + side * 2.0 * risk;
         double r_usd; double lot = Lot(i, risk, r_usd);
         if(lot <= 0 || !RoomFor(r_usd)) return;
         if(!OrderAllowed(side, lot, en, why)) { Logger.Info("MIX", m_s[i].name + " skipped: " + why); return; }   // A336 (#11/#15)
         string cm = StringFormat("m%d|%.2f|%I64d", i, r_usd, (long)bar);
         if(Config.DryRun)                                                 // A336 (#12 / G15)
         {
            Logger.Info("MIX", StringFormat("DRY-RUN %s %s market lot=%.2f sl=%.2f tp=%.2f (not sent)", m_s[i].name,
                        side == 1 ? "BUY" : "SELL", lot, st, tp));
            return;
         }
         m_trade.SetExpertMagicNumber(Magic(i));
         bool ok = (side == 1) ? m_trade.Buy(lot, EA_SYMBOL, 0, NormalizeDouble(st, _Digits), NormalizeDouble(tp, _Digits), cm)
                               : m_trade.Sell(lot, EA_SYMBOL, 0, NormalizeDouble(st, _Digits), NormalizeDouble(tp, _Digits), cm);
         Logger.Info("MIX", StringFormat("%s %s market lot=%.2f sl=%.2f tp=%.2f ok=%d rc=%d", m_s[i].name,
                     side == 1 ? "BUY" : "SELL", lot, st, tp, (int)ok, m_trade.ResultRetcode()));
         return;
      }
      if(!Load(m_s[i].tf, mirror, b)) return;
      bool got = (m_s[i].kind == MIX_FRESH) ? FreshZone(b, top, stop) : QmZone(b, top, stop);
      if(!got) return;
      double en, sl, tp;
      double tp_m = top + 2.0 * (top - stop);                  // python: target = px + 2 (px - stop)
      if(!mirror) { en = top; sl = stop; tp = tp_m; }
      else        { en = 1.0 / top; sl = 1.0 / stop; tp = 1.0 / tp_m; }
      double dist = MathAbs(en - sl);
      double r_usd; double lot = Lot(i, dist, r_usd);
      if(lot <= 0 || !RoomFor(r_usd)) return;
      int lside = (!mirror) ? 1 : -1;
      if(!OrderAllowed(lside, lot, en, why)) { Logger.Info("MIX", m_s[i].name + " skipped: " + why); return; }   // A336 (#11/#15)
      datetime exp = TimeCurrent() + m_s[i].wait * PeriodSeconds(m_s[i].tf);
      string cm = StringFormat("m%d|%.2f|%I64d", i, r_usd, (long)bar);
      if(Config.DryRun)                                                    // A336 (#12 / G15)
      {
         Logger.Info("MIX", StringFormat("DRY-RUN %s %s limit %.2f lot=%.2f sl=%.2f tp=%.2f (not sent)", m_s[i].name,
                     mirror ? "SELL" : "BUY", en, lot, sl, tp));
         return;
      }
      m_trade.SetExpertMagicNumber(Magic(i));
      bool ok = SendLimit(!mirror, lot, en, sl, tp, cm);
      Logger.Info("MIX", StringFormat("%s %s limit %.2f lot=%.2f sl=%.2f tp=%.2f until %s ok=%d rc=%d", m_s[i].name,
                  mirror ? "SELL" : "BUY", en, lot, sl, tp, TimeToString(exp), (int)ok, m_trade.ResultRetcode()));
   }

   //--- expire pendings after `wait` bars, close trades after `hold` bars, first fill cancels other pendings
   void Housekeep()
   {
      for(int p = OrdersTotal() - 1; p >= 0; p--)
      {
         ulong tk = OrderGetTicket(p);
         if(!tk || OrderGetString(ORDER_SYMBOL) != EA_SYMBOL) continue;
         int i = (int)(OrderGetInteger(ORDER_MAGIC) - Config.MagicNumber - MIX_MAGIC_OFFSET);
         if(i < 0 || i >= MIX_N) continue;
         datetime placed = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
         if(TimeCurrent() - placed >= m_s[i].wait * PeriodSeconds(m_s[i].tf) || Positions(i) > 0)
         {
            if(Throttled(tk)) continue;                               // A336 (#25)
            MarkTry(tk);
            if(!m_trade.OrderDelete(tk) || m_trade.ResultRetcode() != TRADE_RETCODE_DONE)
               Logger.Error("MIX", StringFormat("expire delete failed ticket=%I64u rc=%d (retry in 10 s)", tk, m_trade.ResultRetcode()));
         }
      }
      for(int p = PositionsTotal() - 1; p >= 0; p--)
      {
         ulong tk = PositionGetTicket(p);
         if(!tk || PositionGetString(POSITION_SYMBOL) != EA_SYMBOL) continue;
         int i = (int)(PositionGetInteger(POSITION_MAGIC) - Config.MagicNumber - MIX_MAGIC_OFFSET);
         if(i < 0 || i >= MIX_N) continue;
         datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
         if(TimeCurrent() - opened >= m_s[i].hold * PeriodSeconds(m_s[i].tf))
         {
            if(Throttled(tk)) continue;                               // A336 (#25)
            MarkTry(tk);
            m_trade.SetExpertMagicNumber(Magic(i));
            bool ok = m_trade.PositionClose(tk);
            uint rc = m_trade.ResultRetcode();
            if(ok && (rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_DONE_PARTIAL))
               Logger.Info("MIX", StringFormat("%s time exit after %d bars", m_s[i].name, m_s[i].hold));
            else
               Logger.Error("MIX", StringFormat("%s time exit FAILED ticket=%I64u rc=%d (retry in 10 s)", m_s[i].name, tk, rc));
         }
      }
   }

public:
   CMixEngine() : m_atr15(INVALID_HANDLE), m_ready(false), m_last_news_check(0),
                  m_gate_time(0), m_gate_ok(false), m_gate_why(""), m_gate_logged(""), m_thr_i(0)
   {
      ArrayInitialize(m_thr_tk, 0);
      ArrayInitialize(m_thr_t, 0);
   }

   //--- A336 (#28)
   void Shutdown()
   {
      if(m_atr15 != INVALID_HANDLE) { IndicatorRelease(m_atr15); m_atr15 = INVALID_HANDLE; }
      m_ready = false;
   }

   //--- A336 (#7): bar times known? (iTime returns 0 until history is loaded)
   bool TryReady()
   {
      if(m_ready) return true;
      for(int i = 0; i < MIX_N; i++)
      {
         datetime b = iTime(EA_SYMBOL, m_s[i].tf, 1);
         if(b == 0) return false;
         m_s[i].last_bar = b;                                     // act on NEW bars only
      }
      m_ready = true;
      Logger.Info("MIX", "Mix engine ready (bar history loaded)");
      return true;
   }

   //--- A336 (#29): streak sizing survives a restart (sign of each strategy's last closed trade)
   void RebuildStreaks()
   {
      if(!HistorySelect(TimeCurrent() - 60 * 86400, TimeCurrent() + 60)) return;
      datetime last_t[MIX_N];
      ArrayInitialize(last_t, 0);
      int total = HistoryDealsTotal();
      for(int d = 0; d < total; d++)
      {
         ulong dt = HistoryDealGetTicket(d);
         if(dt == 0) continue;
         long mg = HistoryDealGetInteger(dt, DEAL_MAGIC);
         int i = (int)(mg - Config.MagicNumber - MIX_MAGIC_OFFSET);
         if(i < 0 || i >= MIX_N) continue;
         long en = HistoryDealGetInteger(dt, DEAL_ENTRY);
         if(en != DEAL_ENTRY_OUT && en != DEAL_ENTRY_OUT_BY) continue;
         datetime t = (datetime)HistoryDealGetInteger(dt, DEAL_TIME);
         if(t < last_t[i]) continue;
         last_t[i] = t;
         double pnl = HistoryDealGetDouble(dt, DEAL_PROFIT) + HistoryDealGetDouble(dt, DEAL_SWAP) + HistoryDealGetDouble(dt, DEAL_COMMISSION);
         m_s[i].last_r = (pnl > 0) ? 1.0 : -1.0;
      }
   }

   bool Init()
   {
      // name, timeframe, kind, side, wait bars, hold bars  (best_combo_gold.py msnr_trades / ema9_trades)
      Def(0,  "MSNR fresh_v long H1",  PERIOD_H1, MIX_FRESH,  1, 20, 48, inp_W_FreshLongH1);
      Def(1,  "MSNR qm long H1",       PERIOD_H1, MIX_QM,     1, 20, 48, inp_W_QmLongH1);
      Def(2,  "MSNR qm short H1",      PERIOD_H1, MIX_QM,    -1, 20, 48, inp_W_QmShortH1);
      Def(3,  "EMA9 H2",               PERIOD_H2, MIX_EMA9,   0,  1, 24, inp_W_Ema9H2);
      Def(4,  "MSNR fresh_v long H2",  PERIOD_H2, MIX_FRESH,  1, 10, 24, inp_W_FreshLongH2);
      Def(5,  "MSNR fresh_v short H2", PERIOD_H2, MIX_FRESH, -1, 10, 24, inp_W_FreshShortH2);
      Def(6,  "MSNR qm long H2",       PERIOD_H2, MIX_QM,     1, 10, 24, inp_W_QmLongH2);
      Def(7,  "EMA9 H4",               PERIOD_H4, MIX_EMA9,   0,  1, 12, inp_W_Ema9H4);
      Def(8,  "MSNR fresh_v long H4",  PERIOD_H4, MIX_FRESH,  1, 10, 20, inp_W_FreshLongH4);
      Def(9,  "MSNR fresh_v short H4", PERIOD_H4, MIX_FRESH, -1, 10, 20, inp_W_FreshShortH4);
      Def(10, "MSNR qm long H4",       PERIOD_H4, MIX_QM,     1, 10, 20, inp_W_QmLongH4);
      Def(11, "MSNR qm short H4",      PERIOD_H4, MIX_QM,    -1, 10, 20, inp_W_QmShortH4);
      m_atr15 = iATR(EA_SYMBOL, PERIOD_M15, 14);
      m_trade.SetTypeFillingBySymbol(EA_SYMBOL);
      m_trade.SetDeviationInPoints((ulong)MathMax(1.0, MathRound(Config.PipsToPoints(Config.SlippageMax))));
      m_trade.LogLevel(0);
      RebuildStreaks();
      m_ready = false;
      TryReady();                                                  // A336 (#7): retried every tick until history loads
      Logger.Info("MIX", StringFormat("Mix engine init: %d strategies, risk %.2f%%, open-risk cap %.1f%%, lot cap %.2f, min stop %.2f, dry_run=%d, ready=%d",
                  MIX_N, inp_MixRiskPct, inp_MixMaxOpenRiskPct, inp_MixMaxLot, inp_MinStopUsd, (int)Config.DryRun, (int)m_ready));
      return true;
   }

   //--- every tick while trading is allowed
   void OnTick()
   {
      if(!inp_MixEnabled) return;
      if(!TryReady()) return;
      Housekeep();
      //--- A336 (#5/#16): resting limit orders are cancelled the moment the gate closes
      //    (rollover, news, spike, spread, circuit breaker, weekend cut ...), checked each second
      string why;
      bool gate = GateOk(why);
      if(!gate)
      {
         if(why != m_gate_logged) { Logger.Info("MIX", "gate closed: " + why); m_gate_logged = why; }
         CancelPendings("gate:" + why);
      }
      else m_gate_logged = "";
      for(int i = 0; i < MIX_N; i++)
      {
         datetime bar = iTime(EA_SYMBOL, m_s[i].tf, 1);
         if(bar == 0 || bar == m_s[i].last_bar) continue;
         if(!gate) continue;                                   // A336 (#6): bar kept until the gate opens
         m_s[i].last_bar = bar;
         if(m_s[i].weight <= 0) continue;                      // A336: strategy switched off by its weight
         Act(i, bar);
      }
   }

   //--- while suspended: keep time exits, no new orders
   void Manage() { if(m_ready) Housekeep(); }

   void CancelPendings(string why)
   {
      for(int p = OrdersTotal() - 1; p >= 0; p--)
      {
         ulong tk = OrderGetTicket(p);
         if(!tk || OrderGetString(ORDER_SYMBOL) != EA_SYMBOL) continue;
         long mg = OrderGetInteger(ORDER_MAGIC);
         if(mg >= Config.MagicNumber + MIX_MAGIC_OFFSET && mg < Config.MagicNumber + MIX_MAGIC_OFFSET + MIX_N)
         {
            if(Throttled(tk)) continue;                               // A336 (#25)
            MarkTry(tk);
            if(m_trade.OrderDelete(tk) && m_trade.ResultRetcode() == TRADE_RETCODE_DONE)
               Logger.Info("MIX", "pending cancelled: " + why);
            else
               Logger.Error("MIX", StringFormat("pending cancel FAILED ticket=%I64u rc=%d: %s (retry in 10 s)", tk, m_trade.ResultRetcode(), why));
         }
      }
   }

   //--- streak sizing: R of a strategy's closed trade = net P&L / risk $ stored in the entry comment
   void OnTransaction(const MqlTradeTransaction &trans)
   {
      if(trans.type != TRADE_TRANSACTION_DEAL_ADD || trans.deal == 0 || !HistoryDealSelect(trans.deal)) return;
      long mg = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
      int i = (int)(mg - Config.MagicNumber - MIX_MAGIC_OFFSET);
      if(i < 0 || i >= MIX_N) return;
      long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
      if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY) return;
      ulong pos = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
      if(PositionSelectByTicket(pos)) return;                 // partial: wait for the full close
      if(!HistorySelectByPosition(pos)) return;
      double pnl = 0.0, risk = 0.0;
      for(int d = 0; d < HistoryDealsTotal(); d++)
      {
         ulong dt = HistoryDealGetTicket(d);
         pnl += HistoryDealGetDouble(dt, DEAL_PROFIT) + HistoryDealGetDouble(dt, DEAL_SWAP) + HistoryDealGetDouble(dt, DEAL_COMMISSION);
         if(HistoryDealGetInteger(dt, DEAL_ENTRY) == DEAL_ENTRY_IN)
         {
            string cm = HistoryDealGetString(dt, DEAL_COMMENT);
            string parts[];
            if(StringSplit(cm, StringGetCharacter("|", 0), parts) >= 2) risk = StringToDouble(parts[1]);
         }
      }
      m_s[i].last_r = (risk > 0) ? pnl / risk : (pnl > 0 ? 1.0 : -1.0);
      Logger.Info("MIX", StringFormat("%s closed pnl=%.2f R=%.2f", m_s[i].name, pnl, m_s[i].last_r));
   }
};

CMixEngine MixEngine;

#endif // CMIXENGINE_MQH
