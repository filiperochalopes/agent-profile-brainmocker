---
name: moca-app
description: "Use when building or operating the Moca SQLite app."
version: 0.1.0
author: Filipe Lopes, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [SQLite, SQLAlchemy, Alembic, uv, migration, WhatsApp, planning]
    related_skills: [feedback-atas, evolution-api, hermes-agent, age-calculator]
---

# Moca app (SQLite + Python local)

## When to Use
A app `moca` em `$PROFILE/app` (`$PROFILE` = `/Users/filipelopes/.hermes/profiles/bmoca`) substitui cadastros em JSON e feedbacks/atas em Markdown por um banco SQLite estruturado. Use esta skill para: escrever ou revisar código da app, executar fases do plano, migrar dados legados, planejar novas partes (modelo, casos de uso, plano para agente executor) ou operar banco/backup/allowlist.

## Onde está cada coisa
- Modelo (fonte única): `app/src/moca/db/models.py` — tradução fiel do modelo informacional ER (18 tabelas).
- O QUÊ: `app/docs/CASOS_DE_USO.md` (HUs, UCs, testes T-xx, perguntas Q-xx). O COMO: `app/docs/PLANO_DE_IMPLEMENTACAO.md` (fases, CLI, provenance, gates).
- Dados: `$PROFILE/data/` (chmod 700): `moca.db`, `audit/AAAA-MM.jsonl`, `backups/`, `legacy_archive/`. Nunca versione bancos SQLite brutos, WAL/SHM ou auditoria no repositório do app; mantenha `*.db` ignorado. Quando for necessário histórico de recuperação versionado, use `moca db backup` para produzir o backup verificado e derive dele um artefato de dump para um repositório privado de dados, separado do código e revisado quanto a dados pessoais antes do commit.
- Relatórios de execução: `app/docs/relatorios/fase-N.md`.

## Regras sempre válidas (decisões do usuário)
1. **O modelo informacional é seguido à risca.** Não crie tabelas nem colunas. Tudo operacional (idempotência, estados, aprovação, entrega, casos, legado) vai em `document.provenance` (JSON versionado) e `document_relationship`. Auditoria vai em JSONL FORA do banco. Precisa de estrutura nova? Pare e pergunte ao Filipe.
2. **O banco é a fonte da verdade.** Não gere Markdown de feedback/ata; depois do seed os Markdown legados são arquivados (tar + manifesto SHA-256) e removidos.
3. **Canais:** prefira o gateway nativo do Hermes e o número dedicado da Edite para respostas e envios de jobs. Avalie leitura histórica separadamente do envio: só retire a Evolution de um fluxo após comprovar cobertura da janela, mídias e recuperação após desconexão. Registre o canal real; migração planejada não significa migração implantada.
4. **Identidade só do adaptador** (`HERMES_SESSION_*` → `MOCA_CALLER_*`), nunca de texto nem de argumento de ferramenta. Negar por padrão; sem cache de autorização.
5. **Determinístico onde der:** digest, roteamento, datas relativas, idade (port do age-calculator), títulos. Sem LLM nesses caminhos.
6. **Identidade de saída:** Edite no WhatsApp; sem prefixo obrigatório `Moca falando aqui:` no WhatsApp ou Telegram (skill `bmoca-identity`). Remova exigências legadas de forma coordenada em config, prompts, código e testes, sem reescrever registros históricos. Envio ambíguo nunca é reenviado sem reconciliação.
7. **Privacidade:** nada de nomes de crianças em docs versionados, logs, auditoria ou mensagens de commit; telefone só mascarado (`5575****10`) ou como hash na auditoria.
8. **Nunca inventar** papéis, áreas, turmas, vínculos ou casamento telefone→pessoa: gerar CSV de revisão e esperar decisão humana (portão).

## Respostas automáticas em grupos e KB pública
- Faça triagem de toda mensagem admitida no grupo autorizado, sem exigir menção nem prefixo de chamada. Responda só a perguntas pertinentes com evidência acessível ao público daquele grupo; caso contrário, silêncio real, não uma recusa automática para cada conversa.
- Mantenha separados os JIDs autorizados para responder, as fontes de leitura e os destinos de jobs. Não habilite outros grupos por consequência de uma migração; confirme o escopo vigente, inicialmente Escola Sem Nome.
- Minimize tokens: filtro pré-agente, busca de fatos compactos e respostas determinísticas quando suficientes; não envie todo o histórico nem todo o acervo a cada triagem.
- Distinga fatos fixos (local/mapa) e temporais (próximo encontro). Exija fonte, público autorizado, estado de confirmação e validade; uma pergunta ou sugestão não atualiza a resposta oficial.
- Não use atas privadas, feedbacks ou um log indiscriminado de perguntas como KB pública. Informação da equipe só atravessa para as famílias após publicação autorizada para esse público.
- Para o procedimento de investigação e os critérios de migração, consulte `references/group-knowledge-and-native-jobs.md`. É orientação de projeto; verifique os contratos reais antes de implementar.

## Procedimento de trabalho na app
1. `cd $PROFILE/app`; sempre `uv run ...` / `uv add ...` (nunca pip). Python 3.12.
2. Antes de mexer, leia a fase/tarefa correspondente no plano e o critério "Pronto quando".
3. Implemente + testes; rode `uv run ruff check src tests && uv run ruff format --check src tests && uv run pytest`.
4. Mudança de schema só via Alembic (`render_as_batch=True`); confira à mão CHECKs e índices funcionais no autogenerate.
5. Trate `app/` como repositório de código independente do profile: versione fonte, testes, migrações, documentação, configurações de exemplo e lockfile nele. Não inicialize um repositório pai e faça `git add .` sem decidir como representar esse repositório aninhado, pois o Git o registra como gitlink em vez de incorporar seus arquivos.
6. Commit pequeno: `git -c user.name="Moca (Hermes)" -c user.email=moca@local commit -m "fase N.M: ..."`.
7. Registre a saída REAL das verificações no relatório da fase.

## Validar um modelo/schema antes de entregar
Crie o schema num SQLite em memória com `PRAGMA foreign_keys=ON`, compare tabelas/colunas/nulabilidade com o ER e tente violar cada restrição (cada uma deve falhar). Pegue `IntegrityError`, `StatementError`, `ValueError`. O script de contrato está no Apêndice A do plano. Pitfalls de SQLite/SQLAlchemy: `references/sqlite-sqlalchemy-pitfalls.md`.

## Planejar para um agente executor menos capaz
Quando o pedido for "modelo + casos de uso + plano" para outro agente executar, siga `references/planejamento-para-agente-executor.md` (inventário, perguntas em lote, entregáveis, formato do plano, verificação dos documentos).
Para análises de viabilidade, entregue uma conclusão utilizável com evidências, alternativas, fases e critérios de aceite; separe capacidade documentada, comportamento verificado e hipótese a testar. Não apresente um status de investigação como se fosse o plano concluído.

## Implementação das fases e migração
Receitas (Alembic, env de teste, hooks do Hermes, ruff), portões humanos e armadilhas de domínio: `references/implementacao-e-migracao.md`. Regra: sem decisões humanas (Q-01..Q-04) não se grava dado real; se um comando ficar sem aprovação, pare e relate.

## Grupos, KB pública e jobs

Para o planejamento de Edite, triagem sem menção e migração de jobs, carregar `references/grupos-kb-e-jobs.md`. O plano distingue decisões novas de comportamento ainda implantado, incluindo a remoção coordenada do prefixo legado.

## Pitfalls
- Não aplique mudanças de gateway/allowlist sem backup de `.env` e `config.yaml` em `$PROFILE/backups/<motivo>-<timestamp>/`; recarga e verificação do WhatsApp: carregar a referência de hardening do gateway de mensagens na skill `hermes-agent` (arquivo dessa outra skill, não desta).
- Preserve memórias que o usuário decidir versionar; não inclua `memories/` em um `.gitignore` genérico só por serem dados de runtime.
- Mantenha credenciais, tokens OAuth e sessões de mensageria fora do versionamento; eles permitem acesso direto a serviços e contas.
- Cache (`cache/`) não é durável nem fonte oficial: dados de cadastro achados lá precisam ser migrados para o banco, não referenciados.
