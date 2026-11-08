#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — start (agar pehle se chal raha hai to batata hai)
cd "$(dirname "$0")" || exit 1
# shellcheck source=snake_lib.sh
. ./snake_lib.sh

if snake_alive; then
    echo "ℹ️ bot pehle se chal raha hai (pid $(snake_pids | tr '\n' ' '))"
    echo "   dubara restart chahiye to: ./restart.sh"
    exit 0
fi
snake_start
