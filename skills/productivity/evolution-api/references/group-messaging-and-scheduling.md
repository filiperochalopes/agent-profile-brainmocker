# Group messaging and scheduled sends (Evolution API v2.3.7)

## Identity and coordinated transition
- Follow `bmoca-identity`: Edite is the dedicated WhatsApp assistant; do not add the legacy `Moca falando aqui:` prefix on WhatsApp or Telegram.
- Inspect gateway `whatsapp.reply_prefix`, payload templates, every affected job prompt, app validators and tests before removing a legacy prefix requirement. Coordinate the change rather than making the gateway header disagree with stored or delivered text.
- Preserve historical messages and source-specific authorship; updating this reference does not change deployed jobs.

## Identifying instances and groups
- `GET /instance/fetchInstances` returns the instance name in the `name` field (not `instanceName`) on this deployment. Use that exact value, URL-encoded (`%20` for spaces).
- `POST /chat/findChats/{instance}` lists chats; groups have `remoteJid` ending in `@g.us`. Target groups by JID, never by display name: group names get renamed by members, and a rename does not change the JID.
- When a user says a group was renamed, the JID-based jobs keep working; only the human-readable labels in job names become stale.

## Reading message history
- `POST /chat/findMessages/{instance}` body `{"where":{"key":{"remoteJid":JID}},"page":N,"offset":K}`. Records are under `messages.records`; newest first.
- Text is in `message.conversation` or `message.extendedTextMessage.text`. Sender display name is `pushName`; own messages show the account owner's name, so label them by `key.fromMe` when needed.
- Non-text types (`audioMessage`, `imageMessage`, `documentMessage`, `stickerMessage`, `protocolMessage`, `albumMessage`) have no text payload. Do not present them as content, and do not transcribe unless the user asks and the payload exists.
- Dedupe by `key.id` (or text + timestamp) before summarizing.

## Scheduling a one-off send with cronjob_manage
- Use `action=create` with a one-shot ISO schedule (for example `2026-10-23T11:30:00`) and the local timezone -03:00. Verify `next_run_at` in the response matches the requested time.
- Set `deliver=local`: the job posts to the group through the API, so delivering its output to a chat would duplicate the post.
- Give the job a self-contained prompt: JID, instance name, exact text, the no-retry rule (a single send, a retry only if the API confirms nothing was sent), the read-back check, and the final status format.
- To change a scheduled job, call `update` with the full prompt again. Partial edits are not supported, so keep a copy of the full prompt text.
- Confirm the saved state by listing the job; if the prompt text itself must be verified, check the stored job file under the profile's `cron/jobs.json` (read-only).

## Recurring digests and native-channel migration
1. List jobs before editing; inspect full prompts and invoked scripts, not only names or scheduler `deliver`. Inventory every source and recipient, including additional groups and private copies.
2. Prefer the dedicated bot for outgoing messages. Verify `hermes -p bmoca send --help`; authorized native sends use `hermes -p bmoca send --to whatsapp:<JID> --json --file <path>`. Parse the full JSON stdout and verify the exact target message before recording success.
3. Prove historical coverage separately before replacing Evolution reads: persistence, time-window queries, reconnection gaps and media downloads. Do not use LLM session history as evidence of a complete group archive.
4. Preserve approved schedules, recipients, models and provenance. Do not broaden the interactive group allowlist to match job recipients or read sources. Check for daily/weekly overlap without pausing jobs unilaterally.
5. Remove legacy prefix text from the formatting section and payload together with app validators; keep historical attribution compatible with personal-account sources and dedicated-bot sources.
6. Keep only one delivery path: when the script/API sends directly, use `deliver=local`; when the scheduler delivers, do not also send inside the job. Read back persisted job configuration and each actual delivery before claiming completion.
7. Keep existing Evolution access guards in force for any remaining reads. A migration plan is not permission to use a personal instance outside the caller's scope.
