#!/usr/bin/env bash
# 🐍 SHADOW X — start.sh  (screen based, main bot jaisa)
#   /storage/emulated/0 noexec hota hai → `bash start.sh` use karo
exec bash "$(cd "$(dirname "$0")" && pwd)/run.sh" start
