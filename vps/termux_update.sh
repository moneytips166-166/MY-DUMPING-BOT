#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — Termux updater
#   ./update.sh  →  latest bot.py download → compile check → ~/snake/bot.py
#                   + /storage/emulated/0/DBF/bot.py → screen me restart
#   NOTE: Termux me /tmp writable nahi hota — log $TMPDIR/$PREFIX/tmp me jata hai.
set -u

REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
DIR="$(cd "$(dirname "$0")" && pwd)"
EXT="/storage/emulated/0/DBF"
STAMP="$(date +%Y%m%d_%H%M%S)"
URL="${SNAKE_URL:-https://raw.githubusercontent.com/$REPO/$BRANCH/bot.py}"
FALLBACK="https://github.com/$REPO/raw/$BRANCH/bot.py"
LOG="${TMPDIR:-${PREFIX:-$DIR}/tmp}"
[ -d "$LOG" ] || LOG="$DIR"
LOG="$LOG/snake_compile_$$.txt"

cd "$DIR" || exit 1
mkdir -p backups 2>/dev/null

# ── python ka naam ──
PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
if [ -z "$PY" ]; then
    echo "❌ python nahi mila — 'pkg install python' chalao"
    exit 1
fi

# ── downloader ──
if command -v curl >/dev/null 2>&1; then
    DL() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    DL() { wget -q "$1" -O "$2"; }
else
    echo "❌ curl/wget nahi mila — 'pkg install curl' chalao"
    exit 1
fi

[ -f bot.py ] && cp -f bot.py "backups/bot_$STAMP.py" && echo "💾 backup: backups/bot_$STAMP.py"

echo "→ download: $URL"
if ! DL "$URL" bot.py.new; then
    echo "↩ primary fail, fallback try…"
    if ! DL "$FALLBACK" bot.py.new; then
        echo "❌ download fail — net ya URL check karo"
        rm -f bot.py.new
        exit 1
    fi
fi

# ── sanity: khaali / galat file kabhi install na ho ──
if [ ! -s bot.py.new ]; then
    echo "❌ khaali file mili — abort"
    rm -f bot.py.new
    exit 1
fi
if ! grep -q "^VERSION = " bot.py.new || ! grep -q "^def main()" bot.py.new \
   || ! grep -q "ApplicationBuilder" bot.py.new; then
    echo "❌ file bot.py jaisi nahi lagti (HTML/error page?) — abort, purana chalu rahega"
    head -3 bot.py.new 2>/dev/null
    rm -f bot.py.new
    exit 1
fi

# ── compile check (log Termux-safe jagah par) ──
if ! "$PY" -m py_compile bot.py.new 2>"$LOG"; then
    echo "❌ naya bot.py compile nahi hua — purana hi chal raha hai"
    cat "$LOG" 2>/dev/null
    rm -f bot.py.new "$LOG"
    exit 1
fi
rm -f "$LOG"

mv -f bot.py.new bot.py
cp -f bot.py "$EXT/bot.py" 2>/dev/null && EXT_OK=1 || EXT_OK=0
VER="$(grep -m1 '^VERSION = ' bot.py | cut -d'"' -f2)"

echo "✅ $DIR/bot.py"
if [ "$EXT_OK" = "1" ]; then
    echo "✅ $EXT/bot.py"
else
    echo "⚠️ $EXT copy fail — 'termux-setup-storage' chala ke dobara try karo"
fi
echo "✅ version: $VER"

if command -v screen >/dev/null 2>&1; then
    screen -S snake -X quit >/dev/null 2>&1
    sleep 1
    screen -dmS snake "$PY" bot.py
    if screen -ls 2>/dev/null | grep -q "snake"; then
        echo "🚀 restarted in screen 'snake'"
    else
        echo "⚠️ screen start nahi hua — manually: screen -S snake python bot.py"
    fi
else
    echo "⚠️ screen install nahi hai — 'pkg install screen' ya ./restart.sh"
fi
echo "→ Telegram me /ping → $VER dikhna chahiye"
