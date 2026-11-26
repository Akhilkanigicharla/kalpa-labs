# Setup kit review: free-cloud MT5 + gold EA (26 Nov 2026)

Independent review of `07-trading/ea/cloud/setup_mt5_free_cloud.sh` and `README.md`, with the kit layout as shipped: `EA_XAUUSD_E8.zip` (phase5/EA_XAUUSD + phase5/presets + CHANGES md) inside a kit zip with the script and README. Nothing was installed and no account was used. Web pages were treated as data.

## Pass 1: script correctness

| Check | Result |
|---|---|
| `bash -n`, `shellcheck -S warning`, `07-trading/tests/test_cloud_setup.sh` | pass (before and after the fixes) |
| `DRY_RUN=1` | prints all 7 steps; skips the root check, unzip, compile, login prompt and systemd. Bad `PRESET` is rejected |
| Zip found, layout A (zip made inside phase5/: `EA_XAUUSD/`, `presets/`) | simulated in /tmp: finds `EA_XAUUSD/EA_XAUUSD.mq5` and `presets/` (3 .set) |
| Zip found, layout B (paths `phase5/EA_XAUUSD`, `phase5/presets`) | finds both |
| The **kit** zip given by mistake | before: FAIL "EA folder not found". **Fixed:** opens the EA zip inside it |
| `sudo PRESET=... bash script` | works: sudoers man page says the SETENV tag is implied when the matched command is ALL (Ubuntu cloud user has ALL); tested locally with sudo |
| `.ini` keys | match the MT5 help page: [Common] Login/Password/Server/KeepPrivate/NewsEnable, [Experts] AllowLiveTrading/AllowDllImport/Enabled/Account/Profile, [StartUp] Expert/ExpertParameters/Symbol/Period. `Expert=EA_XAUUSD\EA_XAUUSD` (heredoc gives one backslash, checked) is relative to MQL5\Experts |
| ExpertParameters file location | MT5 help: must be in `MQL5\Presets` of the data folder. `/portable` makes the data folder the install folder, and the script copies presets to `MT5_DIR/MQL5/Presets` and fails if the chosen preset is missing. Correct |
| EA includes | all relative (`"Core/..."`) plus `<Trade/Trade.mqh>` (stock); compiles from MQL5/Experts/EA_XAUUSD |
| Password file | `umask 077`, `chown mt5`, `chmod 600`. OK. **Fixed:** `IFS= read` so a password with leading/trailing spaces is kept |
| **Watchdog** | **Bug, fixed.** `sh -c 'pgrep -f terminal64.exe ...'` matched its own `sh` command line, so it never restarted MT5 (reproduced). Now `pgrep -f "[t]erminal64[.]exe"` |
| **Re-run with a new login / preset / EA** | **Bug, fixed.** `systemctl enable --now` does not restart a running service, so switching to the E8 login would have kept MT5 on the old demo account. Now `enable` + `restart` |
| **Temporary Xvfb** | **Bug, fixed.** Step 3 starts Xvfb :99 as root; the kalpa-xvfb service then could not take :99 and would crash-loop until reboot. The script now stops the temporary one before starting the services |
| Wine path in the service | Hangover's deb ships `/usr/bin/wine` (checked in the 11.4 tar); now taken from `command -v wine` anyway |
| Hangover deb globs | match the 4 debs in the 11.4 noble tar (`hangover-wine_11.4~noble_arm64.deb` etc.) |
| Header comments | fixed "up to 24 GB" (now 2 OCPU + 12 GB total) and "The5%ers login" |

## Pass 2: outside facts (fetched 26 Nov 2026)

| Fact | Status |
|---|---|
| A1 Always Free = 2 OCPU + 12 GB total; E2.1.Micro = 1/8 OCPU, 1 GB, up to 2 | verified: docs.oracle.com Always Free resources page. README table already right |
| Idle rule: 7 days, CPU p95 < 20% and network < 20% and (A1 only) memory < 20%, all must be true | verified, same page |
| Ubuntu image | Oracle image list shows family "Ubuntu 24.04", images `Canonical-Ubuntu-24.04-...` (latest 2026.09.18); console label "Canonical Ubuntu 24.04". Verified |
| MetaQuotes demo web terminal | page loads (HTTP 200, title "Web Terminal", MetaQuotes-Demo server named). The "10000 deposit" option is **unverified** (page is script-rendered) |
| Hangover ARM64 | 11.4 release asset `hangover_11.4_ubuntu2404_noble_arm64.tar` downloads (200). Newer releases exist (11.16); 11.4 stays pinned as the one reported to run MT5 |
| MT5 installer URL | `download.mql5.com/.../mt5setup.exe` returns 200 application/exe |
| WineHQ key + noble sources | both 200; sources list amd64 + i386 |
| Windows key permission fix | icacls `/inheritance:r` + `/grant:r user:(R)`: DEV article + Oracle support note title ("Permissions for 'ssh-key-…key' are too open" on Windows). Microsoft's page does not cover private-key ACLs |

**Unverified (needs the first real run):** MT5 actually running for days under Hangover on A1; MT5 under Hangover using >1.2 GB (the README's "6 GB is not idle" reasoning); MT5 reading a plain `name=value` ASCII .set via ExpertParameters (MT5 writes UTF-16 with `||` ranges; plain files are widely used but not on the official page); Oracle emailing a week before reclaiming; E8 Pro on MT5 and the E8 trial not being MT5; MT5 phone app menu wording.

## Pass 3: beginner walkthrough

README was missing or out of order, now fixed:
- no "unzip the kit" step (a beginner could upload the kit zip): added step 1 (and the script now copes)
- demo account was mentioned inside the setup step, after it was needed: now step 2, with login/password/server to write down
- no "Change image / Change shape" clicks, no public IP note, key file name differs from `ssh-key.key`: added
- no PowerShell icacls fix: added (`${env:USERNAME}` form)
- no fingerprint "yes" note: added
- check step only said "phone app": added `systemctl status`, an EA log command, and phone app login
- switching to E8: said "run the setup again" without the zip argument (would fail with "EA folder not found"): exact commands for the E8 challenge and the funded preset
- compile fail: was one line; now says where the log is and what to do

Presets: every key in the 3 `.set` files (13, 13, 11) exists as an `input` in EA_XAUUSD; enum values (inp_Stage 1/3, inp_Program 8) are valid enum members.
