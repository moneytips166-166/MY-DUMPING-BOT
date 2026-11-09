#!/usr/bin/env python3
"""Screen audit — saare text screens render karo aur dhoondo:
   • koi bhi literal %s / %d / %.0f bacha hua (unformatted bug)
   • khaali screen / None
   • HTML tag imbalance (<b> bina </b>)
   • Telegram 4096 limit cross
"""
import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import FakeContext, FakeUpdate, load_core  # noqa: E402

core = load_core()
BAD = []
LEAK = re.compile(r'%(?!%)[-+ #0]*\d*(?:\.\d+)?[sdrifc]')


def check(name, txt):
    if not isinstance(txt, str) or not txt.strip():
        BAD.append("%s → khaali/None screen" % name)
        return txt
    m = LEAK.search(txt)
    if m:
        BAD.append("%s → literal %s leak" % (name, m.group(0)))
    for tag in ("b", "i", "code"):
        if txt.count("<%s>" % tag) != txt.count("</%s>" % tag):
            BAD.append("%s → <%s> tag imbalance" % (name, tag))
    if len(txt) > 4096:
        BAD.append("%s → %d chars (4096 limit cross)" % (name, len(txt)))
    return txt


def screens():
    out = {}
    out["main_text"] = core.main_text("Tester")
    out["help_text"] = core.help_text()
    out["APIS_TEXT"] = core.APIS_TEXT
    out["tool_redeem_text"] = core.tool_redeem_text()
    for fn in ("pro_cfg_text", "tool_parse_text", "tool_dork_text"):
        if callable(getattr(core, fn, None)):
            out[fn] = getattr(core, fn)()
    if callable(getattr(core, "admin_dash", None)):
        out["admin_dash"] = core.admin_dash()
    out["batch_card"] = core.batch_card()
    out["session_card_empty"] = core.session_card(0)
    out["webscan_card_post"] = core._webscan_card(
        {"mode": "post", "done": 3, "tested": 12, "forms": 2, "no_form": 1,
         "vulns": [], "vuln_urls": [], "took": 1.5, "waf": "", "errors": 0})
    out["webscan_card_header"] = core._webscan_card(
        {"mode": "header", "done": 2, "tested": 12, "headers_tested": 6,
         "vulns": [], "vuln_urls": [], "took": 0.8, "waf": "Cloudflare"})
    out["webscan_progress"] = core._webscan_progress(
        {"mode": "post", "done": 1, "urls": 3, "tested": 5, "forms": 1,
         "vulns": [], "waf": "", "stage": "forms"}, 0)
    out["country_kb_page2"] = (core.H("COUNTRY DORKS", "test") + "\n\n" + core.P("test"))
    return out


async def cb_screens():
    """Callback wale screens — fake query se render karo."""
    res = {}
    cases = {
        "tool_parse": ("m:parse", core.tool_parse),
        "tool_dork": ("m:dork", core.tool_dork),
        "tool_kw": ("m:kw", core.tool_kw),
        "tool_rev": ("m:rev", core.tool_rev),
        "tool_inj": ("m:inj", core.tool_inj),
        "tool_inj_post": ("inj:post", core.tool_inj_post),
        "tool_inj_header": ("inj:header", core.tool_inj_header),
        "cb_inj_session": ("inj:session", core.cb_inj_session),
        "tool_proxy": ("m:proxy", core.tool_proxy),
        "tool_qa": ("m:qa", core.tool_qa),
        "tool_rand": ("m:rand", core.tool_rand),
        "tool_dump": ("m:dump", core.tool_dump),
        "cb_inj_go": ("inj:go", core.cb_inj_go),
        "cb_dump_go": ("df:go", core.cb_dump_go),
        "cb_dump_harv": ("df:harv", core.cb_dump_harv),
    }
    for name, (data, fn) in cases.items():
        ctx = FakeContext({})
        upd = FakeUpdate(data=data)
        try:
            await fn(upd, ctx)
            res[name] = upd.last_text()
        except Exception as exc:
            BAD.append("%s → EXCEPTION %s: %s" % (name, type(exc).__name__, exc))
    # admin API cards + proxy/engine batch screens
    for data in ("a:keys_api", "a:apis", "a:home", "a:proxy", "a:eng",
                 "inj:cat:sqli", "df:old", "m:inj",
                 "a:pzbatch", "a:pzwant", "a:injbatch",
                 "m:dork", "dk:cms", "dp:country", "m:dump", "kw:niche",
                 "inj:post", "inj:header", "inj:session", "inj:session_set"):
        ctx = FakeContext({})
        upd = FakeUpdate(data=data)
        try:
            await core.on_callback(upd, ctx)
            res[data] = upd.last_text()
        except Exception as exc:
            BAD.append("%s → EXCEPTION %s: %s" % (data, type(exc).__name__, exc))
    # PRO menu
    ctx = FakeContext({})
    upd = FakeUpdate(data="dd:pro")
    try:
        await core.cb_pro_menu(upd, ctx) if hasattr(core, "cb_pro_menu") else None
        if upd.last_text():
            res["cb_pro_menu"] = upd.last_text()
    except Exception as exc:
        BAD.append("cb_pro_menu → EXCEPTION %s" % exc)
    return res


def main():
    s = screens()
    for k, v in s.items():
        check(k, v)
    a = asyncio.run(cb_screens())
    for k, v in a.items():
        check(k, v)
    print("screens checked:", len(s) + len(a))
    print("=" * 60)
    if BAD:
        print("❌ ISSUES %d" % len(BAD))
        for b in BAD:
            print("   •", b)
        return 1
    print("✅ ALL SCREENS CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
