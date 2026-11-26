# Run the gold EA 24/5 for free (Oracle Cloud Always Free)

Akhil chose the free route on 21 Nov 2026. The bot runs on a free Oracle Cloud server, so his PC can stay off.

## What was checked (21 Nov 2026; Oracle limits, idle rule and download links checked again 26 Nov 2026)

| Fact | Source |
|---|---|
| Free ARM server (A1) is now 2 OCPU and 12 GB RAM in total; the free AMD micro is 1/8 OCPU, 1 GB RAM, 2 of them | docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm |
| Idle rule: an instance can be stopped if, over 7 days, CPU (95th percentile) < 20% **and** network < 20% **and**, on A1 only, memory < 20% | same page |
| Oracle asks for a card to verify identity at sign-up (no charge on Always Free) | cpanelfree.com 2026 guide + Oracle sign-up page |
| MT5 has no ARM version. On ARM, Box64 + Wine is detected by MT5 as a debugger; Hangover 11.4 (a Wine fork for ARM) did run MT5 on Oracle A1. No multi-day uptime report. | medium.com/@altbozon "Running MT5 on a Free Oracle ARM64 VPS"; MQL5 forum 455005 |
| gmag11/MetaTrader5-Docker-Image (MIT, 124★) supports x86 only and is about 4 GB, too big for a 1 GB micro | its README |
| MetaTrader's own VPS costs $10–15 a month (the paid fallback) | mql5.com/en/vps |

The setup script could not be test-run here: this build workspace cannot install MT5 behind its network proxy. It passes `bash -n`, shellcheck and a dry run (`07-trading/tests/test_cloud_setup.sh`). The first real run on the server is the test, and the script prints OK or FAIL at every step.

## Which free server

1. **First choice: Ampere A1, 1 OCPU, 6 GB RAM, Ubuntu 24.04.** MT5 under Hangover uses more than 1.2 GB (20% of 6 GB), so the server is not idle by Oracle's rule. Do not pick 12 GB: MT5 would use under 20% of it, and the server could count as idle.
2. **If A1 says "out of capacity":** retry later or try another availability domain. Otherwise use **E2.1.Micro (AMD, 1 GB)**. The script adds 4 GB of swap. The idle check there uses CPU and network only, so a quiet MT5 could get the server stopped. Oracle emails a week before; the server can be started again from the console.

If the server is ever stopped, every open trade still has its stop-loss and target with the broker, so a trade can't run without limits.

## Steps (Akhil, on the Windows PC, about 60 minutes)

1. **Unzip the kit:** right-click the kit zip → Extract All. The folder has 3 files: `EA_XAUUSD_E8.zip` (do not unzip this one), `setup_mt5_free_cloud.sh` and this `README.md`.
2. **Free demo account first** (the setup asks for it): open https://web.metatrader.app/terminal?mode=demo (MetaQuotes's own page), open a demo account with a 10000 deposit, and write down the **login number, password and server** (usually `MetaQuotes-Demo`). The E8 free trial can't be used: it runs on MatchTrader or E8 Terminal, not MT5.
3. **Oracle account:** go to oracle.com/cloud/free and sign up yourself (Oracle asks for a card to check identity). Pick **India South (Hyderabad)** or **India West (Mumbai)** as the home region; it can't be changed later. Never click "Upgrade" afterwards.
4. **Create the server:** Compute → Instances → Create instance.
   - Image: click **Change image** → **Canonical Ubuntu 24.04**.
   - Shape: click **Change shape** → **Ampere** → **VM.Standard.A1.Flex**, 1 OCPU, 6 GB memory.
   - Networking: keep the defaults ("Assign a public IPv4 address" on).
   - SSH keys: **Generate a key pair for me** → **Save private key**. Move the file (named like `ssh-key-2026-11-26.key`) into the kit folder and rename it to `ssh-key.key`.
   - Create. When it says Running, copy the **Public IP address**.
5. **Open PowerShell in the kit folder** (in File Explorer type `powershell` in the address bar and press Enter). Lock the key file first, or ssh refuses it with "UNPROTECTED PRIVATE KEY FILE":
   ```
   icacls .\ssh-key.key /inheritance:r
   icacls .\ssh-key.key /grant:r "${env:USERNAME}:(R)"
   ```
6. **Send the files and log in** (replace PUBLIC_IP; the first time, type `yes` when asked about the fingerprint):
   ```
   scp -i ssh-key.key setup_mt5_free_cloud.sh EA_XAUUSD_E8.zip ubuntu@PUBLIC_IP:~
   ssh -i ssh-key.key ubuntu@PUBLIC_IP
   ```
7. **Run the setup on the server** (20–40 minutes):
   ```
   sudo PRESET=E8_Pro_10K_challenge.set bash setup_mt5_free_cloud.sh EA_XAUUSD_E8.zip
   ```
   - `PRESET` picks the settings file: `E8_Pro_10K_challenge.set` (demo and E8 challenge), `E8_Pro_10K_funded.set` (after passing), or `The5ers_HighStakes_10K_step1.set`. If the broker names gold differently (for example `XAUUSD.` or `GOLD`), add `SYMBOL=<that name>` before `bash`.
   - **If step 5 (compile) says FAIL:** nothing is broken and nothing trades. Copy the last lines it printed (the full log is in `/home/mt5/compile.log`; show it with `sudo tail -n 40 /home/mt5/compile.log`) and send them to Claude. Claude sends a fixed zip; copy it with step 6 and run step 7 again.
   - Step 6 asks for the MT5 login, server and password. Type them there yourself; never send the password to Claude.
8. **Check it works:**
   - `systemctl status kalpa-mt5` should say **active (running)**; the script itself ends with `OK MT5 is running with the EA`.
   - EA messages: `sudo sh -c 'f=$(ls -t "/home/mt5/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Logs/"*.log | head -1); iconv -f UTF-16 -t UTF-8 "$f" | tail -n 20'` should show EA_XAUUSD loaded on XAUUSD,H1.
   - Trades: on the MT5 phone app, log in with the same login and server (Manage accounts → + → log in to an existing account → search the server name). Trades appear when the EA finds a setup; some days have none.
9. **Switch to E8 later:**
   - After you buy **E8 Pro $10K**, E8 emails an MT5 login, password and server. Log in with ssh (step 6) and run the same command as step 7, typing the E8 details: `sudo PRESET=E8_Pro_10K_challenge.set bash setup_mt5_free_cloud.sh EA_XAUUSD_E8.zip`. The script restarts MT5 with the new login.
   - After you **pass**, E8 gives a new funded login. Run it again with `PRESET=E8_Pro_10K_funded.set` and the funded details.

## Daily commands (on the server)

- `systemctl status kalpa-mt5`: is it running
- `journalctl -u kalpa-mt5 -n 50`: last 50 log lines
- `sudo systemctl stop kalpa-mt5`: stop the bot (open trades keep their stop-loss)
- `sudo PRESET=E8_Pro_10K_challenge.set bash setup_mt5_free_cloud.sh NEW_ZIP`: install a new EA version (asks for the login again, then restarts MT5)
