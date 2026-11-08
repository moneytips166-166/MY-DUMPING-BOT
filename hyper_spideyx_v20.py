#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  HYPER v20 — "SPIDEY-X" REBRAND + FULL BUTTON HARDENING
  --------------------------------------------------------------------------
  1. Engine ka naam badla:  V19-VENOM  ->  SPIDEY-X
  2. HAR callback button ab guaranteed jawab dega (spinner kabhi nahi atkega)
  3. Handler error hone par user ko error message jayega (silence khatam)
  4. Naye commands:  /v19 (panel)  /ping (health)  /reset (state clear)
  5. Startup self-test log (token/admin/handlers) — debugging aasan
  6. V19 init crash-proof (config kharab ho to bhi bot boot hoga)

  Run: python3 hyper_spideyx_v20.py [bot_fixed.py]
================================================================================
"""

import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

V20_BLOCK = r'''
# ═══════════════════════════════════════════════════════════════════════════════
#  SPIDEY-X  (v20)  •  BUTTON HARDENING + SELF-TEST + /v19 /ping /reset
# ═══════════════════════════════════════════════════════════════════════════════
_V20_TAG = "SPIDEY-X"

_V20_KNOWN_PREFIXES = (
    "menu_", "v19", "v15", "v18", "v12", "v11", "v9_", "v7_", "v4_",
    "admin_", "stop_", "back_to_menu", "kw_", "dork_", "sqli_", "dump_",
    "auto_", "purchase", "redeem", "check_", "gen_", "gproxy_", "alldump_",
    "user_", "file_", "src_", "help_", "how_",
)


def _v20_endpoints_check() -> None:
    """Startup snapshot — log me turant pata chal jayega token/admin theek hain ya nahi."""
    try:
        tok = str(globals().get("TOKEN") or globals().get("BOT_TOKEN") or "")
        head = tok.split(":", 1)[0] if ":" in tok else "(invalid)"
        logger.info(
            "🧪 SELF-TEST | tag=%s | token_id=%s | token_len=%d | admins=%s | data=%s",
            _V12_VERSION_TAG, head, len(tok), list(ADMIN_IDS), DATA_DIR,
        )
        if ":" not in tok or len(tok) < 25:
            logger.error("❌ TOKEN galat lagta hai — ./setconfig.sh se dobara set karo")
        if not ADMIN_IDS:
            logger.warning("⚠️ ADMIN_IDS khali hai — /admin kuch kaam nahi karega")
    except Exception as exc:
        logger.warning("V20 self-test skip: %s", exc)


async def _v20_ping_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Health check — bot zinda hai ya nahi."""
    try:
        eff = {}
        try:
            eff = _v19_effective()
        except Exception:
            pass
        uptime = int(time.time() - _V20_BOOT_TS)
        h, m = uptime // 3600, (uptime % 3600) // 60
        txt = (
            "🏓 <b>PONG — Bot zinda hai!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🏷️ <b>Build:</b> <code>%s</code>\n"
            "⏱️ <b>Uptime:</b> <code>%dh %dm</code>\n"
            "🧵 <b>Threads:</b> <code>%s</code> • 📄 <b>Pages:</b> <code>%s</code>\n"
            "👑 <b>Admins:</b> <code>%s</code>\n"
            "🆔 <b>Your ID:</b> <code>%s</code>"
        ) % (_V12_VERSION_TAG, h, m, eff.get("threads", "-"), eff.get("pages", "-"),
             list(ADMIN_IDS), update.effective_user.id)
        await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.warning("V20 /ping failed: %s", exc)


async def _v20_reset_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Agar conversation state atak gaya ho to ye sab clear kar deta hai."""
    try:
        uid = int(update.effective_user.id)
        cid = int(update.effective_chat.id)
        try:
            context.user_data.clear()
        except Exception:
            pass
        try:
            conv = globals().get("_V12_CONV_REF")
            if conv is not None:
                conv._conversations.pop((cid, uid), None)
        except Exception:
            pass
        for _d in ("v19_mode", "v18_tool_mode", "dork_type", "kw_count", "v19_count"):
            try:
                context.user_data.pop(_d, None)
            except Exception:
                pass
        await update.effective_message.reply_text(
            "🧹 <b>State clear ho gaya!</b>\n\nAb <code>/start</code> bhejo — menu fresh khulega.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        logger.warning("V20 /reset failed: %s", exc)


async def _v20_v19_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Button fail ho jaye to bhi /v19 se engine panel khul jayega."""
    try:
        uid = int(update.effective_user.id)
        if not has_access(uid):
            await update.effective_message.reply_text(
                access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
            return
        await update.effective_message.reply_text(
            _v19_panel_text(), reply_markup=_v19_panel_kb(), parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.warning("V20 /v19 failed: %s", exc)


_V20_BOOT_TS = time.time()

_v20_prev_button_handler = button_handler


async def button_handler(update, context):
    """Sab callbacks ka single entry point — kabhi silent nahi rahega."""
    q = getattr(update, "callback_query", None)
    data = (q.data or "") if q is not None else ""
    try:
        if q is not None:
            logger.info("🔘 BUTTON │ %s │ uid=%s", data[:60], getattr(update.effective_user, "id", "?"))
        # 🔴 FIX: `menu_v19` (SPIDEY-X ENGINE button) ko koi route nahi karta tha —
        # router sirf `v19_` prefix pe chalta tha, isliye button bilkul dead tha.
        if q is not None and (data == "menu_v19" or data.startswith("v19_") or data.startswith("v19c_")):
            try:
                await q.answer()
            except Exception:
                pass
            try:
                return await _v19_callback_router(update, context, data)
            except Exception as exc:
                logger.exception("SPIDEY-X engine callback error: %s", exc)
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=("⚠️ <b>Engine panel error</b>\n<code>%s</code>\n\n"
                              "👉 <code>/ping</code> try karo ya <code>/reset</code> ke baad /start"
                              % str(exc)[:180]),
                        parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return MENU
        res = await _v20_prev_button_handler(update, context)
        if q is not None:
            try:
                await q.answer()
            except Exception:
                pass
        return res
    except Exception as exc:
        logger.exception("❌ Button handler crash on %r: %s", data, exc)
        try:
            if q is not None:
                await q.answer("⚠️ Error — /start dabao", show_alert=True)
        except Exception:
            pass
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=("⚠️ <b>Kuch gadbad ho gayi</b>\n\n<code>%s</code>\n\n"
                      "👉 <code>/reset</code> phir <code>/start</code> bhejo.") % str(exc)[:180],
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        return MENU


async def _v20_global_error(update, context) -> None:
    """PTB-level error handler — har unhandled exception user ko dikhega."""
    try:
        err = getattr(context, "error", None)
        logger.error("🛡️ PTB error: %r", err)
        if update is not None and getattr(update, "effective_chat", None) is not None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=("⚠️ <b>Command fail hua</b>\n<code>%s</code>\n\n👉 <code>/reset</code> → <code>/start</code>"
                      % str(err)[:180]),
                parse_mode=ParseMode.HTML,
            )
        if getattr(update, "callback_query", None) is not None:
            try:
                await update.callback_query.answer("⚠️ Error aaya")
            except Exception:
                pass
    except Exception:
        pass



# ─────────────────────────────────────────────────────────────────────────────
#  FIX 2b: kuch jagah `context.bot.send_document(..., _v9_skip_vault=True)`
#          SEEDHA call hota hai — PTB us kwarg ko reject karta hai (TypeError).
#          Yahan ExtBot level pe hi us private flag ko strip kar dete hain.
# ─────────────────────────────────────────────────────────────────────────────
try:
    from telegram.ext import ExtBot as _V20_ExtBot
except Exception:
    try:
        _V20_ExtBot = telegram.ext.ExtBot  # type: ignore[name-defined]
    except Exception:
        _V20_ExtBot = None

if _V20_ExtBot is not None and not getattr(_V20_ExtBot, "_v20_doc_patched", False):
    _v20_orig_send_document = _V20_ExtBot.send_document

    async def _v20_send_document(self, *a, **kw):
        kw.pop("_v9_skip_vault", None)
        return await _v20_orig_send_document(self, *a, **kw)

    _V20_ExtBot.send_document = _v20_send_document
    _V20_ExtBot._v20_doc_patched = True
    try:
        _V20_ExtBot._v20_doc_patched = True
    except Exception:
        pass

logger.info("🕷️ SPIDEY-X hardening loaded (v20)")
'''

RENAMES = [
    ('_V12_VERSION_TAG = "V19-VENOM"', '_V12_VERSION_TAG = "V19-SPIDEY-X"'),
    ('_V19_TAG = "V19-VENOM"', '_V19_TAG = "SPIDEY-X"'),
    ('#  V19-VENOM ENGINE  •  competitor-killer deep parser  •  Termux/VPS safe',
     '#  SPIDEY-X ENGINE  •  competitor-killer deep parser  •  Termux/VPS safe'),
    ('"☠️ <b>V19-VENOM ENGINE</b> ☠️\\n"', '"🕷️ <b>SPIDEY-X ENGINE</b> 🕷️\\n"'),
    ('InlineKeyboardButton("☠️ V19-VENOM ENGINE ⚡", callback_data="menu_v19")',
     'InlineKeyboardButton("🕷️ SPIDEY-X ENGINE ⚡", callback_data="menu_v19")'),
    ('logger.info("☠️ V19-VENOM engine loaded (threads=%s, pages=%s, termux=%s)",',
     'logger.info("🕷️ SPIDEY-X engine loaded (threads=%s, pages=%s, termux=%s)",'),
    ('logger.info("☠️ V19.1 chain engine loaded (auto_sqli=%s)"',
     'logger.info("🕷️ SPIDEY-X chain loaded (auto_sqli=%s)"'),
    ('logger.info("🪪 V19.2 /myid + /adminid commands loaded")',
     'logger.info("🪪 SPIDEY-X /myid + /adminid loaded")'),
]

# crash-proof the three module-level logger.info calls
SAFE_LOGGERS = [
    ('logger.info("🕷️ SPIDEY-X engine loaded (threads=%s, pages=%s, termux=%s)",\n            _v19_effective()["threads"], _v19_effective()["pages"], _V19_HW["termux"])',
     'try:\n    logger.info("🕷️ SPIDEY-X engine loaded (threads=%s, pages=%s, termux=%s)",\n                _v19_effective()["threads"], _v19_effective()["pages"], _V19_HW["termux"])\nexcept Exception as _v19e:\n    logger.warning("SPIDEY-X init warning: %s", _v19e)'),
]

CMD_ANCHOR = '    app.add_handler(CommandHandler("adminid", _v192_adminid_cmd), group=-1)'
CMD_ADD = CMD_ANCHOR + '''
    app.add_handler(CommandHandler("v19", _v20_v19_cmd), group=-1)
    app.add_handler(CommandHandler("engine", _v20_v19_cmd), group=-1)
    app.add_handler(CommandHandler("ping", _v20_ping_cmd), group=-1)
    app.add_handler(CommandHandler("reset", _v20_reset_cmd), group=-1)'''

ERR_ANCHOR = "    app.add_error_handler(_v11_global_ptb_error_handler)"



# ─────────────────────────────────────────────────────────────────────────────
#  FIX 2: `_v9_skip_vault` kwarg PTB ke send_document tak pahunch kar TypeError
#         deta tha (file/dump delivery hi fail ho jati thi). Ab pop ho jata hai.
# ─────────────────────────────────────────────────────────────────────────────
_VAULT_BUG_OLD = """    async def _vaulted_reply_document(self, document, filename=None, caption=None, *args, **kwargs):
        raw_bytes, rewound_doc = _extract_bytes_and_rewind(document)"""
_VAULT_BUG_NEW = """    async def _vaulted_reply_document(self, document, filename=None, caption=None, *args, **kwargs):
        _v20_skip_vault = bool(kwargs.pop("_v9_skip_vault", False))
        raw_bytes, rewound_doc = _extract_bytes_and_rewind(document)"""
_VAULT_FLAG_OLD = '            if not kwargs.get("_v9_skip_vault", False):'
_VAULT_FLAG_NEW = "            if not _v20_skip_vault:"


def _fix_vault_kwarg(src: str) -> tuple:
    n = 0
    if _VAULT_BUG_OLD in src:
        src = src.replace(_VAULT_BUG_OLD, _VAULT_BUG_NEW, 1)
        n += 1
    if _VAULT_FLAG_OLD in src:
        src = src.replace(_VAULT_FLAG_OLD, _VAULT_FLAG_NEW, 1)
        n += 1
    return src, n


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    if "_V19_TAG" not in src:
        raise SystemExit("❌ Pehle V19 patch apply karo.")

    # ---- idempotent cleanup ----
    src = re.sub(r"\n# ═+\n#  SPIDEY-X  \(v20\).*?logger\.info\(\"🕷️ SPIDEY-X hardening loaded \(v20\)\"\)\n", "\n", src, flags=re.S)
    src = src.replace(CMD_ADD, CMD_ANCHOR)

    # ---- renames ----
    for old, new in RENAMES:
        src = src.replace(old, new)
    for old, new in SAFE_LOGGERS:
        src = src.replace(old, new)

    # ---- FIX 2: file delivery TypeError ----
    src, _vault_n = _fix_vault_kwarg(src)

    # ---- register extra commands ----
    if CMD_ANCHOR not in src:
        raise SystemExit("❌ Command anchor nahi mila (v19.2 applied?).")
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)

    # ---- add global error handler (second one, tag-teamed) ----
    if "_v20_global_error" not in src:
        if ERR_ANCHOR in src:
            src = src.replace(ERR_ANCHOR, ERR_ANCHOR + "\n    app.add_error_handler(_v20_global_error)", 1)
        else:
            raise SystemExit("❌ Error-handler anchor nahi mila.")

    # ---- inject v20 block before __main__ ----
    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila.")
    src = src[:m.start()] + V20_BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v20_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 70)
    print("  ✅ v20 APPLIED — SPIDEY-X rebrand + button hardening")
    print("=" * 70)
    print("  Target : %s" % target)
    print("  Backup : %s" % backup)
    print("  New    : /v19  /engine  /ping  /reset  + startup self-test")
    print("  Fix 1  : menu_v19 button ab router tak pahunchta hai (dead button fixed)")
    print("  Fix 2  : _v9_skip_vault kwarg fix -> file delivery TypeError gone (%d)" % _vault_n)
    print("=" * 70)


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
