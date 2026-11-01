#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  SPIDEY BOT — CONFIG EDITOR (token + admin id)   •  Termux / Linux / VPS
#
#  Usage:
#     ./setconfig.sh                  -> interactive menu
#     ./setconfig.sh --token 123:ABC  -> sirf token
#     ./setconfig.sh --admin 123,456  -> sirf admin id(s), comma se alag
#     ./setconfig.sh --show           -> current values dikhao
# ==============================================================================
set -u
cd "$(dirname "$0")" || exit 1

BOT_FILE="${BOT_FILE:-bot_fixed.py}"
[ -f "$BOT_FILE" ] || { echo "❌ $BOT_FILE nahi mila (isi folder me chalao)"; exit 1; }

PY="$(command -v python3 || command -v python || echo python3)"

_show() {
  echo "──────────────────────────────────────────────"
  grep -n '^BOT_TOKEN' "$BOT_FILE" | sed 's/\(: *"\)\([0-9]\{6,\}:\)[A-Za-z0-9_-]*/\1\2********/'
  grep -n '^ADMIN_IDS' "$BOT_FILE"
  echo "──────────────────────────────────────────────"
}

_set_token() {
  NEW="$1"
  if ! echo "$NEW" | grep -qE '^[0-9]{6,}:[A-Za-z0-9_-]{30,}$'; then
    echo "❌ Token format galat. Aisa hona chahiye: 123456789:AAGxxxxxxxxxxxxxxxxxxxxxxx"
    return 1
  fi
  cp -f "$BOT_FILE" "backups/${BOT_FILE%.py}_token_$(date +%Y%m%d_%H%M%S).py" 2>/dev/null || {
    mkdir -p backups; cp -f "$BOT_FILE" "backups/${BOT_FILE%.py}_token_$(date +%Y%m%d_%H%M%S).py"; }
  "$PY" - "$NEW" <<'PYEOF'
import re, sys
tok = sys.argv[1].strip()
f = "bot_fixed.py"
src = open(f, encoding="utf-8").read()
new, n = re.subn(r'^BOT_TOKEN *= *"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if n == 0:
    print("❌ BOT_TOKEN line nahi mili"); sys.exit(1)
open(f, "w", encoding="utf-8").write(new)
print("✅ Token updated")
PYEOF
}

_set_admin() {
  NEW="$1"
  NORM=$(echo "$NEW" | tr ',' ' ' | tr -s ' ')
  for id in $NORM; do
    echo "$id" | grep -qE '^[0-9]{5,}$' || { echo "❌ Admin ID sirf numbers honi chahiye (Telegram user id). Mila: $id"; return 1; }
  done
  mkdir -p backups
  cp -f "$BOT_FILE" "backups/${BOT_FILE%.py}_admin_$(date +%Y%m%d_%H%M%S).py"
  "$PY" - "$NORM" <<'PYEOF'
import re, sys
ids = [x for x in sys.argv[1].split() if x.isdigit()]
if not ids:
    print("❌ Koi valid id nahi mili"); sys.exit(1)
f = "bot_fixed.py"
src = open(f, encoding="utf-8").read()
new, n = re.subn(r'^ADMIN_IDS *= *\[[^\]]*\]', 'ADMIN_IDS = [%s]' % ", ".join(ids), src, count=1, flags=re.M)
if n == 0:
    new, n = re.subn(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]', 'ADMIN_IDS = [%s]' % ", ".join(ids), src, count=1, flags=re.M)
if n == 0:
    print("❌ ADMIN_IDS line nahi mili"); sys.exit(1)
open(f, "w", encoding="utf-8").write(new)
print("✅ ADMIN_IDS updated -> [%s]" % ", ".join(ids))
PYEOF
}

_verify() {
  if "$PY" -m py_compile "$BOT_FILE"; then
    echo "✅ File compile OK — ab restart karo:  ./restart.sh"
    rm -rf __pycache__ 2>/dev/null || true
  else
    echo "❌ Compile FAIL! Backup se wapas karo:  ls backups/  &&  cp backups/<file> $BOT_FILE"
  fi
}

case "${1:-}" in
  --show)  _show; exit 0 ;;
  --token) _set_token "${2:-}" && _verify; exit 0 ;;
  --admin) _set_admin "${2:-}" && _verify; exit 0 ;;
esac

echo "=============================================================="
echo "  ⚙️  SPIDEY BOT CONFIG EDITOR"
echo "=============================================================="
_show
echo "  [1] 🔑 Bot token change karo"
echo "  [2] 👑 Admin ID change karo"
echo "  [3] 🔄 Dono (token + admin id)"
echo "  [0] Exit"
echo "=============================================================="
read -r -p "👉 Choice: " CH

case "$CH" in
  1)
    read -r -p "🔑 Naya token paste karo: " TOK
    _set_token "$TOK" && _verify
    ;;
  2)
    echo "💡 Apni Telegram ID pata karne ke liye bot me /myid bhejo"
    read -r -p "👑 Admin ID(s) (comma se alag): " AID
    _set_admin "$AID" && _verify
    ;;
  3)
    read -r -p "🔑 Naya token: " TOK
    _set_token "$TOK" || exit 1
    echo "💡 Apni Telegram ID: bot me /myid bhejo"
    read -r -p "👑 Admin ID(s) (comma se alag): " AID
    _set_admin "$AID" && _verify
    ;;
  *) echo "Bye 👋"; exit 0 ;;
esac

echo ""
_show
echo "▶️  Ab chalao:  ./restart.sh   (ya ./start.sh)"
