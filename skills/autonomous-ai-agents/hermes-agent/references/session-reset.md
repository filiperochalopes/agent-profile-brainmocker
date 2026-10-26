# Gateway session reset (time-based)

Load this when a user wants messaging conversations (Telegram, WhatsApp, etc.) to start fresh on a schedule, or wants open sessions to stop mixing context across days.

## Core facts

- Core Hermes does NOT rotate gateway conversations on idle or daily boundaries. `session_reset` in config.yaml is inert unless a plugin re-arms it. Only explicit `/new` or `/reset` (or `/stop`) replace a routed conversation.
- Time-based rotation comes from the catalog plugin `hermes-session-reset-policy` (community, fastfinge). It reads the profile's own `session_reset` block: `mode` (idle | daily | both | none), `idle_minutes`, `at_hour` (local hour).
- The plugin has no timers. It resets on the first inbound message past the boundary, so an open session is never closed in the background. Cron and background traffic cannot keep a session alive or reset it.
- The plugin resolves the profile from the message source and reads that profile's config.yaml. A profile without a `session_reset` block is unaffected.

## Procedure

1. Check the current block: `hermes -p <profile> config get session_reset`. If unset, nothing is rotating.
2. Confirm the host timezone before choosing `at_hour`: `date` and `readlink /etc/localtime`. The plugin uses the host's local time, not the profile's.
3. Install into the profile only: `hermes -p <profile> plugins install hermes-session-reset-policy`. It installs disabled.
4. Read the plugin's `__init__.py` before enabling it. It is third-party code running inside the gateway.
5. Enable: `hermes -p <profile> plugins enable hermes-session-reset-policy`.
6. Set the policy with dotted keys: `hermes -p <profile> config set session_reset.mode daily` and `... session_reset.at_hour 0`. The CLI may print "Did you mean sessions.at_hour?" suggestions; these are harmless. Verify with `config get session_reset`.
7. Run `hermes -p <profile> doctor` and look for the `Session Reset` section. It should report the mode as applied by the plugin.

## Pitfalls

- **No platform filter in the plugin.** It applies to every platform the profile's gateway serves. To limit it to one platform (e.g. only Telegram), add a check on `event.source.platform` (`.value`, lowercased) at the top of `_maybe_reset`, before the slash-command check. Place the guard before any clock stamp so other platforms are not touched at all.
- **A local patch is lost on plugin update or reinstall.** Re-apply the platform guard after `hermes plugins update` / reinstall, and record that in the profile memory so it is not forgotten.
- **Gateway restart is needed for a full effect.** The plugin reloads on enable, but confirm the running gateway with `hermes gateway status`; a multiplexed gateway can serve several profiles, so restarting it affects all of them. Ask before restarting.
- **Verify on a real message.** A config check does not prove the platform filter works. Confirm with a fresh inbound message the next day and the gateway log line `session-reset-policy: reset <key> (reason=daily ...)`.
- **Scope is by profile, not by user.** Per-user or per-chat resets are not supported by this plugin.
