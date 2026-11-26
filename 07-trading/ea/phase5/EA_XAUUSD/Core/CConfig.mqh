
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Configuration Manager                   |
//| File: Core/CConfig.mqh                                            |
//| Purpose: Centralised input handling + validation.                 |
//|           All external inputs read ONCE at OnInit().              |
//|           All modules read from CConfig — NEVER from input vars.  |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CCONFIG_MQH
#define CCONFIG_MQH
#include "../Include/Defines.mqh"
#include "CLogger.mqh"

//===================================================================
// PSEUDO-CODE DESIGN
//
// All EA input variables are declared here in one place.
// CConfig.Init() validates each value is within acceptable range.
// Any out-of-range value is rejected and EA halts.
// This prevents "silently wrong" configuration at runtime.
//
// Every module receives a const pointer/reference to CConfig —
// they read values but never modify them.
//
// Rationale for centralization:
//   Scattered input variables create hidden dependencies.
//   One config object makes every dependency explicit.
//   Validation at startup = no silent failure mid-session.
//===================================================================

//--- All user-facing inputs declared as extern for MT5 input panel
//--- A335: The5%ers High Stakes stage-aware limits (targets, floor and 3 profitable days set themselves)
enum ENUM_5ERS_STAGE   { STAGE_STEP1 = 1, STAGE_STEP2 = 2, STAGE_FUNDED = 3 };
enum ENUM_5ERS_PROGRAM { PROGRAM_NEW = 10, PROGRAM_CLASSIC = 8 };

input group "=== THE5%ERS ACCOUNT (A335) ==="
input ENUM_5ERS_STAGE   inp_Stage         = STAGE_STEP1;   // Stage: Step 1 / Step 2 / Funded
input ENUM_5ERS_PROGRAM inp_Program       = PROGRAM_NEW;   // High Stakes New (Step 1 = 10%) or Classic (8%)
input double            inp_AccountSize   = 10000.0;       // Starting balance of this account ($)
input int               inp_MinProfitDays = 3;             // The5%ers: profitable days needed per step
input double            inp_ProfitDayPct  = 0.5;           // A profitable day = min(midnight balance, equity) - previous day balance >= this % of start

input group "=== LIVE SAFETY (A336) ==="
input double   inp_FirmDailyLossPct     = 0.0;   // Prop firm daily loss limit (%). 0 = The5%ers table: 5% (<$50K), 4% ($50K+)
input double   inp_FirmMaxLossPct       = 0.0;   // Prop firm max loss, static from initial balance (%). 0 = The5%ers table: 10% (<$50K), 8% ($50K+)
input double   inp_DailyProfitCapPct    = 0.0;   // A337: close all + stop for the day once equity is this % of account size above the day base. 0 = off (The5%ers). E8 Pro = 2.0
input double   inp_MetalLeverage        = 25.0;  // A337: firm leverage for gold, used as a margin floor (The5%ers 1:25, E8 Pro 1:15)
input double   inp_PropDailyStopPct     = 4.0;   // Close all + pause when equity falls this % below the day base (max(balance,equity) at 00:00 server). Capped at firm limit - 1%
input double   inp_FridayMaxOpenRiskPct = 1.25;  // Friday after inp_FridayCutHour: max total open risk held into the weekend (% equity)
input int      inp_FridayCutHour        = 22;    // Friday cut hour (SERVER time): cancel pendings, shrink open risk, no new entries until Monday
input int      inp_MaxOpenPositions     = 0;     // Max open positions + pendings across ALL our magics; 0 = no limit (re-test: a cap of 3 cut ~850 good trades). Set e.g. 3 if a firm needs it
input bool     inp_AllowOpposite        = true;  // false = never hold a long and a short together (switch off if a firm treats it as hedging)
input double   inp_WeekendGapPct        = 3.75;  // Weekend gap assumed when sizing Friday holds (% of price). Gold 2008-2026: worst 3.56%, p99 2.04%
input double   inp_WeekendLossBudgetPct = 3.0;   // Max worst-case weekend loss of all held positions (% of max(balance, equity))

input group "=== ACCOUNT & RISK ==="
input double   inp_RiskPct         = 0.40;   // Risk per trade (%), x inp_MainWeight (0.5) = 0.20% effective. A336 quant re-test scenario G
input double   inp_EquityFloor     = 0.0;    // Hard equity floor ($); 0 = auto: 91% of account size
input double   inp_ProfitTarget    = 0.0;    // Profit target ($); 0 = auto from stage/program (Step 1 New 10%, Classic 8%, Step 2 5%, Funded none)
input double   inp_DailyLossLimit  = 300.0;  // Daily self-imposed loss ($)
input int      inp_MaxDailyTrades  = 3;      // Max trades per calendar day
input double   inp_LotHardCap      = 0.10;   // Maximum lot size ever

input group "=== SESSION & TIMING ==="
input int      inp_GmtOffset       = 3;      // Broker server GMT offset (hrs)
input int      inp_LondonStartHr   = 7;      // London session start (GMT)
input int      inp_LondonEndHr     = 12;     // London session end (GMT)
input int      inp_NyStartHr       = 13;     // NY session start (GMT)
input int      inp_NyEndHr         = 17;     // NY session end (GMT)
input int      inp_RolloverStartHr = 23;     // A336: rollover blackout start (SERVER time, hour)
input int      inp_RolloverStartMn = 50;     // A336: rollover blackout start (SERVER time, min)
input int      inp_RolloverEndHr   = 0;      // A336: rollover blackout end (SERVER time, hour)
input int      inp_RolloverEndMn   = 20;     // A336: rollover blackout end (SERVER time, min)

input group "=== SPREAD & SLIPPAGE ==="
input double   inp_SpreadHardCap   = 0.80;   // Spread hard cap (pips; 1 pip = $1 -> $0.80)
input double   inp_SlippageMax     = 0.50;   // Max entry slippage (pips; $0.50)
input double   inp_RealRRMin       = 1.5;    // Minimum real RR after spread

input group "=== STOP LOSS & TARGETS ==="
input double   inp_SLPipsMin       = 30.0;   // Minimum SL distance (pips)
input double   inp_SLPipsMax       = 80.0;   // Maximum SL distance (pips)
input double   inp_SLAtrMult       = 1.5;    // SL = ATR × multiplier
input double   inp_TP1RR           = 1.5;    // TP1 risk:reward
input double   inp_TP2RR           = 2.5;    // TP2 risk:reward
input double   inp_TrailAtrMult    = 0.75;   // Trail = ATR × multiplier
input double   inp_TrailMinPips    = 20.0;   // Trail minimum (pips)
input double   inp_TrailMaxPips    = 50.0;   // Trail maximum (pips)

input group "=== REGIME & INTELLIGENCE ==="
input int      inp_RegimeMinScore  = 3;      // H4 regime minimum score
input int      inp_ATRPeriod       = 14;     // ATR period (all timeframes)
input int      inp_EMA_Fast        = 20;     // Fast EMA period
input int      inp_EMA_Slow        = 50;     // Slow EMA period
input int      inp_EMA_200         = 200;    // Long-term EMA period

input group "=== SCORING ==="
input double   inp_ScoreThreshNorm = 6.5;    // Normal entry threshold (legacy 0-10)
input int      inp_TradeScoreMin    = 55;     // Phase 4 min quality score (0-100)
input double   inp_PullbackMaxPips  = 25.0;   // Max pullback distance to EMA20 (pips)
input bool     inp_SweepGateOn      = true;   // Reject entries into opposing fresh sweep
input bool     inp_DryRun           = true;   // Phase 5: log intended orders, do NOT send
input double   inp_ScoreThreshCons = 7.5;    // Conservative threshold

input group "=== EXECUTION RANDOMIZATION ==="
input int      inp_JitterMinSec    = 12;     // Min entry delay (seconds)
input int      inp_JitterMaxSec    = 90;     // Max entry delay (seconds)
input bool     inp_EnableJitter    = true;   // Enable timing randomization

input group "=== CIRCUIT BREAKER ==="
input double   inp_CBSpikeMultATR  = 2.5;   // ATR spike multiplier
input double   inp_CBExpandMultATR = 1.8;   // Expansion multiplier
input double   inp_CBVelocityPips  = 40.0;  // Velocity trigger (pips/2min)
input int      inp_CBCooldownSec   = 1200;  // Default cooldown (20 min)

input group "=== LOGGING ==="
input bool     inp_ProductionMode  = true;   // true = no DEBUG/TRACE logs
input bool     inp_EnableCSVLog    = true;   // Write trade_log.csv

input group "=== MANUAL CONTROLS ==="
input bool     inp_ManualSuspend   = false;  // true = suspend all trading
input bool     inp_ManualReset     = false;  // true = clear prop-firm lock (use with care)

input group "=== MAGIC & IDENTITY ==="
input long     inp_MagicNumber     = 20260522; // EA identifier for orders
input string   inp_AccountComment  = "";       // Optional trader note

//===================================================================
// CONFIG CLASS
//===================================================================
class CConfig
{
private:
   bool m_valid;

   bool ValidateDouble(double val, double vmin, double vmax, string name)
   {
      if(val < vmin || val > vmax)
      {
         Logger.Fatal("CONFIG",
            StringFormat("Invalid %s=%.4f — must be %.4f..%.4f",
                         name, val, vmin, vmax));
         return false;
      }
      return true;
   }

   bool ValidateInt(int val, int vmin, int vmax, string name)
   {
      if(val < vmin || val > vmax)
      {
         Logger.Fatal("CONFIG",
            StringFormat("Invalid %s=%d — must be %d..%d",
                         name, val, vmin, vmax));
         return false;
      }
      return true;
   }

public:
   //--- Validated copies of inputs (read by modules)
   double   RiskPct;
   double   EquityFloor;
   double   ProfitTarget;
   double   DailyLossLimit;
   int      MaxDailyTrades;
   double   LotHardCap;

   int      GmtOffset;
   int      LondonStartHr;
   int      LondonEndHr;
   int      NyStartHr;
   int      NyEndHr;
   int      RolloverStartHr;
   int      RolloverStartMn;
   int      RolloverEndHr;
   int      RolloverEndMn;

   double   SpreadHardCap;
   double   SlippageMax;
   double   RealRRMin;

   double   SLPipsMin;
   double   SLPipsMax;
   double   SLAtrMult;
   double   TP1RR;
   double   TP2RR;
   double   TrailAtrMult;
   double   TrailMinPips;
   double   TrailMaxPips;

   int      RegimeMinScore;
   int      ATRPeriod;
   int      EMA_Fast;
   int      EMA_Slow;
   int      EMA_200;

   double   ScoreThreshNorm;
   double   ScoreThreshCons;
   int      TradeScoreMin;
   double   PullbackMaxPips;
   bool     SweepGateOn;
   bool     DryRun;

   int      JitterMinSec;
   int      JitterMaxSec;
   bool     EnableJitter;

   double   CBSpikeMultATR;
   double   CBExpandMultATR;
   double   CBVelocityPips;
   int      CBCooldownSec;

   bool     ProductionMode;
   bool     EnableCSVLog;

   long     MagicNumber;
   bool     ManualSuspend;
   bool     ManualReset;

   //--- A336: firm limits for this account size, the EA's own daily stop, account-size check
   double   FirmDailyPct;      // The5%ers daily loss limit (%): 5 up to $25K, 4 for $50K/$100K
   double   FirmMaxPct;        // The5%ers max loss (%): 10 up to $25K, 8 for $50K/$100K
   double   DailyStopPct;      // EA daily stop (%), always at least 1% inside FirmDailyPct
   bool     AccountSizeOk;     // false = inp_AccountSize does not match the real balance -> no new trades

   //--- Constructor
   CConfig() : m_valid(false), FirmDailyPct(5.0), FirmMaxPct(10.0), DailyStopPct(4.0), AccountSizeOk(false) {}

   //--- Validate and copy all inputs
   //    Returns false and halts EA if any input is invalid
   bool Init()
   {
      bool ok = true;

      // Copy and validate each input
      ok &= ValidateDouble(inp_RiskPct,        0.1,  2.0,   "RiskPct");
      ok &= ValidateDouble(inp_AccountSize,     1000, 500000, "AccountSize");
      ok &= ValidateInt(   inp_MinProfitDays,   0,    20,    "MinProfitDays");
      ok &= ValidateDouble(inp_ProfitDayPct,    0.0,  5.0,   "ProfitDayPct");
      if(inp_EquityFloor  != 0) ok &= ValidateDouble(inp_EquityFloor,  0.5 * inp_AccountSize, 2.0 * inp_AccountSize, "EquityFloor");   // above size: E8 Pro after 1st payout (floor = initial balance)
      if(inp_ProfitTarget != 0) ok &= ValidateDouble(inp_ProfitTarget, inp_AccountSize, 3 * inp_AccountSize, "ProfitTarget");
      ok &= ValidateDouble(inp_DailyLossLimit,  50,   2000,  "DailyLossLimit");
      ok &= ValidateInt(   inp_MaxDailyTrades,  1,    10,    "MaxDailyTrades");
      ok &= ValidateDouble(inp_LotHardCap,      0.01, 1.0,   "LotHardCap");
      ok &= ValidateInt(   inp_GmtOffset,       -12,  14,    "GmtOffset");
      ok &= ValidateDouble(inp_SpreadHardCap,   0.1,  5.0,   "SpreadHardCap");
      ok &= ValidateDouble(inp_SlippageMax,     0.05, 5.0,   "SlippageMax");
      ok &= ValidateDouble(inp_SLPipsMin,       10.0, 200.0, "SLPipsMin");
      ok &= ValidateDouble(inp_SLPipsMax,       inp_SLPipsMin+1, 500.0, "SLPipsMax");
      ok &= ValidateDouble(inp_TP1RR,           0.5,  5.0,   "TP1RR");
      ok &= ValidateDouble(inp_TP2RR,           inp_TP1RR+0.1, 10.0, "TP2RR");
      ok &= ValidateDouble(inp_ScoreThreshNorm, 1.0,  9.9,   "ScoreThreshNorm");
      ok &= ValidateInt(   inp_JitterMinSec,    0,    300,   "JitterMinSec");
      ok &= ValidateInt(   inp_JitterMaxSec,    inp_JitterMinSec, 600, "JitterMaxSec");
      ok &= ValidateInt(   inp_ATRPeriod,       5,    50,    "ATRPeriod");
      ok &= ValidateInt(   inp_EMA_Fast,        5,    100,   "EMA_Fast");
      ok &= ValidateInt(   inp_EMA_Slow,        inp_EMA_Fast+1, 300, "EMA_Slow");
      // A336 live-safety inputs
      ok &= ValidateDouble(inp_PropDailyStopPct,     0.5,  10.0, "PropDailyStopPct");
      ok &= ValidateDouble(inp_DailyProfitCapPct,    0.0,  20.0, "DailyProfitCapPct");
      ok &= ValidateDouble(inp_MetalLeverage,        1.0, 500.0, "MetalLeverage");
      if(inp_FirmDailyLossPct != 0) ok &= ValidateDouble(inp_FirmDailyLossPct, 1.5, 20.0, "FirmDailyLossPct");
      if(inp_FirmMaxLossPct   != 0) ok &= ValidateDouble(inp_FirmMaxLossPct,   2.0, 30.0, "FirmMaxLossPct");
      ok &= ValidateDouble(inp_FridayMaxOpenRiskPct, 0.0,  5.0,  "FridayMaxOpenRiskPct");
      ok &= ValidateInt(   inp_FridayCutHour,        0,    23,   "FridayCutHour");
      ok &= ValidateInt(   inp_MaxOpenPositions,     0,    50,   "MaxOpenPositions");
      ok &= ValidateDouble(inp_WeekendGapPct,        0.5,  20.0, "WeekendGapPct");
      ok &= ValidateDouble(inp_WeekendLossBudgetPct, 0.1,  10.0, "WeekendLossBudgetPct");
      ok &= ValidateInt(   inp_RolloverStartHr,      0,    23,   "RolloverStartHr");
      ok &= ValidateInt(   inp_RolloverStartMn,      0,    59,   "RolloverStartMn");
      ok &= ValidateInt(   inp_RolloverEndHr,        0,    23,   "RolloverEndHr");
      ok &= ValidateInt(   inp_RolloverEndMn,        0,    59,   "RolloverEndMn");

      if(!ok) return false;

      // A336 (G9): firm limits are inputs (any prop firm); 0 = The5%ers High Stakes table:
      //            $50K/$100K use 4% daily / 8% max, smaller sizes 5% / 10%
      FirmDailyPct    = (inp_FirmDailyLossPct > 0) ? inp_FirmDailyLossPct : ((inp_AccountSize >= 50000.0) ? 4.0 : 5.0);
      FirmMaxPct      = (inp_FirmMaxLossPct   > 0) ? inp_FirmMaxLossPct   : ((inp_AccountSize >= 50000.0) ? 8.0 : 10.0);
      DailyStopPct    = MathMin(inp_PropDailyStopPct, FirmDailyPct - 1.0);

      // A336 (#11 / G4): refuse to trade if inp_AccountSize does not match the real account
      AccountSizeOk   = true;
      double bal_now  = AccountInfoDouble(ACCOUNT_BALANCE);
      if(inp_Stage != STAGE_FUNDED && MathAbs(bal_now - inp_AccountSize) / inp_AccountSize > 0.15)
      {
         AccountSizeOk = false;
         Logger.Error("CONFIG",
            "ACCOUNT SIZE MISMATCH - no new trades until inp_AccountSize is fixed",
            StringFormat("balance=%.2f inp_AccountSize=%.2f (more than 15%% apart)", bal_now, inp_AccountSize));
         Alert(EA_NAME, ": inp_AccountSize does not match the account balance - EA will NOT open trades. Fix the input.");
      }

      // Copy validated values
      RiskPct         = inp_RiskPct / 100.0; // Convert % to fraction
      // Floor = initial balance x (1 - firm max% + 1% buffer): The5%ers 91% up to $25K
      //        (inp_AccountSize * 0.91), 93% for $50K/$100K
      EquityFloor     = (inp_EquityFloor != 0) ? inp_EquityFloor
                      : inp_AccountSize * (1.0 - (FirmMaxPct - 1.0) / 100.0);
      double tgt_pct  = (inp_Stage == STAGE_STEP1) ? (double)inp_Program : ((inp_Stage == STAGE_STEP2) ? 5.0 : 0.0);
      ProfitTarget    = (inp_ProfitTarget != 0) ? inp_ProfitTarget
                      : ((tgt_pct > 0) ? inp_AccountSize * (1.0 + tgt_pct / 100.0) : 1e12);   // funded: no target
      DailyLossLimit  = inp_DailyLossLimit;
      MaxDailyTrades  = inp_MaxDailyTrades;
      LotHardCap      = inp_LotHardCap;

      GmtOffset       = inp_GmtOffset;
      LondonStartHr   = inp_LondonStartHr;
      LondonEndHr     = inp_LondonEndHr;
      NyStartHr       = inp_NyStartHr;
      NyEndHr         = inp_NyEndHr;
      RolloverStartHr = inp_RolloverStartHr;
      RolloverStartMn = inp_RolloverStartMn;
      RolloverEndHr   = inp_RolloverEndHr;
      RolloverEndMn   = inp_RolloverEndMn;

      SpreadHardCap   = inp_SpreadHardCap;
      SlippageMax     = inp_SlippageMax;
      RealRRMin       = inp_RealRRMin;

      SLPipsMin       = inp_SLPipsMin;
      SLPipsMax       = inp_SLPipsMax;
      SLAtrMult       = inp_SLAtrMult;
      TP1RR           = inp_TP1RR;
      TP2RR           = inp_TP2RR;
      TrailAtrMult    = inp_TrailAtrMult;
      TrailMinPips    = inp_TrailMinPips;
      TrailMaxPips    = inp_TrailMaxPips;

      RegimeMinScore  = inp_RegimeMinScore;
      ATRPeriod       = inp_ATRPeriod;
      EMA_Fast        = inp_EMA_Fast;
      EMA_Slow        = inp_EMA_Slow;
      EMA_200         = inp_EMA_200;

      ScoreThreshNorm = inp_ScoreThreshNorm;
      TradeScoreMin   = inp_TradeScoreMin;
      PullbackMaxPips = inp_PullbackMaxPips;
      SweepGateOn     = inp_SweepGateOn;
      DryRun          = inp_DryRun;
      ScoreThreshCons = inp_ScoreThreshCons;

      JitterMinSec    = inp_JitterMinSec;
      JitterMaxSec    = inp_JitterMaxSec;
      EnableJitter    = inp_EnableJitter;

      CBSpikeMultATR  = inp_CBSpikeMultATR;
      CBExpandMultATR = inp_CBExpandMultATR;
      CBVelocityPips  = inp_CBVelocityPips;
      CBCooldownSec   = inp_CBCooldownSec;

      ProductionMode  = inp_ProductionMode;
      EnableCSVLog    = inp_EnableCSVLog;
      MagicNumber     = inp_MagicNumber;
      ManualSuspend   = inp_ManualSuspend;
      ManualReset     = inp_ManualReset;

      // Derived sanity checks
      if(EquityFloor >= ProfitTarget)
      {
         Logger.Fatal("CONFIG",
            "EquityFloor must be less than ProfitTarget",
            StringFormat("floor=%.2f target=%.2f", EquityFloor, ProfitTarget));
         return false;
      }

      // A336: an explicit floor must never sit below the firm's max-loss line
      if(EquityFloor <= inp_AccountSize * (1.0 - FirmMaxPct / 100.0))
      {
         Logger.Fatal("CONFIG", "EquityFloor is at or below the firm max-loss line",
            StringFormat("floor=%.2f firm_line=%.2f", EquityFloor, inp_AccountSize * (1.0 - FirmMaxPct / 100.0)));
         return false;
      }

      m_valid = true;
      Logger.Info("CONFIG", "Configuration validated successfully",
         StringFormat("risk_pct=%.4f equity_floor=%.2f target=%.2f magic=%I64d firm_daily=%.1f%% ea_daily_stop=%.1f%% size_ok=%d",
                      RiskPct, EquityFloor, ProfitTarget, MagicNumber, FirmDailyPct, DailyStopPct, (int)AccountSizeOk));
      return true;
   }

   bool IsValid() const { return m_valid; }

   // Convert pips to price points for XAUUSD
   // For XAUUSD: 1 pip = 0.01 (2nd decimal) when digit=2
   // MT5 normalizes: use SymbolInfoDouble to get actual
   // This helper wraps the conversion (set in PriceUtils)
   double PipsToPoints(double pips) const
   {
      // A320: pips -> broker points using the single pip definition
      double pt = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      if(pt <= 0) return 0;
      return pips * inp_PipSizePrice / pt;
   }
};

//--- Global singleton
CConfig Config;

//--- A336: CountProfitableDays() and StageRiskMult() moved to Core/CDailyStats.mqh (official
//    The5%ers formula from per-day midnight snapshots).

//--- A336 (#20): one clock per purpose.
//    The firm's day, rollover and the Friday cut use SERVER time (TimeTradeServer).
//    London/NY sessions are defined in GMT: live = TimeGMT(); in the Strategy Tester TimeGMT()
//    equals server time, so derive GMT from server time minus inp_GmtOffset there.
datetime EAGmtNow()
{
   if(MQLInfoInteger(MQL_TESTER)) return TimeTradeServer() - (datetime)(Config.GmtOffset * 3600);
   return TimeGMT();
}

int ServerMinuteOfDay()
{
   MqlDateTime s;
   TimeToStruct(TimeTradeServer(), s);
   return s.hour * 60 + s.min;
}

int ServerDayOfWeek()
{
   MqlDateTime s;
   TimeToStruct(TimeTradeServer(), s);
   return s.day_of_week;                       // 0 = Sunday ... 5 = Friday, 6 = Saturday
}

//--- A336 (#2): Friday after inp_FridayCutHour (server) until the market reopens on Monday
bool WeekendCutActive()
{
   MqlDateTime s;
   TimeToStruct(TimeTradeServer(), s);
   if(s.day_of_week == 6 || s.day_of_week == 0) return true;
   return (s.day_of_week == 5 && s.hour >= inp_FridayCutHour);
}

//--- A327: the EA's own magic or one of the mix strategies' magics
bool IsOurMagic(long m)
{
   return m == Config.MagicNumber ||
          (m >= Config.MagicNumber + MIX_MAGIC_OFFSET && m < Config.MagicNumber + MIX_MAGIC_OFFSET + MIX_MAGIC_SPAN);
}

#endif // CCONFIG_MQH
