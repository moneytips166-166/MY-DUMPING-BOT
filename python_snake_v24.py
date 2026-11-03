#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYTHON SNAKE v24 — polish patch
===============================
1. Bache hue "Sᴘɪᴅᴇʏ / 𝙎𝙥𝙞𝙙𝙚𝙮 / 🕸️" naam hata diye (poora rebrand)
2. 4 user screens plain font me: Redeem Key • Premium • How To Use • Contact Owner
3. Saare "back" buttons plain ("⬅️ BACK"), plan buttons bhi plain ("1 Day — $8")
4. Home pe user ka plan/expiry dikhta hai
5. Admin: 📤 EXPORT USERS • 🔍 FIND USER (/find 12345) • 🧅 SCAN PROXIES

Usage:  python3 python_snake_v24.py bot_fixed.py
"""
import os
import re
import shutil
import sys
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v24 START ═══"
MARK_END = "# ═══ PYTHON SNAKE v24 END ═══"

BLOCK = r'''
# ═══ PYTHON SNAKE v24 START ═══
# ─────────────────────────────────────────────────────────────────────────────
#  PART A — plain labels, plan line on home, 4 user screens
# ─────────────────────────────────────────────────────────────────────────────
_V24_TAG = "V24-PYTHON-SNAKE"
_V12_VERSION_TAG = _V24_TAG   # badge / footer / kill-all button bhi V24 dikhe
_V24_PLAN_TXT = {
    "30ᴍ": "30 min", "1ʜ": "1 hour", "6ʜ": "6 hours", "1ᴅ": "1 Day",
    "3ᴅ": "3 Days", "5ᴅ": "5 Days", "10ᴅ": "10 Days", "15ᴅ": "15 Days",
    "20ᴅ": "20 Days", "30ᴅ": "30 Days",
}


def _v24_prev_back_button(text="back", data="menu_back"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="menu_back")]])


def back_button(text=None, data="menu_back"):   # noqa: F811
    """Sab jagah plain back button (font mix khatam)."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="menu_back")]])


def make_purchase_menu():   # noqa: F811
    rows = []
    for label, code, emoji, _delta in PLANS:
        plain = _V24_PLAN_TXT.get(code) or str(label)
        price = PLAN_PRICES.get(code, "?")
        rows.append([InlineKeyboardButton("%s %s — %s" % (emoji, plain, price),
                                          callback_data="buy_%s" % code)])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")])
    return InlineKeyboardMarkup(rows)


def _v24_plan_line(uid: int) -> str:
    try:
        if is_admin(uid):
            return "👑 <b>Admin</b> — full access"
        if uid in authorized_users:
            info = authorized_users[uid]
            exp = info.get("expires")
            if exp and exp > datetime.now():
                return "💎 <b>%s</b> • %s bache" % (info.get("plan", "plan"), _v23_dur(exp - datetime.now()))
        if uid in trial_users:
            st = trial_status(uid)
            if st == "active":
                return "🎁 <b>Free trial</b> active"
            return "⏳ Trial khatam — plan lo"
    except Exception:
        pass
    return "🔒 No plan — Redeem ya Premium dabao"


def _v24_home_text(update) -> str:
    u = getattr(update, "effective_user", None)
    name = (getattr(u, "first_name", "") or "")
    uid = getattr(u, "id", 0) or 0
    hi = ("Hi <b>%s</b>,\n" % name) if name else ""
    return ("🐍 <b>PYTHON SNAKE</b> 🐍\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            + hi +
            _v24_plan_line(uid) + "\n\n"
            "🤖 Auto dorking • Deep parsing • Verified SQLi\n\n"
            "👇 Neeche se option chuno:")


async def _v23_send_home(update, context, edit: bool = False) -> None:   # noqa: F811
    uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
    txt, kb = _v24_home_text(update), _v23_main_kb(uid)
    if edit:
        try:
            await update.callback_query.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass
    msg = getattr(update, "effective_message", None)
    if msg is not None:
        try:
            await msg.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=txt,
                                       reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ── 4 plain user screens ─────────────────────────────────────────────────────
def _v24_redeem_card():
    txt = ("🔑 <b>REDEEM KEY</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "Apni license key niche <b>paste</b> kar do (ya seedha chat me bhej do):\n\n"
           "• Format: <code>XXXXX-XXXXX-XXXXX-XXXXX</code>\n"
           "• Key mil gayi? Bas bhej do — plan khud lag jayega\n"
           "• Key nahi hai? 🍷 PREMIUM se plan lo")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍷 PREMIUM / PLANS", callback_data="menu_purchase")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])
    return txt, kb


def _v24_purchase_card(uid: int):
    lines = ["🍷 <b>PREMIUM — PLANS</b>",
             "━━━━━━━━━━━━━━━━━━━━━"]
    for label, code, emoji, _d in PLANS:
        plain = _V24_PLAN_TXT.get(code) or str(label)
        lines.append("%s <b>%s</b> — <code>%s</code>" % (emoji, plain, PLAN_PRICES.get(code, "?")))
    lines += ["", "💳 <b>Kaise kharide?</b>",
              "👉 Owner ko message karo: <code>%s</code>" % ADMIN_USERNAME,
              "👉 Coupon code: <code>%s</code>" % COUPON_CODE,
              "👉 Ya key lekar 🔑 REDEEM karo"]
    try:
        lines.append("")
        lines.append(_v24_plan_line(uid))
    except Exception:
        pass
    return "\n".join(lines)


def _v24_guide_card():
    txt = ("📖 <b>HOW TO USE</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "<b>Sabse aasan:</b> 🐍 AUTO DUMP dabao → scale chuno → seeds bhejo\n"
           "Bas — keywords, dorks, URLs, verified SQLi, report sab mil jayega.\n\n"
           "Thoda control chahiye to niche se topic chuno:")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📕 Full pipeline (dorks → dump)", callback_data="guide_pipeline")],
        [InlineKeyboardButton("📗 How to dump database", callback_data="guide_dump")],
        [InlineKeyboardButton("📘 How to extract CC/data", callback_data="guide_cc")],
        [InlineKeyboardButton("📙 Sqlmap settings guide", callback_data="guide_sqlopts")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])
    return txt, kb


def _v24_help_card(uid: int):
    txt = ("☎️ <b>CONTACT OWNER</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "🆘 Owner: <code>%s</code>\n"
           "💳 Plans / key / help — sab ke liye wahi message karo.\n\n"
           "📌 Apni ID bhi bhej dena: <code>%d</code>" % (ADMIN_USERNAME, uid))
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍷 PREMIUM / PLANS", callback_data="menu_purchase")],
        [InlineKeyboardButton("📖 HOW TO USE", callback_data="menu_guide")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])
    return txt, kb


# ─────────────────────────────────────────────────────────────────────────────
#  PART B — admin extras: export, find user, scan proxies
# ─────────────────────────────────────────────────────────────────────────────
def make_admin_menu():   # noqa: F811
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="v23a_home")],
        [InlineKeyboardButton("👥 USERS", callback_data="v23a_users_0"),
         InlineKeyboardButton("🔑 KEYS", callback_data="v23a_keys")],
        [InlineKeyboardButton("🏃 LIVE RUNS", callback_data="v23a_live"),
         InlineKeyboardButton("📂 USER VAULT", callback_data="uv_home_0")],
        [InlineKeyboardButton("🕵️ SPY ON/OFF", callback_data="admin_spytoggle"),
         InlineKeyboardButton("📈 STATS", callback_data="v23a_stats")],
        [InlineKeyboardButton("🧅 PROXIES", callback_data="v23a_proxy"),
         InlineKeyboardButton("⚙️ ENGINE", callback_data="v23a_engine")],
        [InlineKeyboardButton("📣 BROADCAST", callback_data="admin_broadcast"),
         InlineKeyboardButton("🚫 BANS", callback_data="admin_banlist")],
        [InlineKeyboardButton("📤 EXPORT USERS", callback_data="admin_exportusers"),
         InlineKeyboardButton("🔍 FIND USER", callback_data="v23a_find")],
        [InlineKeyboardButton("☢️ KILL ALL TASKS", callback_data="admin_killall")],
        [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="v23_home")],
    ])


def _v24_user_text(uid: int) -> str:
    rec = _v23_u_rec(uid)
    last = rec.get("last")
    last_s = datetime.fromtimestamp(float(last)).strftime("%d %b %H:%M") if last else "-"
    return ("👤 <b>USER DETAIL</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👤 Name: <b>%s</b>\n"
            "🔗 Username: %s\n"
            "🆔 ID: <code>%s</code>\n"
            "💎 Plan: <b>%s</b>\n"
            "🚫 Banned: <b>%s</b>\n"
            "🕒 Last seen: <code>%s</code>\n"
            "▶️ Starts: <code>%s</code> • Runs: <code>%s</code>\n"
            "🌍 URLs: <code>%s</code> • 🛡️ Vulns: <code>%s</code>") % (
        (rec.get("name") or "-")[:32], ("@" + rec["uname"]) if rec.get("uname") else "-",
        uid, _v23_plan_text(uid), "YES" if uid in banned_users else "no", last_s,
        format(int(rec.get("starts") or 0), ","), format(int(rec.get("runs") or 0), ","),
        format(int(rec.get("urls") or 0), ","), format(int(rec.get("vulns") or 0), ","))


def _v24_user_kb(uid: int):
    rows = [
        [InlineKeyboardButton("➕ 1 DAY", callback_data="v23a_add_%d_1" % uid),
         InlineKeyboardButton("➕ 7 DAYS", callback_data="v23a_add_%d_7" % uid),
         InlineKeyboardButton("➕ 30 DAYS", callback_data="v23a_add_%d_30" % uid)],
        [InlineKeyboardButton("🎁 GIVE PLAN", callback_data="v23a_plan_%d" % uid),
         InlineKeyboardButton("📂 FILES", callback_data="uv_u_%d_A_0" % uid)],
    ]
    if uid in banned_users:
        rows.append([InlineKeyboardButton("✅ UNBAN", callback_data="v23a_unban_%d" % uid)])
    else:
        rows.append([InlineKeyboardButton("🚫 BAN", callback_data="v23a_ban_%d" % uid)])
    rows.append([InlineKeyboardButton("⬅️ USERS", callback_data="v23a_users_0")])
    return InlineKeyboardMarkup(rows)


async def _v24_find_cmd(update, context) -> None:
    uid = update.effective_user.id
    msg = update.effective_message
    if not is_admin(uid):
        await msg.reply_text("❌ Admin only")
        return
    args = getattr(context, "args", None) or []
    raw = (args[0] if args else "").strip().lstrip("@")
    if not raw:
        await msg.reply_text("Usage: <code>/find 123456789</code> (ya /find @username)",
                             parse_mode=ParseMode.HTML)
        return
    target = None
    if raw.isdigit():
        target = int(raw)
    else:
        low = raw.lower()
        for k, v in list(_V23_USERS.items()):
            if (v.get("uname") or "").lower() == low:
                try:
                    target = int(k)
                except Exception:
                    target = None
                break
    if not target:
        await msg.reply_text("❌ User nahi mila — ID daalo ya pehle wo /start kare.")
        return
    try:
        ch = await context.bot.get_chat(target)
        rec = _V23_USERS.setdefault(str(target), {})
        rec["name"] = ch.full_name or rec.get("name") or ""
        rec["uname"] = ch.username or rec.get("uname") or ""
        _v23_flush(force=True)
    except Exception:
        pass
    await msg.reply_text(_v24_user_text(target), reply_markup=_v24_user_kb(target),
                         parse_mode=ParseMode.HTML)


async def _v24_scan_cmd(update, context) -> None:
    """Admin: proxy scan seedha command se."""
    uid = update.effective_user.id
    msg = update.effective_message
    if not is_admin(uid):
        await msg.reply_text("❌ Admin only")
        return
    note = await msg.reply_text("🧅 Proxy scan chal raha hai… (10-60s)")
    try:
        st = await _v22_proxy_scan(want=150, concurrency=220, force=True)
    except Exception as exc:
        st = {"scraped": 0, "checked": 0, "alive": 0, "pool": 0, "err": str(exc)}
    txt = ("🧅 <b>PROXY SCAN DONE</b>\n"
           "📥 Scraped: <code>%s</code>\n🔍 Checked: <code>%s</code>\n"
           "✅ Alive: <code>%s</code>\n🗄 Pool: <code>%s</code>"
           % (format(int(st.get("scraped") or 0), ","), format(int(st.get("checked") or 0), ","),
              format(int(st.get("alive") or 0), ","), format(int(st.get("pool") or 0), ",")))
    try:
        await note.edit_text(txt, parse_mode=ParseMode.HTML)
    except Exception:
        await msg.reply_text(txt, parse_mode=ParseMode.HTML)


async def _v24_find_hint(update, context) -> None:
    msg = update.effective_message
    try:
        await update.callback_query.edit_message_text(
            "🔍 <b>FIND USER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Chat me ye bhejo:\n"
            "<code>/find 123456789</code>  (Telegram ID)\n"
            "<code>/find @username</code>\n\n"
            "Ya 👥 USERS list se seedha tap karo.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 USERS", callback_data="v23a_users_0")],
                [InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")],
            ]), parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ── PART B2 — ek click me poora users export (plain CSV) ─────────────────────
def _v24_csv_safe(v) -> str:
    t = str(v if v is not None else "")
    t = t.replace("\n", " ").replace("\r", " ").replace(",", ";").strip()
    return t


def _v24_export_user_rows() -> list:
    _v23_init()
    now = datetime.now()
    ids = set()
    for x in list(all_user_ids) + list(trial_users.keys()):
        try:
            ids.add(int(x))
        except Exception:
            pass
    for k in list(_V23_USERS.keys()):
        try:
            ids.add(int(k))
        except Exception:
            pass
    rows = ["uid,name,username,plan,expires,banned,starts,runs,urls,vulns,last_seen"]
    for uid in sorted(ids):
        rec = _V23_USERS.get(str(uid)) or {}
        info = authorized_users.get(uid) or authorized_users.get(str(uid)) or {}
        if is_admin(uid):
            plan, exp = "admin", "-"
        elif isinstance(info, dict) and info.get("expires") and info["expires"] > now:
            plan, exp = (info.get("plan") or "plan"), info["expires"].strftime("%Y-%m-%d %H:%M")
        elif uid in trial_users:
            ends = trial_users[uid] + timedelta(minutes=int(TRIAL_MINUTES or 0))
            plan = "trial-active" if ends > now else "trial-expired"
            exp = ends.strftime("%Y-%m-%d %H:%M")
        else:
            plan, exp = "free", "-"
        last = rec.get("last")
        try:
            last_s = datetime.fromtimestamp(float(last)).strftime("%Y-%m-%d %H:%M") if last else "-"
        except Exception:
            last_s = "-"
        rows.append(",".join(_v24_csv_safe(x) for x in (
            uid, rec.get("name") or "-", ("@" + rec["uname"]) if rec.get("uname") else "-",
            plan, exp, "yes" if uid in banned_users else "no",
            int(rec.get("starts") or 0), int(rec.get("runs") or 0),
            int(rec.get("urls") or 0), int(rec.get("vulns") or 0), last_s)))
    return rows


async def _v24_export_users(update, context) -> None:
    q = update.callback_query
    rows = _v24_export_user_rows()
    body = ("# PYTHON SNAKE users export\n"
            "# generated: %s\n"
            "# total: %d\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(rows) - 1)) + "\n".join(rows)
    ts = datetime.now().strftime("%d%m%y_%H%M")
    await context.bot.send_document(
        chat_id=q.from_user.id,
        document=io.BytesIO(body.encode("utf-8")),
        filename="python_snake_users_%s.csv" % ts,
        caption="📤 <b>EXPORT USERS</b>\n%d users • CSV (Excel/Sheets me khul jayega)" % (len(rows) - 1),
        parse_mode=ParseMode.HTML)


# ─────────────────────────────────────────────────────────────────────────────
#  PART C — router (4 user screens + admin extras), commands
# ─────────────────────────────────────────────────────────────────────────────
_v24_prev_button_handler = button_handler


async def button_handler(update, context):   # noqa: F811
    q = getattr(update, "callback_query", None)
    data = (q.data or "") if q is not None else ""
    if q is not None and data:
        uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
        try:
            if data == "menu_redeem":
                await q.answer()
                txt, kb = _v24_redeem_card()
                try:
                    await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
                except Exception:
                    try:
                        await q.message.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
                    except Exception:
                        pass
                return REDEEM_WAIT_KEY
            if data == "menu_purchase":
                await q.answer()
                txt = _v24_purchase_card(uid)
                try:
                    await q.edit_message_text(txt, reply_markup=make_purchase_menu(), parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return PURCHASE_MENU
            if data == "menu_guide":
                await q.answer()
                txt, kb = _v24_guide_card()
                try:
                    await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return MENU
            if data == "menu_help":
                await q.answer()
                txt, kb = _v24_help_card(uid)
                try:
                    await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return MENU
            if data == "admin_exportusers":
                if not is_admin(uid):
                    await q.answer("❌ Admin only", show_alert=True)
                    return MENU
                await q.answer("📤 Export ban raha hai…")
                await _v24_export_users(update, context)
                return MENU
            if data == "v23a_find":
                if not is_admin(uid):
                    await q.answer("❌ Admin only", show_alert=True)
                    return MENU
                await q.answer()
                await _v24_find_hint(update, context)
                return MENU
        except Exception as exc:
            logger.warning("v24 user-screen error [%s]: %s", data, exc)
    return await _v24_prev_button_handler(update, context)


try:
    _v24_init_ok = True
    logger.info("🐍 PYTHON SNAKE %s loaded — plain screens • find/export • full rebrand", _V24_TAG)
except Exception:
    pass
# ═══ PYTHON SNAKE v24 END ═══
'''

# purane text me bache hue brand naam
TEXT_SWAPS = [
    ("𝙎𝙥𝙞𝙙𝙚𝙮", "𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚"),
    ("Sᴘɪᴅᴇʏ", "Pʏᴛʜᴏɴ Sɴᴀᴋᴇ"),
    ("🕸️", "🐍"),
]

CMD_ANCHOR = '    app.add_handler(CommandHandler("spy", _v23_spy_cmd), group=-1)'
CMD_ADD = CMD_ANCHOR + '''
    app.add_handler(CommandHandler("find", _v24_find_cmd), group=-1)
    app.add_handler(CommandHandler(["pscan", "scanproxies"], _v24_scan_cmd), group=-1)'''


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    for need in ("_v23_handle_cb", "PYTHON SNAKE v23 START", "_V22_SCALES"):
        if need not in src:
            raise SystemExit("❌ %s nahi mila — pehle v23 patch apply karo." % need)

    # ── idempotent cleanup ──
    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)
    src = src.replace(CMD_ADD, CMD_ANCHOR)

    # purane run ke text swaps undo (dobara chalane pe stable rahe)
    for old, new in TEXT_SWAPS:
        pass  # undo ki zaroorat nahi — ek baar badla to "old" string milti hi nahi

    n_swap = 0
    for old, new in TEXT_SWAPS:
        if old in src:
            n_swap += src.count(old)
            src = src.replace(old, new)

    if CMD_ANCHOR not in src:
        raise SystemExit("❌ v23 command anchor nahi mila.")
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)

    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila.")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v24_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 78)
    print("  ✅ PYTHON SNAKE v24 APPLIED")
    print("=" * 78)
    print("  Target   : %s" % target)
    print("  Backup   : %s" % os.path.basename(backup))
    print("  Rebrand  : %d purane naam/emoji swap kiye" % n_swap)
    print("  Screens  : Redeem • Premium • How-to-use • Contact (plain font)")
    print("  Admin    : /find <id> • 📤 Export CSV • 🧅 /pscan")
    print("=" * 78)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 python_snake_v24.py bot_fixed.py")
        raise SystemExit(1)
    patch(sys.argv[1])
