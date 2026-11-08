# 🐍 PYTHON SNAKE CORE — v2.18.0

**Sirf kaam ka bot.** Koi faaltu cheez nahi, koi mockup nahi — sab real.

---

## 📥 v2.18.0 — "20,000 diye, alag amount test hua" ka asli karan + naya UI

### 🔎 Root cause (sab fix ho gaya)

| # | Kahan | Kya ho raha tha | Fix |
|---|---|---|---|
| 1 | precheck `_ping_one` | phone ka resolver load me ho to `Temporary failure in name resolution` aata hai — usse host **DEAD** maan liya jata tha | temporary failure = **ZINDA**; sirf NXDOMAIN / refused / no-route = dead, 3 attempts |
| 2 | precheck valve | ek hi glitch me **hazaaron URL chup-chaap gir** jate the (card par sirf "Dead sites 3" dikhta) | agar **>35% URLs** dead lagein to kuch bhi nahi girta (`precheck_valve`) |
| 3 | mid-scan host kill | 4 fail par host dead → baaki cases `skip`, par wahi URL "tested + safe" me gin liya jata tha | hard-error only, 6 fail, mass-skip guard; skipped URL **na tested na safe** |
| 4 | `inj_probes_for` | category mode me **`base[:14]`** — sqli ke 63 payloads me se **49 kabhi chalte hi nahi the** | poori list + per-URL **rotation** = poore list par saare payload cover |
| 5 | `_run_inject` + `_urls_from_text` | count se **pehle** dedupe → "Total" hi kam dikhta tha | raw lines count hoti hain; duplicate alag line par |
| 6 | final card | "URLs received" precheck ke baad ka number tha | **Total / Duplicates / Unique / tested / dead-skip** — sab alag |

**Harness proof (asli `inj_scan`, 20,000 URLs, network stub):**

| Scene | v2.17 | v2.18 |
|---|---|---|
| 20,000 unique (6 host) | 20,000 | **20,000 tested** |
| 20,500 lines (500 duplicate) | 20,000 (chup) | **20,500 total · 500 dup · 20,000 unique · 20,000 tested** |
| aadhe hosts par temporary DNS fail | **10,042 tested** (9,958 gayab) | **20,000 tested** |
| 100% connection refused | 0 tested | 13,364 tested + **6,636 dead-site URLs card par** |

> Sum check hamesha: `tested + dead-skip = unique`. Koi URL bina batae nahi girta.

### 🖥 Injector UI (naya)
```
📥 Total URLs     : 20,000      ← user ne jitne diye (sites nahi, URLs)
🔁 Duplicates     : 500
🌐 Unique URLs    : 19,500
🌐 URLs tested    : 19,300
💉 Vulnerable     : 12
✅ Safe           : 19,288
⚡ Speed          : 41.2 URLs/s
⏱ Time           : 7m 48s
💀 Dead-site URLs : 200  🏠 14 site(s)
```
- Live card: `URLs x/y · Vulnerable · Safe · Speed URLs/s · ETA` — **requests aur live-hosts nahi** (backend me chalte rehte hain).
- `safe_<cat>.txt` bhi aati hai (pehle sirf vulnerable).

### 🔍 Parser UI (naya)
- Live: **Raw URLs · Unique URLs · Target · Speed dork/s · Time left** — attempts / blocked / engines / proxies hata diye.
- End card: sirf **Dorks scanned · Raw URLs · Unique URLs · Yield · Time · Files** — engine health / proxy / filtered counters backend me (diagnostics sirf 0-URL case me).
- End files: **`raw_*.txt`** (har raw hit, duplicate ke saath, 2 lakh line cap) + **`deep_*.txt`** (unique) + stats.
- `parse_raw_cap` = 200,000 (phone RAM safe), `raw_truncated` flag stats me.

### 🧪 Engine audit (asli local HTTP app par, mock nahi)
| Engine | Result |
|---|---|
| Injector | ✅ SQLi (MySQL), XSS, LFI, SSTI, Open Redirect — sab detect; clean page FP-free |
| SQLi Dumper | ✅ local SQLite app: UNION + blind dono se tables/columns/rows |
| Parser | ✅ extraction/crawl/dedup tests pass; **search engines ke liye internet chahiye** (sandbox me sirf GitHub/npm) |
| Baseline FP fix | sqli / ssrf / graphql ab baseline body se compare karte hain |

### 🗑 Faltu features (hataye ja sakte hain)
1. **45 proxy sources + DoH scrape** — injector/dumper pe default OFF hai hi; phone pe sirf time khaate hain. Sirf `/admin` me rakho (ab bhi wahi hai).
2. **"Live hosts" / "Requests" counters** — user ko kabhi kaam ke nahi lage, hata diye (backend me hain).
3. **8 themes** — 2 (Dark + Mono) kaafi hain; baaki sirf confusion.
4. **`waf` probe family** — dork-list pe yield almost zero; sqli/union se overlap.
5. **GraphQL/NoSQL probes** default `all` me hain — normal dork lists pe 95% waste. Category mode me rakho.

### ➕ Kaam ki missing cheezein (priority order)
1. **TSP dorking tool ka zip (`tsp_exctrated`)** — repo/upload dono me nahi mila. Bhejo to uske templates/variables/keywords 1:1 merge kar dunga.
2. **Resume/checkpoint** — 100k list beech me ruk jaye to dobara 0 se na chale (`done_urls` ab save kar sakte hain).
3. **Per-host throttle** — ek hi host par 24 probes bhejne se WAF block; 2 req/s/host cap.
4. **`/batch` me probe-per-URL** (`inj_targets`) ka button — abhi admin command se.
5. **SERP key pool** — 3-4 free keys rotate → parser yield 3x.
6. **Vuln URL dedupe by (host, param, type)** — file me same site ke 40 rows aate hain.

---

## 📥 v2.17.0 — 24k URLs: poore chale, precheck live, STOP sach me rukta hai

### Screenshot wali teen dikkatein
| Kya dikha | Asli karan | Fix |
|---|---|---|
| File me **24552 URLs**, card **LINES: 20,000** | `FILE_MAX_LINES = 20000` — reader wahin ruk jata tha | cap **300,000** |
| **Sites 0/2,000** | `_urls_from_text(limit=2000)` | `URL_MAX = 200000` (**koi cap nahi**) |
| **0/2000, Requests 0/0** par atka | host pre-check chup-chaap chalta tha — har host ke liye **naya session**, koi progress nahi | live progress + ek hi session |
| **STOPPING… hamesha** | pre-check me stop flag **check hi nahi hota tha** | STOP ab pehle second se kaam karta hai |

### Pre-check ab
```
SCANNING ALL • pre-check
◆ Sites   : 24,552 URLs
◆ Hosts   : 843 / 6,120  (checked)
◆ Step    : dead sites hata rahe hain — phir probes shuru
⛔ STOP isi step me bhi turant kaam karta hai.
```
- ek hi `aiohttp` session (phone pe halka, 3-5x tez)
- **time cap** `inj_precheck` (default **45s**) — jo host check nahi hua use **zinda**
  maan liya jata hai, **koi URL nahi girta** (card me `⚡ Pre-check cap hit` likha aata hai)

### 24k URLs par memory
Pehle har URL ke saare probes ek list me bante the (24k × 16 = ~4 lakh tuples →
phone hang). Ab **feeder** streaming karti hai bounded queue me.
Test: 6,000 URLs → 24,000 probes → **12.7s, RSS 78 MB**.

### Honest counts
- `📥 URLs received: 24,552`
- `🌐 URLs scanned: 12,480 (clean …)`
- `💀 Dead hosts skipped` · `⏱ Host pre-check`
- file card ab **asli line count** dikhata hai

Tests: **907/907** · screens 37 clean · pyflakes 0

---

## 🧅 v2.16.0 — proxy sirf PARSER me (injector/dumper direct)

### Pehle kya tha
| Tool | Proxy | Problem |
|---|---|---|
| PARSER | ON (auto/off/on) | ✅ sahi — engines ko naya IP chahiye |
| INJECTOR | `inj_proxy` (default 0 = off) | ✅ theek, par card me dikhta nahi tha |
| **DUMPER** | **auto ON jitni proxy pool me thi** | ❌ **bug** — dump toot raha tha |

### Dumper me proxy kyun galat tha
SQL dump (union/blind extraction) me **har request ka jawab pichhle request pe**
depend karta hai — same session, same IP, same cookies. Free rotating proxy
**har request naya IP** deta hai → columns/tables ka jawab aadha-aadha aata hai,
dump fail. Isliye:

- **Dumper ab DIRECT** (`ProxyRotator(enabled=False)` by default)
- chahiye to admin: `/batch dumpproxy 1`
- PAGE HARVEST bhi direct
- DUMPER card me saaf likha: `🧅 Proxy: OFF — direct (dump me session same rehna zaroori hai)`

### Injector
- proxy default **OFF** (`/batch injproxy 1` se on)
- INJECTOR card me dikhta hai: `🧅 Proxy: OFF — direct (fast + blocks nahi)`
- result card me bhi: `🧅 Proxy: OFF — direct`
- 25 proxy fail par khud direct ho jata hai (pehle se tha)

### Fark
- Dump pehli baar poora aata hai (rows/tables adhoora nahi)
- Injector tez + false positive kam (2nd-request confirm same IP par hota hai)
- Parser waise hi proxy use karta hai (wahan zaroori hai)

Tests: **894/894** · screens 37 clean · pyflakes 0

---

## 🏆 v2.15.0 — URLs bhi utne hi: dorks × N (yield mode)

### Problem
Raw hits 10x dikh raha tha, par **unique URLs sirf ~2x** — kyunki har dork par
**sirf 1 request** hoti thi (pehla engine result deta hi loop break). 10,000 dorks
× 1 request × ~50 results = 5 lakh raw, par dedupe ke baad ~20k unique.

### Ab — YIELD MODE
| Kya | Kaise |
|---|---|
| **1 request par nahi rukta** | har dork ko baari-baari **extra sources** milte hain: har engine × har page |
| **Target** | `dorks × N` URLs (default **5x**, button se 3x/5x/10x/20x) |
| **Breadth-first** | pehle sab dorks ko 1 request, phir sab ko 2nd source, phir 3rd… (isliye koi dork peeche nahi chhootta) |
| **Guard** | ek dork par max `engines × pages` requests (fast mode: 3×3 = 9) |
| **Saturation** | 120 requests me 5 se kam naye URL → matlab SERP khatam, wahin ruk jata hai (battery/time bachta hai) |
| **Honest card** | `🏆 Yield: 4.8x · target 5x = 50000 URLs` + `Target reached / SERPs saturated / target se kam` |
| **Pages default 3** | bingr RSS 50/page → ek dork se 150 tak |

### Parser settings me naya button
```
🏆 URL TARGET: 5x   |   📄 PAGES: 3
🧵 THREADS: 12
```
Tap = 3x → 5x → 10x → 20x. Jitna zyada, utna lamba scan (budget ke andar).

### Sach
SERPs me overlap hota hai. 10,000 dorks × 10x = 1,00,000 unique URLs sirf tab
milte hain jab engines itna alag-alag dein. Bot ab **poori koshish** karta hai
(har dork ko 9 sources tak), saturation par ruk jata hai aur **sach batata hai** —
jhoothi 10x nahi likhta. 5x practically har baar mil jata hai.

Tests: **865/865** · screens 37 clean · pyflakes 0

---

## 🎯 v2.14.0 — "30-40 dork chale aur 10000/10000 dikha diya" (FIXED)

### Asli bug
Purane parser me engine ko **3 miss par permanently "dead"** mark kar diya jata tha.
Uske baad har dork ka loop turant khatam ho jata tha — **koi request nahi**, par
counter `scanned` badhta rehta tha. Isliye 30-40 asli dork ke baad baaki 9,960 dork
milliseconds me "scan" ho jate the aur card **10000/10000 (100%)** dikha deta tha.

### Ab (coverage mode)
| Kya | Kaise |
|---|---|
| **Har dork ek asli request** | pass 1 = har dork par kam se kam 1 engine request (round-robin healthy engine) |
| **Khaali dork chhoote nahi** | pass 2 = jis dork se kuch nahi mila, uspe 2 engine aur |
| **Engine permanently dead nahi** | 4 block ke baad sirf **90s rest**, phir wapas (auto) |
| **Block par rasta badalta hai** | proxy se block → **direct** try, direct se → **proxy** (auto-heal) |
| **Jhooth nahi** | `scanned` = asli requests hui dorks, `skipped` = jo attempt hi nahi hua |
| **Progress** | `1234 / 10000 dorks (pass 1/2)` + `Attempts: real requests` |
| **CONTINUE** | jitne bhi dork bache (time up / engine block / stop) — button hamesha |

### Card ab aisa dikhta hai
```
Scanned: 37/10000 dorks
Not attempted: 9963  (engines blocked — CONTINUE dabao)
Real requests: 74
Raw URLs: …
Unique URLs: …
```
`Finished ✅ all 10000 dorks scanned` **sirf tab** jab sach me sab ho gaya ho.

### Speed
10,000 dorks × 1 request, 12 parallel workers → ~10-15 min (pehle: ya to 3 dork/s
burn karke 2 min me jhooth, ya ghante). Budget (60 min) ke andar poora scan.

Tests: **842/842** · screens 37 clean · pyflakes 0

---

## 🧨 v2.13.1 — "update hi nahi hua" + token loss (asli karan)

### 1) Token har update par kyun jata tha
| Kya ho raha tha | Fix |
|---|---|
| bot 4 jagah config dhoondhta tha aur **pehli jo mile** use karta tha — khaali token wali file pehle mil jati thi | ab **valid token wali config jeetti hai**, khaali file sirf fallback |
| `_save_config()` khaali token ko **DBF config me bhi copy** kar deta tha → token hamesha ke liye gaya | save se pehle guard: token khaali ho to disk/backup se wapas, **khaali token kabhi likha hi nahi jata** |
| updater pehli baar config banate waqt `"bot_token": ""` likh deta tha (bot.py me placeholder hota hai) | updater ab token ke bina config **banata hi nahi**; mil jaye to repair karta hai |
| `_migrate_config()` sirf backups dekhta tha | ab **saari config files + env + backups** — jo mile wahi wapas |

### 2) "Update nahi hua" — asli karan: download block
`raw.githubusercontent.com` India me kai ISPs pe block hota hai. Purana updater sirf wahi (aur `github.com/raw`, jo wahi redirect hai) try karta tha → **download fail → purana bot chalta rehta tha**.
Ab har file **4 tarike** se aati hai:
1. `raw.githubusercontent.com`
2. `github.com/.../raw/...`
3. **`api.github.com` contents** (raw accept header)
4. **`codeload.github.com` tarball** → `tar` se extract

`update.sh` bootstrap bhi wahi 4 tareeke use karta hai (`SNAKE_BOOT_V=6`).

### 3) "screen already exists" / ek se zyada sessions
- `snake_lib.sh` **v6**: saare `snake*` sessions (`9999.snake`, `snake_old`, `snake_stale`) band, `screen -wipe`, `.snake.lock` clear (HOME/DBF/current), phir start
- naam clash ho jaye to **unique session name** (`snake_<timestamp>`) — "already exists" ab kabhi rukta nahi
- single-instance lock: doosra bot `⚠️ BOT ALREADY RUNNING` bol kar exit
- updater har baar saari scripts overwrite karta hai (sanity check ke saath)

### 4) File deliver nahi ho rahi
- `send_file` ab **2 baar** try karta hai (slow Termux network), aur fail hone par chat me **reason + file path** likhta hai — chup-chaap fail nahi hota
- trial lock owner ko kabhi nahi rokta (`OWNER_IDS` hamesha admin)

### 5) Update hua ya nahi — ab saaf dikhta hai
`/ping` me:
```
📦 Core: v2.13.1
📁 File: bot.py  v2.13.1
🗂 Folder: /data/data/com.termux/files/home/snake
```

Tests: **821/821** · screens 37 clean · pyflakes 0

---

## 🛡️ v2.13.0 — token loss + duplicate sessions (pakka fix)

### 1) Har update par token remove ho jata tha
| Kya galat tha | Fix |
|---|---|
| `_migrate_config()` ne ek baar `snake_config.json` **khaali token** ke saath bana diya | config me token invalid mile to **khud repair** — `_recover_from_backups()` se token wapas, `_save_config()` se likha jata hai |
| repaired file dobara kharab na ho | repair branch har start par chalta hai (valid token ho to kuch nahi badalta) |
| `./update.sh` config ko chhoota hi nahi | `snake_config.json` sirf **read** hoti hai — token/admin delete nahi hote |

Log me dikhega: `🔧 config repaired — token wapas set`.

### 2) `./restart.sh` → "screen already exists"
| Kya galat tha | Fix |
|---|---|
| phone pe purani/tuti scripts (naye version se pehle ki) | bot khud **v5 scripts** install/overwrite karta hai: `snake_lib.sh`, `start.sh`, `stop.sh`, `restart.sh`, `status.sh`, `update.sh` |
| `screen -dmS snake` pehle purana session band nahi karta tha | `snake_kill_all()` pehle **saare `snake*` sessions + bot pids** band karta hai, `screen -wipe`, lock clear — phir fresh `snake_start` |
| update ke baad bhi purani script | `vps/termux_update.sh` **UPDATER_V=5** — khud `snake_lib.sh` source karke wahi flow chalata hai |

### 3) Ek se zyada sessions / 409 conflict
- `.snake.lock` single-instance lock — doosra `bot.py` chalte hi saaf message ke saath exit:
  `⚠️ BOT ALREADY RUNNING (pid …)` → `./stop.sh` ya `./restart.sh`
- lock `atexit` + crash path dono pe release hota hai (stale lock nahi banta)

### Update karna
```bash
cd ~/snake
./update.sh
./restart.sh
```
Telegram me `/ping` → `v2.13.0 (build self-heal+lock)`.

Tests: **801/801** · screens 37 clean · pyflakes 0

---

## 🚀 v2.11.0 — parser / injector / dumper ke asli bugs + naya URL reverse

### 1) Parser — sirf bing chalta tha
| Kya galat tha | Fix |
|---|---|
| DDG GET pe challenge page (200 OK) deta tha, uske 5 nav links "results" ban jaate the | DDG ab **POST** form se (asli results), challenge page detect hota hai |
| `ddgl` extractor page ke **saare** links uthata tha | sirf `result-link` rows |
| bing ke alawa kuch reliable nahi | **mojeek** + **marginalia** add, sets: fast 3 / normal 5 / max 9 |
| "kaun sa engine chala" pata nahi | card me **🔎 engine health** — ✅ bing 15,669 · ❌ ddg (captcha) |

### 2) Parser — 5000 dorks me se sirf 492 scan hue
- **Asli karan:** dorks ek-ek karke chalte the (engine parallel tha, dork nahi)
- Ab **dork-level parallel workers** (default **6**, settings se 2–8)
- Speed: local test 40 dorks 5.27s (7.6 dork/s) — pehle ~0.27 dork/s
- Time khatam hone par **▶️ CONTINUE — N dorks left** button (resume)
- Card me `🧵 Parallel dorks: 6`

### 3) Injector — 1.8 req/s aur 59,832 "tested"
| Kya galat tha | Fix |
|---|---|
| Har URL ke cases alag `gather` — ek slow URL poore batch ko rokta tha | **flat queue** + N workers (40 default) |
| Free proxies default ON (90% dead → har request timeout) | proxy **default OFF** (`/batch injproxy 1` se on), 25 fail par auto-direct |
| "Tested 59,832" = requests, user ne URLs samjha | card ab **URLs 162/7,425** + **Requests 1,312/59,832** alag |
| 40 vuln / 162 URL = 24% false positive | sirf **asli SQL error phrases**, baseline diff, **2nd request confirm** |
| SSTI: "49" har page me | probe `{{1337*1337}}` → `1787569` |
| LFI: "bin/bash" har docs page me | `root:x:0:0:` jaisa asli marker |
- Local benchmark: **480 requests / 0.7s = 686 req/s**, 20/20 asli vuln, **0 false positive**

### 4) Dumper — injector 5 bola, dumper 3
- Karan: dumper apni alag detection dobara chalata tha
- Ab dumper card: **💉 Injector confirmed · ✅ Dumped · ⏭ Needs sqlmap**
- INJECTOR ke result me **📁 DUMP THESE N URL(s)** button (param bhi saath jata hai)
- `df:vuln` pehle se tha, ab consistency line bhi

### 5) Naya: URL REVERSE → **vulnerable URL se UHQ dorks** (bina keywords)
```
URL REVERSE → 💉 VULNERABLE URL → UHQ DORKS
https://site.com/product.php?id=12
```
- same file + same param: `inurl:"product.php?id="`
- same folder shape: `inurl:shop/product.php?id=`
- same extension: `inurl:product.php ext:php`
- sibling files: `inurl:item.php?id=` (16 common names)
- country suffix sirf restricted (`site:.gov.in`), `.com` jaisa broad nahi
- error-page dorks: `intext:"You have an error in your SQL syntax" inurl:product.php`
- **koi keyword nahi** — sirf structure

Tests: `test_core` **732/732** · `test_screens` **37 clean** · pyflakes 0

---
## 🎯 v2.12.2 — Bing se zyada + saaf results

| Change | Detail |
|---|---|
| Bing RSS volume | `count=50` (pehle 30) + `mkt=en-US` → ek page se **50 results** |
| RSS pagination | step `50` — page 2 la 40-50 naye URLs deta hai |
| Default pages | **2** (pehle 1) — same dork se double results, threads 12 hone se time same |
| Redirect unwrap | `bing.com/ck/a?...u=<base64>` se **asli URL** nikalta hai — pehle ye junk me chala jata tha |

Tests: **773/773** · screens 37 clean · pyflakes 0

---
## 🧹 v2.12.1 — sirf proxy-safe engines (baaki hata diye)

User rule: *"jo rotating proxy pe block na de aur achha results de, sirf wahi rakho."*

**Rakhe (5):**

| Engine | Kyun |
|---|---|
| **bingr** (Bing RSS) | Pure XML, koi captcha/JS nahi — sabse pakka |
| **bing** (HTML) | Proxy ke saath results deta hai |
| **mojeek** | Apna independent index, koi bot-protection nahi |
| **ddgl** (DDG lite) | Plain HTML form, proxy-safe |
| **yahoo** | Bing ka data, simple page |

**Hata diye (7+):** google, yandex, brave, startpage, qwant, ecosia, marginalia,
sxng (searx), ddg-html — ye free/rotating proxy IP par **captcha** dete hain.
Yahi "sirf bing chalta hai" ka karan tha.

**Aur bhi:**
- `AUTO engine-proxy` = proxy ho to sab proxy se (naya IP = kam block), warna direct
- Parser threads default **12** (max 24)
- Engine Doctor ab sirf bache engines ke fix dikhata hai
- Time budget default **60 min**

Tests: **765/765** · screens 37 clean · pyflakes 0

---
## 🌐 v2.12.0 — "sirf bing chalta hai" ka asli fix

**Kya galat tha:** parser ke paas sirf 3-7 engine the aur unme se google/yandex
bina proxy pakka block. Proxy ON hone par bhi google block — kyunki **Google free
proxy/datacenter IP ko hamesha block karta hai**. Isi liye sirf bing bachta tha.

| Fix | Detail |
|---|---|
| **Bing RSS** | `bingr` = `format=rss` — JS/captcha nahi, kabhi block nahi. Ab fast/normal dono me |
| **SearXNG** | 9 public instances rotate — Google+Bing+DDG ka result ek jagah |
| **+3 engines** | startpage · qwant · ecosia (kul 13) |
| **AUTO engine-proxy** | jo engine proxy se **ulta block** hote hain (bingr/mojeek/ddgl/ddg) wo **direct**; sirf google/brave/startpage/yandex ko proxy |
| **Engine Doctor** | `PARSER → 🔬 ENGINE DOCTOR` — har engine ka status + **fix** + google ka sach |
| **Proxy truth** | parser card me: kitne request proxy se gaye, pool kitna alive, kitne fail |
| **Proxy bootstrap** | pool khaali ho to admin ke parser chalane par khud scrape+check (45s) |
| **Injector pre-check** | 7,425 URLs ke dead hosts pehle hatao (yahi 1.8 req/s ka karan tha) |
| **Honest counters** | "Sites" vs "Requests" alag, live hosts count |
| **Injector → UHQ** | result card me `🔗 VULN → UHQ DORKS` button (injector ke vulnerable URLs se) |

### `./restart.sh` — naya (phone pe purana tuta hua tha)
Repo me `restart.sh/start.sh/stop.sh/status.sh/snake_lib.sh` **the hi nahi** —
isliye phone pe purana version "bot pehle se chal raha hai" bol ke ruk jata tha.
Ab `./update.sh` ye 5 files **khud install** karta hai, aur restart purane
process ko SIGTERM → SIGKILL karke fresh start karta hai.

### Google ke liye 2 sachche raste
1. **SERPER free key** — 2,500 searches free, card nahi → `/apikeys`
2. **Bina proxy** apni mobile IP se free Google endpoint (parser card me)

Tests: **test_core 771/771** · **test_screens 37 clean** · pyflakes 0

---
## 🪄 v2.10.0 — naye menu emoji + Premium ANIMATED emoji

### Menu emoji (main screen)
| Tool | Emoji |
|---|---|
| HQ KEYWORDS | 🔑 (same) |
| DORKER | 🧬 |
| PARSER | 🌐 |
| URL REVERSE | 🔗 |
| INJECTOR | 💉 (same) |
| DUMPER | 📁 |
| QUALITY CHECK | 📊 (same) |

Baaki sab same — niches 🧩 (taaki DUMPER ke 📁 se mix na ho).

### Premium (animated) emoji — REAL support
- `snake_config.json` me `premium_emoji: {slot: custom_emoji_id}` — update-safe
- Message text me `<tg-emoji emoji-id="...">🔑</tg-emoji>` ban jata hai → **animated**
- **Bot API 9.4+:** bot owner ke paas **Telegram Premium** ho to allowed (Fragment username ki zarurat nahi)
- Telegram reject kare to bot **khud normal emoji** pe switch — message kabhi fail/silent nahi
- ⚠️ Button labels me custom emoji Telegram support **nahi** karta — wahan unicode emoji hi rahenge

### Kaise set karo (do tarike)
1. **Forward trick (easy):** koi bhi animated-emoji wala message bot ko forward karo → bot ID khud nikaal ke slot buttons deta hai → tap → done
2. **Command:** `/se` (list) · `/se dork 5368324170671202286` · `/se dork off` · `/se test`
- Admin panel me bhi: **🪄 PREMIUM EMOJI (animated)** → test animation
- ID manually chahiye to: message ko **@JsonDumpBot** ko forward karo → `custom_emoji_id`

### Safety
- `/ping` me: `🎨 Premium emoji: N set · ON/OFF`
- Premium fail → auto fallback (edit + reply + button screens teeno me)
- Tests: `test_core` **704/704** · `test_screens` **37 clean** · pyflakes 0

---
## 🔐 v2.9.9 — token/admin update me kabhi delete nahi

**Asli bug:** `BOT_TOKEN` aur `ADMIN_IDS` `bot.py` ke andar the, aur `./update.sh` poori `bot.py` replace karta hai — isliye har update pe token ud jata tha.

| Fix | Detail |
|---|---|
| Config bahar | `snake_config.json` (bot.py ke saath) — isko update **kabhi touch nahi** karta |
| Load order | env `BOT_TOKEN` → `snake_config.json` → `bot.py` default |
| Auto-migrate | Purani install (token andar) pehli baar chalte hi khud config bana leta hai |
| Auto-recover | Token kisi purane update me ud gaya ho to `backups/bot_*.py` + DBF se wapas nikaal leta hai (token + admin dono) |
| Update guard | `./update.sh` replace se **pehle** purane `bot.py`/backups se token nikaal ke config bana deta hai |
| `setconfig.sh` | Naya: `--show` (masked), `--token`, `--admin`, `--addadmin` |
| `/ping` | `🔐 Config: snake_config.json · admins N` line |
| Security | `snake_config.json` `.gitignore` me + chmod 600 (repo me kabhi nahi jata) |

---
## 🔎 v2.9.8 — build verify + 409 fix + one-command update

| Cheez | Detail |
|---|---|
| `/ping` build proof | `🧩 Build: guard+fast+kw+cfg` · `🛡 Silent-guard: ✅ ON` · `💉 payloads: 8` · `⚙️ parser-cfg: ✅ ON` · `🕒 Loaded: <time>` — turant pata chal jata hai naya code chal raha hai ya purana |
| 409 Conflict | Start pe webhook check + auto-delete; polling 409 pe saaf Hinglish message (doosra instance kahan chal raha hai, kaise band kare) |
| Silent guard | Ab **import pe hi** patch hota hai — pehle start ke baad; /ping me sach dikhta hai |
| `./update.sh` | **Self-updating** — script khud ko bhi latest karta hai, phir bot.py (Termux + `/storage/emulated/0/DBF`) + restart |
| Restart | Purane process ko **SIGTERM** (graceful) → wait → SIGKILL; start ke 6s baad verify, fail par log |
| Same-folder guard | `~/snake == DBF` ho to copy skip (same-file error nahi) |
| Tests | `test_core` **634/634** · `test_screens` **37 clean** · pyflakes 0 |

---
## 🩹 v2.9.7 — silent-kill fix, fast injector, better keywords, parser settings

| Cheez | Detail |
|---|---|
| Silent kill | Har button ab **kuch na kuch** dikhata hai. Callback me exception → `OOPS` card + menu button (pehle chup-chaap mar jata tha). Tap par turant toast |
| HTML safety | Telegram HTML reject kare to message **plain text** me retry — "kuch nahi hua" wala sabse bada karan khatam |
| Dead button | `HOW TO USE (video)` ab alert deta hai (pehle dead tha) |
| Injector speed | Payloads **19 → 8 main** · body sirf 64 KB padhta hai (pehle poori page) · params 3 → 2 · default parallel 40 · per-URL tests 24. Local test: **240 req/s** |
| Injector bug | `raw` variable shadow ho raha tha — vulnerable URL me page body aa rahi thi. Fixed |
| Keywords | Generator pattern-major + core-shift (pehle ek hi pattern repeat hota tha). 1 seed se bhi **20k+**, 3 seeds pe pattern mix. Dorks bhi template-mix |
| Parser settings | Naya `⚙️ PARSER SETTINGS` — **Pages · Threads · Timeout · URL limit · Engines** (tap = next value), user khud badal sakta hai |
| Parser speed | Engines ab **parallel** (threads setting se bounded) — pehle ek-ek karke chalta tha |
| Paste fallback | Chat me URL/dork paste karo → bot detect karke buttons deta hai: scan / SQL dump / harvest / parse |
| Tests | `test_core` **620/620** · `test_screens` **37 clean** · pyflakes 0 |

---
## ⚠️ v2.9.6 — Large data guard (dump VPS pe, bot sirf batata hai)

| Cheez | Detail |
|---|---|
| Detect | Table list cap se zyada ho, ya kisi table ki `COUNT(*)` inline cap se bada ho, ya request budget khatam ho → **LARGE DATA FOUND** |
| Behaviour | Rows grind nahi karta — sirf columns + preview deta hai, phir **saaf vulnerable URL** deta hai |
| Message | `⚠️ LARGE DATA FOUND — <reason>` + target URL + ready command: `sqlmap -u "<url>" -p <param> --batch --dump --threads 4` |
| File | `large_targets_*.txt` — saari large URLs ek line me (sqlmap me seedha daal do) |
| Report | `!! LARGE DATA FOUND` block report ke andar bhi (copy-paste URL + command) |
| Kahan chalaye | Full dump VPS pe (`/opt/snake`) — phone pe sirf test/preview |
| Termux update | `cd ~/snake && ./update.sh` → `~/snake/bot.py` + `/storage/emulated/0/DBF/bot.py` dono update + screen restart (`vps/termux_update.sh`) |
| Tests | `test_core` **567/567** (asli 40-row table pe large guard test) · `test_screens` **37 clean** |

---
## 🗄 v2.9.5 — Dumper = real SQL data dump (URL pe databases → tables → columns → rows)

| Cheez | Detail |
|---|---|
| Kaam | URL do → engine khud injectable param dhoondta hai → **database → tables → columns → rows** nikaalta hai. Har row asli response se aati hai, koi mock nahi |
| Detection | 8 quote/comment styles. TRUE (`AND 1=1`) vs FALSE (`AND 1=2`) page ka **character-level diff** — isliye `Results: 1` vs `Results: 0` wale pages bhi pakde jate hain |
| Techniques | 1) **UNION** (column count ORDER BY se, phir printed column) 2) **error-based** (MySQL duplicate-key) 3) **boolean-blind** (binary search, ~7 request/char) 4) **time-based** detect (extraction skip — phone pe bahut slow) |
| DBMS | MySQL · SQLite · PostgreSQL · MSSQL · Oracle — dialect-wise queries (`information_schema`, `sqlite_master`, `STRING_AGG`, `LISTAGG`) |
| Blind mode | Page kuch print na kare to bhi tables + columns nikal aate hain. Rows blind me default OFF (`/batch dumpblindrows 5` se on) |
| Output | Per-URL `.txt` report (DB, tables, columns, rows) + `sqldump_rows_*.csv` (saari rows) + poora **zip** |
| Caps | `/batch dumptables 15` · `/batch dumprows 50` · `/batch dumpreq 800` · `/batch dumpblind 0|1` · `/batch dumpconc 4` · `/batch dumptime 12` |
| Honest | Jo URL injectable nahi hai, report me exact reason aata hai. Jahan rights/WAF block kare, wahan "table list empty" likha hota hai — jhooth nahi |
| Dumper menu | `📥 SEND URLS — FULL SQL DUMP` · `💉 LAST VULNERABLE URLS` · `📥 LAST PARSER URLS` · `🕸 PAGE HARVEST (forms/links/secrets)` |
| Tests | `test_core` **553/553** — asli local sqlite app pe union dump + blind dump test · `test_screens` **37 clean** |

---
## 🎯 v2.9.4 — Injector = real SQLi/NoSQL/XSS/LFI/SSTI/SSRF scanner, Dumper = page harvester

| Cheez | Detail |
|---|---|
| Injector flow | Click → **URLs maango** (screen khulte hi input armed). Paste many URLs **or send .txt/.csv/.json/.xlsx** — all URLs used |
| Categories | Saare 11 categories + ALL — same payload bank (311) preserved, probes selection ab live scan chalata hai |
| Real scan | Har URL ka har parameter: payload inject → response parse. **Koi mock nahi** — SQL error / reflection / traversal / template eval / metadata leak |
| Families | SQLi (error-based, union, blind, WAF-bypass), NoSQL, GraphQL, XSS, LFI, SSTI, SSRF, Open Redirect |
| Progress bar | **Apna style** — `⠋ ⟦▓▓▓░░░░⟧ 62%` + URLs / tested / vulnerable / blocked / speed / ETA + ⛔ STOP. Parser wale bar se alag |
| Result | `⚠️ N vulnerable URL(s) found` ya `🛡 No vulnerabilities found` + **Total tested** + row 100% + by-type + top hits |
| Files | `vuln_*.txt` — sirf **plain vulnerable URLs** (payload nahi) · `vuln_report_*.csv` — type, dbms, param, status, url, poc, evidence |
| Dumper flow | Click → URLs maango (text ya file). **Last parser URLs** aur **last scan ke vulnerable URLs** ek tap me |
| Dumper extract | Forms (action/method/inputs) · parameters · endpoints · JS files · emails · HTML comments · table/column names · **API keys / DB URLs / JWT** |
| Dumper output | Har URL ki alag `.txt` report + `summary.csv` + `summary.json` + poora pack ek **zip** |
| Proxy | Rotating proxy pehle, phir pool — scan aur dump dono me |
| Speed controls | `/batch injtargets 36` · `/batch injconc 30` · `/batch injtime 8` · `/batch dumpconc 12` · `/batch dumptime 10` |
| Tests | `test_core` **500/500** (asli local HTTP server se live scan test) · `test_screens` **36 clean** |

---
## 🩺 v2.9.3 — Termux DNS fix (proxy "Could not contact DNS servers")

| Fix | Detail |
|---|---|
| Resolver | Sab connectors ab **ThreadedResolver** (system DNS) — Termux me aiodns fail hota hai |
| DoH fallback | `p.webshare.io` resolve na ho to **1.1.1.1 / 1.0.0.1 / 8.8.8.8 / 9.9.9.9** se DoH |
| Proxy connect | Domain ki jagah **IP se connect** (creds same) — ISP DNS block bhi bypass |
| Test card | DNS line + direct net line + 110-char errors + specific hint |
| Naya command | `/dnstest p.webshare.io` — system DNS vs DoH |

---
## 🔁 v2.9.2 — Rotating proxy (Webshare / koi bhi) support

| Cheez | Detail |
|---|---|
| Endpoint formats | `host:port:user:pass` · `user:pass@host:port` · `http://user:pass@host:port` · `socks5h://user:pass@host:port` |
| Add kahan | `/rotproxy p.webshare.io:80:USER-rotate:PASS` ya `/admin → PROXY SCRAPE → 🔁 ROTATING PROXY` |
| Test | `/rotproxy test` — 3 requests ke IP + DDG Lite se dork test |
| Priority | Rotating endpoint har request pe use hota hai (har baar naya IP), pool proxies backup |
| Cooldown | Rot endpoint 10s rest (dead nahi), pool proxy 180s |
| Storage | `data/rot_proxy.txt` + settings (password repo me nahi) |

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
| 📁 **Niches** — `HQ KEYWORDS → 📁 MY NICHES → ➕ ADD NICHE` (ready packs hata diye), 40 max, menu me button | ✅ NEW |
| 💉 **Injector 311 payloads** — 11 cats incl. blind/UNION/WAF/NoSQL/GraphQL, **240 DBMS patterns (21 DBs)** | ✅ |
| 🔑 **HQ keywords** — 16 verb + 20 qual + 20 noun + geo layers, 1M cap, ~38k unique per core | ✅ |
| 🧅 **Proxy scrape admin-only** — user panel me bilkul nahi (`/admin` → PROXY SCRAPE); ➕ ADD PROXIES (14+ formats) + rotation | ✅ |
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
