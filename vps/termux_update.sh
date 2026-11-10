#!/data/data/com.termux/files/usr/bin/bash
# 🐍 PYTHON SNAKE — Termux updater  (SNAKE_UPDATER_V=7)
#   ./update.sh   →  khud ko latest karta hai, phir bot.py (Termux + DBF) + restart
#   ./update.sh --no-self   →  self-update skip
# NOTE: Termux me /tmp writable nahi — log script folder ke logs/ me jata hai.
set -u
UPDATER_V=7

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

# ── MULTI-SOURCE DOWNLOAD ────────────────────────────────────────────────
# India me raw.githubusercontent.com kai baar block hota hai — isliye
# api.github.com aur codeload tarball bhi try karte hain.
API="https://api.github.com/repos/$REPO/contents"
_TAR=""
api_dl() {   # $1 = repo path, $2 = out
    command -v curl >/dev/null 2>&1 || return 1
    curl -fsSL --max-time 90 -H "Accept: application/vnd.github.raw" \
        "$API/$1?ref=$BRANCH" -o "$2" 2>/dev/null \
        && [ -s "$2" ] && ! head -c 200 "$2" | grep -q '"message": *"Not Found"'
}
tarball_dl() {
    [ -n "$_TAR" ] && [ -d "$_TAR" ] && return 0
    for _u in "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" \
              "https://api.github.com/repos/$REPO/tarball/$BRANCH" \
              "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"; do
        rm -f "$DIR/.repo.tar.gz"
        DL "$_u" "$DIR/.repo.tar.gz" 2>/dev/null || continue
        [ -s "$DIR/.repo.tar.gz" ] || continue
        rm -rf "$DIR/.repo.x"; mkdir -p "$DIR/.repo.x"
        if tar -xzf "$DIR/.repo.tar.gz" -C "$DIR/.repo.x" 2>/dev/null; then
            _TAR="$(find "$DIR/.repo.x" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | head -1)"
            [ -n "$_TAR" ] && return 0
        fi
    done
    _TAR=""
    return 1
}
fetch_file() {   # $1 = repo path, $2 = out
    DL "$RAW/$1" "$2" 2>/dev/null && [ -s "$2" ] && return 0
    DL "$GH/$1"  "$2" 2>/dev/null && [ -s "$2" ] && return 0
    api_dl "$1" "$2" && return 0
    if tarball_dl && [ -f "$_TAR/$1" ]; then
        cp -f "$_TAR/$1" "$2" 2>/dev/null && [ -s "$2" ] && return 0
    fi
    rm -f "$2" 2>/dev/null
    return 1
}

# ── 0) SELF-UPDATE — ./update.sh hamesha latest rahe ──────────────────────
if [ "${SNAKE_NO_SELF:-0}" != "1" ] && [ "${1:-}" != "--no-self" ] && [ -w "$0" ]; then
    if fetch_file "vps/termux_update.sh" "$DIR/update.sh.new" 2>/dev/null; then
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
        case "$last" in bot.py|*/bot.py) echo "$p" ;; esac
    done
}

# ══════════════ 1) BOT DOWNLOAD ══════════════
[ -f bot.py ] && cp -f bot.py "backups/bot_$STAMP.py" && echo "💾 backup: backups/bot_$STAMP.py"

# ── 1.5) 🔐 CONFIG GUARD — token/admin update me KABHI delete nahi honge ──
#  bot.py replace hota hai, par ye file nahi chhooti.
CFG="$DIR/snake_config.json"
#  v2.13.1: config me KHAALI token kabhi nahi likha jayega (wahi token loss
#  ka asli karan tha). Token kisi bhi config/backup se mil jaye to repair.
"$PY" - "$CFG" "$DIR" <<'PYEOF'
import glob, json, os, re, sys, time

out, base = sys.argv[1], sys.argv[2]
home = os.path.expanduser("~")

def tok_ok(t):
    t = str(t or "").strip()
    return bool(t) and "PUT_YOUR" not in t and ":" in t and len(t) >= 20

def read_cfg(p):
    try:
        if os.path.isfile(p) and os.path.getsize(p) < 200000:
            d = json.load(open(p, encoding="utf-8", errors="ignore"))
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}

cfgs = [out, "/storage/emulated/0/DBF/snake_config.json",
        os.path.join(home, "snake", "snake_config.json"),
        os.path.join(base, "data", "snake_config.json")]

tok, src, admins = "", "", []
for p in cfgs:
    d = read_cfg(p)
    t = str(d.get("bot_token") or "").strip()
    if t and not tok_ok(t):
        t = ""
    if t and not tok:
        tok, src = t, p
    for a in (d.get("admin_ids") or []):
        try:
            a = int(a)
        except Exception:
            continue
        if a > 0 and a not in admins:
            admins.append(a)

# backup bot.py se token (purani install)
if not tok:
    cands = sorted(glob.glob(os.path.join(base, "backups", "bot_*.py")),
                   reverse=True)[:8]
    cands += [os.path.join(base, "bot.py"),
              "/storage/emulated/0/DBF/bot.py",
              os.path.join(home, "snake", "bot.py")]
    for p in cands:
        try:
            src_txt = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        m = re.search(r"^BOT_TOKEN\s*=\s*[\"']([^\"']*)[\"']", src_txt, re.M)
        t = (m.group(1) if m else "").strip()
        if tok_ok(t):
            tok, src = t, p
            break

if not tok:
    print("⚠️ token kahin nahi mila — config ko chheda nahi gaya")
    print("   ek baar: ./setconfig.sh  (phir ./update.sh)")
    sys.exit(0)

if not admins:
    admins = [8937044612]
cfg = read_cfg(out)
cfg.update({"bot_token": tok, "admin_ids": admins, "brand": "PYTHON SNAKE",
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Token/Admin yahan safe hain — ./update.sh inse touch nahi karta"})
tmp = out + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
os.replace(tmp, out)
print("🔐 config ready (%s se) — token ✅, admins %d" % (os.path.basename(src), len(admins)))
PYEOF
if [ -f "$CFG" ]; then
    chmod 600 "$CFG" 2>/dev/null
    echo "🔐 config safe hai: $CFG (token isse nahi jayega)"
fi

echo "→ bot download…"
if ! DL "$BOT_URL" bot.py.new 2>/dev/null || [ ! -s bot.py.new ]; then
    echo "↩ raw fail — github.com/raw → api.github.com → tarball try…"
    if ! fetch_file "bot.py" bot.py.new; then
        echo "❌ download fail (raw + api + codeload sab band) — net check karo"
        echo "   WiFi/data ON hai? Browser me github.com khulta hai?"
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

# 🐍 SHADOW X (optional) — shadow/new.py + run.sh bhi sync (fail ho to bot.py pe asar nahi)
_sync_shadow() {
    _sh_dir="$1"
    mkdir -p "$_sh_dir" 2>/dev/null || return 0
    _ok=0
    for _f in new.py run.sh; do
        if fetch_file "shadow/$_f" "$_sh_dir/$_f.new" 2>/dev/null \
           && [ -s "$_sh_dir/$_f.new" ]; then
            mv -f "$_sh_dir/$_f.new" "$_sh_dir/$_f" && _ok=$((_ok+1))
        else
            rm -f "$_sh_dir/$_f.new" 2>/dev/null
        fi
    done
    fetch_file "shadow/README.md" "$_sh_dir/README.md" 2>/dev/null
    chmod +x "$_sh_dir/run.sh" 2>/dev/null
    if [ "$_ok" -gt 0 ]; then
        echo "✅ $_sh_dir/new.py (SHADOW X)"
        "$PY" -m py_compile "$_sh_dir/new.py" 2>/dev/null \
            || echo "⚠️ shadow/new.py compile check fail — deps dekho (pyTelegramBotAPI)"
    fi
}
_sync_shadow "$DIR/shadow"
if [ -d "$EXT" ] && [ "$(cd "$DIR" && pwd -P)" != "$(cd "$EXT" 2>/dev/null && pwd -P)" ]; then
    _sync_shadow "$EXT/shadow"
fi

# 🔐 config DBF folder me bhi (bot wahan se chale to bhi token mile)
if [ -f "$CFG" ] && [ -d "$EXT" ] && \
   [ "$(cd "$DIR" && pwd -P)" != "$(cd "$EXT" && pwd -P)" ]; then
    if [ ! -f "$EXT/snake_config.json" ]; then
        cp -f "$CFG" "$EXT/snake_config.json" 2>/dev/null \
            && echo "🔐 DBF config copy ✅"
    fi
fi

# ══════════════ 3) SCRIPTS REFRESH ══════════════
# v2.13.0: phone pe purani/tuti scripts hi "screen already exists" + duplicate
# sessions ka karan thi. Ab har update pe saari scripts overwrite hoti hain.
_install_script() {                       # $1 = filename, $2 = marker (sanity)
    if fetch_file "$1" "$DIR/$1.new" 2>/dev/null; then
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
_install_script snake_lib.sh "SNAKE_LIB_V" && echo "✅ snake_lib.sh" \
    || echo "⚠️ snake_lib.sh download fail (purana chalega)"
for _s in start.sh stop.sh restart.sh status.sh; do
    case "$_s" in
        start.sh)   _m="snake_start" ;;
        stop.sh)    _m="snake_kill_all" ;;
        restart.sh) _m="snake_kill_all" ;;
        *)          _m="PYTHON SNAKE" ;;
    esac
    _install_script "$_s" "$_m" && echo "✅ $_s" || echo "⚠️ $_s fail"
done

# setconfig.sh bhi install/refresh (token badalne ka official tarika)
if fetch_file "setconfig.sh" "$DIR/setconfig.sh.new" 2>/dev/null; then
    if grep -q "setconfig" "$DIR/setconfig.sh.new" 2>/dev/null \
       && bash -n "$DIR/setconfig.sh.new" 2>/dev/null; then
        mv -f "$DIR/setconfig.sh.new" "$DIR/setconfig.sh"
        chmod +x "$DIR/setconfig.sh" 2>/dev/null
    else
        rm -f "$DIR/setconfig.sh.new"
    fi
fi

# ══════════════ 4) RESTART — purane SAARE sessions saaf, fresh start ══════
cd "$DIR" || exit 1
START_OK=0
if [ -f ./snake_lib.sh ] && grep -q "SNAKE_LIB_V" ./snake_lib.sh 2>/dev/null; then
    . ./snake_lib.sh                      # v5 lib → snake_kill_all + snake_start
    if [ "${SNAKE_LIB_V:-0}" -ge 5 ] 2>/dev/null; then
        echo "→ purane sessions/process saaf…"
        snake_kill_all
        echo "→ fresh start…"
        if snake_start; then
            START_OK=1
        fi
    fi
fi

if [ "$START_OK" != "1" ]; then              # fallback (lib na mile)
    if command -v screen >/dev/null 2>&1; then
        screen -ls 2>/dev/null \
            | sed -n 's/^[[:space:]]*\([0-9][0-9]*\.snake[^[:space:]]*\).*/\1/p' \
            | while read -r sid; do screen -S "$sid" -X quit >/dev/null 2>&1; done
        screen -wipe >/dev/null 2>&1
    fi
    OLD="$(BOT_PIDS)"
    if [ -n "$OLD" ]; then
        echo "→ purana bot band (pids: $(echo "$OLD" | tr '\n' ' '))"
        for p in $OLD; do kill "$p" 2>/dev/null; done
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            [ -z "$(BOT_PIDS)" ] && break
            sleep 1
        done
    fi
    LEFT="$(BOT_PIDS)"
    if [ -n "$LEFT" ]; then
        for p in $LEFT; do kill -9 "$p" 2>/dev/null; done
        sleep 2
    fi
    rm -f "$DIR/.snake.lock" 2>/dev/null
    RLOG="$LOGDIR/bot_$STAMP.log"
    if command -v screen >/dev/null 2>&1; then
        screen -dmS snake bash -c "cd '$DIR' && exec '$PY' bot.py >> '$RLOG' 2>&1"
    else
        ( cd "$DIR" && nohup "$PY" bot.py >>"$RLOG" 2>&1 & )
    fi
    echo "$RLOG" > "$DIR/.last_log"
    sleep 7
    [ -n "$(BOT_PIDS)" ] && START_OK=1
fi

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
    _lastlog="$(cat "$DIR/.last_log" 2>/dev/null || echo "$LOGDIR/bot_$STAMP.log")"
    tail -n 25 "$_lastlog" 2>/dev/null || echo "   (log khaali)"
    echo ""
    echo "   wapas purana version: cp backups/bot_$STAMP.py bot.py && ./restart.sh"
    exit 1
fi
