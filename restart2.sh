#!/data/data/com.termux/files/usr/bin/bash
# 🐍 SHADOW X restart  (bot #2 — new.py)
#   /storage/emulated/0 noexec hai → `bash restart2.sh` chalao
cd "$(dirname "$0")" || exit 1
. ./shadow_lib.sh
echo "🐍 SHADOW X restart — $(date '+%d-%m %H:%M:%S')"
shadow_kill_all
sleep 1
if shadow_alive; then echo "❌ purana process band nahi hua"; exit 1; fi
shadow_start
