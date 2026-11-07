#!/usr/bin/env bash
# ==============================================================================
#  🐍 PYTHON SNAKE — VPS INSTALLER (Ubuntu / Debian / any systemd Linux)
#
#  Ek command (VPS ke root shell me):
#     curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/vps/vps_install.sh" -o si.sh && sudo bash si.sh
#
#  Kya karta hai:
#     • python3 + venv + pip + git + curl + screen install
#     • /opt/snake folder (data / dumps / logs / backups)
#     • alag user "snake" (bot root ke roop me nahi chalega)
#     • bot.py download (ya BOT_SRC se copy) + token purane bot se utha leta hai
#     • systemd service → 24/7 auto restart + boot pe start
#     • logrotate (log file 20 MB pe rotate)
#     • start / stop / restart / status / logs / update / config scripts
#
#  Options:
#     SNAKE_DIR=/opt/snake      install folder
#     SNAKE_USER=snake          service user (root nahi rakhna)
#     BOT_SRC=/path/bot.py      local bot.py se install (download nahi)
#     REPO_RAW=<url>            repo base url
#     --no-systemd              sirf screen based (purane VPS ke liye)
#     --no-apt                  packages install skip
#     --dry-run                 kuch install nahi, sirf steps print
# ==============================================================================
set -u

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot}"
SNAKE_DIR="${SNAKE_DIR:-/opt/snake}"
SNAKE_USER="${SNAKE_USER:-snake}"
BOT="bot.py"
BOT_SRC="${BOT_SRC:-}"
USE_SYSTEMD=1
DO_APT=1
DRY=0

for a in "$@"; do
  case "$a" in
    --no-systemd) USE_SYSTEMD=0 ;;
    --no-apt)     DO_APT=0 ;;
    --dry-run)    DRY=1 ;;
    -h|--help)    sed -n '2,30p' "$0"; exit 0 ;;
  esac
done

C_OK=$'\033[1;32m'; C_NO=$'\033[1;31m'; C_IN=$'\033[1;36m'; C_W=$'\033[1;33m'; C_0=$'\033[0m'
say()  { printf '%s\n' "$*"; }
ok()   { printf '%s✔%s %s\n' "$C_OK" "$C_0" "$*"; }
bad()  { printf '%s✖%s %s\n' "$C_NO" "$C_0" "$*"; }
warn() { printf '%s!%s %s\n' "$C_W" "$C_0" "$*"; }
step() { printf '\n%s━━ %s ━━%s\n' "$C_IN" "$*" "$C_0"; }
run()  {
  if [ "$DRY" = "1" ]; then printf '   [dry] %s\n' "$*"; return 0; fi
  eval "$@"
}

say "=============================================================="
say "  🐍 PYTHON SNAKE — VPS INSTALLER"
say "=============================================================="
printf '  folder : %s\n  user   : %s\n  systemd: %s\n  dry-run: %s\n' \
  "$SNAKE_DIR" "$SNAKE_USER" "$USE_SYSTEMD" "$DRY"

# ---------------------------------------------------------------- 0. root?
if [ "$(id -u)" != "0" ]; then
  warn "root nahi ho — /etc/systemd me likhne ki permission nahi milegi."
  warn "Behtar:  sudo bash $0"
  [ "$USE_SYSTEMD" = "1" ] && USE_SYSTEMD=0 && warn "systemd off → screen mode"
fi

# ---------------------------------------------------------------- 1. packages
step "1/8  Packages (python3, venv, pip, git, curl, screen)"
if [ "$DO_APT" = "1" ] && command -v apt-get >/dev/null 2>&1; then
  run "apt-get update -qq"
  run "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv python3-pip git curl ca-certificates tzdata screen rsync procps logrotate"
  ok "packages installed"
else
  warn "apt skip (ya apt nahi hai) — python3 / venv manually hona chahiye"
fi
PY="$(command -v python3 || true)"
[ -z "$PY" ] && { bad "python3 nahi mila — pehle install karo"; exit 1; }
ok "python: $("$PY" --version 2>&1)"

# ---------------------------------------------------------------- 2. folders
step "2/8  Folders ($SNAKE_DIR)"
run "mkdir -p '$SNAKE_DIR/data' '$SNAKE_DIR/dumps' '$SNAKE_DIR/logs' '$SNAKE_DIR/backups'"
ok "data / dumps / logs / backups ready"

# ---------------------------------------------------------------- 3. user
step "3/8  Service user ($SNAKE_USER)"
if [ "$(id -u)" = "0" ] && [ "$SNAKE_USER" != "root" ]; then
  if ! id "$SNAKE_USER" >/dev/null 2>&1; then
    run "useradd --system --home-dir '$SNAKE_DIR' --shell /usr/sbin/nologin '$SNAKE_USER'"
    ok "user '$SNAKE_USER' bana"
  else
    ok "user '$SNAKE_USER' pehle se hai"
  fi
else
  SNAKE_USER="$(id -un)"
  warn "service user = $SNAKE_USER"
fi

# ---------------------------------------------------------------- 4. venv
step "4/8  Python venv + packages"
run "'$PY' -m venv '$SNAKE_DIR/.venv'"
run "'$SNAKE_DIR/.venv/bin/pip' install -q --upgrade pip setuptools wheel"
run "'$SNAKE_DIR/.venv/bin/pip' install -q 'python-telegram-bot==21.11.1' 'aiohttp>=3.9'"
if [ "$DRY" = "0" ]; then
  "$SNAKE_DIR/.venv/bin/python" -c "import aiohttp, telegram; print('   telegram-bot', telegram.__version__, '| aiohttp', aiohttp.__version__)" \
    && ok "venv ready" || { bad "venv packages fail"; exit 1; }
fi

# ---------------------------------------------------------------- 5. bot.py
step "5/8  bot.py"
OLDBOT="$SNAKE_DIR/$BOT"
if [ -f "$OLDBOT" ] && [ "$DRY" = "0" ]; then
  cp -f "$OLDBOT" "$SNAKE_DIR/backups/${BOT%.py}_$(date +%Y%m%d_%H%M%S).py" && ok "purana bot backup"
fi
if [ -n "$BOT_SRC" ] && [ -f "$BOT_SRC" ]; then
  run "cp -f '$BOT_SRC' '$SNAKE_DIR/.bot.new'"
  ok "local file se copy: $BOT_SRC"
else
  if [ "$DRY" = "0" ]; then
    if ! curl -fsSL --retry 3 --retry-delay 2 --max-time 180 "$REPO_RAW/$BOT" -o "$SNAKE_DIR/.bot.new"; then
      bad "download fail — GitHub/network check karo (ya BOT_SRC=/path/bot.py do)"
      exit 1
    fi
  fi
fi
if [ "$DRY" = "0" ]; then
  BYTES="$(wc -c < "$SNAKE_DIR/.bot.new" | tr -d ' ')"
  if [ "${BYTES:-0}" -lt 50000 ]; then
    bad "file adhuri hai ($BYTES bytes) — abort"; rm -f "$SNAKE_DIR/.bot.new"; exit 1
  fi
  # token / admin purane bot se uthao
  if [ -f "$OLDBOT" ]; then
    "$SNAKE_DIR/.venv/bin/python" - "$OLDBOT" "$SNAKE_DIR/.bot.new" <<'PYEOF' || true
import re, sys
old_p, new_p = sys.argv[1], sys.argv[2]
def grab(p, pat, fl=re.M):
    try:
        m = re.search(pat, open(p, encoding="utf-8", errors="ignore").read(), fl)
        return m.group(1) if m else None
    except Exception:
        return None
tok = grab(old_p, r'^BOT_TOKEN\s*=\s*"([^"]*)"')
adm = grab(old_p, r'^ADMIN_IDS\s*=\s*(\[[^\]]*\])', re.M | re.S)
if not (tok and ":" in tok and "PUT_YOUR" not in tok):
    sys.exit(0)
src = open(new_p, encoding="utf-8").read()
src = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if adm:
    src = re.sub(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]', 'ADMIN_IDS = %s' % " ".join(adm.split()),
                 src, count=1, flags=re.M | re.S)
open(new_p, "w", encoding="utf-8").write(src)
print("   token + ADMIN_IDS purane bot se copy ho gaye")
PYEOF
  fi
  mv -f "$SNAKE_DIR/.bot.new" "$OLDBOT"
  "$SNAKE_DIR/.venv/bin/python" -m py_compile "$OLDBOT" && ok "bot.py compile OK ($(wc -l < "$OLDBOT") lines)"
fi
run "chmod 600 '$SNAKE_DIR/$BOT'"

# ---------------------------------------------------------------- 6. helpers
step "6/8  Control scripts (start / stop / restart / status / logs / update)"
write_script() {  # name content
  if [ "$DRY" = "1" ]; then printf '   [dry] write %s\n' "$1"; return 0; fi
  printf '%s\n' "$2" > "$SNAKE_DIR/$1"
  chmod +x "$SNAKE_DIR/$1"
}

if [ "$USE_SYSTEMD" = "1" ]; then
  SVC_CTL='systemctl'
  write_script start.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
sudo systemctl start snake && sudo systemctl --no-pager --lines=0 status snake
echo "👉 logs: ./logs.sh"'

  write_script stop.sh '#!/usr/bin/env bash
set -u; sudo systemctl stop snake && echo "🛑 band ho gaya"'

  write_script restart.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
sudo systemctl restart snake && sleep 2 && sudo systemctl --no-pager --lines=0 status snake
echo "👉 logs: ./logs.sh"'

  write_script status.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
if systemctl is-active --quiet snake; then
  echo "✅ Bot CHAL RAHA hai (systemd: active)"
  systemctl show snake -p MainPID --value | sed "s/^/   PID: /"
  systemctl show snake -p ActiveEnterTimestamp --value | sed "s/^/   Start: /"
else
  echo "❌ Bot BAND hai"
  systemctl --no-pager --lines=15 status snake || true
fi
echo "── last 8 log lines ──"
sudo journalctl -u snake -n 8 --no-pager 2>/dev/null | tail -n 8'

  write_script logs.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
if [ -f logs/bot.log ]; then tail -n "${1:-80}" -f logs/bot.log
else sudo journalctl -u snake -n "${1:-80}" -f --no-pager; fi'
else
  SVC_CTL='screen'
  write_script start.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
mkdir -p logs
if pgrep -f "python -u bot.py" >/dev/null 2>&1 || pgrep -f "python3 -u bot.py" >/dev/null 2>&1; then
  echo "pehle se chal raha hai"; exit 0
fi
if command -v screen >/dev/null 2>&1; then
  screen -wipe >/dev/null 2>&1
  screen -dmS snake bash -c "cd \"$(pwd)\" && exec .venv/bin/python -u bot.py >> logs/bot.log 2>&1"
else
  setsid nohup .venv/bin/python -u bot.py >> logs/bot.log 2>&1 < /dev/null &
  echo $! > .bot.pid
fi
sleep 3
if pgrep -f "u bot.py" >/dev/null 2>&1; then echo "started"; else echo "start fail"; tail -n 25 logs/bot.log 2>/dev/null; fi'

  write_script stop.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
pkill -f "u bot.py" >/dev/null 2>&1 && echo "band" || echo "pehle se band"
[ -f .bot.pid ] && kill "$(cat .bot.pid)" 2>/dev/null; rm -f .bot.pid
screen -S snake -X quit >/dev/null 2>&1 || true'

  write_script restart.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
./stop.sh >/dev/null 2>&1 || true
sleep 1
exec ./start.sh'

  write_script status.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
P="$(pgrep -f "u bot.py" 2>/dev/null | tr "\n" " ")"
if [ -n "${P:-}" ]; then echo "chal raha hai (PID: $P)"; else echo "band hai"; fi
tail -n 8 logs/bot.log 2>/dev/null || true'

  write_script logs.sh '#!/usr/bin/env bash
set -u; cd "$(dirname "$0")" || exit 1
mkdir -p logs; touch logs/bot.log
tail -n "${1:-80}" -f logs/bot.log'
fi
ok "control scripts ready ($SVC_CTL mode)"

# config.sh — token / admin set
if [ "$DRY" = "0" ]; then
cat > "$SNAKE_DIR/config.sh" <<'CONF_EOF'
#!/usr/bin/env bash
# ./config.sh --token 123456:AA... [--admin 8999053405]
set -u
cd "$(dirname "$0")" || exit 1
.venv/bin/python - "$@" <<'PYEOF'
import re, sys

args = sys.argv[1:]
tok = adm = None
i = 0
while i < len(args):
    if args[i] in ("--token", "-t") and i + 1 < len(args):
        tok = args[i + 1]; i += 2
    elif args[i] in ("--admin", "-a") and i + 1 < len(args):
        adm = args[i + 1]; i += 2
    else:
        i += 1
if not tok and not adm:
    print("usage: ./config.sh --token 123456:AA... [--admin 8999053405]")
    sys.exit(1)
src = open("bot.py", encoding="utf-8").read()
if tok:
    if ":" not in tok or "PUT_YOUR" in tok:
        print("token galat lag raha hai (format 123456:AA...)")
        sys.exit(1)
    src = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if adm:
    ids = [x for x in re.split(r"[,\s]+", adm) if x.strip().isdigit()]
    if not ids:
        print("admin id numeric honi chahiye")
        sys.exit(1)
    src = re.sub(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]',
                 "ADMIN_IDS = [%s]" % ", ".join(ids), src, count=1, flags=re.M | re.S)
open("bot.py", "w", encoding="utf-8").write(src)
print("bot.py updated" + (" (token)" if tok else "") + (" (admin)" if adm else ""))
PYEOF
chmod 600 bot.py
if command -v systemctl >/dev/null 2>&1 && systemctl is-enabled snake >/dev/null 2>&1; then
  sudo systemctl restart snake && echo "service restarted"
else
  ./restart.sh 2>/dev/null || true
fi
CONF_EOF
chmod +x "$SNAKE_DIR/config.sh"
fi

# update.sh — bot.py latest + token preserved
if [ "$DRY" = "0" ]; then
cat > "$SNAKE_DIR/update.sh" <<UPD_EOF
#!/usr/bin/env bash
# ./update.sh — latest bot.py (token/admin safe) + restart
set -u
cd "\$(dirname "\$0")" || exit 1
REPO_RAW="\${REPO_RAW:-$REPO_RAW}"
echo "downloading bot.py..."
cp -f bot.py "backups/bot_\$(date +%Y%m%d_%H%M%S).py" 2>/dev/null
if ! curl -fsSL --retry 3 --retry-delay 2 --max-time 180 "\$REPO_RAW/bot.py" -o .bot.new; then
  echo "download fail — purana bot waisa hi hai"; rm -f .bot.new; exit 1
fi
B=\$(wc -c < .bot.new | tr -d ' ')
if [ "\${B:-0}" -lt 50000 ]; then echo "adhura download (\$B bytes)"; rm -f .bot.new; exit 1; fi
.venv/bin/python - bot.py .bot.new <<'PYEOF'
import re, sys

old_p, new_p = sys.argv[1], sys.argv[2]

def grab(p, pat, fl=re.M):
    try:
        m = re.search(pat, open(p, encoding="utf-8", errors="ignore").read(), fl)
        return m.group(1) if m else None
    except Exception:
        return None

tok = grab(old_p, r'^BOT_TOKEN\s*=\s*"([^"]*)"')
adm = grab(old_p, r'^ADMIN_IDS\s*=\s*(\[[^\]]*\])', re.M | re.S)
src = open(new_p, encoding="utf-8").read()
if tok and ":" in tok and "PUT_YOUR" not in tok:
    src = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"', 'BOT_TOKEN = "%s"' % tok, src, count=1, flags=re.M)
if adm:
    src = re.sub(r'^ADMIN_IDS\s*=\s*\[[^\]]*\]', 'ADMIN_IDS = %s' % " ".join(adm.split()),
                 src, count=1, flags=re.M | re.S)
open(new_p, "w", encoding="utf-8").write(src)
print("   token/admin preserved")
PYEOF
.venv/bin/python -m py_compile .bot.new || { echo "compile fail — purana bot chalu rahega"; rm -f .bot.new; exit 1; }
mv -f .bot.new bot.py && chmod 600 bot.py
echo "bot.py updated"
./restart.sh 2>/dev/null || true
UPD_EOF
chmod +x "$SNAKE_DIR/update.sh"
fi
ok "config.sh + update.sh ready"

# doctor.sh — health check
if [ "$DRY" = "0" ]; then
  if [ -n "${BOT_SRC:-}" ] && [ -f "${BOT_SRC%/*}/vps/vps_doctor.sh" ]; then
    cp -f "${BOT_SRC%/*}/vps/vps_doctor.sh" "$SNAKE_DIR/doctor.sh"
  else
    curl -fsSL --retry 2 --max-time 60 "$REPO_RAW/vps/vps_doctor.sh" -o "$SNAKE_DIR/doctor.sh" \
      || warn "doctor.sh download fail (optional)"
  fi
  [ -f "$SNAKE_DIR/doctor.sh" ] && chmod +x "$SNAKE_DIR/doctor.sh" && ok "doctor.sh ready"
fi

# ---------------------------------------------------------------- 7. systemd
if [ "$USE_SYSTEMD" = "1" ]; then
  step "7/8  systemd service (24/7 + boot pe auto start)"
  SYSVER="$(systemctl --version 2>/dev/null | head -1 | awk '{print $2}' || echo 0)"
  OUTLINE="StandardOutput=journal"
  if [ "${SYSVER:-0}" -ge 240 ] 2>/dev/null; then
    OUTLINE="StandardOutput=append:$SNAKE_DIR/logs/bot.log"
  fi
  UNIT="/etc/systemd/system/snake.service"
  if [ "$DRY" = "0" ]; then
    cat > "$UNIT" <<EOF
[Unit]
Description=Python Snake Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SNAKE_USER
Group=$SNAKE_USER
WorkingDirectory=$SNAKE_DIR
Environment=PYTHONUNBUFFERED=1
Environment=TZ=Asia/Kolkata
ExecStart=$SNAKE_DIR/.venv/bin/python -u $SNAKE_DIR/bot.py
Restart=always
RestartSec=10
TimeoutStopSec=25
KillSignal=SIGTERM
$OUTLINE
StandardError=inherit
SyslogIdentifier=snake
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths=$SNAKE_DIR

[Install]
WantedBy=multi-user.target
EOF
    chown -R "$SNAKE_USER:$SNAKE_USER" "$SNAKE_DIR" 2>/dev/null || true
    chmod 700 "$SNAKE_DIR/.venv" 2>/dev/null || true
    systemctl daemon-reload
    systemctl enable snake >/dev/null 2>&1 && ok "boot pe auto-start ON"
    systemctl restart snake
    sleep 3
    if systemctl is-active --quiet snake; then
      ok "service chal rahi hai (snake)"
    else
      bad "service start nahi hui — logs:"
      journalctl -u snake -n 25 --no-pager 2>/dev/null | tail -n 25
    fi
    # logrotate
    cat > /etc/logrotate.d/snake <<EOF
$SNAKE_DIR/logs/*.log {
    daily
    rotate 7
    size 20M
    missingok
    notifempty
    compress
    delaycompress
    copytruncate
}
EOF
    ok "logrotate set (daily, 20MB, 7 files)"
  fi
else
  step "7/8  screen mode (systemd skip)"
  run "chown -R '$SNAKE_USER:$SNAKE_USER' '$SNAKE_DIR' 2>/dev/null || true"
  [ "$DRY" = "0" ] && ( cd "$SNAKE_DIR" && ./restart.sh )
fi

# ---------------------------------------------------------------- 8. summary
step "8/8  Summary"
KAT="$(grep -c 'PUT_YOUR_BOT_TOKEN_HERE' "$SNAKE_DIR/$BOT" 2>/dev/null || echo 0)"
say ""
say "  📁 Folder     : $SNAKE_DIR"
say "  🐍 Bot file   : $SNAKE_DIR/$BOT"
say "  💾 Data       : $SNAKE_DIR/data   (settings.json, rot_proxy.txt, manual_proxies.txt)"
say "  📄 Dumps      : $SNAKE_DIR/dumps"
say "  🧾 Logs       : $SNAKE_DIR/logs/bot.log"
say "  👤 Service user: $SNAKE_USER"
say ""
if [ "$KAT" != "0" ]; then
  warn "Abhi TOKEN set nahi hai. Do me se ek karo:"
  say "     cd $SNAKE_DIR && sudo ./config.sh --token 123456:AAxxxxxxxxxxxxxxxx"
  say "     ya phone se apna bot.py copy karo (token usme hai):"
  say "     scp /storage/emulated/0/DBF/bot.py root@<VPS-IP>:$SNAKE_DIR/bot.py"
  say "     phir:  sudo systemctl restart snake"
else
  ok "Token set hai — bot background me chal raha hai."
fi
say ""
say "  🎛  Commands :"
say "     cd $SNAKE_DIR"
say "     sudo ./status.sh      # chal raha hai ya nahi"
say "     sudo ./logs.sh        # live log"
say "     sudo ./restart.sh     # restart"
say "     sudo ./stop.sh        # band"
say "     sudo ./start.sh       # chalu"
say "     sudo ./update.sh      # naya bot.py + restart"
say "     sudo ./config.sh --token NEW_TOKEN"
say "     sudo ./doctor.sh      # 🩺 poora health check"
say ""
say "  📲 Verify: Telegram me  /ping  → v2.9.3 + uptime dikhna chahiye"
say ""
