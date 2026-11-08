#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYTHON SNAKE — v27  (chhota patch)

  python3 python_snake_v27.py bot_fixed.py

Kya karta hai:
  • Home menu se "👑 ADMIN PANEL" button HATA deta hai (admin ko bhi nahi dikhega).
    Admin panel sirf /admin command se khulega.
  • Baaki sab v23 + classic look jaisa hi — koi feature add/remove nahi.

Dobara chalane pe safe.
"""
import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v27 START ═══"
MARK_END = "# ═══ PYTHON SNAKE v27 END ═══"

BLOCK = r'''# ═══ PYTHON SNAKE v27 START ═══
# ─────────────────────────────────────────────────────────────────────────────
#  Home menu se admin button hatao — admin panel sirf /admin se
# ─────────────────────────────────────────────────────────────────────────────
def _v23_main_kb(uid: int = 0):   # noqa: F811
    """User home keyboard — sirf 7 user buttons. Admin panel ka button nahi."""
    return InlineKeyboardMarkup(_v23_kb_rows())


_v27_prev_admin_cmd = admin_cmd


async def admin_cmd(update, context):   # noqa: F811
    """/admin — sirf admin ke liye naya dashboard (home me button nahi)."""
    uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
    if not is_admin(uid):
        if not _v27_prev_admin_cmd:
            return MENU
        return await _v27_prev_admin_cmd(update, context)
    msg = getattr(update, "effective_message", None)
    try:
        await msg.reply_text(_v23_dash_text(), reply_markup=make_admin_menu(),
                             parse_mode=ParseMode.HTML)
        return MENU
    except Exception:
        pass
    return await _v27_prev_admin_cmd(update, context)

try:
    logger.info("🐍 v27 — home se admin button hata • /admin se panel")
except Exception:
    pass
# ═══ PYTHON SNAKE v27 END ═══
'''

# command handler registration name se hota hai — function override kaafi hai
CMD_ANCHOR = ""
CMD_ADD = ""


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    if "PYTHON SNAKE v26 CLASSIC LOOK START" not in src:
        raise SystemExit("❌ v26 classic-look nahi mila — pehle v26 apply karo.")

    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)

    # chhota typo fix: "Yᴏᴜʜ" ➪ "Yᴏᴜ"
    src = src.replace("Yᴏᴜʜ", "Yᴏᴜ")
    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v27_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 70)
    print("  ✅ v27 APPLIED — home se admin button hata")
    print("=" * 70)
    print("  Target : %s" % target)
    print("  Backup : %s" % os.path.basename(backup))
    print("  Admin  : sirf /admin command se khulega")
    print("  Baaki  : sab v23 + classic look jaisa")
    print("  Typo   : Yᴏᴜʜ ➪ Yᴏᴜ")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 python_snake_v27.py bot_fixed.py")
    patch(sys.argv[1])
