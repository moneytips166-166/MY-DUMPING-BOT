# 🐍 PYTHON SNAKE — POORA USER MANUAL (Roman Hinglish)

> Ye guide aapke bot ke **asli** buttons aur commands se banayi gayi hai.
> **Note:** install folder ka naam `~/spidey` hi rehta hai (purane users ka setup na tute) — folder purana, andar sab Python Snake.
> Sabse upar se padho — 10 minute me sab samajh aa jayega.

---

## 📑 INDEX

1. [Sabse pehle — 3 command](#1-sabse-pehle--3-command)
2. [Sirf 5 minute me pehla result](#2-sirf-5-minute-me-pehla-result)
3. [Main Menu — har button ka matlab](#3-main-menu--har-button-ka-matlab)
4. [PYTHON SNAKE panel (asli engine)](#4-python-snake-engine-panel-asli-engine)
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
🐍 PYTHON SNAKE ENGINE ⚡  dabao
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

v22 me menu **saaf** kar diya gaya hai — sirf wahi buttons jo sach me kaam karte hain.
Purana poora menu wapas chahiye to `/classic` bhej do.

| # | Button | Kya karta hai | Input chahiye |
|---|---|---|---|
| 1 | 🐍 **AUTO DUMP — 1 TAP FULL CHAIN** | Keywords → dorks → URLs → SQLi verify → report → files. Sab automatic. | seed words (text ya `.txt`) |
| 2 | 🧬 **UNIVERSAL DORK ENGINE** | Aapke keywords padh kar **khud** best dorks banata hai (CC-only nahi) | keywords (text ya `.txt`) |
| 3 | 🧅 **PROXY SCAN + AUTO-FILL** | Free proxies scrape + verify + pool me daal deta hai | kuch nahi |
| 4 | 🐍 **PYTHON SNAKE ENGINE ⚡** | Poora engine panel — keyword, dork, parser, SQLi, settings, logo | kuch nahi |
| 5 | 🔑 **Redeem Key** | License activate | key |
| 6 | 🍷 **Purchase Premium** | Plan kharidne ka contact | — |
| 7 | 🚸 **How To Use** | Chhota guide | — |
| 8 | 🧛 **Contact Owner** | Owner ka contact | — |
| 9 | 🛑 **Stop / Kill Tasks** | Chal raha kaam turant band | — |

> Jo purane 17 duplicate buttons the (purana dork gen, purana parser, purana dump, autopilot, refinery…) wo hide kar diye gaye hain — kaam wahi ab naye pipeline se hota hai. `/classic` se wapas dikh jayenge.

### Hide kiye gaye buttons (`/classic` se wapas)

| Button | Kyun hide | Ab kahan se karein |
|---|---|---|
| Generate Keywords | duplicate | Engine -> Keyword Maker |
| Kw Quality Check / AI Keyword Parser | bekar/extra | hide |
| Generate Dorks / Generate Dorks v2 | duplicate | Engine -> Dork Gen |
| HQ / Country / CMS / Exposed File Dorks | duplicate | Engine -> Dork Gen ya Universal Dorks |
| Deep URL Parser (purana) | duplicate | Engine -> Deep Parser |
| SQLi Scanner (purana) | galat results deta tha | Engine -> SQLi Checker (v2) |
| VULN URLs -> DUMP / Dorks -> DUMP / URLs -> DUMP | duplicate + unverified | AUTO DUMP |
| Auto-Pilot / Refinery / Source Code / Dedup | bekar | `/classic` se |

> Ye buttons **tute nahi hain** — bas menu saaf rakhne ke liye hide hain. `/classic` bhejte hi poora purana menu wapas aa jata hai.

## 4. PYTHON SNAKE ENGINE panel (asli engine)

Ye panel yahi deta hai: **Auto Dump • Keyword Maker • Dork Gen • Universal Dorks • Deep Parser • SQLi Checker • Proxy Scan • Settings • Brand/Logo**.

### 🐍 AUTO DUMP — 1 TAP (sabse aasan raasta)

Ek tap me poora chain:

```
seed words  →  300 keywords  →  1,000 dorks  →  40,000 URLs  →  150 URL SQLi verify  →  report + files
```

1. 🐍 **AUTO DUMP** dabao
2. Scale chuno — ⚡ Quick (1-3 min) / ⚖️ Standard (10-20 min) / 🌊 Deep (30-60 min)
3. Seeds bhejo — `stripe checkout, gaming topup` ya `.txt` (ek line = ek seed)
4. Bas. Live card chalta rahega, aakhir me 7 files aa jayengi:
   - `AUTO_Keywords_*.txt` — keywords
   - `AUTO_Dorks_*.txt` — dorks
   - `V19_All_URLs_*.txt` / `V19_Param_URLs_*.txt` — URLs
   - `V22_SQLi_VERIFIED_*.txt` — **sirf verified** vulnerable URLs (jisme sach me DB hai)
   - `V22_SQLi_REPORT_*.tsv` — url | dbms | columns | confidence | proof
   - `AUTO_REPORT_*.md` — poora summary

> ⚠️ **v22 ka sabse bada fix:** ab koi bhi URL "vulnerable" nahi kehlata jab tak 4-level proof na mile —
> SQL error → boolean diff → ORDER BY columns → UNION reflection.
> Jo page sirf length badalta hai (ads, random nonce, parked, static) wo **reject** ho jata hai.

### 🧬 UNIVERSAL DORK ENGINE (CC ke liye fix nahi)

Purane templates CC/payment ke liye bane the. Universal engine aapke keywords padh kar
niche pehchan kar (gaming / OTT / shopping / crypto / SaaS / hotel / education…) khud templates banata hai:
params, pages (`/api`, `/ajax`, `/admin`, `/panel`, `/checkout`…), extensions, inurl/intext combos.

- 5,000 / 20,000 / 50,000 / 1,00,000 dorks
- Purane CC templates waise ke waise hi hain (engine ke andar) — kuch tuta nahi

### 🧠 Keyword Maker
- **Step 1:** kitne chahiye? → `500` / `5000` / `50000` / `1lakh`
- **Step 2:** seed words bhejo — comma/newline, ya `.txt`
- **Output:** exact count ki unique keywords

### 🎯 Dork Generator
- Purane templates se dorks (CC/payment oriented)
- **Step 1:** count → **Step 2:** keywords

### 🌍 Deep Parser ⚡ (URL nikalne wala engine)
- Dorks `.txt` bhejo (ya paste)
- 22 engines parallel + Wayback CDX + Common Crawl
- **No-proxy mode bhi kaam karta hai** — proxy na ho to engine khud "safe engines" (Wayback/CC/direct) pe shift ho jata hai, isliye 0 URLs wala problem khatam
- Output: `V19_All_URLs_*.txt`, `V19_Param_URLs_*.txt`, `V21_CDX_*.txt`

### 🛡️ SQLi Checker (v2 — no fake results)
- `?param=` URLs do (paste ya file)
- 4 level proof, confidence score:
  - `60` = SQL error match
  - `80` = boolean differential (1=1 vs 1=2)
  - `88-90` = ORDER BY column proof
  - `95` = UNION reflection (data nikalne layak ✅)
- Default minimum `60` — usse neeche kuch report nahi hota
- Files: `V22_SQLi_VERIFIED_*.txt` + `V22_SQLi_REPORT_*.tsv`

### 🧅 Proxy Scan (v2 — ab sach me kaam karta hai)
- `/proxyscan` ya panel ka button
- 6 lenient check targets (JSON + HTML dono chalte hain) → free proxies bhi pass hote hain
- Pool file: `data/v22_proxy_pool.json` (24 ghante TTL)
- Self-healing: jo proxy 2 baar fail hua wo usi run me blacklist, 3 fail pe pool se delete
- Proxy se page na aaye to URL **direct dobara** check hota hai — isliye asli vuln miss nahi hota

### 🐍 Brand / Logo
- Panel me **🐍 Brand / Logo** ya command `/brand`
- Logo image + bot branding info (BotFather me kaise set karo)

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

## 6. Ready-made workflows (copy-paste karo)

### 🅰️ Workflow A — AUTO DUMP (naya, sabse aasan)
```
1. 🐍 AUTO DUMP — 1 TAP FULL CHAIN
2. Scale: ⚡ Quick (1-3 min)
3. Seeds bhejo: stripe checkout, gaming topup
4. Bas — 7 files aa jayengi (keywords, dorks, URLs, VERIFIED vuln, report)
```

### 🅱️ Workflow B — Universal Dorks (jab niche CC nahi hai)
```
1. 🧬 UNIVERSAL DORK ENGINE → 20,000
2. Keywords bhejo: netflix premium, spotify family
3. File mil jayegi → Engine → 🌍 Deep Parser me daal do
4. Aage AUTO DUMP jaisa hi (SQLi verify → report)
```

### 🅲 Workflow C — Domain Miner (sabse fast, competitor ke paas nahi)
```
1. /domainer shopify.com, mystore.com, target.com
2. 4-5 second me hazaron purane ?param= URLs
3. Engine → 🛡️ SQLi Checker → wo file
4. Verified list milegi (sirf asli DB wale)
```

### 🅳 Workflow D — Manual control (jab sab khud karna ho)
```
1. Engine → 🧠 Keyword Maker → count → seeds
2. Engine → 🎯 Dork Gen → count → keywords
3. Engine → 🌍 Deep Parser → dorks file
4. Engine → 🛡️ SQLi Checker → ?param= file
5. (optional) /classic → 💣 VULN URLs ➪ DUMP → poora database
```

### 🅴 Workflow E — File bhej do (smart detect)
```
1. apni dorks .txt seedha bot me bhej do (koi button nahi)
2. bot "Smart Detected" bol kar 1-click options dega
3. 🌍 Deep Parser chuno → aage same
```

---

## 7. Commands cheat-sheet

### 👤 Sabke liye (user commands)

| Command | Kaam |
|---|---|
| `/start` | Main menu |
| `/v19` ya `/engine` | PYTHON SNAKE panel seedha kholo (button ki zaroorat nahi) |
| `/brand` ya `/logo` | Logo + branding card |
| `/proxyscan` ya `/pxscan` | Proxy scan + auto-fill (v2) |
| `/proxystat` ya `/px` | Proxy pool ka status |
| `/proxyclear` ya `/pxclear` | Pool clear |
| `/classic` | Poora purana menu ON/OFF |
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

### Pehle samjho: proxy ka kaam kya hai
Google/Bing/DDG ek hi IP se hazaron query aane par **block** kar dete hain (captcha ya khaali page).
Proxy = aapki request kisi doosre computer se jaati hai, isliye block nahi lagta.
**Competitor jo "inbuilt proxy" bolte hain** — wo bhi yahi karte hain: apne server ke proxies rotate karte hain.
Ab aapke bot me wahi cheez built-in hai.

### 3 tarike (upar wala sabse aasan)

**1. Auto-scan (recommended)**
```
/proxyscan        # free proxies scrape + verify + pool me daal dega
/proxystat        # kitne alive, kitne fast
/proxyclear       # pool khaali
```
Ya menu me: 🧅 **PROXY SCAN + AUTO-FILL**

**2. Apne paid proxies (best quality)**
```
/setpr 45.12.34.56:8080               # bina auth
/setpr 45.12.34.56:8080:user:pass     # auth ke saath
```

**3. Proxy ke bina bhi chalega**
- v22 me **no-proxy safe mode** hai: proxy na ho to parser khud Wayback CDX, Common Crawl
  aur kam-block wale engines pe shift ho jata hai → **0 URLs wala problem khatam**.

### v22 me kya fix hua
| Purana problem | Ab |
|---|---|
| Free proxy "dead" dikhta tha (exact string match) | 6 lenient targets — JSON ya HTML, koi ek chale to LIVE |
| Dead proxy pool me pada rehta tha | 2 fail = usi run me blacklist, 3 fail = pool se delete |
| Proxy ne galat page diya to URL miss ho jata tha | wahi URL **direct dobara** check hota hai |
| /checkproxies sab reject kar deta tha | naya verifier use hota hai |

> 100+ proxies = 50,000 dorks bhi aaram se. 10-20 proxies bhi kaafi improvement dete hain.

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

*Manual version: PYTHON SNAKE (v22) • Made for Termux-first usage*
