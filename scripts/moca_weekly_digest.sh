#!/bin/zsh
set -u
APP="/Users/filipelopes/.hermes/profiles/bmoca/app"
OUT=$("$APP/.venv/bin/moca" jobs staff-weekly-digest --quiet 2>&1) || { echo "⚠️ Digest de segunda da Moca FALHOU: $OUT"; exit 0; }
exit 0
