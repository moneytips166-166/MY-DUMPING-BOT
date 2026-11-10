#!/usr/bin/env bash
# 🐍 SHADOW X — screen based start / stop / restart / logs / status
#   ./start.sh | ./stop.sh | ./restart.sh | ./status.sh | ./run.sh logs
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
SESS="shadow"
PY="${PY:-$(command -v python3)}"
LOG="$DIR/shadow.log"

ensure_screen() {
    command -v screen >/dev/null 2>&1 || { echo "❌ screen nahi hai — pkg install screen"; exit 1; }
}

# token: env → shadow_config.json → new.py ka DEFAULT_TOKEN
ensure_token() {
    if [ -z "${SHADOW_TOKEN:-}" ] && [ -f "$DIR/shadow_config.json" ]; then
        SHADOW_TOKEN="$(cd "$DIR" && python3 -c "import json;print((json.load(open('shadow_config.json')) or {}).get('token',''))" 2>/dev/null)"
    fi
    if [ -z "${SHADOW_TOKEN:-}" ]; then
        if grep -q '^DEFAULT_TOKEN = "[0-9]' "$DIR/new.py" 2>/dev/null; then
            echo "🔑 token: new.py ka default use ho raha hai (badalna ho to shadow_config.json)"
        else
            echo "❌ SHADOW_TOKEN nahi mila — export karo ya shadow_config.json banao"
            exit 1
        fi
    fi
    export SHADOW_TOKEN
}

case "${1:-start}" in
  start)
    ensure_screen; ensure_token
    if screen -list 2>/dev/null | grep -q "\.$SESS"; then echo "⚠️ pehle se chal raha hai ($SESS)"; exit 0; fi
    screen -dmS "$SESS" bash -c "cd '$DIR' && SHADOW_TOKEN='$SHADOW_TOKEN' $PY -u new.py >> '$LOG' 2>&1"
    sleep 2
    if screen -list 2>/dev/null | grep -q "\.$SESS"; then
        echo "✅ started — screen -r $SESS | log: $LOG"
    else
        echo "❌ start fail — log dekho:"; tail -n 20 "$LOG" 2>/dev/null
        exit 1
    fi
    ;;
  stop)
    ensure_screen
    screen -S "$SESS" -X quit 2>/dev/null && echo "⛔ stopped" || echo "kaam nahi chal raha tha"
    # bache-khuche process bhi saaf (sirf new.py wale)
    pkill -f "new.py" 2>/dev/null && echo "🧹 new.py process saaf" || true
    ;;
  restart)
    bash "$0" stop; sleep 1; bash "$0" start
    ;;
  logs)
    tail -f "$LOG"
    ;;
  status)
    ensure_screen
    if screen -list 2>/dev/null | grep -q "\.$SESS"; then
        echo "🟢 running ($SESS)"
        pgrep -af "new.py" | head -3
    else
        echo "⚪ not running"
    fi
    ;;
  *)
    echo "usage: ./run.sh start|stop|restart|logs|status  (ya start.sh/stop.sh/restart.sh/status.sh)"
    ;;
esac
