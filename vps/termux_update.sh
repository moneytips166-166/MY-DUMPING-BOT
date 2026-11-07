#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — Termux updater
#   ./update.sh  →  latest bot.py download → compile check → ~/snake/bot.py
#                   + /storage/emulated/0/DBF/bot.py → screen me restart
set -u

REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
DIR="$(cd "$(dirname "$0")" && pwd)"
EXT="/storage/emulated/0/DBF"
STAMP="$(date +%Y%m%d_%H%M%S)"
URL="${SNAKE_URL:-https://raw.githubusercontent.com/$REPO/$BRANCH/bot.py}"
FALLBACK="https://github.com/$REPO/raw/$BRANCH/bot.py"

cd "$DIR" || exit 1
mkdir -p backups "$EXT" 2>/dev/null
[ -f bot.py ] && cp -f bot.py "backups/bot_$STAMP.py" && echo "💾 backup: backups/bot_$STAMP.py"

echo "→ download: $URL"
if ! curl -fsSL "$URL" -o bot.py.new; then
    echo "↩ primary fail, fallback try…"
    if ! curl -fsSL "$FALLBACK" -o bot.py.new; then
        echo "❌ download fail — net ya URL check karo"
        rm -f bot.py.new
        exit 1
    fi
fi

if [ ! -s bot.py.new ]; then
    echo "❌ khaali file mili — abort"
    rm -f bot.py.new
    exit 1
fi

if ! python -m py_compile bot.py.new 2>/tmp/snake_compile.txt; then
    echo "❌ naya bot.py compile nahi hua — purana hi chal raha hai"
    cat /tmp/snake_compile.txt
    rm -f bot.py.new
    exit 1
fi

mv -f bot.py.new bot.py
cp -f bot.py "$EXT/bot.py" 2>/dev/null && EXT_OK=1 || EXT_OK=0
VER="$(grep -m1 '^VERSION = ' bot.py | cut -d'"' -f2)"

echo "✅ $DIR/bot.py"
if [ "$EXT_OK" = "1" ]; then
    echo "✅ $EXT/bot.py"
else
    echo "⚠️ $EXT copy fail (storage permission?)"
fi
echo "✅ version: $VER"

if command -v screen >/dev/null 2>&1; then
    screen -S snake -X quit >/dev/null 2>&1
    sleep 1
    screen -dmS snake python bot.py
    if screen -ls 2>/dev/null | grep -q "snake"; then
        echo "🚀 restarted in screen 'snake'"
    else
        echo "⚠️ screen start nahi hua — manually: screen -S snake python bot.py"
    fi
else
    echo "⚠️ screen install nahi hai — ./restart.sh se start karo"
fi
echo "→ Telegram me /ping → $VER dikhna chahiye"
