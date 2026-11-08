#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  HYPER v19.2 — /myid + /adminid COMMANDS  (Telegram bot only)
  Adds two tiny commands so aap apni Telegram user ID turant dekh sako:
      /myid      -> aapki user ID + admin status + license status
      /adminid   -> current ADMIN_IDS list (sirf admin ko, warna apni id)
  Run:  python3 hyper_myid_v19_2.py [bot_fixed.py]
================================================================================
"""

import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

BLOCK = r'''
# ═══════════════════════════════════════════════════════════════════════════════
#  V19.2 — /myid  &  /adminid   (Telegram user-id helper)
# ═══════════════════════════════════════════════════════════════════════════════
async def _v192_myid_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Apni Telegram user ID + admin/license status dikhata hai."""
    try:
        u = update.effective_user
        uid = int(u.id)
        uname = ("@" + u.username) if getattr(u, "username", None) else (getattr(u, "first_name", "") or "—")
        is_adm = False
        try:
            is_adm = bool(is_admin(uid))
        except Exception:
            is_adm = uid in ADMIN_IDS
        lic = "—"
        try:
            if uid in authorized_users:
                exp = authorized_users[uid].get("expires")
                lic = "✅ Active till `%s`" % exp.strftime("%d %b %Y %H:%M") if exp else "✅ Active"
            elif is_adm:
                lic = "👑 Admin (unlimited)"
            else:
                st = trial_status(uid)
                lic = {"active": "🟡 Trial active", "expired": "🔴 Trial expired", "none": "⚪ No license"}.get(st, "—")
        except Exception:
            pass
        txt = (
            "🪪 <b>YOUR TELEGRAM IDs</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👤 <b>Name:</b> %s\n"
            "🆔 <b>User ID:</b> <code>%s</code>\n"
            "💬 <b>Chat ID:</b> <code>%s</code>\n"
            "👑 <b>Admin:</b> %s\n"
            "🎫 <b>License:</b> %s\n\n"
            "📋 <i>Copy karo:</i> <code>%s</code>\n"
            "⚙️ Admin banana ho to bot file me:\n"
            "<code>ADMIN_IDS = [%s]</code>"
        ) % (
            uname, uid, int(update.effective_chat.id),
            "✅ YES" if is_adm else "❌ NO", lic,
            uid, uid,
        )
        await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.warning("V19.2 /myid failed: %s", exc)


async def _v192_adminid_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Admin ko poora ADMIN_IDS list dikhata hai; baaki ko sirf apni id."""
    try:
        uid = int(update.effective_user.id)
        if uid in ADMIN_IDS:
            ids = ", ".join("<code>%s</code>" % x for x in ADMIN_IDS)
            txt = (
                "👑 <b>ADMIN_IDS (current)</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "%s\n\n"
                "🔧 Change karne ke liye (Termux):\n"
                "<code>./setconfig.sh</code>"
            ) % ids
        else:
            txt = (
                "🔒 Ye command sirf admin ke liye hai.\n\n"
                "Aapki ID: <code>%s</code>\n"
                "Isko admin banane ke liye owner se bolo." % uid
            )
        await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.warning("V19.2 /adminid failed: %s", exc)


logger.info("🪪 V19.2 /myid + /adminid commands loaded")
'''

ANCHOR = 'aigen_callback,\n        pattern=r"^aigen_(anthropic|gemini|gpt4o|mistral|llama|deepseek)$",\n    ), group=-1)'
NEW_HANDLERS = ANCHOR + '''
    app.add_handler(CommandHandler("myid", _v192_myid_cmd), group=-1)
    app.add_handler(CommandHandler("adminid", _v192_adminid_cmd), group=-1)'''


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # idempotent
    src = re.sub(r"\n# ═+\n#  V19\.2 — /myid  &  /adminid.*?logger\.info\(\"🪪 V19\.2 /myid \+ /adminid commands loaded\"\)\n", "\n", src, flags=re.S)
    src = src.replace(NEW_HANDLERS, ANCHOR)

    if ANCHOR not in src:
        raise SystemExit("❌ Handler anchor nahi mila — file version mismatch.")

    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila.")

    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]
    src = src.replace(ANCHOR, NEW_HANDLERS, 1)

    backup = "%s.v192_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 70)
    print("  ✅ v19.2 ADDED:  /myid   +   /adminid")
    print("=" * 70)
    print("  Target : %s" % target)
    print("  Backup : %s" % backup)
    print("=" * 70)


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
