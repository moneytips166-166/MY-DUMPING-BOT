# 🐍 SHADOW X — v3.0 (fixed build)

> `shadow/new.py` — ek hi file ka Telegram bot: **keywords → dorks → parser → injector → dumper**.
> Purane SHADOW X code ke saare known bugs fix, UI/UX bilkul main `bot.py` jaisa.

## ⚡ Install (Termux)

```bash
pkg update -y && pkg install -y python screen

cd ~/snake             # jahan tumhara main bot + update.sh hai
bash update.sh         # bot.py + shadow/ (aur /storage/emulated/0/shadow) dono update

cd /storage/emulated/0/shadow
bash restart.sh
```

`update.sh` khatam hone par khud batata hai: `🐍 SHADOW X ready: <folder>`.
Agar `~/snake` me `update.sh` na ho to pehle dhoondo:

```bash
find ~ -maxdepth 3 -name update.sh 2>/dev/null
```

## 🔑 Token + Admin (default set hai)

Bina kuch kiye chal jayega — `new.py` me ye default hai:

| | Value |
|---|---|
| Token | `8897685033:AAEDffs29JBrS1VYyl5ao9wWFrh64Tgscz8` |
| Admin / Owner | `8937044612` · **@Bloody_sweet_baby** |

Badalna ho (recommended — token chat me share ho chuka hai):

```bash
# permanent override — shadow/shadow_config.json
{"token": "NAYA_TOKEN", "admins": [8937044612]}
```

Ya temporary:

```bash
export SHADOW_TOKEN="123456:ABCDEF..."
```

Priority: `SHADOW_TOKEN` env → `shadow_config.json` → `new.py` ka default.
`shadow_config.json` gitignored hai — repo me kabhi nahi jaata.

## ▶️ Chalana — do tarike

**A) DBF me (recommended, main bot ke saath):** `new.py` `/storage/emulated/0/DBF/` me
rehta hai, control scripts `~/snake/` me:

```bash
cd ~/snake
bash restart2.sh     # shadow restart
bash stop2.sh
bash status2.sh
bash update2.sh      # sirf shadow update
bash bots.sh         # dono bots ka status
```

**B) alag shadow folder se:**



```bash
cd /storage/emulated/0/shadow

bash start.sh      # background me start
bash status.sh     # chal raha hai ya nahi
bash restart.sh    # fresh restart (purana session saaf)
bash stop.sh       # band
bash run.sh logs   # live log
```

> ⚠️ **`./start.sh` mat likho** — `/storage/emulated/0` `noexec` mount hota hai,
> isliye `Permission denied` aata hai. `bash start.sh` likhne se chalta hai.
> (`~/snake` jaisi internal storage me `./start.sh` bhi chalta hai.)

`./update.sh` (main repo me) shadow folder ko **khud update** karta hai —
`~/MY-DUMPING-BOT/shadow` aur `/storage/emulated/0/shadow` dono me.
Token purane `new.py` se auto-migrate ho jata hai (`shadow_config.json`).

Manual (agar chahiye):

```bash
screen -S shadow
python3 new.py
# detach: Ctrl+A phir D  |  wapas: screen -r shadow
```

## 🎛 Commands

| Command | Kaam |
|---|---|
| `/start` / `/menu` | main menu |
| `/ping` | version + build + uptime |
| `/help` | feature list |
| `/id` | aapka Telegram ID |
| `/admin` | owner panel (sirf admins) |
| `/stop` | aapke saare running tasks band |
| `/redeem SHX-XXXX-XXXX` | key activate |

## 🧅 Proxy system (pool + rotating)

`🧅 PROXIES` button ya `/proxy`:

| Button | Kaam |
|---|---|
| ➕ ADD PROXIES | text / `.txt` — `host:port`, `http://u:p@host:port`, `socks5://…` |
| ✅ CHECK MINE | saari proxies ka live test, dead hata do |
| 📋 LIST / 📤 SEND FILE | pool dekho / file me lo |
| 🧹 CLEAN | dead nikaal ke pool chhota karo |
| ⚡ HUNT 500 | free proxy list scrape + live filter |
| 🌀 ROTATING | **admin only** — ek endpoint jo har request pe IP badle |
| ⚙️ USE ON/OFF | proxy engine band/chalu |

Parser · Injector · Dumper · QC — **sab** is pool se chalte hain. Dead proxy par
request automatic **direct retry** ho jaati hai, isliye kaam rukta nahi.

## 🧭 Menu

| Button | Kaam | Rang |
|---|---|---|
| 🚀 FULL PIPELINE | dorks → parse → inject (auto) | 🟢 |
| 🧠 HQ KEYWORDS | seed → 500+ UHQ keywords | 🔵 |
| 🧬 DORKER | param dorks (up to 50,000) | 🔵 |
| 🌐 PARSER | 10 engines se URLs | 🔵 |
| 💉 INJECTOR | error / boolean / time SQLi | 🔵 |
| 📥 DUMPER | DB → tables → columns → rows | 🟢 |
| 📥 DUMPER → 🐍 SQLMAP | sqlmap se dump (optional) | 🟢 |
| 🎯 QUALITY CHECK | URL scoring (0–100) | 🔵 |
| 🛡 WAF LAB | WAF detect + bypass mode | 🔵 |
| 🕸 SUBFINDER | crt.sh se subdomains | 🔵 |
| 🧅 PROXIES | pool + rotating + hunt | 🔵 |
| ⚙️ SETTINGS | threads / pages / engines / param-only | 🔵 |

**Rang ka rule:** 🟢 green = kaam shuru/kare, 🔴 red = band/khatam/delete, 🔵 blue = navigation/info.
Purane Telegram clients par rang ignore hoga — button normal dikhega, kaam same.

## 🕷 Engines

`DDG · Bing · Yahoo · Brave · Mojeek · Ecosia · Ask · Yep · Google · Yandex`

Settings me toggle — ek dork pehle engine se try hota hai, block mile to agla.

## 📂 Resource files (tumhare folder wale)

`shadow/` me ye files rakho to bot **inhi se** dorks/keywords banata hai
(na milne par built-in pool):

| File | Kya |
|---|---|
| `sites.txt` | `site:` list |
| `keywords.txt` | seed keywords |
| `page_types.txt` | `product.php`, `news.php` … |
| `page_parameters.txt` | `id`, `cat`, `page` … |
| `patterns.txt` | dork patterns (`{site}`, `{keyword}`, `{page_type}`, `{page_parameter}`, `{search_function}`) |

Dorker screen par `Sources: patterns 20 · sites 40 · kw 500` dikhega.

## 🐍 SQLMAP (optional)

Native **📥 DUMPER** ko sqlmap ki zaroorat nahi. Bada/blind dump chahiye to:

```bash
pip install sqlmap
```

Phir **📥 DUMPER → 🐍 SQLMAP** button (max 10 URLs, `--dbs --dump`).
Status: `/sqlmap`. VPS par zyada tez chalta hai.

## 🗄 Files

| Path | Kya |
|---|---|
| `shadow/data/*.json` | settings, users, tasks, keys, proxies (auto) |
| `shadow/dumps/` | keywords / dorks / urls / vulns / sqldump `.txt` |
| `shadow/shadow.log` | `./run.sh logs` |

## 🔧 Purane code ke jo bugs fix hue

| Bug | Fix |
|---|---|
| `send_photo_cached` infinite recursion | recursion hata diya, cache clean |
| `WAF_SIGS` dict → list redefine (`.items()` crash) | ek hi definition |
| `_last_saver` / `_auto_saver` duplicate | ek-ek baar |
| state dict race / galat unpack | `RLock` + `await_set/get/clear` |
| `bkey_txt` days vs `license_until` hours mismatch | `days × 86400` |
| `make_key` vs `bkey_txt` key format mismatch | ek format: `SHX-XXXX-XXXX` |
| `ENABLE_MIDDLEWARE` deprecated | hata diya |
| bot restart pe task gum | `data/tasks.json` |

## 🧪 Test (network ke bina)

```bash
cd ~/MY-DUMPING-BOT
./tests/run.sh
# ya sirf shadow:
SHADOW_NO_RUN=1 python3 tests/test_shadow.py
```

`SHADOW_NO_RUN=1` = sirf import + screens/handlers check, polling start nahi hoti.

## ⚠️ Note

Dumper native Python engine par chalta hai (error-based extraction). Bade/Time-based
dumps ke liye VPS par `sqlmap` behtar hai — `VPS_GUIDE.md` dekho. Sirf apni ya
permission wali sites par use karo.
