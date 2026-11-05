# 🐍 PYTHON SNAKE CORE — v1.6

**Sirf kaam ka bot.** Koi faaltu cheez nahi, koi mockup nahi — sab real.

---

## ⚡ Install (ek command)

```bash
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_install.sh" -o si.sh && bash si.sh
```

Ye kya karta hai:

- `~/snake` folder banata hai
- `snake_core.py` download karta hai (**3,9xx lines** — pehle wale 29,000 ki jagah)
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

Commands: `/admin` `/theme` `/ping` `/setkey` `/myid` `/ban <id>` `/unban <id>` `/addkey <days>` `/help`

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

## 🔑 v1.6 — REDEEM THEEK + BUGS FIX

### Key redeem ab 3 tarike se chalti hai
Pehle **key redeem hi nahi hoti thi** — 3 jagah se tooti hui thi:

| Bug | Pehle | Ab |
|---|---|---|
| `/redeem KEY` command | **exist hi nahi karta tha** — bot chup | ✅ kaam karta hai |
| Chat me key type karna | access-gate pehle atak jata tha | ✅ seedha redeem |
| 🔑 REDEEM button | wapas wahi "key lo" message (loop) | ✅ redeem screen khulti hai |
| `/start SNK-...` | ignore | ✅ deep-link redeem |
| 📖 HELP bina key | blocked | ✅ khulta hai |

**Ab bas ye 3 tarike:**
```text
/redeem SNK-AB12-CD34
```
```text
SNK-AB12-CD34          ← bas paste kar do
```
ya 🔑 **REDEEM KEY** button → key bhejo.

- Format: `SNK-XXXX-XXXX` (dashes ke saath)
- Galat format / use ho chuki key / nahi mili → **saaf jawab** (pehle silence)
- `/redeem` bina key → instructions + key listener
- Telegram `/` menu me commands register ho gaye (`redeem` included)

### 🐛 Aur jo fix hua
- **VERSION** ab `v1.6` — header me dikhega, update hua ya nahi turant pata chalega
- **Captcha dobara nahi poochta** — ek baar solve, `data/users.json` me save
- `./update.sh` bhi dead-screen safe (`screen -wipe` + precise pgrep)

## 🆕 v1.5 — DEAD SCREEN FIX + FILE UPLOAD

### 🩺 "Bot pehle se chal raha hai" par bot chup? — FIXED
Asli wajah: **dead screen session** (`26134.snake (Dead ???)`). Purana `start.sh`
sirf `screen -ls` ka text dekhta tha aur maan leta tha ki bot chal raha hai —
jabki wo session mar chuka tha. Ab:

- `screen -wipe` pehle chalta hai (dead session saaf)
- `pgrep -f snake_core.py` se **asli process** check hota hai (text nahi)
- dead session mile to auto-quit + fresh start
- 8 sec wait, phir bhi na utha to **log tail** dikhata hai
- `stop.sh` / `status.sh` bhi same logic

```bash
cd ~/snake && ./update.sh && ./start.sh && ./doctor.sh
```

### 📂 FILE UPLOAD — `.txt` bhejo, bot khud samajh jayega
Ab bot ko **document** bhej sakte ho — dorks / URLs / keywords ka `.txt`.
Bot **auto-detect** karta hai (dork operators %, URL %, warna keywords) aur
uske hisaab se buttons deta hai:

| File type | Buttons |
|---|---|
| 🎯 **DORKS** | 🚀 Deep Scan · 📊 Analyze · 🎲 Randomize · 💉 Injector |
| 🔗 **URLs** | 🔗 URL Reverse · 💉 Injector · 🧹 Clean + Dedupe |
| 🔑 **KEYWORDS** | 🎯 Keywords ➪ Dorks · 💉 Injector |

- **8 MB** / **20,000 lines** tak, `.txt/.csv/.list/.dork/.urls/.lst`
- `#` comments aur blank lines skip
- `site:` domains se Common Crawl **automatic** use hota hai
- Analyze → har line ka score + bucket (🔥80+ … 🔴<25) + txt dump
- Clean+Dedupe → tracking params, fragments hata ke unique URLs
- Sab results `.txt` file me download

> File bhejne ke liye bas chat me document attach karo — koi command nahi.

## 🩺 v1.4 — bot chup kyun hai + Deep Parser + free APIs

### Bot chal raha hai par jawab nahi? — `./doctor.sh`

Sabse common 3 wajah, sab auto-check hoti hain:

| Problem | Doctor kya karta hai |
|---|---|
| **Webhook set hai** | Polling chalti hi nahi. Bot khud `delete_webhook` karta hai startup pe |
| **Purana bot same token pe** (`~/spidey/bot_fixed.py`) | Telegram `409 Conflict` — doctor PID dhoondh ke batata hai + `pkill` command deta hai |
| **Token revoke / galat** | `getMe` se 401 pakadta hai |

Doctor ye bhi check karta hai: file syntax, screen session, duplicate process,
`getUpdates` conflict, admin id, theme, aaj ka log — aur end me **quick fix block**.

Plus `/ping` command — bot zinda hai ya nahi, uptime, PID, users, theme.

### 🚀 DEEP PARSER (competitor jaisa card)

PARSER → **🚀 DEEP SCAN** — har dork scan hota hai (koi early stop nahi), aur card:

```
Scanned: 1000/1000 dorks
Raw URLs: 23454
Unique URLs: 1513
⚠️ Errors: 418

🚫 Filtered: 17160
   (junk 16234 • dork-mismatch 926)
```

Live progress bar bhi chalta hai `[████░░░░] 42%`.

### 🌐 Free URL sources (koi API key nahi)

| Source | Limit | Key |
|---|---|---|
| **Common Crawl CDX** | practically unlimited | ❌ nahi chahiye |
| **Wayback CDX** | unlimited | ❌ nahi chahiye |
| 13 search engines | engine-dependent | ❌ nahi chahiye |
| **SerpAPI** (optional) | 100/month free | ✅ chahiye |
| **Google CSE** (optional) | 100/day free | ✅ chahiye |

`site:example.com` wala dork ho to bot **automatically Common Crawl** se us domain
ke saare URLs uthata hai (bade engines isse nahi kar paate).

API key optional: `/setkey serpapi YOUR_KEY` ya `/setkey cse KEY CX`

---

## 🎨 v1.3 — THEME / FONT ENGINE (8 looks)

Poora bot ka look badalne ke liye ek command: **`/theme`** (admin) ya admin panel → **🎨 THEME / FONT**

Har theme 3 cheez badalta hai: **heading font**, **button font**, **divider + icon**.

| Theme | Heading | Buttons | Divider |
|---|---|---|---|
| ✿︎ **CLASSIC** | `ᴘʏᴛʜᴏɴ ꜱɴᴀᴋᴇ` | small caps | `✿︎━━━━━━━✿︎` |
| ❤︎ **CURSIVE** | `𝓟𝓨𝓣𝓗𝓞𝓝` | script | `❤︎﹌﹌﹌﹌❤︎` |
| ﹌ **POPPINS** | `𝗣𝗬𝗧𝗛𝗢𝗡` | bold sans | `﹌﹌﹌﹌﹌﹌` |
| ಄ **ITALIC** | `𝑷𝒀𝑻𝑯𝑶𝑵` | bold italic | `಄──────಄` |
| ♛ **ROYAL** | `𝔓𝔜𝔗ℌ𝔒𝔑` | double-struck | `♛﹌﹌﹌♛` |
| ◆ **ROBOTO** | `𝖯𝖸𝖳𝖧𝖮𝖭` | sans | `◆▬▬▬▬◆` |
| 𝗕 **BOLD** | `𝐏𝐘𝐓𝐇𝐎𝐍` | bold serif | `❰❰❰❰❰❰❱` |
| ▚ **MONO** | `𝙿𝚈𝚃𝙷𝙾𝙽` | monospace | `▚▚▚▚▚▚` |

**16 unicode fonts** available: bold, italic, bold-italic, script, bold-script,
fraktur, double-struck, sans, sans-bold, sans-italic, sans-bold-italic, mono,
wide, small-caps, circled, plain.

> Font automatically sirf **text** pe lagta hai — emoji/icon waise hi rehte hain
> (`🔍 PARSER` → `🔍 ᴘᴀʀꜱᴇʀ`). Har button, heading, aur section tag themed hai.
> Setting `data/settings.json` me save hoti hai — restart ke baad bhi rehti hai.

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

**105 tests pass** (55 v1.4 + 50 UI/core)
- **16 font maps** — koi invalid/box glyph nahi (unicodedata se verify)
- **8 themes** — header, divider, icon, buttons, HTML validity
- **button routing** — main menu, dorker, parser, injector, randomizer, dumper, theme, admin
- **persistence** — theme disk se wapas load — mock HTTP server se real behaviour verify:
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
