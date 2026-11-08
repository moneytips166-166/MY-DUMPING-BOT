#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  SPIDEY-X PRO  (v21)  —  PARSER QUALITY + SPEED ENGINE
  --------------------------------------------------------------------------
  Competitor-level URL volume, bina 1 ghante me 30 min waste kiye.

  KYA BADLA:
   1. 3 engines/dork  ->  4-8 engines/dork (mode ke hisaab se, auto-tuned)
   2. Pages 1-2       ->  1-3 pages/engine
   3. Naye engines    ->  Yep, Stract, SearX(be/priv.au), Wiby  (16 -> 21)
   4. Wayback CDX     ->  purane/archived URLs = instant volume (lakhs URLs)
   5. Common Crawl    ->  CC index se aur URLs (optional)
   6. Canonical dedupe->  utm/fbclid jaise junk hataye, asli unique count
   7. Sig limit       ->  4-6 se 14-20 (ek hi template ke URLs block nahi hote)
   8. Engine scoring  ->  jo engine zyada deta hai, usko pehle chalata hai
   9. Adaptive        ->  block/error badhe to fanout khud kam, warna badhe
  10. Live metrics    ->  dorks/sec + ETA + URLs-per-dork + engine leaderboard

  NAYE COMMANDS:
    /domainer <site1,site2,..>   Wayback+CommonCrawl se bulk param URLs
    /bench                       5-dork live speed+quality test
    /stats                       engine leaderboard + last run

  Run: python3 hyper_spideyx_v21.py [bot_fixed.py]
================================================================================
"""

import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

MARK_START = "# ═══ SPIDEY-X PRO (v21) START ═══"
MARK_END = "# ═══ SPIDEY-X PRO (v21) END ═══"

BLOCK = r'''
# ═══ SPIDEY-X PRO (v21) START ═══
#  Quality + speed engine. Purane V19 functions ko runtime pe override karta hai.
# ═══════════════════════════════════════════════════════════════════════════════
_V21_TAG = "SPIDEY-X PRO"

# ── naye config keys (purani file me nahi the) ────────────────────────────────
_V19_DEFAULT_CFG.update({
    "mode": "balanced",     # fast | balanced | deep | max
    "sig_limit": 0,         # 0 = mode se lo
    "use_cdx": True,        # Wayback Machine
    "use_cc": True,         # Common Crawl
    "cdx_limit": 6000,      # per-domain CDX cap
    "adaptive": True,       # error rate ke hisaab se fanout auto-tune
})

_V21_PRESETS = {
    "fast":     {"fanout": 2, "pages": 1, "sig": 20},
    "balanced": {"fanout": 4, "pages": 2, "sig": 14},
    "deep":     {"fanout": 6, "pages": 2, "sig": 10},
    "max":      {"fanout": 8, "pages": 3, "sig": 8},
}

# ── naye engines (pehle se jo hain unhe chheda nahi) ──────────────────────────
_V21_EXTRA_ENGINES = [
    ("yep",      "https://api.yep.com/fs/2/search",  "get", "q", {"client": "web", "gl": "US", "limit": "30", "no_correct": "false", "safeSearch": "off", "type": "web"}),
    ("stract",   "https://stract.com/search",         "get", "q", {"lang": "en"}),
    ("searx_be", "https://searx.be/search",           "get", "q", {"format": "html", "language": "en-US"}),
    ("priv_au",  "https://priv.au/search",            "get", "q", {"language": "en-US"}),
    ("wiby",     "https://wiby.me/",                  "get", "q", {}),
    ("searxng",  "https://searxng.site/search",       "get", "q", {"language": "en-US"}),
]
_V21_PAGE_PARAM = {
    "stract": "s", "searx_be": "p", "priv_au": "p", "wiby": "p",
    "searxng": "p", "yep": "page", "marginalia": "s", "mojeek": "s",
}

_v21_existing = {e[0] for e in _V19_ENGINES}
for _e in _V21_EXTRA_ENGINES:
    if _e[0] not in _v21_existing:
        _V19_ENGINES.append(_e)
del _v21_existing

_V21_ENG_STATS = {}   # name -> {ok, urls, blocked, err}
_V21_LAST = {}


def _v21_eng(name: str) -> dict:
    d = _V21_ENG_STATS.get(name)
    if d is None:
        d = {"ok": 0, "urls": 0, "blocked": 0, "err": 0}
        _V21_ENG_STATS[name] = d
    return d


def _v21_score(name: str) -> float:
    d = _V21_ENG_STATS.get(name) or {}
    ok = d.get("ok", 0)
    urls = d.get("urls", 0)
    bad = d.get("blocked", 0) + d.get("err", 0)
    if ok + bad == 0:
        return 6.0                      # naya engine — fair chance
    return (urls + 4.0) / (ok + bad * 2.0 + 1.0)


def _v21_cfg() -> dict:
    cfg = _v19_load_cfg()
    mode = str(cfg.get("mode") or "balanced").lower()
    if mode not in _V21_PRESETS:
        mode = "balanced"
    pre = _V21_PRESETS[mode]
    eff = _v19_effective()
    pages = int(cfg.get("pages") or pre["pages"])
    sig = int(cfg.get("sig_limit") or 0) or pre["sig"]
    fanout = pre["fanout"]
    # Termux safety caps (battery + RAM)
    if _V19_HW["termux"]:
        pages = min(pages, 2)
        fanout = min(fanout, 4)
    return {
        "mode": mode, "fanout": fanout, "pages": max(1, min(3, pages)),
        "sig": max(0, min(50, sig)),
        "threads": eff["threads"],
        "max_per_domain": int(cfg.get("max_per_domain") or 0),
        "use_proxies": bool(cfg.get("use_proxies", True)),
        "use_cdx": bool(cfg.get("use_cdx", True)),
        "use_cc": bool(cfg.get("use_cc", True)),
        "cdx_limit": max(500, int(cfg.get("cdx_limit") or 6000)),
        "adaptive": bool(cfg.get("adaptive", True)),
    }


# ──────────────────────────  URL NORMALISATION  ──────────────────────────────
_V21_EXTRA_TRACKING = frozenset([
    "ref", "referrer", "src", "source", "spm", "scm", "trk", "tracking_id",
    "_ga", "_gl", "igshid", "share", "share_id", "s_kwcid", "ef_id", "cmpid",
    "pk_campaign", "vero_id", "wickedid", "oly_anon_id", "oly_enc_id",
])
_V21_ALL_TRACKING = _V19_TRACKING | _V21_EXTRA_TRACKING


def _v21_strip_tracking(u: str) -> str:
    """Junk query params hatao (utm/fbclid/ref...), baaki order preserve."""
    try:
        p = urllib_parse.urlsplit(u)
        if not p.query:
            return u
        keep = [(k, v) for k, v in urllib_parse.parse_qsl(p.query, keep_blank_values=True)
                if k.lower() not in _V21_ALL_TRACKING]
        if len(keep) == len(urllib_parse.parse_qsl(p.query, keep_blank_values=True)):
            return u
        return urllib_parse.urlunsplit((p.scheme, p.netloc, p.path,
                                        urllib_parse.urlencode(keep, doseq=True), ""))
    except Exception:
        return u


def _v21_canon(u: str) -> str:
    """Dedupe key — scheme/www/case/tracking/param-order normalised."""
    try:
        p = urllib_parse.urlsplit(u)
        host = _v19_strip_www((p.netloc or "").lower())
        path = re.sub(r"/+", "/", (p.path or "/")).rstrip("/") or "/"
        q = sorted((k.lower(), v) for k, v in urllib_parse.parse_qsl(p.query, keep_blank_values=True)
                   if k.lower() not in _V21_ALL_TRACKING)
        return host + path + ("?" + urllib_parse.urlencode(q) if q else "")
    except Exception:
        return u


# ─────────────────────  WAYBACK CDX + COMMON CRAWL  ─────────────────────────
_V21_CC_INDEX = {"id": ""}


async def _v21_cdx_fetch(session, domain: str, limit: int = 6000, timeout: float = 30.0):
    """Wayback CDX — ek domain ke saikdon/hazaron archived param URLs."""
    mock = os.environ.get("_V19_MOCK_SERP") or ""
    if mock:
        url = mock.rstrip("/") + "/cdx"
        params = {"domain": domain, "limit": str(limit)}
    else:
        url = "https://web.archive.org/cdx/search/cdx"
        params = {
            "url": domain + "/*", "output": "txt", "fl": "original",
            "collapse": "urlkey", "filter": "original:.*%3F.*",
            "limit": str(limit), "fastLatest": "true",
        }
    try:
        async with session.get(url, params=params, headers={"User-Agent": random.choice(_V19_UAS)},
                               timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as r:
            if r.status != 200:
                return []
            body = await r.text(errors="ignore")
    except Exception:
        return []
    out = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s.lower().startswith(("http://", "https://")):
            continue
        out.append(s)
        if len(out) >= limit:
            break
    return out


async def _v21_cc_index(session) -> str:
    if _V21_CC_INDEX["id"]:
        return _V21_CC_INDEX["id"]
    if os.environ.get("_V19_MOCK_SERP"):
        _V21_CC_INDEX["id"] = "MOCK"
        return "MOCK"
    try:
        async with session.get("https://index.commoncrawl.org/collinfo.json",
                               timeout=aiohttp.ClientTimeout(total=20), ssl=False) as r:
            if r.status == 200:
                data = await r.json(content_type=None)
                if isinstance(data, list) and data:
                    _V21_CC_INDEX["id"] = str(data[0].get("id") or "")
    except Exception:
        pass
    return _V21_CC_INDEX["id"]


async def _v21_cc_fetch(session, domain: str, limit: int = 6000, timeout: float = 35.0):
    """Common Crawl index — domain ke crawled URLs."""
    idx = await _v21_cc_index(session)
    if not idx:
        return []
    mock = os.environ.get("_V19_MOCK_SERP") or ""
    if mock:
        url = mock.rstrip("/") + "/cc"
        params = {"domain": domain, "limit": str(limit)}
    else:
        url = "https://index.commoncrawl.org/%s" % idx
        params = {"url": domain + "/*", "output": "json", "limit": str(limit)}
    try:
        async with session.get(url, params=params, headers={"User-Agent": random.choice(_V19_UAS)},
                               timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as r:
            if r.status != 200:
                return []
            body = await r.text(errors="ignore")
    except Exception:
        return []
    out = []
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("{"):
            m = re.search(r'"url"\s*:\s*"(https?:[^"]+)"', ln)
            if m:
                out.append(m.group(1).replace("\\/", "/"))
        elif ln.lower().startswith("http"):
            out.append(ln)
        if len(out) >= limit:
            break
    return out


def _v21_site_domains(dorks) -> list:
    seen, out = set(), []
    for d in dorks:
        for m in re.finditer(r"site:([a-z0-9][a-z0-9.\-]*\.[a-z]{2,12})", d or "", re.I):
            dom = m.group(1).lower()
            if dom.startswith("www."):
                dom = dom[4:]
            if dom not in seen:
                seen.add(dom)
                out.append(dom)
    return out[:120]


# ─────────────────────────────  SERP FETCH  ──────────────────────────────────
async def _v19_fetch_serp(session, eng_tuple, dork: str, page: int, proxy: str = "", timeout: float = 9.0) -> tuple:
    name, url, method, qparam, extra = eng_tuple
    params = dict(extra)
    params[qparam] = _v19_native_query(dork, name)
    if name.startswith("yahoo"):
        params["b"] = str(page * 10 + 1)
    elif name in ("bing_rss", "bing_html"):
        params["first"] = str(page * 10 + 1)
    elif name in ("mojeek", "marginalia", "stract"):
        params["s"] = str(page * 10)
    elif name == "ecosia":
        params["p"] = str(page + 1)
    elif name == "google":
        params["start"] = str(page * 10)
    elif name in ("ddg_lite", "ddg_html"):
        params["s"] = str(page * 30)
    elif name == "startpage":
        params["page"] = str(page + 1)
    elif name in _V21_PAGE_PARAM:
        params[_V21_PAGE_PARAM[name]] = str(page * 10 if name != "yep" else page + 1)
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
    headers = {
        "User-Agent": random.choice(_V19_UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with session.request(method.upper(), url, params=params, headers=headers, **kw) as resp:
            if resp.status != 200:
                st = _v21_eng(name)
                st["err" if resp.status in (404, 500, 502, 503) else "blocked"] += 1
                return [], "blocked" if resp.status in (403, 429, 401) else "err"
            body = await resp.text(errors="ignore")
    except Exception:
        _v21_eng(name)["err"] += 1
        return [], "err"
    if not body or len(body) < 400:
        _v21_eng(name)["err"] += 1
        return [], "err"
    if any(s in body[:7000].lower() for s in _V19_BLOCK_SIGS):
        _v21_eng(name)["blocked"] += 1
        return [], "blocked"
    links = _v19_extract_links(body, name)
    st = _v21_eng(name)
    if links:
        st["ok"] += 1
        st["urls"] += len(links)
    else:
        st["err"] += 1
    return links, "ok"


# ────────────────────────  LINK EXTRACTION (upgrade)  ────────────────────────
_V21_JSON_URL = re.compile(r'"(?:url|link|href)"\s*:\s*"(https?:(?:[^"\\]|\\.){4,600})"', re.I)


def _v19_extract_links(body: str, eng: str) -> list:
    if not body or len(body) < 60:
        return []
    out, seen = [], set()

    def _add(raw_u: str) -> None:
        u = (raw_u or "").replace("&amp;", "&").replace("\\/", "/").strip()
        if not u.startswith(("http://", "https://")):
            return
        for _ in range(2):
            if "%2F" in u.upper() or "%3A" in u.upper():
                try:
                    d = urllib_parse.unquote(u)
                    if d.startswith(("http://", "https://")):
                        u = d
                        continue
                except Exception:
                    pass
            break
        u = u.split("#", 1)[0]
        if "?" not in u:
            u = u.rstrip("/")
        if u and u not in seen and len(u) < 900:
            seen.add(u)
            out.append(u)

    head = body[:7000].lower()
    if eng == "bing_rss" or ("<rss" in head and "<item>" in head):
        for lk in _V19_RSS_LINK.findall(body):
            _add(lk)
        if out:
            return out
    flat = body.replace("&amp;", "&")
    # engines jo JSON deti hain (yep, cc, custom APIs)
    for ju in _V21_JSON_URL.findall(flat):
        _add(ju)
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
        elif hc.startswith("//"):
            _add("https:" + hc)
    return out


def _v21_pick_engines(idx: int, pg: int, fanout: int) -> list:
    """Best-yield engines pehle, baaki round-robin (fairness + kam block)."""
    scored = sorted(_V19_ENGINES, key=lambda e: _v21_score(e[0]), reverse=True)
    if fanout >= len(scored):
        return scored
    half = max(1, fanout // 2)
    top = scored[:half]
    rest = scored[half:]
    start = (idx * 3 + pg * 5) % max(1, len(rest))
    picks = list(top)
    for k in range(fanout - len(top)):
        picks.append(rest[(start + k) % len(rest)])
    return picks


# ────────────────────────  MAIN DEEP PARSER (v21)  ───────────────────────────
async def _v19_deep_parse(dorks: list, uid: int, progress=None) -> dict:
    cf = _v21_cfg()
    threads, pages, fanout = cf["threads"], cf["pages"], cf["fanout"]
    max_per_domain = cf["max_per_domain"]
    if 0 < max_per_domain <= 250:      # legacy default 250 bahut tight tha
        max_per_domain = 2000
    dorks = [d.strip() for d in dorks if d and d.strip()]
    total = len(dorks)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    param_path = os.path.join(_V19_OUT_DIR, "V19_Param_URLs_%s.txt" % ts)
    all_path = os.path.join(_V19_OUT_DIR, "V19_All_URLs_%s.txt" % ts)
    cdx_path = os.path.join(_V19_OUT_DIR, "V21_CDX_%s.txt" % ts)

    st = {
        "scanned": 0, "total": total, "raw": 0, "unique": 0, "filtered": 0,
        "errors": 0, "retries": 0, "param": 0, "threads": threads,
        "started": time.time(), "phase": "cdx" if (cf["use_cdx"] or cf["use_cc"]) else "serp",
        "cdx": 0, "cc": 0, "dup": 0, "mode": cf["mode"], "fanout": fanout,
        "pages": pages, "engines": len(_V19_ENGINES), "tps": 0.0, "eta": 0,
    }
    cap = 3_000_000 if _V19_HW["ram"] >= 12 else (1_200_000 if _V19_HW["ram"] >= 4 else 400_000)
    seen = set()
    sig_count = {}
    dom_count = {}
    sig_limit = cf["sig"]
    stop_ev = _V19_STOP.get(int(uid)) or asyncio.Event()
    proxies = []
    if cf["use_proxies"]:
        try:
            proxies = list(effective_proxy_pool(int(uid)) or [])
        except Exception:
            proxies = []

    sem = asyncio.Semaphore(max(_V19_MIN_THREADS, threads))
    req_sem = asyncio.Semaphore(min(max(60, threads * 3), 240 if not _V19_HW["termux"] else 120))
    _pf = open(param_path, "w", encoding="utf-8", buffering=1024 * 256)
    _af = open(all_path, "w", encoding="utf-8", buffering=1024 * 256)
    _cf = open(cdx_path, "w", encoding="utf-8", buffering=1024 * 256)

    def _commit(links: list, src: str = "") -> None:
        acc_all, acc_par, acc_cdx = [], [], []
        for u in links:
            st["raw"] += 1
            u = _v21_strip_tracking(u)
            if not _v19_clean_url(u, allow_root=False):
                st["filtered"] += 1
                continue
            key = _v21_canon(u)
            h = hash(key) & 0x7FFFFFFF
            if h in seen:
                st["filtered"] += 1
                st["dup"] += 1
                continue
            dom = _v19_strip_www(urllib_parse.urlparse(u).netloc)
            if max_per_domain and dom_count.get(dom, 0) >= max_per_domain:
                st["filtered"] += 1
                continue
            has_p = "?" in u and "=" in u
            if has_p and sig_limit:
                s = _v19_sig(u)
                if sig_count.get(s, 0) >= sig_limit:
                    st["filtered"] += 1
                    continue
                sig_count[s] = sig_count.get(s, 0) + 1
            if len(seen) >= cap:
                st["filtered"] += 1
                continue
            seen.add(h)
            dom_count[dom] = dom_count.get(dom, 0) + 1
            st["unique"] += 1
            acc_all.append(u)
            if has_p:
                st["param"] += 1
                acc_par.append(u)
                if src == "cdx":
                    acc_cdx.append(u)
        if acc_all:
            _af.write("\n".join(acc_all) + "\n")
            _af.flush()
        if acc_par:
            _pf.write("\n".join(acc_par) + "\n")
            _pf.flush()
        if acc_cdx:
            _cf.write("\n".join(acc_cdx) + "\n")
            _cf.flush()

    async def _push_progress(force: bool = False) -> None:
        if not progress:
            return
        now = time.time()
        el = max(0.001, now - st["started"])
        st["tps"] = round(st["scanned"] / el, 1)
        left = max(0, st["total"] - st["scanned"])
        st["eta"] = int(left / st["tps"]) if st["tps"] > 0 else 0
        try:
            await progress(dict(st))
        except Exception:
            pass

    connector = aiohttp.TCPConnector(limit=max(80, min(400, threads * (fanout + 2))),
                                     ssl=False, ttl_dns_cache=600, force_close=False,
                                     enable_cleanup_closed=True)
    async with aiohttp.ClientSession(connector=connector) as session:

        # ---------- PHASE 1: Wayback + Common Crawl (site: dorks) ----------
        domains = _v21_site_domains(dorks) if (cf["use_cdx"] or cf["use_cc"]) else []
        if domains and not stop_ev.is_set():
            st["phase"] = "cdx"
            await _push_progress()
            d_sem = asyncio.Semaphore(3)
            # ⏱ time budget — Wayback agar slow ho to poora run na atke
            _phase_deadline = time.time() + (120.0 if _V19_HW["termux"] else 240.0)

            async def _one_domain(dom: str):
                got = []
                if time.time() > _phase_deadline or stop_ev.is_set():
                    return
                async with d_sem:
                    if time.time() > _phase_deadline:
                        return
                    if cf["use_cdx"]:
                        got += await _v21_cdx_fetch(session, dom, cf["cdx_limit"])
                        st["cdx"] += len(got)
                    if cf["use_cc"] and not stop_ev.is_set():
                        cc = await _v21_cc_fetch(session, dom, cf["cdx_limit"])
                        st["cc"] += len(cc)
                        got += cc
                if got:
                    _commit(got, src="cdx")
                await _push_progress()

            d_tasks = [asyncio.create_task(_one_domain(d)) for d in domains]
            try:
                await asyncio.gather(*d_tasks, return_exceptions=True)
            finally:
                for t in d_tasks:
                    if not t.done():
                        t.cancel()

        # ---------- PHASE 2: SERP scan (adaptive) ----------
        st["phase"] = "serp"
        cur_fanout = fanout
        win = {"ok": 0, "bad": 0}

        async def _one_dork(idx: int, dork: str) -> None:
            nonlocal cur_fanout
            if stop_ev.is_set():
                return
            links: list = []
            async with sem:
                for pg in range(pages):
                    if stop_ev.is_set():
                        break
                    picks = _v21_pick_engines(idx, pg, cur_fanout)
                    tasks = []
                    for off, eng in enumerate(picks):
                        px = proxies[(idx + off + pg) % len(proxies)] if proxies else ""

                        async def _go(e=eng, p=px, page=pg):
                            async with req_sem:
                                return await _v19_fetch_serp(session, e, dork, page, proxy=p)

                        tasks.append(asyncio.create_task(_go()))
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for i, res in enumerate(results):
                        if isinstance(res, Exception):
                            st["errors"] += 1
                            win["bad"] += 1
                            continue
                        got, status = res
                        if status == "ok":
                            win["ok"] += 1
                            links.extend(got)
                        else:
                            st["errors"] += 1
                            st["retries"] += 1
                            win["bad"] += 1
                            if stop_ev.is_set():
                                continue
                            alt = _V21_ENGINE_ROTATE[(idx * 3 + pg * 5 + i + 11) % len(_V21_ENGINE_ROTATE)]
                            if alt[0] not in [p[0] for p in picks]:
                                async with req_sem:
                                    got2, status2 = await _v19_fetch_serp(session, alt, dork, pg, proxy="")
                                if status2 == "ok":
                                    links.extend(got2)
                                    st["retries"] = max(0, st["retries"] - 1)
                    # adaptive fanout
                    if cf["adaptive"] and (win["ok"] + win["bad"]) >= 40:
                        rate = win["bad"] / float(win["ok"] + win["bad"])
                        if rate > 0.45 and cur_fanout > 2:
                            cur_fanout -= 1
                        elif rate < 0.12 and cur_fanout < fanout:
                            cur_fanout += 1
                        win["ok"] = win["bad"] = 0
                _commit(links)
                st["scanned"] += 1

        _V21_ENGINE_ROTATE = list(_V19_ENGINES)
        tasks = [asyncio.create_task(_one_dork(i, d)) for i, d in enumerate(dorks)]
        last_push = 0.0
        try:
            while True:
                pending = [t for t in tasks if not t.done()]
                if not pending:
                    break
                await asyncio.sleep(1.0)
                now = time.time()
                if (now - last_push) >= 2.5:
                    last_push = now
                    await _push_progress()
                if stop_ev.is_set():
                    for t in pending:
                        t.cancel()
                    break
        finally:
            _pf.close()
            _af.close()
            _cf.close()
            for t in tasks:
                if not t.done():
                    t.cancel()

    st["elapsed"] = time.time() - st["started"]
    st["tps"] = round(st["scanned"] / max(0.001, st["elapsed"]), 1)
    try:
        _V21_LAST.clear()
        _V21_LAST.update(dict(st))
        _V21_LAST["engines_top"] = sorted(_V21_ENG_STATS.items(),
                                          key=lambda kv: -kv[1].get("urls", 0))[:5]
    except Exception:
        pass
    return {"stats": st, "param_path": param_path, "all_path": all_path, "cdx_path": cdx_path}


# ─────────────────────────  UI TEXT (quality view)  ──────────────────────────
def _v19_running_text(st: dict) -> str:
    total = max(1, int(st.get("total") or 1))
    scanned = int(st.get("scanned") or 0)
    pct = scanned * 100.0 / total
    el = max(0.001, time.time() - float(st.get("started") or time.time()))
    tps = st.get("tps") or (scanned / el)
    eta = st.get("eta") or (int((total - scanned) / tps) if tps > 0 else 0)
    eta_s = ("%dm %02ds" % (eta // 60, eta % 60)) if eta < 3600 else ("%dh %02dm" % (eta // 3600, (eta % 3600) // 60))
    per_dork = (st.get("unique") or 0) / float(max(1, scanned))
    phase = "🌐 Wayback/CC" if st.get("phase") == "cdx" else "🔎 SERP engines"
    return (
        "🕷️ <b>SPIDEY-X PRO — RUNNING</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>Done:</b> <code>%s/%s</code> dorks\n"
        "🔗 <b>Found:</b> <code>%s</code>\n"
        "💎 <b>Unique:</b> <code>%s</code> • 🎯 <b>param:</b> <code>%s</code>\n"
        "📈 <b>URLs/dork:</b> <code>%.1f</code>\n"
        "⚡ <b>Speed:</b> <code>%.0f dorks/s</code>\n"
        "🧵 %s threads • 🔧 %s engines • 🎛 <code>%s</code>\n"
        "🌊 <b>Phase:</b> %s\n\n"
        "<code>[%s]</code> <b>%d%%</b> • ⏳ ETA <code>%s</code>"
    ) % (
        format(scanned, ","), format(total, ","),
        format(int(st.get("raw") or 0), ","), format(int(st.get("unique") or 0), ","),
        format(int(st.get("param") or 0), ","), per_dork, tps,
        st.get("threads"), st.get("engines"), str(st.get("mode") or "").upper(), phase,
        _v19_bar(pct), int(pct), eta_s,
    )


def _v19_done_text(st: dict, elapsed: float) -> str:
    scanned = max(1, int(st.get("scanned") or 0))
    unique = int(st.get("unique") or 0)
    raw = int(st.get("raw") or 0)
    per_dork = unique / float(scanned)
    uniq_rate = (unique * 100.0 / raw) if raw else 0.0
    tps = scanned / max(0.001, float(elapsed or 0.001))
    top = _V21_LAST.get("engines_top") or sorted(_V21_ENG_STATS.items(), key=lambda kv: -kv[1].get("urls", 0))[:5]
    eng_lines = "\n".join(
        "   %s <code>%s</code>" % (n, format(d.get("urls", 0), ",")) for n, d in top if d.get("urls")
    ) or "   <i>koi engine data nahi</i>"
    grade = "🏆 A+ (competitor se behtar)" if per_dork >= 33 else (
        "✅ A (competitor level)" if per_dork >= 20 else (
            "🟡 B (chalega)" if per_dork >= 10 else "🔴 C (proxy/settings badlo)"))
    return (
        "🕷️ <b>SPIDEY-X PRO — COMPLETE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>Scanned:</b> <code>%s/%s</code> dorks\n"
        "🔗 <b>Raw URLs:</b> <code>%s</code>\n"
        "💎 <b>Unique URLs:</b> <code>%s</code>\n"
        "🎯 <b>?param= URLs:</b> <code>%s</code>\n"
        "🌐 <b>Wayback:</b> <code>%s</code> • <b>CommonCrawl:</b> <code>%s</code>\n"
        "🧹 <b>Duplicates hataye:</b> <code>%s</code>\n"
        "📈 <b>URLs/dork:</b> <code>%.1f</code> • 💯 <b>unique rate:</b> <code>%.0f%%</code>\n"
        "⚡ <b>Speed:</b> <code>%.0f dorks/s</code> • ⏱ <code>%.1fs</code>\n"
        "🎚 <b>Mode:</b> <code>%s</code> • 🧵 <code>%s</code> threads • 📄 <code>%s</code> pages\n"
        "🏅 <b>Quality:</b> %s\n\n"
        "🏆 <b>Top engines:</b>\n%s\n\n"
        "📦 <i>Files ready ⬇️</i>"
    ) % (
        format(int(st.get("scanned") or 0), ","), format(int(st.get("total") or 0), ","),
        format(raw, ","), format(unique, ","), format(int(st.get("param") or 0), ","),
        format(int(st.get("cdx") or 0), ","), format(int(st.get("cc") or 0), ","),
        format(int(st.get("dup") or 0), ","),
        per_dork, uniq_rate, tps, elapsed,
        str(st.get("mode") or "").upper(), st.get("threads"), st.get("pages"),
        grade, eng_lines,
    )


def _v19_panel_text() -> str:
    cf = _v21_cfg()
    hw = _V19_HW
    dev = "📱 Termux" if hw["termux"] else "🖥️ Server/VPS"
    return (
        "🕷️ <b>SPIDEY-X PRO</b> 🕷️\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>%d engines</b> • multi-page • auto-retry\n"
        "🌐 <b>Wayback CDX:</b> %s • <b>CommonCrawl:</b> %s\n"
        "💎 Canonical dedupe • engine scoring • adaptive speed\n\n"
        "🎚 <b>Mode:</b> <code>%s</code> (fanout %d)\n"
        "⚡ <b>Threads:</b> <code>%s</code> (min %s)\n"
        "📄 <b>Pages/engine:</b> <code>%s</code>\n"
        "🧩 <b>Sig limit:</b> <code>%s</code>\n"
        "💻 <b>Device:</b> %s • %s cores / %s GB RAM\n\n"
        "<i>Choose your weapon ⬇️</i>"
    ) % (
        len(_V19_ENGINES), "ON ✅" if cf["use_cdx"] else "OFF ❌",
        "ON ✅" if cf["use_cc"] else "OFF ❌",
        cf["mode"].upper(), cf["fanout"], cf["threads"], _V19_MIN_THREADS,
        cf["pages"], cf["sig"], dev, hw["cores"], hw["ram"],
    )


def _v19_cfg_kb():
    cf = _v21_cfg()
    mode_row = [
        InlineKeyboardButton(("✅ " if cf["mode"] == "fast" else "") + "🚀 Fast", callback_data="v21_mode_fast"),
        InlineKeyboardButton(("✅ " if cf["mode"] == "balanced" else "") + "⚖️ Balanced", callback_data="v21_mode_balanced"),
    ]
    mode_row2 = [
        InlineKeyboardButton(("✅ " if cf["mode"] == "deep" else "") + "🌊 Deep", callback_data="v21_mode_deep"),
        InlineKeyboardButton(("✅ " if cf["mode"] == "max" else "") + "🔥 Max", callback_data="v21_mode_max"),
    ]
    return InlineKeyboardMarkup([
        mode_row, mode_row2,
        [InlineKeyboardButton("🟢 Lite 24", callback_data="v19_thr_24"),
         InlineKeyboardButton("🟡 40", callback_data="v19_thr_40"),
         InlineKeyboardButton("🟠 60", callback_data="v19_thr_60")],
        [InlineKeyboardButton("🔵 100", callback_data="v19_thr_100"),
         InlineKeyboardButton("🔥 160", callback_data="v19_thr_160"),
         InlineKeyboardButton("⚡ Auto", callback_data="v19_thr_0")],
        [InlineKeyboardButton("📄 Pages: 1", callback_data="v19_pg_1"),
         InlineKeyboardButton("📄 Pages: 2", callback_data="v19_pg_2"),
         InlineKeyboardButton("📄 Pages: 3", callback_data="v19_pg_3")],
        [InlineKeyboardButton(("🌐 Wayback: ON" if cf["use_cdx"] else "🌐 Wayback: OFF"), callback_data="v21_cdx_toggle"),
         InlineKeyboardButton(("🧠 CC: ON" if cf["use_cc"] else "🧠 CC: OFF"), callback_data="v21_cc_toggle")],
        [InlineKeyboardButton("🎯 Sig limit: %s" % (cf["sig"] or "off"), callback_data="v21_sig_cycle")],
        [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="menu_v19")],
    ])


def _v19_panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Kᴇʏᴡᴏʀᴅ Mᴀᴋᴇʀ", callback_data="v19_kw"),
         InlineKeyboardButton("🎯 Dᴏʀᴋ Gᴇɴᴇʀᴀᴛᴏʀ", callback_data="v19_dork")],
        [InlineKeyboardButton("🌍 Dᴇᴇᴘ Pᴀʀsᴇʀ ⚡", callback_data="v19_parse")],
        [InlineKeyboardButton("🛡️ Sǫʟɪ Cʜᴇᴄᴋᴇʀ", callback_data="v19_sqli")],
        [InlineKeyboardButton("⚙️ Eɴɢɪɴᴇ Sᴇᴛᴛɪɴɢs", callback_data="v19_cfg")],
        [InlineKeyboardButton("⬅️ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", callback_data="menu_back")],
    ])


# ───────────────────  v21 CALLBACKS + ROUTER OVERRIDE  ───────────────────────
async def _v21_handle(update, context, data: str) -> int:
    q = update.callback_query
    if data.startswith("v21_mode_"):
        mode = data.split("v21_mode_", 1)[1]
        if mode in _V21_PRESETS:
            _v19_save_cfg({"mode": mode})
        cf = _v21_cfg()
        try:
            await q.edit_message_text(
                ("🎚 <b>MODE: %s</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                 "🔧 Engines/dork: <code>%d</code>\n📄 Pages: <code>%d</code>\n"
                 "🎯 Sig limit: <code>%d</code>\n⚡ Threads: <code>%s</code>\n\n"
                 "<i>Saved ✅ — ab parser is mode pe chalega</i>")
                % (cf["mode"].upper(), cf["fanout"], cf["pages"], cf["sig"], cf["threads"]),
                reply_markup=_v19_cfg_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    if data == "v21_cdx_toggle":
        cur = bool(_v19_load_cfg().get("use_cdx", True))
        _v19_save_cfg({"use_cdx": not cur})
        await q.answer("Wayback %s" % ("OFF" if cur else "ON"))
        try:
            await q.edit_message_text(_v19_panel_text(), reply_markup=_v19_panel_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    if data == "v21_cc_toggle":
        cur = bool(_v19_load_cfg().get("use_cc", True))
        _v19_save_cfg({"use_cc": not cur})
        await q.answer("CommonCrawl %s" % ("OFF" if cur else "ON"))
        try:
            await q.edit_message_text(_v19_panel_text(), reply_markup=_v19_panel_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    if data == "v21_sig_cycle":
        cf = _v21_cfg()
        order = [8, 14, 20, 30, 0]
        try:
            nxt = order[(order.index(cf["sig"]) + 1) % len(order)]
        except Exception:
            nxt = 14
        _v19_save_cfg({"sig_limit": nxt})
        await q.answer("Sig limit: %s" % (nxt or "off"))
        try:
            await q.edit_message_text(_v19_panel_text(), reply_markup=_v19_panel_kb(), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return MENU
    return MENU


_v21_prev_router = _v19_callback_router


async def _v19_callback_router(update, context, data: str) -> int:
    if data.startswith("v21_"):
        try:
            await update.callback_query.answer()
        except Exception:
            pass
        try:
            return await _v21_handle(update, context, data)
        except Exception as exc:
            logger.warning("v21 callback error: %s", exc)
            return MENU
    return await _v21_prev_router(update, context, data)


# ────────────────────────────  /stats + /bench  ──────────────────────────────
async def _v21_stats_cmd(update, context) -> None:
    msg = update.effective_message
    uid = update.effective_user.id
    if not has_access(uid):
        await msg.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return
    cf = _v21_cfg()
    rows = sorted(_V21_ENG_STATS.items(), key=lambda kv: -kv[1].get("urls", 0))
    lines = []
    for n, d in rows[:12]:
        ok = d.get("ok", 0)
        urls = d.get("urls", 0)
        per = (urls / float(ok)) if ok else 0.0
        lines.append("   %-10s <code>%6s</code> URLs • <code>%.1f</code>/call • 🚫%d" %
                     (n[:10], format(urls, ","), per, d.get("blocked", 0) + d.get("err", 0)))
    body = "\n".join(lines) or "   <i>abhi koi data nahi — pehle parser chalao</i>"
    last = _V21_LAST or {}
    last_txt = ""
    if last:
        last_txt = ("\n🏁 <b>Last run:</b> <code>%s</code> dorks → <code>%s</code> unique "
                    "(<code>%.1f</code>/dork, <code>%.0f</code> dorks/s)") % (
            format(int(last.get("scanned") or 0), ","), format(int(last.get("unique") or 0), ","),
            (last.get("unique") or 0) / float(max(1, last.get("scanned") or 1)), last.get("tps") or 0)
    await msg.reply_text(
        ("📊 <b>SPIDEY-X PRO — STATS</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
         "🎚 Mode: <code>%s</code> • 🔧 Engines: <code>%d</code>\n"
         "🧵 Threads: <code>%s</code> • 📄 Pages: <code>%d</code> • 🎯 Sig: <code>%s</code>\n"
         "🌐 Wayback: %s • CC: %s\n%s\n\n"
         "🏆 <b>Engine leaderboard</b> (URLs mili):\n%s") % (
            cf["mode"].upper(), len(_V19_ENGINES), cf["threads"], cf["pages"], cf["sig"],
            "ON" if cf["use_cdx"] else "OFF", "ON" if cf["use_cc"] else "OFF", last_txt, body),
        parse_mode=ParseMode.HTML)


async def _v21_bench_cmd(update, context) -> None:
    msg = update.effective_message
    uid = update.effective_user.id
    if not has_access(uid):
        await msg.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return
    note = await msg.reply_text("⏱ <b>BENCH</b> — 6 dorks, fast mode...", parse_mode=ParseMode.HTML)
    dorks = [
        "inurl:product.php?id= shop",
        "inurl:product.php?id= store",
        "inurl:item.php?id= buy",
        "inurl:details.php?id= cart",
        "inurl:cart.php?id= checkout",
        "inurl:page.php?id= order",
    ]
    old_mode = _v19_load_cfg().get("mode", "balanced")
    _V19_STOP[int(uid)] = asyncio.Event()
    try:
        _v19_save_cfg({"mode": "fast"})
        res = await _v19_deep_parse(dorks, uid)
    except Exception as exc:
        await note.edit_text("❌ Bench fail: <code>%s</code>" % str(exc)[:200], parse_mode=ParseMode.HTML)
        return
    finally:
        _v19_save_cfg({"mode": old_mode})
        _V19_STOP.pop(int(uid), None)
    st = res["stats"]
    scanned = max(1, int(st.get("scanned") or 0))
    per = (st.get("unique") or 0) / float(scanned)
    tps = st.get("tps") or 0
    probe = "🏆 A+" if per >= 33 else ("✅ A" if per >= 20 else ("🟡 B" if per >= 10 else "🔴 C"))
    est_50k = int(50000 / tps) if tps else 0
    try:
        await note.edit_text(
            ("⏱ <b>BENCH RESULT</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
             "📥 Dorks: <code>%d</code> • ⏱ <code>%.1fs</code>\n"
             "🔗 Raw: <code>%s</code> • 💎 Unique: <code>%s</code> • 🎯 param: <code>%s</code>\n"
             "📈 <b>URLs/dork:</b> <code>%.1f</code> → %s\n"
             "⚡ <b>Speed:</b> <code>%.1f dorks/s</code>\n"
             "🕒 50,000 dorks ka estimate: <code>%s</code>\n\n"
             "<i>Ye asli engines pe measured hai. Slow lage to mode badlo ya proxy daalo.</i>")
            % (int(st.get("scanned") or 0), st.get("elapsed") or 0,
               format(int(st.get("raw") or 0), ","), format(int(st.get("unique") or 0), ","),
               format(int(st.get("param") or 0), ","), per, probe, tps,
               ("%dh %02dm" % (est_50k // 3600, (est_50k % 3600) // 60)) if est_50k else "n/a"),
            parse_mode=ParseMode.HTML)
    except Exception:
        pass
    for p in (res.get("param_path"), res.get("all_path"), res.get("cdx_path")):
        try:
            if p and os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass


async def _v21_domainer_cmd(update, context) -> None:
    """/domainer site1.com, site2.com  -> Wayback + CommonCrawl bulk param URLs."""
    msg = update.effective_message
    uid = update.effective_user.id
    if not has_access(uid):
        await msg.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return
    raw = " ".join(context.args or []) if getattr(context, "args", None) else ""
    doms = [d.strip().lower().replace("https://", "").replace("http://", "").strip("/")
            for d in re.split(r"[,\s]+", raw or "") if d.strip()]
    doms = [d for d in doms if re.match(r"^[a-z0-9.\-]+\.[a-z]{2,}$", d)]
    if not doms:
        await msg.reply_text(
            "🌐 <b>DOMAIN MINER</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Usage: <code>/domainer site1.com, site2.com</code>\n\n"
            "Ye Wayback Machine + Common Crawl se us domain ke\n"
            "<b>saare purane ?param= URLs</b> nikal deta hai — lakho URLs, seconds me.\n\n"
            "👉 Example: <code>/domainer shopify.com, mystore.com</code>",
            parse_mode=ParseMode.HTML)
        return
    doms = doms[:20]
    cf = _v21_cfg()
    note = await msg.reply_text("🌐 <b>Domain Mining...</b>\n%d domains • Wayback + CC" % len(doms),
                                parse_mode=ParseMode.HTML)
    seen, param_urls = set(), []
    connector = aiohttp.TCPConnector(limit=12, ssl=False, ttl_dns_cache=600)
    async with aiohttp.ClientSession(connector=connector) as session:
        for d in doms:
            got = []
            if cf["use_cdx"]:
                got += await _v21_cdx_fetch(session, d, cf["cdx_limit"])
            if cf["use_cc"]:
                got += await _v21_cc_fetch(session, d, cf["cdx_limit"])
            for u in got:
                u = _v21_strip_tracking(u)
                if not _v19_clean_url(u, allow_root=False):
                    continue
                if "?" not in u or "=" not in u:
                    continue
                k = _v21_canon(u)
                if k in seen:
                    continue
                seen.add(k)
                param_urls.append(u)
            try:
                await note.edit_text(
                    "🌐 <b>Domain Mining...</b>\n✅ %s\n🎯 <code>%s</code> param URLs"
                    % (d, format(len(param_urls), ",")), parse_mode=ParseMode.HTML)
            except Exception:
                pass
    if not param_urls:
        await note.edit_text(
            "🌐 <b>Domain Miner</b>\n❌ Kuch nahi mila.\n\n"
            "Possible reasons: domain galat, Wayback pe archive nahi, ya internet issue.",
            parse_mode=ParseMode.HTML)
        return
    path = os.path.join(_V19_OUT_DIR, "V21_Domain_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(param_urls) + "\n")
    await note.edit_text(
        "🌐 <b>DOMAIN MINER — DONE</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Domains: <code>%d</code>\n🎯 <b>Param URLs:</b> <code>%s</code>\n\n"
        "<i>Ab isse SQLi Checker me daal do 🛡️</i>" % (len(doms), format(len(param_urls), ",")),
        parse_mode=ParseMode.HTML)
    try:
        with open(path, "rb") as fh:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=fh,
                                            filename=os.path.basename(path),
                                            caption="🌐 %s param URLs" % format(len(param_urls), ","))
    except Exception:
        pass


logger.info("🕷️ SPIDEY-X PRO (v21) loaded — %d engines • Wayback+CC • adaptive • quality metrics",
            len(_V19_ENGINES))
# ═══ SPIDEY-X PRO (v21) END ═══
'''

CMD_ANCHOR = '    app.add_handler(CommandHandler("ping", _v20_ping_cmd), group=-1)'
CMD_ADD = CMD_ANCHOR + '''
    app.add_handler(CommandHandler(["stats", "engine_stats"], _v21_stats_cmd), group=-1)
    app.add_handler(CommandHandler("bench", _v21_bench_cmd), group=-1)
    app.add_handler(CommandHandler(["domainer", "miner"], _v21_domainer_cmd), group=-1)'''


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    if "_V19_TAG" not in src:
        raise SystemExit("❌ Pehle V19 patch apply karo.")
    if "_V20_TAG" not in src:
        raise SystemExit("❌ Pehle v20 (SPIDEY-X) patch apply karo.")

    # idempotent: purana v21 block hatao
    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)
    src = src.replace(CMD_ADD, CMD_ANCHOR)

    # commands
    if CMD_ANCHOR not in src:
        raise SystemExit("❌ /ping anchor nahi mila — v20 applied hai?")
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)

    # ---- FIX: group -1 guard (filters.ALL) blocks ALL other group -1 handlers ----
    # `MessageHandler(filters.ALL, _v12_pre_router_guard)` group -1 me tha aur PTB
    # ek group me sirf PEHLA matching handler chalata hai -> /myid /adminid /ping
    # /v19 /stats jaise saare group -1 commands dead the. Guard ko -2 me bheja.
    guard_fixed = 0
    for old_g, new_g in (
        ("app.add_handler(MessageHandler(filters.ALL, _v12_pre_router_guard), group=-1)",
         "app.add_handler(MessageHandler(filters.ALL, _v12_pre_router_guard), group=-2)"),
        ("app.add_handler(CallbackQueryHandler(_v12_pre_router_guard), group=-1)",
         "app.add_handler(CallbackQueryHandler(_v12_pre_router_guard), group=-2)"),
    ):
        if old_g in src:
            src = src.replace(old_g, new_g, 1)
            guard_fixed += 1

    # insert block before __main__
    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila.")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v21_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)
    try:
        os.remove(backup)
    except Exception:
        pass

    print("=" * 74)
    print("  ✅ SPIDEY-X PRO (v21) APPLIED")
    print("=" * 74)
    print("  Target : %s" % target)
    print("  Engines: 16 -> 21 (Yep, Stract, SearX x3, Wiby)")
    print("  Volume : Wayback CDX + Common Crawl (lakeh URLs)")
    print("  Quality: canonical dedupe, sig 14-20, mode presets, engine scoring")
    print("  Speed  : adaptive fanout, req throttle, live dorks/sec + ETA")
    print("  New    : /domainer  /bench  /stats  + mode buttons in settings")
    print("  FIX    : group -1 guard moved to -2 -> /myid /adminid /ping /v19 ab chalenge (%d)" % guard_fixed)
    print("=" * 74)


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
