#!/data/data/com.termux/files/usr/bin/bash
# 🐍 SHADOW X start  (bot #2 — new.py)
#   /storage/emulated/0 noexec hai → `bash start2.sh` chalao
cd "$(dirname "$0")" || exit 1
. ./shadow_lib.sh
if shadow_alive; then
    echo "ℹ️ SHADOW pehle se chal raha hai (pid $(shadow_pids | tr '\n' ' '))"
    exit 0
fi
shadow_start
