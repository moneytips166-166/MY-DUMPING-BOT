# 🐍 PYTHON SNAKE — VPS COMPLETE GUIDE (phone se VPS tak, 24/7)

Ye guide **shuru se end tak** hai: naya VPS → packages → phone se file upload → bot run → 24/7 → update → backup → troubleshooting.

---

## 📁 Directory map (saari guide isi structure pe hai)

| Cheez | VPS path (example) | Phone path |
|---|---|---|
| Bot code | `/opt/snake/bot.py` | `/storage/emulated/0/DBF/bot.py` |
| Settings (users, keys) | `/opt/snake/data/settings.json` | `/storage/emulated/0/DBF/data/settings.json` |
| Rotating proxy (webshare) | `/opt/snake/data/rot_proxy.txt` | `/storage/emulated/0/DBF/data/rot_proxy.txt` |
| Manual proxy list | `/opt/snake/data/manual_proxies.txt` | `/storage/emulated/0/DBF/data/manual_proxies.txt` |
| Dumps (txt/json) | `/opt/snake/dumps/` | `/storage/emulated/0/DBF/dumps/` |
| Logs | `/opt/snake/logs/bot.log` | `~/snake/bot.log` |
| Backups | `/opt/snake/backups/` | `~/snake/backups/` |
| venv (python libs) | `/opt/snake/.venv/` | — |

> Bot ka folder **kahin bhi** rakh sakte ho (`SNAKE_DIR=/home/ubuntu/bot`), par guide me `/opt/snake` use kiya hai.

---

## ✅ Part 0 — VPS se kya chahiye (5 min)

Provider panel (Hostinger / Contabo / DigitalOcean / Hetzner / any) se ye 3 cheez copy karo:

1. **IP address** — jaise `103.21.44.10`
2. **root password** (ya SSH key)
3. **OS** — Ubuntu 22.04 / 24.04 ya Debian 12 ✅ (ye guide inke liye hai)

**Bas itna hi kaafi hai.** Bot ko koi port open nahi karna, koi domain nahi chahiye — Telegram ko outbound internet chahiye, jo default me hota hai.

**VPS size:** 1 vCPU / 1 GB RAM / 10 GB disk bilkul kaafi hai (bot ~120 MB RAM leta hai, parse pe 250–400 MB).

---

## 🆓 Part 0.5 — FREE 24/7 hosting (kaun saas lena hai)

Dumper ko chahiye: **long-running process** + **outbound 80/443** + **persistent
disk** (data/ aur dumps/). Serverless aur "sleep" wale platforms isme fail hote hain.

| Platform | 24/7 | Dumper | Card | Sach |
|---|---|---|---|---|
| **Oracle Cloud Always Free** (ARM Ampere) | ✅ | ✅ best (4 OCPU / 24 GB) | ✅ ₹2 hold | Signup reject common; Mumbai/Hyderabad region me ARM capacity kabhi "out of capacity" |
| **Google Cloud e2-micro** (us-central1/1/e) | ✅ | ✅ | ✅ | 1 GB RAM tight (dump pe 400 MB tak), US IP = zyada WAF block |
| **AWS free tier** | ⏳ ~6 mahine | ✅ | ✅ | Ab "always free" nahi — 12 mahine wala purana scene khatam |
| **Purana Android + Termux** | ✅ (charger laga rehna) | ⚠️ slow par chalta hai | ❌ | **Mobile IP sabse kam block hota hai** — scanning ke liye best stealth |
| PythonAnywhere free | ✅ | ❌ outbound whitelist | ❌ | Free plan sirf whitelisted hosts — dumper dead |
| Render / Railway / Fly / Koyeb / Replit / Heroku | ❌ sleep ya credit khatam | ❌ | — | Polling bot ke liye useless |
| Vercel / Supabase (serverless) | ⚠️ | ❌ 10–60 s limit | ❌ | Dump minute bhar chalta hai — timeout |
| HuggingFace Spaces | ⚠️ idle sleep | ⚠️ ToS risk | ❌ | Scanning ke liye recommend nahi |

**Order:** Oracle → GCP → purana phone.

> ⚠️ Datacenter IP (Oracle/GCP) par Cloudflare zyada block karta hai. Ghar/mobile IP
> par block kam hota hai — isliye phone se scan "better" result deta hai, VPS se
> **uptime** better milta hai. Dono ka combo best: phone se scan, VPS pe 24/7.

---
## 📲 Part 1 — Phone se VPS me SSH (2 min)

Termux kholo:

```bash
pkg update -y && pkg install openssh -y
termux-setup-storage          # permission popup → Allow
```

VPS me login (pehli baar `yes` likhna padega):

```bash
ssh root@103.21.44.10          # apna IP daalo
# password maange to VPS ka root password paste karo (type nahi dikhta, normal hai)
```

Login ho gaya to prompt aisa dikhega: `root@vps:~#`

**Chhota shortcut** (baar-baar login ke liye):
```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519      # sirf pehli baar
ssh-copy-id root@103.21.44.10                          # sirf pehli baar
ssh root@103.21.44.10                                  # ab password nahi poochega
```

---

## ⚡ Part 2 — Ek command me poora install (3–5 min)

VPS ke andar (root) ye ek line:

```bash
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/vps/vps_install.sh" -o /tmp/si.sh && sudo bash /tmp/si.sh
```

Ye script khud ye sab karti hai:

| Step | Kya hota hai |
|---|---|
| 1 | `apt update` + `python3`, `python3-venv`, `pip`, `git`, `curl`, `screen`, `rsync`, `logrotate`, `tzdata` install |
| 2 | `/opt/snake/{data,dumps,logs,backups}` folders |
| 3 | alag user `snake` (bot root me nahi chalega — security) |
| 4 | venv `/opt/snake/.venv` + `python-telegram-bot==21.11.1` + `aiohttp` |
| 5 | `bot.py` GitHub se download + token purane bot se copy (agar mile) |
| 6 | `start.sh` `stop.sh` `restart.sh` `status.sh` `logs.sh` `update.sh` `config.sh` |
| 7 | **systemd service `snake`** → boot pe auto start + crash pe auto restart + logrotate |
| 8 | summary + next steps print |

Custom folder chahiye to:
```bash
SNAKE_DIR=/home/ubuntu/bot sudo -E bash /tmp/si.sh
```

Kuch bhi install nahi karna, sirf dekhna hai:
```bash
bash /tmp/si.sh --dry-run
```

---

## 🔑 Part 3 — Token daalna (3 tarike — ek chuno)

### Tarika A (recommended) — phone ka bot.py seedha copy karo

Phone Termux me (VPS se bahar, naya Termux tab):

```bash
# bot ka phone path → VPS path
scp /storage/emulated/0/DBF/bot.py      root@103.21.44.10:/opt/snake/bot.py
scp /storage/emulated/0/DBF/data/settings.json      root@103.21.44.10:/opt/snake/data/settings.json
scp /storage/emulated/0/DBF/data/rot_proxy.txt      root@103.21.44.10:/opt/snake/data/rot_proxy.txt
scp /storage/emulated/0/DBF/data/manual_proxies.txt root@103.21.44.10:/opt/snake/data/manual_proxies.txt
```

Phir VPS me:
```bash
sudo chown snake:snake /opt/snake/bot.py /opt/snake/data/*
sudo chmod 600 /opt/snake/bot.py
sudo systemctl restart snake
```

> `settings.json` me tumhare **users + redeem keys** hain — ye copy karne se user data bacha rahega.
> `rot_proxy.txt` me webshare endpoint hai. Ye teen files optional hain (nahi hain to bot naye sire se chalega).

### Tarika B — command se token

```bash
cd /opt/snake
sudo ./config.sh --token 123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxx
sudo ./config.sh --admin 8999053405
```
(Ya dono ek saath: `sudo ./config.sh --token 123:AA... --admin 8999053405`)

### Tarika C — file edit

```bash
sudo nano /opt/snake/bot.py
# line 64-65:
# BOT_TOKEN = "123456789:AAHxxxx..."
# ADMIN_IDS = [8999053405]
# Ctrl+O → Enter → Ctrl+X
sudo systemctl restart snake
```

---

## ▶️ Part 4 — Bot chalu + verify

```bash
sudo systemctl start snake
sudo systemctl status snake        # green "active (running)" dikhna chahiye
sudo ./logs.sh                      # live log (Ctrl+C se bahar)
```

Telegram me bot kholo:

```
/ping
```

Aisa dikhna chahiye:
```
🐍 ᴘᴏɴɢ
🟢 Bot zinda hai
🔁 Rotating proxy: 1 set
🌐 DNS: system resolver (Termux-safe)
📦 Core: v2.9.3
```

`/ping` me **uptime** badhta rahe = 24/7 chal raha hai.

> ⚠️ **Ek token = ek bot.** Phone pe bhi chal raha ho to pehle phone pe `~/snake/stop.sh` chalao, warna dono aapas me conflict karenge (Telegram ek hi token se ek connection allow karta hai).

---

## ♻️ Part 5 — 24/7 (systemd kaise kaam karta hai)

| Cheez | Setting |
|---|---|
| Auto start (boot pe) | `systemctl enable snake` (installer kar deta hai) |
| Crash pe restart | `Restart=always`, 10 sec baad |
| Timezone | `Asia/Kolkata` |
| Logs | `/opt/snake/logs/bot.log` + `journalctl -u snake` |
| Log rotate | daily, 20 MB, 7 files (purane compress) |

Roz ke commands (VPS me, ya `cd /opt/snake` ke baad):

```bash
sudo ./status.sh        # chal raha hai ya band
sudo ./logs.sh           # live log
sudo ./restart.sh        # restart
sudo ./stop.sh           # band
sudo ./start.sh          # chalu
sudo ./doctor.sh         # 🩺 poora health check (systemd, token, DNS, disk, duplicates)
```

Ek line me sab kuch (alias jaisa):
```bash
echo 'alias snk="cd /opt/snake && sudo ./status.sh"' >> ~/.bashrc && source ~/.bashrc
```

**Optional — roz 4:30 AM auto restart** (memory fresh rakhne ke liye):
```bash
sudo crontab -e
# ye line add karo:
30 4 * * * /bin/systemctl restart snake
```

---

## 🔄 Part 6 — Naya version aane par update

```bash
cd /opt/snake
sudo ./update.sh          # latest bot.py + token safe + compile check + restart
```

`update.sh` kya karta hai:
1. purana bot `backups/bot_YYYYMMDD_HHMMSS.py` me backup
2. GitHub se naya `bot.py` (adhura download ho to abort)
3. **token + ADMIN_IDS** purane se copy
4. `py_compile` — fail ho to purana bot chalta rehta hai
5. service restart

Manual bhi kar sakte ho:
```bash
sudo cp /opt/snake/bot.py /opt/snake/backups/bot_$(date +%F_%H%M).py
sudo curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/bot.py" -o /opt/snake/bot.py
sudo chown snake:snake /opt/snake/bot.py && sudo systemctl restart snake
```
> ⚠️ Manual me token chala jayega — uske baad `./config.sh --token ...` dobara chalao. Isliye `./update.sh` better hai.

---

## 💾 Part 7 — Backup (2 min, mahine me ek baar)

```bash
cd /opt/snake
sudo tar czf ~/snake-backup-$(date +%F).tar.gz data/ backups/ --exclude='*.log'
ls -lh ~/snake-backup-*.tar.gz
```

Phone pe backup laana:
```bash
# phone Termux me
scp root@103.21.44.10:~/snake-backup-2026-11-07.tar.gz /storage/emulated/0/DBF/
```

Restore:
```bash
sudo systemctl stop snake
sudo tar xzf ~/snake-backup-2026-11-07.tar.gz -C /opt/snake
sudo chown -R snake:snake /opt/snake/data
sudo systemctl start snake
```

---

## 🩺 Part 8 — Troubleshooting (jo asli me aata hai)

| Problem | Check | Fix |
|---|---|---|
| `systemctl status` red | `sudo journalctl -u snake -n 50` | error padho — 90% cases me token galat ya package missing |
| `TelegramConflictError` | phone pe bot chal raha hai | phone pe `~/snake/stop.sh` → `sudo systemctl restart snake` |
| `getMe FAILED / token wrong` | `grep -n '^BOT_TOKEN' bot.py` | `sudo ./config.sh --token NEW` |
| Bot start hota hai par reply nahi | `sudo ./logs.sh` me kya aata hai | internet: `curl -I https://api.telegram.org` |
| `No module named telegram` | venv galat use ho raha | service me path `/opt/snake/.venv/bin/python` hona chahiye |
| DNS fail | `getent hosts api.telegram.org` | `echo 'nameserver 1.1.1.1' \| sudo tee /etc/resolv.conf` |
| Disk full | `df -h` | `sudo rm -rf /opt/snake/dumps/*` (ya `dumps` clear karo) |
| RAM full (OOM) | `dmesg \| grep -i kill` | `/batch conc 200` karo, engines `fast` |
| Log bada ho gaya | `du -sh logs/bot.log` | logrotate khud kat deta hai; manual: `sudo truncate -s 0 logs/bot.log` |
| Service start nahi hoti | `sudo systemctl status snake` | `sudo systemctl daemon-reload && sudo systemctl restart snake` |

**Ek command me sab check:**
```bash
sudo /opt/snake/doctor.sh
```
Output: `Result: X OK • Y issue` + har issue ka fix.

---

## 🔒 Part 9 — Security basics (5 min, recommended)

1. **Root login band karo, naya user banao:**
```bash
adduser yash
usermod -aG sudo yash
rsync --archive --chown=yash:yash ~/.ssh /home/yash
# test karo (naya tab): ssh yash@103.21.44.10
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

2. **Firewall** (sirf SSH; bot ko inbound port nahi chahiye):
```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw --force enable
sudo ufw status
```

3. **fail2ban** (brute-force block):
```bash
sudo apt install -y fail2ban && sudo systemctl enable --now fail2ban
```

4. **Token kabhi share mat karo** — `bot.py` me hai, `chmod 600` rehta hai. Repo me placeholder hi jaata hai.

---

## 🧭 Part 10 — Phone vs VPS (kaun kya kare)

| Kaam | Phone (Termux) | VPS (24/7) |
|---|---|---|
| Dork/keyword banwana | ✅ | ✅ |
| Parser (7 engines) | chal jata hai, par data/WiFi pe block | ✅ **best** (stable IP, proxy rotation) |
| Injector batch | slow, battery | ✅ |
| Proxy scrape (admin) | ✅ | ✅ (400 parallel — fast) |
| 24/7 online | ❌ (screen band → bot band) | ✅ systemd |
| File dumps | phone storage | VPS `dumps/`, phir `scp` se phone |

**Best setup:** VPS pe bot 24/7 + phone sirf Telegram se control. Files chahiye to bot khud Telegram pe bhej deta hai (`DUMPER` button), ya `scp` se phone pe le aao.

---

## 📋 Part 11 — Copy-paste cheat sheet

```bash
# ---- pehli baar (VPS) ----
curl -fsSL "https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot/vps/vps_install.sh" -o /tmp/si.sh && sudo bash /tmp/si.sh
cd /opt/snake && sudo ./config.sh --token 123456:AAHxxxx
sudo systemctl restart snake && sudo ./status.sh

# ---- roz ----
cd /opt/snake && sudo ./status.sh
tail -f /opt/snake/logs/bot.log

# ---- update ----
cd /opt/snake && sudo ./update.sh

# ---- health ----
sudo /opt/snake/doctor.sh

# ---- phone se file bhejna ----
scp /storage/emulated/0/DBF/bot.py root@103.21.44.10:/tmp/
# phir VPS me:
sudo mv /tmp/bot.py /opt/snake/bot.py && sudo chown snake:snake /opt/snake/bot.py && sudo systemctl restart snake

# ---- phone pe dump laana ----
scp root@103.21.44.10:/opt/snake/dumps/latest.txt /storage/emulated/0/DBF/
```

---

## ❓ FAQ

**Q: VPS pe bhi proxy chahiye?**
A: Parser ke liye haan (Google/Yandex VPS IP bhi block karte hain). WebShare endpoint `data/rot_proxy.txt` me daal do — phone se copy ya `/rotproxy host:port:user:pass`.

**Q: Port open karna hai?**
A: Nahi. Bot **outbound** connect karta hai (Telegram + search engines). Inbound port ki zaroorat nahi.

**Q: 1 GB RAM kaafi hai?**
A: Haan. Injector/proxy scrape 400 parallel pe RAM badhta hai — heavy kaam ke waqt `/batch conc 200` kar dena.

**Q: Phone wala data (users/keys) VPS pe kaise aayega?**
A: `scp` se `data/settings.json` copy karo (Part 3 Tarika A). Ye file hi users, keys, settings rakhti hai.

**Q: Bot band ho gaya raat me?**
A: systemd `Restart=always` 10 sec me wapas utha deta hai. `journalctl -u snake -n 100` se wajah dekho; `doctor.sh` chalao.

**Q: VPS delete kar diya to?**
A: `data/` ka backup rakho (`settings.json` + `rot_proxy.txt`) — naye VPS pe wahi 2 file daal ke bot same users/keys ke saath chalu ho jayega.

---

*Guide version: v2.9.3 • scripts: `vps/vps_install.sh`, `vps/vps_doctor.sh`, `vps/snake.service`*
