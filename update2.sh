#!/data/data/com.termux/files/usr/bin/bash
# 🐍 SHADOW X update (sirf bot #2 — new.py)
#   bash update2.sh
cd "$(dirname "$0")" || exit 1
UPD="$HOME/snake/update.sh"
[ -f "$UPD" ] || UPD="$(pwd)/update.sh"
if [ ! -f "$UPD" ]; then
    echo "❌ update.sh nahi mila — main bot ka update.sh chalao pehle"
    exit 1
fi
bash "$UPD" --shadow-only
