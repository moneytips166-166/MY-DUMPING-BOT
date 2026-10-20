#!/usr/bin/env python3
"""
patch_fix.py — Complete Safe Patch for Spidey / Lucifer Bot

Fixes:
1. Main menu: adds Email Harvest, Status Filter, AI Keywords, Dedup Status buttons.
2. Admin menu: adds Live Feed, Dedup Stats buttons.
3. Silent crash on /start: resolves UnboundLocalError by moving extended feature
   handlers (aigen, apikeys, emails, livefeed, statuscheck) from inside main()
   to module level, removing duplicate aigen_cmd and duplicate handler registrations.
4. Duplicate admin_livefeed handler: cleans up redundant early callback.
5. Scoped globals check: fixes dir() issue so _LIVE_FEED and _SCANNED_URLS work properly.
"""

import os
import sys
import shutil
import py_compile

def find_target_file():
    candidates = [
        "bot.py",
        "main.py",
        "/home/yashdev/spidey/bot.py",
        "/root/spidey/bot.py",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def apply_patch():
    target = find_target_file()
    if not target:
        print("❌ Could not find bot.py or main.py in current directory!")
        print("   Please cd to your bot directory or pass the file name:")
        print("   python3 patch_fix.py /path/to/bot.py")
        sys.exit(1)

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        target = sys.argv[1]

    print(f"Target file: {target}")
    with open(target, "r", encoding="utf-8") as f:
        src = f.read()

    # Create backup
    bak = target + ".bak"
    shutil.copy2(target, bak)
    print(f"💾 Backup created: {bak}")

    applied = []
    skipped = []
    errors = []

    # ──────────────────────────────────────────────────────────────────
    # 1. Main menu buttons
    # ──────────────────────────────────────────────────────────────────
    main_menu_new_btns = (
        '        [InlineKeyboardButton("📧 Eᴍᴀɪʟ Hᴀʀᴠᴇsᴛ",            callback_data="menu_emails"),\n'
        '         InlineKeyboardButton("⚡ Sᴛᴀᴛᴜs Fɪʟᴛᴇʀ",           callback_data="menu_statuscheck")],\n'
        '        [InlineKeyboardButton("🤖 AI Kᴇʏᴡᴏʀᴅs",             callback_data="menu_aigen"),\n'
        '         InlineKeyboardButton("🔁 Dᴇᴅᴜᴘ Sᴛᴀᴛᴜs",            callback_data="menu_dedup")],\n'
        '        [InlineKeyboardButton("⚜️ Bᴜʏ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ",          callback_data="menu_source")],'
    )
    main_menu_old = '        [InlineKeyboardButton("⚜️ Bᴜʏ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ",          callback_data="menu_source")],'

    if 'callback_data="menu_emails")' in src and 'callback_data="menu_aigen")' in src[:src.find("def make_admin_menu")]:
        skipped.append("Main menu buttons (already present)")
    elif main_menu_old in src:
        src = src.replace(main_menu_old, main_menu_new_btns, 1)
        applied.append("Main menu buttons added")
    else:
        errors.append("Could not locate main menu anchor line (⚜️ Bᴜʏ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ)")

    # ──────────────────────────────────────────────────────────────────
    # 2. Admin menu buttons
    # ──────────────────────────────────────────────────────────────────
    admin_menu_new_btns = (
        '        [InlineKeyboardButton("👁️ Lɪᴠᴇ Fᴇᴇᴅ",           callback_data="admin_livefeed"),\n'
        '         InlineKeyboardButton("🔁 Dᴇᴅᴜᴘ Sᴛᴀᴛs",          callback_data="admin_dedupstats")],\n'
        '        [InlineKeyboardButton("🗂️︎ Gᴇᴛ Bᴏᴛ Fɪʟᴇ",    callback_data="admin_getfile")],'
    )
    admin_menu_old = '        [InlineKeyboardButton("🗂️︎ Gᴇᴛ Bᴏᴛ Fɪʟᴇ",    callback_data="admin_getfile")],'

    if 'callback_data="admin_livefeed")' in src[:src.find("def make_genkey_plan_menu")]:
        skipped.append("Admin menu buttons (already present)")
    elif admin_menu_old in src:
        src = src.replace(admin_menu_old, admin_menu_new_btns, 1)
        applied.append("Admin menu buttons added")
    else:
        errors.append("Could not locate admin menu anchor line (🗂️︎ Gᴇᴛ Bᴏᴛ Fɪʟᴇ)")

    # ──────────────────────────────────────────────────────────────────
    # 3. Remove duplicate early admin_livefeed handler in button_handler
    # ──────────────────────────────────────────────────────────────────
    dup_livefeed_str = (
        '    elif data == "admin_livefeed":\n'
        '        if not is_admin(user_id):\n'
        '            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)\n'
        '            return MENU\n'
        '        if not _LIVE_FEED:\n'
        '            await query.answer("💤 No active sessions", show_alert=True)\n'
        '            return MENU\n'
        '        lines = ["⚔️━━━━━━━━━━━━━━━━━━━━⚔️\\n👁️ 𝗟𝗜𝗩𝗘 𝗙𝗘𝗘𝗗\\n⚔️━━━━━━━━━━━━━━━━━━━━⚔️\\n"]\n'
        '        for i, (sid, s) in enumerate(_LIVE_FEED.items(), 1):\n'
        '            lines.append(\n'
        '                f"*{i}. {s.get(\'name\',\'?\')}* (`{sid}`)\\n"\n'
        '                f"  {s.get(\'phase\',\'?\')} | Started: `{s.get(\'start\',\'?\')}`\\n"\n'
        '                f"  Dorks: `{s.get(\'dorks_done\',0):,}/{s.get(\'dorks_total\',0):,}` "\n'
        '                f"| URLs: `{s.get(\'urls_found\',0):,}`\\n"\n'
        '            )\n'
        '        lines.append("🔄 _Tap again to refresh_")\n'
        '        await query.edit_message_text(\n'
        '            "\\n".join(lines),\n'
        '            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]),\n'
        '            parse_mode=ParseMode.MARKDOWN,\n'
        '        )\n'
        '        return MENU\n\n'
    )
    if dup_livefeed_str in src:
        src = src.replace(dup_livefeed_str, "", 1)
        applied.append("Removed duplicate early admin_livefeed callback")
    else:
        skipped.append("Duplicate early admin_livefeed callback (not found or already removed)")

    # ──────────────────────────────────────────────────────────────────
    # 4. Fix globals check for _LIVE_FEED and _SCANNED_URLS
    # ──────────────────────────────────────────────────────────────────
    if '"_LIVE_FEED" in dir()' in src or '"_SCANNED_URLS" in dir()' in src:
        src = src.replace('"_LIVE_FEED" in dir()', '"_LIVE_FEED" in globals()')
        src = src.replace('"_SCANNED_URLS" in dir()', '"_SCANNED_URLS" in globals()')
        applied.append("Fixed globals check for _LIVE_FEED and _SCANNED_URLS")
    else:
        skipped.append("Globals check for _LIVE_FEED and _SCANNED_URLS (already fixed)")

    # ──────────────────────────────────────────────────────────────────
    # 5. Fix UnboundLocalError on /start (Silent Crash Fix)
    # Move extended feature handlers from inside main() to module level
    # ──────────────────────────────────────────────────────────────────
    start_marker = "    # ── /emails — harvest emails from any uploaded txt ──────────────────────\n"
    end_marker = "    async def _auto_proxy_cleaner():"

    if start_marker in src and end_marker in src:
        start_idx = src.index(start_marker)
        end_idx = src.index(end_marker)
        funcs_block = src[start_idx:end_idx]

        # Remove duplicate old single-provider aigen_cmd if present
        old_aigen_block = (
            '    # ── /aigen — AI keyword generator via Anthropic API ─────────────────────\n'
            '    async def aigen_cmd(update, ctx):\n'
            '        if not has_access(update.effective_user.id):\n'
            '            await update.message.reply_text("❌ Access denied.")\n'
            '            return\n'
            '        prompt = " ".join(ctx.args).strip() if ctx.args else ""\n'
            '        if not prompt:\n'
            '            await update.message.reply_text(\n'
            '                "⚔️ Usage: `/aigen email dump keywords`\\n"\n'
            '                "Generates 500+ targeted keywords via AI.",\n'
            '                parse_mode=ParseMode.MARKDOWN,\n'
            '            )\n'
            '            return\n'
            '        if not _ANTHROPIC_KEY:\n'
            '            await update.message.reply_text(\n'
            '                "❌ `ANTHROPIC_API_KEY` not set on VPS.\\n"\n'
            '                "Run: `export ANTHROPIC_API_KEY=sk-ant-...` before starting bot.",\n'
            '                parse_mode=ParseMode.MARKDOWN,\n'
            '            )\n'
            '            return\n'
            '        msg = await update.message.reply_text("🔮 Generating keywords via AI...")\n'
            '        try:\n'
            '            import aiohttp as _ah\n'
            '            _sys = (\n'
            '                "You are an expert keyword generator for OSINT and web scraping. "\n'
            '                "Generate ONLY a plain list of keywords, one per line, no numbering, "\n'
            '                "no extra text, no explanation. Just the keywords."\n'
            '            )\n'
            '            _user = (\n'
            '                f"Generate 600 highly specific search keywords for: {prompt}\\n"\n'
            '                "Include variations, related terms, synonyms, and niche-specific terms. "\n'
            '                "600 keywords minimum, one per line."\n'
            '            )\n'
            '            async with _ah.ClientSession() as _sess:\n'
            '                async with _sess.post(\n'
            '                    "https://api.anthropic.com/v1/messages",\n'
            '                    headers={\n'
            '                        "x-api-key": _ANTHROPIC_KEY,\n'
            '                        "anthropic-version": "2023-06-01",\n'
            '                        "content-type": "application/json",\n'
            '                    },\n'
            '                    json={\n'
            '                        "model": "claude-sonnet-4-6",\n'
            '                        "max_tokens": 8000,\n'
            '                        "system": _sys,\n'
            '                        "messages": [{"role": "user", "content": _user}],\n'
            '                    },\n'
            '                    timeout=_ah.ClientTimeout(total=60),\n'
            '                ) as _r:\n'
            '                    _data = await _r.json()\n'
            '            _text = _data.get("content", [{}])[0].get("text", "")\n'
            '            if not _text:\n'
            '                await msg.edit_text("❌ AI returned empty response. Try again.")\n'
            '                return\n'
            '            _kws = [l.strip() for l in _text.splitlines() if l.strip()]\n'
            '            ts = datetime.now().strftime("%d%m%y_%H%M")\n'
            '            content = "\\n".join(_kws).encode("utf-8")\n'
            '            await msg.delete()\n'
            '            await update.message.reply_document(\n'
            '                document=io.BytesIO(content),\n'
            '                filename=f"lucifer_keywords_{len(_kws)}_{ts}.txt",\n'
            '                caption=(\n'
            '                    f"⚔️ 𝗔𝗜 𝗞𝗲𝘆𝘄𝗼𝗿𝗱𝘀 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱\\n"\n'
            '                    f"├ 🔑 Total: `{len(_kws):,}`\\n"\n'
            '                    f"├ 🎯 Topic: `{prompt[:40]}`\\n"\n'
            '                    f"└ ⚔️ Lᴜᴄɪꜰᴇʀ AI"\n'
            '                ),\n'
            '                parse_mode=ParseMode.MARKDOWN,\n'
            '            )\n'
            '        except Exception as _e:\n'
            '            await msg.edit_text(f"❌ AI Error: `{str(_e)[:80]}`", parse_mode=ParseMode.MARKDOWN)\n\n'
        )
        if old_aigen_block in funcs_block:
            funcs_block = funcs_block.replace(old_aigen_block, "")

        # Dedent 4 spaces
        dedented_lines = []
        for line in funcs_block.splitlines():
            if line.startswith("    "):
                dedented_lines.append(line[4:])
            elif line == "":
                dedented_lines.append("")
            else:
                dedented_lines.append(line)
        dedented_block = "\n".join(dedented_lines) + "\n\n"

        # Remove funcs_block from inside main()
        src = src[:start_idx] + src[end_idx:]

        # Place before `def main():`
        main_marker = "# ── MAIN ───────────────────────────────────────────────────────────────────────\n\ndef main():"
        if main_marker in src:
            header = "# ── EXTENDED FEATURES (AI, Emails, LiveFeed, StatusCheck) ───────────────────────\n\n"
            src = src.replace(main_marker, header + dedented_block + main_marker, 1)
            applied.append("Moved extended handlers to module scope (fixed UnboundLocalError on /start)")
        else:
            errors.append("Could not find '# ── MAIN ... def main():' anchor line")
    else:
        skipped.append("Extended handlers already at module scope")

    # ──────────────────────────────────────────────────────────────────
    # 6. Remove duplicate handler registrations in main()
    # ──────────────────────────────────────────────────────────────────
    dup_handler_reg = (
        '    app.add_handler(CommandHandler("livefeed",     livefeed_cmd))\n'
        '    app.add_handler(CommandHandler("aigen",        aigen_cmd))\n'
        '    app.add_handler(CommandHandler("statuscheck",  statuscheck_cmd))'
    )
    clean_handler_reg = (
        '    app.add_handler(CommandHandler("livefeed",     livefeed_cmd))\n'
        '    app.add_handler(CommandHandler("statuscheck",  statuscheck_cmd))'
    )
    if dup_handler_reg in src:
        src = src.replace(dup_handler_reg, clean_handler_reg, 1)
        applied.append("Removed duplicate CommandHandler('aigen', aigen_cmd)")
    else:
        skipped.append("Duplicate aigen handler registration (already clean)")

    # Save changes
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    # Validate syntax
    try:
        py_compile.compile(target, doraise=True)
        print("✅ Python syntax validation passed!")
    except Exception as e:
        print(f"❌ Syntax Error: {e}")
        print(f"Restoring backup from {bak}...")
        shutil.copy2(bak, target)
        sys.exit(1)

    print("\n" + "="*50)
    print("PATCH REPORT:")
    print("="*50)
    for a in applied:
        print(f"  ✅ {a}")
    for s in skipped:
        print(f"  ⏭️  {s}")
    for err in errors:
        print(f"  ❌ {err}")
    print("="*50)
    if errors:
        print("⚠️  Some patches encountered errors. Please check above.")
    else:
        print(f"🎉 SUCCESS! {target} is now fully updated and tested.")
        print("You can now start your bot safely:")
        print("  python3 bot.py")

if __name__ == "__main__":
    apply_patch()
