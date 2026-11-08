#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE updater bootstrap (SNAKE_BOOT_V=5)
# Ye hamesha latest updater download karta hai, phir use chalata hai.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
URL1="https://raw.githubusercontent.com/$REPO/$BRANCH/vps/termux_update.sh"
URL2="https://github.com/$REPO/raw/$BRANCH/vps/termux_update.sh"
cd "$DIR" || exit 1

DL() { if command -v curl >/dev/null 2>&1; then curl -fsSL --max-time 60 "$1" -o "$2";
       else wget -q -T 60 "$1" -O "$2"; fi; }

if DL "$URL1" .upd.new 2>/dev/null || DL "$URL2" .upd.new 2>/dev/null; then
    if grep -q "SNAKE_UPDATER_V" .upd.new 2>/dev/null && bash -n .upd.new 2>/dev/null; then
        mv -f .upd.new update_run.sh
        chmod +x update_run.sh
        SNAKE_NO_SELF=1 exec bash ./update_run.sh "$@"
    fi
    rm -f .upd.new
fi
echo "❌ updater download nahi hua — internet check karo"
echo "   retry: ./update.sh"
exit 1
