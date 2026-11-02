#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  SPIDEY TELEGRAM BOT — SPIDEY-X ENGINE — TERMUX (ANDROID PHONE) INSTALLER
#  Ye script ASLI TELEGRAM BOT (bot_fixed.py) install + run karti hai.
#  VPS ki zaroorat NAHI — sirf phone + internet chahiye.
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_bot_termux_setup.sh -o bs.sh && bash bs.sh
# ==============================================================================
set -u

REPO_RAW="https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot"
INSTALL_DIR="${1:-$HOME/spidey}"

echo "=============================================================="
echo "  🤖 SPIDEY TELEGRAM BOT  •  SPIDEY-X  •  TERMUX INSTALLER"
echo "  Install dir : $INSTALL_DIR"
echo "=============================================================="

# ---------- 1) System packages ----------
echo "📦 [1/5] Installing packages (python, clang, openssl, screen)..."
pkg update -y >/dev/null 2>&1 || true
pkg install -y python clang make binutils openssl libffi libxml2 libxslt libjpeg-turbo curl screen termux-api >/dev/null 2>&1 || true
pkg install -y python curl screen >/dev/null 2>&1 || true

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "❌ Python install nahi hua. Manually:  pkg install python"
  exit 1
fi
echo "✅ Python: $($PY -V 2>&1)"

# ---------- 2) Wake lock ----------
echo "🔒 [2/5] Wake lock..."
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock 2>/dev/null && echo "   ✅ ON" \
  || echo "   ⚠️  Termux notification me 'Acquire wakelock' daba dena"

# ---------- 3) Python libraries (bot ki dependencies) ----------
echo "🐍 [3/5] Installing bot libraries (thoda time lagega — aiohttp compile hota hai)..."
$PY -m pip install --quiet --upgrade pip setuptools wheel 2>/dev/null || true

_install_pkg () {  # $1 = pip name, $2 = friendly label
  if $PY -c "import ${3:-$1}" >/dev/null 2>&1; then
    echo "   ✅ $2 (already installed)"
    return 0
  fi
  if $PY -m pip install --quiet --upgrade "$1" >/dev/null 2>&1; then
    echo "   ✅ $2 installed"
    return 0
  fi
  echo "   ⚠️  $2 install fail — dubara:  $PY -m pip install $1"
  return 1
}

_install_pkg "python-telegram-bot" "python-telegram-bot (bot core)" "telegram"
_install_pkg "aiohttp"             "aiohttp (HTTP engine)"        "aiohttp"
_install_pkg "beautifulsoup4"      "beautifulsoup4 (HTML parser)"  "bs4"
_install_pkg "aiohttp-socks"       "aiohttp-socks (SOCKS proxies)" "aiohttp_socks" || true
_install_pkg "ddgs"                "ddgs (DuckDuckGo search)"      "ddgs"          || true
_install_pkg "psutil"              "psutil (RAM/CPU stats)"        "psutil"        || true
_install_pkg "primp"               "primp (TLS bypass, optional)"  "primp"         || true

# ---------- 4) Download the bot ----------
echo "⬇️  [4/5] Downloading bot_fixed.py (V18-TITAN)..."
mkdir -p "$INSTALL_DIR" && cd "$INSTALL_DIR" || exit 1
if ! curl -fsSL "$REPO_RAW/bot_fixed.py" -o bot_fixed.py; then
  echo "❌ Download fail — internet check karo."
  exit 1
fi
$PY -m py_compile bot_fixed.py || { echo "❌ bot_fixed.py corrupt — dobara try karo"; exit 1; }
if grep -q "SPIDEY-X" bot_fixed.py; then
  echo "✅ bot_fixed.py ready ($(wc -l < bot_fixed.py) lines) — SPIDEY-X engine included"
else
  echo "⚠️  bot_fixed.py downloaded but V19 marker missing — update.sh se dobara lo"
fi

# ---------- 5) Launchers ----------
echo "🛠️  [5/5] Creating launchers..."

cat > run.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 🤖 Bot start (screen ke andar, log -> bot.log)
cd "$(dirname "$0")" || exit 1
termux-wake-lock 2>/dev/null || true
PY="$(command -v python3 || command -v python)"
exec "$PY" bot_fixed.py >> bot.log 2>&1
EOF

cat > start.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# ▶️  Bot ko background (screen) me chalao — terminal band karo tab bhi chalta rahega
cd "$(dirname "$0")" || exit 1
screen -S spidey -X quit >/dev/null 2>&1 || true
sleep 1
screen -dmS spidey ./run.sh
sleep 3
screen -ls | grep -q spidey && echo "✅ Bot STARTED (screen: spidey)" || echo "❌ Start fail — dekho: tail -50 bot.log"
echo "📜 Live log:  ./logs.sh"
EOF

cat > stop.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# ⏹️  Bot band karo
screen -S spidey -X quit >/dev/null 2>&1 && echo "✅ Bot STOPPED" || echo "ℹ️  Bot already stopped"
EOF

cat > restart.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
./stop.sh; sleep 2; ./start.sh
EOF

cat > logs.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 📜 Live log dekho (Ctrl+C se bahar)
cd "$(dirname "$0")" || exit 1
touch bot.log
tail -n 80 -f bot.log
EOF

cat > status.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
echo "── SCREEN ─────────────────────────────"
screen -ls 2>/dev/null | grep spidey || echo "❌ Bot screen nahi chal raha"
echo "── LAST 12 LOG LINES ──────────────────"
tail -n 12 bot.log 2>/dev/null || echo "(log khali hai)"
EOF

cat > settoken.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 🔑 Naya bot token set karo (BotFather se):  ./settoken.sh 123456:ABC...
cd "$(dirname "$0")" || exit 1
NEW="$1"
if [ -z "$NEW" ]; then
  echo "Usage: ./settoken.sh 123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  exit 1
fi
cp -f bot_fixed.py "bot_fixed.backup.$(date +%Y%m%d_%H%M%S).py"
python3 - "$NEW" <<'PYEOF'
import re, sys
tok = sys.argv[1].strip()
src = open("bot_fixed.py", encoding="utf-8").read()
new, n = re.subn(r'^BOT_TOKEN *= *"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if n == 0:
    print("❌ BOT_TOKEN line nahi mili — manually edit karo")
    sys.exit(1)
open("bot_fixed.py", "w", encoding="utf-8").write(new)
print("✅ Token updated")
PYEOF
python3 -m py_compile bot_fixed.py && echo "✅ File OK — ab: ./restart.sh"
EOF

cat > setconfig.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# ⚙️  Token + Admin ID change karo:  ./setconfig.sh
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_setconfig.sh" -o .setconfig.tmp && bash .setconfig.tmp && rm -f .setconfig.tmp
EOF

cat > doctor.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 🩺 Bot jawab nahi de raha? Ye chalao:  ./doctor.sh
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_doctor.sh" -o .doctor.tmp && bash .doctor.tmp && rm -f .doctor.tmp
EOF

cat > update.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 🔄 Latest bot (aapka token + admin id PRESERVE rehta hai)
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_update.sh" -o .update.tmp && bash .update.tmp && rm -f .update.tmp
EOF

chmod +x run.sh start.sh stop.sh restart.sh logs.sh status.sh settoken.sh setconfig.sh doctor.sh update.sh 2>/dev/null || true

echo ""
echo "=============================================================="
echo "  ✅ BOT INSTALL COMPLETE — VPS KI ZAROORAT NAHI"
echo "=============================================================="
echo "  cd $INSTALL_DIR"
echo ""
echo "  ./start.sh      -> 🤖 Bot BACKGROUND me start (Telegram pe /start karo)"
echo "  Telegram menu   -> 🕷️ SPIDEY-X ENGINE button (new!)"
echo "  ./status.sh     -> chal raha hai ya nahi"
echo "  ./logs.sh       -> live log"
echo "  ./setconfig.sh  -> ⚙️ token / admin id change"
echo "  ./doctor.sh     -> 🩺 bot jawab nahi de raha? ye chalao"
echo "  ./stop.sh       -> band"
echo "  ./restart.sh    -> restart"
echo "  ./update.sh     -> 🔄 latest version (token/admin safe + auto restart)"
echo ""
echo "  💡 Phone ko sona nahi dena: Battery Optimization OFF (Settings > Apps > Termux)"
echo "  💡 Termux notification me 'Acquire wakelock' ON rakho"
echo "=============================================================="
