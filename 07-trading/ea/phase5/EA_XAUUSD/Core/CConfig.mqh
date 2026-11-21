
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
input group "=== ACCOUNT & RISK ==="
input double   inp_RiskPct         = 0.75;   // Risk per trade (%)
input double   inp_EquityFloor     = 9100.0; // Hard equity floor ($)
input double   inp_ProfitTarget    = 11000.0;// Profit target (equity $): The5%ers High Stakes New step 1 = 10% (11,000); Classic = 8% (10,800); step 2 = 5% (10,500)
input double   inp_DailyLossLimit  = 300.0;  // Daily self-imposed loss ($)
input int      inp_MaxDailyTrades  = 3;      // Max trades per calendar day
input double   inp_LotHardCap      = 0.10;   // Maximum lot size ever

input group "=== SESSION & TIMING ==="
input int      inp_GmtOffset       = 3;      // Broker server GMT offset (hrs)
input int      inp_LondonStartHr   = 7;      // London session start (GMT)
input int      inp_LondonEndHr     = 12;     // London session end (GMT)
input int      inp_NyStartHr       = 13;     // NY session start (GMT)
input int      inp_NyEndHr         = 17;     // NY session end (GMT)
input int      inp_RolloverStartHr = 21;     // Rollover blackout start (GMT)
input int      inp_RolloverStartMn = 45;     // Rollover blackout start (min)
input int      inp_RolloverEndHr   = 0;      // Rollover blackout end (GMT)
input int      inp_RolloverEndMn   = 15;     // Rollover blackout end (min)

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

   //--- Constructor
   CConfig() : m_valid(false) {}

   //--- Validate and copy all inputs
   //    Returns false and halts EA if any input is invalid
   bool Init()
   {
      bool ok = true;

      // Copy and validate each input
      ok &= ValidateDouble(inp_RiskPct,        0.1,  2.0,   "RiskPct");
      ok &= ValidateDouble(inp_EquityFloor,     1000, 50000, "EquityFloor");
      ok &= ValidateDouble(inp_ProfitTarget,    1000, 50000, "ProfitTarget");
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

      if(!ok) return false;

      // Copy validated values
      RiskPct         = inp_RiskPct / 100.0; // Convert % to fraction
      EquityFloor     = inp_EquityFloor;
      ProfitTarget    = inp_ProfitTarget;
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

      m_valid = true;
      Logger.Info("CONFIG", "Configuration validated successfully",
         StringFormat("risk_pct=%.4f equity_floor=%.2f target=%.2f magic=%lld",
                      RiskPct, EquityFloor, ProfitTarget, MagicNumber));
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

//--- A327: the EA's own magic or one of the mix strategies' magics
bool IsOurMagic(long m)
{
   return m == Config.MagicNumber ||
          (m >= Config.MagicNumber + MIX_MAGIC_OFFSET && m < Config.MagicNumber + MIX_MAGIC_OFFSET + MIX_MAGIC_SPAN);
}

#endif // CCONFIG_MQH
