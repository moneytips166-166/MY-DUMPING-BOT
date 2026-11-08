# 🔐 SECURITY — zaroor padho

## Repo public hai

Ye repository **public** hai. Iska matlab duniya me koi bhi `bot_fixed.py` dekh sakta hai.

## Bot token kabhi commit na karo

`bot_fixed.py` me line likhi hai:

```python
BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
```

Ye **placeholder** hai — jaan bujh ke khaali chhoda gaya hai. Asli token **sirf** aapke
phone/PC pe `bot_fixed.py` me hona chahiye, GitHub pe nahi.

Token set karne ke 2 tarike:

```bash
cd ~/spidey
./setconfig.sh                              # poochh ke set karega
./settoken.sh 123456789:AAxxxxxxxxxxxxxxx    # seedha
./restart.sh
```

`./update.sh` chalao to aapka **local token khud preserve** ho jata hai — nayi file me
placeholder hota hai, updater usme aapka token daal deta hai. Kuch nahi tootta.

## Agar token kabhi leak ho gaya ho

Telegram bot token = **password**. Jisko mila, wo aapke bot ko chala sakta hai
(messages padh sakta hai, bhej sakta hai, admin commands chala sakta hai).

**Turant ye karo:**

1. Telegram me **@BotFather** kholo
2. `/revoke` → apna bot select karo
3. Naya token copy karo
4. Termux me: `cd ~/spidey && ./settoken.sh <NAYA_TOKEN> && ./restart.sh`

Purana token usi second **mar jata hai** — leak ho chuka ho to bhi safe.

## Checklist

- [ ] Token sirf device pe hai, repo me placeholder hai
- [ ] `.env` / `config.py` gitignored hain
- [ ] Screen session ka screenshot share karne se pehle token check karo
- [ ] Kabhi kabhi BotFather se `/revoke` kar ke rotate karte raho

## Aur kya sensitive hai

| Cheez | Risk | Kya karo |
|---|---|---|
| `BOT_TOKEN` | Poora bot hijack | `/revoke` + `./settoken.sh` |
| `API_ID` / `API_HASH` | Telegram account access | Repo me na rakho |
| `ADMIN_IDS` | Sirf aapka TG id — low risk | Theek hai |
| `data/` folder | User data | `.gitignore` me hai ✅ |
