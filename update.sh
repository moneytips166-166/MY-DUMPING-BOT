
#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE updater bootstrap (SNAKE_BOOT_V=6)
# Ye hamesha latest updater download karta hai, phir use chalata hai.
# 3 tarike: raw.githubusercontent → api.github.com → codeload tarball
# (India me raw kabhi block hota hai — isliye fallback zaroori hai)
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
API="https://api.github.com/repos/$REPO/contents"
cd "$DIR" || exit 1

DL() { if command -v curl >/dev/null 2>&1; then curl -fsSL --max-time 90 "$1" -o "$2";
       else wget -q -T 90 "$1" -O "$2"; fi; }
API_DL() {
    command -v curl >/dev/null 2>&1 || return 1
    curl -fsSL --max-time 90 -H "Accept: application/vnd.github.raw" \
        "$API/$1?ref=$BRANCH" -o "$2" 2>/dev/null && [ -s "$2" ] \
        && ! head -c 200 "$2" | grep -q '"message": *"Not Found"'
}
TAR_DL() {
    for u in "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" \
             "https://api.github.com/repos/$REPO/tarball/$BRANCH" \
             "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"; do
        rm -rf .repo.x .repo.tar.gz
        DL "$u" .repo.tar.gz 2>/dev/null || continue
        [ -s .repo.tar.gz ] || continue
        mkdir -p .repo.x
        tar -xzf .repo.tar.gz -C .repo.x 2>/dev/null || continue
        _d="$(find .repo.x -maxdepth 1 -mindepth 1 -type d 2>/dev/null | head -1)"
        if [ -n "$_d" ] && [ -f "$_d/vps/termux_update.sh" ]; then
            cp -f "$_d/vps/termux_update.sh" .upd.new
            rm -rf .repo.x .repo.tar.gz
            return 0
        fi
        rm -rf .repo.x .repo.tar.gz
    done
    return 1
}

OK=0
DL "https://raw.githubusercontent.com/$REPO/$BRANCH/vps/termux_update.sh" .upd.new 2>/dev/null \
    && grep -q "SNAKE_UPDATER_V" .upd.new 2>/dev/null && OK=1
if [ "$OK" != "1" ]; then
    DL "https://github.com/$REPO/raw/$BRANCH/vps/termux_update.sh" .upd.new 2>/dev/null \
        && grep -q "SNAKE_UPDATER_V" .upd.new 2>/dev/null && OK=1
fi
if [ "$OK" != "1" ]; then
    API_DL "vps/termux_update.sh" .upd.new && \
        grep -q "SNAKE_UPDATER_V" .upd.new 2>/dev/null && OK=1
fi
if [ "$OK" != "1" ]; then
    TAR_DL && grep -q "SNAKE_UPDATER_V" .upd.new 2>/dev/null && OK=1
fi

if [ "$OK" = "1" ] && bash -n .upd.new 2>/dev/null; then
    mv -f .upd.new update_run.sh
    chmod +x update_run.sh
    SNAKE_NO_SELF=1 exec bash ./update_run.sh "$@"
fi

rm -f .upd.new
rm -rf .repo.x .repo.tar.gz
echo "❌ updater download nahi hua — internet check karo"
echo "   WiFi/data ON? Browser me github.com khulta hai?"
echo "   retry: ./update.sh"
exit 1
