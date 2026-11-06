#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🔄 PYTHON SNAKE CORE — safe updater
#     • Token + ADMIN_IDS preserve
#     • Purani file ka backup -> backups/
#     • Syntax check fail = auto rollback
#     • Bot chal raha ho to auto restart (screen)
# ==============================================================================
set -u
cd "$(dirname "$0")" || exit 1

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot}"
BOT="bot.py"                       # EK hi file — har update isi me
NEW=".snake_new.py"
DBF_DIR="${DBF_DIR:-/storage/emulated/0/DBF}"   # mirror copy yahan bhi
PY="$(command -v python3 || echo python3)"

mkdir -p backups

echo "=============================================================="
echo "  🔄 PYTHON SNAKE CORE — UPDATER"
echo "  Folder: $(pwd)"
echo "=============================================================="

if [ ! -f "$BOT" ]; then
  if [ -f "snake_core.py" ] && [ "$(wc -l < snake_core.py)" -gt 1000 ]; then
    echo "  🔁 Purani snake_core.py mili — bot.py me migrate…"
    cp -f snake_core.py "$BOT"
  else
    echo "❌ $BOT nahi mila — pehle installer chalao"
    exit 1
  fi
fi

echo "  📄 Purani : $(wc -l < "$BOT") lines"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="backups/${BOT%.py}_$STAMP.py"
cp -f "$BOT" "$BACKUP" && echo "  💾 Backup : $BACKUP"

echo ""
echo "  ⬇️  Downloading latest…"
rm -f "$NEW"
if ! curl -fsSL --retry 3 --retry-delay 2 --max-time 180 "$REPO_RAW/$BOT" -o "$NEW"; then
  echo "❌ Download fail — purani file waise hi hai"
  rm -f "$NEW"; exit 1
fi

NEW_BYTES="$(wc -c < "$NEW" | tr -d ' ')"
if [ "${NEW_BYTES:-0}" -lt 50000 ]; then
  echo "❌ Download adhura ($NEW_BYTES bytes) — abort"
  rm -f "$NEW"; exit 1
fi
echo "  📦 Nayi   : $(wc -l < "$NEW") lines / $NEW_BYTES bytes"

# ---------- token + admin preserve ----------
echo ""
PRESERVED="$($PY - "$BOT" "$NEW" <<'PYEOF'
import re, sys
old_path, new_path = sys.argv[1], sys.argv[2]

def grab(path, pat, flags=re.M):
    try:
        s = open(path, encoding="utf-8", errors="ignore").read()
        m = re.search(pat, s, flags)
        return m.group(1) if m else None
    except Exception:
        return None

tok = grab(old_path, r'^BOT_TOKEN\s*=\s*"([^"]*)"')
adm = grab(old_path, r'^ADMIN_IDS\s*=\s*(\[[^\]]*\])', re.M | re.S)
if not (tok and ":" in tok and "PUT_YOUR" not in tok):
    print("SKIP"); sys.exit(0)
src = open(new_path, encoding="utf-8", errors="ignore").read()
src = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if adm:
    src = re.sub(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]', 'ADMIN_IDS = %s' % " ".join(adm.split()),
                 src, count=1, flags=re.M | re.S)
open(new_path, "w", encoding="utf-8").write(src)
print("OK " + tok.split(":")[0])
PYEOF
)"
case "$PRESERVED" in
  OK*) echo "  🔐 Token preserve ho gaya (bot id: $(echo "$PRESERVED" | awk '{print $2}'))" ;;
  *)   echo "  ⚠️  Token nahi mila — update ke baad ./setconfig.sh chalao" ;;
esac

# ---------- syntax ----------
echo ""
if $PY -m py_compile "$NEW" 2>/dev/null; then
  echo "  ✅ Syntax pass"
else
  echo "  ❌ Syntax error — purani file safe hai, kuch replace nahi hua"
  rm -f "$NEW"; exit 1
fi

# ---------- replace ----------
mv -f "$NEW" "$BOT"
rm -rf __pycache__
echo "  ✅ $BOT update ho gaya (ek hi file — koi patch nahi)"

# ---------- snake_core.py shim (purane start.sh ke liye) ----------
cat > snake_core.py <<'SHIMEOF'
#!/usr/bin/env python3
# snake_core.py — sirf COMPAT SHIM. Asli code bot.py me hai (ek hi file).
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.join(BASE, "bot.py")

if not os.path.exists(BOT):
    sys.exit("❌ bot.py nahi mila — ./update.sh chalao")

with open(BOT, encoding="utf-8") as _f:
    _src = _f.read()

exec(compile(_src, BOT, "exec"))
SHIMEOF
$PY -m py_compile snake_core.py 2>/dev/null && echo "  ✅ shim ready (start.sh waise hi chalega)"

# ---------- DBF folder me wahi file ----------
echo ""
if mkdir -p "$DBF_DIR" 2>/dev/null && cp -f "$BOT" "$DBF_DIR/bot.py" 2>/dev/null; then
  echo "  📁 DBF copy : $DBF_DIR/bot.py  ($(wc -l < "$DBF_DIR/bot.py") lines)"
else
  echo "  ⚠️  DBF folder likhne ki permission nahi: $DBF_DIR"
  echo "      Termux me ek baar chalao:  termux-setup-storage"
fi

# ---------- helpers refresh ----------
echo ""
echo "  🔧 Helper scripts refresh…"
if curl -fsSL --retry 2 --max-time 60 "$REPO_RAW/snake_helpers.sh" -o .helpers.tmp 2>/dev/null; then
  bash .helpers.tmp && rm -f .helpers.tmp
else
  echo "  ⚠️  helpers refresh skip (net issue)"
fi

# dead session saaf karo, phir ASLI process dekho (text nahi)
screen -wipe >/dev/null 2>&1 || true
WAS_RUNNING=0
if pgrep -f "python3 -u snake_core\.py" >/dev/null 2>&1 || pgrep -f "python3 snake_core\.py" >/dev/null 2>&1 \
   || pgrep -f "python3 -u bot\.py" >/dev/null 2>&1 || pgrep -f "python3 bot\.py" >/dev/null 2>&1; then WAS_RUNNING=1; fi
[ "$WAS_RUNNING" = "0" ] && screen -ls 2>/dev/null | grep -q "\.[Ss]nake" && WAS_RUNNING=1
if [ "$WAS_RUNNING" = "1" ]; then
  echo "  🔄 Bot chal raha tha — restart kar rahe hain…"
  [ -x ./restart.sh ] && ./restart.sh
else
  echo "  ℹ️  Bot band tha — ./start.sh se chalao"
fi

# ---------- version dikhao ----------
VER="$(grep -m1 '^VERSION = ' "$BOT" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')"
LINES="$(wc -l < "$BOT" 2>/dev/null | tr -d ' ')"
echo ""
echo "  📦 Version : ${VER:-?}  (${LINES:-?} lines)"
case "${VER:-}" in
  v2.4)
    echo "  ✅ v2.4 — EK file system: bot.py (+ DBF copy), koi patch nahi"
    ;;
  v2.3|v2.2|v2.1|v2.0)
    echo "  ⚠️  ${VER} lag raha hai — v2.4 chahiye (dobara ./update.sh chalao)"
    ;;
  *)
    echo "  ⚠️  Purana version lag raha hai — dobara ./update.sh chalao"
    ;;
esac
echo "  📁 File     : $(pwd)/$BOT"
echo "  📁 DBF copy : $DBF_DIR/bot.py"

echo ""
echo "=============================================================="
echo "  ✅ UPDATE DONE"
echo "  Rollback : cp $BACKUP $BOT && ./restart.sh"
echo "=============================================================="
