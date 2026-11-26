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

//+------------------------------------------------------------------+
//| A325: news blackout — no NEW entries within inp_NewsBlockMin of a |
//| high-impact USD event (CPI, jobs report, FOMC ...) from the MT5   |
//| economic calendar. 2-year test (research/macro_layer_gold.py):    |
//| the 163 trades within 2h of CPI/NFP/FOMC made only +0.015R vs     |
//| +0.169R for the rest, before the wider news spreads a real broker |
//| charges. It is a safety rule; it does not add backtest profit.    |
//| NOTE: MT5 calendar functions return nothing in the Strategy       |
//| Tester, so this gate only works on demo/live charts.              |
//+------------------------------------------------------------------+
input int      inp_NewsBlockMin = 120;    // A325: block entries this many minutes before/after high-impact USD news (min 3 = The5%ers +/-2 min rule, always on)

//--- A336 (#9 / G6): the calendar FAILS CLOSED. If CalendarValueHistory errors (-1) or the
//    calendar has no USD events at all for the current server week (database not synced, e.g.
//    on a Wine VPS), new entries are blocked and this is logged once per hour.
datetime g_cal_last_log      = 0;
datetime g_cal_synced_check  = 0;
bool     g_cal_synced        = false;

void CalendarLog(string why)
{
   if(g_cal_last_log != 0 && TimeCurrent() - g_cal_last_log < 3600) return;
   g_cal_last_log = TimeCurrent();
   Logger.Error("NEWS_CAL", "Economic calendar unavailable - NEW ENTRIES BLOCKED (fail closed)", why);
}

bool CalendarSynced()
{
   if(g_cal_synced_check != 0 && TimeCurrent() - g_cal_synced_check < 600) return g_cal_synced;
   g_cal_synced_check = TimeCurrent();
   MqlDateTime s;
   TimeToStruct(TimeTradeServer(), s);
   int back_days = (s.day_of_week + 6) % 7;                 // days since Monday
   s.hour = 0; s.min = 0; s.sec = 0;
   datetime week0 = StructToTime(s) - back_days * 86400;
   MqlCalendarValue w[];
   ResetLastError();
   int n = CalendarValueHistory(w, week0, week0 + 7 * 86400, "US", "USD");
   g_cal_synced = (n > 0);
   if(!g_cal_synced)
      CalendarLog(StringFormat("no USD events this week (n=%d err=%d)", n, GetLastError()));
   return g_cal_synced;
}

//--- A345: official US schedule as a backup (UTC). Sources, fetched 26 Nov 2026:
//    FOMC: federalreserve.gov/monetarypolicy/fomccalendars.htm (statement 14:00 New York time)
//    CPI + jobs report: bls.gov/schedule/2027 and BLS 2026 schedule (08:30 New York time)
//    Used (1) always, as a second check next to the MT5 calendar, and (2) instead of the MT5
//    calendar when that is missing or not synced (common on a Wine VPS), so the bot keeps
//    trading safely. After the last date below it fails closed again: update the list yearly.
const datetime KALPA_US_EVENTS_UTC[] = {
   D'2026.12.04 13:30', D'2026.12.09 19:00', D'2026.12.10 13:30', D'2027.01.08 13:30',
   D'2027.01.13 13:30', D'2027.01.27 19:00', D'2027.02.05 13:30', D'2027.02.11 13:30',
   D'2027.03.05 13:30', D'2027.03.10 13:30', D'2027.03.17 18:00', D'2027.04.02 12:30',
   D'2027.04.13 12:30', D'2027.04.28 18:00', D'2027.05.07 12:30', D'2027.05.12 12:30',
   D'2027.06.04 12:30', D'2027.06.09 18:00', D'2027.06.10 12:30', D'2027.07.02 12:30',
   D'2027.07.14 12:30', D'2027.07.28 18:00', D'2027.08.06 12:30', D'2027.08.11 12:30',
   D'2027.09.03 12:30', D'2027.09.14 12:30', D'2027.09.15 18:00', D'2027.10.08 12:30',
   D'2027.10.14 12:30', D'2027.10.27 18:00', D'2027.11.05 12:30', D'2027.11.10 13:30',
   D'2027.11.17 19:00', D'2027.12.03 13:30', D'2027.12.10 13:30'
};

bool ScheduledEventNear(int win_min, string &why)
{
   datetime now = TimeGMT();
   for(int i = 0; i < ArraySize(KALPA_US_EVENTS_UTC); i++)
   {
      if(MathAbs((double)((long)now - (long)KALPA_US_EVENTS_UTC[i])) <= win_min * 60.0)   // signed: the "after" half of the window too
      {
         why = "scheduled_us_event@" + TimeToString(KALPA_US_EVENTS_UTC[i], TIME_DATE | TIME_MINUTES) + "UTC";
         return true;
      }
   }
   return false;
}

bool ScheduleCovers()
{
   int n = ArraySize(KALPA_US_EVENTS_UTC);
   return n > 0 && TimeGMT() <= KALPA_US_EVENTS_UTC[n - 1];
}

bool NewsBlackout(string &why)
{
   why = "";
   if(MQLInfoInteger(MQL_TESTER)) return false;            // calendar not available in the tester
   int win = MathMax(inp_NewsBlockMin, 3);                 // A336: the firm's +/-2 min rule cannot be switched off
   datetime now = TimeTradeServer();
   MqlCalendarValue v[];
   ResetLastError();
   if(ScheduledEventNear(win, why)) return true;           // A345: official schedule, always checked
   int n = CalendarValueHistory(v, now - win * 60, now + win * 60, "US", "USD");
   if(n < 0)
   {
      why = StringFormat("calendar_error_%d", GetLastError());
      CalendarLog(why);
      if(ScheduleCovers()) { why = ""; return false; }      // A345: backup schedule covers CPI/NFP/FOMC
      return true;                                          // fail closed
   }
   if(!CalendarSynced())
   {
      why = "calendar_not_synced";
      if(ScheduleCovers()) { why = ""; return false; }      // A345: backup schedule covers CPI/NFP/FOMC
      return true;                                          // fail closed
   }
   for(int i = 0; i < n; i++)
   {
      MqlCalendarEvent ev;
      if(!CalendarEventById(v[i].event_id, ev)) continue;
      if(ev.importance != CALENDAR_IMPORTANCE_HIGH) continue;
      why = StringFormat("news_blackout:%s@%s", ev.name, TimeToString(v[i].time, TIME_MINUTES));
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| A346: cut the book before scheduled news (instant-jump guard).   |
//| Within inp_NewsDeriskMin minutes BEFORE a CPI / NFP / FOMC        |
//| release (official list above, plus high-importance USD events in  |
//| the MT5 calendar), close our positions - losers first, then the   |
//| largest - until a sudden inp_JumpPct move against the net book    |
//| (stops skipped) would lose at most inp_JumpBudgetPct of the       |
//| account minus what today has already lost. Backtest (29 months,  |
//| E8 $10K): news-time jump risk 22% -> 1.4% of releases, profit -5%.|
//+------------------------------------------------------------------+
input int      inp_NewsDeriskMin  = 120;   // A346: minutes before news to cut the book (0 = off)
input double   inp_JumpPct        = 3.0;   // A346: instant move to survive (%)
input double   inp_JumpBudgetPct  = 2.0;   // A346: max loss from that move incl. today's loss (% of account size)

bool UpcomingEventWithin(int minutes)
{
   datetime now = TimeGMT();
   for(int i = 0; i < ArraySize(KALPA_US_EVENTS_UTC); i++)
   {
      long dt = (long)KALPA_US_EVENTS_UTC[i] - (long)now;
      if(dt >= 0 && dt <= (long)minutes * 60) return true;
   }
   datetime srv = TimeTradeServer();
   MqlCalendarValue v[];
   int n = CalendarValueHistory(v, srv, srv + minutes * 60, "US", "USD");
   for(int i = 0; i < n; i++)
   {
      MqlCalendarEvent ev;
      if(CalendarEventById(v[i].event_id, ev) && ev.importance == CALENDAR_IMPORTANCE_HIGH) return true;
   }
   return false;
}

void NewsDerisk()
{
   if(inp_NewsDeriskMin <= 0 || MQLInfoInteger(MQL_TESTER)) return;
   static datetime last_check = 0;
   static bool     near = false;
   if(TimeGMT() - last_check >= 30) { near = UpcomingEventWithin(inp_NewsDeriskMin); last_check = TimeGMT(); }
   if(!near) return;
   static datetime fail_t = 0;                              // debug pass 26 Nov: a failed close is retried every 10 s, not every tick
   if(fail_t != 0 && TimeCurrent() - fail_t < 10) return;
   double contract = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   double price    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(contract <= 0 || price <= 0) return;
   double day_base = DailyStats.GetDayBase();
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity <= 0) return;
   double room = inp_JumpBudgetPct / 100.0 * inp_AccountSize - MathMax(0.0, day_base - equity);
   CTrade tr;
   tr.SetDeviationInPoints(50);
   tr.SetTypeFillingBySymbol(_Symbol);
   for(int guard = 0; guard < 20; guard++)
   {
      double net = 0.0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong t = PositionGetTicket(i);
         if(t == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
         if(!IsOurMagic(PositionGetInteger(POSITION_MAGIC))) continue;
         double vol = PositionGetDouble(POSITION_VOLUME);
         net += (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? vol : -vol;
      }
      if(MathAbs(net) * contract * price * inp_JumpPct / 100.0 <= MathMax(room, 0.0)) return;
      //--- pick the position to close: same side as the net book, losers first, then the largest
      ulong pick = 0; double best_key = -DBL_MAX;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong t = PositionGetTicket(i);
         if(t == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
         if(!IsOurMagic(PositionGetInteger(POSITION_MAGIC))) continue;
         int side = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;
         if(side * net <= 0) continue;
         double key = (PositionGetDouble(POSITION_PROFIT) < 0 ? 1e6 : 0.0) + PositionGetDouble(POSITION_VOLUME);
         if(key > best_key) { best_key = key; pick = t; }
      }
      if(pick == 0) return;
      //--- review 26 Nov: the closing deal carries the request magic. Use the position's own magic,
      //    else the close is magic 0 and OnTradeTransaction/daily stats/streaks never see it.
      if(!PositionSelectByTicket(pick)) continue;
      tr.SetExpertMagicNumber((ulong)PositionGetInteger(POSITION_MAGIC));
      if(!tr.PositionClose(pick))
      {
         Logger.Error("NEWS_DERISK", StringFormat("close failed ticket=%I64u retcode=%u (retry in 10 s)", pick, tr.ResultRetcode()), "");
         fail_t = TimeCurrent();
         return;
      }
      Logger.Info("NEWS_DERISK", StringFormat("closed ticket=%I64u before news (net %.2f lots, room $%.2f)", pick, net, room));
   }
}

#endif // CMSNRENGINE_MQH
