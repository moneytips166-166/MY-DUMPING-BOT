# 🐍 PYTHON SNAKE CORE — v2.9

**Sirf kaam ka bot.** Koi faaltu cheez nahi, koi mockup nahi — sab real.

---

## 🆕 v2.9 — 8 parser bugs fixed, 7 engines, rotating proxy, STOP button, niches

| Feature | Status |
|---|---|
| 🐛 **8 parser bugs** (abort 15→100, engine-miss pollution, gj cooldown, 6s timeout, 45s window, www-strip no-op, per-run miss) | ✅ FIXED |
| ⚙️ **Engines = 7** — `ddgl, ddg, bing, google, brave, yandex, yahoo` (baaki hata diye) | ✅ |
| 🧅 **Rotating proxy pool** — round-robin, fail pe 180s cooldown, dead engine skip | ✅ NEW |
| ⏱ **Never-block timeout** — 6/8/10s per engine, per-dork cap, 3-miss pe engine side | ✅ NEW |
| ⛔ **STOP button** — DORKER deep scan, PARSER, injector, proxy check (sab me) | ✅ NEW |
| 📊 **New progress bar** — `▰▰▰▱▱` + %, proxies alive, engines up, speed, time left | ✅ NEW |
| 🏠 **Main menu redesign** — HQ KEYWORDS top, ADD NICHE, small-caps labels, counts+disclaimer hataye | ✅ NEW |
| 📁 **Niches** — apne keywords se niche banao (40 max), menu me button, ek tap se dorks | ✅ NEW |
| 💉 **Injector 311 payloads** — 11 cats incl. blind/UNION/WAF/NoSQL/GraphQL, **240 DBMS patterns (21 DBs)** | ✅ |
| 🔑 **HQ keywords** — 16 verb + 20 qual + 20 noun + geo layers, 1M cap, ~38k unique per core | ✅ |
| 🧅 **Proxy scrape admin-only** — home se hata, admin panel me; ➕ ADD PROXIES (14+ formats) + rotation toggle | ✅ |
| 📤 **Dumper FULL EXPORT** — txt + json + csv, no row caps | ✅ NEW |
| 🇬🇧 **UI 100% English** — har screen, har prompt, har error | ✅ NEW |
| 🎨 Stylish fonts har screen pe (cursive/bold/italic headings) | ✅ |

**Jaan bujh ke nahi daala:** full sqlmap dump (row caps ke bina) — active attack hai.
Bot dorks → URLs → injectable URLs banata hai, DB dump nahi karta.

---

## 🆕 v2.8 — competitor se jo cheez kaam ki thi, wo add ho gayi

| Feature | Status |
|---|---|
| 🎖 **Dork Grader** — S+/S/A/B/C/D/F + 9 dimensions + auto split files | ✅ NEW |
| 🧬 **Combo / Hash Analyzer** — `email:pass` extract, hash **pehchan**, password strength | ✅ NEW |
| 🧩 **Merge + Dedup** — jitni files chahiye jama karo, ek merged file | ✅ NEW |
| 🏗 **CMS Dorks** — WordPress/Joomla/OpenCart/PrestaShop/Magento/Drupal/Laravel/CodeIgniter | ✅ NEW |
| 📂 **Exposed Files** — `.env/.sql/.bak/wp-config/phpMyAdmin/.git` dorks | ✅ NEW |
| 🌍 **100+ Countries** — page-wise (45 per page) | ✅ 16 → 107 |
| 🧅 **Proxy formats** — `user:pass@`, `socks5h`, `socks4a`, IPv6 `[::1]:port` | ✅ NEW |
| 🔒 **Trial lock** — `/batch trial 1` (scan chalega, file locked) | ✅ NEW |
| ⚠️ **Anti-leak disclaimer** | ✅ NEW |
| 🎨 Premium emojis / themes | ✅ pehle se (8 theme + cursive/bold/italic fonts) |

**Jo jaan bujh ke nahi daala (sach):**

- `ENV/ADM/PMA Hunter` (200+ paths probe karke DB password nikalna) — doosre ke server pe
  bina permission attack karna hai. Bot ka kaam dork → URL dhoondhna hai, break-in karna nahi.
- `Exploitables` (SQLi confirm), `Live sqlmap monitor`, `43 WAF tamper` — yahi cheez, active attack.
- `Unhash / Brute` (hash cracking) — bot hash **pehchanta** hai (md5/sha1/sha256/bcrypt/argon2),
  par cracking engine nahi hai. Hashcat alag se available hai.

Use kaise:
```
PARSER/DUMPER → file bhejo → 🎖 GRADE / 🧬 COMBO ANALYZE / 🧩 MERGE+DEDUP
DORKER → 🏗 CMS DORKS ya 📂 EXPOSED FILES
```

---

## 🎯 v2.7 — 1,000 dorks = 1,000 scan (koi "kitne URLs?" nahi)

Aapne 1,000 dork ki file bheji thi, bot ne **50** bataye — code me `[:50]` ka
hardcoded cap tha aur phir "kitne URLs chahiye?" poochta tha. Dono gaye.

- ✅ **Saare dorks** use hote hain — 50 / 30 wale caps hata diye (1 se 20,000 tak)
- ✅ **Koi URL count ka sawaal nahi** — `URL limit: SAB (jitna mile utna)`
- ✅ **Timeout ki jagah budget** — default **30 min** scan, `⏱ Baaki: 22 min` live dikhta hai
- ✅ Time khatam → jo URLs mile wahi de deta hai (`⏱ Ruka: time budget khatam`)
- ✅ Progress card me `⏱ Baaki` + `Blocked` + engine-wise wajah
- ✅ Parse card me `Dorks ready` + `URL limit` dikhta hai
- ⚡ **Fast engines** — block hone wale engine (Google/Yandex/Startpage/Brave/Qwant/Ecosia)
  bina proxy try hi nahi hote; jo 3 baar fail ho wo **poori run me skip** (time bachta hai)

```bash
cd ~/snake && ./update.sh && ./restart.sh
```

Control (admin se, agar chahiye):
```
/batch limit 0        # 0 = jitna mile utna (default)
/batch limit 20000    # ya fix limit
/batch budget 60      # 60 minute tak scan chale
```

Aur parser screen me naya button: **🎯 URL LIMIT: SAB** (cycle: SAB → 5k → 20k → 50k → 1L)

---

## 📦 v2.6 — proxy BATCH check (40k–80k bhi poora check hoga)

Pehle: 60k proxies scrape hote the par sirf **pehle 4,000** check hote the — baaki bekaar.
Ab: **batch ke baad agla batch**, jab tak saare na ho.

| Setting | Default | Panel se | Command se |
|---|---|---|---|
| Proxy check batch | **4,000** | 👑 `/admin` → PROXY → 📦 | `/batch proxy 4000` |
| Target alive | **0 (saare)** | 👑 `/admin` → PROXY → 🎯 | `/batch want 0` |
| Inject batch | **200** | 👑 `/admin` → ENGINE → 💉 | `/batch inj 500` |
| Parallel | 400 | 👑 `/admin` → ENGINE | `/batch conc 600` |
| Check timeout | 6s | 👑 `/admin` → ENGINE | `/batch timeout 8` |

- 60,000 proxies + batch 4,000 = **15 batch**, progress me `Batch 7/15` dikhta hai
- Har batch ke baad alive count jama hota hai — koi proxy chhuta nahi
- 🎯 Target alive set karo (jaise 500) to 500 milte hi ruk jaata hai (time bachta hai), `0` = sab check
- 💉 Injector bhi batch me chalta hai (200 URLs → agla 200) — badi list pe bhi atakta nahi
- 📱 Phone pe 2000–4000 best; 10,000 pe RAM zyada kharch hoti hai

```bash
cd ~/snake && ./update.sh && ./restart.sh
```

Phir `/ping` → `📦 Core: v2.6`, aur `/batch` se settings dekh lo.

---

## 🩺 v2.5 — "0 URLs kyun?" ka seedha jawab

Aapke phone pe kuch engines block hain — parser galat nahi tha, bot **ab wajah batata hai**.

- 🔬 `/enginetest` — har engine ke saamne asli wajah: `blocked (IP/rate limit)`, `timeout`, `DNS fail`, `page aayi, 0 results`
- 🪶 **DDG Lite** engine add (`lite.duckduckgo.com`) — halka page, mobile net pe zyada chance
- 📡 **Bing RSS** engine (`format=rss`) — HTML se halka, block kam; `bing.com/ck/a` redirects decode hote hain
- ⏱ Free Google endpoint ka timeout 45s → **12s** (mobile pe parser atakta nahi)
- 🛑 **Early abort** — 15 dork tak 0 URLs + engines fail → ruk jata hai (1000 dork zaya nahi)
- 🕰 **Wayback CDX fallback** — `site:` dork pe Common Crawl khaali ho to Wayback se URLs
- 📉 Parse card me ab `Blocked` bhi dikhta hai, 0-URL card me **engine-wise asli wajah**

```bash
cd ~/snake && ./update.sh && ./restart.sh
```

Phir `/ping` → `📦 Core: v2.5` aur `/enginetest` chalao.

> **Sach:** bina proxy sab kaam kare, iski guarantee nahi. Jio/Airtel ke kuch IP pe DDG/Mojeek block hote hain — us case me proxy ya apna SearXNG hi asli hal hai. Bot ab jhooth nahi bolta ki "sab chal raha hai".

---

## ⚡ Install (ek command)

```bash
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/snake_install.sh" -o si.sh && bash si.sh
```

Ye kya karta hai:

- `~/snake` folder banata hai
- `bot.py` download karta hai (**ek hi file**, ~7,800 lines)
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
| 1 | 🔍 **PARSER** | **15 engines** (SearXNG auto • **DDG Lite** • DDG • Bing • **Bing RSS** • Mojeek • Yahoo • Brave • Startpage • Yandex • Qwant • Ecosia • Google • Marginalia • SearX) + pagination + strict dork matching |
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

## ✨ v2.4 — EK FILE SYSTEM (`bot.py`)

### 📄 Ab sirf EK file: `bot.py`
- **Repo me**: `bot.py` = poora bot. Koi patch, koi alag module nahi.
- **Phone me**: `~/snake/bot.py` (chalta yahi hai) + **same copy**
  `/storage/emulated/0/DBF/bot.py` (aapki maangi jagah — har update pe wahi file refresh hoti hai).
- `snake_core.py` ab sirf **15 line ka shim** hai (purane `start.sh/stop.sh/restart.sh`
  tod na dein) — wo bhi `bot.py` ko hi load karta hai. Code duplicate nahi hota.

### 🔄 `./update.sh` kya karta hai (naya)
```
1. bot.py download (EAGER: 50 KB se chhoti ho to abort)
2. purana token + ADMIN_IDS preserve
3. py_compile check — fail ho to KUCH replace nahi (auto safe)
4. bot.py replace  →  ~/snake/bot.py
5. snake_core.py shim dobara likhta hai
6. /storage/emulated/0/DBF/bot.py me copy
7. version + lines print
```
Purani install (jisme sirf `snake_core.py` tha) bhi **khud migrate** ho jati hai —
pehli baar update chalane pe `snake_core.py` → `bot.py` ban jata hai.

### 🛠 Jo scripts bhi update ho gaye
`snake_setconfig.sh` (token/admin ab `bot.py` me likhta hai) • `snake_doctor.sh` (bot.py check karta hai) • `snake_install.sh` (naya install bhi bot.py + DBF copy).

## ✨ v2.3 — FILE PEHLE, COUNT BAAD ME

### 📂 Ab dono order chalte hain
```
Order A:  GEN → number → FILE        ✅ (v2.2 se)
Order B:  GEN → FILE → number        ✅ (v2.3 — naya)
```
Order B me bot file padh ke **15 min yaad** rakhta hai, aur number aate hi usi file se
dorks bana deta hai. GEN • PRO GEN • HQ KEYWORDS (expand) • PARSER — sab me.

### 🔬 `/enginetest` — asli sach
`/enginetest site:gov.in inurl:login` → har engine ko **bina proxy** try karta hai aur batata hai:
```
✅ ddg        — 12 URLs • 1.3s
❌ yandex     — blocked / 0
```
Ab guess nahi — aapke net pe kaun sa engine chal raha hai wo dikh jata hai.
Jo ❌ hai wo proxy ke bina nahi chalega; `/engines fast` se sirf chalne wale chalao.

### 🧹 Gap-fix report (dork card me)
Har gen ke baad card me dikhta hai: `🧹 Gap fix : 2 multi-word → inurl me hyphen, intitle me quote`
— matlab kitne keywords ka gap bot ne khud sahi shape me badla.

## ✨ v2.2 — HAR FORMAT + FAST PARSER + DEEP CRAWLER

### 📂 File = har format, aur seedha flow me
Pehle: GEN/PRO flow me "keywords bhejo" ke waqt file bhejne se flow **cancel** ho jata tha.
Ab: jo flow khula hai (GEN • PRO • HQ KW • PARSER • QA • REVERSE • INJECTOR • PRO config),
**file seedha usme chali jati hai**.

Supported (koi library nahi chahiye — sab Python built-in):
`txt` • `csv` • `tsv` • `json` / `ndjson` • `log` • `html` • `xlsx` • `docx` • `pptx` •
`zip` • `gz` • **bina extension** bhi.
Saath me: BOM, bullets (`- * •`), numbering (`1.`), quotes, comments (`# //`), duplicates —
sab khud saaf.

### 🔤 Keyword ka gap — sach + fix
**Sach:** haan, aadha sach. `inurl:` me **space kabhi match nahi karta** (URL me space hota hi nahi),
isliye wahan keyword ko **hyphen** karna zaroori hai. `intitle:` / `intext:` me ulta — wahan
**quoted phrase** zyada HQ hota hai.

Ab bot khud decide karta hai:
| Template | Output |
|---|---|
| `inurl:(KW)` | `inurl:shopify-store` ✅ |
| `intitle:(KW)` | `intitle:"shopify store"` ✅ |
| `(KW) (CO)` | `"shopify store" email:pass` ✅ |
| pehle (galat) | `inurl:"shopify store"` → 0 results ❌ |

### ⚡ Engines — phone pe fast
Termux/phone pe 15 engines = slow + block. Ab 3 modes:
```
/engines fast     → ddg, mojeek, marginalia   (bina proxy chalte hain)
/engines normal   → + bing, searxng           (default)
/engines max      → saare 13                  (proxy chahiye)
```
PARSER screen pe 🎛 button se tap-tap me badal jata hai (per user).

### 🔍 Parser — "errors" ka sach
- Default: **proxy ho to use, warna bina proxy** (auto) — pehle zyada "errors" isi se aate the
- "⚠️ Errors" ab **"Engine block"** — matlab us engine ne IP/proxy block kiya, dork me kharabi nahi
- **Relaxed fallback**: strict match me 0 mila to usi dork ke URLs liye jate hain (0-result fix)
- `DEEP PARSER` card me per-engine hits, relaxed count, filtered breakdown — sab dikhta hai

### 🧅 ProxyScrape add
`proxyscrape.com/free-proxy-list` ke apne endpoints + unki GitHub lists — sources **45 → 53**.
`protocolipport` format bhi parse hota hai (`http://1.2.3.4:8080`).

### 🌊 DEEP URL CRAWLER (naya)
URLs do → har page ke andar ke **saare links + parameters** nikaal ke file de deta hai.
- 40 parallel requests, **bina proxy**, 8s timeout
- 2 level (seed → andar ke links → unke andar) optional
- Live progress: pages ok/fail • URLs • params
- Buttons: file card me `🌊 DEEP CRAWL` / `🌊🌊 DEEP 2 LEVEL`, PARSER me `🌊 DEEP CRAWL (last URLs)`

## ✨ v2.1 — FLOW FIX + SERP API HUB

### 🩹 Stale-flow bug (screenshots wala)
Pehle: keywords file upload → **EXPAND** dabao → bot purana adhoora GEN PRO flow
yaad rakh ke **"GEN DORKS (PRO) step 2/2 — ab keywords bhejo"** dikha deta tha.

Ab kaise theek hai:
- har pending input ke saath **timestamp** (`await_set` / `await_get` / `await_clear`)
- **15 min** baad prompt khud expire
- **koi bhi naya button** ya **file upload** = naya intent → purana prompt cancel
- **koi bhi `/command`** = naya intent → purana prompt cancel (group `-1` handler)
- sirf-number input keywords ki jagah reject ("Sirf number keyword nahi hota")
- 14 jagah purana `pop("await")` → `await_clear()` (timestamp bhi saaf)

### 🔑 SERP API hub — `/apis`
Poori list, **asli numbers ke saath** (koi "unlimited" jhooth nahi):

| Provider | Free | Card | Paid |
|---|---|---|---|
| 🔵 Serper | 2,500 one-time | nahi | $0.30–1.00 / 1k |
| 🟢 SerpApi | 250/mahina | nahi | $25 / 1k |
| 🦁 Brave | $5 credit/mahina (~1,000) | haan (abuse check) | metered |
| 🔶 Bright Data | 5,000/mahina | KYC | $1.50 / 1k |
| 🐦 Free Google (bina key) | rate-limited | nahi | — |
| 🌐 Common Crawl | unlimited | nahi | — |
| 🕰 Wayback CDX | unlimited | nahi | — |
| ⚙️ SearXNG (self-host) | **unlimited** | nahi | $0 |

⚠️ **Sach:** koi bhi API truly unlimited nahi hoti. Jo "unlimited" bolti hai wo
limit chhupa rahi hai. Aapki di hui free endpoint bhi kisi ki personal service hai —
kal band ho sakti hai, isliye bot me **endpoint pool + auto rotate** hai.

### 🧩 Naye commands
```
/apis                                   — free + paid API list (rate ke saath)
/setkey serper KEY                      — Serper (2,500 free)
/setkey serpapi KEY                     — SerpApi (250/mo)
/setkey brave KEY                       — Brave ($5 credit/mo)
/setkey gapi https://...                — free Google endpoint pool me add
/setkey gapi -                          — pool clear
```
Admin panel → 🔑 **API KEYS** → 📋 **API LIST** button bhi hai.

### 🐞 Aur jo bugs mile (hunt ke baad)
- FILE ANALYZE me `%.0f/100` literal print ho raha tha (avg format nahi ho raha) — fix
- duplicate dead `UNIVERSAL_TEMPLATES` block (18 purani `{kw}` templates) — hata diya
- tutorial-video prompt bina timestamp ke set ho raha tha — `await_set` me aaya
- proxy screen ka unused `src_ok` — hata diya

### 🧪 Tests (workspace me, permanent)
```bash
cd ~/snake && python3 tests/test_core.py      # 154 assertions
python3 tests/test_screens.py                 # 19 screens: font/tag/4096 audit
python3 tests/repro_flows.py                  # scenario A/B/C repro
```

## ✨ v2.0 — STYLISH FONTS + FLOW LOCK

### 🔤 Har text ab theme font me
Pehle sirf **headings** styled thi, body plain thi. Ab:
- **Labels** → heading font (`ᴅᴏᴍᴀɪɴꜱ : 11`)
- **Prose** → italic font (`Country chuno — us desh ke domains me dorks banenge`)
- **Buttons** → button font (pehle se tha)

Function: `KV(label, value, emoji)` + `B()` + `P()`.
**Data kabhi styled nahi** — keywords/dorks/URLs plain rehte hain (copy-paste ke liye).

### 🔒 Flow lock — keywords ke bina dorks NAHI
Purane `dd:mode:*` buttons ab `DORKS GEN` pe redirect hote hain:
```
🎯 DORKER
  ├── ⚡ DORKS GEN      → Count → Keywords → dorks
  ├── 🚀 DORKS GEN PRO  → config → Count → Keywords → dorks (best template)
  └── 🌍 COUNTRY DORKS  → country → GEN DORKS → Count → Keywords
```
Koi bhi raasta keywords skip nahi karta.

### 🩺 Update confirm kaise kare
- `./update.sh` ab **version print** karta hai:
  ```
  📦 Version : v2.0  (6,xxx lines)
  ✅ Naya dorker (DORKS GEN + PRO) aa gaya
  ```
- `/ping` me: `📦 Core: v2.0`
- Main menu header me: `v2.0 • sirf kaam ka`

Agar `v1.8` ya purana dikhe → update nahi hua, dobara `./update.sh`.

## 🚀 v1.9 — DORKER PRO (templates system)

### 🎯 DORKER → 2 options
```
⚡ DORKS GEN        → Count → Keywords → ready dorks (universal templates)
🚀 DORKS GEN PRO    → poora template system (neeche)
🌍 COUNTRY DORKS    → 16 countries (.in .pk .us .uk .ru .de … .gov .edu)
```

### ⚡ DORKS GEN (normal)
Count poochta → keywords poochta → **40 universal templates** (har niche pe kaam karti hain):
`intitle:`, `allintitle:`, `intext:`, `inurl:`, `ext:`, `filetype:`, `site:`, `inurl:index of`, combos, params + numbers.
Ek keyword se **1000+ unique dorks**. Fresh button se naye.

### 🚀 DORKS GEN PRO — 10 buttons
| Button | Kya karta hai |
|---|---|
| 🌐 **Set Domains** | `.com .net .org .ru .de .in .pk .us .uk .info .gov` (aap jo bhejo) |
| 🔢 **Set URL Params** | `id, user_id, cat, type, page, item, product` |
| 📄 **Set Filetypes** | `.php .asp .aspx .jsp` |
| 🔍 **Set Search Filters** | `inurl: intitle: allinurl: allintitle:` |
| 📋 **Set Page Filters** | `index view page item product user login search show cat` |
| 🧩 **View Templates** | saari templates + har ek ko **ON/OFF** |
| 📊 **View Current Config** | poora status card + saari templates |
| 🧬 **Gen All Combos** | `email:pass` `cc` etc — add / remove / save |
| ♻️ **Reset to Default** | confirmation ke saath reset |
| 🎯 **GEN DORKS** | count → keywords → **best template** chun ke dorks |

### 🧩 Template engine (20 default + custom)
```
(KW)=keyword  (DE)=domain   (PF)=page-filter (PT)=param
(FT)=filetype (SF)=search-filter (NB)=number (CO)=combo
```
Default 10 (jaise purane bot me thay) + 10 naye HQ:
```
(KW).(PF)?(PT)=          (KW).(PF)?(PT)= site:(DE)
(KW).(PF)?(PT)=(NB)      (KW).(PF)?(PT)=(NB) site:(DE)
(SF)"(KW)" site:(DE)     (SF)(KW).(PF)?(PT)=
(SF)(KW).(PF)?(PT)= site:(DE)   (SF)(PT)=(KW).(PF)? site:(DE)
(SF)(KW).(PF)?(PT)=(NB)  (SF)(KW).(PF)?(PT)=(NB) site:(DE)
+ (SF)(KW) (FT) · (KW) (CO) · inurl:(KW)/(PF) · intitle:(KW) inurl:(PT)= …
```
**Config card** exactly jaise aapne dikhaya:
```
🌐 Domains  : 11 — .com .net .org .ru .de
🔢 Params   : 7 — id, user_id, cat, type, page
📄 Filetypes: 4 — .php .asp .aspx .jsp
✅ Enabled  : 20/20 templates
01. (KW).(PF)?(PT)= …
```

### 🌍 Country dorks
16 countries ready — `.in .pk .us .uk .ru .de .fr .br .id .ng .cn .tr .ae .sa .gov .edu`
Country chuno → domains set → `🎯 GEN DORKS` → `site:.in inurl:login` type dorks.

### 🧠 AUTO-DETECT — galat input pe saaf jawab
Bot khud pehchanta hai input kya hai:
`keywords · dorks · urls · domains · params · filetypes · sfilters · pfilters · combos`

```
❌ Ye keywords nahi hai — DORKS dijiye.
📥 Aapne bheja: 🎯 DORKS
✅ Chahiye   : 🔑 KEYWORDS — jaise shopify store, crypto wallet
```
Laga hua hai: **HQ KEYWORDS**, **PARSER**, **DORKER**, **INJECTOR**, **DUMPER**, **QUALITY**.

### 📊 QUALITY CHECKER — ab 3 type
| Type | Kya dekhta hai |
|---|---|
| 🔑 **KEYWORDS** | length, words, intent, repeat |
| 🎯 **DORKS** | operators, structure, quotes, deprecated |
| 🔗 **URLS** | params, tracking, junk host, dynamic page, injectable param |

Har report: avg + buckets (🔥80+ … 🔴<25) + top/worst + `80+ only` file + full scored txt.

### 🔑 REDEEM + 🎬 TUTORIAL + 🚧 ADMIN CONTROL
- **Home me 🔑 REDEEM KEY** button (admin button nahi — sirf `/admin`)
- **HELP me 🎬 HOW TO USE** button — admin panel se YouTube link set karo
- **Admin → 🚧 FEATURES ON/OFF** — koi bhi feature band karo + **apna message** likho
  ```
  🚧 PARSER
  ye feature abhi maintenance me hai
  ```
  ya `this feature have issue we are fixing` — jo likho wahi user ko dikhega.
  12 features: parser, dorker, keywords, reverse, injector, dumper, proxy, quality, randomizer, theme, file upload, redeem.
- Admin ko gate kabhi nahi lagta.

### 📦 NICHE PACKS (ready HQ seeds)
15 packs — click → count → keywords:
`crypto · email:pass · cc · ecommerce · admin panel · database · api · files · shopping · smtp · tools · leak · gov/edu · mobile/apk · hosting`

### ✨ Stylish fonts
Naye screens ke labels/headings bhi ab **theme font** me hain (`tag()` + `style()`),
sirf data plain rehta hai (keywords/dorks waise ke waise — warna copy-paste kharab hota).

## 🚀 v1.8 — HQ KEYWORDS v2 + 100K LIMIT + FRESH SYSTEM

### 🔑 HQ KEYWORDS — naya flow (seed YA apne keywords)
Pehle: seed do → bina poochhe tukke se keywords. **Ab:**

```
1) Seeds bhejo  →  shopify store, crypto wallet
   YA apne keywords paste karo (ek line me ek)
2) Count batao  →  1 – 100,000
3) Keywords mile →  scored + sorted + file
```

| Cheez | Pehle | Ab |
|---|---|---|
| 1 seed se kitne | **81** 😴 | **35,800+** |
| Keyword list do | "kuch nahi bana" | usi se **1 lakh tak naye** |
| Count poochta | ❌ | ✅ (max 1,00,000) |
| 1 lakh banane ka time | — | **0.06 sec** ⚡ |
| Quality report | ❌ | ✅ avg + buckets + top/worst |
| Result buttons | ❌ | 🎯 Dorks banao · 📊 Quality · 🔁 Aur (fresh) |

**Result screen:** 🎯 **DORKS BANAO** (keywords se real dorks),
📊 **QUALITY REPORT** (🔥80+ … 🔴<25 + `HQ only 80+` file), 🔁 **AUR** (naya fresh batch).

### 🎯 DORKER — naye modes + 1 lakh limit
```
📄 PAGE-TYPES   🗂 EXTENSIONS   🔧 PARAMETERS
🔗 INURL        🌐 SITE         🎯 NICHE
🎲 MIXED (HQ)   🆕 FRESH DORKS (purane skip)
```
- **🔗 INURL** — `inurl:product.php`, `allinurl:`, `inurl:"…"`, `inurl:?id=`
- **🌐 SITE** — domain/TLD bhejo (`gov.in`, `.pk`, `auto`) → `site:gov.in inurl:login` type dorks
- **Limit 5,000 → 1,00,000** (mixed 1 lakh = **1.1 sec**)
- 🆕 **FRESH mode** — pehle bane dorks skip, sirf naye → **fresh URLs**

### 🆕 FRESH SYSTEM (duplicate dorks khatam)
- Har bane dork **history me** jaata hai (`data/dork_seen.txt`, hashed)
- FRESH mode / "🆕 AUR FRESH" purane skip karta hai → **0 overlap**
- 1 lakh fresh dorks = **2.6 sec**
- `4,00,000` history par purane auto-trim
```text
/fresh            ← history stats
/fresh clear      ← reset (sab dobara naya)
```

### 📂 Keywords FILE bhejne par
Pehle: `KEYWORDS ➪ DORKS` + `INJECTOR` (hata diye ✅)
Ab: **📊 QUALITY CHECK** (score + `80+ only` file) aur **🔁 EXPAND** (count poochh ke aur banata hai)

### 📋 Purane bot se kya restore hua
Purane `bot_fixed.py` me ye keyword/dork features the — jo ab wapas hain:

| Purana feature | Ab kahan |
|---|---|
| `kw_get_count` (count step) | ✅ HQ KEYWORDS → count |
| `dork_get_keywords_file/text` | ✅ 🎯 DORKS BANAO (keywords se) |
| keyword quality checker | ✅ 📊 QUALITY REPORT + `80+ only` file |
| `parser_get_dorks_file` | ✅ file upload → 🚀 DEEP SCAN |
| `dump_get_dorks` / `dump_multiple` | ✅ 📦 DUMPER (txt/json/zip) |
| proxy bulk check | ✅ 🧅 PROXY ENGINE (400 parallel) |
| — | ➕ inurl/site modes, fresh system, free Google |

### ⚡ Speed (Termux par bhi tez)
| Kaam | Time |
|---|---|
| 1 lakh keywords | 0.06 s |
| 1 lakh dorks (mixed) | 1.1 s |
| 1 lakh dorks FRESH | 2.6 s |
| Quality report (1 lakh) | 0.34 s |

> `parse_deep` ka max URLs bhi **50,000 → 1,00,000** ho gaya.

## 🐦 v1.7 — FREE GOOGLE (ijerm, koi key nahi)

### Sabse pehle: ye chalta hai ya nahi? — **HAAN, chalta hai**
Live test kiya gaya (aapke diye endpoint par):

| Dork | Result |
|---|---|
| `shopping sites uk` | 18 URLs (real shops) ✅ |
| `inurl:admin.php` | 9 URLs (real admin panels) ✅ |
| `site:gov.in inurl:login` | **17/17 asli gov login pages** ✅ |
| `inurl:php?id= site:gov.in` | 10 URLs, sab gov.in ✅ |
| `inurl:/wp-content/uploads/` (6 pages) | 59 URLs ✅ |

- **Key nahi chahiye** — bilkul free, unlimited (throttle ke saath)
- Response ~2-5 sec
- **`pages=6` tak theek, `10+` pe timeout** → bot 6 pe clamp karta hai
- Error format: `{"status":"error","message":"..."}` — bot handle karta hai

### ⚠️ Imaandaar baat — limits
1. **Ye official Google API nahi hai.** Kisi ne apna Google scraper
   `ijerm.com/submit_article/book1/` pe public chhod diya hai. Kal band ho sakta hai.
2. **Dork quality Google pe depend karti hai:**
   - `site:` ke saath → **gold** (junk almost zero)
   - bina `site:` ke `inurl:`/`ext:` → bahut junk (youtube, reddit, stackoverflow)
   - Bot ka **`dork_match` strict filter** us junk ko kaat deta hai
3. **Rate limit** — bot 2.5 sec ka gap rakhta hai, 3 fail pe 5 min cooldown

### Bot me kahan laga
- **PARSER → DEEP SCAN** — har dork pe free Google try hota hai (budget: 40 dorks / 2 min)
- **PARSER → normal parse** — page 0 pe pehle free Google, phir 15 engines
- Deep card me naya row: **`🐦 Google (free): N`**
- Junk hosts (exploit-db, scribd, github, reddit, youtube…) auto-remove

### Command
```text
/gtest site:gov.in inurl:login
```
Live proof — URLs, speed, count sab dikhata hai. `/ping` me bhi status.

```text
/setkey gjerm -                      ← band karo
/setkey gjerm https://...            ← URL badlo (endpoint mar jaye to)
```

### 🧹 Bonus fix — tracking params
Google `srsltid`, `gclid`, `utm_*`, `fbclid` add karta hai — isse same URL
do baar aata tha aur dedupe fail hota tha. Ab `_clean_url` ye sab strip karta hai
(`?id=5` jaise kaam ke params safe hain).

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
