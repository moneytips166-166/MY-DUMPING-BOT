#!/data/data/com.termux/files/usr/bin/bash
# 🐍 DONO BOTS ka status — kaun chal raha hai, kaunsi file se, kaunsa data
#   bash bots.sh
cd "$(dirname "$0")" || exit 1

mask() { # token ko chhota karke dikhao
    [ -z "$1" ] && { echo "—"; return; }
    echo "$(echo "$1" | cut -d: -f1):••••$(echo "$1" | rev | cut -c1-4 | rev)"
}

echo "════════════════════════════════════════════════════"
echo "🐍 PYTHON SNAKE — dono bots"
echo "════════════════════════════════════════════════════"

# ── bot #1: bot.py ──────────────────────────────────
if [ -f ./snake_lib.sh ]; then
    . ./snake_lib.sh
    echo ""
    echo "① MAIN BOT  (bot.py)"
    echo "   file   : $SNAKE_RUN/bot.py"
    echo "   version: $(snake_version)"
    echo "   screen : snake"
    echo "   data   : $SNAKE_RUN/data"
    if snake_alive; then
        echo "   status : 🟢 RUNNING (pid $(snake_pids | tr '\n' ' '))"
    else
        echo "   status : ⚪ stopped"
    fi
    if [ -f ./snake_config.json ]; then
        echo "   token  : $(mask "$("$(snake_py)" -c 'import json;print((json.load(open("snake_config.json")) or {}).get("bot_token",""))' 2>/dev/null)")"
    fi
fi

# ── bot #2: new.py ──────────────────────────────────
if [ -f ./shadow_lib.sh ]; then
    . ./shadow_lib.sh
    echo ""
    echo "② SHADOW X  (new.py)"
    echo "   file   : $SHADOW_FILE"
    echo "   version: $(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$SHADOW_FILE" 2>/dev/null | head -1)"
    echo "   screen : shadow"
    echo "   data   : $SHADOW_DATA"
    if shadow_alive; then
        echo "   status : 🟢 RUNNING (pid $(shadow_pids | tr '\n' ' '))"
    else
        echo "   status : ⚪ stopped"
    fi
    echo "   token  : $(mask "$(shadow_token)")"
fi

echo ""
echo "────────────────────────────────────────────────────"
echo "COMMANDS (dono ek folder se)"
echo "  bash update.sh    → dono files update (bot.py + new.py)"
echo "  bash restart.sh   → main bot restart"
echo "  bash restart2.sh  → shadow restart"
echo "  bash stop.sh      → main stop     bash stop2.sh → shadow stop"
echo "  bash status.sh    → main status   bash status2.sh → shadow status"
echo "  bash bots.sh      → ye screen"
echo "────────────────────────────────────────────────────"
