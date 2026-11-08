#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#  🐍 PYTHON SNAKE — DORK PACK ko /storage/emulated/0 me le jao (one command)
#  Usage:  bash spidey_getzip.sh
# ==============================================================================
set -u
REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/moneytips166-166/MY-DUMPING-BOT/arena/063f862a-my-dumping-bot}"
DEST_DIR="${DEST_DIR:-/storage/emulated/0}"
ZIP="PYTHON_SNAKE_DORK_PACK.zip"
MAN="PYTHON_SNAKE_MANUAL.md"

echo "=============================================================="
echo "  🐍 PYTHON SNAKE — DORK PACK DOWNLOAD"
echo "=============================================================="

# ---------- 1. storage permission ----------
if [ ! -d "$DEST_DIR" ]; then
  echo "  ⚠️  $DEST_DIR nahi mila — storage permission maang rahe hain…"
  command -v termux-setup-storage >/dev/null 2>&1 && termux-setup-storage
  for i in 1 2 3 4 5 6 7 8 9 10; do
    [ -d "$DEST_DIR" ] && break
    sleep 1
  done
fi
if [ ! -d "$DEST_DIR" ]; then
  echo "  ❌ $DEST_DIR abhi bhi nahi mila."
  echo "     👉 Ek baar 'termux-setup-storage' chalao, Allow dabao, phir dobara try karo."
  echo "     👉 Ya yahan save kar lo:  DEST_DIR=\$HOME ./spidey_getzip.sh"
  DEST_DIR="$HOME"
fi

# ---------- 2. download ----------
mkdir -p "$DEST_DIR"
cd "$DEST_DIR" || { echo "❌ folder me nahi ja saka"; exit 1; }

for F in "$ZIP" "$MAN"; do
  echo ""
  echo "  ⬇️  $F"
  rm -f "$F.part"
  if ! curl -fL --retry 3 --retry-delay 2 --max-time 300 "$REPO_RAW/$F" -o "$F.part"; then
    echo "  ❌ Download fail: $F  (internet / GitHub check karo)"
    rm -f "$F.part"
    continue
  fi
  mv -f "$F.part" "$F"
  SIZE="$(du -h "$F" 2>/dev/null | cut -f1)"
  echo "  ✅ Saved : $DEST_DIR/$F  ($SIZE)"
done

# ---------- 3. verify zip ----------
if [ -f "$DEST_DIR/$ZIP" ]; then
  echo ""
  echo "  🔍 ZIP check…"
  if command -v unzip >/dev/null 2>&1; then
    N="$(unzip -l "$DEST_DIR/$ZIP" 2>/dev/null | tail -1 | awk '{print $2}')"
    [ -n "${N:-}" ] && echo "  ✅ ZIP theek hai — $N files"
  fi
  echo "  📦 Path  : $DEST_DIR/$ZIP"
  echo "  📄 Manual: $DEST_DIR/$MAN"
fi

echo ""
echo "=============================================================="
echo "  ✅ HO GAYA — phone ke File Manager me /storage/emulated/0"
echo "     (ya 'Internal storage') kholo, dono files wahin milengi."
echo "=============================================================="
