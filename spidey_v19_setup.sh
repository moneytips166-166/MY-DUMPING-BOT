#!/usr/bin/env bash
# ==============================================================================
#  SPIDEY V19-TITAN — ONE-COMMAND FRESH-VPS / LAPTOP INSTALLER
#  Naya VPS? Files delete ho gayi? Bas ye ek command chalao:
#     bash spidey_v19_setup.sh
#  (ya direct: curl -fsSL <raw-url> | bash)
# ==============================================================================
set -e

REPO_RAW="https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot"
INSTALL_DIR="${1:-$HOME/spidey}"
PORT="${SPIDEY_PORT:-8080}"
THREADS="${SPIDEY_THREADS:-60}"

echo "=============================================================="
echo "  🕷️  SPIDEY V19-TITAN INSTALLER  ->  $INSTALL_DIR"
echo "=============================================================="

# ---------- 1) Python check ----------
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "❌ Python nahi mila. Pehle install karo:"
  echo "   Ubuntu/Debian: sudo apt update && sudo apt install -y python3"
  echo "   Windows      : https://www.python.org/downloads/"
  exit 1
fi
echo "✅ Python: $($PY -V 2>&1)"

# ---------- 2) Download the suite ----------
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
echo "⬇️  Downloading spidey_offline_suite.py ..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$REPO_RAW/spidey_offline_suite.py" -o spidey_offline_suite.py
else
  wget -qO spidey_offline_suite.py "$REPO_RAW/spidey_offline_suite.py"
fi
$PY -m py_compile spidey_offline_suite.py
echo "✅ Suite ready: $INSTALL_DIR/spidey_offline_suite.py"

# ---------- 3) Optional (recommended) speed/TLS boost ----------
if [ "$SPIDEY_NO_PIP" != "1" ]; then
  echo "⚡ Installing optional boosters (primp TLS impersonation)..."
  ($PY -m pip install --quiet --upgrade primp 2>/dev/null && echo "   ✅ primp installed (faster + better TLS)") \
    || echo "   ⚠️  primp install skip (suite 100% chalega bina iske bhi)"
  if command -v apt >/dev/null 2>&1 && [ "$(id -u)" = "0" ]; then
    (apt-get install -y -qq sqlmap 2>/dev/null && echo "   ✅ sqlmap installed (bonus deep blind dump)") \
      || echo "   ⚠️  sqlmap skip (built-in UNION/Error dumper use hoga)"
  fi
fi

# ---------- 4) Launcher scripts ----------
cat > run_web.sh <<EOF
#!/usr/bin/env bash
# Web Control Center (browser me kholo: http://<VPS-IP>:$PORT)
cd "\$(dirname "\$0")"
exec $PY spidey_offline_suite.py --host 0.0.0.0 --port $PORT --threads $THREADS
EOF

cat > run_cli.sh <<EOF
#!/usr/bin/env bash
# Pure SSH terminal menu (1 se 9, S = settings)
cd "\$(dirname "\$0")"
exec $PY spidey_offline_suite.py --cli --threads $THREADS
EOF

cat > run_autopilot.sh <<EOF
#!/usr/bin/env bash
# Headless 1-Click Auto-Pilot (bina browser ke, seedha terminal se)
# Usage: ./run_autopilot.sh "stripe shop, gaming topup" 2000 5000
cd "\$(dirname "\$0")"
SEEDS="\${1:-stripe shop, gaming topup}"
KWC="\${2:-2000}"
DKC="\${3:-5000}"
exec $PY spidey_offline_suite.py --autopilot "\$SEEDS" --kw-count "\$KWC" --dork-count "\$DKC" --threads $THREADS
EOF

chmod +x run_web.sh run_cli.sh run_autopilot.sh 2>/dev/null || true

cat > update.sh <<'EOF'
#!/usr/bin/env bash
# Latest version dobara download karo (purani files safe rehti hain)
set -e
cd "$(dirname "$0")"
mkdir -p backups
cp -f spidey_offline_suite.py "backups/spidey_offline_suite_$(date +%Y%m%d_%H%M%S).py"
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_offline_suite.py" -o spidey_offline_suite.py
python3 -m py_compile spidey_offline_suite.py
echo "✅ Updated! Backup -> backups/"
EOF
chmod +x update.sh 2>/dev/null || true

echo ""
echo "=============================================================="
echo "  ✅ INSTALL COMPLETE"
echo "=============================================================="
echo "  📂 Folder      : $INSTALL_DIR"
echo "  🌐 Web Panel   : ./run_web.sh   ->  http://<VPS-IP>:$PORT"
echo "  🖥️  Terminal    : ./run_cli.sh"
echo "  🚀 Auto-Pilot  : ./run_autopilot.sh \"stripe shop\" 2000 5000"
echo "  🔄 Update      : ./update.sh"
echo ""
echo "  💡 Chota VPS (1-2 GB RAM) ke liye:"
echo "       ./run_web.sh   (threads $THREADS default, min 20)"
echo "     Firewall open (agar zaroorat ho):  sudo ufw allow $PORT"
echo "=============================================================="
