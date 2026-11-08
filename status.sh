#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — status (zinda hai? kaun sa version? log kahan?)
cd "$(dirname "$0")" || exit 1
# shellcheck source=snake_lib.sh
. ./snake_lib.sh

echo "🐍 PYTHON SNAKE — status"
echo "📁 dir     : $SNAKE_DIR"
echo "📦 file    : $(snake_version)   ($(date -r bot.py '+%d-%m %H:%M' 2>/dev/null || echo '?'))"
[ -f "$SNAKE_EXT/bot.py" ] && \
    echo "📦 DBF     : $(grep -m1 '^VERSION = ' "$SNAKE_EXT/bot.py" | cut -d'"' -f2)"
if snake_alive; then
    echo "🟢 running : pid $(snake_pids | tr '\n' ' ')"
    command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q "$SNAKE_SCREEN" \
        && echo "🖥 screen  : $SNAKE_SCREEN"
else
    echo "🔴 running : nahi chal raha"
fi
[ -f .last_log ] && echo "📝 last log: $(cat .last_log)"
[ -f snake_config.json ] && grep -q '"bot_token": ""' snake_config.json 2>/dev/null \
    && echo "⚠️ token khaali — ./setconfig.sh --token <TOKEN>"
exit 0
