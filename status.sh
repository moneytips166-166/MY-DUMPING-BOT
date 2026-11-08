#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
. ./snake_lib.sh
echo "🐍 PYTHON SNAKE — status"
echo "📁 dir  : $SNAKE_DIR"
echo "📦 file : $(snake_version)"
if snake_alive; then
    echo "🟢 running: pid $(snake_pids | tr '\n' ' ')"
else
    echo "🔴 running: nahi chal raha"
fi
if command -v screen >/dev/null 2>&1; then
    n=$(screen -ls 2>/dev/null | grep -c 'snake')
    echo "🖥 screen sessions: $n"
fi
[ -f .last_log ] && echo "📝 last log: $(cat .last_log)"
[ -f snake_config.json ] && grep -q '"bot_token": ""' snake_config.json 2>/dev/null \
    && echo "⚠️ token khaali — ./setconfig.sh --token <TOKEN>"
exit 0
