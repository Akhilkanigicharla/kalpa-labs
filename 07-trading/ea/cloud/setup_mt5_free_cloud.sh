#!/usr/bin/env bash
# A334: run the Kalpa gold EA 24/5 on a FREE Oracle Cloud server (Always Free tier), no PC needed.
#
#   Works on:  Oracle "VM.Standard.E2.1.Micro" (x86, 1 GB RAM)  -> normal Wine (WineHQ stable) + 4 GB swap
#              Oracle "VM.Standard.A1.Flex"   (ARM, 2 OCPU + 12 GB free in total; use 1 OCPU + 6 GB) -> Hangover 11.4 (Wine for ARM; Box64 is
#              detected by MT5 as a debugger, see research notes in 07-trading/ea/cloud/README.md)
#   OS:        Ubuntu 24.04 (Canonical image in the Oracle console)
#
# What it does (each step prints OK/FAIL):
#   1. swap file (so MT5 fits in 1 GB RAM)
#   2. Wine (x86) or Hangover (ARM), Xvfb (invisible screen), x11vnc (optional remote view over SSH)
#   3. MetaTrader 5 from metaquotes' official installer
#   4. the EA: downloads the zip you give it (or uses ./EA_XAUUSD), copies it into MQL5/Experts
#   5. COMPILES the EA with MetaEditor and prints the error count + log (send it to Claude if > 0)
#   6. asks YOU for the MT5 login, server and password (demo, then E8) (typed here only; stored in a file only
#      root and the mt5 user can read; never sent anywhere else)
#   MT5 runs in /portable mode so MQL5/ lives inside the install folder (as in the ARM write-up).
#   7. systemd services: invisible screen + MT5 with the EA on XAUUSD H1, auto-start on boot,
#      restart within 1 minute if MT5 dies, plus a 5-minute watchdog
#
# Usage on the server (after SSH):   sudo bash setup_mt5_free_cloud.sh [path-or-https-url-of-EA-zip]
# Dry run (prints the plan only):     DRY_RUN=1 bash setup_mt5_free_cloud.sh
set -euo pipefail

MT5_USER="mt5"
HOME_DIR="/home/${MT5_USER}"
PREFIX="${HOME_DIR}/.wine"
MT5_DIR="${PREFIX}/drive_c/Program Files/MetaTrader 5"
EA_NAME="EA_XAUUSD"
SWAP_GB="${SWAP_GB:-4}"
HANGOVER_VER="11.4"
DRY_RUN="${DRY_RUN:-0}"
EA_SRC="${1:-}"

say()  { printf '\n==> %s\n' "$*"; }
ok()   { printf '    OK   %s\n' "$*"; }
fail() { printf '    FAIL %s\n' "$*" >&2; exit 1; }
run()  { if [ "$DRY_RUN" = "1" ]; then printf '    would run: %s\n' "$*"; else "$@"; fi; }
as_mt5() { run sudo -u "$MT5_USER" env WINEPREFIX="$PREFIX" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=" DISPLAY=:99 "$@"; }

ARCH="$(uname -m)"
say "Machine: ${ARCH}, $(grep -c ^processor /proc/cpuinfo) CPU, $(awk '/MemTotal/{printf "%.1f GB", $2/1048576}' /proc/meminfo) RAM"
case "$ARCH" in
  x86_64) MODE="wine" ;;
  aarch64) MODE="hangover" ;;
  *) fail "unsupported CPU type ${ARCH} (need x86_64 or aarch64)" ;;
esac
ok "install mode: ${MODE}"
if [ "$DRY_RUN" != "1" ] && [ "$(id -u)" != "0" ]; then fail "run with sudo"; fi

say "1/7 Swap ${SWAP_GB} GB"
if swapon --show | grep -q /swapfile; then ok "swap already on"; else
  run fallocate -l "${SWAP_GB}G" /swapfile
  run chmod 600 /swapfile
  run mkswap /swapfile
  run swapon /swapfile
  if [ "$DRY_RUN" != "1" ]; then grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab; fi
  ok "swap on"
fi

say "2/7 Wine + invisible screen"
run apt-get update -qq
run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq xvfb x11vnc cabextract curl unzip ca-certificates
if [ "$MODE" = "wine" ]; then
  run dpkg --add-architecture i386
  run mkdir -pm755 /etc/apt/keyrings
  run curl -fsSL -o /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
  run curl -fsSL -o /etc/apt/sources.list.d/winehq-noble.sources https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
  run apt-get update -qq
  # 27 Nov 2026 first real run: wine-stable 11.0 and 10.0 both tripped MT5's anti-debugger check ("A debugger
  # has been found running in your system"). wine-staging (what MetaQuotes' own mt5linux.sh installs) ran MT5.
  run apt-mark unhold winehq-stable wine-stable wine-stable-amd64 wine-stable-i386:i386 >/dev/null 2>&1 || true
  run env DEBIAN_FRONTEND=noninteractive apt-get remove -y -qq winehq-stable wine-stable wine-stable-amd64 "wine-stable-i386:i386" >/dev/null 2>&1 || true
  run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --install-recommends winehq-staging libegl1 libgl1
else
  TMP="$(mktemp -d)"
  run curl -fsSL -o "${TMP}/hangover.tar" "https://github.com/AndreRH/hangover/releases/download/hangover-${HANGOVER_VER}/hangover_${HANGOVER_VER}_ubuntu2404_noble_arm64.tar"
  run tar -xf "${TMP}/hangover.tar" -C "$TMP"
  run dpkg -r fonts-wine libwine wine64 || true
  for deb in "${TMP}"/hangover-libwow64fex_*_arm64.deb "${TMP}"/hangover-libarm64ecfex_*_arm64.deb \
             "${TMP}"/hangover-wowbox64_*_arm64.deb "${TMP}"/hangover-wine_*_arm64.deb; do
    run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$deb"
  done
fi
if [ "$DRY_RUN" != "1" ]; then wine --version >/dev/null || fail "wine not working"; ok "$(wine --version)"; fi

say "3/7 MetaTrader 5"
id "$MT5_USER" >/dev/null 2>&1 || run useradd -m -s /bin/bash "$MT5_USER"
if [ "$DRY_RUN" != "1" ] && ! pgrep -f "Xvfb :99" >/dev/null; then (Xvfb :99 -screen 0 1024x768x24 >/dev/null 2>&1 &); sleep 2; fi
as_mt5 wineboot --init
if [ -f "${MT5_DIR}/terminal64.exe" ]; then ok "MT5 already installed"; else
  run curl -fsSL -o /tmp/mt5setup.exe https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe
  run chmod 644 /tmp/mt5setup.exe
  # 27 Nov 2026 first real run: mt5setup quit without installing. MetaQuotes' own mt5linux.sh sets Windows 11
  # mode and installs the WebView2 runtime first (fetched 27 Nov 2026 from download.mql5.com/.../mt5linux.sh).
  as_mt5 winecfg -v=win11 || true
  run curl -fsSL -o /tmp/webview2.exe "https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/f2910a1e-e5a6-4f17-b52d-7faf525d17f8/MicrosoftEdgeWebview2Setup.exe"
  run chmod 644 /tmp/webview2.exe
  as_mt5 timeout 900 wine /tmp/webview2.exe /silent /install || true
  as_mt5 timeout 1200 wine /tmp/mt5setup.exe /auto || true
  if [ "$DRY_RUN" != "1" ]; then
    for _ in $(seq 1 60); do [ -f "${MT5_DIR}/terminal64.exe" ] && break; sleep 10; done
    [ -f "${MT5_DIR}/terminal64.exe" ] || fail "MT5 did not install (send Claude: journalctl -n 50)"
  fi
  run pkill -f terminal64.exe || true
  ok "MT5 installed"
fi

say "4/7 The EA"
EA_DIR="${MT5_DIR}/MQL5/Experts/${EA_NAME}"
if [ -n "$EA_SRC" ]; then
  W="$(mktemp -d)"
  case "$EA_SRC" in
    https://*) run curl -fsSL -o "${W}/ea.zip" "$EA_SRC" ;;
    *) run cp "$EA_SRC" "${W}/ea.zip" ;;
  esac
  run unzip -q -o "${W}/ea.zip" -d "$W"
  SRC_DIR="$(find "$W" -maxdepth 3 -type d -name "$EA_NAME" | head -1)"
  if [ -z "$SRC_DIR" ] && [ "$DRY_RUN" != "1" ]; then  # the whole kit zip was given: open the EA zip inside it
    find "$W" -maxdepth 2 -name '*.zip' ! -path "${W}/ea.zip" -exec unzip -q -o {} -d "${W}/inner" \;
    SRC_DIR="$(find "${W}/inner" -maxdepth 3 -type d -name "$EA_NAME" 2>/dev/null | head -1)"
  fi
elif [ -d "./${EA_NAME}" ]; then SRC_DIR="./${EA_NAME}"
else SRC_DIR=""; fi
if [ "$DRY_RUN" != "1" ]; then [ -n "$SRC_DIR" ] && [ -f "${SRC_DIR}/${EA_NAME}.mq5" ] || fail "EA folder ${EA_NAME} not found (give the zip path)"; fi
run mkdir -p "$(dirname "$EA_DIR")"
run rm -rf "$EA_DIR"
run cp -r "${SRC_DIR:-./${EA_NAME}}" "$EA_DIR"
# A337: firm presets (.set) go to MQL5/Presets; PRESET=E8_Pro_10K_challenge.set picks one at start-up
PRESET="${PRESET:-E8_Pro_10K_challenge.set}"
SYMBOL="${SYMBOL:-XAUUSD}"
[[ "$PRESET" =~ ^[A-Za-z0-9._-]+\.set$ ]] || fail "PRESET must be a .set file name"
[[ "$SYMBOL" =~ ^[A-Za-z0-9._#-]{3,20}$ ]] || fail "SYMBOL looks wrong"
PRESET_SRC="$(dirname "${SRC_DIR:-./${EA_NAME}}")/presets"
run mkdir -p "${MT5_DIR}/MQL5/Presets"
if [ -d "$PRESET_SRC" ]; then run cp "$PRESET_SRC"/*.set "${MT5_DIR}/MQL5/Presets/"; fi
if [ "$DRY_RUN" != "1" ]; then [ -f "${MT5_DIR}/MQL5/Presets/${PRESET}" ] || fail "preset ${PRESET} not found in the zip"; fi
run chown -R "${MT5_USER}:${MT5_USER}" "$HOME_DIR"
ok "EA copied (preset ${PRESET}, symbol ${SYMBOL})"

say "5/7 Compile the EA"
LOG="${HOME_DIR}/compile.log"
as_mt5 wine "C:/Program Files/MetaTrader 5/MetaEditor64.exe" /portable "/compile:C:/Program Files/MetaTrader 5/MQL5/Experts/${EA_NAME}/${EA_NAME}.mq5" "/log:C:/users/${MT5_USER}/compile.log" || true
if [ "$DRY_RUN" != "1" ]; then
  CL="${PREFIX}/drive_c/users/${MT5_USER}/compile.log"
  [ -f "$CL" ] && iconv -f UTF-16 -t UTF-8 "$CL" > "$LOG" 2>/dev/null || cp "$CL" "$LOG" 2>/dev/null || true
  # 27 Nov 2026 first real run: MetaEditor /compile quit silently under Wine, but the terminal compiles new
  # .mq5 sources in MQL5/Experts at start-up (EA_XAUUSD.ex5 appeared within 60 s). Use that as the fallback.
  if [ ! -f "${EA_DIR}/${EA_NAME}.ex5" ]; then
    as_mt5 timeout 150 wine "C:/Program Files/MetaTrader 5/terminal64.exe" /portable || true
    pkill -f terminal64.exe || true; sleep 3
  fi
  if [ -f "${EA_DIR}/${EA_NAME}.ex5" ]; then ok "compiled: ${EA_NAME}.ex5"; else
    echo "    The EA did not compile. Last lines of the log (send these to Claude):"
    tail -n 40 "$LOG" 2>/dev/null || echo "    (no log)"
    fail "compile errors"
  fi
  grep -iE "result|error|warning" "$LOG" | tail -n 5 || true
fi

say "6/7 Your MT5 login: demo first, then the prop-firm account (typed here only)"
INI="${PREFIX}/drive_c/kalpa_start.ini"   # no space in the path: MT5 split "/config:C:/Program Files/..." at the space (27 Nov 2026 first run)
if [ "$DRY_RUN" = "1" ]; then
  printf '    would ask for login / server / password and write %s (chmod 600)\n' "$INI"
else
  read -r -p "    MT5 login number: " LOGIN
  read -r -p "    MT5 server (exactly as shown by your broker or prop firm): " SERVER
  IFS= read -r -s -p "    MT5 password (not shown): " PASS; echo
  [[ "$LOGIN" =~ ^[0-9]{4,12}$ ]] || fail "login must be the account number"
  [[ "$SERVER" =~ ^[A-Za-z0-9._-]{3,64}$ ]] || fail "server name looks wrong"
  # Release check 27 Nov: the EA's state files (target/floor lock, day stats) are not per account,
  # so a new login (demo -> E8 -> funded) must start clean or the demo's lock would block E8
  OLD_LOGIN="$(sed -n 's/^Login=//p' "$INI" 2>/dev/null || true)"
  NEW_ACCOUNT=0; [ "$OLD_LOGIN" != "$LOGIN" ] && NEW_ACCOUNT=1
  umask 077
  cat > "$INI" <<EOF
[Common]
Login=${LOGIN}
Password=${PASS}
Server=${SERVER}
KeepPrivate=1
NewsEnable=1
[Experts]
AllowLiveTrading=1
AllowDllImport=0
Enabled=1
Account=0
Profile=0
[StartUp]
Expert=${EA_NAME}\\${EA_NAME}
ExpertParameters=${PRESET}
Symbol=${SYMBOL}
Period=H1
EOF
  unset PASS
  chown "${MT5_USER}:${MT5_USER}" "$INI"; chmod 600 "$INI"
  ok "login saved for the mt5 user only"
fi

say "7/7 Run forever (systemd)"
if [ "$DRY_RUN" != "1" ]; then
WINE_BIN="$(command -v wine)"
cat > /etc/systemd/system/kalpa-xvfb.service <<EOF
[Unit]
Description=Invisible screen for MT5
[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1024x768x24
Restart=always
User=${MT5_USER}
[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/kalpa-mt5.service <<EOF
[Unit]
Description=MetaTrader 5 running the Kalpa gold EA
After=network-online.target kalpa-xvfb.service
Wants=network-online.target
Requires=kalpa-xvfb.service
[Service]
User=${MT5_USER}
Environment=WINEPREFIX=${PREFIX} DISPLAY=:99 WINEDEBUG=-all
ExecStart=${WINE_BIN} "C:/Program Files/MetaTrader 5/terminal64.exe" /portable /config:C:/kalpa_start.ini
Restart=always
RestartSec=30
[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/kalpa-watchdog.service <<'EOF'
[Unit]
Description=Restart MT5 if terminal64 is not running
[Service]
Type=oneshot
ExecStart=/bin/sh -c 'pgrep -f "[t]erminal64[.]exe" >/dev/null || systemctl restart kalpa-mt5'
EOF
cat > /etc/systemd/system/kalpa-watchdog.timer <<'EOF'
[Unit]
Description=Check MT5 every 5 minutes
[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl stop kalpa-mt5 2>/dev/null || true; pkill -f terminal64.exe || true; sleep 3
# Release check 27 Nov: drop saved charts so only the start-up chart (new preset) runs the EA;
# a restored old chart would take the EA's one-instance lock with the old settings
rm -f "${MT5_DIR}/MQL5/Profiles/Charts/"*/chart*.chr
if [ "${NEW_ACCOUNT:-0}" = "1" ] && ls "${MT5_DIR}/MQL5/Files/"EA_XAUUSD_*.txt >/dev/null 2>&1; then
  B="${MT5_DIR}/MQL5/Files/old-account-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$B"; mv "${MT5_DIR}/MQL5/Files/"EA_XAUUSD_*.txt "$B/"; chown -R "${MT5_USER}:${MT5_USER}" "$B"
  ok "new login: old EA state moved to ${B}"
fi
pkill -f "^Xvfb :99" || true   # the temporary screen from step 3; the service takes over :99
systemctl enable kalpa-xvfb kalpa-mt5 kalpa-watchdog.timer
systemctl restart kalpa-xvfb kalpa-mt5 kalpa-watchdog.timer   # restart, so a re-run loads the new login, preset and EA
sleep 60
if pgrep -f terminal64.exe >/dev/null; then ok "MT5 is running with the EA"; else fail "MT5 not running: journalctl -u kalpa-mt5 -n 50"; fi
else
  echo "    would install kalpa-xvfb, kalpa-mt5 (Restart=always) and a 5-minute watchdog timer"
fi

say "Done. Check trades on the MT5 phone app with the same login."
echo "    Status:  systemctl status kalpa-mt5      Logs: journalctl -u kalpa-mt5 -n 50"
echo "    Stop:    sudo systemctl stop kalpa-mt5   (the EA stops; open trades keep their stop-loss)"
echo "    See the screen once (optional): on your PC run  ssh -L 5900:localhost:5900 ubuntu@SERVER_IP"
echo "             then on the server  x11vnc -display :99 -localhost -nopw -once  and open a VNC viewer at localhost:5900"
