
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Equity Guard                            |
//| File: Guards/CEquityGuard.mqh                                     |
//| Purpose: Tiered equity protection. Adaptive risk reduction.       |
//|           Sits between PropFirmGuard (hard floor) and daily limits.|
//| Phase: 2 — Guard Layer / Step 5                                   |
//|                                                                    |
//| GUARD SLOT: 3                                                      |
//| THREE TIERS:                                                       |
//|   Tier 1 ($9,500): WARNING only — no trading restriction          |
//|   Tier 2 ($9,300): PASS but with 50% size reduction               |
//|   Tier 3 ($9,200): Close open position + SUSPEND_EQUITY_PROTECT   |
//|                                                                    |
//| HYSTERESIS: Tier transitions require confirmation to prevent       |
//|   oscillation. Tier upgrade needs 2 consecutive PASS ticks.       |
//|   Tier downgrade is immediate (safety always wins).               |
//+------------------------------------------------------------------+
#ifndef CEQUITYGUARD_MQH
#define CEQUITYGUARD_MQH

#include "../Include/Defines.mqh"
#include "../Core/CLogger.mqh"
#include "../Core/CConfig.mqh"
#include "GuardTypes.mqh"

#define EQ_TIER1_BUFFER   500.0   // $500 above floor = Tier 1 warning
#define EQ_TIER2_BUFFER   700.0   // $700 above floor = Tier 2 reduce
#define EQ_TIER3_BUFFER   900.0   // $900 above floor = Tier 3 protect
// On $10K: Tier1=$9,500 Tier2=$9,300 Tier3=$9,100+200=$9,100+900?
// Recalculated: floor=$9,100. Tier3=floor+200=$9,300. Tier2=floor+400=$9,500.
// See Init() for dynamic calculation from Config.EquityFloor.
#define EQ_HYSTERESIS_TICKS 2     // Consecutive passes before tier upgrade

class CEquityGuard : public IGuard
{
private:
   EQUITY_TIER   m_current_tier;
   EQUITY_TIER   m_prev_tier;
   double        m_tier1_threshold;  // Warning
   double        m_tier2_threshold;  // Reduce sizing (50%)
   double        m_tier3_threshold;  // Close + suspend
   int           m_hysteresis_count; // Ticks at better tier before upgrading
   bool          m_tier3_triggered;  // Latched: Tier3 suspend is irreversible
                                     // until position closes and equity recovers

   EQUITY_TIER CalculateTier(double equity)
   {
      if(equity <= m_tier3_threshold) return EQUITY_TIER_PROTECT;
      if(equity <= m_tier2_threshold) return EQUITY_TIER_REDUCE;
      if(equity <= m_tier1_threshold) return EQUITY_TIER_WARNING;
      return EQUITY_TIER_NORMAL;
   }

public:
   CEquityGuard() :
      m_current_tier(EQUITY_TIER_NORMAL),
      m_prev_tier(EQUITY_TIER_NORMAL),
      m_tier1_threshold(0.0),   // Invalid until Init() — must not evaluate before Init
      m_tier2_threshold(0.0),
      m_tier3_threshold(0.0),
      m_hysteresis_count(0),
      m_tier3_triggered(false)
   {
      m_meta.index       = 3;
      m_meta.priority    = GPRIO_EQUITY;
      m_meta.name        = "EQUITY";
      m_meta.description = "Tiered equity curve protection";
      m_meta.enabled     = true;
   }

   virtual bool Init() override
   {
      // Compute thresholds dynamically from Config.EquityFloor
      // Floor = $9,100. Buffers above floor:
      //   Tier3 = floor + $200 = $9,300  (close + suspend)
      //   Tier2 = floor + $400 = $9,500  (50% sizing)
      //   Tier1 = floor + $700 = $9,800  (warning only)
      double floor = Config.EquityFloor;
      //--- A352 (26 Nov 2026): Tier 3 used to sit at floor + $200 ($9,500 on E8) and suspend until equity came
      //    back above it, which can never happen with no trades open -> a permanent stop at -5% while E8 allows -8%
      //    and the backtests trade on down to the $9,300 floor. Tier 3 now coincides with the floor itself
      //    (the floor guard closes everything there anyway); tiers 1-2 stay as early warnings.
      m_tier3_threshold = floor;
      m_tier2_threshold = floor + 200.0;
      m_tier1_threshold = floor + 400.0;

      m_meta.initialized = true;
      m_initialized      = true;

      Logger.Info("EQUITY",
         StringFormat("Initialized. tier1=%.0f tier2=%.0f tier3=%.0f floor=%.0f",
                      m_tier1_threshold, m_tier2_threshold,
                      m_tier3_threshold, floor));
      return true;
   }

   virtual GuardEvalResult Evaluate(const GuardContext &ctx) override
   {
      RecordEval();
      // Guard against Evaluate() called before Init()
      if(m_tier3_threshold <= 0.0)
      {
         Logger.Fatal("EQUITY",
            "Evaluate() called before Init() — thresholds are zero");
         return GuardFatal(GPRIO_EQUITY, m_meta.name, m_meta.index,
                           SUSPEND_SYSTEM_HEALTH,
                           "EquityGuard not initialized");
      }
      EQUITY_TIER new_tier = CalculateTier(ctx.equity);

      //--- TIER 3 — Close and suspend (SUSPEND with close_required)
      if(new_tier == EQUITY_TIER_PROTECT)
      {
         if(!m_tier3_triggered)
         {
            m_tier3_triggered = true;
            m_current_tier    = EQUITY_TIER_PROTECT;
            Logger.Critical("EQUITY",
               StringFormat("TIER 3 TRIGGERED: equity=%.2f <= threshold=%.2f "
                            "— closing position and suspending",
                            ctx.equity, m_tier3_threshold));
         }
         RecordTrigger(GUARD_SUSPEND);
         return GuardSuspend(GPRIO_EQUITY, m_meta.name, m_meta.index,
                             SUSPEND_EQUITY_PROTECT,
                             StringFormat("equity=%.2f <= tier3=%.2f",
                                          ctx.equity, m_tier3_threshold),
                             "Resumes when equity recovers above tier3 threshold",
                             true,   // close_required
                             true);  // alert_trader
      }

      // Tier3 was triggered but equity recovered (position closed)
      if(m_tier3_triggered && new_tier < EQUITY_TIER_PROTECT)
      {
         m_tier3_triggered = false;
         Logger.Info("EQUITY",
            StringFormat("Tier3 cleared: equity=%.2f recovered above %.2f",
                         ctx.equity, m_tier3_threshold));
      }

      //--- TIER 2 — Reduce sizing (PASS with modifier)
      if(new_tier == EQUITY_TIER_REDUCE)
      {
         if(m_current_tier != EQUITY_TIER_REDUCE)
         {
            m_current_tier = EQUITY_TIER_REDUCE;
            Logger.Warn("EQUITY",
               StringFormat("TIER 2: equity=%.2f — sizing reduced to 50%%",
                            ctx.equity));
         }
         RecordTrigger(GUARD_BLOCK); // Not really a block — using to count it
         return GuardPassReduced(GPRIO_EQUITY, m_meta.name, m_meta.index,
                                 0.50,
                                 StringFormat("equity=%.2f tier2 active",
                                              ctx.equity));
      }

      //--- TIER 1 — Warning only (PASS)
      if(new_tier == EQUITY_TIER_WARNING)
      {
         if(m_current_tier != EQUITY_TIER_WARNING)
         {
            m_current_tier = EQUITY_TIER_WARNING;
            Logger.Warn("EQUITY",
               StringFormat("TIER 1 WARNING: equity=%.2f — "
                            "approaching protection zone",
                            ctx.equity));
         }
         return GuardPass(GPRIO_EQUITY, m_meta.name, m_meta.index);
      }

      //--- NORMAL — Hysteresis on tier upgrade (prevents oscillation)
      if(m_current_tier != EQUITY_TIER_NORMAL)
      {
         m_hysteresis_count++;
         if(m_hysteresis_count >= EQ_HYSTERESIS_TICKS)
         {
            m_prev_tier        = m_current_tier;
            m_current_tier     = EQUITY_TIER_NORMAL;
            m_hysteresis_count = 0;
            Logger.Info("EQUITY",
               StringFormat("Recovered to NORMAL tier from %s. equity=%.2f",
                            EnumToString(m_prev_tier), ctx.equity));
         }
         // During hysteresis: still pass but don't upgrade tier yet
      }

      return GuardPass(GPRIO_EQUITY, m_meta.name, m_meta.index);
   }

   virtual bool CheckResume(const GuardContext &ctx) override
   {
      // Resume from SUSPEND_EQUITY_PROTECT when equity is above Tier3
      return (ctx.equity > m_tier3_threshold);
   }

   EQUITY_TIER GetCurrentTier() const { return m_current_tier; }
};

#endif // CEQUITYGUARD_MQH
