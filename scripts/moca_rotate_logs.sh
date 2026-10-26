#!/bin/zsh
set -u
OUT=$(/usr/bin/python3 /Users/filipelopes/.hermes/profiles/bmoca/scripts/rotate_logs_archive.py 2>&1) || { echo "⚠️ Arquivamento de logs da Moca FALHOU: $OUT"; exit 0; }
exit 0
