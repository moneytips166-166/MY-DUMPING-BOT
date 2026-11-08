#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🩺 SPIDEY BOT DOCTOR v2 — "bot jawab nahi de raha" ka asli karan batata hai
#  Termux-safe: koi /tmp use nahi, koi file write nahi (parse check memory me).
#  Usage:  ./doctor.sh
# ==============================================================================
set -u
cd "$(dirname "$0")" 2>/dev/null || true

BOT_FILE="${BOT_FILE:-bot_fixed.py}"
PY="$(command -v python3 || command -v python || echo python3)"
REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot}"
OK="✅"; BAD="❌"; WARN="⚠️ "
ISSUES=0
FAILS=""; WARNS=""

line() { echo "──────────────────────────────────────────────────────────"; }
fail() { echo "  $BAD $1"; ISSUES=$((ISSUES+1)); FAILS="$FAILS\n     • $1"; }
warn() { echo "  $WARN $1"; ISSUES=$((ISSUES+1)); WARNS="$WARNS\n     • $1"; }
pass() { echo "  $OK $1"; }
num()  { echo "$1" | tr -dc '0-9' ; }   # "0 0\n" -> "00" type mess se bacho

# 🧷 Har jagah same helper: sirf ASLI bot process, command-line ke jhoothe match nahi
bot_pids() {
  { ps -eo pid,args 2>/dev/null || ps aux 2>/dev/null; } \
    | awk 'NR>1 && $2 ~ /(^|\/)python[0-9.]*$/ && $0 ~ /bot_fixed\.py/ {print $1}' \
    | tr -dc '0-9\n'
}
bot_pid_count() { bot_pids | grep -c . 2>/dev/null || echo 0; }


echo "=============================================================="
echo "  🩺 SPIDEY BOT DOCTOR v2"
echo "  Folder: $(pwd)"
echo "  Time  : $(date '+%d-%b-%Y %H:%M:%S')"
echo "=============================================================="

# ---------- 1. FILE + VERSION ----------
echo ""
echo "【1】 FILE & VERSION"
line
if [ ! -f "$BOT_FILE" ]; then
  fail "$BOT_FILE NAHI mila — installer dobara chalao"
  echo ""; echo "❌ Yahan se aage check nahi ho sakta."; exit 1
fi
BYTES="$(wc -c < "$BOT_FILE" | tr -d ' ')"
LINES="$(wc -l < "$BOT_FILE" | tr -d ' ')"
pass "$BOT_FILE mila ($BYTES bytes / $LINES lines)"

V_IS_SPIDEYX=0
V_IS_V19=0
grep -q '_V20_TAG *= *"SPIDEY-X"' "$BOT_FILE" 2>/dev/null && V_IS_SPIDEYX=1
grep -q 'V19-VENOM' "$BOT_FILE" 2>/dev/null && V_IS_V19=1

if [ "$V_IS_V19" -eq 1 ]; then
  fail "PURANI FILE chal rahi hai — V19-VENOM (SPIDEY-X / V20 nahi)"
  echo "     Isi wajah se naya button aur fixes nahi dikh rahe."
  echo "     👉 Fix:  ./update.sh    (token + admin id safe rahenge)"
elif [ "$V_IS_SPIDEYX" -eq 1 ]; then
  TAG="$(grep -m1 '^_V12_VERSION_TAG' "$BOT_FILE" 2>/dev/null | sed 's/.*= *"//; s/".*//')"
  pass "Version: ${TAG:-SPIDEY-X}  (latest build ✅)"
  grep -q 'CommandHandler("ping", _v20_ping_cmd)' "$BOT_FILE" 2>/dev/null \
    && pass "/ping command present" \
    || warn "/ping command nahi mila — file adhuri ho sakti hai (./update.sh)"
else
  warn "Version detect nahi hua — purani file lagti hai"
  echo "     👉 Fix:  ./update.sh"
fi

for _f in start.sh stop.sh restart.sh logs.sh; do
  [ -f "$_f" ] || { warn "$_f nahi mila — ./update.sh / installer dobara chalao"; break; }
done

# ---------- 2. PYTHON + PARSE ----------
echo ""
echo "【2】 PYTHON & SYNTAX"
line
pass "Python: $($PY -V 2>&1)"
if $PY - "$BOT_FILE" <<'PYEOF'
import ast, sys
try:
    src = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    ast.parse(src, filename=sys.argv[1])
except SyntaxError as e:
    print("   line %s: %s" % (e.lineno, e.msg))
    sys.exit(1)
except Exception as e:
    print("   %s" % e)
    sys.exit(1)
sys.exit(0)
PYEOF
then
  pass "Syntax OK (koi syntax error nahi)"
else
  fail "SYNTAX ERROR — file kharab hai (upar line number dekho)"
  echo "     👉 Fix:  cp backups/<purani-file> bot_fixed.py"
fi

# ---------- 3. DEPENDENCIES ----------
echo ""
echo "【3】 DEPENDENCIES"
line
$PY - <<'PYEOF'
import importlib, sys
mods = [("telegram", "python-telegram-bot"), ("aiohttp", "aiohttp"), ("bs4", "beautifulsoup4")]
bad = []
for mod, pkg in mods:
    try:
        m = importlib.import_module(mod)
        print("  ✅ %-12s %s" % (mod, getattr(m, "__version__", "?")))
    except Exception as e:
        print("  ❌ %-12s MISSING (%s)" % (mod, e)); bad.append(pkg)
if bad:
    print("\n     👉 Fix:  pip install " + " ".join(bad))
    sys.exit(3)
PYEOF
[ $? -eq 3 ] && ISSUES=$((ISSUES+1))

# ---------- 4. TOKEN & ADMIN ----------
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
    m = re.search(r'^ADMIN_IDS\s*=\s*\[([^\]]*)\]', src, re.M | re.S)
    print(" ".join((m.group(1) if m else "").split()))
except Exception:
    print("")
PYEOF
)"

if [ -z "$TOKEN" ]; then
  fail "BOT_TOKEN nahi mila — ./setconfig.sh chalao"
elif echo "$TOKEN" | grep -qE '^[0-9]{6,}:[A-Za-z0-9_-]{30,}$'; then
  pass "Token format OK (bot id: ${TOKEN%%:*})"
else
  fail "Token format GALAT: ${TOKEN%:*}:****"
  echo "     👉 Fix: ./setconfig.sh --token <BotFather-se-naya-token>"
fi

if [ -z "$ADMINS" ]; then
  warn "ADMIN_IDS khali hai — admin commands nahi chalenge"
  echo "     👉 Fix: ./setconfig.sh --admin <aapki-telegram-id>"
else
  pass "ADMIN_IDS = [$ADMINS]"
fi

# ---------- 5. TELEGRAM API ----------
echo ""
echo "【5】 TELEGRAM API (live)"
line
NET_OK=0
if [ -z "$TOKEN" ]; then
  warn "Token nahi hai to API check skip"
elif ! echo "$TOKEN" | grep -qE '^[0-9]{6,}:[A-Za-z0-9_-]{30,}$'; then
  warn "Token format galat — API check skip"
else
  ME="$(curl -s --max-time 25 "https://api.telegram.org/bot${TOKEN}/getMe" 2>/dev/null)"
  if [ -z "$ME" ]; then
    warn "Telegram tak pahunch nahi paya (internet issue)"
    echo "     📶 Mobile data/WiFi check karo. Bot chal raha ho to ye temporary blip hai."
  else
    NET_OK=1
    if echo "$ME" | grep -q '"ok":true'; then
      NAME="$(echo "$ME" | $PY -c 'import sys,json;d=json.load(sys.stdin)["result"];print(d.get("first_name","")+" @"+str(d.get("username","")))' 2>/dev/null)"
      pass "Token VALID — bot: $NAME"
    else
      DESC="$(echo "$ME" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("description","unknown"))' 2>/dev/null || echo unknown)"
      fail "Token REJECTED: $DESC"
      echo "     👉 Fix: BotFather -> /revoke -> naya token -> ./setconfig.sh --token <token>"
    fi

    WH="$(curl -s --max-time 25 "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" 2>/dev/null)"
    WURL="$(echo "$WH" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("result",{}).get("url",""))' 2>/dev/null || echo "")"
    if echo "$WH" | grep -q '"ok":true' && [ -n "$WURL" ]; then
      fail "WEBHOOK set hai ($WURL) → polling block ho jati hai!"
      echo "     👉 Fix: curl -s \"https://api.telegram.org/bot${TOKEN}/deleteWebhook?drop_pending_updates=true\""
    elif echo "$WH" | grep -q '"ok":true'; then
      pass "Webhook clear (polling chalega)"
    else
      warn "Webhook check skip (network)"
    fi

    UP="$(curl -s --max-time 30 "https://api.telegram.org/bot${TOKEN}/getUpdates?timeout=1&limit=1" 2>/dev/null)"
    if echo "$UP" | grep -qi "terminated by other getUpdates"; then
      fail "DUPLICATE INSTANCE (Conflict) — 2 bot chal rahe hain!"
      echo "     👉 Fix: pkill -f bot_fixed.py ; ./start.sh"
    elif echo "$UP" | grep -q '"ok":true'; then
      pass "getUpdates OK — koi duplicate instance nahi"
    else
      DESC="$(echo "$UP" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("description","unknown"))' 2>/dev/null || echo network)"
      warn "getUpdates: $DESC"
    fi
  fi
fi

# ---------- 6. PROCESS ----------
echo ""
echo "【6】 RUNNING PROCESS"
line
PIDS="$(num "$(bot_pid_count)")"; PIDS="${PIDS:-0}"
if [ "$PIDS" -ge 2 ]; then
  fail "$PIDS bot instances chal rahe hain — Conflict pakka!"
  echo "     👉 Fix: ./stop.sh ; ./start.sh"
elif [ "$PIDS" -eq 1 ]; then
  pass "1 instance chal raha hai (PID: $(bot_pids | head -1))"
else
  warn "Koi bot process nahi chal raha"
  echo "     👉 Fix: ./start.sh"
fi

if command -v screen >/dev/null 2>&1; then
  SESS="$(screen -ls 2>/dev/null | grep -E '[0-9]+\.spidey' || true)"
  DEAD="$(echo "$SESS" | grep -ic 'dead\|remote' 2>/dev/null || echo 0)"; DEAD="$(num "$DEAD")"
  ALIVE="$(echo "$SESS" | grep -ic 'attached\|detached' 2>/dev/null || echo 0)"; ALIVE="$(num "$ALIVE")"
  if [ "${DEAD:-0}" -gt 0 ] && [ "${ALIVE:-0}" -eq 0 ]; then
    warn "Purani screen sessions dead pade hain ($(echo "$SESS" | grep -c . )) — jagah gher rahi hain"
    echo "     👉 Cleanup: screen -wipe && ./start.sh"
  elif [ "${ALIVE:-0}" -gt 0 ]; then
    pass "screen session zinda hai"
  else
    echo "     screen: koi session nahi"
  fi
fi

# ---------- 7. LOG ----------
echo ""
echo "【7】 LAST LOG LINES (bot.log)"
line
if [ -f bot.log ]; then
  echo "  --- last 10 ---"
  tail -n 10 bot.log | cut -c1-160 | sed 's/^/     /'
  NETERRS="$(grep -c 'NetworkError\|ConnectError\|All connection attempts failed' bot.log 2>/dev/null || echo 0)"
  NETERRS="$(num "$NETERRS")"
  if [ "${NETERRS:-0}" -gt 0 ]; then
    echo ""
    echo "  📶 Network errors mile ($NETERRS baar) — ye phone ka internet blip hai,"
    echo "     bot khud retry karta rehta hai. WiFi/data stable karo (ya 'Acquire wakelock')."
  fi
  HARD="$(grep -Ei 'InvalidToken|Unauthorized|Conflict|Traceback' bot.log | tail -4)"
  if [ -n "$HARD" ]; then
    echo ""
    echo "  --- asli errors ---"
    echo "$HARD" | cut -c1-160 | sed 's/^/     /'
  fi
else
  warn "bot.log nahi mila — bot shayad kabhi start nahi hua"
  echo "     👉 Fix: ./start.sh  phir  ./logs.sh"
fi

# ---------- 8. SUMMARY ----------
echo ""
echo "=============================================================="
if [ "$ISSUES" -eq 0 ]; then
  echo "  ✅ SAB THEEK HAI"
  echo "  Telegram me bhejo:  /ping   (jawab aana chahiye)"
  echo "  Phir:               /start  →  🕷️ SPIDEY-X ENGINE ⚡"
else
  echo "  ⚠️  $ISSUES issue mile — upar 👉 wale fix karo"
  echo ""
  echo "  🔧 3-step reset:"
  echo "       1) ./update.sh      # latest bot (token/admin safe)"
  echo "       2) ./stop.sh ; screen -wipe   # purane dead sessions saaf"
  echo "       3) ./start.sh && ./logs.sh"
fi
echo "=============================================================="
