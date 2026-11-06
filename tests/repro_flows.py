"""Scenario A/B/C repro — stale-flow bug (v2.1).

A: clean flow     — file upload → EXPAND → number → keywords file bane
B: stale dpgen_count + file + EXPAND → sahi EXPAND flow chale
C: stale dpgen_count + stale dpgen_kw await + seedha "1000" → purana PRO flow na chale
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import ADMIN, FakeContext, FakeDocument, FakeUpdate, load_core  # noqa: E402

KW_FILE = "\n".join([
    "shopify store", "woocommerce shop", "magento admin", "wordpress login",
    "prestashop panel", "bigcommerce store",
]).encode()


async def scenario(name, setup):
    core = load_core()
    ud, ctx = setup()
    print("\n=== %s ===" % name)
    yield_out = []
    out = await _run(core, ud, ctx)
    print(out)
    return out


async def _run(core, ud, ctx=None):
    ctx = ctx or FakeContext(ud)
    # 1) file upload
    upd = FakeUpdate(text=None, doc=FakeDocument("kw.txt", KW_FILE))
    await core.on_document(upd, ctx)
    print("  upload ->", _short(upd.last_text()))
    print("  await  ->", ctx.user_data.get("await"), "| dpgen_count ->",
          ctx.user_data.get("dpgen_count"))
    # 2) EXPAND button
    upd2 = FakeUpdate(data="f:kexp")
    await core.on_callback(upd2, ctx)
    print("  EXPAND ->", _short(upd2.last_text()))
    print("  await  ->", ctx.user_data.get("await"))
    # 3) number bhejo
    upd3 = FakeUpdate(text="1000")
    await core.on_text(upd3, ctx)
    print("  '1000' ->", _short(upd3.last_text()))
    print("  files  ->", upd3.docs()[:2])
    return "\n".join(upd3.texts())


def _short(t):
    t = (t or "").replace("\n", " | ")
    return t[:150]


async def main():
    core = load_core()

    # ── A: clean ──
    ud = {}
    ctx = FakeContext(ud)
    print("\n=== A: clean flow ===")
    upd = FakeUpdate(text=None, doc=FakeDocument("kw.txt", KW_FILE))
    await core.on_document(upd, ctx)
    print("  upload  ->", _short(upd.last_text()))
    upd2 = FakeUpdate(data="f:kexp")
    await core.on_callback(upd2, ctx)
    print("  EXPAND  ->", _short(upd2.last_text()))
    print("  await   ->", ctx.user_data.get("await"))
    upd3 = FakeUpdate(text="1000")
    await core.on_text(upd3, ctx)
    print("  '1000'  ->", _short(upd3.last_text()))
    print("  files   ->", upd3.docs()[:2])

    # ── B: stale dpgen_count ──
    ud = {"dpgen_count": 2000}
    ctx = FakeContext(ud)
    print("\n=== B: stale dpgen_count + file + EXPAND ===")
    upd = FakeUpdate(text=None, doc=FakeDocument("kw.txt", KW_FILE))
    await core.on_document(upd, ctx)
    print("  upload  ->", _short(upd.last_text()))
    upd2 = FakeUpdate(data="f:kexp")
    await core.on_callback(upd2, ctx)
    print("  EXPAND  ->", _short(upd2.last_text()))
    print("  await   ->", ctx.user_data.get("await"))
    upd3 = FakeUpdate(text="1000")
    await core.on_text(upd3, ctx)
    print("  '1000'  ->", _short(upd3.last_text()))
    print("  files   ->", upd3.docs()[:2])

    # ── C: stale dpgen_count + stale await dpgen_kw + seedha number ──
    ud = {"dpgen_count": 2000, "await": "dpgen_kw", "await_ts": __import__("time").time()}
    ctx = FakeContext(ud)
    print("\n=== C: stale PRO flow (fresh ts) + seedha '1000' ===")
    upd = FakeUpdate(text="1000")
    await core.on_text(upd, ctx)
    print("  '1000'  ->", _short(upd.last_text()))
    print("  await   ->", ctx.user_data.get("await"))
    print("  files   ->", upd.docs()[:2])


if __name__ == "__main__":
    asyncio.run(main())
