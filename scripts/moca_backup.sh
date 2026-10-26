#!/bin/zsh
# Legacy compatibility wrapper; use bmoca_app_backup.sh.
exec "$(dirname "$0")/bmoca_app_backup.sh" "$@"
