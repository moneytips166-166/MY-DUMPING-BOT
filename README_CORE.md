# 🐍 PYTHON SNAKE CORE — v1.2

**Sirf kaam ka bot.** Koi faaltu cheez nahi, koi mockup nahi — sab real.

---

## ⚡ Install (ek command)

```bash
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_install.sh" -o si.sh && bash si.sh
```

Ye kya karta hai:

- `~/snake` folder banata hai
- `snake_core.py` download karta hai (**2,680 lines** — pehle wale 29,000 ki jagah)
- purane `~/spidey/bot_fixed.py` se **token + admin ID khud utha leta hai**
- `start.sh / stop.sh / restart.sh / logs.sh / status.sh / update.sh / setconfig.sh` banata hai (sab **screen** based)
- packages check karta hai

Phir:

```bash
cd ~/snake && ./start.sh && ./logs.sh
```

---

## 🧰 Tools — bas yehi 9

| # | Tool | Kya karta hai |
|---|---|---|
| 1 | 🔍 **PARSER** | **13 engines** (SearXNG auto • DDG • Bing • Mojeek • Yahoo • Brave • Startpage • Yandex • Qwant • Ecosia • Google • Marginalia • SearX) + pagination + strict dork matching |
| 2 | 🎯 **DORKER** | page-type / extension / parameter / mixed / niche — real generator, quality se sorted |
| 3 | 🔑 **HQ KEYWORDS** | seed topic → scored, filtered keyword list |
| 4 | 🔗 **URL REVERSE** | URL toda → domain / path / ext / params + dorks (DORKPRO jaisa) |
| 5 | 💉 **INJECTOR** | **67 payloads, 6 categories** (SQLi/LFI/XSS/SSRF/redirect/SSTI) |
| 6 | 📦 **DUMPER** | sab results txt/json/zip me |
| 7 | 🧅 **PROXY** | 45 sources + DoH bypass + **400 parallel** checker |
| 8 | 📊 **QUALITY** | dork/keyword ko 0-100 + wajah |
| 9 | 🎲 **RANDOMIZER** | shuffle + operator mutate |

Plus 👑 **ADMIN PANEL** (`/admin`) — 14 buttons.

---

## 📦 Database (real, generated)

| Cheez | Count |
|---|---|
| Page-types (dir × file × query-shape) | **57,288** |
| Dorks | **35,689,680** |
| Parameters | 615 |
| Extensions | 62 |
| TLDs | 73 |
| Keywords space | 23,664 |

---

## 🧅 Proxy engine

- **45 sources / 15 domains** — jsDelivr, Statically, gitHack, GitHub, proxyscrape v2+v4, geonode, github.io mirrors
- **DoH bypass** — `1.1.1.1` / `8.8.8.8` se IP nikaal ke `Host:` header ke saath direct IP connect (DNS block bypass)
- **400 parallel** checker, 200 alive milne pe ruk jata hai
- **Manual list** — `data/manual_proxies.txt` (1 line = 1 proxy)
- **Card me diagnostics** — `🌐 Sources: 31/45 OK • raw lines: 128,450`

---

## 👑 Admin panel

```
📊 DASHBOARD   👥 USERS     🔑 KEYS      🧅 PROXY
⚙️ ENGINE      📦 DUMPS     📣 BROADCAST 🚫 BANS
💾 BACKUP      🖥 SYSTEM    🧹 CLEAR     📜 LOGS
🔄 RESTART     ⬅️ MENU
```

Commands: `/admin` `/myid` `/ban <id>` `/unban <id>` `/addkey <days>` `/help`

---

## 🔐 Security

`snake_core.py` me token **placeholder** hai. Asli token sirf aapke device pe:

```bash
./setconfig.sh --token 123456789:AAGxxxx
./setconfig.sh --admin 8999053405
./restart.sh
```

`.gitignore` me `.env`, `config.py`, `data/`, `dumps/` hai.

---

## 🆚 Pehle vs ab

| | Pehle (bot_fixed.py) | Ab (snake_core.py) |
|---|---|---|
| Lines | 29,222 | **2,680** |
| Buttons | 7 + 13 admin | 10 + 14 admin |
| Layers | v1 → v28 patches | **clean rewrite** |
| Mock data | tha | **zero** |
| Proxy | 45 src (v28 patch) | 45 src (**native**) |
| Parser | mixed | **7 engines, retry, dead-skip** |

Purana bot safe hai — `~/spidey` me waise hi pada hai. Rollback chahiye to wahi chalao.

---

## 🚀 v1.2 — advanced engine layer

| Upgrade | Detail |
|---|---|
| 🔎 **13 engines** | SearXNG (auto-instance) • DDG • Bing • Mojeek • Yahoo • Brave • Startpage • **Yandex** • **Qwant** • **Ecosia** • Google • **Marginalia** • SearX |
| 🌐 **SearXNG auto-discovery** | `searx.space/data/instances.json` se healthy instances khud uthata hai (HTTP 200 + 70%+ success + non-Tor), 24h disk cache, 6h memory cache. JSON API try karta hai, fail pe HTML fallback |
| 📄 **Pagination** | har engine ka apna page-param (ddg `s=30`, bing `first=11`, google `start=30` …) |
| 🎯 **Strict dork matching** | results ko dork ke `inurl:` / `filetype:` se verify karta hai — jo match nahi karta wo **drop**. Ye wahi cheez hai jo "advanced" tools me nahi hoti. Kisi dork pe 0 bache to fallback unfiltered |
| 💉 **67 payloads / 6 categories** | SQLi (22), LFI (12), XSS (8), SSRF (10), Open-Redirect (8), SSTI (8) |
| 🔧 **Helper refresh** | `update.sh` ab `start.sh`/`logs.sh` bhi update karta hai |

### 🐛 v1.2 me fix

- **Sub-buttons route nahi ho rahe the** — DORKER ke mode buttons, PARSER ke "LAST DORKS", PROXY ke "SCAN", DUMPER ke file buttons — sab dead the. Poora callback router (`_route_tool_cb`) add hua.
- **`logs.sh` purana crash dikhata tha** — ab `=== START ===` marker ke baad ka hi log dikhata hai.
- **`start.sh` chup-chaap fail hota tha** — ab fail pe seedha error print karta hai.

---

## 🐍 Python 3.14 support (v1.1)

Python 3.12+ / 3.14 pe PTB ka `run_polling()` ye error deta hai:

```
RuntimeError: There is no current event loop in thread 'MainThread'.
```

**Fix ho gaya.** Ab bot apna event loop khud banata hai (`_run_loop` + `_serve`) —
`asyncio.get_event_loop()` bilkul use nahi hota. Clean shutdown SIGINT/SIGTERM pe.

---

## 🧪 Test

**193 tests + 22 runner = 215 pass**
- `103` core (parser/proxy/dork/kw/reverse/inject/dump/storage/UI)
- `49` button routing (har button click simulate)
- `41` advanced (searx discovery, pagination, strict match, 67 payloads, helpers)
- `22` runner (3.14 simulate) — mock HTTP server se real behaviour verify:
proxy parse (6 format), scrape (7 sources), checker, dork gen (5 mode), quality scorer,
keyword gen, URL reverse, randomizer, injector, parser (8 engines), extractors,
wayback, dumper, storage/access, UI render (HTML valid), callback routing, e2e, chunker.

---

## ❓ Kuch toota to

```bash
cd ~/snake
./logs.sh          # kya error hai
./status.sh        # chal raha hai?
./restart.sh
```

Token issue: `./setconfig.sh --show` → `./setconfig.sh --token <new>` → `./restart.sh`
