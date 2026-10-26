---
name: feedback-atas
description: "Use when logging feedback or atas via the moca CLI (SQLite)."
version: 0.2.0
author: Filip Lopes, Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [feedback, atas, melhorias, Telegram, WhatsApp, moca]
    related_skills: [moca-app, evolution-api]
---

# Feedback e Atas (BMoca)

Catalogar o que as pessoas dizem sobre as aulas/encontros e sobre a aplicação, para alimentar melhorias. A **ata é um tipo de feedback**. Use esta skill quando alguém der feedback no Telegram/desktop, quando um job ler um grupo de WhatsApp, quando o usuário pedir para registrar/consultar feedbacks ou organizar transcrições de reuniões.

## Onde fica
No banco SQLite da app Moca (`$PROFILE/data/moca.db`), acessado SOMENTE pelo CLI `moca` (`$PROFILE/app/.venv/bin/moca`; `$PROFILE` = `/Users/filipelopes/.hermes/profiles/bmoca`). Não existem mais arquivos Markdown de feedback ou ata (arquivados em `data/legacy_archive/`); não crie nenhum. Pessoas, telefones e papéis também estão no banco (`moca people ...`); Telegram → pessoa em `app/config/identities.toml`.

## Como gravar
- **Feedback da equipe (desktop/Telegram):** `moca feedback add --topic encontro|aplicacao|crianca --author <ref da pessoa> [--student <ref>] --original-text "..." --summary "..." [--event-date-text "ontem|DD/MM|DD/MM/AAAA"] [--domain <código>]`. O `ref` da pessoa vem de `moca people resolve --phone <dígitos> --json` ou `moca people list --json`. `--original-text` é o texto copiado do que a pessoa disse; `--summary` é sua síntese curta (≤ 600). Sem data informada, não invente: omita `--event-date-text`.
- **Ata de job:** monte a ata em `cache/scratch/ata-<grupo>-<data>.md` (seções `### HH:MM`, linhas `**Nome (HH:MM):** fato dito`, áudios marcados `(áudio)`), resolva cada falante com `moca people resolve --phone <dígitos> --json` e grave com `moca atas record --group "<nome do grupo>" --window-start <ISO -03:00> --window-end <ISO -03:00> --file <arquivo> --speaker <ref> ... --unresolved "…1234" ... --producer job:<nome>`. Uma ata por janela (reexecução = `duplicate`). A ata é recusada se citar nome completo de criança.
- **Falante sem cadastro:** `Falante não identificado (…1234)`; nunca invente nome.
- **Resumo enviado por job:** depois de confirmar o envio no destino exato, registre o canal real: `moca outbox record-external --channel evolution --instance "<instância>" --to <JID> --external-id <id> --file <texto>`; para o bot nativo, use `--channel whatsapp_native` e confirme a sintaxe vigente em `--help`. Não acrescente o prefixo antigo no WhatsApp/Telegram (skill `bmoca-identity`). Se o validador ainda exigir o prefixo, trate a migração coordenada com `moca-app`; não burle a validação nem declare registro concluído.
- **Consultar:** `moca docs list --type feedback|ata [--since AAAA-MM-DD]` e `moca docs show <ref> --json` (leitura administrativa, auditada).

## Verificação
`moca atas record` e `moca feedback add` imprimem o `ref` do documento (ou `duplicate`). Leia de volta com `moca docs show <ref> --json` e confirme tipo, autor/falantes e data. Erro de gravação: reporte ao usuário; não grave em outro lugar.

## Regras
1. **Autoria:** `narrado` = a pessoa escreveu/falou; `autoproduzido` = gerado por job/Moca. Autor do feedback = a pessoa resolvida pelo cadastro (Telegram: `identities.toml`). Se não houver cadastro, avise o usuário; nunca invente nome.
2. **Ata completa, só de conteúdo e atribuída:** uma linha por fala relevante (feedback, opinião, sugestão, pergunta, decisão, combinado, aviso logístico), no formato "Fulano disse X". Omita só conversa social sem conteúdo. O resumo de envio é derivado da ata e é o produto curto; a ata não é encolhida para caber nele. Sem dados de saúde nem nomes de crianças.
3. **Fato ≠ interpretação:** parafraseie o que foi dito; leitura pedagógica vai separada, opcional.
4. A ata é gravada ANTES do envio do resumo. Falha ao gravar não bloqueia o envio, mas deve ser reportada.
5. Determine autoria pelos metadados confiáveis da origem e pelos IDs de envio/outbox, não só pelo texto. Na conta dedicada, `fromMe` é a assistente; em conta pessoal, é o dono da instância, salvo envio automatizado identificado. Preserve essa distinção ao migrar históricos; o prefixo legado ajuda a reconhecer envios antigos, mas sua presença isolada não prova autoria.
6. Privacidade: ao relatar a uma pessoa, não exponha feedbacks atribuídos a outra sem autorização do usuário principal.
7. Relato de família ≠ observação da equipe ≠ avaliação; nunca diagnostique.
8. Atas, feedbacks e logs de perguntas não são KB pública por padrão. Para responder às famílias, recupere apenas fatos publicados para aquele público, com fonte e validade; sintetizar ou remover nomes não autoriza divulgar conversa interna.
9. Ao planejar mensagens para o grupo (job ou envio manual), se o conteúdo envolver pauta, feedback ou ideias, estruture com antecedência, verifique se há registros anteriores no banco (`moca docs list`) e apresente ao usuário para revisão antes de agendar ou enviar. Não envie resumos sem validação prévia.
10. O rascunho de pauta/ideias deve ser estruturado em Markdown (`/Users/filipelopes/.hermes/profiles/bmoca/cache/scratch/mensagem_grupo.md`) e validado pelo usuário antes de qualquer agendamento ou envio.

## Organização de transcrições e documentos derivados
1. Leia a fonte integral e confirme se há áudio ou somente texto antes de identificar falantes; nome de arquivo não comprova data nem local da reunião.
2. Preserve uma cópia bruta durável antes de editar o arquivo solicitado. Quando pedida edição direta, entregue o próprio TXT atualizado, não apenas uma proposta no chat.
3. Organize primeiro as falas, não substitua a transcrição por um resumo de requisitos. Preserve conteúdo relevante, perguntas, ressalvas e ambiguidades; separe notas editoriais das falas e não crie horários.
4. Identifique autoria comprovada pela fonte e pelo cadastro. Se o usuário autorizar inferência, marque cada atribuição provisória como `Nome [inferido]` e explique o método no cabeçalho; mantenha trechos ambíguos como `Falante não identificado`. Não alegue escuta ou distinção de vozes quando só há texto.
5. Não transforme falas inferidas em registros individuais de feedback com autoria confirmada. Sem data original ou autoria verificável, mantenha a minuta separada dos registros do banco.
6. Quando também houver pedido de planejamento, produza um segundo documento (histórias de usuário, requisitos, critérios de aceite, casos de uso, follow-up); distinga decisões da reunião, inferências e recomendações novas.
7. Verifique o arquivo final e a integridade da cópia bruta; entregue os arquivos e um follow-up curto. Não confunda documentação entregue com integração implantada.

Roteiro detalhado: `references/transcricoes-e-requisitos.md`. Plano para outro agente executar: skill `moca-app` → `references/planejamento-para-agente-executor.md`.

## Backfill a partir de áudios/mensagens do WhatsApp
Baixe e transcreva os áudios (skill `evolution-api`, `references/media-download-and-transcription.md`), junte com as mensagens de texto do dia e monte UMA ata por janela (comando acima). Áudios longos: resuma em fato atribuído, sem dados de saúde das crianças e sem nomes incertos. O resumo para envio é gerado depois, só mostrado ao usuário em chat, e nunca enviado sem pedido explícito.

## Job diário de ata + resumo (Equipe Pedagógica)
Cron diário 23:00: lê a janela 23:00→23:00 do grupo, grava a ata completa ANTES do envio, gera o resumo `🤖 *Resumo do dia (DD/MM)*` e envia só a esse grupo, com leitura de volta e `record-external`. Dia sem conteúdo: não envia. Antes de criar/alterar um job que envia ao mesmo grupo, liste os jobs existentes: resumos semanais do mesmo grupo duplicam o diário; avise o usuário e deixe-o decidir pausar (Q-10).
