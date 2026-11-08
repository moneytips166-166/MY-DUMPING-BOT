#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — restart (purana process zabardasti band → naya fresh start)
#   ./restart.sh          → kill sab + latest bot.py se start
#   ./restart.sh --keep   → sirf process restart (file touch nahi)
cd "$(dirname "$0")" || exit 1
# shellcheck source=snake_lib.sh
. ./snake_lib.sh

echo "🐍 PYTHON SNAKE restart — $(date '+%d-%m %H:%M:%S')"
echo "📦 version: $(snake_version)"

# 1) jo bhi chal raha hai — sab band (screen + nohup dono)
if snake_alive; then
    echo "→ purana process band: $(snake_pids | tr '\n' ' ')"
else
    echo "→ koi purana process nahi mila"
fi
snake_kill_all

if snake_alive; then
    echo "❌ purana process band nahi hua (pid $(snake_pids | tr '\n' ' '))"
    echo "   kill -9 $(snake_pids | tr '\n' ' ')  → phir ./restart.sh"
    exit 1
fi
sleep 1

# 2) fresh start
if ! snake_start; then
    echo ""
    echo "↩️ purana backup wapas chahiye to:"
    echo "   cp backups/$(ls -t backups/bot_*.py 2>/dev/null | head -1 | xargs -r basename) bot.py && ./restart.sh"
    exit 1
fi

# 3) token check
[ -f snake_config.json ] && ! grep -q '"bot_token": ""' snake_config.json 2>/dev/null \
    && echo "🔐 token/admin config se load honge"
echo "✅ done — Telegram me /ping bhejo (v$(snake_version | sed 's/^v//'))"
