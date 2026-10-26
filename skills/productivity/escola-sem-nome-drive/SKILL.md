---
name: escola-sem-nome-drive
description: "Use when archiving Escola Sem Nome media to Drive daily."
version: 1.0.0
author: Filipe Lopes, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Evolution API, Google Drive, WhatsApp, cron]
    related_skills: [evolution-api, google-workspace]
---

# Escola Sem Nome: arquivo diário no Drive

Rotina diária (03:00, GMT-3) que pega as imagens e documentos enviados no dia anterior no grupo "Escola Sem Nome" e os armazena em uma pasta com o nome da data dentro da pasta Drive "Arquivo".

## Parâmetros fixos

- Grupo: `Escola Sem Nome`, JID `120363429552702512@g.us`.
- Instância Evolution: `Filipe Lopes - Pessoal` (codificar o espaço como `%20`).
- Pasta raiz no Drive: `131RkBdxE_b7Z6TIKvfkFiqEcq4jZPq0_` ("Arquivo").
- Nome da pasta do dia: `YYYY-MM-DD` (data coberta pela varredura).
- Notificação Telegram (somente se houver imagens): user_id `1106796150` (Robson), via `deliver: telegram:1106796150`.

## Arquivos

Os arquivos reais ficam em `~/.hermes/profiles/bmoca/scripts/` (o cron só aceita scripts ali; links simbólicos de fora são rejeitados). A pasta da skill guarda links para eles.

- `arquivar_escola_diario.py`: pipeline completo. Argumento opcional `YYYY-MM-DD` para reprocessar outro dia.
- `evo_client.py`: cliente Evolution API usado pelo script (mesmo mecanismo do `evo.py`: chave lida do Keychain apenas no processo local). **Também serve para análises ad-hoc do grupo** (roster, mensagens, cadastros) via `execute_code` — ver skill `evolution-api` seção "Reusable local client" e "Cadastro analysis workflow".
- Job cron: `97cb2b194a22` ("Escola sem nome - arquivo diário no Drive"), primeira execução 2026-10-24 03:00.

## Comportamento

1. Varre as mensagens do dia anterior (00:00 a 24:00 GMT-3), paginando do mais recente para o mais antigo.
2. Considera `imageMessage` e `documentMessage` (também `documentWithCaptionMessage`). Ignora áudios, figurinhas, reações e álbuns (as imagens do álbum já vêm como registros próprios).
3. Se não houver nenhuma imagem nem documento: não cria pasta e não imprime nada (cron não envia nada, equivalente a `[SILENT]`).
4. Se houver: cria (ou reutiliza) a pasta `YYYY-MM-DD` no Drive e envia os arquivos que ainda não estão lá. A deduplicação é feita pelo ID da mensagem (8 primeiros caracteres), que aparece no nome dos arquivos.
5. Notificação no Telegram somente quando houver imagens: "documentos do grupo Escola sem nome foram devidamente armazenados no Drive", com contagens e link da pasta. Se houver falhas de upload, a notificação informa a quantidade.

## Job (cron)

Criado com `cronjob_manage`: `schedule: "0 3 * * *"`, `no_agent: true`, `script` apontando para o script absoluto, `deliver: "telegram:1106796150"`. Como é `no_agent`, o stdout do script é entregue literalmente; por isso o script só imprime quando há imagens.

## Dependências e pitfalls

- Drive: o perfil bmoca não tem token próprio. O script usa `HERMES_HOME=/Users/filipelopes/.hermes` para o `google_api.py` do google-workspace (token da conta do Filipe). Sem essa variável, o token não é encontrado.
- Busca no Drive: consultas `'<id>' in parents` só funcionam com `--raw-query` e `trashed = false`.
- Upload: o `google_api.py drive upload` retorna JSON; verificar `status == "uploaded"`. Uma checagem por `grep` no texto falhou silenciosamente antes; não usar.
- A pasta de cache é `cache/escola_arquivo` (não `cache/scratch`, que é podada após 24h).
- Ao alterar JID, instância ou pasta, atualizar as constantes no topo do script e a descrição do job.

## Verificação

- Rodar `python3 ~/.hermes/profiles/bmoca/scripts/arquivar_escola_diario.py 2026-10-23`: deve listar 30 mídias já presentes, sem criar duplicatas, e imprimir a notificação.
- Confirmar o job com `cronjob_manage action=list`: schedule `0 3 * * *`, deliver `telegram:1106796150`, no_agent true.
