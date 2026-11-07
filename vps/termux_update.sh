#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — Termux updater
#   ./update.sh  →  latest bot.py download → compile check → ~/snake/bot.py
#                   + /storage/emulated/0/DBF/bot.py → restart (screen)
#   NOTE: Termux me /tmp writable nahi — log $TMPDIR / script folder me jata hai.
set -u

REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
DIR="$(cd "$(dirname "$0")" && pwd)"
EXT="/storage/emulated/0/DBF"
STAMP="$(date +%Y%m%d_%H%M%S)"
URL="${SNAKE_URL:-https://raw.githubusercontent.com/$REPO/$BRANCH/bot.py}"
FALLBACK="https://github.com/$REPO/raw/$BRANCH/bot.py"
LOGDIR="$DIR/logs"
mkdir -p "$DIR/backups" "$LOGDIR" 2>/dev/null
LOG="$LOGDIR/compile_$$.txt"

cd "$DIR" || exit 1

PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
if [ -z "$PY" ]; then
    echo "❌ python nahi mila — 'pkg install python' chalao"
    exit 1
fi

if command -v curl >/dev/null 2>&1; then
    DL() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    DL() { wget -q "$1" -O "$2"; }
else
    echo "❌ curl/wget nahi mila — 'pkg install curl' chalao"
    exit 1
fi

# ── bot process dhoondo: SIRF wahi jiska aakhri argument "bot.py" hai ──
#    (broad pkill khatarnak hai — tumhari shell bhi mar sakti hai)
BOT_PIDS() {
    for p in $(pgrep -f "bot\.py" 2>/dev/null); do
        [ -r "/proc/$p/cmdline" ] || continue
        c="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)"
        last=""
        for w in $c; do last="$w"; done
        [ "$last" = "bot.py" ] && echo "$p"
    done
}

# ══════════════ 1) DOWNLOAD ══════════════
[ -f bot.py ] && cp -f bot.py "backups/bot_$STAMP.py" && echo "💾 backup: backups/bot_$STAMP.py"

echo "→ download: $URL"
if ! DL "$URL" bot.py.new; then
    echo "↩ primary fail, fallback try…"
    if ! DL "$FALLBACK" bot.py.new; then
        echo "❌ download fail — net ya URL check karo (purana bot chalu hai)"
        rm -f bot.py.new
        exit 1
    fi
fi

if [ ! -s bot.py.new ]; then
    echo "❌ khaali file mili — abort (purana bot chalu hai)"
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

# ══════════════ 2) COMPILE ══════════════
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

# ══════════════ 3) RESTART ══════════════
# purana process pura marne do (warna naya 409 Conflict pe exit ho jata hai)
if command -v screen >/dev/null 2>&1; then
    screen -S snake -X quit >/dev/null 2>&1
fi
OLD="$(BOT_PIDS)"
if [ -n "$OLD" ]; then
    echo "→ purana bot band ho raha hai (pids: $(echo "$OLD" | tr '\n' ' '))"
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        [ -z "$(BOT_PIDS)" ] && break
        sleep 1
    done
fi
LEFTOVER="$(BOT_PIDS)"
if [ -n "$LEFTOVER" ]; then
    echo "→ zabardasti band…"
    for p in $LEFTOVER; do kill -9 "$p" 2>/dev/null; done
    sleep 2
fi

RLOG="$LOGDIR/bot_$STAMP.log"
START_OK=0
if [ -x "./restart.sh" ]; then
    echo "→ ./restart.sh chala rahe hain"
    ./restart.sh >/dev/null 2>&1 && START_OK=1
fi
if [ "$START_OK" != "1" ] && command -v screen >/dev/null 2>&1; then
    screen -dmS snake bash -c "cd '$DIR' && exec '$PY' bot.py > '$RLOG' 2>&1"
    START_OK=1
fi
if [ "$START_OK" != "1" ]; then
    echo "⚠️ screen nahi hai — nohup fallback"
    setsid nohup "$PY" bot.py >"$RLOG" 2>&1 &
    START_OK=1
fi

sleep 6
if [ -n "$(BOT_PIDS)" ]; then
    echo "🚀 bot chalu hai ($(echo "$(BOT_PIDS)" | tr '\n' ' '))"
    command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q snake \
        && echo "🖥 screen session: snake (dekho: screen -r snake)"
    echo "→ Telegram me /ping → $VER"
else
    echo "❌ bot start hote hi band ho gaya — log:"
    tail -n 20 "$RLOG" 2>/dev/null || echo "   (log khaali — 'python bot.py' se khud chala ke error dekho)"
    echo "   purana version wapas: cp backups/bot_$STAMP.py bot.py && ./restart.sh"
    exit 1
fi
