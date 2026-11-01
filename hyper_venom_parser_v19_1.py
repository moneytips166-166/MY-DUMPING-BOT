#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  HYPER VENOM v19.1 — PIPELINE CHAIN UPGRADE (Telegram bot only, no web)
  Applies on top of v19 (bot_fixed.py already patched with V19-VENOM).

  Adds:
    • 1-tap chain:  Parser  ➜  SQLi Checker  ➜  (dump button)
    • Live speed (dorks/s), ETA, per-engine hit table
    • Auto-continue toggle (parser finishes ➜ SQLi auto start)
    • Resume: re-run same dork file ➜ already-scanned dorks skipped
    • "Send files again" button after job

  Run:  python3 hyper_venom_parser_v19_1.py [bot_fixed.py]
================================================================================
"""

import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

V191_BLOCK = r'''
# ═══════════════════════════════════════════════════════════════════════════════
#  V19.1 — PIPELINE CHAIN • SPEED/ETA • PER-ENGINE TELEMETRY • RESUME
# ═══════════════════════════════════════════════════════════════════════════════
_V191_TAG = "V19.1-CHAIN"
_V191_LAST: dict = {}            # uid -> {"param_path":..., "all_path":..., "stats":...}
_V191_ENGINE_STATS: dict = {}
_V191_DONE_DORKS: dict = {}      # uid -> set(hash) of already scanned dorks

_V19_DEFAULT_CFG["auto_sqli"] = False
_V19_DEFAULT_CFG["auto_chain"] = True


def _v191_reset_engines() -> None:
    _V191_ENGINE_STATS.clear()


_v191_prev_fetch = _v19_fetch_serp


async def _v19_fetch_serp(session, eng_tuple, dork: str, page: int, proxy: str = "", timeout: float = 9.0):
    name = eng_tuple[0] if isinstance(eng_tuple, (tuple, list)) and eng_tuple else "?"
    rec = _V191_ENGINE_STATS.setdefault(name, {"ok": 0, "err": 0, "urls": 0})
    res = await _v191_prev_fetch(session, eng_tuple, dork, page, proxy, timeout)
    try:
        links, status = res
        if status == "ok":
            rec["ok"] += 1
            rec["urls"] += len(links or [])
        else:
            rec["err"] += 1
    except Exception:
        rec["err"] += 1
    return res


def _v191_speed_eta(st: dict) -> tuple:
    elapsed = max(0.001, time.time() - float(st.get("started") or time.time()))
    done = int(st.get("scanned") or 0)
    total = int(st.get("total") or 0)
    speed = done / elapsed
    remain = max(0, total - done)
    eta = (remain / speed) if speed > 0.01 else 0
    return speed, eta


def _v191_engines_block(top: int = 4) -> str:
    if not _V191_ENGINE_STATS:
        return ""
    rows = sorted(_V191_ENGINE_STATS.items(), key=lambda kv: kv[1]["urls"], reverse=True)[:top]
    lines = ["━━━━━━━━━━━━━━━━━━━━━", "<b>🔬 Engine hits:</b>"]
    for name, rec in rows:
        lines.append("  • <code>%s</code> → %s URLs (%s ok / %s err)" % (
            name, format(rec["urls"], ","), rec["ok"], rec["err"]))
    return "\n".join(lines)


def _v19_running_text(st: dict) -> str:
    pct = (st["scanned"] * 100.0 / max(1, st["total"]))
    speed, eta = _v191_speed_eta(st)
    eta_s = "%dm %ds" % (int(eta) // 60, int(eta) % 60) if eta >= 1 else "—"
    body = (
        "🌍 <b>DEEP PARSER — RUNNING</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>Done:</b> <code>%s/%s</code> dorks\n"
        "⚡ <b>Speed:</b> <code>%.1f</code> dorks/s • ⏳ <b>ETA:</b> <code>%s</code>\n"
        "🔗 <b>Raw:</b> <code>%s</code> • 💎 <b>Unique:</b> <code>%s</code>\n"
        "🎯 <b>?param=:</b> <code>%s</code> • ⚠️ <b>Retries:</b> <code>%s</code>\n"
        "🧵 <b>Threads:</b> <code>%s</code>\n\n"
        "<code>[%s]</code> <b>%d%%</b>\n"
        "⏳ <i>Please wait...</i>"
    ) % (
        format(st["scanned"], ","), format(st["total"], ","),
        speed, eta_s,
        format(st["raw"], ","), format(st["unique"], ","),
        format(st.get("param", 0), ","), format(st["retries"], ","),
        st["threads"], _v19_bar(pct), int(pct),
    )
    eng = _v191_engines_block(3)
    return body + ("\n" + eng if eng else "")


def _v19_done_text(st: dict, elapsed: float) -> str:
    speed = st["scanned"] / max(0.001, elapsed)
    body = (
        "🌍 <b>DEEP PARSER — COMPLETE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>Scanned:</b> <code>%s/%s</code> dorks\n"
        "⚡ <b>Speed:</b> <code>%.1f</code> dorks/s\n"
        "🔗 <b>Raw URLs:</b> <code>%s</code>\n"
        "💎 <b>Unique URLs:</b> <code>%s</code>\n"
        "🎯 <b>?param= URLs:</b> <code>%s</code>\n"
        "⚠️ <b>Errors:</b> <code>%s</code> • 🚫 <b>Filtered:</b> <code>%s</code>\n"
        "🧵 <b>Threads:</b> <code>%s</code> • ⏱ <code>%.1fs</code>\n"
        "<code>[%s]</code> <b>100%%</b>\n"
        "📦 <i>Files ready ⬇️</i>"
    ) % (
        format(st["scanned"], ","), format(st["total"], ","), speed,
        format(st["raw"], ","), format(st["unique"], ","), format(st.get("param", 0), ","),
        format(st["errors"], ","), format(st["filtered"], ","),
        st["threads"], elapsed, _v19_bar(100),
    )
    eng = _v191_engines_block(5)
    return body + ("\n" + eng if eng else "")


def _v191_chain_kb(uid: int, has_params: bool) -> "InlineKeyboardMarkup":
    rows = []
    if has_params:
        rows.append([InlineKeyboardButton("🛡️ Sᴄᴀɴ Sǫʟɪ Nᴏᴡ ⚡", callback_data="v19c_sqli")])
    rows.append([InlineKeyboardButton("📦 Sᴇɴᴅ Fɪʟᴇs Aɢᴀɪɴ", callback_data="v19c_files"),
                 InlineKeyboardButton("🔁 Rᴜɴ Aɢᴀɪɴ", callback_data="v19c_again")])
    rows.append([InlineKeyboardButton("⬅️ V19 Pᴀɴᴇʟ", callback_data="menu_v19")])
    return InlineKeyboardMarkup(rows)


async def _v19_do_deep_parse(update, context, dorks: list) -> int:
    uid = update.effective_user.id
    eff = _v19_effective()
    ev = asyncio.Event()
    _V19_STOP[int(uid)] = ev
    _v191_reset_engines()
    chat_id = update.effective_chat.id

    if int(uid) not in _V191_DONE_DORKS:
        _v191_load_done(int(uid))
    done_set = _V191_DONE_DORKS.setdefault(int(uid), set())
    skipped = 0
    if done_set:
        fresh = [d for d in dorks if (hash(d) & 0x7FFFFFFF) not in done_set]
        skipped = len(dorks) - len(fresh)
        if not fresh:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=("♻️ <b>Resume:</b> is dork file ke saare <code>%s</code> dorks pehle hi scan ho chuke hain.\n\n"
                      "📥 Naya dork file bhejo, ya <code>🔁 Run Again</code> se resume reset karo.") % format(len(dorks), ","),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧹 Rᴇsᴇᴛ Rᴇsᴜᴍᴇ", callback_data="v19c_reset"),
                                                    InlineKeyboardButton("⬅️ V19", callback_data="menu_v19")]]),
            )
            del msg
            return MENU
        dorks = fresh

    head = "🌍 <b>DEEP PARSER STARTING</b>\n⚡ Threads: <code>%s</code> • Pages: <code>%s</code>\n📥 Dorks: <code>%s</code>\n" % (
        eff["threads"], eff["pages"], format(len(dorks), ","))
    if skipped:
        head += "♻️ <b>Resume:</b> <code>%s</code> already-scanned dorks skipped\n" % format(skipped, ",")
    head += "\n<code>[%s]</code> 0%%" % _v19_bar(0)

    status = await context.bot.send_message(
        chat_id=chat_id, text=head, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="v19_stop")]]),
    )
    msg_id = status.message_id
    last = {"t": 0.0}

    async def _progress(snap: dict) -> None:
        now = time.time()
        if now - last["t"] < 2.5:
            return
        last["t"] = now
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id,
                                                text=_v19_running_text(snap), parse_mode=ParseMode.HTML)
        except Exception:
            pass

    try:
        result = await _v19_deep_parse(dorks, uid, progress=_progress)
    except Exception as exc:
        logger.exception("V19.1 deep parse failed: %s", exc)
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id,
                                                text="❌ Parser error: <code>%s</code>" % str(exc)[:300],
                                                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    finally:
        _V19_STOP.pop(int(uid), None)

    for d in dorks:
        done_set.add(hash(d) & 0x7FFFFFFF)
    _v191_save_done(int(uid))

    st = result["stats"]
    _V191_LAST[int(uid)] = {"param_path": result["param_path"], "all_path": result["all_path"], "stats": st}
    _v19_save_last = None
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, parse_mode=ParseMode.HTML,
            text=_v19_done_text(st, st.get("elapsed", 0.0)),
            reply_markup=_v191_chain_kb(uid, st.get("param", 0) > 0),
        )
    except Exception:
        pass

    for path, caption in ((result["param_path"], "🎯 V19 ?param= URLs"),
                          (result["all_path"], "🌍 V19 All Unique URLs")):
        try:
            with open(path, "rb") as fh:
                await context.bot.send_document(chat_id=chat_id, document=fh,
                                                filename=os.path.basename(path), caption=caption)
        except Exception:
            pass

    # auto-continue ➜ SQLi
    try:
        if _v19_load_cfg().get("auto_sqli") and st.get("param", 0) > 0:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚙️ <b>Auto-continue ON</b> → SQLi checker starting...",
                parse_mode=ParseMode.HTML)
            urls = []
            with open(result["param_path"], "r", encoding="utf-8", errors="ignore") as fh:
                for ln in fh:
                    s = ln.strip()
                    if s:
                        urls.append(s)
            return await _v19_do_sqli(update, context, urls)
    except Exception as exc:
        logger.warning("V19.1 auto-chain failed: %s", exc)
    return MENU


def _v19_cfg_kb():
    cfg = _v19_load_cfg()
    auto = "✅ ON" if cfg.get("auto_sqli") else "❌ OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Lite 24", callback_data="v19_thr_24"),
         InlineKeyboardButton("🟡 40", callback_data="v19_thr_40"),
         InlineKeyboardButton("🟠 60", callback_data="v19_thr_60")],
        [InlineKeyboardButton("🔵 100", callback_data="v19_thr_100"),
         InlineKeyboardButton("🔥 160", callback_data="v19_thr_160"),
         InlineKeyboardButton("⚡ Auto", callback_data="v19_thr_0")],
        [InlineKeyboardButton("📄 Pages: 1", callback_data="v19_pg_1"),
         InlineKeyboardButton("📄 Pages: 2", callback_data="v19_pg_2"),
         InlineKeyboardButton("📄 Pages: 3", callback_data="v19_pg_3")],
        [InlineKeyboardButton("🔗 Auto SQLi chain: %s" % auto, callback_data="v19_auto_toggle")],
        [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="menu_v19")],
    ])


def _v191_cfg_text() -> str:
    eff = _v19_effective()
    cfg = _v19_load_cfg()
    return (
        "⚙️ <b>ENGINE SETTINGS</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ Threads: <code>%s</code>\n📄 Pages/engine: <code>%s</code>\n"
        "🔗 Auto SQLi chain: <code>%s</code>\n\n"
        "<i>Phone/Termux: 40-60 threads, 1 page. VPS: 100-160, 2 pages.</i>"
    ) % (eff["threads"], eff["pages"], "ON" if cfg.get("auto_sqli") else "OFF")


_v191_prev_router = _v19_callback_router


async def _v19_callback_router(update, context, data: str) -> int:
    q = update.callback_query
    uid = update.effective_user.id

    if data == "v19c_files":
        last = _V191_LAST.get(int(uid)) or {}
        sent = 0
        for key, cap in (("param_path", "🎯 ?param= URLs"), ("all_path", "🌍 All Unique URLs")):
            p = last.get(key)
            if p and os.path.isfile(p):
                try:
                    with open(p, "rb") as fh:
                        await context.bot.send_document(chat_id=update.effective_chat.id, document=fh,
                                                        filename=os.path.basename(p), caption=cap)
                    sent += 1
                except Exception:
                    pass
        try:
            await q.answer("📦 %d file(s) sent" % sent)
        except Exception:
            pass
        return MENU

    if data == "v19c_again":
        last = _V191_LAST.get(int(uid)) or {}
        try:
            await q.answer("🔁 Bhejo dorks dobara (resume active)")
        except Exception:
            pass
        context.user_data["v19_mode"] = "parse"
        await q.edit_message_text(
            "🌍 <b>V19 DEEP PARSER — RE-RUN</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "♻️ Purane scanned dorks <b>skip</b> ho jayenge (resume).\n\n"
            "📥 Naya dorks <code>.txt</code> bhejo ya chat me paste karo.",
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return PARSER_WAIT_DORKS

    if data == "v19c_sqli":
        last = _V191_LAST.get(int(uid)) or {}
        p = last.get("param_path")
        if not has_access(uid):
            await q.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ", show_alert=True)
            return MENU
        urls = []
        if p and os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                urls = [ln.strip() for ln in fh if ln.strip()]
        if not urls:
            await q.answer("❌ Koi ?param= URL nahi mila", show_alert=True)
            return MENU
        try:
            await q.answer("🛡️ SQLi scan starting (%s URLs)" % format(len(urls), ","))
        except Exception:
            pass
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        return await _v19_do_sqli(update, context, urls)

    if data == "v19c_reset":
        _V191_DONE_DORKS.pop(int(uid), None)
        try:
            os.remove(os.path.join(_V19_OUT_DIR, "resume_%s.txt" % uid))
        except Exception:
            pass
        try:
            await q.answer("🧹 Resume memory cleared")
        except Exception:
            pass
        context.user_data["v19_mode"] = "parse"
        await q.edit_message_text(
            "🌍 <b>V19 DEEP PARSER — FRESH RUN</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 Dorks <code>.txt</code> bhejo ya chat me paste karo.",
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return PARSER_WAIT_DORKS

    if data == "v19_auto_toggle":
        cfg = _v19_load_cfg()
        _v19_save_cfg({"auto_sqli": not bool(cfg.get("auto_sqli"))})
        eff = _v19_effective()
        await q.answer("🔗 Auto SQLi: %s" % ("ON" if _v19_load_cfg().get("auto_sqli") else "OFF"))
        try:
            await q.edit_message_text(_v191_cfg_text(), reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU

    if data == "v19_cfg":
        await q.edit_message_text(_v191_cfg_text(), reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        return MENU

    if data.startswith("v19_thr_") or data.startswith("v19_pg_"):
        state = await _v191_prev_router(update, context, data)
        try:
            await q.edit_message_text(_v191_cfg_text(), reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return state

    return await _v191_prev_router(update, context, data)


_v191_prev_button_handler = button_handler


async def button_handler(update, context):
    q = getattr(update, "callback_query", None)
    data = (q.data or "") if q else ""
    if data.startswith("v19_"):
        try:
            await q.answer()
        except Exception:
            pass
        try:
            return await _v19_callback_router(update, context, data)
        except Exception as exc:
            logger.exception("V19.1 callback error: %s", exc)
            return MENU
    if data.startswith("v19c_"):
        try:
            return await _v19_callback_router(update, context, data)
        except Exception as exc:
            logger.exception("V19.1 chain callback error: %s", exc)
            return MENU
    return await _v191_prev_button_handler(update, context)


# ── Resume store: remember dorks per user in memory + disk (survives restarts) ──
def _v191_save_done(uid: int) -> None:
    try:
        p = os.path.join(_V19_OUT_DIR, "resume_%s.txt" % uid)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("\n".join(str(h) for h in list(_V191_DONE_DORKS.get(int(uid), set()))[:300000]))
    except Exception:
        pass


def _v191_load_done(uid: int) -> None:
    try:
        p = os.path.join(_V19_OUT_DIR, "resume_%s.txt" % uid)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                _V191_DONE_DORKS[int(uid)] = set(int(x) for x in fh.read().split() if x.isdigit())
    except Exception:
        pass


logger.info("☠️ V19.1 chain engine loaded (auto_sqli=%s)", _v19_load_cfg().get("auto_sqli"))
'''


def find_insert_index(src: str) -> int:
    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit('❌ `if __name__ == "__main__":` block nahi mila.')
    return m.start()


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)

    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    if "V19.1 — PIPELINE CHAIN" in src:
        src = re.sub(r"\n# ═+\n#  V19\.1 — PIPELINE CHAIN.*?logger\.info\(\"☠️ V19\.1 chain engine loaded.*?\n", "\n", src, flags=re.S)

    if "_V19_TAG = \"V19-VENOM\"" not in src:
        raise SystemExit("❌ Pehle V19 patch apply karo (hyper_venom_parser_v19.py).")

    idx = find_insert_index(src)
    src = src[:idx] + V191_BLOCK.strip("\n") + "\n\n\n" + src[idx:]

    backup = "%s.v191_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)

    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 70)
    print("  ✅ v19.1 PIPELINE CHAIN PATCH APPLIED")
    print("=" * 70)
    print("  Target : %s" % target)
    print("  Backup : %s" % backup)
    print("  Added  : chain buttons (SQLi/Files/Run-again), speed+ETA,")
    print("           per-engine hit table, auto-SQLi toggle, dork resume")
    print("=" * 70)


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
