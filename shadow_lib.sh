#!/data/data/com.termux/files/usr/bin/bash
# 🐍 SHADOW X — bot #2 helpers  (SHADOW_LIB_V=1)
#   Main bot  : /storage/emulated/0/DBF/bot.py   → ./start.sh    ./stop.sh    ./restart.sh
#   Shadow    : /storage/emulated/0/DBF/new.py   → ./start2.sh   ./stop2.sh   ./restart2.sh
#   Dono ek hi folder (DBF) me, par alag screen session + alag data folder.
SHADOW_LIB_V=1

SHADOW_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHADOW_DBF="${SHADOW_DBF:-/storage/emulated/0/DBF}"
SHADOW_SCREEN="shadow"

# new.py kahan hai — pehle DBF, phir script ke saath wala shadow/
if [ -f "$SHADOW_DBF/new.py" ]; then
    SHADOW_RUN_DIR="$SHADOW_DBF"
elif [ -f "$SHADOW_HOME/shadow/new.py" ]; then
    SHADOW_RUN_DIR="$SHADOW_HOME/shadow"
else
    SHADOW_RUN_DIR="$SHADOW_DBF"
fi
SHADOW_FILE="$SHADOW_RUN_DIR/new.py"
# data ALAG — main bot ke data/ se takrao na ho
SHADOW_DATA="${SHADOW_DATA_DIR:-$SHADOW_RUN_DIR/shadow_data}"
SHADOW_LOGDIR="$SHADOW_HOME/logs"          # internal storage (writable + fast)
mkdir -p "$SHADOW_LOGDIR" "$SHADOW_DATA" 2>/dev/null

shadow_py() { command -v python3 2>/dev/null || command -v python 2>/dev/null; }

# SIRF asli shadow process (last arg new.py)
shadow_pids() {
    for p in $(pgrep -f "new\.py" 2>/dev/null); do
        [ -r "/proc/$p/cmdline" ] || continue
        _c="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)"
        _last=""
        for _w in $_c; do _last="$_w"; done
        case "$_last" in
            new.py|*/new.py) [ "$p" != "$$" ] && echo "$p" ;;
        esac
    done
}
shadow_alive() { [ -n "$(shadow_pids)" ]; }

shadow_screen_kill() {
    command -v screen >/dev/null 2>&1 || return 0
    screen -ls 2>/dev/null \
        | sed -n 's/^[[:space:]]*\([0-9][0-9]*\.shadow[^[:space:]]*\).*/\1/p' \
        | while read -r sid; do screen -S "$sid" -X quit >/dev/null 2>&1; done
    screen -S "$SHADOW_SCREEN" -X quit >/dev/null 2>&1
    screen -wipe >/dev/null 2>&1
}

shadow_kill_all() {
    local waited=0 pids
    shadow_screen_kill
    pids="$(shadow_pids)"
    if [ -n "$pids" ]; then
        for p in $pids; do kill "$p" 2>/dev/null; done
        while [ -n "$(shadow_pids)" ] && [ "$waited" -lt 8 ]; do
            sleep 1; waited=$((waited + 1))
        done
    fi
    pids="$(shadow_pids)"
    if [ -n "$pids" ]; then
        for p in $pids; do kill -9 "$p" 2>/dev/null; done
        sleep 1
    fi
    shadow_screen_kill
}

# token: env → shadow_config.json (DBF / shadow folder) → new.py ka default
shadow_token() {
    if [ -n "${SHADOW_TOKEN:-}" ]; then
        printf '%s' "$SHADOW_TOKEN"; return 0
    fi
    local f t py
    py="$(shadow_py)"
    for f in "$SHADOW_RUN_DIR/shadow_config.json" \
             "$SHADOW_HOME/shadow_config.json" \
             "$SHADOW_HOME/shadow/shadow_config.json"; do
        [ -f "$f" ] || continue
        t="$("$py" -c 'import json,sys
try:
    print((json.load(open(sys.argv[1])) or {}).get("token","") or "")
except Exception:
    print("")' "$f" 2>/dev/null)"
        [ -n "$t" ] && { printf '%s' "$t"; return 0; }
    done
    t="$(sed -n 's/^DEFAULT_TOKEN = "\([^"]*\)".*/\1/p' "$SHADOW_FILE" 2>/dev/null | head -1)"
    printf '%s' "$t"
}

# deps (pyTelegramBotAPI + aiohttp) — na ho to ek baar install
shadow_deps() {
    local py; py="$(shadow_py)"
    [ -z "$py" ] && return 1
    "$py" -c "import telebot, aiohttp" >/dev/null 2>&1 && return 0
    echo "📦 shadow deps install ho rahi hain (pyTelegramBotAPI, aiohttp)…"
    if command -v pip >/dev/null 2>&1; then
        pip install -q --disable-pip-version-check pyTelegramBotAPI aiohttp 2>/dev/null
    else
        "$py" -m pip install -q --disable-pip-version-check pyTelegramBotAPI aiohttp 2>/dev/null
    fi
    "$py" -c "import telebot, aiohttp" >/dev/null 2>&1
}

shadow_start() {
    local py log tok name="$SHADOW_SCREEN"
    py="$(shadow_py)"
    [ -z "$py" ] && { echo "❌ python nahi mila — pkg install python"; return 1; }
    [ -f "$SHADOW_FILE" ] || { echo "❌ new.py nahi mila ($SHADOW_RUN_DIR)"; return 1; }
    shadow_deps || echo "⚠️ deps install fail — 'pip install pyTelegramBotAPI aiohttp'"
    tok="$(shadow_token)"
    [ -z "$tok" ] && echo "⚠️ token nahi mila — new.py ka default use hoga"
    shadow_kill_all
    mkdir -p "$SHADOW_DATA" "$SHADOW_LOGDIR"
    log="$SHADOW_LOGDIR/shadow_$(date +%Y%m%d_%H%M%S).log"
    if command -v screen >/dev/null 2>&1; then
        screen -dmS "$name" bash -c "cd '$SHADOW_RUN_DIR' && SHADOW_TOKEN='$tok' SHADOW_DATA_DIR='$SHADOW_DATA' exec '$py' -u new.py >> '$log' 2>&1"
    else
        ( cd "$SHADOW_RUN_DIR" && SHADOW_TOKEN="$tok" SHADOW_DATA_DIR="$SHADOW_DATA" \
          nohup "$py" -u new.py >>"$log" 2>&1 & )
    fi
    echo "$log" > "$SHADOW_HOME/.shadow_log"
    sleep 5
    shadow_alive || sleep 4
    if shadow_alive; then
        echo "🚀 SHADOW X chalu hai (pid $(shadow_pids | tr '\n' ' '))"
        echo "📂 $SHADOW_FILE"
        echo "🗄 data: $SHADOW_DATA"
        echo "🖥 screen: $name  →  screen -r $name"
        echo "📄 log: $log"
        return 0
    fi
    echo "❌ shadow start nahi hua — log:"
    tail -n 20 "$log" 2>/dev/null
    return 1
}
