#!/bin/zsh
# Legacy compatibility wrapper; use bmoca_app_weekly_digest.sh.
exec "$(dirname "$0")/bmoca_app_weekly_digest.sh" "$@"
