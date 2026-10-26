# Messaging gateway hardening (WhatsApp/Baileys focus, multiplexed profiles)

Use when a profile's messaging bot must only serve registered people, hide admin commands, or expose a restricted toolset to end users.

## Audit first
- Allowlist: `grep -E '^WHATSAPP_ALLOWED_USERS=' $HERMES_HOME/.env` (print counts/masked values only). `*` means every sender reaches a full agent.
- Bridge log shows what is live: `tail $HERMES_HOME/whatsapp/bridge.log` → `Allowed users: ...`, `group_policy_rejected` events.
- Effective tools: `platform_toolsets.<platform>` in the profile config; absent = defaults (`hermes-whatsapp` = same as CLI, i.e. terminal + files).
- Existing sessions per platform: read-only query on `state.db` `sessions.source`.

## Lock down (always back up `.env` + `config.yaml` first)
```bash
hermes -p <p> config set WHATSAPP_ALLOWED_USERS "<digits,comma,separated>"   # writes .env
hermes -p <p> config set whatsapp.unauthorized_dm_behavior ignore            # silence instead of pairing code
hermes -p <p> config set whatsapp.allow_admin_from '["<digits>@s.whatsapp.net","<lid>@lid"]'
hermes -p <p> config set whatsapp.user_allowed_commands '[]'                 # non-admins: only /help /whoami
hermes -p <p> config set whatsapp.group_allow_admin_from '[...]'             # group scope is separate
hermes -p <p> config set whatsapp.group_user_allowed_commands '[]'
hermes -p <p> config set platform_toolsets.whatsapp '[]'                      # chat only; or '["<plugin-toolset>"]'
```
- Allowlist numbers: use the digits exactly as in the WhatsApp JID (Brazilian legacy numbers may lack the 9th digit); the adapter maps LID↔phone itself.
- Slash-command admin match is an exact string compare against the session `user_id`, which for WhatsApp is `<digits>@s.whatsapp.net`; list that form (plus the `@lid` form for safety), not bare digits.
- Root-level `whatsapp:` keys (`unauthorized_dm_behavior`, `allow_admin_from`, `reply_prefix`, `require_mention`, `group_policy`, `group_allow_from`) are bridged into the platform `extra`.
- Slash tiers gate only slash commands, not chat or tools; restricting tools needs `platform_toolsets` and/or a plugin `pre_tool_call` block.
- Groups: `group_policy: allowlist` + `group_allow_from` (group JIDs) admits EVERY participant of those groups regardless of the DM allowlist — authorize per person inside your tools.

## Cheap group triage and intentional silence
1. Keep receive/response policy, read-source scope and scheduled-send destinations separate. A bot being connected or present in a group does not prove that the group passes admission; inspect exact-JID rejection events and effective configuration without printing message bodies or full phone numbers.
2. For a no-mention workflow, investigate `pre_gateway_dispatch` and `post_gateway_admission` in the current hooks docs and installed call sites before choosing an integration. `pre_gateway_dispatch` runs before authorization, so never send or expose data there based only on a text-supplied identity; `post_gateway_admission` is after admission but is fail-open on errors/timeouts. Neither is automatically a fail-closed privacy boundary.
3. Run cheap deterministic triage before starting the full agent when feasible. A full model call that returns `[SILENT]` suppresses delivery but still spends tokens. Preserve a bounded, access-scoped source buffer rather than injecting the entire group transcript into every call.
4. Verify both marker recognition and turn eligibility: `gateway/response_filters.py` recognizes a bare `[SILENT]`; `silence_allowed(display_kind, reply_expected)` permits it for internal machinery or `reply_expected is False`. A human turn expecting a reply may receive a visible fallback. Test actual adapter metadata and batch behavior before enabling ambient silence.
5. Keep silence markers bare: `Moca falando aqui: [SILENT]` is ordinary text, not the exact marker. Test silence alongside platform prefixes, streaming and progress notifications so ignored messages produce no visible output.
6. Inspect native history persistence separately from outbound send support before replacing an API-backed archive. Agent sessions omit filtered/rejected events and are not evidence of complete group history. Require window coverage, reconnection and media tests before migrating read-dependent jobs.

## Set a model for one WhatsApp chat
Use a channel override when a WhatsApp group needs a different model without changing the profile-wide model used by Desktop, Telegram, or other chats.

1. Identify the exact WhatsApp `source.chat_id` from authorized configuration or a bounded, authorized lookup; do not use a display name, session key, or sender `user_id` as the configuration key. For DMs, `chat_id` may be a `@lid` even when the session key uses a phone number; inspect the current WhatsApp row's `chat_id` in `state.db` without reading message bodies.
2. Back up `$HERMES_HOME/config.yaml` and `$HERMES_HOME/.env` before changing gateway settings.
3. Write the full override mapping through the CLI, explicitly including both model and provider:
   ```bash
   hermes -p <p> config set platforms.whatsapp.channel_overrides \
     '{"<chat-jid>":{"model":"<provider-model-id>","provider":"<provider>"}}'
   hermes -p <p> config get platforms.whatsapp.channel_overrides --json
   ```
   Merge any existing mappings before writing: `config set` replaces the mapping at that key.
4. Run a minimal direct inference probe with the same provider and model to verify authentication and model availability, but do not post a test message to a family group unless the user explicitly requests it.
5. Confirm the adapter-owning profile from the post-restart gateway log. In multiplexed gateways, shared-ingress status text can be ambiguous; treat a fresh `whatsapp connected (profile: <p>)` entry as the proof of the profile actually serving WhatsApp.
6. Explain scope precisely: channel overrides are exact-chat mappings, not a platform-wide wildcard. A `/new` clears a session-level `/model` selection but continues to resolve the matching channel override; a nonmatching DM or group uses the profile default.

### Configure a resilience fallback
When the user wants a secondary model only for provider failure, keep the preferred model as the channel override and configure `fallback_providers` separately:
```bash
hermes -p <p> config set fallback_providers \
  '[{"provider":"<fallback-provider>","model":"<fallback-model-id>"}]'
hermes -p <p> fallback list
```
A fallback runs for rate limits, overloads, or connection errors; it is not a quality-based model router. State that this chain is profile-wide unless a more narrowly scoped mechanism is verified.

## Reload one multiplexed profile and verify
1. `hermes -p <p> gateway restart` (re-reads that profile only; never restart the default host for this).
2. Wait ~45 s; `lsof -nP -iTCP:<bridge_port> -sTCP:LISTEN` (port in `$HERMES_HOME/platforms/whatsapp/bridge_port`) must show `node`.
3. `grep "whatsapp connected (profile: <p>)" ~/.hermes/logs/gateway.log | tail -1` must be newer than step 1, and `bridge.log` must print the new `Allowed users:` line.
4. If the log shows `✗ whatsapp failed to connect`, run the restart once more — the old bridge can still hold the port during the first reconnect. A second failure is a real problem; stop and investigate.

## Building restricted tools (plugin)
- Register tools with `ctx.register_tool(..., toolset="<name>")` and set `platform_toolsets.<platform> '["<name>"]'`.
- Read caller identity inside handlers/hooks with `from gateway.session_context import get_session_env` (`HERMES_SESSION_PLATFORM`, `_USER_ID`, `_USER_ID_ALT`, `_CHAT_ID`, `_CHAT_TYPE`, `_MESSAGE_ID`), never from model arguments.
- `pre_tool_call` can block (fails closed on timeout) or `modify` args; `pre_llm_call` can inject per-turn context; `register_system_prompt_section` adds bounded always-on rules (≤4000 chars, frozen per session).
- Scripted sends without an agent: `hermes -p <p> send --to <platform>:<target> --json --file <path>`; read `message_id` from the JSON.
