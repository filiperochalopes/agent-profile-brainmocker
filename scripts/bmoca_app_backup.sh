#!/bin/zsh
set -u
APP="/Users/filipelopes/.hermes/profiles/bmoca/app"
OUT=$("$APP/.venv/bin/bmoca-app" db backup --quiet 2>&1) || { echo "⚠️ Backup do banco da BMoca App FALHOU: $OUT"; exit 0; }
exit 0
