

#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE helpers  (SNAKE_LIB_V=6)
SNAKE_LIB_V=6
SNAKE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNAKE_EXT="/storage/emulated/0/DBF"
SNAKE_SCREEN="snake"
SNAKE_LOGDIR="$SNAKE_DIR/logs"
mkdir -p "$SNAKE_LOGDIR" "$SNAKE_DIR/backups" 2>/dev/null

snake_py() { command -v python3 2>/dev/null || command -v python 2>/dev/null; }

# SIRF asli bot process (last arg bot.py) — screen/bash wrappers nahi
snake_pids() {
    for p in $(pgrep -f "bot\.py" 2>/dev/null); do
        [ -r "/proc/$p/cmdline" ] || continue
        _c="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)"
        _last=""; for _w in $_c; do _last="$_w"; done
        # relative ("bot.py") aur absolute ("/path/bot.py") dono
        case "$_last" in
            bot.py|*/bot.py) [ "$p" != "$$" ] && echo "$p" ;;
        esac
    done
}
snake_alive() { [ -n "$(snake_pids)" ]; }

# screen sessions jo "snake" naam se hain — "1234.snake" / "1234.snake_x" dono
snake_screen_kill() {
    command -v screen >/dev/null 2>&1 || return 0
    screen -ls 2>/dev/null \
        | sed -n 's/^[[:space:]]*\([0-9][0-9]*\.snake[^[:space:]]*\).*/\1/p' \
        | while read -r sid; do
            screen -S "$sid" -X quit >/dev/null 2>&1
        done
    # jo bhi naam me snake hai (koi bhi prefix)
    screen -ls 2>/dev/null | grep -i 'snake' \
        | sed -n 's/^[[:space:]]*\([0-9][0-9]*\.[^[:space:]]*\).*/\1/p' \
        | while read -r sid; do
            screen -S "$sid" -X quit >/dev/null 2>&1
        done
    screen -S "$SNAKE_SCREEN" -X quit >/dev/null 2>&1
    screen -wipe >/dev/null 2>&1
}

snake_lock_clear() {
    rm -f "$SNAKE_DIR/.snake.lock" "$SNAKE_EXT/.snake.lock" \
          "$HOME/snake/.snake.lock" 2>/dev/null
}

snake_kill_all() {
    local waited=0 pids
    snake_screen_kill
    pids="$(snake_pids)"
    if [ -n "$pids" ]; then
        for p in $pids; do kill "$p" 2>/dev/null; done
        while [ -n "$(snake_pids)" ] && [ "$waited" -lt 8 ]; do
            sleep 1; waited=$((waited + 1))
        done
    fi
    pids="$(snake_pids)"
    if [ -n "$pids" ]; then
        for p in $pids; do kill -9 "$p" 2>/dev/null; done
        sleep 1
    fi
    snake_screen_kill
    snake_lock_clear
}

snake_start() {
    local py log rc=1 waited=0 name="$SNAKE_SCREEN"
    py="$(snake_py)"
    [ -z "$py" ] && { echo "❌ python nahi mila — pkg install python"; return 1; }
    [ -f "$SNAKE_DIR/bot.py" ] || { echo "❌ bot.py nahi mila ($SNAKE_DIR)"; return 1; }
    log="$SNAKE_LOGDIR/bot_$(date +%Y%m%d_%H%M%S).log"
    cd "$SNAKE_DIR" || return 1
    snake_lock_clear

    if command -v screen >/dev/null 2>&1; then
        snake_screen_kill
        if ! screen -dmS "$name" bash -c "cd '$SNAKE_DIR' && exec '$py' bot.py >> '$log' 2>&1"; then
            # naam clash (purana session zinda) → unique naam, phir bhi chalta rahe
            name="snake_$(date +%s)"
            echo "→ 'snake' session clash — naya naam: $name"
            screen -dmS "$name" bash -c "cd '$SNAKE_DIR' && exec '$py' bot.py >> '$log' 2>&1"
        fi
        rc=0
    fi
    if [ "$rc" != "0" ]; then
        nohup "$py" bot.py >>"$log" 2>&1 &
        rc=0
    fi

    while [ "$waited" -lt 12 ]; do
        sleep 1; waited=$((waited + 1))
        snake_alive && break
    done
    echo "$log" > "$SNAKE_DIR/.last_log"
    if snake_alive; then
        echo "🚀 bot chalu (pid $(snake_pids | tr '\n' ' '))"
        echo "📝 log: $log"
        command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q snake \
            && echo "🖥 screen: $name  →  screen -r $name"
        return 0
    fi
    echo "❌ bot start nahi hua — log tail:"
    tail -n 25 "$log" 2>/dev/null || echo "   (log khaali)"
    return 1
}

snake_version() {
    [ -f "$SNAKE_DIR/bot.py" ] && \
        grep -m1 '^VERSION = ' "$SNAKE_DIR/bot.py" | cut -d'"' -f2 || echo "?"
}
