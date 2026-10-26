#!/bin/zsh
# Legacy compatibility wrapper; use bmoca_app_rotate_logs.sh.
exec "$(dirname "$0")/bmoca_app_rotate_logs.sh" "$@"
