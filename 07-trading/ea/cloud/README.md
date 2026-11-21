# Run the gold EA 24/5 for free (Oracle Cloud Always Free)

Akhil chose the free route on 21 Nov 2026. The bot runs on a free Oracle Cloud server, so his PC can stay off.

## What was checked (21 Nov 2026)

| Fact | Source |
|---|---|
| Free ARM server (A1) is now 2 OCPU and 12 GB RAM in total; the free AMD micro is 1/8 OCPU, 1 GB RAM, 2 of them | docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm |
| Idle rule: an instance can be stopped if, over 7 days, CPU (95th percentile) < 20% **and** network < 20% **and**, on A1 only, memory < 20% | same page |
| Oracle asks for a card to verify identity at sign-up (no charge on Always Free) | cpanelfree.com 2026 guide + Oracle sign-up page |
| MT5 has no ARM version. On ARM, Box64 + Wine is detected by MT5 as a debugger; Hangover 11.4 (a Wine fork for ARM) did run MT5 on Oracle A1. No multi-day uptime report. | medium.com/@altbozon "Running MT5 on a Free Oracle ARM64 VPS"; MQL5 forum 455005 |
| gmag11/MetaTrader5-Docker-Image (MIT, 124★) supports x86 only and is about 4 GB, too big for a 1 GB micro | its README |
| MetaTrader's own VPS costs $10–15 a month (the paid fallback) | mql5.com/en/vps |

The setup script could not be test-run here: this build workspace cannot install MT5 behind its network proxy. It passes `bash -n`, shellcheck and a dry run (`tests/test_cloud_setup.sh`). The first real run on the server is the test, and the script prints OK or FAIL at every step.

## Which free server

1. **First choice: Ampere A1, 1 OCPU, 6 GB RAM, Ubuntu 24.04.** MT5 under Hangover uses more than 1.2 GB (20% of 6 GB), so the server is not idle by Oracle's rule. Do not pick 12 GB: MT5 would use under 20% of it, and the server could count as idle.
2. **If A1 says "out of capacity":** retry later or try another availability domain. Otherwise use **E2.1.Micro (AMD, 1 GB)**. The script adds 4 GB of swap. The idle check there uses CPU and network only, so a quiet MT5 could get the server stopped. Oracle emails a week before; the server can be started again from the console.

If the server is ever stopped, every open trade still has its stop-loss and target with the broker, so a trade can't run without limits.

## Steps (Akhil, on the Windows PC, about 45 minutes)

1. **Oracle account:** go to oracle.com/cloud/free and sign up yourself. Pick **India South (Hyderabad)** or **India West (Mumbai)** as the home region; it can't be changed later. Never click "Upgrade" afterwards.
2. **Create the server:** Compute → Instances → Create.
   - Image: Canonical Ubuntu 24.04.
   - Shape: Ampere → VM.Standard.A1.Flex, 1 OCPU, 6 GB.
   - Click "Save private key" and keep the file.
   - Create, then copy the **Public IP**.
3. **Send the two files**: open PowerShell where the key and files are, and run:
   ```
   scp -i ssh-key.key setup_mt5_free_cloud.sh EA_XAUUSD_The5ers_10K.zip ubuntu@PUBLIC_IP:~
   ssh -i ssh-key.key ubuntu@PUBLIC_IP
   ```
4. **Run the setup on the server:**
   ```
   sudo bash setup_mt5_free_cloud.sh EA_XAUUSD_The5ers_10K.zip
   ```
   - Step 5 compiles the EA. If it says FAIL, send Claude the last lines it prints.
   - Step 6 asks for the MT5 login, server and password. For the 2-week demo, use the demo account opened in the MT5 phone app; later use the The5%ers account. You type the password there yourself; never send it to Claude.
5. **Check:** open the MT5 phone app with the same login. The EA's trades appear there within a few hours.

## Daily commands (on the server)

- `systemctl status kalpa-mt5`: is it running
- `journalctl -u kalpa-mt5 -n 50`: last 50 log lines
- `sudo systemctl stop kalpa-mt5`: stop the bot (open trades keep their stop-loss)
- `sudo bash setup_mt5_free_cloud.sh NEW_ZIP`: install a new EA version
