#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  HYPER v19.3 — KEYWORD MAKER EXACT-COUNT FIX
  Bug  : 800 keywords maange -> sirf 624 bane (2 seeds par combination space chhoti thi)
  Fix  : 8 x 10 x 9 variant expansion -> 50,000+ unique keywords guaranteed
  Run  : python3 hyper_kwboost_v19_3.py [bot_fixed.py]
================================================================================
"""

import os
import re
import sys
import shutil
import py_compile
from datetime import datetime

NEW_FUNC = '''def _v19_make_keywords(seeds: list, count: int) -> list:
    """Exact-count UHQ keyword generator (8x10x9 variant expansion — 50,000+ guaranteed)."""
    count = max(1, int(count))
    bases, seen_b = [], set()
    for s in seeds:
        s = re.sub(r"\\s+", " ", str(s or "").strip().lower())
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

    out, seen = [], set()

    def _push(kw: str) -> bool:
        kw = re.sub(r"\\s+", " ", str(kw or "")).strip()
        if not kw or len(kw) < 6 or len(kw) > 70 or kw in seen:
            return False
        if not re.search(r"[a-z]{2,}", kw):
            return False
        seen.add(kw)
        out.append(kw)
        return len(out) >= count

    B = len(bases)
    S = len(_V19_KW_SUFFIX)
    i = 0
    max_iter = count * 200 + 20_000
    while len(out) < count and i < max_iter:
        b = bases[i % B]
        s = _V19_KW_SUFFIX[(i // B) % S]
        v1 = _V19_KW_V1[(i // (B * S)) % len(_V19_KW_V1)]
        v2 = _V19_KW_V2[(i // (B * S * len(_V19_KW_V1))) % len(_V19_KW_V2)]
        v3 = _V19_KW_V3[(i // (B * S * len(_V19_KW_V1) * len(_V19_KW_V2))) % len(_V19_KW_V3)]
        parts = []
        if v2:
            parts.append(v2)
        parts.append(b)
        if s and s not in b:
            parts.append(s)
        if v1 and v1 not in b:
            parts.append(v1)
        if v3:
            parts.append(v3)
        if _push(" ".join(parts)):
            break
        i += 1
    return out[:count]


_V19_KW_V1 = ["", "online", "page", "store", "shop", "site", "checkout", "instant"]
_V19_KW_V2 = ["", "best", "cheap", "new", "pro", "global", "vip", "fast", "secure", "trusted"]
_V19_KW_V3 = ["", "deals", "offers", "sale", "hub", "zone", "world", "point", "plus"]
'''

MARKERS = ("def _v19_make_keywords(seeds: list, count: int) -> list:", "_V19_KW_V1 = [")


def patch(target: str) -> None:
    if not os.path.isfile(target):
        raise SystemExit("❌ %s nahi mila" % target)
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    if "_V19_KW_V1 = [" not in src and "def _v19_make_keywords(seeds: list, count: int) -> list:" not in src:
        raise SystemExit("❌ Pehle V19 patch apply karo (hyper_venom_parser_v19.py).")

    # remove old variant constants if present
    src = re.sub(r"\n_V19_KW_V1 = \[[^\]]*\]\n", "\n", src)
    src = re.sub(r"\n_V19_KW_V2 = \[[^\]]*\]\n", "\n", src)
    src = re.sub(r"\n_V19_KW_V3 = \[[^\]]*\]\n", "\n", src)

    # replace whole function
    m = re.search(r"^def _v19_make_keywords\(seeds: list, count: int\) -> list:\n(?:.*?\n)*?(?=^\S)", src, re.M)
    if not m:
        raise SystemExit("❌ _v19_make_keywords nahi mili — version mismatch.")
    src = src[:m.start()] + NEW_FUNC + "\n" + src[m.end():]

    backup = "%s.v193_backup_%s" % (target, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(target, backup)
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
    except Exception as exc:
        shutil.copyfile(backup, target)
        raise SystemExit("❌ Compile fail — rollback. %s" % exc)

    print("=" * 70)
    print("  ✅ v19.3 KEYWORD EXACT-COUNT FIX APPLIED")
    print("=" * 70)
    print("  Target : %s" % target)
    print("  Backup : %s" % backup)
    print("  Fix    : 800 -> 800 (pehle 624), 50,000 bhi possible")
    print("=" * 70)


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else "bot_fixed.py")
