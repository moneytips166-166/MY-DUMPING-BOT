#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — Termux updater  (SNAKE_UPDATER_V=4)
#   ./update.sh   →  khud ko latest karta hai, phir bot.py (Termux + DBF) + restart
#   ./update.sh --no-self   →  self-update skip
# NOTE: Termux me /tmp writable nahi — log script folder ke logs/ me jata hai.
set -u
UPDATER_V=3

REPO="moneytips166-166/MY-DUMPING-BOT"
BRANCH="arena/063f862a-my-dumping-bot"
DIR="$(cd "$(dirname "$0")" && pwd)"
EXT="/storage/emulated/0/DBF"
STAMP="$(date +%Y%m%d_%H%M%S)"
BOT_URL="${SNAKE_URL:-https://raw.githubusercontent.com/$REPO/$BRANCH/bot.py}"
BOT_FB="https://github.com/$REPO/raw/$BRANCH/bot.py"
SELF_URL="https://raw.githubusercontent.com/$REPO/$BRANCH/vps/termux_update.sh"
SELF_FB="https://github.com/$REPO/raw/$BRANCH/vps/termux_update.sh"
SELFC_URL="https://raw.githubusercontent.com/$REPO/$BRANCH/setconfig.sh"
SELFC_FB="https://github.com/$REPO/raw/$BRANCH/setconfig.sh"
RAW="https://raw.githubusercontent.com/$REPO/$BRANCH"
GH="https://github.com/$REPO/raw/$BRANCH"
# jo helper scripts har update pe refresh honge (phone pe purane tuten nahi chalenge)
HELPERS="snake_lib.sh start.sh stop.sh restart.sh status.sh"
LOGDIR="$DIR/logs"
mkdir -p "$DIR/backups" "$LOGDIR" 2>/dev/null
LOG="$LOGDIR/compile_$$.txt"
cd "$DIR" || exit 1

PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
if [ -z "$PY" ]; then
    echo "❌ python nahi mila — 'pkg install python' chalao"
    exit 1
fi
if command -v curl >/dev/null 2>&1; then
    DL() { curl -fsSL --max-time 60 "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    DL() { wget -q -T 60 "$1" -O "$2"; }
else
    echo "❌ curl/wget nahi mila — 'pkg install curl' chalao"
    exit 1
fi

# ── 0) SELF-UPDATE — ./update.sh hamesha latest rahe ──────────────────────
if [ "${SNAKE_NO_SELF:-0}" != "1" ] && [ "${1:-}" != "--no-self" ] && [ -w "$0" ]; then
    if DL "$SELF_URL" "$DIR/update.sh.new" 2>/dev/null \
       || DL "$SELF_FB" "$DIR/update.sh.new" 2>/dev/null; then
        if grep -q "SNAKE_UPDATER_V" "$DIR/update.sh.new" 2>/dev/null \
           && bash -n "$DIR/update.sh.new" 2>/dev/null; then
            chmod +x "$DIR/update.sh.new" 2>/dev/null
            if ! cmp -s "$DIR/update.sh.new" "$0" 2>/dev/null; then
                echo "🔄 updater script bhi naya mila — use kar rahe hain"
                mv -f "$DIR/update.sh.new" "$0"
                SNAKE_NO_SELF=1 exec bash "$0" --no-self
            fi
            rm -f "$DIR/update.sh.new"
        else
            rm -f "$DIR/update.sh.new"
        fi
    fi
fi

# ── bot process dhoondo (SIRF jiska aakhri arg bot.py) ────────────────────
BOT_PIDS() {
    for p in $(pgrep -f "bot\\.py" 2>/dev/null); do
        [ -r "/proc/$p/cmdline" ] || continue
        c="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)"
        last=""
        for w in $c; do last="$w"; done
        [ "$last" = "bot.py" ] && echo "$p"
    done
}

# ══════════════ 1) BOT DOWNLOAD ══════════════
[ -f bot.py ] && cp -f bot.py "backups/bot_$STAMP.py" && echo "💾 backup: backups/bot_$STAMP.py"

# ── 1.5) 🔐 CONFIG GUARD — token/admin update me KABHI delete nahi honge ──
#  bot.py replace hota hai, par ye file nahi chhooti.
CFG="$DIR/snake_config.json"
if [ ! -f "$CFG" ]; then
    "$PY" - "$CFG" <<'PYEOF'
import glob, json, os, re, sys, time

out = sys.argv[1]


def grab(path):
    """bot.py (ya backup) se token + admins nikalo."""
    tok, adm = "", []
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return tok, adm
    m = re.search(r"^BOT_TOKEN\s*=\s*[\"']([^\"']*)[\"']", src, re.M)
    if m:
        tok = m.group(1).strip()
    if "PUT_YOUR" in tok or ":" not in tok or len(tok) < 20:
        tok = ""
    m = re.search(r"^ADMIN_IDS\s*=\s*\[([^\]]*)\]", src, re.M)
    if m:
        adm = [int(x) for x in re.findall(r"\d{5,}", m.group(1))]
    return tok, adm


cands = [p for p in ("bot.py", "bot.py.new") if os.path.isfile(p)]
cands += sorted(glob.glob("backups/bot_*.py"), reverse=True)[:6]   # naye pehle
tok, adm, src_used = "", [], ""
for pth in cands:
    t, a = grab(pth)
    if t and not tok:
        tok, src_used = t, pth
    for x in a:
        if x not in adm:
            adm.append(x)
    if tok and adm:
        break

if not tok and not adm:
    print("🔐 config nahi mila (token khaali) — ./setconfig.sh --token <TOKEN>")
else:
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"bot_token": tok, "admin_ids": adm, "brand": "PYTHON SNAKE",
                   "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "note": "Token/Admin yahan safe hain — ./update.sh inse touch nahi karta"},
                  f, indent=2)
    print("🔐 config banaya (%s se) — token %s, admins %d" %
          (src_used or "-", "✅" if tok else "❌ khaali", len(adm)))
PYEOF
fi
if [ -f "$CFG" ]; then
    chmod 600 "$CFG" 2>/dev/null
    echo "🔐 config safe hai: $CFG (isse touch nahi kiya)"
fi

echo "→ bot download…"
if ! DL "$BOT_URL" bot.py.new; then
    echo "↩ primary fail, fallback…"
    if ! DL "$BOT_FB" bot.py.new; then
        echo "❌ download fail — net/URL check karo (purana bot chalu hai)"
        rm -f bot.py.new
        exit 1
    fi
fi

if [ ! -s bot.py.new ]; then
    echo "❌ khaali file — abort (purana bot chalu hai)"
    rm -f bot.py.new
    exit 1
fi
if ! grep -q "^VERSION = " bot.py.new || ! grep -q "^def main()" bot.py.new \
   || ! grep -q "ApplicationBuilder" bot.py.new; then
    echo "❌ file bot.py jaisi nahi lagti (HTML/error page?) — abort"
    head -3 bot.py.new 2>/dev/null
    rm -f bot.py.new
    exit 1
fi

# ══════════════ 2) COMPILE ══════════════
if ! "$PY" -m py_compile bot.py.new 2>"$LOG"; then
    echo "❌ naya bot.py compile nahi hua — purana hi chal raha hai"
    cat "$LOG" 2>/dev/null
    rm -f bot.py.new "$LOG"
    exit 1
fi
rm -f "$LOG"

mv -f bot.py.new bot.py
VER="$(grep -m1 '^VERSION = ' bot.py | cut -d'"' -f2)"
BUILD="$(grep -m1 '^BUILD = ' bot.py | cut -d'"' -f2)"

echo "✅ $DIR/bot.py"
# DBF copy — agar wahi folder hai to skip (same file error na aaye)
if [ "$(cd "$DIR" && pwd -P)" = "$(cd "$EXT" 2>/dev/null && pwd -P)" ]; then
    echo "ℹ️ DBF copy skip — yahi folder hai"
elif cp -f bot.py "$EXT/bot.py" 2>/dev/null; then
    echo "✅ $EXT/bot.py"
else
    echo "⚠️ DBF copy fail — 'termux-setup-storage' chala ke dobara ./update.sh"
fi
echo "✅ version: $VER  (build: ${BUILD:-?})"

# 🔐 config DBF folder me bhi (bot wahan se chale to bhi token mile)
if [ -f "$CFG" ] && [ -d "$EXT" ] && \
   [ "$(cd "$DIR" && pwd -P)" != "$(cd "$EXT" && pwd -P)" ]; then
    if [ ! -f "$EXT/snake_config.json" ]; then
        cp -f "$CFG" "$EXT/snake_config.json" 2>/dev/null \
            && echo "🔐 DBF config copy ✅"
    fi
fi

# ══════════════ 3) SCRIPTS REFRESH ══════════════
# Ye scripts hi phone pe "restart kaam nahi karta" ka karan thi — repo me hi
# nahi thi. Ab har update pe nayi install hoti hain.
_install_script() {                       # $1 = filename, $2 = marker (sanity)
    if DL "$RAW/$1" "$DIR/$1.new" 2>/dev/null || DL "$GH/$1" "$DIR/$1.new" 2>/dev/null; then
        if [ -s "$DIR/$1.new" ] && grep -q "$2" "$DIR/$1.new" 2>/dev/null \
           && bash -n "$DIR/$1.new" 2>/dev/null; then
            mv -f "$DIR/$1.new" "$DIR/$1"
            chmod +x "$DIR/$1" 2>/dev/null
            return 0
        fi
        rm -f "$DIR/$1.new"
    fi
    return 1
}
_install_script snake_lib.sh "snake_alive" && echo "✅ snake_lib.sh" \
    || echo "⚠️ snake_lib.sh download fail (purana chalega)"
for _s in start.sh stop.sh restart.sh status.sh; do
    case "$_s" in
        start.sh)   _m="snake_start" ;;
        stop.sh)    _m="snake_kill_all" ;;
        restart.sh) _m="PYTHON SNAKE restart" ;;
        *)          _m="PYTHON SNAKE" ;;
    esac
    _install_script "$_s" "$_m" && echo "✅ $_s" || echo "⚠️ $_s fail"
done

# setconfig.sh bhi install/refresh (token badalne ka official tarika)
if DL "$SELFC_URL" "$DIR/setconfig.sh.new" 2>/dev/null \
   || DL "$SELFC_FB" "$DIR/setconfig.sh.new" 2>/dev/null; then
    if grep -q "setconfig" "$DIR/setconfig.sh.new" 2>/dev/null \
       && bash -n "$DIR/setconfig.sh.new" 2>/dev/null; then
        mv -f "$DIR/setconfig.sh.new" "$DIR/setconfig.sh"
        chmod +x "$DIR/setconfig.sh" 2>/dev/null
    else
        rm -f "$DIR/setconfig.sh.new"
    fi
fi

if command -v screen >/dev/null 2>&1; then
    screen -S snake -X quit >/dev/null 2>&1
fi
OLD="$(BOT_PIDS)"
if [ -n "$OLD" ]; then
    echo "→ purana bot band (pids: $(echo "$OLD" | tr '\n' ' '))"
    for p in $OLD; do kill "$p" 2>/dev/null; done        # graceful SIGTERM
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        [ -z "$(BOT_PIDS)" ] && break
        sleep 1
    done
fi
LEFT="$(BOT_PIDS)"
if [ -n "$LEFT" ]; then
    echo "→ zabardasti band…"
    for p in $LEFT; do kill -9 "$p" 2>/dev/null; done
    sleep 2
fi

RLOG="$LOGDIR/bot_$STAMP.log"
START_OK=0
# naya restart.sh (jo abhi install hua) — ye khud screen/nohup handle karta hai.
# NOTE: `setsid` Termux me hota hi nahi — isliye fallback sirf nohup.
if [ -f "./restart.sh" ]; then
    bash ./restart.sh > "$LOGDIR/restart_$STAMP.log" 2>&1 && START_OK=1
    tail -n 4 "$LOGDIR/restart_$STAMP.log" 2>/dev/null
fi
if [ "$START_OK" != "1" ] && command -v screen >/dev/null 2>&1; then
    echo "→ screen se start…"
    screen -dmS snake bash -c "cd '$DIR' && exec '$PY' bot.py >> '$RLOG' 2>&1"
    START_OK=1
fi
if [ "$START_OK" != "1" ]; then
    echo "→ nohup se start…"
    ( cd "$DIR" && nohup "$PY" bot.py >>"$RLOG" 2>&1 & )
    START_OK=1
fi

sleep 7
PIDS="$(BOT_PIDS)"
if [ -z "$PIDS" ]; then            # ek aur mauka — slow phone
    sleep 6
    PIDS="$(BOT_PIDS)"
fi
if [ -n "$PIDS" ]; then
    echo "🚀 bot chalu hai (pid $(echo "$PIDS" | tr '\n' ' '))"
    command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q snake \
        && echo "🖥 screen: snake  →  dekhne ke liye: screen -r snake"
    echo "→ Telegram: /ping  →  $VER (build ${BUILD:-?})"
    if [ -f "$CFG" ]; then
        if grep -q '"bot_token": ""' "$CFG" 2>/dev/null; then
            echo "⚠️ token khaali hai — chalao: ./setconfig.sh --token <TOKEN> && ./restart.sh"
        else
            echo "🔐 token/admin safe (config se load honge)"
        fi
    fi
else
    echo "❌ bot start hote hi band ho gaya — log:"
    _lastlog="$(cat "$DIR/.last_log" 2>/dev/null || echo "$RLOG")"
    tail -n 25 "$_lastlog" 2>/dev/null || echo "   (log khaali)"
    [ -s "$RLOG" ] && tail -n 25 "$RLOG" 2>/dev/null
    echo ""
    echo "   wapas purana version: cp backups/bot_$STAMP.py bot.py && ./restart.sh"
    exit 1
fi
