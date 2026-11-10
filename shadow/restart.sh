#!/usr/bin/env bash
# 🐍 SHADOW X — restart.sh  (screen based, main bot jaisa)
#   /storage/emulated/0 noexec hota hai → `bash restart.sh` use karo
exec bash "$(cd "$(dirname "$0")" && pwd)/run.sh" restart
