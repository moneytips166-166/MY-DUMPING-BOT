# 🐍 SHADOW X — v3.0 (fixed build)

> `shadow/new.py` — ek hi file ka Telegram bot: **keywords → dorks → parser → injector → dumper**.
> Purane SHADOW X code ke saare known bugs fix, UI/UX bilkul main `bot.py` jaisa.

## ⚡ Install (Termux)

```bash
pkg update -y && pkg install -y python screen

cd ~/MY-DUMPING-BOT
./update.sh            # bot.py + shadow/ (aur /storage/emulated/0/shadow) dono update

cd shadow              # ya: cd /storage/emulated/0/shadow
pip install -r requirements.txt
```

## 🔑 Token

Do tariqe — dono chalte hain:

```bash
# 1) env se (temporary)
export SHADOW_TOKEN="123456:ABCDEF..."

# 2) file se (permanent) — shadow/shadow_config.json
{"token": "123456:ABCDEF...", "admins": [8937044612]}
```

`shadow_config.json` gitignored hai — token repo me nahi jaata.

## ▶️ Chalana (sirf screen se — main bot jaisa)

```bash
cd /storage/emulated/0/shadow

./start.sh      # background me start
./status.sh     # chal raha hai ya nahi
./restart.sh    # fresh restart (purana session saaf)
./stop.sh       # band
./run.sh logs   # live log
```

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
| 🧅 PROXIES | hunt + live check | 🔵 |
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
