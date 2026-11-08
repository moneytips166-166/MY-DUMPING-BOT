#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
. ./snake_lib.sh
if ! snake_alive; then
    snake_screen_kill
    echo "ℹ️ bot pehle se band hai"
    exit 0
fi
echo "→ band: $(snake_pids | tr '\n' ' ')"
snake_kill_all
snake_alive && { echo "❌ band nahi hua"; exit 1; }
echo "✅ band"
