---
name: evolution-api
description: Use when inspecting or sending Evolution API messages.
version: 0.1.0
author: Filip Lopes, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Evolution API, WhatsApp, macOS Keychain]
    related_skills: [age-calculator]
---

# Evolution API Skill

Use the local Keychain helper to retrieve the Evolution API credential, then access only the explicitly identified instance, conversation, and requested date range. Read and summarize on request; send a message only when the user explicitly asks. Never change instance settings or retrieve unrelated conversations.

## Telegram: acesso SOMENTE via guarda (obrigatório)

- Em sessões do Telegram, toda chamada à Evolution API passa por `python3 /Users/filipelopes/.hermes/profiles/bmoca/skills/productivity/evolution-api/scripts/evo_guard.py METHOD PATH [--body JSON]`. O guarda lê o remetente do ambiente (`HERMES_SESSION_USER_ID`) e aplica `policies/evolution_access.json` (padrão: negar), grava auditoria em `policies/evolution_audit.jsonl` e filtra `fetchInstances`.
- Proibido no Telegram: usar `evo.py`, ler a chave no Keychain, chamar a API com curl/urllib, ou ler/editar `policies/`. Se o guarda responder `NEGADO`, informe a recusa ao usuário e pare; não contorne.
- Permissões atuais: Filipe `1556914128` = admin; Robson `1106796150` = só `Robson - Pessoal`; Lorena `1104815252` = só `Lorena - Pessoal`. Novos usuários: só o Filipe autoriza, editando o JSON de política.
- Jobs de cron e sessões locais (desktop/CLI) do Filipe continuam usando `evo.py`. O guarda trata a plataforma `cron`/`desktop`/`cli` como confiável (`trusted_platforms`) e nega sessão sem identidade; um limite real exigiria perfil/bot sem terminal, pois o guarda só vale por convenção enquanto o agente tiver terminal e Keychain.
- Autorizar novo usuário do Telegram = (1) `hermes -p bmoca config set TELEGRAM_ALLOWED_USERS <lista com o novo ID>` + reiniciar o gateway, (2) entrada em `policies/evolution_access.json`, (3) mapeamento Telegram → pessoa em `app/config/identities.toml` (pessoa cadastrada no banco via `moca people`).

## Roteamento por remetente do Telegram

- Se a mensagem vier do Telegram com o ID de usuário `1106796150`, use SEMPRE a instância `Robson - Pessoal` (nome exato retornado por `fetchInstances`; codifique o espaço como `%20`). Não pergunte qual instância e não use outra.
- Isso define apenas a instância. Os demais cuidados continuam valendo: ler somente o chat e o período pedidos, e enviar mensagem apenas com pedido explícito.
- Se a mensagem vier do Telegram com o ID de usuário `1104815252` (Lorena), use SEMPRE e SOMENTE a instância `Lorena - Pessoal` (`%20` no espaço). Nunca consulte, liste detalhes nem envie por nenhuma outra instância, mesmo que ela peça; recuse e explique. `fetchInstances` serve só para confirmar o nome exato e não deve ter outras instâncias exibidas a ela. Não revele conversas, grupos ou dados de outras instâncias.
- Mensagens de outros IDs ou de outras origens não herdam essas regras; para elas, a instância deve ser informada pelo usuário.

## When to Use

- The user asks to inspect, summarize, or send messages through their Evolution API instance.
- Administrative changes remain out of scope unless separately authorized.

## Prerequisites

- macOS login Keychain contains a generic password with account `$USER` and service `EVOLUTION_API_KEY`.
- Helper: `/Users/filipelopes/Desktop/Development/agents/infra/helpers/evolution-keychain-env.sh`.
- The user must provide or identify the Evolution API base URL, instance name, and target chat/contact. Never ask them to paste the API key into chat.
- Confirm the API version and endpoint against the instance's Swagger/OpenAPI docs or official Evolution API documentation before requesting data; endpoints and auth headers can vary by version.

## Procedure

1. Retrieve the secret only into the request process environment by invoking the helper; never print, log, or include its output in the conversation. Avoid shell tracing and debugging output.
2. Verify the base URL is the user's intended host and use HTTPS where available. Do not follow redirects to a different host while carrying the API key.
3. Confirm the correct read-only endpoint and required auth header for this deployed version.
4. Resolve the exact instance name and target conversation before requesting data; avoid broad chat enumeration. For date windows, fetch a bounded page and filter timestamps client-side when server-side timestamp filters are unreliable.
5. For group rosters, use the group-participants endpoint and map each participant LID to its returned phone number. Map display names from matching message `key.participant` + `pushName`; use the phone number when no display name is available. State the source of names and verify the final roster count.
6. For weekly summaries, inspect message types and payload keys for audio/image/video/document media before summarizing. Transcribe audio only when an actual audio payload is present, using the requested local transcription CLI; do not infer that `unknown` or history-notice messages are media. When the user asks to transcribe audio from a chat, follow `references/media-download-and-transcription.md`. Summarize only the requested period and minimize sensitive personal details.
7. Before sending a summary to a phone number, verify the destination is the specified recipient and, when the summary concerns a private group, check whether that number belongs to the group or ask the user if authorization is unclear. Exclude unnecessary children's health or other sensitive personal details.
8. Use the deployed API's documented send-text endpoint and schema. If the server returns an explicit 400 schema-validation error, inspect only its validation message, adapt the payload, and retry only when the rejection confirms nothing was sent.
9. After sending, read back the exact target conversation and verify the returned message ID and text before reporting success. If authorization fails, stop and report status without dumping request headers, environment, or secrets.
10. For recurring group digests, compute the requested local-time window precisely, inspect every paginated message in that window, and send the identical finalized text to every user-authorized destination. Keep the scheduler's own delivery local when the job sends through Evolution API, so it does not create duplicate chat posts.
11. When the user adds a destination to an existing digest, list the scheduled job first, send any explicitly requested one-off backfill to the new destination and read it back, then update the job's self-contained prompt so its source scope, complete destination list, and per-destination verification all change together. Read back the saved job configuration before confirming the change.

## Weekly group digest format

- When the user asks to "see" or preview a summary, show it in chat only and send nothing; send only after a separate explicit request, to the named group only, then read back and match message ID and exact text.
- Weekday/time is the user's choice per group (Friday 03:00 is only the default); use a cron expression such as `0 3 * * 1` and keep the job's prompt scoped to one instance, one JID.
- The `cronjob_manage` create tool does not take a model; `pinned=true` locks whatever the main model is at that moment. After creating, run `hermes -p bmoca cron edit <job_id> --model <model> --provider <provider> --pin` with the user's requested model (e.g. `gpt-6-luna` / `openai-codex`), then list the job and confirm model, provider, schedule and next run. Check the existing digest job's model for the user's usual choice.

- When the user requests a weekly summary, use a Friday-to-Friday window anchored at 03:00 local time unless they specify another cadence. Make the title show the local start and end dates only: `🤖 *Resumo da semana (DD a DD/MM)*`.
- Daily digests use the same block with title `🤖 *Resumo do dia (DD/MM)*`; see skill `feedback-atas` for the daily ata+digest job.
- Write 1–6 concise, factual bullets using WhatsApp Markdown (`* texto`), with no introduction, closing, run metadata, or commentary outside that block.
- Preserve relevant plans, dates, times, locations, materials, and agreed actions. Do not mention missing media; mention audio or image content only when it was actually retrieved and inspected.
- Before scheduling a recurring digest, pin the requested model/provider explicitly with the cron CLI's `--model` and `--provider` options; verify the persisted job's schedule, skills, model, provider, destinations, and next run after creation.

## Known deployment (wpp.orango.io, v2.3.7)

- Success codes: POST endpoints (`sendText`, `getBase64FromMediaMessage`, `findMessages`) can return `201` instead of `200`. Treat any 2xx as success, then read the body; a status-only check (`== 200`) wrongly reports media downloads as failed.
- Auth header `apikey`. Endpoints: `GET /instance/fetchInstances`; `POST /chat/findChats/{instance}`; `GET /group/participants/{instance}?groupJid={groupJid}`; and `POST /chat/findMessages/{instance}` with `{"where":{"key":{"remoteJid":JID}},"page":N,"offset":K}`. Verify the deployed response shape; message search is newest first. Send text with `POST /message/sendText/{instance}` only after explicit user authorization.
- Instances (exact `name` from `fetchInstances`; `instanceName` is None in the response, use `name`): `Filipe Lopes - Business` 557186056232, `Filipe Lopes - Pessoal` 557192540736, `Filipe Lopes - Medico` 557192518950, `Robson - Pessoal` 557592637710, `Lorena - Pessoal` 557192518959, `Robson`, `Adri`. Sender-specific routing rules are in the Telegram section above.
- Find a group by name: `POST /chat/findChats/{instance}` with `{}` returns all chats (name in `pushName`/`name`, JID in `remoteJid`, groups end in `@g.us`); match by substring and note that the WhatsApp group name may be spelled differently from what the user types. Message records live at `d['messages']['records']`.
- Scratch client: `~/.hermes/cache/scratch/evo.py` (`call(method, path, body)`, `inst(name)`); recreate if pruned — read key via `security find-generic-password -w` inside Python, refuse cross-host redirects.

## Pitfalls

- `messageTimestamp` filters in `where` returned nothing; paginate newest-first and filter by timestamp client-side.
- Group participant IDs and message `key.participant` commonly use `@lid`; use `phoneNumber` from the participants endpoint for display/fallback, and correlate names via `key.participant`. For chat message queries, use the actual `remoteJid` (often a group JID or LID), not a guessed phone JID.
- Use o campo `name` de `fetchInstances` para obter o nome exato da instância nesta implantação, não `instanceName` nem um apelido abreviado. URL-encode espaços como `%20`; nome incorreto ou codificação malformada pode retornar 404.
- Multi-device duplicates: the same message may appear twice; dedupe by text + timestamp.
- "New contact" = earliest message in the chat falls inside the requested window.

- The helper outputs a secret assignment; its stdout is sensitive. Never inspect it in tool output. Test only exit status and redact any diagnostic.
- macOS Keychain may show an access prompt on first use. The user should approve it locally; never try to bypass Keychain access controls.
- A Keychain item is not automatically connected to Hermes: the helper must be configured as a command helper or used by the specific API client process.
- Evolution API deployments can differ in version, base path, auth header, and payload schema. Confirm docs for the deployed version, then trust explicit validation errors from that instance; some v2.3.7 installations require `{"number":"…","text":"…"}` for sendText even when published examples show a nested `textMessage` object.

## Verification

- Confirm the helper is executable and succeeds without displaying its stdout.
- Confirm Hermes has loaded the secret via its supported command-helper mechanism without recording the credential in config files.
- Before reporting API access as working, verify one bounded read-only request against the user's specified instance and chat.

## Reusable local client for ad-hoc analysis

- The script `~/.hermes/profiles/bmoca/scripts/evo_client.py` (from the `escola-sem-nome-drive` skill) provides a minimal `call(method, path, body)` function that reads the Keychain in-process and talks to `wpp.orango.io`. Use it from `execute_code` for one-off group roster/message queries in desktop/CLI/cron sessions — it avoids the Telegram guard and is simpler than the scratch client.
- Pattern: `sys.path.insert(0, "~/.hermes/profiles/bmoca/scripts"); from evo_client import call` then `call("GET", "/group/participants/{INST}?groupJid={JID}")` etc.
- Correlate participant LIDs with message `key.participant` + `pushName` to build named rosters.
- **Guard behavior**: The `evo_guard.py` checks `HERMES_SESSION_USER_ID` and platform; in desktop/CLI sessions without that env var, it returns `NEGADO: plataforma/identidade desconhecida`. Use `evo_client.py` directly in those contexts instead of the guard.

## Cadastro analysis workflow (Escola Sem Nome pattern)

Recurring task: parse `*CADASTRO DE PARTICIPANTES*` messages from a group, build a complete participant database with family relationships, children's birth dates, and calculated ages.

**Procedure**:
1. Fetch group participants (`GET /group/participants/{INST}?groupJid={JID}`)
2. Fetch messages paginated newest-first (`POST /chat/findMessages/{INST}` with `where.key.remoteJid`)
3. Filter messages containing `CADASTRO DE PARTICIPANTES`
4. Parse each cadastro: extract parent names, child names, birth dates (DD/MM/YYYY or DD/MM), sexes
5. Correlate cadastro authors with roster via LID (`key.participant`) and `pushName`
6. Enrich with user-provided phone directory for participants without pushName
7. Calculate children's ages using `age-calculator` skill with reference date = analysis date
8. Output in user's requested format (with hyphens, without hyphens, names only)

**Key integration**: Always use `age-calculator.calculate_age(birth_date, reference_date)` for deterministic ages. Never approximate manually — the user caught and corrected manual calculation errors.

**Incomplete birth date patterns** (see `references/cadastro-birth-date-patterns.md`):
- Age only: `"2 anos"` → infer year from reference date minus age
- Day/month only: `"19/02"` → infer year from context (age stated elsewhere or recent birth)
- Day/month + approx age: `"01/12 (3 anos)"` → use day/month, infer year from age
- Typo year: `"23/10/2026"` for a 3-year-old → correct to 2023
- Always confirm inferred dates with user when possible

**Phone correlation workflow**:
1. Get roster: `GET /group/participants/{INST}?groupJid={JID}` → list of `{id (LID), phoneNumber, pushName, admin}`
2. Build LID→pushName map from messages (`key.participant` + `pushName`)
3. For roster entries without pushName, match `phoneNumber` (cleaned) to user-provided directory
4. Result: complete named roster with phone numbers in `+55 DDD NNNN-NNNN` format

**Output formats** (user preference):
- `<Nome completo> (+55 DDD NUMERO)` with hyphens
- `<Nome completo> (+55 DDD NUMERO)` without hyphens  
- `<Nome completo>` names only

## Identidade e escolha do canal de saída

- No WhatsApp dedicado, a assistente se chama **Edite**. Não acrescente o antigo prefixo `Moca falando aqui:` no WhatsApp nem no Telegram; siga `bmoca-identity`.
- Prefira envios pelo número dedicado via gateway nativo, inclusive nos jobs. Não troque silenciosamente uma conta remetente: confirme o escopo da migração, os destinos e a presença do bot neles.
- Avalie leitura e envio separadamente. Só retire a Evolution como fonte depois de verificar o histórico persistente, a janela completa e as mídias do caminho nativo. A existência de `hermes send` não comprova recuperação de histórico.
- Leia os prompts completos e scripts de todos os jobs afetados: prefixos e chamadas Evolution podem estar embutidos. Migre em conjunto com os validadores da app, preserve registros antigos e verifique a entrega; documentação alterada não significa produção migrada.
- Procedimento de transição: `references/group-messaging-and-scheduling.md`. Para KB e triagem, carregue a skill `moca-app` e sua referência sobre conhecimento público em grupos e jobs nativos.

## Desktop/CLI vs Telegram client choice

- **Desktop/CLI/cron sessions**: use `evo_client.py` directly (reads Keychain in-process, no guard)
- **Telegram sessions**: must use `evo_guard.py` (enforces per-user instance policies)
- The guard returns `NEGADO: plataforma/identidade desconhecida` when `HERMES_SESSION_USER_ID` is absent — this is expected in desktop/CLI; switch to `evo_client.py` instead of retrying the guard.