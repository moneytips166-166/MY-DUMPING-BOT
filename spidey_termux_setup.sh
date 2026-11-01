#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  SPIDEY V19 — TERMUX (ANDROID PHONE) INSTALLER  —  VPS ki zaroorat NAHI
#
#  Phone me Termux app kholo aur bas ye ek line paste karo:
#    curl -fsSL https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_termux_setup.sh -o ts.sh && bash ts.sh
# ==============================================================================
set -u

REPO_RAW="https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot"
INSTALL_DIR="${1:-$HOME/spidey}"
PORT="${SPIDEY_PORT:-8080}"
THREADS="${SPIDEY_THREADS:-40}"

echo "=============================================================="
echo "  📱 SPIDEY V19 — TERMUX INSTALLER"
echo "  Install dir : $INSTALL_DIR"
echo "  Port        : $PORT   |  Threads: $THREADS"
echo "=============================================================="

# ---------- 1) Packages ----------
echo "📦 [1/5] Installing packages (python, curl, screen)..."
pkg update -y >/dev/null 2>&1 || true
pkg install -y python curl screen termux-api coreutils >/dev/null 2>&1 || pkg install -y python curl screen >/dev/null 2>&1 || true

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "❌ Python install nahi hua. Manually chalao:  pkg install python"
  exit 1
fi
echo "✅ Python: $($PY -V 2>&1)"

# ---------- 2) Wake lock (phone app ko zinda rakhta hai) ----------
echo "🔒 [2/5] Wake lock ON (app background me band nahi hogi)..."
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock 2>/dev/null && echo "   ✅ termux-wake-lock enabled" \
  || echo "   ⚠️  termux-api nahi mila — Termux notification me 'Acquire wakelock' daba dena"

# ---------- 3) Download the suite ----------
echo "⬇️  [3/5] Downloading spidey_offline_suite.py ..."
mkdir -p "$INSTALL_DIR" && cd "$INSTALL_DIR" || exit 1
if ! curl -fsSL "$REPO_RAW/spidey_offline_suite.py" -o spidey_offline_suite.py; then
  echo "❌ Download fail (internet check karo)."
  exit 1
fi
$PY -m py_compile spidey_offline_suite.py || { echo "❌ File corrupt — dobara try karo"; exit 1; }
echo "✅ Suite ready ($(wc -l < spidey_offline_suite.py) lines)"

# ---------- 4) Optional boosters ----------
echo "⚡ [4/5] Optional boosters..."
$PY -m pip install --quiet --upgrade sqlmap >/dev/null 2>&1 \
  && echo "   ✅ sqlmap installed (deep blind dump support)" \
  || echo "   ⚠️  sqlmap skip (built-in UNION/Error dumper use hoga)"
# primp: Android ke liye wheel nahi hoti -> bina iske bhi suite 100% chalta hai
$PY -m pip install --quiet --upgrade primp >/dev/null 2>&1 \
  && echo "   ✅ primp installed (TLS impersonation)" \
  || echo "   ℹ️  primp Android par support nahi — built-in TLS engine use hoga (koi dikkat nahi)"

# ---------- 5) Launchers ----------
echo "🛠️  [5/5] Creating launchers..."
cat > run.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# 📱 Web panel start (phone me Chrome: http://127.0.0.1:$PORT)
cd "\$(dirname "\$0")"
termux-wake-lock 2>/dev/null || true
exec $PY spidey_offline_suite.py --host 0.0.0.0 --port $PORT --threads $THREADS --depth 1
EOF

cat > cli.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "\$(dirname "\$0")"
termux-wake-lock 2>/dev/null || true
exec $PY spidey_offline_suite.py --cli --threads $THREADS
EOF

cat > auto.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# 🚀 Headless full pipeline:  ./auto.sh "stripe shop, gaming topup" 2000 5000
cd "\$(dirname "\$0")"
termux-wake-lock 2>/dev/null || true
SEEDS="\${1:-stripe shop, gaming topup}"
KWC="\${2:-2000}"
DKC="\${3:-5000}"
exec $PY spidey_offline_suite.py --autopilot "\$SEEDS" --kw-count "\$KWC" --dork-count "\$DKC" --threads $THREADS --depth 1
EOF

cat > pull.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 📂 Saari output files phone ke Download folder me copy karo
cd "$(dirname "$0")" || exit 1
DEST="/sdcard/Download/SpideyOutput"
if [ ! -d /sdcard ]; then
  echo "❌ /sdcard nahi mila — pehle ek baar chalao:  termux-setup-storage"
  exit 1
fi
mkdir -p "$DEST"
COUNT=0
while IFS= read -r f; do
  cp -f "$f" "$DEST/" 2>/dev/null && COUNT=$((COUNT+1))
done <<< "$(find spidey_offline_workspace -type f -size +0c 2>/dev/null)"
echo "✅ $COUNT files copied -> $DEST"
EOF

cat > update.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p backups
cp -f spidey_offline_suite.py "backups/spidey_$(date +%Y%m%d_%H%M%S).py" 2>/dev/null || true
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_offline_suite.py" -o spidey_offline_suite.py
python3 -m py_compile spidey_offline_suite.py && echo "✅ Updated (backup -> backups/)"
EOF

chmod +x run.sh cli.sh auto.sh pull.sh update.sh 2>/dev/null || true

echo ""
echo "=============================================================="
echo "  ✅ TERMUX INSTALL COMPLETE — VPS KI ZAROORAT NAHI!"
echo "=============================================================="
echo "  cd $INSTALL_DIR"
echo "  ./run.sh                      -> Chrome me http://127.0.0.1:$PORT"
echo "  ./cli.sh                      -> Terminal menu (1..9, S = settings)"
echo "  ./auto.sh \"stripe shop\" 2000 5000   -> full pipeline ek command me"
echo "  ./pull.sh                     -> files /sdcard/Download/SpideyOutput"
echo "  ./update.sh                   -> naya version"
echo ""
echo "  💡 Battery Optimization OFF karo (Settings > Apps > Termux > Battery > Unrestricted)"
echo "  💡 Screen band karne se pehle:  termux-wake-lock"
echo "=============================================================="
