# 🕷️ SPIDEY BOT — POORA USER MANUAL (Roman Hinglish)

> Ye guide aapke bot ke **asli** buttons aur commands se banayi gayi hai.
> Sabse upar se padho — 10 minute me sab samajh aa jayega.

---

## 📑 INDEX

1. [Sabse pehle — 3 command](#1-sabse-pehle--3-command)
2. [Sirf 5 minute me pehla result](#2-sirf-5-minute-me-pehla-result)
3. [Main Menu — har button ka matlab](#3-main-menu--har-button-ka-matlab)
4. [SPIDEY-X PRO panel (asli engine)](#4-spidey-x-pro-panel-asli-engine)
5. [Engine Settings — kaunsa mode, kitne threads](#5-engine-settings--kaunsa-mode-kitne-threads)
6. [3 ready-made workflows (copy-paste karo)](#6-3-ready-made-workflows-copy-paste-karo)
7. [Commands cheat-sheet](#7-commands-cheat-sheet)
8. [Proxy — kyun chahiye, kaise daale](#8-proxy--kyun-chahiye-kaise-daale)
9. [License / Access](#9-license--access)
10. [Admin panel](#10-admin-panel)
11. [Problem → Fix table](#11-problem--fix-table)
12. [Termux tips + VPS deploy](#12-termux-tips--vps-deploy)
13. [Kya kar sakte ho / kya nahi](#13-kya-kar-sakte-ho--kya-nahi)
14. [Glossary — shabd samjho](#14-glossary--shabd-samjho)

---

## 1. Sabse pehle — 3 command

Termux kholo:

```bash
cd ~/spidey
./start.sh          # bot chalu
./logs.sh           # live log dekho (Ctrl+C se bahar)
```

Update karna ho:
```bash
cd ~/spidey && ./update.sh      # token + admin id safe rehta hai
```

Kuch gadbad lage:
```bash
cd ~/spidey && ./doctor.sh      # 8 point check — exact problem batata hai
```

Telegram me bot kholo → `/start` → menu aa jayega.

---

## 2. Sirf 5 minute me pehla result

Ye sabse aasan raasta hai. Bas ye karo:

```
/start
  ↓
🕷️ SPIDEY-X ENGINE ⚡  dabao
  ↓
🧠 Keyword Maker  dabao
  ↓
500  bhejo          (kitne keywords chahiye)
  ↓
stripe checkout, gaming topup   bhejo   (seed words)
  ↓
✅ 500 keywords ki .txt file aa jayegi
  ↓
⬅️ Back → 🎯 Dork Generator  dabao
  ↓
2000  bhejo        (kitne dorks chahiye)
  ↓
(jo keyword file mili thi — usse content copy karke paste karo, YA .txt file bhej do)
  ↓
✅ 2000 dorks ki .txt file
  ↓
⬅️ Back → 🌍 Deep Parser ⚡  dabao
  ↓
wahi dork .txt file bhej do
  ↓
⏳ Live counters chalenge — Done / Found / Unique / Speed / ETA
  ↓
✅ 2 files milengi:
     · All Unique URLs
     · ?param= URLs   ← ye sabse important
  ↓
⬅️ Back → 🛡️ SQLi Checker  dabao
  ↓
?param= wali .txt file bhej do
  ↓
✅ Vulnerable URLs ki list
```

Bas. Yahi poora dumping pipeline hai: **Keyword → Dork → URLs → Vulnerable URLs**.

---

## 3. Main Menu — har button ka matlab

### 🔥 Top section (naya engine — ye sabse pehle use karo)

| Button | Kya karta hai | Input chahiye |
|---|---|---|
| 🕷️ **SPIDEY-X ENGINE ⚡** | Poora naya engine — keyword, dork, parser, SQLi, settings | kuch nahi, seedha khulta hai |
| 🚀 **Auto-Pilot Pipeline** | Ek hi flow me: dork → URLs → SQLi → dump (3 modes: blitz / pro / beast) | dorks (text ya file) |
| 🧰 **Combo & URL Refinery** | File saaf karna — duplicate hatao, sirf `?param=` URLs chhaanto, email:pass nikalo | `.txt` file |

### 🧠 Keyword / AI section

| Button | Kya karta hai | Input |
|---|---|---|
| 🥇 **Generate Keywords** | Purana keyword generator (brand + intent mix) | pehle count (`5000`), phir seed words |
| 💎 **Kw Quality Check** | Keywords ki quality check — kitne UHQ hain, kitne bekaar | keywords paste ya `.txt` |
| 🧠 **AI Keyword Parser** | AI se keyword nikalo (OpenRouter/Gemini key chahiye — `/apikeys`) | niche / target text |

### 🎯 Dork section

| Button | Kya karta hai | Input |
|---|---|---|
| 🥈 **Generate Dorks** | Random SQLi dorks | pehle count, phir keywords |
| 🎖️ **Generate Dorks v2** | Pro dorks — file bhi accept karta hai, templates custom | count **YA** seedha `.txt`/`.zip` |
| 🪷 **HQ SQLi Dorks** | Payment/CC target wale high-quality dorks | count |
| 🌍 **Country Dorks** | 40 country TLDs wale dorks (`.in .br .tr .ru` …) | count |
| 🦨 **CMS Dorks** | WordPress / Joomla / OpenCart / Magento specific | count |
| 🌫️ **Exposed File Dorks** | `.env`, `.sql`, config, log files dhoondhne wale dorks | count |

### 🌍 Parser / Scraper

| Button | Kya karta hai | Input |
|---|---|---|
| 🥉 **Deep URL Parser** | Purana parser (Bing/DDG/Yandex/Vepar…) — SPIDEY-X se kam powerful | dorks |
| 🦠 **SQLi Scanner** | URLs ko SQL injection ke liye test karta hai | `?param=` URLs (file/paste) |

### 💣 Dump section (advanced — sqlmap wala kaam)

| Button | Kya karta hai |
|---|---|
| 💣 **Vuln URLs → ALL DATA DUMP** | Vulnerable URL do → poora database dump (tables, columns, data) + CC extract |
| 🪵 **Dorks → DB Dump** | Ek hi flow: dork → URLs → SQLi test → dump → CC |
| 🎢 **URLs → DB Dump** | Phase 1 skip — seedha URLs do, aage dump tak |
| 🛡️ **Auto SQLi chain** (settings me) | Parser khatam hote hi khud SQLi chala de |

### 🔑 Access / Info

| Button | Kya karta hai |
|---|---|
| 🔑 **Redeem Key** | License key daalo — `XXXXX-XXXXX-XXXXX-XXXXX` |
| 🍷 **Purchase Premium** | Plans + admin contact |
| 🚸 **How To Use?** | Andar hi guide hai — 4 topic (pipeline, dump, CC, sqlmap settings) |
| 🧛🏻 **Contact Owner** | Admin ka username |
| ⚜️ **Buy Source Code** | Source bechne ka page |
| 🛑 **Stop / Kill Tasks** | Chal rahe saare kaam band (`/killall` bhi) |

---

## 4. SPIDEY-X PRO panel (asli engine)

Ye panel 5 cheezein deta hai:

### 🧠 Keyword Maker
- **Step 1:** kitne chahiye? → `500` / `5000` / `50000` / `1lakh`
- **Step 2:** seed words bhejo — comma ya newline se alag, ya `.txt` file
- **Output:** exact count ki unique keywords (800 maango to 800 hi milenge, kam nahi)
- **Tip:** 2-3 seed best hote hain. `stripe checkout, gaming topup, netflix`

### 🎯 Dork Generator
- **Step 1:** kitne dorks? → `2000` / `20000` / `50000`
- **Step 2:** keywords paste/file
- **Output:** unique dorks, quality tiers ke saath
- **Tip:** 50,000 dorks ek baar me ban jate hain — phone pe 20k se zyada mat maango warna file bhaari

### 🌍 Deep Parser ⚡ (ye hi asli kaam karta hai)
- Dorks `.txt` file bhejo (ya chat me paste karo)
- 22 engines pe parallel chalega
- **Live card** ye dikhata hai:
  ```
  📥 Done: 3241/50000 dorks
  🔗 Found: 106885
  💎 Unique: 37054  •  🎯 param: 31000
  📈 URLs/dork: 11.4
  ⚡ Speed: 42 dorks/s
  🌊 Phase: Wayback/CC  ya  SERP engines
  [████░░░░░░░░░░░░] 6% • ETA 18m 40s
  ```
- **Output files:**
  - `V19_All_URLs_*.txt` — sab unique
  - `V19_Param_URLs_*.txt` — sirf `?param=` (ye SQLi ke liye)
  - `V21_CDX_*.txt` — Wayback/CommonCrawl wale

### 🛡️ SQLi Checker
- `?param=` URLs bhejo (file ya paste)
- Error-based + boolean test karta hai
- **Output:** vulnerable URLs + kitne % vulnerable mile

### ⚙️ Engine Settings
- Mode, Threads, Pages, Wayback ON/OFF, CC ON/OFF, Sig limit — niche section 5 me poora.

---

## 5. Engine Settings — kaunsa mode, kitne threads

### 🎚 Mode (sabse important setting)

| Mode | Engines/dork | Pages | Kab use karo |
|---|---|---|---|
| 🚀 **Fast** | 2 | 1 | **Termux**, kam data, jaldi test |
| ⚖️ **Balanced** | 4 | 2 | **Default** — Termux aur VPS dono pe best |
| 🌊 **Deep** | 6 | 2 | VPS, zyada URLs chahiye |
| 🔥 **Max** | 8 | 3 | VPS + proxies, maximum volume |

> Termux pe Deep/Max dabane par bhi bot khud cap kar deta hai (4 engines, 2 pages) — phone safe rehta hai.

### ⚡ Threads (kitne kaam ek saath)

| Button | Kiske liye |
|---|---|
| 🟢 Lite 24 | Purana phone, 2GB RAM |
| 🟡 40 | Normal phone (recommended Termux) |
| 🟠 60 | Acha phone / 4GB+ RAM |
| 🔵 100 | VPS small |
| 🔥 160 | VPS medium |
| ⚡ Auto | Bot khud decide kare (safe) |

### 📄 Pages
Har engine se kitne page nikale. `1` = fast, `2` = balanced, `3` = zyada URLs (slow).

### 🌐 Wayback / 🧠 CC
- **Wayback CDX** = archive.org se **purane** URLs → **sabse zyada volume**, sabse fast source
- **CC** = Common Crawl index → aur bhi purane URLs
- Dono ON rakho, warna aadha volume chala jayega

### 🎯 Sig limit
Ek hi URL template se kitne variants rakhe (8 = strict, 30 = loose, off = sab).
Zyada = zyada URLs par duplicate badhenge. `14` default best hai.

### ✅ Meri recommendation

**Termux (abhi aap):**
```
Mode: Balanced  •  Threads: 40  •  Pages: 2  •  Wayback: ON  •  CC: ON
```

**VPS (baad me):**
```
Mode: Deep  •  Threads: 100  •  Pages: 2  •  Wayback: ON  •  CC: ON  +  proxy
```

---

## 6. 3 ready-made workflows (copy-paste karo)

### 🅰️ Workflow A — Classic (beginner, sabse safe)
```
1. 🕷️ SPIDEY-X → 🧠 Keyword Maker → 1000 → seed words
2. 🎯 Dork Generator → 10000 → keywords paste
3. 🌍 Deep Parser → dorks file
4. 🛡️ SQLi Checker → ?param= file
5. (optional) 💣 Vᴜʟɴ URLs ➪ Dump → vulnerable file
```

### 🅱️ Workflow B — Domain Miner (fastest, competitor ke paas nahi)
```
1. /domainer shopify.com, mystore.com, target.com
2. → 4-5 second me hazaron purane ?param= URLs
3. 🛡️ SQLi Checker → wo file
4. 💣 Vuln URLs ➪ Dump
```
> Ye tab best hai jab aapko pata ho kaunse sites dumps karni hain.

### 🅲 Workflow C — File-based (jab dorks pehle se hain)
```
1. apni dorks .txt seedha bot me bhej do (koi button nahi dabana)
2. bot khud "Smart Detected" bol ke 1-click options dega
3. 🌍 Deep Parser chuno
4. aage same
```

### 🅳 Workflow D — Full Auto (jab time nahi hai)
```
🚀 Auto-Pilot Pipeline → mode chuno (blitz/pro/beast) → dorks do
→ khud parse + SQLi + dump kar dega
```

---

## 7. Commands cheat-sheet

### 👤 Sabke liye (user commands)

| Command | Kaam |
|---|---|
| `/start` | Main menu |
| `/v19` ya `/engine` | SPIDEY-X PRO panel seedha kholo (button ki zaroorat nahi) |
| `/ping` | Bot zinda hai? uptime, threads, admins |
| `/myid` | Aapki Telegram ID (admin ko dena ho to) |
| `/reset` | State atak gaya ho to clear |
| `/bench` | 6 dorks ka live test — speed + quality + 50k ka ETA |
| `/stats` | Engine leaderboard — kaunsa engine sabse zyada de raha hai |
| `/domainer site1.com, site2.com` | Wayback + CommonCrawl se bulk param URLs |
| `/stop` | Apne chal rahe kaam band |
| `/redeem KEY` | License key activate |
| `/proxies` | Apni proxy list dekho |
| `/setpr host:port:user:pass` | Ek proxy add karo |
| `/delpr` | Saari proxy hatao |
| `/autopilot` | Auto-pilot pipeline |
| `/cleaner` | Combo/URL refinery |
| `/emails` | Email extract |
| `/statuscheck` | URL live/dead filter |
| `/kwcheck` | Keyword quality check |

### 👑 Admin commands (ADMIN_IDS wale)

| Command | Kaam |
|---|---|
| `/admin` | Admin panel |
| `/myid` / `/adminid` | Apni ID / current admin list |
| `/genkey 7d` | License key banao (`30m 1h 1d 7d 30d lifetime`) |
| `/listkeys` | Saari keys |
| `/revokekey KEY` | Key band |
| `/adduser 123456789 7d` | User ko direct access do |
| `/removeuser 123456789` | Access hatao |
| `/banuser` / `/unbanuser` | Ban / unban |
| `/users` | Active users |
| `/broadcast message` | Sabko message |
| `/stats` | Engine stats |
| `/dstatus` | Dork config status |
| `/dconfig` | Dork config badlo |
| `/apikeys` | AI keys (Anthropic/Gemini/OpenRouter) |
| `/getfile` | Chalti hui bot file download (backup) |
| `/userfiles` | User files vault |
| `/livefeed` | Kaun kya kar raha hai live |
| `/checkproxies` | Proxy pool refill/check |
| `/setminproxy` | Min proxy target |
| `/checkuser 123456789` | Kisi user ki detail |
| `/killall` | Sab tasks band |
| `/vps` ya `/settings` | VPS + engine settings |

---

## 8. Proxy — kyun chahiye, kaise daale

**Kyun:** bina proxy 200-500 dorks ke baad Google/Bing aapko block kar deta hai → URLs aana band.
**Kab:** 5,000+ dorks wale run ke liye proxy zaroori hai. Chhote test me nahi.

### Add karna
```bash
/setpr 45.12.34.56:8080               # bina auth
/setpr 45.12.34.56:8080:user:pass     # auth ke saath
```

### Dekhna / hatana
```
/proxies     # list
/delpr       # sab clear
```

### Auto-scrape (admin)
```
/checkproxies      # pool check + refill
/setminproxy       # minimum kitne proxies rakhne hain
```

> 100 proxies daal do to 50,000 dorks bhi aaram se chalenge.

---

## 9. License / Access

- **Admin** = full access, kuch nahi chahiye
- **User** = license key ya trial chahiye

**Key kaise milega:**
1. 🍷 Purchase Premium se plan dekho
2. Admin se lo (`/genkey 7d`)
3. Main menu → 🔑 Redeem Key → key paste

**Key format:** `XXXXX-XXXXX-XXXXX-XXXXX`

> Trial bhi hota hai — bina key ke bhi kuch der chalta hai.

---

## 10. Admin panel

`/admin` se khulta hai. Sabse kaam ki cheezein:

| Button | Kab |
|---|---|
| 🔑 Generate Key | User ko access dena |
| 📛 Active Users | Kaun kaun hai |
| 📣 Broadcast | Sabko update bhejna |
| ☢️ FORCE KILL ALL | Kuch atak gaya ho |
| 🗂️ Get Bot File | **Backup** — apni file download kar lo (bahut kaam aata hai) |
| 🔄 Scrape & Validate | Proxy pool bharo |
| 👁️ Live Feed | Kaun kya chala raha hai |
| ⚙️ VPS & Engine Settings | Threads/mode |
| 📂 User Files Vault | Kisi user ki file dekho |

**💡 Golden rule:** har update ke pehle `🗂️ Get Bot File` se backup le lo. Kuch bhi ho, wapas laga sakte ho.

---

## 11. Problem → Fix table

| Problem | Karan | Fix |
|---|---|---|
| Bot jawab nahi de raha | Purani file / crash | `cd ~/spidey && ./doctor.sh` |
| Button dabane pe kuch nahi | Purana message ka button | `/start` dobara bhejo |
| `/ping` ka jawab nahi | Duplicate instance | `./stop.sh ; ./start.sh` |
| "Conflict: terminated by other getUpdates" | 2 bot chal rahe | `pkill -f bot_fixed.py ; ./start.sh` |
| Token invalid | Token revoke ho gaya | BotFather → `/revoke` → `./setconfig.sh` |
| Parser 0 URLs | Proxies dead / blocked | Mode `Fast` karo, proxy add karo, thodi der baad try |
| Parser bahut slow | Mode Max + bina proxy | `Balanced` + `40 threads` |
| URLs kam aa rahe | Wayback OFF, sig limit tight | Wayback ON, sig `14`+, pages 2 |
| File download nahi hui | Network blip | `/ping` chalao, phir dobara try |
| Battery khatam jaldi | 100+ threads phone pe | `Lite 24` ya `40` |
| Bot raat me band | Phone soya | Battery Optimization OFF + Wakelock ON |

---

## 12. Termux tips + VPS deploy

### Termux (abhi)

```bash
# 1. Wakelock (bahut zaroori)
termux-wake-lock

# 2. Bot chalao
cd ~/spidey && ./start.sh

# 3. Check
./status.sh
```

**Phone settings:**
- Settings → Apps → Termux → Battery → **Unrestricted**
- Termux notification → **Acquire wakelock**
- Charging pe chalao long runs me

### VPS (baad me)

```bash
apt update && apt install -y python3 python3-pip screen curl
git clone <your-repo> spidey && cd spidey
pip3 install python-telegram-bot aiohttp beautifulsoup4
# token + admin
nano bot_fixed.py     # line 68, 69
python3 bot_fixed.py
```

**VPS pe recommended:**
- Mode `Deep`, Threads `100-160`, Pages `2`
- 100+ proxy
- `screen -S spidey` me chalao (ya systemd)

**VPS pe expected speed** (proxy ke saath): 50,000 dorks ≈ 45-60 min.

---

## 13. Kya kar sakte ho / kya nahi

### ✅ Kar sakte ho
- 50,000 tak unique keywords (exact count)
- 1,000,000 tak dorks
- 22 engines pe parallel parse
- Wayback + CommonCrawl se purane URLs
- SQLi test + vulnerable list
- Full DB dump (sqlmap flow)
- Proxy ke saath bade scale run
- Resume (bot restart ho to jahan tha wahan se)

### ⚠️ Dhyan rakho
- Bina proxy 5,000+ dorks pe block hoga — ye bot ki galti nahi, engine ki limit hai
- Phone pe 160 threads = garam + battery drain
- Ek waqt me ek hi run — do run ek saath mat chalao
- Bahut bada dump phone pe nahi hoga — VPS chahiye
- File size: 100k+ URLs wali file Telegram pe bhejne me time lagega

### ❌ Nahi hota
- Real Google ko bypass karna bina proxy ke — possible nahi
- 0 dorks pe kaam — kuch to dena padega
- Purane message ke button se naya feature — `/start` fresh chahiye

---

## 14. Glossary — shabd samjho

| Shabd | Matlab |
|---|---|
| **Keyword** | Base word (jaise `stripe checkout`) |
| **Dork** | Search query jo specific pages dhoondhti hai (`inurl:product.php?id=`) |
| **URL** | Website ka address |
| **?param=** | URL me `?id=1` jaisa hissa — **yahi SQLi ka rasta hai** |
| **SQLi** | SQL Injection — database me ghusne ka tarika |
| **Unique** | Duplicate hatane ke baad bache URLs |
| **Raw** | Bina filter, jitne mile |
| **Engine** | Search engine (Google, Bing, Yandex…) |
| **Wayback CDX** | archive.org ka index — purane URLs |
| **Common Crawl** | Bada public web crawl index |
| **Sig limit** | Ek template se kitne URLs rakhe |
| **Threads** | Ek saath kitne kaam |
| **Fanout** | Ek dork pe kitne engines chalenge |
| **Sig** | URL ka pattern (domain + path + params) |
| **CC** | Credit Card (dumps me) ya Common Crawl — context se pata chalta hai |
| **Vault** | Bot ke andar file storage (backup) |
| **Trial** | Bina key ka test access |

---

## 🎯 Ek line me yaad rakho

> **Keyword → Dork → Deep Parser → `?param=` file → SQLi Checker**
> Yahi 5 step hai. Baaki sab inhe fast/automatic banane ke tools hain.

Kuch atke to:
```bash
cd ~/spidey && ./doctor.sh
```
Aur Telegram me `/ping` — bot zinda hai ya nahi, turant pata chal jayega.

---

*Manual version: SPIDEY-X PRO (v21) • Made for Termux-first usage*
