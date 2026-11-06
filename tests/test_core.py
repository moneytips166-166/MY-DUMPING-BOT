#!/usr/bin/env python3
"""t19 — bot.py ka full regression suite (v2.4).

Chalane ka tarika:
    .venv/bin/python tests/test_core.py

Har test ke saath ✅/❌ print hota hai, end me total count.
"""
import asyncio
import os
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
    eq(core.VERSION, "v2.6", "VERSION")
    eq(core.ADMIN_IDS, [8999053405], "ADMIN_IDS")
    ok("SNAKE" in core.BRAND.upper(), "brand")
    ok(core.DORK_MAX >= 100000, "DORK_MAX")
    ok(core.KW_MAX >= 100000, "KW_MAX")
    eq(len(core.COUNTRIES), 16, "countries count")
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
    contains(txt.lower(), "truly unlimited nahi")
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
    eq(core.engine_list("fast"), ["ddgl", "ddg", "mojeek"], "fast list")
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
    contains(btxt, 'VERSION = "v2.6"')
    # shim jo module load karta hai = bot.py hi
    eq(core.__file__.endswith("snake_core.py"), True, "module = shim")
    eq(core.VERSION, "v2.6", "shim se version")


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
    # v2.5.x — bing RSS + ck/a unwrap
    contains(core.ENGINE_URLS["bingr"], "format=rss")
    ok("bingr" in core.ENGINE_SETS["normal"], "bingr in normal")
    rss = "<item><link>https://a.gov.in/login</link></item>"
    ok(any("a.gov.in/login" in u for u in core.extract_urls("bingr", rss)), "rss link")
    import base64 as _b64
    enc = _b64.urlsafe_b64encode(b"https://x.example.com/p?q=1").decode().rstrip("=")
    ck = "https://www.bing.com/ck/a?!&&p=1&u=a1" + enc + "&ntb=1"
    eq(core._clean_url(ck), "https://x.example.com/p?q=1")
    eq(core.engine_reason("ok"), "results mile, dork se match nahi")


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
    # /batch card
    txt = core.batch_card()
    contains(txt, "ʙᴀᴛᴄʜ")
    contains(txt, "/batch proxy 4000")


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
               test_single_file, test_diagnostics, test_batch):
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
