//+------------------------------------------------------------------+
//|             ICT_RR_HYBRID_ALL_CONDITIONS_5ERS.mq5                |
//|   Hybrid EA (your v7.10) + The5ers funded-challenge guards.      |
//|   Strategy logic 100% unchanged — only risk envelope added.      |
//|   Live evidence (May 13 → Jun 2): +$468 / 45% WR / PF 1.67       |
//|   Validate in Strategy Tester on broker-matched data before use. |
//+------------------------------------------------------------------+
#property copyright "ICT_RR_HYBRID + 5ers envelope"
#property version   "8.00"
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

// ========== STRATEGY INPUTS (UNCHANGED from v7.10) ==========
input int    zzPeriod              = 5;
input double riskPercent           = 0.5;     // CHANGED from 2.5 — funded account safety
input int    atrPeriod             = 14;
input double atrMultiplier         = 0.7;
input double maxLot                = 0.10;
input int    lossPauseCandles      = 3;
input double entryBufferATR        = 0.32;

input int    fastMAPeriod          = 10;
input int    breakoutBars          = 20;
input double adxThreshold          = 25;

// Trailing stop — DEFAULT OFF, your live evidence proved this was right
input bool   useTrailingStop       = false;
input double breakevenPips         = 100;
input double trailStartPips        = 300;
input double trailDistancePips     = 250;

// ========== NEW: SYMBOL FILTER ==========
input group "=== Symbol Filter (BTCUSD lost -$162 / 1W:10L in live) ==="
input bool   TradeXAUUSD           = true;
input bool   TradeBTCUSD           = false;   // OFF based on live evidence

// ========== NEW: THE5ERS RISK ENVELOPE ==========
input group "=== The5ers Risk Envelope (10K High Stakes) ==="
input double initialBalance        = 0;       // 0 = auto-detect at init
input double maxDDPct              = 10.0;    // Absolute floor (10% from initial = $9,000)
input double ddBufferPct           = 1.0;     // Stop trading this % above the floor
input double dailyBreakerPct       = 3.0;     // Halt at this % daily loss (hard limit is 5%)
input double dailyProfitTargetPct  = 999.0;   // Optional profit lock (set lower to lock gains)

// ========== NEW: TRADE FILTERS ==========
input group "=== Trade Filters ==="
input int    maxSpreadPoints       = 60;      // Skip if spread above this
input bool   useSession            = true;
input int    sessionStartHour      = 6;       // Server time
input int    sessionEndHour        = 21;
input bool   blockRollover         = true;
input int    rolloverGuardMin      = 5;       // No trades +/- this around 00:00 server
input bool   useNewsFilter         = true;    // MT5 calendar (live/forward only)
input int    newsBufferMin         = 2;       // No execution +/- this around high-impact USD news

// ========== LEGACY DAILY (kept but percentage-based now) ==========
input int    maxTradesPerDay       = 50;      // Reduced from 200
input bool   resetAtMidnight       = true;

// ========== GLOBALS ==========
#define MAX_SWINGS 200
double pVals[MAX_SWINGS];
int pSize = 0;
int dir = 0;
double cur_ext = 0;
datetime lastBarTime = 0;
int consecutiveLoss = 0;
int pauseBars = 0;
int atrHandle = INVALID_HANDLE;
int adxHandle = INVALID_HANDLE;
int emaHandle = INVALID_HANDLE;

double dailyProfit = 0.0;
datetime lastResetTime = 0;
bool tradingHalted = false;
int tradesToday = 0;

// New risk-envelope globals
double g_initBalance = 0.0;
double g_floor       = 0.0;
double g_dailyBaseline = 0.0;
int    g_dayOfYear   = -1;

// ========== PRICE HELPERS ==========
double H(int i){ return iHigh(_Symbol, PERIOD_CURRENT, i); }
double L(int i){ return iLow(_Symbol, PERIOD_CURRENT, i); }
double C(int i){ return iClose(_Symbol, PERIOD_CURRENT, i); }
datetime T(int i){ return iTime(_Symbol, PERIOD_CURRENT, i); }

// ========== INIT ==========
int OnInit()
{
   atrHandle = iATR(_Symbol, PERIOD_CURRENT, atrPeriod);
   if(atrHandle == INVALID_HANDLE) return INIT_FAILED;
   adxHandle = iADX(_Symbol, PERIOD_CURRENT, 14);
   if(adxHandle == INVALID_HANDLE) return INIT_FAILED;
   emaHandle = iMA(_Symbol, PERIOD_CURRENT, fastMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(emaHandle == INVALID_HANDLE) return INIT_FAILED;

   lastResetTime = TimeTradeServer();
   g_initBalance = (initialBalance>0) ? initialBalance : AccountInfoDouble(ACCOUNT_BALANCE);
   g_floor = g_initBalance * (1.0 - maxDDPct/100.0);
   g_dailyBaseline = AccountInfoDouble(ACCOUNT_BALANCE);

   PrintFormat("EA v8 (5ers envelope) initialised. balance=%.2f  floor=%.2f  risk/trade=%.2f%%",
               g_initBalance, g_floor, riskPercent);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(atrHandle != INVALID_HANDLE) IndicatorRelease(atrHandle);
   if(adxHandle != INVALID_HANDLE) IndicatorRelease(adxHandle);
   if(emaHandle != INVALID_HANDLE) IndicatorRelease(emaHandle);
}

// ========== INDICATOR VALUES ==========
double GetATR()
{ double b[]; if(CopyBuffer(atrHandle,0,1,1,b)!=1) return 0; return b[0]; }
double GetADX()
{ double b[]; if(CopyBuffer(adxHandle,0,1,1,b)!=1) return 0; return b[0]; }
double GetEMA()
{ double b[]; if(CopyBuffer(emaHandle,0,1,1,b)!=1) return 0; return b[0]; }

double HighestHigh(int bars){ double hh=H(1); for(int i=2;i<=bars;i++) if(H(i)>hh) hh=H(i); return hh; }
double LowestLow(int bars){ double ll=L(1); for(int i=2;i<=bars;i++) if(L(i)<ll) ll=L(i); return ll; }

// ========== LOT CALCULATION ==========
double NormalizeLot(double lot)
{
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double minLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxLotBroker=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   lot=MathMax(minLot,MathMin(maxLotBroker,lot));
   lot=MathMin(lot,maxLot);
   lot=MathFloor(lot/step)*step;
   return NormalizeDouble(lot,2);
}

double CalculateLot(double sl, double entry)
{
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmt=bal*(riskPercent/100.0);
   double tickVal=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double pts=MathAbs(entry-sl)/tickSize;
   if(pts<=0) return SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double lot=riskAmt/(pts*tickVal);
   return NormalizeLot(lot);
}

// ========== SWING DETECTION (UNCHANGED) ==========
bool isPH(int s){ double m=H(s); for(int i=1;i<=zzPeriod;i++) if(H(s+i)>=m) return false; return true; }
bool isPL(int s){ double m=L(s); for(int i=1;i<=zzPeriod;i++) if(L(s+i)<=m) return false; return true; }

void Push(double price)
{
   if(pSize<MAX_SWINGS) pVals[pSize++]=price;
   else { for(int i=1;i<MAX_SWINGS;i++) pVals[i-1]=pVals[i]; pVals[MAX_SWINGS-1]=price; }
}

int GetMSS()
{
   if(pSize<5) return 0;
   if(pVals[pSize-1]>pVals[pSize-3]) return 1;
   if(pVals[pSize-2]<pVals[pSize-4]) return -1;
   return 0;
}

bool HasOpenPosition()
{
   for(int i=0;i<PositionsTotal();i++)
   { ulong t=PositionGetTicket(i); if(PositionSelectByTicket(t))
       if(PositionGetString(POSITION_SYMBOL)==_Symbol) return true; }
   return false;
}

// ========== NEW: SYMBOL GATE ==========
bool SymbolAllowed()
{
   string s = _Symbol;
   if(StringFind(s,"XAU")>=0 || StringFind(s,"GOLD")>=0) return TradeXAUUSD;
   if(StringFind(s,"BTC")>=0)                            return TradeBTCUSD;
   return true;  // any other symbol — allow (you can tighten this)
}

// ========== NEW: RISK GUARDS ==========
void UpdateDailyBaseline()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   if(dt.day_of_year != g_dayOfYear)
   {
      g_dayOfYear = dt.day_of_year;
      g_dailyBaseline = MathMax(AccountInfoDouble(ACCOUNT_BALANCE),
                                AccountInfoDouble(ACCOUNT_EQUITY));
   }
}

bool RiskGuardsPassed()
{
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double guardLevel = g_floor + g_initBalance*(ddBufferPct/100.0);
   if(eq <= guardLevel) return false;
   double dailyLossAbs = g_dailyBaseline - eq;
   if(dailyLossAbs >= g_dailyBaseline*(dailyBreakerPct/100.0)) return false;
   double dailyProfitAbs = eq - g_dailyBaseline;
   if(dailyProfitAbs >= g_dailyBaseline*(dailyProfitTargetPct/100.0)) return false;
   return true;
}

bool SpreadOK()
{ long sp=SymbolInfoInteger(_Symbol,SYMBOL_SPREAD); return sp<=maxSpreadPoints; }

bool InSession()
{
   if(!useSession) return true;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   return (dt.hour>=sessionStartHour && dt.hour<sessionEndHour);
}

bool NotRollover()
{
   if(!blockRollover) return true;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   int m=dt.hour*60+dt.min;
   if(m<=rolloverGuardMin) return false;
   if(m>=(1440-rolloverGuardMin)) return false;
   return true;
}

bool NewsClear()
{
   if(!useNewsFilter) return true;
   datetime from=TimeCurrent()-newsBufferMin*60;
   datetime to=TimeCurrent()+newsBufferMin*60;
   MqlCalendarValue values[];
   if(CalendarValueHistory(values,from,to,NULL,"USD")<=0) return true;
   for(int i=0;i<ArraySize(values);i++)
   {
      MqlCalendarEvent ev;
      if(CalendarEventById(values[i].event_id,ev))
         if(ev.importance==CALENDAR_IMPORTANCE_HIGH) return false;
   }
   return true;
}

// ========== TRAILING STOP (UNCHANGED) ==========
void UpdateTrailingStop()
{
   if(!useTrailingStop) return;
   double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   long stopLevel=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   long freezeLevel=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL);
   double minStopDist=stopLevel*tickSize;
   double minFreezeDist=freezeLevel*tickSize;
   for(int i=0;i<PositionsTotal();i++)
   {
      ulong ticket=PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      double entry=PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL=PositionGetDouble(POSITION_SL);
      double currentTP=PositionGetDouble(POSITION_TP);
      int type=(int)PositionGetInteger(POSITION_TYPE);
      double currentPrice=(type==POSITION_TYPE_BUY)?SymbolInfoDouble(_Symbol,SYMBOL_BID):SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      double profitPips=MathAbs(currentPrice-entry)/tickSize;
      if(profitPips>=breakevenPips && (currentSL==0 || (type==POSITION_TYPE_BUY && currentSL<entry) || (type==POSITION_TYPE_SELL && currentSL>entry)))
      {
         double beSL=(type==POSITION_TYPE_BUY)?entry+tickSize*10:entry-tickSize*10;
         if(MathAbs(beSL-currentPrice)>=minStopDist && MathAbs(beSL-currentPrice)>=minFreezeDist)
            trade.PositionModify(ticket,beSL,currentTP);
         continue;
      }
      if(profitPips>=trailStartPips)
      {
         double newSL=(type==POSITION_TYPE_BUY)?currentPrice-trailDistancePips*tickSize:currentPrice+trailDistancePips*tickSize;
         if((type==POSITION_TYPE_BUY && newSL<=currentSL)||(type==POSITION_TYPE_SELL && newSL>=currentSL)) continue;
         bool validSL=(type==POSITION_TYPE_BUY)?(newSL<currentPrice && (currentPrice-newSL)>=minStopDist && (currentPrice-newSL)>=minFreezeDist)
                                               :(newSL>currentPrice && (newSL-currentPrice)>=minStopDist && (newSL-currentPrice)>=minFreezeDist);
         if(validSL) trade.PositionModify(ticket,newSL,currentTP);
      }
   }
}

// ========== DAILY RESET ==========
void UpdateDailyProtection()
{
   if(!resetAtMidnight) return;
   datetime now=TimeTradeServer();
   MqlDateTime dtNow,dtReset;
   TimeToStruct(now,dtNow); TimeToStruct(lastResetTime,dtReset);
   if(dtNow.day!=dtReset.day || dtNow.mon!=dtReset.mon || dtNow.year!=dtReset.year)
   { dailyProfit=0.0; tradingHalted=false; tradesToday=0; lastResetTime=now; }
}

// ========== MAIN ONTICK ==========
void OnTick()
{
   UpdateDailyProtection();
   UpdateDailyBaseline();
   if(tradingHalted) return;
   UpdateTrailingStop();

   if(T(0)==lastBarTime) return;
   lastBarTime=T(0);

   if(pauseBars>0){ pauseBars--; return; }

   // ===== NEW: hard risk envelope (checked every bar before any trade logic) =====
   if(!SymbolAllowed())    return;
   if(!RiskGuardsPassed()) return;
   if(!SpreadOK())         return;
   if(!InSession())        return;
   if(!NotRollover())      return;
   if(!NewsClear())        return;
   // ============================================================================

   double atr=GetATR(); double adx=GetADX(); double ema=GetEMA();
   double close=C(1); double low=L(1); double high=H(1);

   // ========== 1. SWING MODE ==========
   bool newSwing=false;
   int s=1;
   bool ph=isPH(s); bool pl=isPL(s);
   if(dir==0){ if(ph){dir=1;cur_ext=H(s);} else if(pl){dir=-1;cur_ext=L(s);} }
   if(dir==1)
   { if(ph) cur_ext=H(s);
     if(pl && !ph){ Push(cur_ext); newSwing=true; dir=-1; cur_ext=L(s); } }
   else
   { if(pl) cur_ext=L(s);
     if(ph && !pl){ Push(cur_ext); newSwing=true; dir=1; cur_ext=H(s); } }

   if(pSize>=5)
   {
      double a=cur_ext, b=pVals[pSize-1], c=pVals[pSize-2];
      double fib=b+(a-b)*0.618;
      double buffer=atr*entryBufferATR;
      bool buy_cross=(low<=fib+buffer && close>fib);
      bool sell_cross=(high>=fib-buffer && close<fib);
      int mss=GetMSS();
      bool hl=(a>c), lh=(a<c);
      bool structure_active=(newSwing && mss!=0);
      bool allowBuy=(!structure_active||(hl&&mss==1));
      bool allowSell=(!structure_active||(lh&&mss==-1));
      if(!HasOpenPosition() && tradesToday<maxTradesPerDay)
      {
         if(dir==-1 && buy_cross && allowBuy)
         { double sl=c-(atr*atrMultiplier); double tp=close+(close-sl)*2; double lot=CalculateLot(sl,close);
           if(lot>0 && trade.Buy(lot,_Symbol,0,sl,tp)){ tradesToday++; } }
         else if(dir==1 && sell_cross && allowSell)
         { double sl=c+(atr*atrMultiplier); double tp=close-(sl-close)*2; double lot=CalculateLot(sl,close);
           if(lot>0 && trade.Sell(lot,_Symbol,0,sl,tp)){ tradesToday++; } }
      }
   }
   // ========== 2. TREND MODE ==========
   else if(adx>adxThreshold)
   {
      bool buy_trend=(close>ema && low<=ema);
      bool sell_trend=(close<ema && high>=ema);
      if(!HasOpenPosition() && tradesToday<maxTradesPerDay)
      {
         if(buy_trend)
         { double sl=close-(atr*atrMultiplier); double tp=close+(close-sl)*2; double lot=CalculateLot(sl,close);
           if(lot>0 && trade.Buy(lot,_Symbol,0,sl,tp)){ tradesToday++; } }
         else if(sell_trend)
         { double sl=close+(atr*atrMultiplier); double tp=close-(sl-close)*2; double lot=CalculateLot(sl,close);
           if(lot>0 && trade.Sell(lot,_Symbol,0,sl,tp)){ tradesToday++; } }
      }
   }
   // ========== 3. BREAKOUT MODE ==========
   else
   {
      double high20=HighestHigh(breakoutBars);
      double low20=LowestLow(breakoutBars);
      bool breakout_up=(close>high20*1.0005);
      bool breakout_down=(close<low20*0.9995);
      if(!HasOpenPosition() && tradesToday<maxTradesPerDay)
      {
         if(breakout_up)
         { double sl=low20-(atr*0.5); double tp=close+(close-sl)*2; double lot=CalculateLot(sl,close);
           if(lot>0 && trade.Buy(lot,_Symbol,0,sl,tp)){ tradesToday++; } }
         else if(breakout_down)
         { double sl=high20+(atr*0.5); double tp=close-(sl-close)*2; double lot=CalculateLot(sl,close);
           if(lot>0 && trade.Sell(lot,_Symbol,0,sl,tp)){ tradesToday++; } }
      }
   }
}

// ========== TRADE TRANSACTION (UNCHANGED) ==========
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &req,
                        const MqlTradeResult &res)
{
   if(trans.type==TRADE_TRANSACTION_DEAL_ADD && trans.deal>0)
   {
      double profit=HistoryDealGetDouble(trans.deal,DEAL_PROFIT);
      dailyProfit+=profit;
      if(profit<0)
      {
         consecutiveLoss++;
         if(consecutiveLoss>=2){ pauseBars=lossPauseCandles; consecutiveLoss=0; }
      }
      else if(profit>0) consecutiveLoss=0;
   }
}
