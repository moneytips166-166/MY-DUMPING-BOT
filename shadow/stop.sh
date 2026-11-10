#!/usr/bin/env bash
# 🐍 SHADOW X — stop.sh  (screen based, main bot jaisa)
#   /storage/emulated/0 noexec hota hai → `bash stop.sh` use karo
exec bash "$(cd "$(dirname "$0")" && pwd)/run.sh" stop
