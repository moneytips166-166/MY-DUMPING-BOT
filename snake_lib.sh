#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — shared helpers (baaki scripts isi ko source karti hain)
# SNAKE_LIB_V=4
SNAKE_LIB_V=4

SNAKE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNAKE_EXT="/storage/emulated/0/DBF"
SNAKE_SCREEN="snake"
SNAKE_LOGDIR="$SNAKE_DIR/logs"
mkdir -p "$SNAKE_LOGDIR" "$SNAKE_DIR/backups" 2>/dev/null

snake_py() {
    command -v python3 2>/dev/null || command -v python 2>/dev/null
}

# Sirf wahi process jo ASLI bot.py chala raha hai (last arg = bot.py)
snake_pids() {
    for p in $(pgrep -f "bot\.py" 2>/dev/null); do
        [ -r "/proc/$p/cmdline" ] || continue
        _c="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)"
        _last=""
        for _w in $_c; do _last="$_w"; done
        [ "$_last" = "bot.py" ] && [ "$p" != "$$" ] && echo "$p"
    done
}

snake_alive() {
    [ -n "$(snake_pids)" ]
}

snake_kill_all() {
    local waited=0
    command -v screen >/dev/null 2>&1 && screen -S "$SNAKE_SCREEN" -X quit >/dev/null 2>&1
    local pids
    pids="$(snake_pids)"
    if [ -n "$pids" ]; then
        for p in $pids; do kill "$p" 2>/dev/null; done
        while [ -n "$(snake_pids)" ] && [ "$waited" -lt 8 ]; do
            sleep 1
            waited=$((waited + 1))
        done
    fi
    pids="$(snake_pids)"
    if [ -n "$pids" ]; then
        for p in $pids; do kill -9 "$p" 2>/dev/null; done
        sleep 1
    fi
}

# Bot start — screen pehle, phir nohup (Termux me setsid NAHI hota)
snake_start() {
    local py log rc=1
    py="$(snake_py)"
    [ -z "$py" ] && { echo "❌ python nahi mila — pkg install python"; return 1; }
    [ -f "$SNAKE_DIR/bot.py" ] || { echo "❌ bot.py nahi mila ($SNAKE_DIR)"; return 1; }
    log="$SNAKE_LOGDIR/bot_$(date +%Y%m%d_%H%M%S).log"

    if command -v screen >/dev/null 2>&1; then
        screen -dmS "$SNAKE_SCREEN" bash -c \
            "cd '$SNAKE_DIR' && exec '$py' bot.py >> '$log' 2>&1"
        rc=0
    fi
    if [ "$rc" != "0" ]; then
        cd "$SNAKE_DIR" || return 1
        nohup "$py" bot.py >>"$log" 2>&1 &
        rc=0
    fi
    cd "$SNAKE_DIR" 2>/dev/null

    local waited=0
    while [ "$waited" -lt 10 ]; do
        sleep 1
        waited=$((waited + 1))
        snake_alive && break
    done
    if snake_alive; then
        echo "🚀 bot chalu (pid $(snake_pids | tr '\n' ' '))"
        echo "📝 log: $log"
        command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q "$SNAKE_SCREEN" \
            && echo "🖥 screen: $SNAKE_SCREEN  →  screen -r $SNAKE_SCREEN"
        echo "$log" > "$SNAKE_DIR/.last_log"
        return 0
    fi
    echo "❌ bot start nahi hua — log tail:"
    tail -n 25 "$log" 2>/dev/null || echo "   (log khaali)"
    echo "$log" > "$SNAKE_DIR/.last_log"
    return 1
}

snake_version() {
    [ -f "$SNAKE_DIR/bot.py" ] && \
        grep -m1 '^VERSION = ' "$SNAKE_DIR/bot.py" | cut -d'"' -f2 || echo "?"
}
