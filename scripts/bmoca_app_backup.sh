#!/bin/zsh
set -eu
PROFILE="/Users/filipelopes/.hermes/profiles/bmoca"
APP="$PROFILE/app"
"$APP/.venv/bin/bmoca-app" db backup --quiet
"$APP/.venv/bin/python" "$PROFILE/scripts/bmoca_app_drive_backup.py"
