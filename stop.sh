#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — stop (sab sessions + process saaf)
cd "$(dirname "$0")" || exit 1
# shellcheck source=snake_lib.sh
. ./snake_lib.sh

if ! snake_alive; then
    command -v screen >/dev/null 2>&1 && screen -S "$SNAKE_SCREEN" -X quit >/dev/null 2>&1
    echo "ℹ️ bot pehle se band hai"
    exit 0
fi
echo "→ band kar rahe hain: $(snake_pids | tr '\n' ' ')"
snake_kill_all
if snake_alive; then
    echo "❌ band nahi hua — manual: kill -9 $(snake_pids | tr '\n' ' ')"
    exit 1
fi
echo "✅ bot band hai"
