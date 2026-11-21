//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — MSNR (Malaysian SnR) engine             |
//| File: Intelligence/CMSNREngine.mqh                                |
//| A320 (21 Nov 2026). Port of 07-trading/src/msnr.py, the rules     |
//| tested in research/ea_msnr_gold.py.                               |
//|                                                                    |
//| Levels come from CLOSES (MSNR rule), built on H4, tracked on H1:  |
//|   A level: green then red candle -> resistance at green close     |
//|   V level: red then green candle -> support at red close          |
//|   key (k=2): close is the highest (A) / lowest (V) of k bars each |
//|   side, so a level is known only k bars after it formed.          |
//|   fresh: untouched since formed or flipped                        |
//|   touch: wick reaches it, close stays on its side -> unfresh      |
//|   flip:  close through it -> role swaps (RBS / SBR), fresh again  |
//| Storyline: weekly direction from weekly key levels.               |
//|                                                                    |
//| Gates (inputs) and the backtest result behind each default        |
//| (2 years H1, earlier part used to choose, later part to check):   |
//|   inp_MSNR_FreshGate  ON : nearest level on the trade side must   |
//|        still be fresh. Later part +0.23R/trade (36 trades) vs     |
//|        base +0.14R (60); random entries -0.03R; p = 0.02.         |
//|   inp_MSNR_LevelGate  OFF: pullback must reach that level.        |
//|        Earlier part -0.07R (worse than base).                     |
//|   inp_MSNR_StoryGate  OFF: weekly storyline must agree.           |
//|        Earlier part -0.21R, later -0.01R (hurts).                 |
//| Not compiled here (no MetaEditor in the build cloud).             |
//+------------------------------------------------------------------+
#ifndef CMSNRENGINE_MQH
#define CMSNRENGINE_MQH
#include "../Include/Defines.mqh"

input group    "=== MSNR (A320) ==="
input bool     inp_MSNR_FreshGate = true;   // Trade only if nearest MSNR level on trade side is fresh
input bool     inp_MSNR_LevelGate = false;  // Pullback must reach that MSNR level (tested: worse)
input bool     inp_MSNR_StoryGate = false;  // Weekly MSNR storyline must agree (tested: worse)
input int      inp_MSNR_KeyBars   = 2;      // Key-level width k (bars each side)

#define MSNR_MAX_LEVELS 600
#define MSNR_H4_HISTORY 1500
#define MSNR_W1_HISTORY 200

struct MSNRLevel
{
   double   price;
   int      role;        // +1 support, -1 resistance
   bool     fresh;
   bool     prev_fresh;  // fresh value before the last applied H1 bar
   bool     just_flipped;
   datetime known;       // time the level became known (H4 close time)
   bool     active;      // known and being tracked
};

class CMSNREngine
{
private:
   MSNRLevel m_lv[];
   int       m_count;
   int       m_k;
   datetime  m_last_h1_open;    // open time of last applied (closed) H1 bar
   datetime  m_last_h4_open;    // open time of last H4 bar scanned as a key-window end
   datetime  m_last_w1_open;
   double    m_last_close;
   double    m_last_low;
   double    m_last_high;
   int       m_story;
   bool      m_ready;
   string    m_reason;

   //--- append; drop the oldest when full (manual shift: no overlapping ArrayCopy)
   void Add(double price, int role, datetime known)
   {
      if(m_count >= MSNR_MAX_LEVELS)
      {
         for(int i = 1; i < m_count; i++) m_lv[i - 1] = m_lv[i];
         m_count--;
      }
      m_lv[m_count].price        = price;
      m_lv[m_count].role         = role;
      m_lv[m_count].fresh        = true;
      m_lv[m_count].prev_fresh   = true;
      m_lv[m_count].just_flipped = false;
      m_lv[m_count].known        = known;
      m_lv[m_count].active       = false;
      m_count++;
   }

   //--- key level whose window ends at index e (rates oldest-first). Pair = (p, p+1), p = e - k.
   void ScanPair(const MqlRates &r[], int e, int period_sec)
   {
      int p = e - m_k;
      if(p - m_k < 0 || p + 1 > e) return;
      int a = (r[p].close > r[p].open) ? 1 : (r[p].close < r[p].open ? -1 : 0);
      int b = (r[p + 1].close > r[p + 1].open) ? 1 : (r[p + 1].close < r[p + 1].open ? -1 : 0);
      int role = 0;
      if(a == 1 && b == -1)      role = -1;   // A level -> resistance
      else if(a == -1 && b == 1) role = 1;    // V level -> support
      else return;
      double px = r[p].close;
      for(int j = p - m_k; j <= p + m_k; j++)
      {
         if(role == -1 && r[j].close > px) return;   // not the highest close
         if(role == 1  && r[j].close < px) return;   // not the lowest close
      }
      int known_i = MathMax(p + 1, p + m_k);
      Add(px, role, r[known_i].time + period_sec);
   }

   //--- one closed H1 bar: activate newly known levels, then flips / touches
   void ApplyBar(double hi, double lo, double cl, datetime close_time)
   {
      for(int j = 0; j < m_count; j++)
      {
         if(!m_lv[j].active)
         {
            if(m_lv[j].known > close_time) continue;
            m_lv[j].active = true;
         }
         m_lv[j].prev_fresh   = m_lv[j].fresh;
         m_lv[j].just_flipped = false;
         if(m_lv[j].role == 1)
         {
            if(cl < m_lv[j].price)      { m_lv[j].role = -1; m_lv[j].fresh = true; m_lv[j].just_flipped = true; }
            else if(lo <= m_lv[j].price)  m_lv[j].fresh = false;
         }
         else
         {
            if(cl > m_lv[j].price)      { m_lv[j].role = 1;  m_lv[j].fresh = true; m_lv[j].just_flipped = true; }
            else if(hi >= m_lv[j].price)  m_lv[j].fresh = false;
         }
      }
      m_last_close = cl; m_last_low = lo; m_last_high = hi;
   }

   //--- weekly storyline (python: msnr.storyline), recomputed on each new weekly bar
   void RebuildStory()
   {
      MqlRates w[];
      ArraySetAsSeries(w, false);
      int n = CopyRates(EA_SYMBOL, PERIOD_W1, 1, MSNR_W1_HISTORY, w);   // closed weeks only
      if(n < 2 * m_k + 3) { m_story = 0; return; }
      double lp[]; int lr[]; int lk[];
      ArrayResize(lp, 0); ArrayResize(lr, 0); ArrayResize(lk, 0);
      for(int e = 2 * m_k; e < n; e++)
      {
         int p = e - m_k;
         int a = (w[p].close > w[p].open) ? 1 : (w[p].close < w[p].open ? -1 : 0);
         int b = (w[p + 1].close > w[p + 1].open) ? 1 : (w[p + 1].close < w[p + 1].open ? -1 : 0);
         int role = (a == 1 && b == -1) ? -1 : ((a == -1 && b == 1) ? 1 : 0);
         if(role == 0) continue;
         bool key = true;
         for(int j = p - m_k; j <= p + m_k && key; j++)
            if((role == -1 && w[j].close > w[p].close) || (role == 1 && w[j].close < w[p].close)) key = false;
         if(!key) continue;
         int s = ArraySize(lp);
         ArrayResize(lp, s + 1); ArrayResize(lr, s + 1); ArrayResize(lk, s + 1);
         lp[s] = w[p].close; lr[s] = role; lk[s] = MathMax(p + 1, p + m_k);
      }
      int cur = 0;
      for(int j = 1; j < n; j++)
      {
         for(int q = 0; q < ArraySize(lp); q++)
         {
            if(lk[q] >= j) continue;                 // only levels known before this week
            double L = lp[q];
            if(lr[q] == 1  && w[j].low  <= L && L < w[j].close)                    cur = 1;
            else if(lr[q] == -1 && w[j].close > L && w[j - 1].close <= L)          cur = 1;
            else if(lr[q] == -1 && w[j].high >= L && L > w[j].close)               cur = -1;
            else if(lr[q] == 1  && w[j].close < L && w[j - 1].close >= L)          cur = -1;
         }
      }
      m_story = cur;
   }

   //--- nearest level on a side, as of the last closed H1 bar
   int Nearest(int side)
   {
      int best = -1;
      for(int j = 0; j < m_count; j++)
      {
         if(!m_lv[j].active) continue;
         if(side == 1 && m_lv[j].role == 1 && m_lv[j].price <= m_last_close)
         { if(best < 0 || m_lv[j].price > m_lv[best].price) best = j; }
         if(side == -1 && m_lv[j].role == -1 && m_lv[j].price >= m_last_close)
         { if(best < 0 || m_lv[j].price < m_lv[best].price) best = j; }
      }
      return best;
   }

public:
   CMSNREngine() : m_count(0), m_k(2), m_last_h1_open(0), m_last_h4_open(0), m_last_w1_open(0),
                   m_last_close(0), m_last_low(0), m_last_high(0), m_story(0), m_ready(false), m_reason("") {}

   bool Init()
   {
      m_k = MathMax(1, MathMin(10, inp_MSNR_KeyBars));
      ArrayResize(m_lv, MSNR_MAX_LEVELS);
      m_count = 0;
      MqlRates h4[];
      ArraySetAsSeries(h4, false);
      int n4 = CopyRates(EA_SYMBOL, PERIOD_H4, 1, MSNR_H4_HISTORY, h4);   // closed bars, oldest first
      if(n4 < 2 * m_k + 3)
      {
         Print("[MSNR WARN] not enough H4 history (", n4, ") — MSNR gates will block until ready");
         return false;
      }
      for(int e = 2 * m_k; e < n4; e++) ScanPair(h4, e, PeriodSeconds(PERIOD_H4));
      m_last_h4_open = h4[n4 - 1].time;
      // replay H1 from the first level's known time
      datetime from = (m_count > 0) ? m_lv[0].known - PeriodSeconds(PERIOD_H1) : h4[0].time;
      MqlRates h1[];
      ArraySetAsSeries(h1, false);
      int n1 = CopyRates(EA_SYMBOL, PERIOD_H1, from, TimeCurrent(), h1);
      int sec1 = PeriodSeconds(PERIOD_H1);
      datetime cur_h1 = iTime(EA_SYMBOL, PERIOD_H1, 0);
      for(int t = 0; t < n1; t++)
      {
         if(h1[t].time >= cur_h1) break;                       // skip the forming bar
         ApplyBar(h1[t].high, h1[t].low, h1[t].close, h1[t].time + sec1);
         m_last_h1_open = h1[t].time;
      }
      RebuildStory();
      m_last_w1_open = iTime(EA_SYMBOL, PERIOD_W1, 0);
      m_ready = (n1 > 0);
      Print(StringFormat("[MSNR] ready=%d levels=%d story=%d", (int)m_ready, m_count, m_story));
      return m_ready;
   }

   //--- call every tick; cheap unless an H1/H4/W1 bar closed
   void Update()
   {
      if(!m_ready) return;
      datetime h4_open = iTime(EA_SYMBOL, PERIOD_H4, 1);           // last CLOSED H4 bar
      if(h4_open > m_last_h4_open)
      {
         MqlRates r[];
         ArraySetAsSeries(r, false);
         int need = 2 * m_k + 2;
         int n = CopyRates(EA_SYMBOL, PERIOD_H4, 1, need, r);
         if(n == need) ScanPair(r, n - 1, PeriodSeconds(PERIOD_H4));
         m_last_h4_open = h4_open;
      }
      datetime h1_open = iTime(EA_SYMBOL, PERIOD_H1, 1);           // last CLOSED H1 bar
      if(h1_open > m_last_h1_open)
      {
         MqlRates b[];
         ArraySetAsSeries(b, false);
         // apply every closed H1 bar we missed (gaps, restarts), oldest first
         int n = CopyRates(EA_SYMBOL, PERIOD_H1, m_last_h1_open + 1, h1_open, b);
         for(int i = 0; i < n; i++)
            ApplyBar(b[i].high, b[i].low, b[i].close, b[i].time + PeriodSeconds(PERIOD_H1));
         m_last_h1_open = h1_open;
      }
      datetime w1_open = iTime(EA_SYMBOL, PERIOD_W1, 0);
      if(w1_open > m_last_w1_open) { RebuildStory(); m_last_w1_open = w1_open; }
   }

   //--- simple ATR(14) of closed H1 bars, price units (only needed by the level gate)
   double H1ATR()
   {
      MqlRates r[];
      ArraySetAsSeries(r, false);
      int n = CopyRates(EA_SYMBOL, PERIOD_H1, 1, 15, r);
      if(n < 15) return 0.0;
      double sum = 0.0;
      for(int i = 1; i < n; i++)
         sum += MathMax(r[i].high, r[i - 1].close) - MathMin(r[i].low, r[i - 1].close);
      return sum / (n - 1);
   }

   //--- the scorer gate. side: +1 long, -1 short
   bool Allows(int side)
   {
      m_reason = "";
      if(!inp_MSNR_FreshGate && !inp_MSNR_LevelGate && !inp_MSNR_StoryGate) return true;
      if(!m_ready) { m_reason = "msnr_not_ready"; return false; }
      int j = Nearest(side);
      if(inp_MSNR_FreshGate)
      {
         if(j < 0 || !m_lv[j].prev_fresh || m_lv[j].just_flipped)
         { m_reason = "msnr_level_not_fresh"; return false; }
      }
      if(inp_MSNR_LevelGate)
      {
         if(j < 0) { m_reason = "msnr_no_level"; return false; }
         double swing = (side == 1) ? m_last_low : m_last_high;
         bool touched = (side == 1) ? (m_last_low <= m_lv[j].price) : (m_last_high >= m_lv[j].price);
         if(!touched && MathAbs(swing - m_lv[j].price) > 0.5 * H1ATR())
         { m_reason = "msnr_pullback_not_at_level"; return false; }
      }
      if(inp_MSNR_StoryGate && m_story * side <= 0)
      { m_reason = "msnr_storyline_against"; return false; }
      return true;
   }

   string LastReason()     const { return m_reason; }
   int    Storyline()      const { return m_story; }
   int    LevelCount()     const { return m_count; }
   bool   IsReady()        const { return m_ready; }
   double NearestPrice(int side) { int j = Nearest(side); return (j < 0) ? 0.0 : m_lv[j].price; }
};

CMSNREngine MSNR;

#endif // CMSNRENGINE_MQH
