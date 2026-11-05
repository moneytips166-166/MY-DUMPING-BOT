#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🩺 PYTHON SNAKE — DOCTOR
#  Bot chal raha hai par jawab nahi de raha? Ye script wajah pakad legi.
#
#  Usage:  ./doctor.sh
# ==============================================================================
set -u
cd "$(dirname "$0")" || exit 1

PY="$(command -v python3 || echo python3)"
BOT="snake_core.py"
TMPD="${TMPDIR:-$PWD}"
SYN="$TMPD/.snake_syn"
num() { echo "${1:-0}" | tr -dc '0-9' | head -c 9 | sed 's/^$/0/'; }
OK=0; WARN=0; BAD=0

say()  { echo "$@"; }
ok()   { echo "  ✅ $*"; OK=$((OK+1)); }
warn() { echo "  ⚠️  $*"; WARN=$((WARN+1)); }
bad()  { echo "  ❌ $*"; BAD=$((BAD+1)); }

echo "=============================================================="
echo "  🩺 PYTHON SNAKE — DOCTOR"
echo "  Folder: $(pwd)"
echo "=============================================================="

# ---------- 1. files ----------
say ""
say "── 1. FILES ──────────────────────────────"
[ -f "$BOT" ] && ok "$BOT mila ($(wc -l < "$BOT") lines)" || bad "$BOT NAHI mila — installer dobara chalao"
[ -f bot.log ] && ok "bot.log mila ($(du -h bot.log | cut -f1))" || warn "bot.log nahi hai"
[ -d data ] && ok "data/ folder" || warn "data/ nahi hai (ban jayega)"
[ -d backups ] && ok "backups/ ($(ls backups 2>/dev/null | wc -l) files)" || warn "backups/ nahi hai"

# ---------- 2. syntax ----------
say ""
say "── 2. SYNTAX ─────────────────────────────"
if $PY -m py_compile "$BOT" 2>"$SYN"; then
  ok "File compile OK"
else
  bad "SYNTAX ERROR — file kharab hai:"
  sed -n "1,12p" "$SYN" 2>/dev/null | sed "s/^/      /"
  say "      👉 Rollback: cp backups/<purani> $BOT && ./restart.sh"
fi
rm -rf __pycache__ 2>/dev/null
rm -f "$SYN" 2>/dev/null

# ---------- 3. token ----------
say ""
say "── 3. TOKEN ──────────────────────────────"
TOK="$($PY - "$BOT" <<'PYEOF'
import re, sys
try:
    s = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    m = re.search(r'^BOT_TOKEN\s*=\s*"([^"]*)"', s, re.M)
    print(m.group(1) if m else "")
except Exception:
    print("")
PYEOF
)"
if [ -z "$TOK" ]; then
  bad "BOT_TOKEN line nahi mili"
elif echo "$TOK" | grep -q "PUT_YOUR"; then
  bad "TOKEN PLACEHOLDER hai — ./setconfig.sh --token <token> chalao"
elif ! echo "$TOK" | grep -qE '^[0-9]{6,}:[A-Za-z0-9_-]{30,}$'; then
  bad "Token ka format galat hai"
else
  ok "Token set hai (id: $(echo "$TOK" | cut -d: -f1), ...$(echo "$TOK" | rev | cut -c1-6 | rev))"
fi

# ---------- 4. process ----------
say ""
say "── 4. PROCESS ────────────────────────────"
SNAKE_PIDS="$(pgrep -f "python3 -u snake_core.py" 2>/dev/null; pgrep -f "python3 snake_core.py" 2>/dev/null | head -5)"
SNAKE_N="$(num "$(echo "$SNAKE_PIDS" | grep -c . 2>/dev/null)")"
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  if screen -ls 2>/dev/null | grep "\.snake" | grep -qi "dead"; then
    bad "screen session 'snake' DEAD hai (bot mar chuka, screen bacha hua)"
    say "      👉 Ye hi wajah hai ki start.sh 'pehle se chal raha hai' bolta tha"
    say "      👉 FIX: screen -wipe   (naya start.sh khud kar deta hai)"
  else
    ok "screen session 'snake' chal raha hai (alive)"
  fi
else
  warn "screen session 'snake' NAHI hai"
fi
if [ "$SNAKE_N" -ge 1 ]; then
  ok "snake_core.py process zinda (PID: $(echo $SNAKE_PIDS | tr '\n' ' '))"
else
  bad "snake_core.py ka koi process NAHI chal raha — ./start.sh chalao"
fi

# ⚠️ SABSE BADA PROBLEM: purana bot same token pe
OLD_PIDS="$(pgrep -f "bot_fixed.py" 2>/dev/null | head -5)"
OLD_N="$(num "$(echo "$OLD_PIDS" | grep -c . 2>/dev/null)")"
if [ "$OLD_N" -ge 1 ]; then
  bad "PURANA BOT abhi bhi chal raha hai (bot_fixed.py, PID: $(echo $OLD_PIDS | tr '\n' ' '))"
  say "      👉 SAME TOKEN pe 2 bot = jawab NAHI aayega (Telegram 409 Conflict)"
  say "      👉 FIX: pkill -f bot_fixed.py     phir: ./restart.sh"
else
  ok "Purana bot (bot_fixed.py) nahi chal raha"
fi

if [ "$SNAKE_N" -ge 2 ]; then
  bad "snake_core.py ke $SNAKE_N process chal rahe hain — sirf 1 hona chahiye"
  say "      👉 FIX: ./stop.sh ; ./start.sh"
fi

# ---------- 5. network + telegram api ----------
say ""
say "── 5. TELEGRAM API ───────────────────────"
if ! command -v curl >/dev/null 2>&1; then
  warn "curl nahi mila — API check skip"
else
  if [ -z "$TOK" ] || echo "$TOK" | grep -q "PUT_YOUR"; then
    warn "Token nahi — API check skip"
  else
    ME="$(curl -s --max-time 20 "https://api.telegram.org/bot$TOK/getMe")"
    if echo "$ME" | grep -q '"ok":true'; then
      UNAME="$(echo "$ME" | sed 's/.*"username":"\([^"]*\)".*/\1/')"
      ok "getMe OK — bot @$UNAME (token valid)"
    elif echo "$ME" | grep -q "401"; then
      bad "getMe 401 — token REVOKE ho chuka hai"
      say "      👉 BotFather → /revoke → naya token → ./setconfig.sh --token <naya>"
    else
      bad "getMe fail — net ya Telegram block"
      say "      $(echo "$ME" | head -c 200)"
    fi

    WH="$(curl -s --max-time 20 "https://api.telegram.org/bot$TOK/getWebhookInfo")"
    WHURL="$(echo "$WH" | sed -n 's/.*"url":"\([^"]*\)".*/\1/p')"
    if [ -n "${WHURL:-}" ]; then
      bad "WEBHOOK SET HAI: $WHURL"
      say "      👉 Webhook set hone se polling bilkul kaam nahi karti (bot chup)"
      say "      👉 FIX: curl -s \"https://api.telegram.org/bot\$TOKEN/deleteWebhook\""
      say "      (naya bot khud hi hata deta hai — ./restart.sh karo)"
    else
      ok "Webhook clear hai (polling mode theek)"
    fi

    UP="$(curl -s --max-time 20 "https://api.telegram.org/bot$TOK/getUpdates?offset=-1&limit=1")"
    if echo "$UP" | grep -q '"ok":true'; then
      ok "getUpdates OK — koi doosra instance updates nahi kha raha"
    elif echo "$UP" | grep -q "409"; then
      bad "409 CONFLICT — koi DOOSRA bot same token pe polling kar raha hai"
      say "      👉 FIX: pkill -f bot_fixed.py ; pkill -f snake_core.py ; ./start.sh"
    else
      warn "getUpdates: $(echo "$UP" | head -c 160)"
    fi
  fi
fi

# ---------- 6. log ----------
say ""
say "── 6. AAJ KA LOG (last start ke baad) ────"
if [ -f bot.log ]; then
  N="$(grep -n '=== START' bot.log | tail -1 | cut -d: -f1)"
  if [ -n "${N:-}" ]; then
    sed -n "${N},\$p" bot.log | tail -n 20 | sed 's/^/  │ /'
  else
    tail -n 20 bot.log | sed 's/^/  │ /'
  fi
  if grep -q "There is no current event loop" bot.log; then
    warn "log me PURANA 3.14 crash hai — agar last start ke baad ka hai to ./update.sh karo"
  fi
else
  say "  │ (log khali)"
fi

# ---------- 7. config ----------
say ""
say "── 7. CONFIG ─────────────────────────────"
ADM="$($PY - "$BOT" <<'PYEOF'
import re, sys
try:
    s = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    m = re.search(r'^ADMIN_IDS\s*=\s*\[([^\]]*)\]', s, re.M)
    print(m.group(1).strip() if m else "")
except Exception:
    print("")
PYEOF
)"
[ -n "$ADM" ] && ok "ADMIN_IDS = [$ADM]" || bad "ADMIN_IDS nahi mili"
if [ -f data/settings.json ]; then
  TH="$($PY -c "import json;d=json.load(open('data/settings.json'));print(d.get('theme','classic'))" 2>/dev/null || echo "?")"
  ok "Theme: $TH"
fi
say "  💡 Apni Telegram ID: bot me /myid bhejo"

# ---------- verdict ----------
say ""
say "=============================================================="
if [ "$BAD" -eq 0 ]; then
  say "  ✅ SAB THEEK — bot chalna chahiye"
elif [ "$BAD" -le 2 ]; then
  say "  ⚠️  $BAD problem mili — upar ke 👉 steps karo"
else
  say "  ❌ $BAD problems — neeche ka quick fix chalao"
fi
say "=============================================================="
if [ "$BAD" -gt 0 ]; then
  cat <<EOF

  🚑 QUICK FIX (ek saath chalao):

      cd ~/snake
      pkill -f bot_fixed.py            # purana bot band
      pkill -f snake_core.py           # koi adhura process
      screen -ls | grep snake && screen -S snake -X quit
      ./start.sh
      sleep 3
      ./doctor.sh                      # dobara check

EOF
fi
say "  📊 Summary: ✅ $OK ok   ⚠️  $WARN warn   ❌ $BAD problem"
say "=============================================================="
