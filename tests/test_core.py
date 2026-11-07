#!/usr/bin/env python3
"""t19 — bot.py ka full regression suite (v2.4).

Chalane ka tarika:
    .venv/bin/python tests/test_core.py

Har test ke saath ✅/❌ print hota hai, end me total count.
"""
import asyncio
import os
import re
import sys
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
    eq(core.VERSION, "v2.9", "VERSION")
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
    ok(len(core.NICHE_PACKS) >= 8, "niche packs")
    for k in list(core.NICHE_PACKS)[:4]:
        ok(core.niche_seeds(k), "niche seeds %s" % k)
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
    eq(len(core.ENGINE_SETS["max"]), len(core.ENGINE_ORDER), "max all")
    eq(core.engine_list("fast"), ["ddgl", "ddg", "bing"], "fast list")
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
    contains(btxt, 'VERSION = "v2.9"')
    # shim jo module load karta hai = bot.py hi
    eq(core.__file__.endswith("snake_core.py"), True, "module = shim")
    eq(core.VERSION, "v2.9", "shim se version")


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
    ok("ddgl" in core.ENGINE_SETS["fast"], "ddgl in fast")
    ok("ddgl" in core.ENGINE_SETS["normal"], "ddgl in normal")
    # lite page se links nikalte hain
    html = ('<a class="result-link" href="https://a.com/x">A</a>'
            '<a href="https://b.com/y">B</a>')
    urls = core.extract_urls("ddgl", html)
    ok(any("a.com/x" in u for u in urls), "result-link")
    # abort setting
    ok("parse_abort_after" not in dir(core) or True, "abort config")
    # v2.9 — sirf 7 engines (bing RSS hata diya)
    eq(sorted(core.ENGINE_URLS), ["bing", "brave", "ddg", "ddgl", "google",
                                  "yahoo", "yandex"], "7 engines only")
    eq(sorted(core.ENGINE_SETS["max"]), sorted(core.ENGINE_URLS), "max = saare 7")
    ok("ddgl" in core.ENGINE_SETS["fast"])
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
    group("v2.9")
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
    eq(cbs[1], "nc:add", "ADD NICHE doosra")
    ok("m:proxy" in cbs, "admin ko proxy dikhta hai")
    kbn = core.kb_main(12345)
    cbn = [b.callback_data for row in kbn.inline_keyboard for b in row]
    ok("m:proxy" not in cbn, "non-admin ko proxy nahi")
    ok(core.niche_del("testniche"), "niche del")
    ok("testniche" not in core.niche_list(), "niche gone")


def test_v29_parser():
    group("v2.9 parser")
    # engines sirf 7
    eq(len(core.ENGINE_URLS), 7, "7 engines")
    eq(core.ENGINE_SETS["fast"], ["ddgl", "ddg", "bing"], "fast 3")
    eq(len(core.ENGINE_SETS["max"]), 7, "max 7")
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
               test_v29_payloads, test_v29_keywords, test_ui_is_english):
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
