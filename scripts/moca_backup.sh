#!/bin/zsh
set -u
APP="/Users/filipelopes/.hermes/profiles/bmoca/app"
OUT=$("$APP/.venv/bin/moca" db backup --quiet 2>&1) || { echo "⚠️ Backup do banco da Moca FALHOU: $OUT"; exit 0; }
exit 0
