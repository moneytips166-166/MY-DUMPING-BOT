#!/data/data/com.termux/files/usr/bin/bash
# 🐍 SHADOW X status  (bot #2 — new.py)
#   /storage/emulated/0 noexec hai → `bash status2.sh` chalao
cd "$(dirname "$0")" || exit 1
. ./shadow_lib.sh
if shadow_alive; then
    echo "🟢 SHADOW X running (pid $(shadow_pids | tr '\n' ' '))"
    echo "📂 $SHADOW_FILE"
    echo "🗄 data: $SHADOW_DATA"
    command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q "shadow" \
        && echo "🖥 screen: shadow"
else
    echo "⚪ SHADOW X not running"
fi
