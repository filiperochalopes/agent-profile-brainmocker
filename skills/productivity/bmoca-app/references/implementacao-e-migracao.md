# Implementação das fases e migração legada: receitas e armadilhas

## Estado de referência (após fases 1-2 + código do seed + plugin)
- Código: `moca/{settings,audit}.py`, `db/{session,migrate}.py`, `domain/`, `authz/{identity,policy}.py`, `services/{documents,people,feedback,atas,knowledge,cases,outbox,digest}.py`, `channels/hermes_send.py`, `cli/{main,cmd_db,cmd_seed,cmd_admin,cmd_ops,tool,common}.py`, `migration/{legacy_cadastro,legacy_markdown,seed}.py`; plugin em `$PROFILE/plugins/moca-core/` (desabilitado até o piloto).
- Relatório: `app/docs/relatorios/fase-1-3.md`. Antes de refazer algo, confira o que já existe.

## Portões humanos e ações que exigem aprovação
- O `seed --apply` lê SÓ `migration/decisions/*.csv`. Sem as respostas Q-01..Q-04 do Filipe, NÃO grave dados reais: entregue o dry-run, pergunte (clarify) e relate o pendente. Validar o seed com dados sintéticos em `tmp_path` (fixture) em vez de rodar contra o banco real.
- Comando de shell bloqueado por falta de aprovação (timeout) = parar aquele resultado; não reformular o mesmo efeito por outro caminho. Criação de `scripts/*.sh` com chmod, cron, `gateway restart`, habilitar plugin e `allowlist apply` dependem do Filipe presente.

## Receitas
- Alembic: `uv run alembic -x url=sqlite:////caminho/scratch.db revision --autogenerate --rev-id 0001`; `env.py` aceita `-x url=`, `sqlalchemy.url` ou `load_settings()`. O autogenerate NÃO emite o índice funcional parcial `uq_document_idempotency_key` nem o import de `moca.db.models` (UTCDateTime): acrescente à mão (`op.execute(CREATE UNIQUE INDEX ... WHERE ...)` e DROP no downgrade).
- Settings sobrescrevíveis por env para testes/validação: `MOCA_PROFILE_HOME`, `MOCA_CONFIG_DIR`, `BMOCA_APP_DB_FILE`, `MOCA_MIGRATION_DIR`.
- Testes: fixtures `profile_home` → `settings` → `engine` (Alembic em arquivo temporário) → `session`; `tests/helpers.py` monta duas famílias sintéticas, equipe e atribuição. Teste do plugin carrega o pacote por `importlib` com `submodule_search_locations`.
- Ruff: ignore `E501`/`RUF001-003` no pyproject (formatador não quebra strings; textos em português). Rode `ruff check --fix --unsafe-fixes` e depois `ruff format` (o formatter reescreve arquivos: releia antes de `write_file`, que recusa escrita sobre arquivo modificado).
- `write_file` recusa sobrescrever arquivo existente não lido nesta tarefa: para arquivos do `uv init` (`__init__.py`, `.gitignore`) use `patch` ou leia antes.
- macOS: `sed -i ''`; um `&&` abortado silenciosamente impede os comandos seguintes (ex.: mkdir) — confira com `ls` antes de supor que os arquivos existem.
- Hooks do Hermes (conferido na doc instalada, `website/docs/user-guide/features/hooks.md`): `pre_tool_call(tool_name, args, task_id, **kw)` retorna `{"action":"block","message":...}` ou `{"action":"modify","args":{...}}` (shallow-merge); `pre_llm_call(**kw)` retorna `{"context": ...}` e recebe `platform`, `session_id`, `user_message`; `register_tool(name, toolset, schema{name,description,parameters}, handler)`; callback que levanta exceção ou estoura timeout em `pre_tool_call` falha fechado.

## Plugin moca-core no gateway real (piloto)
- O Hermes adia ferramentas de plugin atrás de `tool_search`/`tool_describe`/`tool_call`. O `pre_tool_call` que bloqueia tudo que não é `moca_*` DEVE deixar a ponte passar e bloquear só quando algum `calls[].name` de `tool_call` não começar com `moca_` (senão a Moca fica "sem ferramentas").
- Buffer de mensagens recentes: chave = `HERMES_SESSION_CHAT_ID` (igual no hook e no handler), não a sessão; evita mistura entre conversas.
- Spike 4.2 medido: `message_id`, `chat_type`, `chat_id`, `user_id` existem em `pre_llm_call`. Voz: o gateway entrega a transcrição ENTRE ASPAS em `user_message` (marcar `is_audio`).
- `hermes send --json` imprime JSON multilinha; parseie o stdout inteiro, não só a última linha. Alvo que funciona: `whatsapp:<número>@s.whatsapp.net`.
- Logs do Hermes (`logs/agent.log`, `state.db`, `sessions/request_dump_*`) gravam o texto das mensagens recebidas, fora das proteções do banco: avise o Filipe sobre privacidade/retenção.
- Teste de piloto só vale com evidência de escrita: confira `data/audit/AAAA-MM.jsonl` (evento de feedback) e `document` no banco de teste; a resposta do modelo ("registrei", "tomei nota") não prova nada, e modelos fracos (ex.: gemini flash-lite no WhatsApp) respondem só com texto. Por isso o `pre_llm_call` deve injetar regra explícita: registrar chamando `moca_registrar_feedback`, só dizer "registrei" após `ok`, nunca tratar o histórico da conversa como registro, usar só as crianças vinculadas. Peça ao usuário nomes das crianças `[TESTE]` nos testes. Só saia do piloto (remover `PILOTO`) depois dessa evidência.
- UX no WhatsApp para pais leigos: silencie o ruído do Hermes só nessa plataforma — `display.platforms.whatsapp.{tool_progress,interim_assistant_messages,long_running_notifications,busy_ack_detail,busy_steer_ack_enabled}` desligados (`tool_progress` precisa do TEXTO `'off'`: `hermes config set ... off` grava booleano `false` que NÃO desliga; confira no YAML), `display.busy_input_mode: steer`, `onboarding.seen.busy_input_prompt/tool_progress_prompt: true` e `WHATSAPP_HOME_CHANNEL` definido (evita o aviso "No home channel"). A resposta ao `/new` não é configurável: só o admin usa comandos. O contexto injetado deve mandar responder em português simples, 2-3 frases, sem refs (#abc), nomes de ferramenta, "sessão" ou "histórico"; confirmar o registro em uma frase.
- Sessão longa de WhatsApp acumula respostas falsas ("registrei") que o modelo imita e fica sem as ferramentas novas do plugin (carregadas só em sessão nova): após mudar plugin/regras, o admin manda `/new`; considere reset diário também no WhatsApp (o patch local do reset restringe a Telegram).
- Retenção de logs: o Hermes rotaciona por tamanho (padrão 5 MB × 3 apaga em dias). Configure `logging.max_size_mb`/`backup_count` altos e use `scripts/rotate_logs_archive.py` (cron `no_agent` diário) para gzipar em `logs/archive/` os segmentos `*.log.N` com mais de 90 dias; nunca mexa no arquivo ativo.
- Idempotência no piloto: registros distintos têm `message_id` distinto na chave `feedback:wa:<chat>:<msg>:<criança>`; "registro duplo" = mesma chave/texto repetida, confira por `idempotency_key` no banco.
- Piloto: banco `BMOCA_APP_DB_FILE=moca_test.db` (famílias `[TESTE]`) + arquivo marcador `plugins/moca-core/PILOTO`; `gateway restart` pode responder "pending" e conectar ~40 s depois.

## Armadilhas de domínio
- Casar telefone→adulto: tokens do apelido ⊆ tokens do nome de EXATAMENTE um adulto (sem acentos/emojis); caso contrário REVISAR com sugestão só como proposta. Máscara de telefone pode colidir entre famílias: chave de decisão = (família, telefone mascarado).
- Mensagem de cadastro ↔ família: casar pelos nomes completos das crianças no texto (modelos vazios não casam); família sem mensagem usa o trecho JSON SEM telefones (`content_kind=legacy_json`).
- Nome de exibição = primeiro token do `full_name`: em dados de teste com prefixo `[TESTE]` ele vira `[TESTE]`; ajuste as asserções, não o código.
- Resumo que já termina em ponto: `rstrip('. ')` antes de compor templates (evita `..`).
- Coordenação via CLI local: o operador age em nome de uma pessoa (`--approver`/`--author`, `identity_for_person`); o papel sempre vem do banco.
- `PERSON_ROLE` e `STAFF_ASSIGNMENT` não têm `active`: remover = apagar a associação, com auditoria; o resto só desativa/revoga.
- `outbox dispatch` com `target_format` pendente deve falhar explicitamente (`failed`), nunca marcar `sent`.
