#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
. ./snake_lib.sh
echo "🐍 PYTHON SNAKE restart — $(date '+%d-%m %H:%M:%S')"
echo "📦 version: $(snake_version)"
if snake_alive; then
    echo "→ purana process band: $(snake_pids | tr '\n' ' ')"
else
    echo "→ koi purana process nahi mila"
fi
snake_kill_all
sleep 1
if snake_alive; then
    echo "❌ purana process band nahi hua — kill -9 $(snake_pids | tr '\n' ' ')"
    exit 1
fi
if ! snake_start; then
    echo ""
    echo "↩️ wapas: cp backups/$(ls -t backups/bot_*.py 2>/dev/null | head -1 | xargs -r basename) bot.py && ./restart.sh"
    exit 1
fi
[ -f snake_config.json ] && ! grep -q '"bot_token": ""' snake_config.json 2>/dev/null \
    && echo "🔐 token/admin config se load honge"
echo "✅ done — Telegram me /ping bhejo (v$(snake_version | sed 's/^v//'))"
