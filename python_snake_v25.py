#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYTHON SNAKE — v25 patch  (v24 ke upar chalao)

  python3 python_snake_v25.py bot_fixed.py

Kya karta hai:
  • Home me user ka apna kaam: "Aapka kaam: 3 runs • 40,014 URLs • 14 vulns"
  • Naya command /myplan  — plan, expiry, kitna bacha, aapke stats, files
  • FIND USER / USER DETAIL card me expiry + files count
  • 🍷 PREMIUM ke plan card naye plain style me (legacy ✿ card replace)
  • 🔑 REDEEM ka poora flow naye plain cards me (galat key / used key / success)
  • 📊 LEADERBOARD (admin) — top 10 users, bars, ALL TIME / AAJ toggle, /top command
  • Version: V25-PYTHON-SNAKE

Note: dobara chalane pe safe hai (idempotent) — purana block hata ke naya lagata hai.
"""
import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v25 START ═══"
MARK_END = "# ═══ PYTHON SNAKE v25 END ═══"

BLOCK = r'''# ═══ PYTHON SNAKE v25 START ═══
# ─────────────────────────────────────────────────────────────────────────────
#  v25 — leaderboard, /myplan, plain redeem+buy cards, user ke apne stats
# ─────────────────────────────────────────────────────────────────────────────
_V25_TAG = "V25-PYTHON-SNAKE"
_V12_VERSION_TAG = _V25_TAG


# ── chhote helpers ───────────────────────────────────────────────────────────
def _v25_files_count(uid) -> int:
    """User ke vault me kitni files hain."""
    try:
        base = str(globals().get("_V9_VAULT_DIR") or os.path.join(DATA_DIR, "user_vault"))
        d = os.path.join(base, str(int(uid)))
        if not os.path.isdir(d):
            return 0
        return sum(1 for f in os.listdir(d) if not f.startswith("."))
    except Exception:
        return 0


def _v25_my_work(uid) -> str:
    """User ka apna kaam — home / myplan me dikhta hai."""
    try:
        _v23_init()
        rec = _V23_USERS.get(str(int(uid))) or {}
        runs = int(rec.get("runs") or 0)
        urls = int(rec.get("urls") or 0)
        vulns = int(rec.get("vulns") or 0)
        if not (runs or urls or vulns):
            return "📈 Abhi koi run nahi — 🐍 AUTO DUMP se shuru karo"
        return ("📈 <b>Aapka kaam:</b> %s runs • %s URLs • %s vulns"
                % (format(runs, ","), format(urls, ","), format(vulns, ",")))
    except Exception:
        return ""


def _v25_expiry_line(uid) -> str:
    """Plan/trial ki expiry — din + kitna bacha."""
    try:
        now = datetime.now()
        uid = int(uid)
        if is_admin(uid):
            return "📅 <b>Expiry:</b> lifetime (admin)"
        if uid in authorized_users:
            info = authorized_users.get(uid) or {}
            exp = info.get("expires")
            if exp:
                left = exp - now
                if left.total_seconds() > 0:
                    return ("📅 <b>Expiry:</b> <code>%s</code> • <b>%s</b> bache"
                            % (exp.strftime("%d %b %H:%M"), _v23_dur(left)))
                return ("📅 <b>Expiry:</b> <code>%s</code> • <b>khatam</b>"
                        % exp.strftime("%d %b %H:%M"))
        if uid in trial_users:
            ends = trial_users[uid] + timedelta(minutes=int(TRIAL_MINUTES or 0))
            left = ends - now
            if left.total_seconds() > 0:
                return ("📅 <b>Trial ends:</b> <code>%s</code> • <b>%s</b> bache"
                        % (ends.strftime("%d %b %H:%M"), _v23_dur(left)))
            return "📅 <b>Trial:</b> khatam — plan lo"
    except Exception:
        pass
    return "📅 <b>Plan:</b> nahi hai — 🔑 REDEEM ya 🍷 PREMIUM"


# ── per-user aaj ka data (leaderboard ke AAJ tab ke liye) ────────────────────
_V25_DAY_FILE = os.path.join(DATA_DIR, "v25_day.json")
_V25_DAY: dict = {}
_V25_DAY_READY = {"done": False}


def _v25_day_init() -> None:
    if _V25_DAY_READY["done"]:
        return
    _V25_DAY_READY["done"] = True
    try:
        d = _v23_lj(_V25_DAY_FILE, {})
        if isinstance(d, dict):
            _V25_DAY.update(d)
    except Exception:
        pass


def _v25_day_save() -> None:
    try:
        keep = sorted(_V25_DAY.keys())[-10:]
        for k in list(_V25_DAY.keys()):
            if k not in keep:
                _V25_DAY.pop(k, None)
        _v23_sj(_V25_DAY_FILE, _V25_DAY)
    except Exception:
        pass


_v25_prev_note_run = _v23_note_run


def _v23_note_run(uid, kind, st):   # noqa: F811
    """v23 ka counter + v25 ka per-user/day counter (leaderboard AAJ ke liye)."""
    try:
        _v25_prev_note_run(uid, kind, st)
    except Exception:
        pass
    try:
        _v25_day_init()
        st = st or {}
        day = _v23_today()
        box = _V25_DAY.setdefault(day, {}).setdefault(
            str(int(uid)), {"runs": 0, "urls": 0, "vulns": 0})
        if kind == "parse":
            box["urls"] = int(box.get("urls") or 0) + int(st.get("unique") or 0)
        else:
            box["runs"] = int(box.get("runs") or 0) + 1
            box["vulns"] = int(box.get("vulns") or 0) + int(st.get("vulns") or 0)
        _v25_day_save()
    except Exception:
        pass


# ── leaderboard ──────────────────────────────────────────────────────────────
def _v25_bars(val, maxv, width=10) -> str:
    try:
        val = int(val or 0)
        maxv = int(maxv or 0)
    except Exception:
        return "░" * width
    if maxv <= 0 or val <= 0:
        return "░" * width
    n = int(round(width * float(val) / float(maxv)))
    n = max(1, min(width, n))
    return "▓" * n + "░" * (width - n)


def _v25_top_rows(mode="all") -> list:
    _v23_init()
    _v25_day_init()
    src = {}
    try:
        if mode == "today":
            src = dict(_V25_DAY.get(_v23_today(), {}) or {})
        else:
            src = dict(_V23_STATS.get("by_user", {}) or {})
    except Exception:
        src = {}
    rows = []
    for k, v in src.items():
        try:
            uid = int(k)
        except Exception:
            continue
        v = v or {}
        urls = int(v.get("urls") or 0)
        runs = int(v.get("runs") or 0)
        vulns = int(v.get("vulns") or 0)
        if urls or runs or vulns:
            rows.append((uid, urls, runs, vulns))
    rows.sort(key=lambda r: (r[1], r[3], r[2]), reverse=True)
    return rows


def _v25_top_card(mode="all"):
    rows = _v25_top_rows(mode)
    mode = "today" if mode == "today" else "all"
    mode_lbl = "AAJ" if mode == "today" else "ALL TIME"
    maxv = rows[0][1] if rows else 0
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for i, (uid, urls, runs, vulns) in enumerate(rows[:10], 1):
        rec = _V23_USERS.get(str(uid), {}) or {}
        nm = (rec.get("name") or str(uid))[:16]
        tag = medals.get(i, "%2d." % i)
        lines.append("%s <b>%s</b> — <code>%s</code> URLs\n"
                     "<code>%s</code> %s runs • %s vulns"
                     % (tag, nm, format(urls, ","),
                        _v25_bars(urls, maxv), format(runs, ","), format(vulns, ",")))
    try:
        today = (_V23_STATS.get("days", {}) or {}).get(_v23_today(), {}) or {}
        tot_urls = sum(r[1] for r in rows)
        txt = ("📊 <b>LEADERBOARD</b> — %s\n"
               "━━━━━━━━━━━━━━━━━━━━━\n"
               "👥 Users: <b>%s</b> • 🌍 URLs: <b>%s</b> • 🛡️ Vulns: <b>%s</b>\n"
               "📅 Aaj (sab): runs <b>%s</b> • URLs <b>%s</b>\n\n"
               "%s" % (mode_lbl, len(rows), format(tot_urls, ","),
                       format(sum(r[3] for r in rows), ","),
                       format(int(today.get("runs") or 0), ","),
                       format(int(today.get("urls") or 0), ","),
                       "\n\n".join(lines) if lines else "<i>abhi data nahi — AUTO DUMP chalao</i>"))
    except Exception:
        txt = "📊 <b>LEADERBOARD</b>\n<i>data nahi</i>"

    kb_rows = [[
        InlineKeyboardButton("🏆 ALL TIME" + (" ✅" if mode == "all" else ""), callback_data="v25a_top_all"),
        InlineKeyboardButton("📅 AAJ" + (" ✅" if mode == "today" else ""), callback_data="v25a_top_today"),
    ]]
    for uid, _u, _r, _v in rows[:5]:
        rec = _V23_USERS.get(str(uid), {}) or {}
        kb_rows.append([InlineKeyboardButton("👤 %s" % (rec.get("name") or uid)[:20],
                                             callback_data="v23a_u_%d" % uid)])
    kb_rows.append([InlineKeyboardButton("🔄 REFRESH", callback_data="v25a_top_%s" % mode)])
    kb_rows.append([InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")])
    return txt, InlineKeyboardMarkup(kb_rows)


# ── admin panel me LEADERBOARD tile ──────────────────────────────────────────
_v25_prev_admin_menu = make_admin_menu


def make_admin_menu():   # noqa: F811
    try:
        kb = _v25_prev_admin_menu()
        rows = [list(r) for r in kb.inline_keyboard]
        out = []
        for r in rows:
            out.append(r)
            if len(r) == 2 and getattr(r[0], "callback_data", "") == "admin_spytoggle":
                out.append([InlineKeyboardButton("📊 LEADERBOARD", callback_data="v25a_top_all")])
        return InlineKeyboardMarkup(out)
    except Exception:
        return _v25_prev_admin_menu()


# ── home: aapka kaam line ────────────────────────────────────────────────────
_v25_prev_home_text = _v24_home_text


def _v24_home_text(update):   # noqa: F811
    base = _v25_prev_home_text(update)
    try:
        uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
        line = _v25_my_work(uid)
        if not line:
            return base
        marker = "\n\n🤖 "
        if marker in base:
            return base.replace(marker, "\n" + line + marker, 1)
        return base + "\n" + line
    except Exception:
        return base


# ── USER DETAIL card me expiry + files ──────────────────────────────────────
_v25_prev_user_text = _v24_user_text


def _v24_user_text(uid):   # noqa: F811
    base = _v25_prev_user_text(uid)
    try:
        extra = [_v25_expiry_line(uid), "📂 Files: <b>%s</b>" % format(_v25_files_count(uid), ",")]
        return base + "\n" + "\n".join(extra)
    except Exception:
        return base


# ── /myplan ─────────────────────────────────────────────────────────────────
def _v25_myplan_card(update):
    u = getattr(update, "effective_user", None)
    uid = int(getattr(u, "id", 0) or 0)
    nm = (getattr(u, "first_name", "") or "boss")[:24]
    txt = ("💎 <b>MERA PLAN</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "👤 <b>%s</b> • <code>%s</code>\n"
           "%s\n%s\n%s\n"
           "📂 Files: <b>%s</b> • ▶️ Starts: <b>%s</b>"
           % (nm, uid, _v24_plan_line(uid), _v25_expiry_line(uid),
              _v25_my_work(uid), format(_v25_files_count(uid), ","),
              format(int((_V23_USERS.get(str(uid)) or {}).get("starts") or 0), ",")))
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="menu_redeem"),
         InlineKeyboardButton("🍷 PREMIUM", callback_data="menu_purchase")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="v23_home")],
    ])
    return txt, kb


async def _v25_myplan_cmd(update, context):
    try:
        _v23_touch(update, context)
    except Exception:
        pass
    txt, kb = _v25_myplan_card(update)
    try:
        await update.effective_message.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    return MENU


async def _v25_top_cmd(update, context):
    u = getattr(update, "effective_user", None)
    uid = int(getattr(u, "id", 0) or 0)
    if not is_admin(uid):
        try:
            await update.effective_message.reply_text("❌ Admin only")
        except Exception:
            pass
        return MENU
    txt, kb = _v25_top_card("all")
    try:
        await update.effective_message.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    return MENU


# ── plain plan card (legacy ✿ card ki jagah) ────────────────────────────────
def _v25_buy_card(plan_code: str):
    try:
        code, label, emoji, _delta = _v10_resolve_plan(plan_code)
    except Exception:
        code, label, emoji = plan_code, plan_code, "💎"
    label = label or plan_code
    short = (_V24_PLAN_TXT.get(plan_code) or _V24_PLAN_TXT.get(code) or label)
    price = (PLAN_PRICES.get(plan_code) or PLAN_PRICES.get(code) or "Owner se poochho")
    txt = ("🍷 <b>PLAN</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "%s <b>%s</b>\n"
           "💰 Price: <b>%s</b>\n"
           "🧛 Owner: <code>%s</code>\n\n"
           "Payment ke liye owner ko message karo — key milte hi\n"
           "🔑 REDEEM dabao aur sab features khul jayenge." % (emoji, short, price, ADMIN_USERNAME))
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥂 CONTACT OWNER", url="https://t.me/%s" % ADMIN_USERNAME.lstrip("@"))],
        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="menu_redeem"),
         InlineKeyboardButton("⬅️ BACK", callback_data="menu_purchase")],
    ])
    return txt, kb


# ── plain redeem flow ───────────────────────────────────────────────────────
async def _v25_redeem_flow(update, context) -> int:
    msg = getattr(update, "effective_message", None)
    u = getattr(update, "effective_user", None)
    uid = int(getattr(u, "id", 0) or 0)
    try:
        _v23_touch(update, context)
    except Exception:
        pass
    try:
        all_user_ids.add(uid)
    except Exception:
        pass
    raw = (getattr(msg, "text", "") or "") if msg is not None else ""
    try:
        key = _v10_extract_key_candidate(raw)
    except Exception:
        key = (raw or "").strip()

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍷 PREMIUM", callback_data="menu_purchase")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])

    if not key or key not in license_keys:
        if msg is not None:
            await msg.reply_text(
                "❌ <b>KEY GALAT HAI</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Format aisa hona chahiye: <code>XXXXX-XXXXX-XXXXX-XXXXX</code>\n\n"
                "Dhyan se copy karo (space/language check) — ya owner se nayi key lo.",
                reply_markup=back_kb, parse_mode=ParseMode.HTML)
        return REDEEM_WAIT_KEY

    try:
        info = _v10_normalize_key_entry(key, license_keys[key])
    except Exception:
        info = license_keys.get(key) or {}

    used_by = info.get("used_by")
    try:
        used_by_int = int(used_by) if used_by is not None else None
    except Exception:
        used_by_int = None
    if used_by_int is not None and used_by_int != uid:
        if msg is not None:
            await msg.reply_text(
                "❌ <b>YE KEY PEHLE USE HO CHUKI</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "1 key = 1 user. Owner se nayi key lo.",
                reply_markup=back_kb, parse_mode=ParseMode.HTML)
        return REDEEM_WAIT_KEY

    now = datetime.now()
    base = now
    try:
        if uid in authorized_users:
            exp = (authorized_users[uid] or {}).get("expires")
            if exp and exp > base:
                base = exp
    except Exception:
        pass
    delta = info.get("delta") or timedelta(0)
    expires = base + delta
    authorized_users[uid] = {"plan": info.get("label") or "Plan", "expires": expires, "granted_by": key}
    info["used_by"] = uid
    try:
        _save_auth()
    except Exception:
        pass
    try:
        _save_users()
    except Exception:
        pass
    try:
        _v9_log_activity(uid=uid, name=(getattr(u, "full_name", "") or str(uid)),
                         username=(getattr(u, "username", "") or ""),
                         module="🔑 Key Redeemed", detail="%s (%s)" % (key, info.get("label") or "plan"))
    except Exception:
        pass

    if msg is not None:
        await msg.reply_text(
            "✅ <b>KEY REDEEM HO GAYI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 Key: <code>%s</code>\n"
            "💎 Plan: <b>%s</b>\n"
            "📅 Valid till: <code>%s</code>\n"
            "⏳ Bacha: <b>%s</b>\n\n"
            "🚀 Ab 🐍 AUTO DUMP dabao — saare features khul gaye."
            % (key, info.get("label") or "Plan", expires.strftime("%d %b %Y %H:%M"),
               _v23_dur(expires - now)),
            parse_mode=ParseMode.HTML)
    await _v23_send_home(update, context)
    return MENU


async def redeem_key(update, context):   # noqa: F811
    return await _v25_redeem_flow(update, context)


# ── router front layer: buy_*, v25a_top_* ───────────────────────────────────
_v25_prev_button_handler = button_handler


async def button_handler(update, context):   # noqa: F811
    q = getattr(update, "callback_query", None)
    data = (q.data or "") if q is not None else ""
    if q is not None and data:
        uid = int(getattr(getattr(update, "effective_user", None), "id", 0) or 0)
        try:
            if data.startswith("buy_"):
                await q.answer()
                txt, kb = _v25_buy_card(data[4:])
                try:
                    await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return PURCHASE_MENU
            if data.startswith("v25a_top_"):
                if not is_admin(uid):
                    await q.answer("❌ Admin only", show_alert=True)
                    return MENU
                mode = "today" if data.endswith("today") else "all"
                await q.answer("📊 Leaderboard…")
                txt, kb = _v25_top_card(mode)
                try:
                    await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return MENU
        except Exception as exc:
            logger.warning("v25 router error [%s]: %s", data, exc)
    return await _v25_prev_button_handler(update, context)


try:
    logger.info("🐍 PYTHON SNAKE %s loaded — leaderboard • /myplan • plain redeem/buy", _V25_TAG)
except Exception:
    pass
# ═══ PYTHON SNAKE v25 END ═══
'''

CMD_ANCHOR = '    app.add_handler(CommandHandler(["pscan", "scanproxies"], _v24_scan_cmd), group=-1)'
CMD_ADD = CMD_ANCHOR + '''
    app.add_handler(CommandHandler("myplan", _v25_myplan_cmd), group=-1)
    app.add_handler(CommandHandler("top", _v25_top_cmd), group=-1)'''

NEED = ("PYTHON SNAKE v24 START", "_v24_find_cmd", "_V24_PLAN_TXT")


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    for need in NEED:
        if need not in src:
            raise SystemExit("❌ %s nahi mila — pehle v24 patch apply karo." % need)

    # ── idempotent cleanup ──
    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)
    src = src.replace(CMD_ADD, CMD_ANCHOR)

    if CMD_ANCHOR not in src:
        raise SystemExit("❌ v24 command anchor nahi mila.")
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)

    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v25_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 78)
    print("  ✅ PYTHON SNAKE v25 APPLIED")
    print("=" * 78)
    print("  Target     : %s" % target)
    print("  Backup     : %s" % os.path.basename(backup))
    print("  User       : home work-line • /myplan • plain redeem + plan cards")
    print("  Admin      : 📊 LEADERBOARD (ALL/AAJ) • /top • user detail me expiry+files")
    print("  Version    : %s" % "V25-PYTHON-SNAKE")
    print("=" * 78)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 python_snake_v25.py bot_fixed.py")
    patch(sys.argv[1])
