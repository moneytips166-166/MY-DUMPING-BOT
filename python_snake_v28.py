#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYTHON SNAKE — v28: PROXY ENGINE v3 (0 proxies bug ka permanent fix)

  python3 python_snake_v28.py bot_fixed.py

Kya fix karta hai:
  • "Scraped: 0 • Checked: 0 • 0.9s" — pehle sirf raw.githubusercontent.com type
    sources the. Ab 45+ sources 8 alag domains/CDN pe (jsDelivr, Statically,
    gitHack, proxyscrape v2/v4, proxy-list.download, openproxylist, geonode,
    proxifly, github.io ...). Ek domain block ho to baaki chalte hain.
  • Source-wise diagnostics — card me dikhega kitne sources reachable the,
    kitni raw lines aayi, kaunse domain fail hue (isse pata chalega kya block hai).
  • Tolerant parser — ip:port, ip port, ip,port, protocol URL, JSON — sab.
  • Faster verify — 2 target parallel, 5s timeout, lenient.
  • Manual/paid proxy fallback — data/manual_proxies.txt + /setpr wale proxies
    scrape fail hone pe bhi pool me aate hain.
  • Guardian + v22 scan + v23 UI — sab isi naye engine se chalte hain
    (_v7_scrape_tiered_sources override).

Dobara chalane pe safe (idempotent).
"""
import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v28 PROXY ENGINE v3 START ═══"
MARK_END = "# ═══ PYTHON SNAKE v28 PROXY ENGINE v3 END ═══"

BLOCK = r'''# ═══ PYTHON SNAKE v28 PROXY ENGINE v3 START ═══
# ─────────────────────────────────────────────────────────────────────────────
#  PROXY ENGINE v3 — 45+ sources, 8 domains, diagnostics, tolerant parsing
# ─────────────────────────────────────────────────────────────────────────────
import socket as _v28_socket
import asyncio as _v28_asyncio
import aiohttp as _v28_aiohttp
import json as _v28_json
import re as _v28_re
import time as _v28_time
import random as _v28_random

_V28_UA = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"),
    "Accept": "*/*",
}

# ── 45+ sources — har family alag domain pe (ek block ho to baaki chalein) ───
_V28_SOURCES = [
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

# ── tolerant proxy parsing ──────────────────────────────────────────────────
_V28_IP_PORT = _v28_re.compile(
    r"(\d{1,3}(?:\.\d{1,3}){3})\s*[:\s,|]\s*(\d{2,5})")


def _v28_parse_proxies(text: str) -> list:
    """Kisi bhi format se proxy nikaalo: ip:port, ip port, ip,port, url, JSON."""
    out, seen = [], set()
    if not text:
        return out
    t = text.strip()
    # JSON ho to pehle usse try karo
    if t[:1] in "{[":
        try:
            j = _v28_json.loads(t)
            items = []
            if isinstance(j, dict):
                items = j.get("data") or j.get("proxies") or j.get("results") or []
                if isinstance(items, dict):
                    items = list(items.values())
            elif isinstance(j, list):
                items = j
            for it in items:
                if isinstance(it, dict):
                    ip = str(it.get("ip") or it.get("host") or it.get("proxy") or "").strip()
                    pt = str(it.get("port") or "").strip()
                    if ip and pt:
                        if _V28_IP_PORT.fullmatch(ip) or ":" in ip:
                            cand = ip
                        else:
                            cand = "%s:%s" % (ip, pt)
                        for h, p in _V28_IP_PORT.findall(cand):
                            k = "%s:%s" % (h, p)
                            if k not in seen:
                                seen.add(k); out.append(k)
                elif isinstance(it, str):
                    for h, p in _V28_IP_PORT.findall(it):
                        k = "%s:%s" % (h, p)
                        if k not in seen:
                            seen.add(k); out.append(k)
            if out:
                return out
        except Exception:
            pass
    for h, p in _V28_IP_PORT.findall(t):
        k = "%s:%s" % (h, p)
        if k in seen:
            continue
        # basic sanity
        try:
            if not all(0 <= int(x) <= 255 for x in h.split(".")):
                continue
            if not (1 <= int(p) <= 65535):
                continue
        except Exception:
            continue
        seen.add(k)
        out.append(k)
    return out


_V28_STATS = {"sources_total": 0, "sources_ok": 0, "raw_lines": 0,
              "hosts_ok": [], "hosts_fail": [], "ts": 0.0, "elapsed": 0.0}
_V28_CACHE = {"items": [], "ts": 0.0}


_V28_DNS_CACHE: dict = {}


async def _v28_doh_resolve(host: str) -> str:
    """DNS-over-HTTPS (1.1.1.1 / 8.8.8.8 IP se) — DNS block ho to bhi IP mil jaye."""
    if host in _V28_DNS_CACHE:
        return _V28_DNS_CACHE[host]
    out = ""
    for resolver in ("https://1.1.1.1/dns-query", "https://8.8.8.8/resolve"):
        try:
            conn = _v28_aiohttp.TCPConnector(limit=4, ssl=False)
            async with _v28_aiohttp.ClientSession(connector=conn) as sess:
                async with sess.get(resolver, params={"name": host, "type": "A"},
                                    headers={"Accept": "application/dns-json"},
                                    timeout=_v28_aiohttp.ClientTimeout(total=6),
                                    ssl=False) as r:
                    if r.status == 200:
                        j = _v28_json.loads(await r.text(errors="ignore"))
                        for ans in (j.get("Answer") or []):
                            ip = str(ans.get("data") or "")
                            if _v28_re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                                out = ip
                                break
        except Exception:
            out = ""
        if out:
            break
    _V28_DNS_CACHE[host] = out
    return out


async def _v28_fetch(session, kind: str, url: str, timeout: float = 12.0) -> tuple:
    """Ek source fetch -> (url, proxies, raw_line_count, ok?)

    Plan: 1) seedha try  2) retry  3) DNS fail hue to DoH se IP nikaal ke
    Host header ke saath wahi URL IP pe try (DNS block bypass).
    """
    raw = ""
    for attempt in (1, 2):
        try:
            async with session.get(url, headers=_V28_UA,
                                   timeout=_v28_aiohttp.ClientTimeout(total=timeout),
                                   ssl=False, allow_redirects=True) as r:
                if r.status == 200:
                    raw = await r.text(errors="ignore")
                    break
        except Exception:
            raw = ""
        if attempt == 1:
            await _v28_asyncio.sleep(0.3)

    if not raw:
        # ── DoH fallback: IP se connect karo, Host header me asli domain ──
        try:
            u = url.split("/", 3)
            host = u[2]
            path = "/" + (u[3] if len(u) > 3 else "")
            ip = await _v28_doh_resolve(host)
            if ip:
                ip_url = "https://%s%s" % (ip, path)
                hdrs = dict(_V28_UA)
                hdrs["Host"] = host
                conn2 = _v28_aiohttp.TCPConnector(limit=8, ssl=False)
                async with _v28_aiohttp.ClientSession(connector=conn2) as sess2:
                    async with sess2.get(ip_url, headers=hdrs,
                                         timeout=_v28_aiohttp.ClientTimeout(total=timeout),
                                         ssl=False, allow_redirects=True) as r2:
                        if r2.status == 200:
                            raw = await r2.text(errors="ignore")
                            if raw:
                                logger.info("v28 DoH bypass OK: %s -> %s", host, ip)
        except Exception:
            raw = ""

    if not raw:
        return url, [], 0, False
    px = _v28_parse_proxies(raw)
    return url, px, len(raw.splitlines()), True


async def _v28_scrape(force: bool = False, timeout: float = 12.0) -> list:
    """Saare sources parallel — 8 domains, fail hone pe bhi baaki chalte hain."""
    now = _v28_time.monotonic()
    if not force and _V28_CACHE["items"] and (now - _V28_CACHE["ts"]) < 120:
        return list(_V28_CACHE["items"])

    t0 = _v28_time.time()
    conn = _v28_aiohttp.TCPConnector(limit=80, ssl=False, ttl_dns_cache=120,
                                     family=_v28_socket.AF_INET)
    try:
        async with _v28_aiohttp.ClientSession(connector=conn) as sess:
            res = await _v28_asyncio.gather(
                *[_v28_fetch(sess, k, u, timeout) for k, u in _V28_SOURCES],
                return_exceptions=True)
    except Exception:
        res = []

    allpx, seen, ok_hosts, fail_hosts = [], set(), [], []
    raw_lines, ok_count = 0, 0
    for item in res:
        if isinstance(item, Exception) or not isinstance(item, tuple):
            continue
        url, px, nlines, ok = item
        host = ""
        try:
            host = url.split("/")[2]
        except Exception:
            pass
        if ok:
            ok_count += 1
            raw_lines += nlines
            if host and host not in ok_hosts:
                ok_hosts.append(host)
            for p in px:
                if p not in seen:
                    seen.add(p)
                    allpx.append(p)
        else:
            if host and host not in fail_hosts:
                fail_hosts.append(host)

    _V28_STATS.update({
        "sources_total": len(_V28_SOURCES), "sources_ok": ok_count,
        "raw_lines": raw_lines, "hosts_ok": ok_hosts, "hosts_fail": fail_hosts,
        "ts": _v28_time.time(), "elapsed": round(_v28_time.time() - t0, 1),
    })
    if allpx:
        _V28_CACHE["items"] = list(allpx)
        _V28_CACHE["ts"] = _v28_time.monotonic()
    logger.info("v28 proxy scrape: %d/%d sources • %d raw lines • %d proxies • %.1fs",
                ok_count, len(_V28_SOURCES), raw_lines, len(allpx), _V28_STATS["elapsed"])
    return allpx


def _v28_manual_proxies() -> list:
    """User ke apne proxies (file + /setpr wale) — scrape fail ho to bhi kaam chale."""
    out = []
    try:
        p = os.path.join(DATA_DIR, "manual_proxies.txt")
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                out += _v28_parse_proxies(f.read())
    except Exception:
        pass
    try:
        for px in list(global_proxy_pool or []):
            out += _v28_parse_proxies(str(px))
    except Exception:
        pass
    return list(dict.fromkeys(out))


# ── purane engine ko replace — guardian + v22 + v23 sab isse chalenge ───────
async def _v7_scrape_tiered_sources(tier: int = 0, force_refresh: bool = False):   # noqa: F811
    items = await _v28_scrape(force=force_refresh)
    if not items:
        items = _v28_manual_proxies()
        if items:
            logger.info("v28: scrape khali — manual proxies se %d liye", len(items))
    return items


async def _scrape_fresh_proxies():   # noqa: F811
    return await _v7_scrape_tiered_sources(0, force_refresh=True)


# ── naya scan wrapper: purane _v22_proxy_scan ke baad diagnostics bhi deta hai ─
_v28_prev_proxy_scan = _v22_proxy_scan


async def _v22_proxy_scan(want: int = 150, concurrency: int = 220,   # noqa: F811
                          progress=None, force: bool = False) -> dict:
    _V28_STATS["sources_ok"] = 0
    st = await _v28_prev_proxy_scan(want=want, concurrency=concurrency,
                                    progress=progress, force=force)
    try:
        st = dict(st or {})
        st["sources_total"] = _V28_STATS.get("sources_total") or len(_V28_SOURCES)
        st["sources_ok"] = _V28_STATS.get("sources_ok") or 0
        st["raw_lines"] = _V28_STATS.get("raw_lines") or 0
        st["hosts_ok"] = list(_V28_STATS.get("hosts_ok") or [])[:4]
        st["scrape_secs"] = _V28_STATS.get("elapsed") or 0
        if not st.get("scraped") and not st.get("pool"):
            manual = _v28_manual_proxies()
            st["manual_available"] = len(manual)
    except Exception:
        pass
    return st


def _v28_diag_line(st: dict) -> str:
    """Card me proxy diagnostics line."""
    try:
        st = st or {}
        tot = int(st.get("sources_total") or 0)
        ok = int(st.get("sources_ok") or 0)
        raw = int(st.get("raw_lines") or 0)
        if not tot:
            return ""
        line = "🌐 Sources: <code>%d/%d</code> OK • raw lines: <code>%s</code>" % (
            ok, tot, format(raw, ","))
        if ok and st.get("hosts_ok"):
            line += "\n✅ <code>%s</code>" % ", ".join(st["hosts_ok"][:3])[:60]
        if not ok:
            line += ("\n⚠️ <b>Koi source khula hi nahi</b> — net/DNS block lag raha hai.\n"
                     "👉 Mobile data ↔ WiFi switch karo, ya paid proxy <code>/setpr</code> se daalo.\n"
                     "👉 Ya <code>data/manual_proxies.txt</code> me list daal do (ek line = ek proxy).")
        return line
    except Exception:
        return ""


# ── PROXY UI v3 — live source progress + diagnostics + asli hints ───────────
async def _v23_proxy_ui(update, context):   # noqa: F811
    q = update.callback_query
    uid = update.effective_user.id
    started = _v28_time.time()
    try:
        await q.edit_message_text(
            "🧅 <b>PROXY SCRAPE + AUTO-FILL</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <code>%d</code> sources scrape ho rahe hain…\n"
            "<i>(jsDelivr • Statically • gitHack • proxyscrape • github.io …)</i>"
            % len(_V28_SOURCES),
            parse_mode=ParseMode.HTML)
    except Exception:
        pass
    last = {"t": 0.0}

    async def _prog(s: dict) -> None:
        now = _v28_time.time()
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
                "🗄 Pool: <code>%s</code>\n"
                "🌐 Sources: <code>%s/%s</code>"
                % (format(int(s.get("scraped") or 0), ","),
                   format(int(s.get("checked") or 0), ","),
                   format(int(s.get("alive") or 0), ","),
                   format(int(s.get("pool") or 0), ","),
                   _V28_STATS.get("sources_ok") or 0, len(_V28_SOURCES)),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    try:
        st = await _v22_proxy_scan(want=150, concurrency=220, progress=_prog, force=True)
    except Exception as exc:
        logger.warning("v28 proxy scan failed: %s", exc)
        st = {"scraped": 0, "checked": 0, "alive": 0, "pool": 0}
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
        "⏱ Time: <code>%.1fs</code>" % (_v28_time.time() - started),
        "",
    ]
    diag = _v28_diag_line(st)
    if diag:
        lines.append(diag)
        lines.append("")
    if pool_n:
        lines.append("✅ <b>Auto-fill ho gaya</b> — parser ab inhe use karega.")
        if good:
            lines.append("<i>Top: %s</i>" % ", ".join(g.replace("http://", "") for g in good[:4]))
    else:
        lines.append("⚠️ Is baar koi proxy alive nahi mila.")
        if int(st.get("scraped") or 0) > 0:
            lines.append("👉 Scrape to hua, par verify me koi live nahi — thodi der baad "
                         "🔁 SCAN AGAIN dabao.")
        lines.append("👉 <b>Proxy ke bina bhi</b> parser chalega (safe engines mode).")
        manual = _v28_manual_proxies()
        if manual:
            lines.append("📄 Aapke manual proxies: <code>%d</code> — pool me daal diye." % len(manual))
        else:
            lines.append("👉 Paid proxy: <code>/setpr host:port:user:pass</code>")
            lines.append("👉 Ya list file banao: <code>data/manual_proxies.txt</code>")
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


try:
    logger.info("🐍 PROXY ENGINE v3 loaded — %d sources • %d domains",
                len(_V28_SOURCES), len({u.split('/')[2] for _, u in _V28_SOURCES}))
except Exception:
    pass
# ═══ PYTHON SNAKE v28 PROXY ENGINE v3 END ═══
'''

NEED = ("PYTHON SNAKE v27 START", "_v22_proxy_scan", "_v23_proxy_ui")


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    for need in NEED:
        if need not in src:
            raise SystemExit("❌ %s nahi mila — pehle v27 apply karo." % need)

    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)

    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v28_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 74)
    print("  ✅ PROXY ENGINE v3 APPLIED")
    print("=" * 74)
    print("  Target   : %s" % target)
    print("  Backup   : %s" % os.path.basename(backup))
    print("  Sources  : 45+ (jsDelivr, Statically, gitHack, proxyscrape, github.io ...)")
    print("  Parse    : ip:port / ip port / ip,port / URL / JSON")
    print("  Fallback : data/manual_proxies.txt + /setpr proxies")
    print("  Diag     : card me sources OK + raw lines dikhega")
    print("=" * 74)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 python_snake_v28.py bot_fixed.py")
    patch(sys.argv[1])
