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
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  echo "⚠️  Bot pehle se chal raha hai (screen: snake)."
  echo "    Restart: ./restart.sh"
  exit 0
fi
echo "=== START $(date '+%Y-%m-%d %H:%M:%S') ===" >> bot.log
screen -dmS snake bash -c 'cd "'"$(pwd)"'" && python3 -u snake_core.py >> bot.log 2>&1'
sleep 3
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  echo "🚀 Started — logs: ./logs.sh"
else
  echo "❌ Start fail — neeche error:"
  sed -n '/=== START/,$p' bot.log | tail -n 25
fi
EOF
cat > stop.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
pkill -f "python3 -u snake_core.py" 2>/dev/null
pkill -f "python3 snake_core.py" 2>/dev/null
screen -S snake -X quit 2>/dev/null
sleep 1
echo "🛑 Stopped."
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
if screen -ls 2>/dev/null | grep -q "\.snake"; then
  echo "✅ Bot CHAL RAHA hai"
else
  echo "❌ Bot BAND hai"
fi
echo "── last start ke baad ka log ──"
./logs.sh | tail -n 8
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
