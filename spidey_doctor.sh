#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🩺 SPIDEY BOT DOCTOR — "bot response nahi kar raha" ka asli karan batata hai
#  Usage:  ./doctor.sh
# ==============================================================================
set -u
cd "$(dirname "$0")" 2>/dev/null || true

BOT_FILE="${BOT_FILE:-bot_fixed.py}"
PY="$(command -v python3 || command -v python || echo python3)"
OK="✅"; BAD="❌"; WARN="⚠️ "
ISSUES=0

line() { echo "──────────────────────────────────────────────────────────"; }
fail() { echo "  $BAD $1"; ISSUES=$((ISSUES+1)); }
warn() { echo "  $WARN $1"; ISSUES=$((ISSUES+1)); }
pass() { echo "  $OK $1"; }

echo "=============================================================="
echo "  🩺 SPIDEY BOT DOCTOR"
echo "  Folder: $(pwd)"
echo "=============================================================="

# ---------- 1. Files ----------
echo ""
echo "【1】 FILES"
line
if [ -f "$BOT_FILE" ]; then
  pass "$BOT_FILE mila ($(wc -c < "$BOT_FILE" | tr -d ' ') bytes, $(wc -l < "$BOT_FILE" | tr -d ' ') lines)"
else
  fail "$BOT_FILE NAHI mila — ./update.sh chalao ya installer dobara chalao"
  echo ""; echo "❌ Yahan se aage check nahi ho sakta."; exit 1
fi

# ---------- 2. Python + compile ----------
echo ""
echo "【2】 PYTHON"
line
pass "Python: $($PY -V 2>&1)"
if $PY -m py_compile "$BOT_FILE" 2>/tmp/spidey_doc_err.txt; then
  pass "File compile OK (koi syntax error nahi)"
else
  fail "SYNTAX ERROR — file kharab hai:"
  sed -n '1,8p' /tmp/spidey_doc_err.txt | sed 's/^/       /'
  echo "     👉 Fix: ./update.sh   (ya backups/ se purani file wapas lo)"
fi
rm -rf __pycache__ 2>/dev/null || true

# ---------- 3. Dependencies ----------
echo ""
echo "【3】 DEPENDENCIES"
line
$PY - <<'PYEOF'
import importlib, sys
mods = [("telegram", "python-telegram-bot"), ("aiohttp", "aiohttp"), ("bs4", "beautifulsoup4")]
bad = 0
for mod, pkg in mods:
    try:
        m = importlib.import_module(mod)
        v = getattr(m, "__version__", "?")
        print("  ✅ %-12s %s" % (mod, v))
    except Exception as e:
        print("  ❌ %-12s MISSING (%s)" % (mod, e))
        bad += 1
if bad:
    print("\n     👉 Fix:  pip install python-telegram-bot aiohttp beautifulsoup4")
    sys.exit(3)
PYEOF
[ $? -eq 3 ] && ISSUES=$((ISSUES+1))

# ---------- 4. Token ----------
echo ""
echo "【4】 TOKEN & ADMIN"
line
TOKEN="$($PY - "$BOT_FILE" <<'PYEOF'
import re, sys
try:
    src = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    m = re.search(r'^BOT_TOKEN\s*=\s*"([^"]*)"', src, re.M)
    print(m.group(1) if m else "")
except Exception:
    print("")
PYEOF
)"
ADMINS="$($PY - "$BOT_FILE" <<'PYEOF'
import re, sys
try:
    src = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    m = re.search(r'^ADMIN_IDS\s*=\s*\[([^\]]*)\]', src, re.M)
    print((m.group(1) if m else "").strip())
except Exception:
    print("")
PYEOF
)"

if [ -z "$TOKEN" ]; then
  fail "BOT_TOKEN nahi mila — ./setconfig.sh chalao"
elif echo "$TOKEN" | grep -qE '^[0-9]{6,}:[A-Za-z0-9_-]{30,}$'; then
  pass "Token format OK (ID: ${TOKEN%%:*}, length ${#TOKEN})"
else
  fail "Token format GALAT hai: ${TOKEN:0:20}..."
  echo "     👉 ./setconfig.sh --token <naya-token>"
fi

if [ -z "$ADMINS" ]; then
  warn "ADMIN_IDS khali hai — admin commands kaam nahi karenge"
else
  pass "ADMIN_IDS = [$ADMINS]"
fi

# ---------- 5. Telegram API live checks ----------
echo ""
echo "【5】 TELEGRAM API (live)"
line
if [ -z "$TOKEN" ]; then
  warn "Token nahi hai to API check skip"
else
  ME="$(curl -s --max-time 20 "https://api.telegram.org/bot${TOKEN}/getMe" 2>/dev/null)"
  if [ -z "$ME" ]; then
    warn "Telegram tak pahunch nahi paya (internet/curl issue) — token check skip"
  elif echo "$ME" | grep -q '"ok":true'; then
    NAME="$(echo "$ME" | $PY -c 'import sys,json;d=json.load(sys.stdin)["result"];print(d.get("first_name","")+" @"+str(d.get("username","")))' 2>/dev/null)"
    pass "Token VALID — bot: $NAME"
  else
    DESC="$(echo "$ME" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("description","no response"))' 2>/dev/null || echo "unknown")"
    fail "Token REJECTED by Telegram: $DESC"
    echo "     👉 BotFather se naya token lo -> ./setconfig.sh --token <token>"
  fi

  WH="$(curl -s --max-time 20 "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" 2>/dev/null)"
  WURL="$(echo "$WH" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("result",{}).get("url",""))' 2>/dev/null || echo "")"
  if echo "$WH" | grep -q '"ok":true' && [ -n "$WURL" ]; then
    fail "WEBHOOK set hai: $WURL  → polling BLOCK ho jati hai!"
    echo "     👉 Fix:  curl -s \"https://api.telegram.org/bot${TOKEN}/deleteWebhook?drop_pending_updates=true\""
  elif echo "$WH" | grep -q '"ok":true'; then
    pass "Webhook clear hai (polling chalega)"
  else
    warn "Webhook check skip (network)"
  fi

  UP="$(curl -s --max-time 25 "https://api.telegram.org/bot${TOKEN}/getUpdates?timeout=1&limit=1" 2>/dev/null)"
  if echo "$UP" | grep -qi "terminated by other getUpdates"; then
    fail "DUPLICATE INSTANCE chal raha hai (Conflict)!"
    echo "     👉 Fix:  screen -ls   →  purani sessions band karo"
    echo "              pkill -f bot_fixed.py   →  ./start.sh"
  elif echo "$UP" | grep -q '"ok":true'; then
    pass "getUpdates OK — koi duplicate instance nahi"
  else
    DESC="$(echo "$UP" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("description","unknown"))' 2>/dev/null || echo "network")"
    warn "getUpdates response: $DESC"
  fi
fi

# ---------- 6. Process / screen ----------
echo ""
echo "【6】 RUNNING PROCESS"
line
if command -v pgrep >/dev/null 2>&1; then
  NPROC="$(pgrep -fc "python.*bot_fixed\.py" 2>/dev/null || echo 0)"
  if [ "$NPROC" -ge 2 ]; then
    fail "$NPROC instances chal rahe hain — Conflict ho jayega!"
    echo "     👉 Fix:  pkill -f bot_fixed.py ; ./start.sh"
  elif [ "$NPROC" -eq 1 ]; then
    pass "1 instance chal raha hai (PID: $(pgrep -f "python.*bot_fixed\.py" | head -1))"
  else
    warn "Koi bot process nahi chal raha"
    echo "     👉 Fix:  ./start.sh"
  fi
fi
if command -v screen >/dev/null 2>&1; then
  SESS="$(screen -ls 2>/dev/null | grep -E 'spidey|Attached|Detached' | tr -d '\t')"
  if [ -n "$SESS" ]; then
    echo "     sessions: $(echo "$SESS" | tr '\n' ' ')"
  else
    echo "     screen session: koi nahi"
  fi
fi

# ---------- 7. Log ----------
echo ""
echo "【7】 LAST LOG LINES (bot.log)"
line
if [ -f bot.log ]; then
  echo "  --- last 12 ---"
  tail -n 12 bot.log | sed 's/^/     /'
  ERRS="$(grep -Ei 'error|traceback|exception|unauthorized|conflict' bot.log | tail -5)"
  if [ -n "$ERRS" ]; then
    echo ""
    echo "  --- errors ---"
    echo "$ERRS" | sed 's/^/     /'
  fi
else
  warn "bot.log nahi mila — bot shayad kabhi start nahi hua"
fi

# ---------- Summary ----------
echo ""
echo "=============================================================="
if [ "$ISSUES" -eq 0 ]; then
  echo "  ✅ SAB THEEK HAI — bot chalna chahiye"
  echo "  Telegram me bhejo:  /ping   (jawab aana chahiye)"
  echo "  Phir:               /start  →  🕷️ SPIDEY-X ENGINE ⚡"
else
  echo "  ⚠️  $ISSUES issue mile — upar ke 👉 wale fix karo"
  echo ""
  echo "  🔧 Quick full reset:"
  echo "       pkill -f bot_fixed.py"
  echo "       ./setconfig.sh            # token + admin id"
  echo "       ./start.sh"
  echo "       ./logs.sh                 # live dekho"
fi
echo "=============================================================="
