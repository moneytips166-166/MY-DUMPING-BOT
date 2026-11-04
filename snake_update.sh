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
BOT="snake_core.py"
NEW=".snake_new.py"
PY="$(command -v python3 || echo python3)"

mkdir -p backups

echo "=============================================================="
echo "  🔄 PYTHON SNAKE CORE — UPDATER"
echo "  Folder: $(pwd)"
echo "=============================================================="

if [ ! -f "$BOT" ]; then
  echo "❌ $BOT nahi mila — pehle installer chalao"
  exit 1
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

# ---------- replace + restart ----------
mv -f "$NEW" "$BOT"
rm -rf __pycache__
echo "  ✅ $BOT update ho gaya"

WAS_RUNNING=0
screen -ls 2>/dev/null | grep -q "\.snake" && WAS_RUNNING=1
if [ "$WAS_RUNNING" = "1" ]; then
  echo "  🔄 Bot chal raha tha — restart kar rahe hain…"
  [ -x ./restart.sh ] && ./restart.sh
else
  echo "  ℹ️  Bot band tha — ./start.sh se chalao"
fi

echo ""
echo "=============================================================="
echo "  ✅ UPDATE DONE"
echo "  Rollback : cp $BACKUP $BOT && ./restart.sh"
echo "=============================================================="
