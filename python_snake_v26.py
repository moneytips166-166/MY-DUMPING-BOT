#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYTHON SNAKE — v23 CLASSIC-LOOK patch  (naya feature kuch nahi, sirf look + owner name)

  python3 python_snake_v26.py bot_fixed.py

Kya karta hai (v23 ke upar, features bilkul same):
  • Purana CLASSIC font wapas — small-caps (ᴀʙᴄ), ✿ borders — user panel + admin panel
    dono me, jaise original classic bot me tha. Naye plain screens bhi auto classic ho
    jayenge (buttons + messages + captions sab).
  • Keys / IDs / URLs / @username / code blocks ekdum safe — unhe font nahi badalta.
  • Owner username: @LUCIFERCOMINGBABY  ➪  @Bloody_sweet_baby
  • Branding (Python Snake 🐍 + logo) waisa hi.

Dobara chalane pe safe (idempotent).
"""
import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

MARK_START = "# ═══ PYTHON SNAKE v26 CLASSIC LOOK START ═══"
MARK_END = "# ═══ PYTHON SNAKE v26 CLASSIC LOOK END ═══"

OLD_OWNER = '@LUCIFERCOMINGBABY'
NEW_OWNER = '@Bloody_sweet_baby'

BLOCK = r'''# ═══ PYTHON SNAKE v26 CLASSIC LOOK START ═══
# ─────────────────────────────────────────────────────────────────────────────
#  CLASSIC LOOK — purana small-caps font + ✿ borders (user + admin, sab jagah)
#  Data safe: <code>, URLs, @username, HTML tags — inko chhua nahi jaata.
# ─────────────────────────────────────────────────────────────────────────────
import telegram as _v26_tg
import functools as _v26_ft

_V26_GLYPHS = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡʏᴢ"          # 25 (x ka small-cap hota hi nahi)
_V26_ASCII = "abcdefghijklmnopqrstuvwyz"                    # isi order me, bina x
assert len(_V26_GLYPHS) == len(_V26_ASCII) == 25
_V26_MAP = {}
for _a, _g in zip(_V26_ASCII, _V26_GLYPHS):
    _V26_MAP[_a] = _g
    _V26_MAP[_a.upper()] = _g

# jo cheez kabhi nahi badalni: code blocks, prefilled data, HTML tags, links, @handle
_V26_PROTECT = re.compile(
    r"(<code>.*?</code>|<pre>.*?</pre>|<a\s+[^>]*>.*?</a>|<[^>]+>|`[^`]*`|"
    r"https?://[^\s<]+|www\.[^\s<]+|@[A-Za-z0-9_]+|\b\d[\d,.:/%-]*\b)", re.S)


def _v26_caps(seg: str) -> str:
    """ASCII letters ➪ purane classic small-caps (x/X waise hi rehte hain)."""
    if not seg:
        return seg
    return "".join(_V26_MAP.get(_c, _c) for _c in seg)


def _v26_classic(t):
    """Poore text ko classic look do — data protected."""
    if not isinstance(t, str) or not t:
        return t
    try:
        parts = _V26_PROTECT.split(t)
        for _i in range(0, len(parts), 2):
            seg = parts[_i]
            if not seg:
                continue
            seg = _v26_caps(seg)
            # purane jaise ✿ borders
            seg = re.sub(r"(?m)^(━{8,})$", lambda m: "✿︎" + m.group(1) + "✿︎", seg)
            parts[_i] = seg
        return "".join(parts)
    except Exception:
        return t


def _v26_wrap_send(cls, name, text_pos=1):
    orig = getattr(cls, name, None)
    if orig is None or getattr(orig, "_v26_classic", False):
        return False

    @_v26_ft.wraps(orig)
    async def wrapper(self, *args, **kwargs):
        if "text" in kwargs:
            kwargs["text"] = _v26_classic(kwargs["text"])
        if "caption" in kwargs:
            kwargs["caption"] = _v26_classic(kwargs["caption"])
        if text_pos and len(args) >= text_pos and isinstance(args[text_pos - 1], str):
            a = list(args)
            a[text_pos - 1] = _v26_classic(a[text_pos - 1])
            args = tuple(a)
        return await orig(self, *args, **kwargs)

    wrapper._v26_classic = True
    try:
        setattr(cls, name, wrapper)
        return True
    except Exception:
        return False


def _v26_wrap_button(cls):
    orig = getattr(cls, "__init__", None)
    if orig is None or getattr(orig, "_v26_classic", False):
        return False

    @_v26_ft.wraps(orig)
    def init(self, text=None, *a, **k):
        return orig(self, _v26_classic(text), *a, **k)

    init._v26_classic = True
    try:
        cls.__init__ = init
        return True
    except Exception:
        return False


_V26_WRAPPED = 0
for _bcls in (_v26_tg.InlineKeyboardButton, _v26_tg.KeyboardButton):
    try:
        if _v26_wrap_button(_bcls):
            _V26_WRAPPED += 1
    except Exception:
        pass

for _cls, _methods in (
    (_v26_tg.Message, (("reply_text", 1), ("edit_text", 1), ("reply_markdown", 1),
                       ("edit_caption", 1), ("reply_photo", 0), ("reply_document", 0))),
    (_v26_tg.CallbackQuery, (("edit_message_text", 1), ("edit_message_caption", 0))),
    (_v26_tg.Bot, (("send_message", 2), ("edit_message_text", 1), ("send_document", 0),
                   ("send_photo", 0), ("send_video", 0), ("send_animation", 0),
                   ("edit_message_caption", 0), ("send_media_group", 0))),
):
    for _n, _pos in _methods:
        try:
            if _v26_wrap_send(_cls, _n, _pos):
                _V26_WRAPPED += 1
        except Exception:
            pass


# ── jo screens send-path se nahi jaate (seedha text banate hain) ─────────────
_v26_prev_home_text = _v23_home_text
_v26_prev_kb_rows = _v23_kb_rows
_v26_prev_admin_menu = make_admin_menu
_v26_prev_manual_ui = _v23_manual_ui
_v26_prev_captcha_new = _v23_captcha_new


def _v23_home_text(name: str = ""):   # noqa: F811
    return _v26_classic(_v26_prev_home_text(name))


def _v23_kb_rows():   # noqa: F811
    return _v26_prev_kb_rows()   # labels button-wrapper se apne aap classic


def make_admin_menu():   # noqa: F811
    return _v26_prev_admin_menu()


async def _v23_manual_ui(update, context):   # noqa: F811
    return await _v26_prev_manual_ui(update, context)


def _v23_captcha_new(context):   # noqa: F811
    q, kb = _v26_prev_captcha_new(context)
    return _v26_classic(q), kb


try:
    logger.info("🐍 PYTHON SNAKE %s — CLASSIC look ON (%d send-paths) • owner %s",
                _V12_VERSION_TAG, _V26_WRAPPED, ADMIN_USERNAME)
except Exception:
    pass
# ═══ PYTHON SNAKE v26 CLASSIC LOOK END ═══
'''

NEED = ("PYTHON SNAKE v23 START", "_v23_home_text", "_v23_manual_ui")


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    for need in NEED:
        if need not in src:
            raise SystemExit("❌ %s nahi mila — v23 file honi chahiye." % need)

    # ── idempotent cleanup ──
    src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\n*", "", src, flags=re.S)

    # ── owner username ──
    n_owner = src.count(OLD_OWNER)
    src = src.replace(OLD_OWNER, NEW_OWNER)

    m = re.search(r'^if __name__ == ["\']__main__["\']:', src, re.M)
    if not m:
        raise SystemExit("❌ __main__ block nahi mila")
    src = src[:m.start()] + BLOCK.strip("\n") + "\n\n\n" + src[m.start():]

    backup = "%s.v26_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 78)
    print("  ✅ PYTHON SNAKE — CLASSIC LOOK APPLIED (v23 features same)")
    print("=" * 78)
    print("  Target   : %s" % target)
    print("  Backup   : %s" % os.path.basename(backup))
    print("  Font     : purana classic small-caps + ✿ borders (user + admin)")
    print("  Owner    : %s ➪ %s  (%d jagah)" % (OLD_OWNER, NEW_OWNER, n_owner))
    print("  Naya     : kuch nahi — features bilkul v23 wale")
    print("=" * 78)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 python_snake_v26.py bot_fixed.py")
    patch(sys.argv[1])
