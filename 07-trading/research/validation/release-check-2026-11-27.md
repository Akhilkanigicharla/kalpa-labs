# Release check: gold EA kit for a live E8 Pro $10K MT5 account (27 Nov 2026)

Independent checker, no prior context, no login anywhere, nothing committed.
Scope: `ea/cloud/setup_mt5_free_cloud.sh`, `ea/cloud/README.md`, `ea/phase5/presets/*.set`, `ea/phase5/EA_XAUUSD/`.

## Pass 1: presets vs EA inputs and CConfig validation

All keys in the 3 presets exist as `input` declarations (scripted grep). Presets are ASCII only.

| E8 challenge line | Exists | Range check (CConfig.mqh) | Result |
|---|---|---|---|
| inp_Stage=1 | CConfig:38 | enum STAGE_STEP1=1 | OK |
| inp_Program=8 | CConfig:39 | enum PROGRAM_CLASSIC=8 | OK |
| inp_AccountSize=10000 | :40 | 1000..500000 | OK |
| inp_MinProfitDays=0 | :41 | 0..20 | OK |
| inp_FirmDailyLossPct=2.5 | :45 | 1.5..20 | OK; EA stop = min(1.5, 2.5-1) = 1.5% |
| inp_FirmMaxLossPct=8 | :46 | 2..30 | OK; auto floor $9,300 (E8 line $9,200) |
| inp_PropDailyStopPct=1.5 | :49 | 0.5..10 | OK |
| inp_DailyProfitCapPct=2.0 | :47 | 0..20 | OK |
| inp_MetalLeverage=15 | :48 | 1..500 | OK |
| inp_ProfitTarget=10850 | :60 | 10000..30000 | OK |
| inp_EquityFloor=0 | :59 | 0 = auto | OK |
| inp_MixRiskPct=0.30 | CMixEngine:32 | not validated | OK |
| inp_RiskPct=0.30 | :58 | 0.1..2.0 | OK |
| inp_WeekendLossBudgetPct=1.5 | :55 | 0.1..10 | OK |
| inp_DryRun=false | :103 | bool | **present**, real orders |

Funded preset: same plus Stage=3 (STAGE_FUNDED), ProfitTarget=0 (no target), FloorAfterPayoutPct=101 (CDailyStats:447, not range-checked, gives $10,100). The5ers preset: Program=10, firm limits 0 = table; all in range.

Inputs not in the preset, defaults judged for E8 $10K live:
- Symbol: EA takes the chart symbol and refuses non-XAU/GOLD (EA_XAUUSD.mq5:129). Setup default `SYMBOL=XAUUSD`; E8's gold name not verified, the README already says how to override.
- Timeframe: no code reads the chart period (timeframes are explicit), so `Period=H1` in the .ini is fine.
- Magic 20260522 with one-instance lock: fine for one account.
- inp_GmtOffset=3: live sessions and news use TimeGMT() (the VPS clock); the offset is only used in the tester and for a drift warning. Harmless live, but the VPS clock must be right (added to checklist).
- inp_DailyLossLimit=$300 is above E8's $250, but the 1.5% ($150) equity stop fires first. Harmless.
- inp_NewsBlockMin=120 / NewsDerisk: stricter than E8 (news allowed). Fine.
- inp_JumpBudgetPct=2.0, inp_MixMaxOpenRiskPct=2.0: inside the 2.5% daily line. Fine.
- inp_AllowOpposite=true: same-account hedging rule still UNVERIFIED (as in the 26 Nov audit).
- Account must be HEDGING or OnInit fails (EA_XAUUSD.mq5:159). E8 MT5 margin mode: UNVERIFIED; the README check now tells him to stop on a NETTING line.

## Pass 2: end-to-end simulation in /tmp

- Built `EA_XAUUSD_E8.zip` and the kit zip exactly as specified. Inner zip unzips to `phase5/EA_XAUUSD` (found by `find -maxdepth 3`) and `phase5/presets` (3 .set) = `PRESET_SRC`. Giving the whole kit zip also works (inner-zip fallback).
- `DRY_RUN=1 PRESET=E8_Pro_10K_challenge.set`: all 7 steps print. Compile: `MetaEditor64.exe /portable /compile:.../MQL5/Experts/EA_XAUUSD/EA_XAUUSD.mq5 /log:...`. Presets copied to `MT5_DIR/MQL5/Presets` (the folder MT5 reads `ExpertParameters` from in /portable mode).
- .ini: [Common] Login/Password/Server/KeepPrivate/NewsEnable; [Experts] AllowLiveTrading=1 etc.; [StartUp] `Expert=EA_XAUUSD\EA_XAUUSD`, `ExpertParameters=E8_Pro_10K_challenge.set`, `Symbol=XAUUSD`, `Period=H1`. Password read with `-s`, file chmod 600 owned by mt5. Server regex accepts `E8Markets-Server`.
- systemd: xvfb + mt5 (Restart=always, 30 s) + 5-minute watchdog timer.

Problems found and fixed:
1. **HIGH: demo state carried into E8.** EA state files (`EA_XAUUSD_propfirm_lock.txt`, daily, days, cooldown, CB, position) are not per account. If the demo hit the 10,850 target or a floor, the lock would block the live E8 account; same-day demo stats would also mix in. Fix: step 6 compares the old .ini login with the new one; on a new login step 7 moves `MQL5/Files/EA_XAUUSD_*.txt` to `old-account-<time>/`. Simulated: same login keeps the files, new login moves them, first run (no .ini) is fine.
2. **MEDIUM: an old chart could win over the new preset.** On restart MT5 restores the saved profile chart (old preset) and also opens the start-up chart; the EA's one-instance lock lets only the first one run, so a funded preset switch could keep the challenge settings. Fix: step 7 stops MT5 and deletes `MQL5/Profiles/Charts/*/chart*.chr` before the restart.

## Pass 3: README, live E8 route

Fixed:
3. The live step said "E8 emails an MT5 login". Now: buy E8 Pro $10K on MT5, E8X dashboard (e8x.e8markets.com) → account overview → key symbol → login, server (`E8Markets-Server`) and **master** password (not investor), exact re-run command, then the checks.
4. The verify step looked only in `MQL5/Logs`. "authorized on" and "loaded successfully" lines are in the terminal journal `Logs/`. The new command greps both logs and says what counts as stop.
5. No go-live checklist. Added: server clock (`timedatectl` synchronized), first trades have a stop-loss and a small size (with a stop action), one account only (not on PC, not on a second E8 account, no manual trades), and DryRun=false means real orders.

Sources (fetched 27 Nov 2026): E8 help "How to log in to your MT5 account?" https://help.e8markets.com/en/articles/12414114 (credentials from the dashboard, server `E8Markets-Server`); E8 help "How to log in to E8 Terminal" https://intercom.help/e8/en/articles/16734784 (account overview → "the key symbol"). That the key symbol shows the MT5 master password is confirmed only through that second page: UNVERIFIED for MT5 accounts specifically.

## Remaining risks (not fixable here)
- The generic MetaQuotes installer may not list `E8Markets-Server`. E8's page says that if the server can't be found, search for it under "Open an Account". If the journal shows no "authorized on E8Markets-Server", the next step is to switch to E8's own installer (`e8markets5setup.exe`). That needs a path change and a real test.
- E8 hedging/netting mode, gold symbol name and spread: unverified. The first-run log check will catch these.
- MT5 under Wine/Hangover is still untested on a real server (as noted 26 Nov).

## Tests
`bash tests/test_cloud_setup.sh` → "cloud setup checks passed"; `python3 -m pytest -q tests` → 285 passed. `bash -n` OK.
