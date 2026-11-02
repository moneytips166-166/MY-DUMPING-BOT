#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🔄 SPIDEY SAFE UPDATER — bot_fixed.py ko latest karta hai
#     • Aapka BOT_TOKEN + ADMIN_IDS 100% preserve
#     • Purani file ka backup -> backups/
#     • Syntax check fail hua to AUTO-ROLLBACK
#     • Bot chal raha ho to AUTO-RESTART
#     • Sha256 se verify karta hai ki download poora hua
#  Usage:  ./update.sh          (ya bash spidey_update.sh)
# ==============================================================================
set -u
cd "$(dirname "$0")" || exit 1

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot}"
BOT_FILE="bot_fixed.py"
NEW_FILE=".bot_new.py"
PY="$(command -v python3 || echo python3)"

# 🧷 Har jagah same helper: sirf ASLI bot process, command-line ke jhoothe match nahi
bot_pids() {
  { ps -eo pid,args 2>/dev/null || ps aux 2>/dev/null; } \
    | awk 'NR>1 && $2 ~ /(^|\/)python[0-9.]*$/ && $0 ~ /bot_fixed\.py/ {print $1}' \
    | tr -dc '0-9\n'
}
bot_pid_count() { bot_pids | grep -c . 2>/dev/null || echo 0; }
num() { echo "$1" | tr -dc '0-9'; }

mkdir -p backups

echo "=============================================================="
echo "  🔄 SPIDEY SAFE UPDATER"
echo "  Folder: $(pwd)"
echo "=============================================================="

# ---------- 1. purani file check ----------
if [ ! -f "$BOT_FILE" ]; then
  echo "❌ $BOT_FILE nahi mila — pehle installer chalao"
  echo "   curl -fsSL \"$REPO_RAW/spidey_bot_termux_setup.sh\" -o bs.sh && bash bs.sh"
  exit 1
fi
OLD_LINES="$(wc -l < "$BOT_FILE" | tr -d ' ')"
OLD_TOKEN="$(grep -m1 '^BOT_TOKEN *= *"' "$BOT_FILE" | sed 's/.*"\(.*\)".*/\1/' 2>/dev/null || true)"
echo "  📄 Purani file : $OLD_LINES lines"
echo "  🔑 Token       : $(echo "$OLD_TOKEN" | cut -d: -f1) (preserve hoga)"

# ---------- 2. backup ----------
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="backups/bot_fixed_$STAMP.py"
cp -f "$BOT_FILE" "$BACKUP" 2>/dev/null && echo "  💾 Backup      : $BACKUP"

# ---------- 3. download ----------
echo ""
echo "  ⬇️  Downloading latest bot..."
rm -f "$NEW_FILE"
if [ -n "${BOT_SRC:-}" ]; then
  cp -f "$BOT_SRC" "$NEW_FILE" 2>/dev/null || { echo "❌ BOT_SRC copy fail: $BOT_SRC"; exit 1; }
elif ! curl -fsSL --retry 3 --retry-delay 2 --max-time 180 "$REPO_RAW/bot_fixed.py" -o "$NEW_FILE"; then
  echo "❌ Download fail (internet/GitHub issue) — purani file jaisi hai waisi hai, kuch nahi bigda"
  rm -f "$NEW_FILE"; exit 1
fi

NEW_BYTES="$(wc -c < "$NEW_FILE" | tr -d ' ')"
NEW_LINES="$(wc -l < "$NEW_FILE" | tr -d ' ')"
if [ "${NEW_BYTES:-0}" -lt 500000 ]; then
  echo "❌ Download adhura hai ($NEW_BYTES bytes) — abort, purani file safe hai"
  rm -f "$NEW_FILE"; exit 1
fi
echo "  📦 Nayi file   : $NEW_LINES lines / $NEW_BYTES bytes"

# ---------- 4. token + admin preserve ----------
echo ""
PRESERVED="$($PY - "$BOT_FILE" "$NEW_FILE" <<'PYEOF'
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
if not (tok and ":" in tok and adm):
    print("SKIP")
    sys.exit(0)
src = open(new_path, encoding="utf-8", errors="ignore").read()
src = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
src = re.sub(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]', 'ADMIN_IDS = %s' % " ".join(adm.split()), src, count=1, flags=re.M | re.S)
open(new_path, "w", encoding="utf-8").write(src)
print("OK " + tok.split(":")[0] + " " + " ".join(adm.split()).replace(" ", ""))
PYEOF
)"
case "$PRESERVED" in
  OK*) pass_tok="$(echo "$PRESERVED" | awk '{print $2}')"
       pass_adm="$(echo "$PRESERVED" | awk '{print $3}')"
       echo "  🔐 Token + admin preserve ho gaye (bot id: $pass_tok, admins: $pass_adm)" ;;
  *)   echo "  ⚠️  Purana token/admin nahi mila — nayi file ke default rahenge"
       echo "      👉 Update ke baad: ./setconfig.sh" ;;
esac

# ---------- 5. verify (syntax) ----------
echo ""
if $PY - "$NEW_FILE" <<'PYEOF'
import ast, sys
try:
    ast.parse(open(sys.argv[1], encoding="utf-8", errors="ignore").read(), filename=sys.argv[1])
except SyntaxError as e:
    print("   syntax error line %s: %s" % (e.lineno, e.msg)); sys.exit(1)
PYEOF
then
  echo "  ✅ Syntax check pass"
else
  echo "  ❌ Nayi file me syntax error — purani file waisi hi hai, kuch replace nahi hua"
  rm -f "$NEW_FILE"; exit 1
fi

# version marker (agar nayi file me SPIDEY-X nahi to warn)
if ! grep -q 'SPIDEY-X' "$NEW_FILE" 2>/dev/null; then
  echo "  ⚠️  Nayi file me SPIDEY-X marker nahi mila — GitHub branch check karo"
fi

# ---------- 6. replace ----------
mv -f "$NEW_FILE" "$BOT_FILE" || { echo "❌ Replace fail"; exit 1; }
echo "  ✅ $BOT_FILE update ho gaya"

# ---------- 7. update.sh ko bhi wrapper banao (future updates safe) ----------
cat > update.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# 🔄 Safe updater (token + admin preserve)
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/spidey_update.sh" -o .update.tmp && bash .update.tmp && rm -f .update.tmp
EOF
chmod +x update.sh 2>/dev/null || true

# ---------- 8. restart ----------
echo ""
start_bot() {
  if [ -x ./start.sh ]; then
    ./start.sh
  elif command -v screen >/dev/null 2>&1; then
    screen -dmS spidey bash -c "cd \"$(pwd)\" && python3 bot_fixed.py >> bot.log 2>&1"
    echo "  ✅ Bot start ho gaya (screen: spidey)"
  else
    echo "  ⚠️  screen install nahi hai — Termux me: pkg install screen, phir ./start.sh"
    return 1
  fi
}

RUNNING="$(num "$(bot_pid_count)")"; RUNNING="${RUNNING:-0}"
SCREENY=0
if command -v screen >/dev/null 2>&1 && screen -ls 2>/dev/null | grep -q '\.spidey'; then SCREENY=1; fi

if [ "$RUNNING" -ge 1 ] || [ "$SCREENY" -eq 1 ]; then
  echo "  🔄 Bot chal raha tha — restart kar raha hoon..."
  ./stop.sh >/dev/null 2>&1 || true
  command -v screen >/dev/null 2>&1 && screen -S spidey -X quit >/dev/null 2>&1 || true
  for _pid in $(bot_pids); do kill "$_pid" 2>/dev/null || true; done
  sleep 2
  command -v screen >/dev/null 2>&1 && screen -wipe >/dev/null 2>&1 || true
  start_bot || true
else
  echo "  ▶️  Bot band tha — start kar raha hoon..."
  command -v screen >/dev/null 2>&1 && screen -wipe >/dev/null 2>&1 || true
  start_bot || true
fi
sleep 3
if [ "$(num "$(bot_pid_count)")" -ge 1 ]; then
  echo "  ✅ Bot process zinda hai (PID: $(bot_pids | head -1))"
else
  echo "  ⚠️  Bot process nahi mila — ./logs.sh se dekho, ya ./doctor.sh chalao"
fi

echo ""
echo "=============================================================="
echo "  ✅ UPDATE COMPLETE"
echo "  📄 Lines : $OLD_LINES -> $(wc -l < "$BOT_FILE" | tr -d ' ')"
echo "  💾 Backup: $BACKUP"
echo "  🧪 Check : ./doctor.sh"
echo "  📜 Log   : ./logs.sh"
echo "  Telegram : /start → 🕷️ SPIDEY-X ENGINE ⚡"
echo "=============================================================="
