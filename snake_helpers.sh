#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🐍 PYTHON SNAKE CORE — helper scripts generator (start/stop/logs/...)
#  Isi folder me chalao:  bash snake_helpers.sh
# ==============================================================================
set -u
cd "$(dirname "$0")" || exit 1
echo "  🔧 helper scripts bana rahe hain…"
# ---------- 6. helper scripts ----------
cat > start.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1

# process zinda hai?
alive() {
  pgrep -f "python3 -u snake_core.py" >/dev/null 2>&1 && return 0
  pgrep -f "python3 snake_core.py"   >/dev/null 2>&1 && return 0
  return 1
}

screen -wipe >/dev/null 2>&1

if alive; then
  echo "⚠️  Bot pehle se chal raha hai (PID: $(pgrep -f snake_core.py 2>/dev/null | tr '\n' ' '))"
  echo "    Restart: ./restart.sh"
  exit 0
fi

# DEAD screen session (bot mar chuka par screen bacha hua) — hata do
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  if screen -ls 2>/dev/null | grep "\.snake" | grep -qi "dead"; then
    echo "🧹 Dead screen session mila — saaf kar rahe hain…"
  else
    echo "🧹 Purana screen session mila — saaf kar rahe hain…"
  fi
  screen -S snake -X quit >/dev/null 2>&1
  screen -wipe >/dev/null 2>&1
  sleep 1
fi

echo "=== START $(date '+%Y-%m-%d %H:%M:%S') ===" >> bot.log
screen -wipe >/dev/null 2>&1
screen -dmS snake bash -c 'cd "'"$(pwd)"'" && exec python3 -u snake_core.py >> bot.log 2>&1'

for i in 1 2 3 4 5 6 7 8; do
  sleep 1
  alive && break
done

if alive; then
  echo "🚀 Started (PID: $(pgrep -f snake_core.py 2>/dev/null | tr '\n' ' ')) — logs: ./logs.sh"
else
  echo "❌ Start fail (8 sec me bot nahi utha) — error:"
  echo "──────────────────────────────────────────"
  sed -n '/=== START/,$p' bot.log 2>/dev/null | tail -n 25
  echo "──────────────────────────────────────────"
  echo "👉 ./doctor.sh chalao"
  screen -S snake -X quit >/dev/null 2>&1
  screen -wipe >/dev/null 2>&1
fi
EOF
cat > stop.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
pkill -f "python3 -u snake_core.py" 2>/dev/null
pkill -f "python3 snake_core.py" 2>/dev/null
screen -S snake -X quit >/dev/null 2>&1
sleep 1
screen -wipe >/dev/null 2>&1
echo "🛑 Stopped (screen bhi saaf)."
EOF
cat > restart.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
./stop.sh >/dev/null 2>&1
sleep 1
./start.sh
EOF
cat > logs.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Sirf AAJ ke (last start ke baad ka) log dikhata hai — purana crash nahi
cd "$(dirname "$0")" || exit 1
if [ ! -f bot.log ]; then echo "(log khali — bot kabhi chala hi nahi)"; exit 0; fi
N="$(grep -n '=== START' bot.log | tail -1 | cut -d: -f1)"
if [ -n "${N:-}" ]; then
  sed -n "${N},\$p" bot.log | tail -n 50
else
  tail -n 50 bot.log
fi
EOF
cat > status.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
PIDS="$(pgrep -f snake_core.py 2>/dev/null | tr '\n' ' ')"
if [ -n "${PIDS:-}" ]; then
  echo "✅ Bot CHAL RAHA hai (PID: $PIDS)"
else
  echo "❌ Bot BAND hai"
  if screen -ls 2>/dev/null | grep "\.snake" | grep -qi "dead"; then
    echo "   ⚠️  Dead screen session pada hai — ./start.sh khud saaf kar dega"
  fi
fi
echo "── last start ke baad ka log ──"
./logs.sh 2>/dev/null | tail -n 8
EOF
cat > update.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_update.sh" -o .upd.tmp && bash .upd.tmp && rm -f .upd.tmp
EOF
cat > setconfig.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_setconfig.sh" -o .cfg.tmp && bash .cfg.tmp && rm -f .cfg.tmp
EOF
cat > doctor.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_doctor.sh" -o .doc.tmp && bash .doc.tmp && rm -f .doc.tmp
EOF
chmod +x start.sh stop.sh restart.sh logs.sh status.sh update.sh setconfig.sh doctor.sh 2>/dev/null
echo "  ✅ helpers ready"
