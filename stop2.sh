#!/data/data/com.termux/files/usr/bin/bash
# 🐍 SHADOW X stop  (bot #2 — new.py)
#   /storage/emulated/0 noexec hai → `bash stop2.sh` chalao
cd "$(dirname "$0")" || exit 1
. ./shadow_lib.sh
shadow_kill_all
if shadow_alive; then echo "❌ band nahi hua"; exit 1; fi
echo "⛔ SHADOW X stopped"
