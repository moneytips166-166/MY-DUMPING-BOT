#!/usr/bin/env bash
# snake_core.py ke saare tests — venv khud bana leta hai
set -u
cd "$(dirname "$0")/.." || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "🔧 venv bana rahe hain…"
  python3 -m venv .venv && .venv/bin/pip -q install -r tests/requirements.txt
fi
rc=0
echo "━━━ core   ━━━"; .venv/bin/python tests/test_core.py   || rc=1
echo "━━━ screens━━━"; .venv/bin/python tests/test_screens.py || rc=1
echo "━━━ flow   ━━━"; .venv/bin/python tests/repro_flows.py >/dev/null && echo "✅ repro OK" || rc=1
exit $rc
