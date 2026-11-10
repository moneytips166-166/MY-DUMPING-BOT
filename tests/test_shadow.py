#!/usr/bin/env python3
"""SHADOW X (shadow/new.py) — offline audit.

Kya check hota hai (koi network nahi):
   • module SHADOW_NO_RUN=1 par import ho jaata hai
   • saare screens render hote hain (HTML tag balance, 4096 limit, empty)
   • saare menu callbacks ka output aata hai (crash nahi)
   • button colours: red / green / blue rule
   • keywords / dorks generator + uniq + build_url
   • admin key → /redeem flow
   • WAF signatures + tamper + error-based value extract
"""
import importlib.util
import os
import re
import sys
import types

os.environ["SHADOW_NO_RUN"] = "1"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "shadow", "new.py")

if not os.path.exists(PATH):
    print("⚠️ shadow/new.py nahi mila — skip")
    sys.exit(0)

try:
    import telebot  # noqa: F401
    import aiohttp  # noqa: F401
except ImportError as e:
    print("⚠️ dependency missing (%s) — skip: pip install pyTelegramBotAPI aiohttp" % e)
    sys.exit(0)

BAD = []
OK = [0]
LEAK = re.compile(r"%(?!%)[-+ #0]*\d*(?:\.\d+)?[sdrifc]")


def chk(cond, msg):
    if cond:
        OK[0] += 1
    else:
        BAD.append(msg)


def load():
    spec = importlib.util.spec_from_file_location("shadow_new", PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _Msg:
    def __init__(self, mid=1):
        self.message_id = mid


def fake_bot(sent):
    class Fake:
        def send_message(self, chat_id, text, **kw):
            sent.append((chat_id, "send", text, kw.get("reply_markup")))
            return _Msg(len(sent))

        def edit_message_text(self, text, **kw):
            sent.append((kw.get("chat_id"), "edit", text, kw.get("reply_markup")))
            return _Msg(kw.get("message_id", 1))

        def answer_callback_query(self, *a, **k):
            return None

        def delete_message(self, *a, **k):
            return None

        def send_document(self, chat_id, f, caption=""):
            sent.append((chat_id, "doc", caption, None))
            return _Msg(len(sent))

        def get_me(self):
            return types.SimpleNamespace(username="shadow_test")

    return Fake()


def audit_text(name, txt):
    if not isinstance(txt, str) or not txt.strip():
        BAD.append("%s → khaali/None" % name)
        return
    m = LEAK.search(txt)
    if m:
        BAD.append("%s → literal %s leak" % (name, m.group(0)))
    for tag in ("b", "i", "code"):
        if txt.count("<%s>" % tag) != txt.count("</%s>" % tag):
            BAD.append("%s → <%s> tag imbalance" % (name, tag))
    if len(txt) > 4096:
        BAD.append("%s → %d chars (4096 cross)" % (name, len(txt)))
    OK[0] += 1


def main():
    m = load()

    # ── basic ────────────────────────────────────────────────────────────────
    chk(m.VERSION.startswith("v"), "VERSION missing")
    chk(m.BUILD, "BUILD missing")
    chk(callable(m.main), "main() missing")
    chk(hasattr(m.bot, "infinity_polling"), "infinity_polling missing")

    sent = []
    m.bot = fake_bot(sent)
    uid = 8937044612
    m.ADMINS = [uid, 8999053405]

    class U:
        id = uid
        username = "tester"

    class Chat:
        id = uid

    class Call:
        id = "cb1"

        def __init__(self, data):
            self.data = data
            self.from_user = U()
            self.message = types.SimpleNamespace(chat=Chat())

    class MsgObj:
        def __init__(self, text="", document=None):
            self.text = text
            self.document = document
            self.chat = Chat()
            self.from_user = U()

    # ── screens ──────────────────────────────────────────────────────────────
    for fn, name in ((m.main_text, "main_text"),):
        audit_text(name, fn(uid))
    for f in (m.screen_kw, m.screen_dork, m.screen_parse, m.screen_inj,
              m.screen_dump, m.screen_cfg):
        n = len(sent)
        f(Chat.id)
        chk(len(sent) > n, "%s → kuch bheja hi nahi" % f.__name__)
        audit_text(f.__name__, sent[-1][2])

    # ── buttons ──────────────────────────────────────────────────────────────
    rule = {"home": "primary", "kw": "primary", "dork": "primary",
            "dork:5000": "success", "parse:last": "success", "inj:last": "success",
            "dump:last": "success", "stop:abc": "danger", "del:1": "danger",
            "cfg:param": "primary", "proxy:hunt": "success", "adm:key": "success"}
    for cb, want in rule.items():
        got = m.bstyle(cb)
        chk(got == want, "bstyle(%s) = %s, chahiye %s" % (cb, got, want))
    chk(m.bstyle("x", "⛔ STOP") == "danger", "⛔ label danger nahi")
    chk(m.bstyle("x", "🚀 GO") == "success", "🚀 label success nahi")
    kb = m.main_kb().to_dict()["inline_keyboard"]
    styles = [b.get("style") for row in kb for b in row]
    chk(all(s in ("primary", "success", "danger") for s in styles),
        "main_kb me invalid style")
    chk("primary" in styles and "success" in styles, "main_kb me rang missing")
    chk(kb[0][0]["text"].endswith("PIPELINE"), "pehla button pipeline nahi")
    chk(any("HQ KEYWORDS" in b["text"] for row in kb for b in row), "HQ KEYWORDS button nahi")

    # ── callbacks (network-free) ─────────────────────────────────────────────
    for d in ("home", "kw", "dork", "parse", "inj", "dump", "qc", "waf", "subs",
              "proxy", "cfg", "cfg:param", "cfg:eng", "files", "support",
              "admin", "adm:stats", "adm:users"):
        n = len(sent)
        m.on_cb(Call(d))
        chk(len(sent) > n, "callback %s → output nahi" % d)

    n = len(sent)
    m.on_cb(Call("dork:200"))
    chk(len(sent) > n, "dork:200 → output nahi")
    chk(len(m.gen_dorks(50)) == 50, "gen_dorks(50) count galat")

    m.on_cb(Call("cfg:eng:yandex"))
    chk("yandex" in m.sget("engines"), "engine toggle ON fail")
    m.on_cb(Call("cfg:eng:yandex"))
    chk("yandex" not in m.sget("engines"), "engine toggle OFF fail")

    # ── keyword flow ─────────────────────────────────────────────────────────
    m.on_cb(Call("kw"))
    m.on_input(MsgObj("shoes\nwatch\nlaptop"))
    kws = m.gen_keywords(["shoes"], 30)
    chk(len(kws) == 30, "gen_keywords count galat")
    chk(len(set(kws)) == len(kws), "keywords duplicate")
    chk(all(k == k.lower() for k in kws), "keywords lowercase nahi")

    # ── admin key + redeem ───────────────────────────────────────────────────
    m.on_cb(Call("adm:key"))
    keys = m.jload("keys", {})
    chk(bool(keys), "admin key create nahi hui")
    key = list(keys)[-1]
    chk(re.match(r"^SHX-[0-9A-F]{4}-[0-9A-F]{4}$", key), "key format galat: %s" % key)
    m.cmd_redeem(MsgObj("/redeem " + key))
    chk(m.jload("keys", {})[key].get("used_by") == uid, "redeem ne key use nahi ki")

    # ── helpers ──────────────────────────────────────────────────────────────
    chk(m.build_url("http://x/a.php?id=1&p=2", "' OR 1=1-- -", "id").startswith("http://x/a.php"),
        "build_url base galat")
    chk("p=2" in m.build_url("http://x/a.php?id=1&p=2", "x", "id"), "build_url doosra param gira")
    chk(m.uniq([1, 1, 2, 3]) == [1, 2, 3], "uniq fail")
    chk(m.waf_detect(403, {"Server": "cloudflare", "cf-ray": "x"}, "") == "Cloudflare",
        "waf_detect CF fail")
    chk(m.extract_value("XPATH syntax error: '~5.7.44~'") == "5.7.44", "extract_value fail")
    chk("UN/**/ION" in m.tamper("' UNION SELECT 1-- -", "comment"), "tamper comment fail")
    chk(m.param_of("http://x/a.php?id=1",) == "id", "param_of fail")
    chk(m.only_params(["http://x/a", "http://x/b?q=1"]) == ["http://x/b?q=1"],
        "only_params fail")

    # ── commands ─────────────────────────────────────────────────────────────
    m.cmd_start(MsgObj("/start"))
    chk(str(uid) in m.jload("users", {}), "/start ne user save nahi kiya")
    m.cmd_ping(MsgObj("/ping"))
    chk(m.VERSION in sent[-1][2], "/ping me version nahi")
    m.cmd_help(MsgObj("/help"))
    m.cmd_admin(MsgObj("/admin"))
    m.cmd_stop(MsgObj("/stop"))
    m.on_input(MsgObj("random text"))
    chk("Samajh nahi aaya" in sent[-1][2], "fallback message nahi")

    print("shadow checks:", OK[0] + len(BAD))
    print("=" * 60)
    if BAD:
        print("❌ ISSUES %d" % len(BAD))
        for b in BAD:
            print("   •", b)
        return 1
    print("✅ SHADOW X CLEAN (%d checks)" % OK[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
