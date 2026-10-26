#!/bin/zsh
set -u
APP="/Users/filipelopes/.hermes/profiles/bmoca/app"
OUT=$("$APP/.venv/bin/bmoca-app" jobs staff-weekly-digest --quiet 2>&1) || { echo "⚠️ Digest de segunda da BMoca App FALHOU: $OUT"; exit 0; }
exit 0
