#!/usr/bin/env bash
# ==============================================================================
#  🩺 PYTHON SNAKE — VPS DOCTOR
#  Chalane ka tarika:   sudo /opt/snake/doctor.sh      (ya  bash vps/vps_doctor.sh)
#  Kya check karta hai: service, python/venv, token, disk, RAM, DNS, Telegram API,
#                       duplicate process, logs
# ==============================================================================
set -u
DIR="${SNAKE_DIR:-/opt/snake}"
SVC="${SNAKE_SVC:-snake}"
PASS=0; FAIL=0
ok()   { printf '  \033[1;32m✔\033[0m %s\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '  \033[1;31m✖\033[0m %s\n' "$*"; FAIL=$((FAIL+1)); }
info() { printf '  \033[1;36m•\033[0m %s\n' "$*"; }

echo "=============================================================="
echo "  🩺 PYTHON SNAKE — VPS DOCTOR   ($DIR)"
echo "=============================================================="

# ---------------------------------------------------------------- 1. files
echo ""
echo "── 1. Files ──"
[ -f "$DIR/bot.py" ] && ok "bot.py mila ($(wc -l < "$DIR/bot.py") lines)" || bad "bot.py nahi mila"
[ -x "$DIR/.venv/bin/python" ] && ok "venv: $("$DIR/.venv/bin/python" --version 2>&1)" || bad "venv nahi mila ($DIR/.venv)"
if [ -x "$DIR/.venv/bin/python" ]; then
  "$DIR/.venv/bin/python" -c "import aiohttp, telegram" 2>/dev/null \
    && ok "packages: $(  "$DIR/.venv/bin/python" -c 'import telegram,aiohttp;print("ptb",telegram.__version__,"| aiohttp",aiohttp.__version__)')" \
    || bad "python-telegram-bot / aiohttp missing → sudo $DIR/.venv/bin/pip install 'python-telegram-bot==21.11.1' 'aiohttp>=3.9'"
fi

# ---------------------------------------------------------------- 2. token
echo ""
echo "── 2. Config (token) ──"
if [ -f "$DIR/bot.py" ]; then
  TOKLINE="$(grep -m1 '^BOT_TOKEN' "$DIR/bot.py" || true)"
  case "$TOKLINE" in
    *PUT_YOUR*) bad "token set nahi hai → sudo $DIR/config.sh --token 123456:AA..." ;;
    *\":\"*)    ok "token set hai (${TOKLINE:0:40}…)" ;;
    *)          bad "token line ajeeb hai: $TOKLINE" ;;
  esac
  ADMIN="$(grep -m1 '^ADMIN_IDS' "$DIR/bot.py" || true)"
  [ -n "$ADMIN" ] && ok "admin: $ADMIN" || bad "ADMIN_IDS missing"
  V="$(grep -m1 '^VERSION' "$DIR/bot.py" || true)"
  info "version: ${V#VERSION = }"
fi

# ---------------------------------------------------------------- 3. service
echo ""
echo "── 3. Service ──"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q "^$SVC.service"; then
  if systemctl is-active --quiet "$SVC"; then
    ok "systemd: active (PID $(systemctl show "$SVC" -p MainPID --value))"
  else
    bad "systemd: inactive → sudo systemctl start $SVC ; sudo journalctl -u $SVC -n 40"
  fi
  systemctl is-enabled --quiet "$SVC" && ok "boot pe enabled (24/7)" || bad "boot pe enable nahi → sudo systemctl enable $SVC"
else
  info "systemd unit nahi mila — screen/nohup mode?"
  P="$(pgrep -f 'u bot.py' 2>/dev/null | tr '\n' ' ')"
  [ -n "${P:-}" ] && ok "process chal raha hai (PID: $P)" || bad "koi bot process nahi"
fi
N="$(pgrep -fc 'bot\.py' 2>/dev/null || echo 0)"
[ "${N:-0}" -le 1 ] && ok "ek hi instance ($N)" || bad "$N processes chal rahe hain — duplicate! (pkill -f bot.py phir restart)"

# ---------------------------------------------------------------- 4. network
echo ""
echo "── 4. Network / DNS ──"
if getent hosts api.telegram.org >/dev/null 2>&1; then
  ok "DNS: api.telegram.org → $(getent hosts api.telegram.org | awk '{print $1}' | head -1)"
else
  bad "DNS fail (api.telegram.org) → /etc/resolv.conf me 1.1.1.1 daalo"
fi
if curl -fsS --max-time 12 -o /dev/null -w '%{http_code}' https://api.telegram.org 2>/dev/null | grep -qE '^(200|302|404|401)$'; then
  ok "Telegram API reachable"
else
  info "Telegram API check inconclusive (firewall/proxy?)"
fi
if [ -f "$DIR/data/rot_proxy.txt" ]; then
  info "rotating proxy set: $(grep -c . "$DIR/data/rot_proxy.txt") endpoint(s)"
else
  info "rotating proxy file nahi hai (optional)"
fi

# ---------------------------------------------------------------- 5. system
echo ""
echo "── 5. System ──"
info "RAM : $(free -h 2>/dev/null | awk '/Mem:/{print $3" used / "$2" total"}' || echo '?')"
DISK="$(df -h "$DIR" 2>/dev/null | awk 'NR==2{print $4}')"
info "Disk free: ${DISK:-?} (dumps folder bada ho sakta hai)"
[ -n "${DISK:-}" ] && ok "disk check done" || bad "df fail"
info "Uptime: $(uptime -p 2>/dev/null || uptime)"
info "TZ    : $(date '+%Z %z') — Asia/Kolkata hona chahiye"

# ---------------------------------------------------------------- 6. logs
echo ""
echo "── 6. Last 12 log lines ──"
if [ -f "$DIR/logs/bot.log" ]; then
  tail -n 12 "$DIR/logs/bot.log"
elif command -v journalctl >/dev/null 2>&1; then
  journalctl -u "$SVC" -n 12 --no-pager 2>/dev/null
fi

echo ""
echo "=============================================================="
printf '  Result: \033[1;32m%d OK\033[0m • \033[1;31m%d issue\033[0m\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] && echo "  ✅ Sab theek — bot 24/7 chalega." || echo "  ⚠️  Upar ke ✖ wale steps follow karo."
echo "=============================================================="
exit 0
