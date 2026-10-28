---
name: moca-operacao
description: "Use when operating the Moca app day to day (admin only)."
version: 0.1.0
author: Filipe Lopes, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [moca, operacao, runbook, SQLite]
    related_skills: [moca-app, feedback-atas, evolution-api]
---

# Moca: operação diária (só administração)

Runbook completo: `$PROFILE/app/docs/RUNBOOK.md` (`$PROFILE` = `/Users/filipelopes/.hermes/profiles/bmoca`). Todos os comandos: `cd $PROFILE/app && uv run moca ...` (ou `$PROFILE/app/.venv/bin/moca`). Esta skill não tem segredos e só aponta comandos que a própria app já restringe a `admin_tecnico`/operador local. Fica desabilitada no WhatsApp.

## Comandos de uso diário
- Saúde: `bmoca-app db check` · backup manual: `bmoca-app db backup` (diário às 02:30 por cron, mantém 30).
- Pessoas: `bmoca-app people list [--role R] [--json]` · `bmoca-app people show <ref>` · `bmoca-app people resolve --phone <dígitos> --json` · `bmoca-app people add-family --file f.toml --dry-run|--apply` (modelo em `app/config/templates/familia.toml`).
- Revogar acesso: `bmoca-app people deactivate <ref>` · `bmoca-app people contact deactivate <ref> --phone D` · `bmoca-app people link revoke <responsável> <criança>` e depois `bmoca-app allowlist render` + `bmoca-app allowlist apply --confirm`.
- Áreas/atribuições: `bmoca-app people staff assign <ref> --group "Grupo 1-2" --domain linguagens`.
- Fila de saída: `bmoca-app outbox list [--status ambiguous]` · `bmoca-app outbox reconcile <ref> --result sent|failed [--external-id ID]`. Nunca reenviar sem reconciliar.
- Documentos: `bmoca-app docs list --type feedback|ata|report|reference` · `bmoca-app docs show <ref> --json` (auditado).
- Orientações: `bmoca-app guidance draft|submit|publish|revoke|list` (aprovador com papel coordenacao via `--approver <ref>`).
- Casos: `bmoca-app cases list|show|close`.
- Digest de segunda: `bmoca-app jobs staff-weekly-digest --dry-run` antes de qualquer envio real.

## Regras rígidas
1. O banco é a fonte da verdade; nunca abra `moca.db` por fora nem grave Markdown de feedback/ata.
2. Nunca imprima segredos (`.env`, Keychain, `whatsapp/session/`) nem telefone completo (use mascarado `5575****10`).
3. Nunca envie a famílias em teste; testes de envio só para os números do Filipe e do Robson.
4. Mudança de schema só por Alembic e só com pedido do Filipe; não altere `models.py`.
5. Reinício do gateway: `hermes -p bmoca gateway restart` (2 tentativas; se o WhatsApp não reconectar, pare e avise o Filipe).
6. Use Edite no WhatsApp, sem prefixo obrigatório no WhatsApp ou Telegram (skill `bmoca-identity`). Ao migrar, atualize config, payloads de jobs e validadores da outbox em conjunto; não confunda a decisão de identidade com alteração já aplicada ao runtime.
7. Ao validar o WhatsApp, não confie no que a Moca respondeu: confirme a escrita na auditoria/banco antes de declarar sucesso ao Filipe.
8. Atribuição de áreas: confirme nome completo (ex.: Raquel Eustáquio **Cardoso**) e turmas antes de gravar; `staff assign` é por grupo × área.
