#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#  snake_core.py — sirf COMPAT SHIM (patli file, ~20 lines)
#
#  Asli bot ab EK hi file me hai:  bot.py
#  Wahi file /storage/emulated/0/DBF/bot.py me bhi same rehti hai.
#
#  Purane scripts (start.sh / restart.sh / doctor.sh) snake_core.py chalate hain,
#  isliye ye shim bot.py ko isi namespace me load kar deta hai — code ek hi jagah,
#  duplicate nahi.
# ═══════════════════════════════════════════════════════════════════════════════
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.join(BASE, "bot.py")

if not os.path.exists(BOT):
    sys.exit("❌ bot.py nahi mila.\n"
             "   Chalao: ./update.sh   (ya DBF folder se copy karo)\n"
             "   Path dekha: %s" % BOT)

with open(BOT, encoding="utf-8") as _f:
    _src = _f.read()

# compile ka filename bot.py rakha hai — traceback me sahi line dikhegi
exec(compile(_src, BOT, "exec"))
