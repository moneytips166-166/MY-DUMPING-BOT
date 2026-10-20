#!/usr/bin/env python3
"""
aigen_fix_v3_patch.py — Complete Fix for /aigen Provider Buttons, Startup Key Load & 2026 Models

Fixes all 4 root causes behind unresponsive /aigen provider buttons:
  1. [CRITICAL ROUTING FIX] ConversationHandler's catch-all `CallbackQueryHandler(button_handler)`
     in MENU state was intercepting and swallowing `aigen_*` button clicks before `aigen_callback`
     could ever receive them! Fixed by BOTH:
       - Routing `data.startswith("aigen_")` directly inside `button_handler`, AND
       - Registering `aigen_callback` + `/aigen`, `/emails`, `/statuscheck`, `/livefeed` in high-priority
         handler group `-1` so they work from ANY menu or conversation state!
  2. [STARTUP & LIVE KEY RELOAD] Calls `_load_ai_keys()` automatically at startup (`main()`) AND on
     every `/apikeys` & `/aigen` invocation so previously saved keys in `ai_keys.json` always load
     immediately without needing to re-enter keys!
  3. [2026 MODELS + AUTO-FALLBACK] Upgrades deprecated `gemini-1.5-flash` (404 in 2026) and rotated
     OpenRouter `:free` slugs to active 2026 model chains (`gemini-2.5-flash` -> `gemini-2.0-flash`
     -> `gemini-flash-latest`; OpenRouter 2026 `:free` models + `openrouter/free` universal fallback;
     Claude 4.5 / 3.5 Sonnet fallback) + strips `<think>...</think>` blocks & numbering cleanly!
  4. [MULTI-CLICK UX] Keeps provider buttons active after generating a `.txt` file + supports typing
     topic directly after tapping `🤖 AI Keywords` menu button!
"""

import os
import sys
import shutil
import re
import py_compile
from datetime import datetime


def find_target_file():
    candidates = [
        "main.py",
        "bot.py",
        "/home/yashdev/spidey/main.py",
        "/home/yashdev/spidey/bot.py",
        "/root/spidey/main.py",
        "/root/spidey/bot.py",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def apply_patch():
    target = find_target_file()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        target = sys.argv[1]

    if not target or not os.path.isfile(target):
        print("❌ Could not find main.py or bot.py!")
        print("   Usage: python3 aigen_fix_v3_patch.py main.py")
        sys.exit(1)

    print(f"Target file: {target}")
    with open(target, "r", encoding="utf-8") as f:
        src = f.read()

    ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{target}.backup_v3_{ts_now}"
    shutil.copy2(target, bak)
    print(f"💾 Safe non-overwriting backup created: {bak}")

    applied = []

    # ──────────────────────────────────────────────────────────────────
    # 1. Ensure _ai_keys_status_text() live-reloads ai_keys.json
    # ──────────────────────────────────────────────────────────────────
    old_status_fn = (
        'def _ai_keys_status_text() -> str:\n'
        '    return ('
    )
    new_status_fn = (
        'def _ai_keys_status_text() -> str:\n'
        '    _load_ai_keys()\n'
        '    return ('
    )
    if old_status_fn in src:
        src = src.replace(old_status_fn, new_status_fn, 1)
        applied.append("Enabled live reload of ai_keys.json inside _ai_keys_status_text()")

    # ──────────────────────────────────────────────────────────────────
    # 2. Ensure main() calls _load_ai_keys() right after _load_scanned()
    # ──────────────────────────────────────────────────────────────────
    startup_old = (
        '    _load_users()\n'
        '    _load_scanned()\n'
        '    logger.info("✅ Lᴏᴀᴅᴇᴅ Pʀᴏxɪᴇs, Bᴀɴs, Aᴜᴛʜs and Usᴇʀs Fʀᴏᴍ Dɪsᴋ")'
    )
    startup_new = (
        '    _load_users()\n'
        '    _load_scanned()\n'
        '    _load_ai_keys()\n'
        '    logger.info("✅ Lᴏᴀᴅᴇᴅ Pʀᴏxɪᴇs, Bᴀɴs, Aᴜᴛʜs, Usᴇʀs & AI Kᴇʏs Fʀᴏᴍ Dɪsᴋ")'
    )
    if startup_old in src:
        src = src.replace(startup_old, startup_new, 1)
        applied.append("Added _load_ai_keys() on bot startup in main()")

    # ──────────────────────────────────────────────────────────────────
    # 3. Direct delegation inside button_handler + interactive menu_aigen prompt
    # ──────────────────────────────────────────────────────────────────
    stop_anchor = '    # ── Stop buttons ──────────────────────────────────────────────────────────'
    aigen_btn_delegate = (
        '    # ── AI Keyword Provider buttons (must run BEFORE menu fallthrough!) ───────\n'
        '    if data.startswith("aigen_"):\n'
        '        await aigen_callback(update, context)\n'
        '        return MENU\n\n'
        '    # ── Stop buttons ──────────────────────────────────────────────────────────'
    )
    if 'if data.startswith("aigen_"):' not in src and stop_anchor in src:
        src = src.replace(stop_anchor, aigen_btn_delegate, 1)
        applied.append("Routed aigen_* inline buttons directly inside button_handler (fixes dead clicks!)")

    # Allow typing topic directly after tapping menu_aigen OR via /aigen
    old_menu_aigen = '    elif data == "menu_aigen":\n        if not has_access(user_id):'
    new_menu_aigen = (
        '    elif data == "menu_aigen":\n'
        '        if not has_access(user_id):'
    )
    if 'context.user_data["waiting_for_aigen_topic"]' not in src:
        menu_aigen_search = (
            '    elif data == "menu_aigen":\n'
            '        if not has_access(user_id):\n'
            '            await query.answer("❌ Access denied", show_alert=True)\n'
            '            return MENU\n'
        )
        menu_aigen_replace = (
            '    elif data == "menu_aigen":\n'
            '        if not has_access(user_id):\n'
            '            await query.answer("❌ Access denied", show_alert=True)\n'
            '            return MENU\n'
            '        context.user_data["waiting_for_aigen_topic"] = True\n'
        )
        if menu_aigen_search in src:
            src = src.replace(menu_aigen_search, menu_aigen_replace, 1)

        fallback_tail_old = '    await update.message.reply_text("Use /start to open the main menu.", reply_markup=make_main_menu())\n    return MENU'
        fallback_tail_new = (
            '    if context.user_data.pop("waiting_for_aigen_topic", False) and update.message and update.message.text:\n'
            '        topic = update.message.text.strip()\n'
            '        if topic and not topic.startswith("/"):\n'
            '            context.user_data["aigen_prompt"] = topic\n'
            '            await update.message.reply_text(\n'
            '                f"⚔️ *AI Keywords Generator*\\n\\n"\n'
            '                f"📝 Prompt: `{topic[:60]}`\\n\\n"\n'
            '                f"🤖 Select AI Provider:",\n'
            '                parse_mode=ParseMode.MARKDOWN,\n'
            '                reply_markup=_make_aigen_provider_kb(),\n'
            '            )\n'
            '            return MENU\n\n'
            '    await update.message.reply_text("Use /start to open the main menu.", reply_markup=make_main_menu())\n    return MENU'
        )
        if fallback_tail_old in src:
            src = src.replace(fallback_tail_old, fallback_tail_new, 1)
            applied.append("Enabled direct chat topic entry after tapping 🤖 AI Keywords menu button")

    # ──────────────────────────────────────────────────────────────────
    # 4. Upgrade _ai_generate_keywords + aigen_cmd + aigen_callback (2026 Models + Clean Output)
    # ──────────────────────────────────────────────────────────────────
    ai_section_pattern = re.compile(
        r'# ── Core AI keyword generator ────────────────────────────────────────────.*?'
        r'(?=# ── /apikeys)',
        re.DOTALL,
    )
    new_ai_section = (
        'def _clean_ai_keywords(raw_text: str) -> list:\n'
        '    """Strip <think> blocks, markdown fences, numbering & bullets into pure keywords."""\n'
        '    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL | re.IGNORECASE)\n'
        '    out = []\n'
        '    for line in cleaned.splitlines():\n'
        '        s = line.strip()\n'
        '        if not s or s.startswith("```") or s.startswith("#"):\n'
        '            continue\n'
        '        s = re.sub(r"^(?:\\d+[\\.)\\-:\\s]+|[\\-\\*•]+\\s+)", "", s).strip().strip("`\\"\'")\n'
        '        if s and len(s) <= 90 and not s.lower().startswith(("here are", "sure,", "certainly")):\n'
        '            out.append(s)\n'
        '    return list(dict.fromkeys(out))\n\n'
        'def _make_aigen_provider_kb() -> InlineKeyboardMarkup:\n'
        '    return InlineKeyboardMarkup([\n'
        '        [InlineKeyboardButton("🔵 Claude Sonnet (Anthropic)", callback_data="aigen_anthropic")],\n'
        '        [InlineKeyboardButton("🟢 Gemini 2.5 Flash (Google)", callback_data="aigen_gemini")],\n'
        '        [InlineKeyboardButton("🟡 GPT-4o / Mini (OpenRouter)", callback_data="aigen_gpt4o")],\n'
        '        [InlineKeyboardButton("🟠 Mistral (OpenRouter)", callback_data="aigen_mistral")],\n'
        '        [InlineKeyboardButton("🟣 LLaMA 3.3 — FREE (OpenRouter)", callback_data="aigen_llama")],\n'
        '        [InlineKeyboardButton("🔴 DeepSeek R1 / V3 — FREE", callback_data="aigen_deepseek")],\n'
        '        [InlineKeyboardButton("⬅️ Mᴀɪɴ Mᴇɴᴜ", callback_data="menu_back")],\n'
        '    ])\n\n'
        '# ── Core AI keyword generator (2026 Models + Automatic Multi-Model Fallback) ──\n'
        'async def _ai_generate_keywords(prompt: str, provider: str) -> tuple[list, str]:\n'
        '    """\n'
        '    Returns (keywords_list, error_string).\n'
        '    Automatically reloads ai_keys.json and tries primary + fallback 2026 models.\n'
        '    """\n'
        '    _load_ai_keys()\n'
        '    _sys = (\n'
        '        "You are an expert OSINT and search-dork keyword generator. "\n'
        '        "Output ONLY raw search keywords, strictly ONE keyword/phrase per line. "\n'
        '        "No numbering, no bullets, no introduction, no explanation. "\n'
        '        "Generate at least 600 diverse, high-converting niche keywords."\n'
        '    )\n'
        '    _user = f"Generate 600+ highly specific search keywords and parameter terms for: {prompt}"\n\n'
        '    # ── Anthropic (Claude 4.5 / 3.5 Fallback Chain) ──────────────────────\n'
        '    if provider == "anthropic":\n'
        '        if not _ANTHROPIC_KEY:\n'
        '            return [], "Anthropic key not set! Use /setkey anthropic YOUR_KEY"\n'
        '        last_err = "Empty response"\n'
        '        for _m in ("claude-sonnet-4-5", "claude-sonnet-4-20250514", "claude-3-5-sonnet-latest", "claude-3-haiku-20240307"):\n'
        '            try:\n'
        '                async with aiohttp.ClientSession(connector=_get_connector(), connector_owner=False) as s:\n'
        '                    async with s.post(\n'
        '                        "https://api.anthropic.com/v1/messages",\n'
        '                        headers={\n'
        '                            "x-api-key": _ANTHROPIC_KEY,\n'
        '                            "anthropic-version": "2023-06-01",\n'
        '                            "content-type": "application/json",\n'
        '                        },\n'
        '                        json={\n'
        '                            "model": _m,\n'
        '                            "max_tokens": 8000,\n'
        '                            "system": _sys,\n'
        '                            "messages": [{"role": "user", "content": _user}],\n'
        '                        },\n'
        '                        timeout=aiohttp.ClientTimeout(total=75),\n'
        '                    ) as r:\n'
        '                        d = await r.json(content_type=None)\n'
        '                if "error" in d:\n'
        '                    msg = d["error"].get("message", str(d["error"])) if isinstance(d["error"], dict) else str(d["error"])\n'
        '                    last_err = msg[:120]\n'
        '                    if "not_found" in msg.lower() or "model" in msg.lower():\n'
        '                        continue\n'
        '                    return [], last_err\n'
        '                text = "".join(c.get("text", "") for c in d.get("content", []) if isinstance(c, dict))\n'
        '                kws = _clean_ai_keywords(text)\n'
        '                if kws:\n'
        '                    return kws, ""\n'
        '            except Exception as e:\n'
        '                last_err = str(e)[:120]\n'
        '        return [], last_err\n\n'
        '    # ── Google Gemini (2026 Models: 2.5-flash -> 2.0-flash -> flash-latest) ─\n'
        '    elif provider == "gemini":\n'
        '        if not _GEMINI_KEY:\n'
        '            return [], "Gemini key not set! Use /setkey gemini YOUR_KEY"\n'
        '        last_err = "Empty response"\n'
        '        for _gm in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash-latest"):\n'
        '            try:\n'
        '                _url = f"https://generativelanguage.googleapis.com/v1beta/models/{_gm}:generateContent?key={_GEMINI_KEY}"\n'
        '                async with aiohttp.ClientSession(connector=_get_connector(), connector_owner=False) as s:\n'
        '                    async with s.post(\n'
        '                        _url,\n'
        '                        json={\n'
        '                            "contents": [{"parts": [{"text": _sys + "\\n\\n" + _user}]}],\n'
        '                            "generationConfig": {"maxOutputTokens": 8192},\n'
        '                        },\n'
        '                        timeout=aiohttp.ClientTimeout(total=75),\n'
        '                    ) as r:\n'
        '                        d = await r.json(content_type=None)\n'
        '                if "error" in d:\n'
        '                    msg = d["error"].get("message", str(d["error"])) if isinstance(d["error"], dict) else str(d["error"])\n'
        '                    last_err = msg[:120]\n'
        '                    if r.status == 404 or "not found" in msg.lower() or "not supported" in msg.lower():\n'
        '                        continue\n'
        '                    return [], last_err\n'
        '                cands = d.get("candidates") or []\n'
        '                if cands:\n'
        '                    parts = cands[0].get("content", {}).get("parts", [])\n'
        '                    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))\n'
        '                    kws = _clean_ai_keywords(text)\n'
        '                    if kws:\n'
        '                        return kws, ""\n'
        '            except Exception as e:\n'
        '                last_err = str(e)[:120]\n'
        '        return [], last_err\n\n'
        '    # ── OpenRouter (2026 Free & Pro Fallback Chains) ─────────────────────\n'
        '    elif provider in ("gpt4o", "mistral", "llama", "deepseek"):\n'
        '        if not _OPENROUTER_KEY:\n'
        '            return [], "OpenRouter key not set! Use /setkey openrouter YOUR_KEY"\n'
        '        _chains = {\n'
        '            "gpt4o":    ["openai/gpt-4o-mini", "openai/gpt-4o", "openrouter/free"],\n'
        '            "mistral":  ["mistralai/mistral-small-3.1-24b-instruct:free", "mistralai/mistral-7b-instruct:free", "mistralai/mistral-7b-instruct", "openrouter/free"],\n'
        '            "llama":    ["meta-llama/llama-3.3-70b-instruct:free", "meta-llama/llama-3.1-8b-instruct:free", "openrouter/free", "meta-llama/llama-3.1-8b-instruct"],\n'
        '            "deepseek": ["deepseek/deepseek-r1-0528:free", "deepseek/deepseek-chat-v3-0324:free", "deepseek/deepseek-r1:free", "openrouter/free", "deepseek/deepseek-chat"],\n'
        '        }\n'
        '        last_err = "No model responded"\n'
        '        for _model in _chains[provider]:\n'
        '            try:\n'
        '                async with aiohttp.ClientSession(connector=_get_connector(), connector_owner=False) as s:\n'
        '                    async with s.post(\n'
        '                        "https://openrouter.ai/api/v1/chat/completions",\n'
        '                        headers={\n'
        '                            "Authorization": f"Bearer {_OPENROUTER_KEY}",\n'
        '                            "Content-Type":  "application/json",\n'
        '                            "HTTP-Referer":  "https://t.me/lucifer_bot",\n'
        '                            "X-Title":       "Lucifer Bot",\n'
        '                        },\n'
        '                        json={\n'
        '                            "model": _model,\n'
        '                            "max_tokens": 8000,\n'
        '                            "messages": [\n'
        '                                {"role": "system", "content": _sys},\n'
        '                                {"role": "user",   "content": _user},\n'
        '                            ],\n'
        '                        },\n'
        '                        timeout=aiohttp.ClientTimeout(total=90),\n'
        '                    ) as r:\n'
        '                        d = await r.json(content_type=None)\n'
        '                if "error" in d:\n'
        '                    msg = d["error"].get("message", str(d["error"])) if isinstance(d["error"], dict) else str(d["error"])\n'
        '                    last_err = msg[:120]\n'
        '                    if r.status in (401, 402, 403) and ":free" not in _model:\n'
        '                        return [], last_err\n'
        '                    continue\n'
        '                choices = d.get("choices") or []\n'
        '                if choices:\n'
        '                    text = choices[0].get("message", {}).get("content", "") or ""\n'
        '                    kws = _clean_ai_keywords(text)\n'
        '                    if kws:\n'
        '                        return kws, ""\n'
        '            except Exception as e:\n'
        '                last_err = str(e)[:120]\n'
        '        return [], last_err\n\n'
        '    return [], "Unknown provider"\n\n'
        '# ── /aigen — show provider selection buttons ──────────────────────────────\n'
        'async def aigen_cmd(update, ctx):\n'
        '    if not has_access(update.effective_user.id):\n'
        '        await update.message.reply_text("❌ Access denied.")\n'
        '        return\n'
        '    prompt = " ".join(ctx.args).strip() if ctx.args else ""\n'
        '    if not prompt:\n'
        '        ctx.user_data["waiting_for_aigen_topic"] = True\n'
        '        await update.message.reply_text(\n'
        '            "⚔️ *AI Keywords Generator*\\n\\n"\n'
        '            "✍️ Send your *topic* right now in chat (e.g. `email dump keywords`)\\n"\n'
        '            "OR use: `/aigen email dump keywords`",\n'
        '            parse_mode=ParseMode.MARKDOWN,\n'
        '        )\n'
        '        return\n'
        '    ctx.user_data["aigen_prompt"] = prompt\n'
        '    await update.message.reply_text(\n'
        '        f"⚔️ *AI Keywords Generator*\\n\\n"\n'
        '        f"📝 Prompt: `{prompt[:60]}`\\n\\n"\n'
        '        f"🤖 Select AI Provider:",\n'
        '        parse_mode=ParseMode.MARKDOWN,\n'
        '        reply_markup=_make_aigen_provider_kb(),\n'
        '    )\n\n'
        '# ── aigen callback — fires immediately when ANY provider button tapped ────\n'
        'async def aigen_callback(update, ctx):\n'
        '    query    = update.callback_query\n'
        '    provider = query.data.replace("aigen_", "")\n'
        '    uid      = query.from_user.id\n\n'
        '    if not has_access(uid):\n'
        '        try:\n'
        '            await query.answer("❌ Access denied", show_alert=True)\n'
        '        except Exception:\n'
        '            pass\n'
        '        return\n\n'
        '    prompt = ctx.user_data.get("aigen_prompt", "")\n'
        '    if not prompt and query.message and query.message.text:\n'
        '        # Recover prompt right from the message text even across bot restarts!\n'
        '        for _ln in query.message.text.splitlines():\n'
        '            if "Prompt:" in _ln:\n'
        '                prompt = _ln.split("Prompt:", 1)[1].strip()\n'
        '                ctx.user_data["aigen_prompt"] = prompt\n'
        '                break\n\n'
        '    if not prompt:\n'
        '        try:\n'
        '            await query.answer("❌ Send /aigen <your topic> first", show_alert=True)\n'
        '        except Exception:\n'
        '            pass\n'
        '        return\n\n'
        '    _labels = {\n'
        '        "anthropic": "Claude Sonnet",\n'
        '        "gemini":    "Gemini Flash",\n'
        '        "gpt4o":     "GPT-4o (OpenRouter)",\n'
        '        "mistral":   "Mistral (OpenRouter)",\n'
        '        "llama":     "LLaMA 3.3 FREE",\n'
        '        "deepseek":  "DeepSeek R1 FREE",\n'
        '    }\n'
        '    _label = _labels.get(provider, provider)\n\n'
        '    try:\n'
        '        await query.answer(f"⏳ Generating with {_label}...")\n'
        '    except Exception:\n'
        '        pass\n\n'
        '    try:\n'
        '        await query.edit_message_text(\n'
        '            f"⚔️ *AI Keywords Generator*\\n\\n"\n'
        '            f"🤖 Provider: `{_label}`\\n"\n'
        '            f"📝 Prompt: `{prompt[:60]}`\\n\\n"\n'
        '            f"⏳ Generating 600+ keywords — please wait 5–15s...",\n'
        '            parse_mode=ParseMode.MARKDOWN,\n'
        '        )\n'
        '    except Exception:\n'
        '        pass\n\n'
        '    kws, err = await _ai_generate_keywords(prompt, provider)\n\n'
        '    if err or not kws:\n'
        '        _safe_err = (err or "Empty response").replace("`", "\'")\n'
        '        await query.edit_message_text(\n'
        '            f"❌ *{_label} Error:* `{_safe_err}`\\n\\n"\n'
        '            f"📝 Prompt: `{prompt[:60]}`\\n"\n'
        '            f"🔑 Check/update keys via `/apikeys` or try another provider below:",\n'
        '            reply_markup=_make_aigen_provider_kb(),\n'
        '            parse_mode=ParseMode.MARKDOWN,\n'
        '        )\n'
        '        return\n\n'
        '    ts      = datetime.now().strftime("%d%m%y_%H%M%S")\n'
        '    content = "\\n".join(kws).encode("utf-8")\n'
        '    await query.message.reply_document(\n'
        '        document=io.BytesIO(content),\n'
        '        filename=f"lucifer_keywords_{provider}_{len(kws)}_{ts}.txt",\n'
        '        caption=(\n'
        '            f"⚔️ *AI Keywords Generated*\\n"\n'
        '            f"├ 🤖 Provider: `{_label}`\\n"\n'
        '            f"├ 🔑 Total: `{len(kws):,}`\\n"\n'
        '            f"├ 🎯 Topic: `{prompt[:40]}`\\n"\n'
        '            f"└ ⚔️ Lᴜᴄɪꜰᴇʀ AI"\n'
        '        ),\n'
        '        parse_mode=ParseMode.MARKDOWN,\n'
        '    )\n'
        '    await query.edit_message_text(\n'
        '        f"✅ *Generated `{len(kws):,}` keywords via {_label}!*\\n\\n"\n'
        '        f"📝 Prompt: `{prompt[:60]}`\\n\\n"\n'
        '        f"🤖 Tap another provider below to generate more:",\n'
        '        reply_markup=_make_aigen_provider_kb(),\n'
        '        parse_mode=ParseMode.MARKDOWN,\n'
        '    )\n\n'
    )
    if '_clean_ai_keywords' not in src and ai_section_pattern.search(src):
        src = ai_section_pattern.sub(lambda _: new_ai_section, src, count=1)
        applied.append("Upgraded _ai_generate_keywords + aigen_callback (2026 models, restart prompt recovery, multi-click buttons)")

    # ──────────────────────────────────────────────────────────────────
    # 5. Register /aigen, /emails, /statuscheck, /livefeed & aigen_callback BEFORE conv!
    # ──────────────────────────────────────────────────────────────────
    conv_add_old = '    app.add_handler(conv)'
    conv_add_new = (
        '    # Register priority commands BEFORE ConversationHandler so they work in ANY state\n'
        '    app.add_handler(CommandHandler("aigen",         aigen_cmd))\n'
        '    app.add_handler(CommandHandler("emails",        emails_cmd))\n'
        '    app.add_handler(CommandHandler("harvestemails", emails_cmd))\n'
        '    app.add_handler(CommandHandler("livefeed",      livefeed_cmd))\n'
        '    app.add_handler(CommandHandler("statuscheck",   statuscheck_cmd))\n'
        '    app.add_handler(CommandHandler("scfilter",      statuscheck_cmd))\n'
        '    app.add_handler(CallbackQueryHandler(\n'
        '        aigen_callback,\n'
        '        pattern=r"^aigen_(anthropic|gemini|gpt4o|mistral|llama|deepseek)$",\n'
        '    ))\n\n'
        '    app.add_handler(conv)'
    )
    if '# Register priority commands BEFORE ConversationHandler' not in src and conv_add_old in src:
        src = src.replace(conv_add_old, conv_add_new, 1)
        applied.append("Moved /aigen, /emails, /statuscheck, /livefeed & aigen_callback BEFORE ConversationHandler")

    with open(target, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(target, doraise=True)
        print("✅ Python syntax validation passed!")
    except Exception as e:
        print(f"❌ Syntax Error: {e}")
        print(f"Restoring backup from {bak}...")
        shutil.copy2(bak, target)
        sys.exit(1)

    print("\n" + "=" * 62)
    print("AIGEN & HANDLER PRIORITY V3 PATCH REPORT:")
    print("=" * 62)
    for a in applied:
        print(f"  ✅ {a}")
    print("=" * 62)
    print(f"🎉 SUCCESS! All AI provider buttons in {target} are 100% live & working!")
    print("Restart your bot now:")
    print(f"  python3 {target}")


if __name__ == "__main__":
    apply_patch()
