#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — Termux updater  (SNAKE_UPDATER_V=3)
#   ./update.sh   →  khud ko latest karta hai, phir bot.py (Termux + DBF) + restart
#   ./update.sh --no-self   →  self-update skip
# NOTE: Termux me /tmp writable nahi — log script folder ke logs/ me jata hai.
set -u
UPDATER_V=3

REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
DIR="$(cd "$(dirname "$0")" && pwd)"
EXT="/storage/emulated/0/DBF"
STAMP="$(date +%Y%m%d_%H%M%S)"
BOT_URL="${SNAKE_URL:-https://raw.githubusercontent.com/$REPO/$BRANCH/bot.py}"
BOT_FB="https://github.com/$REPO/raw/$BRANCH/bot.py"
SELF_URL="https://raw.githubusercontent.com/$REPO/$BRANCH/vps/termux_update.sh"
SELF_FB="https://github.com/$REPO/raw/$BRANCH/vps/termux_update.sh"
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
    DL() { curl -fsSL --max-time 60 "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    DL() { wget -q -T 60 "$1" -O "$2"; }
else
    echo "❌ curl/wget nahi mila — 'pkg install curl' chalao"
    exit 1
fi

# ── 0) SELF-UPDATE — ./update.sh hamesha latest rahe ──────────────────────
if [ "${SNAKE_NO_SELF:-0}" != "1" ] && [ "${1:-}" != "--no-self" ] && [ -w "$0" ]; then
    if DL "$SELF_URL" "$DIR/update.sh.new" 2>/dev/null \
       || DL "$SELF_FB" "$DIR/update.sh.new" 2>/dev/null; then
        if grep -q "SNAKE_UPDATER_V" "$DIR/update.sh.new" 2>/dev/null \
           && bash -n "$DIR/update.sh.new" 2>/dev/null; then
            chmod +x "$DIR/update.sh.new" 2>/dev/null
            if ! cmp -s "$DIR/update.sh.new" "$0" 2>/dev/null; then
                echo "🔄 updater script bhi naya mila — use kar rahe hain"
                mv -f "$DIR/update.sh.new" "$0"
                SNAKE_NO_SELF=1 exec bash "$0" --no-self
            fi
            rm -f "$DIR/update.sh.new"
        else
            rm -f "$DIR/update.sh.new"
        fi
    fi
fi

# ── bot process dhoondo (SIRF jiska aakhri arg bot.py) ────────────────────
BOT_PIDS() {
    for p in $(pgrep -f "bot\\.py" 2>/dev/null); do
        [ -r "/proc/$p/cmdline" ] || continue
        c="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)"
        last=""
        for w in $c; do last="$w"; done
        [ "$last" = "bot.py" ] && echo "$p"
    done
}

# ══════════════ 1) BOT DOWNLOAD ══════════════
[ -f bot.py ] && cp -f bot.py "backups/bot_$STAMP.py" && echo "💾 backup: backups/bot_$STAMP.py"

echo "→ bot download…"
if ! DL "$BOT_URL" bot.py.new; then
    echo "↩ primary fail, fallback…"
    if ! DL "$BOT_FB" bot.py.new; then
        echo "❌ download fail — net/URL check karo (purana bot chalu hai)"
        rm -f bot.py.new
        exit 1
    fi
fi

if [ ! -s bot.py.new ]; then
    echo "❌ khaali file — abort (purana bot chalu hai)"
    rm -f bot.py.new
    exit 1
fi
if ! grep -q "^VERSION = " bot.py.new || ! grep -q "^def main()" bot.py.new \
   || ! grep -q "ApplicationBuilder" bot.py.new; then
    echo "❌ file bot.py jaisi nahi lagti (HTML/error page?) — abort"
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
VER="$(grep -m1 '^VERSION = ' bot.py | cut -d'"' -f2)"
BUILD="$(grep -m1 '^BUILD = ' bot.py | cut -d'"' -f2)"

echo "✅ $DIR/bot.py"
# DBF copy — agar wahi folder hai to skip (same file error na aaye)
if [ "$(cd "$DIR" && pwd -P)" = "$(cd "$EXT" 2>/dev/null && pwd -P)" ]; then
    echo "ℹ️ DBF copy skip — yahi folder hai"
elif cp -f bot.py "$EXT/bot.py" 2>/dev/null; then
    echo "✅ $EXT/bot.py"
else
    echo "⚠️ DBF copy fail — 'termux-setup-storage' chala ke dobara ./update.sh"
fi
echo "✅ version: $VER  (build: ${BUILD:-?})"

# ══════════════ 3) RESTART ══════════════
if command -v screen >/dev/null 2>&1; then
    screen -S snake -X quit >/dev/null 2>&1
fi
OLD="$(BOT_PIDS)"
if [ -n "$OLD" ]; then
    echo "→ purana bot band (pids: $(echo "$OLD" | tr '\n' ' '))"
    for p in $OLD; do kill "$p" 2>/dev/null; done        # graceful SIGTERM
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        [ -z "$(BOT_PIDS)" ] && break
        sleep 1
    done
fi
LEFT="$(BOT_PIDS)"
if [ -n "$LEFT" ]; then
    echo "→ zabardasti band…"
    for p in $LEFT; do kill -9 "$p" 2>/dev/null; done
    sleep 2
fi

RLOG="$LOGDIR/bot_$STAMP.log"
START_OK=0
if [ -x "./restart.sh" ]; then
    ./restart.sh >/dev/null 2>&1 && START_OK=1
fi
if [ "$START_OK" != "1" ] && command -v screen >/dev/null 2>&1; then
    screen -dmS snake bash -c "cd '$DIR' && exec '$PY' bot.py > '$RLOG' 2>&1"
    START_OK=1
fi
if [ "$START_OK" != "1" ]; then
    setsid nohup "$PY" bot.py >"$RLOG" 2>&1 &
    START_OK=1
fi

sleep 6
PIDS="$(BOT_PIDS)"
if [ -n "$PIDS" ]; then
    echo "🚀 bot chalu hai (pid $(echo "$PIDS" | tr '\n' ' '))"
    command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q snake \
        && echo "🖥 screen: snake  →  dekhne ke liye: screen -r snake"
    echo "→ Telegram: /ping  →  $VER (build ${BUILD:-?})"
else
    echo "❌ bot start hote hi band ho gaya — log:"
    tail -n 20 "$RLOG" 2>/dev/null || echo "   (log khaali)"
    echo "   wapas: cp backups/bot_$STAMP.py bot.py && ./restart.sh"
    exit 1
fi
