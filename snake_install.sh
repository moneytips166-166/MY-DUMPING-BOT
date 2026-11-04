#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🐍 PYTHON SNAKE CORE — installer (Termux / Linux / VPS)
#
#  Ek command:
#     curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_install.sh" -o si.sh && bash si.sh
#
#  Kya karta hai:
#     • ~/snake folder banata hai
#     • snake_core.py download karta hai
#     • purane bot (~/spidey/bot_fixed.py) se TOKEN + ADMIN_IDS khud utha leta hai
#     • start/stop/restart/logs/status/setconfig scripts banata hai (screen based)
#     • packages check karta hai
# ==============================================================================
set -u

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot}"
DIR="${SNAKE_DIR:-$HOME/snake}"
OLD_BOT="${OLD_BOT:-$HOME/spidey/bot_fixed.py}"
BOT="snake_core.py"

echo "=============================================================="
echo "  🐍 PYTHON SNAKE CORE — INSTALLER"
echo "=============================================================="

# ---------- 1. folder ----------
mkdir -p "$DIR"/{data,dumps,backups}
cd "$DIR" || { echo "❌ $DIR me nahi ja saka"; exit 1; }
echo "  📁 Folder : $DIR"

# ---------- 2. python ----------
PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "  ❌ python3 nahi mila. Chalao:  pkg install python"
  exit 1
fi
echo "  🐍 Python : $($PY --version 2>&1)"

# ---------- 3. packages ----------
echo ""
echo "  📦 Packages check…"
$PY - <<'PYEOF' 2>/dev/null || NEED=1
import importlib
for m in ("aiohttp", "telegram"):
    importlib.import_module(m)
print("  ✅ aiohttp + python-telegram-bot installed")
PYEOF
if ! $PY -c "import aiohttp, telegram" 2>/dev/null; then
  echo "  ⬇️  Installing aiohttp + python-telegram-bot…"
  command -v pkg >/dev/null 2>&1 && pkg install -y python >/dev/null 2>&1
  $PY -m pip install --upgrade pip >/dev/null 2>&1
  $PY -m pip install "aiohttp" "python-telegram-bot>=21,<22" || {
    echo "  ❌ pip install fail"; exit 1; }
  echo "  ✅ Packages ready"
fi

# ---------- 4. download bot ----------
echo ""
echo "  ⬇️  Downloading $BOT…"
cp -f "$BOT" "backups/${BOT%.py}_$(date +%Y%m%d_%H%M%S).py" 2>/dev/null
if ! curl -fsSL --retry 3 --retry-delay 2 --max-time 180 "$REPO_RAW/$BOT" -o ".$BOT.new"; then
  echo "  ❌ Download fail — internet / GitHub check karo"
  exit 1
fi
BYTES="$(wc -c < ".$BOT.new" | tr -d ' ')"
if [ "${BYTES:-0}" -lt 50000 ]; then
  echo "  ❌ Download adhura ($BYTES bytes)"; rm -f ".$BOT.new"; exit 1
fi
mv -f ".$BOT.new" "$BOT"
echo "  ✅ $BOT aaya ($(wc -l < "$BOT") lines)"

# ---------- 5. token + admin migrate ----------
echo ""
if [ -f "$OLD_BOT" ]; then
  echo "  🔎 Purana bot mila: $OLD_BOT"
  $PY - "$OLD_BOT" "$BOT" <<'PYEOF'
import re, sys
old_p, new_p = sys.argv[1], sys.argv[2]
def grab(p, pat, fl=re.M):
    try:
        m = re.search(pat, open(p, encoding="utf-8", errors="ignore").read(), fl)
        return m.group(1) if m else None
    except Exception:
        return None
tok = grab(old_p, r'^BOT_TOKEN\s*=\s*"([^"]*)"')
adm = grab(old_p, r'^ADMIN_IDS\s*=\s*(\[[^\]]*\])', re.M | re.S)
if not (tok and ":" in tok and "PUT_YOUR" not in tok):
    print("  ⚠️  purane bot me valid token nahi mila")
    sys.exit(0)
src = open(new_p, encoding="utf-8").read()
src = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if adm:
    src = re.sub(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]', 'ADMIN_IDS = %s' % " ".join(adm.split()),
                 src, count=1, flags=re.M | re.S)
open(new_p, "w", encoding="utf-8").write(src)
print("  ✅ Token + ADMIN_IDS purane bot se copy ho gaye")
PYEOF
else
  echo "  ℹ️  Purana bot nahi mila — token baad me ./setconfig.sh se daalo"
fi

# ---------- 6. helper scripts ----------
cat > start.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  echo "⚠️  Bot pehle se chal raha hai. Restart ke liye: ./restart.sh"
  exit 0
fi
screen -dmS snake bash -c 'python3 snake_core.py 2>&1 | tee -a bot.log'
sleep 2
echo "🚀 Started. Logs: ./logs.sh"
EOF
cat > stop.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
pkill -f "python3 snake_core.py" 2>/dev/null
screen -S snake -X quit 2>/dev/null
echo "🛑 Stopped."
EOF
cat > restart.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
./stop.sh >/dev/null 2>&1
sleep 1
./start.sh
EOF
cat > logs.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
tail -n 40 bot.log 2>/dev/null || echo "(log khali)"
EOF
cat > status.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  echo "✅ Bot CHAL RAHA hai"
else
  echo "❌ Bot BAND hai"
fi
echo "── last 5 log lines ──"
tail -n 5 bot.log 2>/dev/null || echo "(log khali)"
EOF
cat > update.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_update.sh" -o .upd.tmp && bash .upd.tmp && rm -f .upd.tmp
EOF
cat > setconfig.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_setconfig.sh" -o .cfg.tmp && bash .cfg.tmp && rm -f .cfg.tmp
EOF
chmod +x start.sh stop.sh restart.sh logs.sh status.sh update.sh setconfig.sh 2>/dev/null

# ---------- 7. syntax check ----------
echo ""
if $PY -m py_compile "$BOT" 2>/dev/null; then
  echo "  ✅ Syntax check pass"
  rm -rf __pycache__
else
  echo "  ❌ Syntax error — file kharab aayi, dobara download karo"
  exit 1
fi

echo ""
echo "=============================================================="
echo "  ✅ INSTALL HO GAYA — $DIR"
echo "=============================================================="
echo ""
echo "  🚀 Start   :  cd ~/snake && ./start.sh"
echo "  📜 Logs    :  ./logs.sh"
echo "  🔄 Restart :  ./restart.sh"
echo "  ⛔ Stop    :  ./stop.sh"
echo "  ⚙️  Config  :  ./setconfig.sh   (token / admin id)"
echo "  🔃 Update  :  ./update.sh"
echo ""
echo "  Bot me /start → captcha → menu"
echo "  Admin panel:  /admin"
echo "=============================================================="
