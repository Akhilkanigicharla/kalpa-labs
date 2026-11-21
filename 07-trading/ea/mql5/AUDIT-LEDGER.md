# Audit ledger · XAUUSD EA (master audit prompt, 21 Nov 2026)

Akhil's master prompt (`d2260730-attachment.txt`, 1,152 lines) says: inventory first, inspect every file, and no
code changes until the audit is documented. This ledger records what was received, what was covered, and what's
missing. Guard-layer findings: `AUDIT-2026-11-21.md`.

## 1. Every uploaded file (unique content)

| Upload | Lines | Kind | Purpose | Status |
|---|---|---|---|---|
| 5b464eda-XAUUSD_EA_Architecture.md | 857 | design | Phase 1: architecture, state machine, risk tiers, pseudo-code, risk review | Read in full; reviewed in `research/ea-design-gold-2026-11-21.md` (lot-size and stop-clamp bugs) |
| 75b2f0eb-attachment.txt | 449 | design | Same Phase 1 doc, cut off at section 9 | Superseded by the full version above |
| 09480b15 / abc7dcc0 / bc322874 / eba2cade-Phase3_Intelligence_Design.md | 790 | design (4 identical copies) | Phase 3 intelligence layer: 6 modules + entry gate | Read in full; gate measured on gold (A317) |
| 13b68662 / 5850c361 / 9b30eecb / dc6796f5-Phase2_Hardening_Report.md | 577 | report (4 identical copies) | Phase 2.5: 16 issues in the guard code | Read in full; status checked against the code (AUDIT, table "Hardening report") |
| af537a9b-Quantitative_EA_Guard_Modules_Agent_Prompt.md | 4,299 | prompt + **source** | Audit prompt plus 10 guard files (4,057 lines) | Source extracted to `Guards/`, every line read, audited |
| d2260730-attachment.txt | 1,152 | prompt | This master audit prompt (no source) | Read in full |
| 21 × image.png | — | images | Earlier reel screenshots | Not EA material |

## 2. Source inspection register

| File | Total | Inspected | Status | Findings |
|---|---|---|---|---|
| CDailyDrawdownGuard.mqh | 175 | 175 | Complete | M5, H8 |
| CSystemHealthCheck.mqh | 453 | 453 | Complete | H5, M8 |
| CGuardCoordinator.mqh | 794 | 794 | Complete | C1, C2, C3, H6, H7, H9, M7, L |
| GuardTypes.mqh | 645 | 645 | Complete | L1, L2 |
| CCooldownManager.mqh | 292 | 292 | Complete | M4, M5, M9 |
| CSpreadGuard.mqh | 478 | 478 | Complete | M1, M2, M4 |
| CCircuitBreaker.mqh | 319 | 319 | Complete | H1, H3 |
| CNewsGuard.mqh | 357 | 357 | Complete | H2, H3, M3 |
| CPropFirmGuard.mqh | 346 | 346 | Complete | H6, H7, H8 |
| CEquityGuard.mqh | 198 | 198 | Complete | H4 |
| **Total** | **4,057** | **4,057** | | 3 critical/top, 9 high, 9 medium, low/info |

## 3. Files the master prompt expects that were NOT supplied

| Area (prompt phase) | Missing files | Effect on the audit |
|---|---|---|
| EA entry point (2, 3.3) | `EA_XAUUSD.mq5` | Can't verify OnInit order (hardening CRITICAL-3), OnTick state switch, OnTimer, OnTradeTransaction, or whether guards run while suspended (C1) |
| Intelligence (4) | `IIntelligenceEngine`, `CIntelligenceCoordinator`, `IntelligenceTypes`, `CRegimeEngine`, `CRegimePersistenceModel`, `CLiquidityEngine`, `CStructureEngine`, `CTrendEngine`, `CVolatilityEngine` | Phase 4 can't be audited from code; only the design was tested (A317: gate open 2.2 % of hours) |
| Guards (5) | `CSessionGuard.mqh`, `CRolloverGuard.mqh` (slots 5–6) | Session/rollover blocking and HIGH-2 (MathSrand) unverified |
| Sizing & execution (6) | `CPositionSizer`, `CTradeCalculator`, `CEntryEngine`, `PriceUtils`, trade manager | Lot-size bug from the design (pip value 10–100× too big) can't be confirmed or cleared in code; pip size undefined (M6) |
| Persistence (8) | `CPersistence`, `CStateManager`, `CLogger`, `CDailyStats` | Daily reset, closed-vs-floating P&L (H8), state transitions unverified |
| Config (9) | `CConfig.mqh`, `Defines.mqh` | Thresholds (EquityFloor, ProfitTarget, SpreadHardCap, CB multipliers), `DeterministicRand`, enums unverified |
| Evidence (7) | Strategy Tester reports, broker symbol spec | No EA backtest exists; only our Python tests of the design |

## 4. Batch status

- **Done:** inventory; all 4,057 guard lines; design docs; hardening status; design backtests (A311/A315–A317).
- **Pending:** every file in section 3.
- **Compiler:** none here; nothing is claimed to compile.
- **Edge (phase 16):** THE EXISTING INFORMATION IS INSUFFICIENT TO ESTABLISH A STATISTICALLY VALIDATED TRADING EDGE.
  Evidence so far: design as written 0 trades in 2 yrs (H1); loosened +0.08R/trade, 118 trades, early half +0.02R;
  3-trade variant +0.05R. No out-of-sample or live proof.

## 5. Intelligence-layer audit prompt (2d8a0e40-attachment.txt, 758 lines, received 10:51 IST)
Read in full. It names 10 files (CVolatilityEngine 719, CDailyStats 237, IIntelligenceEngine 190,
CIntelligenceCoordinator 1,020, CRegimeEngine 764, CLiquidityEngine 1,281, CRegimePersistenceModel 689,
CStructureEngine 1,078, CTrendEngine 536, IntelligenceTypes 607 = 7,121 lines). **None of the source was attached**:
the upload holds only the instructions (no `#include`, no class code), and no `.mqh` exists anywhere on this machine.
Audit not started; waiting for the files. The prompt's last line is cut off mid-sentence ("…rather than guessing").
