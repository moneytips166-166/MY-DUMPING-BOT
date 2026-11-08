#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
. ./snake_lib.sh
if snake_alive; then
    echo "ℹ️ bot pehle se chal raha hai (pid $(snake_pids | tr '\n' ' '))"
    exit 0
fi
snake_start
