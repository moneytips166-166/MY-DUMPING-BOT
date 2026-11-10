#!/usr/bin/env bash
# 🐍 SHADOW X — status.sh  (screen based, main bot jaisa)
#   /storage/emulated/0 noexec hota hai → `bash status.sh` use karo
exec bash "$(cd "$(dirname "$0")" && pwd)/run.sh" status
