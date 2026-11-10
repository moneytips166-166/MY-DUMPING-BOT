#!/usr/bin/env bash
# 🐍 SHADOW X — screen based start / stop / restart / logs
#   ./run.sh start | stop | restart | logs | status
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
SESS="shadow"
PY="${PY:-$(command -v python3)}"
LOG="$DIR/shadow.log"

ensure_screen() {
    command -v screen >/dev/null 2>&1 || { echo "❌ screen nahi hai — pkg install screen"; exit 1; }
}

ensure_token() {
    if [ -z "${SHADOW_TOKEN:-}" ] && [ -f "$DIR/shadow_config.json" ]; then
        SHADOW_TOKEN="$(cd "$DIR" && python3 -c "import json;print((json.load(open('shadow_config.json')) or {}).get('token',''))" 2>/dev/null)"
    fi
    [ -n "${SHADOW_TOKEN:-}" ] || { echo "❌ SHADOW_TOKEN nahi mila (export ya shadow_config.json)"; exit 1; }
    export SHADOW_TOKEN
}

case "${1:-start}" in
  start)
    ensure_screen; ensure_token
    if screen -list | grep -q "\.$SESS"; then echo "⚠️ pehle se chal raha hai ($SESS)"; exit 0; fi
    screen -dmS "$SESS" bash -c "cd '$DIR' && SHADOW_TOKEN='$SHADOW_TOKEN' $PY -u new.py >> '$LOG' 2>&1"
    sleep 2
    echo "✅ started — screen -r $SESS | log: $LOG"
    ;;
  stop)
    ensure_screen
    screen -S "$SESS" -X quit 2>/dev/null && echo "⛔ stopped" || echo "kaam nahi chal raha"
    ;;
  restart)
    "$0" stop; sleep 1; "$0" start
    ;;
  logs)
    tail -f "$LOG"
    ;;
  status)
    ensure_screen
    screen -list | grep "\.$SESS" || echo "⚪ not running"
    ;;
  *)
    echo "usage: ./run.sh start|stop|restart|logs|status"
    ;;
esac
