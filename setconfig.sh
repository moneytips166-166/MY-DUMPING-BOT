#!/usr/bin/env bash
# 🐍 PYTHON SNAKE — config (token + admin) — update ke baad bhi safe
#   ./setconfig.sh --show              → masked token + admins
#   ./setconfig.sh --token 123:ABC     → token badlo
#   ./setconfig.sh --admin 8999053405  → admin list (comma se alag)
#   ./setconfig.sh --addadmin 123456   → ek admin jodo
# Ye values snake_config.json me jaati hain — bot.py update hone se farak nahi padta.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
EXT="/storage/emulated/0/DBF"
CFG="$DIR/snake_config.json"

PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
[ -z "$PY" ] && { echo "❌ python nahi mila — pkg install python"; exit 1; }

# purani install: token bot.py ke andar hai → pehle config banao
if [ ! -f "$CFG" ] && [ -f "$DIR/bot.py" ]; then
    "$PY" - "$DIR/bot.py" "$CFG" <<'PYEOF'
import json, re, sys, time
src_path, out = sys.argv[1], sys.argv[2]
src = open(src_path, encoding="utf-8", errors="ignore").read()
tok = ""
m = re.search(r'^BOT_TOKEN\s*=\s*["\']([^"\']*)["\']', src, re.M)
if m:
    tok = m.group(1).strip()
if "PUT_YOUR" in tok or ":" not in tok:
    tok = ""
adm = []
m = re.search(r'^ADMIN_IDS\s*=\s*\[([^\]]*)\]', src, re.M)
if m:
    adm = [int(x) for x in re.findall(r"\d{5,}", m.group(1))]
cfg = {"bot_token": tok, "admin_ids": adm, "brand": "PYTHON SNAKE",
       "created": time.strftime("%Y-%m-%d %H:%M:%S"),
       "note": "Token/Admin yahan safe hain — ./update.sh inse touch nahi karta"}
with open(out, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
print("🔐 config banaya: %s" % out)
PYEOF
    [ -f "$CFG" ] && chmod 600 "$CFG" 2>/dev/null
fi

"$PY" - "$CFG" "$@" <<'PYEOF'
import json, os, re, sys

cfg_path = sys.argv[1]
args = sys.argv[2:]

def load():
    try:
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def mask(t):
    t = str(t or "")
    if not t:
        return "❌ not set"
    if ":" in t:
        a, b = t.split(":", 1)
        return "%s:%s…%s" % (a, "*" * max(0, len(b) - 4), b[-4:])
    return "***"

def save(cfg):
    tmp = cfg_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    try:
        os.chmod(tmp, 0o600)
    except Exception:
        pass
    os.replace(tmp, cfg_path)
    # DBF copy bhi (agar alag folder hai)
    ext = "/storage/emulated/0/DBF/snake_config.json"
    try:
        if os.path.isdir(os.path.dirname(ext)) and \
           os.path.realpath(os.path.dirname(ext)) != os.path.realpath(os.path.dirname(cfg_path)):
            with open(ext, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
    except Exception:
        pass

cfg = load()
adm = [int(x) for x in cfg.get("admin_ids") or []]

if not args or args[0] in ("--show", "-s", "show"):
    print("📦 config : %s" % cfg_path)
    print("🔑 token  : %s" % mask(cfg.get("bot_token")))
    print("👑 admins : %s" % (", ".join(str(x) for x in adm) or "❌ none"))
    print("🕒 update : %s" % cfg.get("updated", cfg.get("created", "?")))
    print("\nBadalna ho to:  ./setconfig.sh --token <TOKEN>   |   ./setconfig.sh --addadmin <ID>")
    print("Phir restart:  ./restart.sh")
    sys.exit(0)

def val(i):
    """args[0] = flag, args[1] = value"""
    return args[i] if len(args) > i else ""

if args[0] in ("--token", "-t"):
    tok = val(1).strip()
    if ":" not in tok or len(tok) < 20:
        print("❌ token galat lagta hai (BotFather ka poora token: 123456789:AA...)")
        sys.exit(1)
    cfg["bot_token"] = tok
    save(cfg)
    print("✅ token update: %s" % mask(tok))
elif args[0] in ("--admin", "-a"):
    raw = val(1)
    ids = [int(x) for x in re.findall(r"\d{5,}", raw)]
    if not ids:
        print("❌ admin id galat — sirf numbers (Telegram numeric id)")
        sys.exit(1)
    cfg["admin_ids"] = ids
    save(cfg)
    print("✅ admins: %s" % ", ".join(str(x) for x in ids))
elif args[0] in ("--addadmin",):
    raw = val(1)
    ids = [int(x) for x in re.findall(r"\d{5,}", raw)]
    if not ids:
        print("❌ admin id galat")
        sys.exit(1)
    for i in ids:
        if i not in adm:
            adm.append(i)
    cfg["admin_ids"] = adm
    save(cfg)
    print("✅ admins: %s" % ", ".join(str(x) for x in adm))
else:
    print(__doc__ if False else "Usage: ./setconfig.sh [--show|--token T|--admin ID1,ID2|--addadmin ID]")
    sys.exit(1)

print("👉 apply: ./restart.sh")
PYEOF
