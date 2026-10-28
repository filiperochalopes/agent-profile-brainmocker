# Planejar uma refatoração para um agente executor menos capaz

Pedido típico: "analise tudo, crie o modelo (código), os casos de uso e um plano estrito; não crie mais código".

## 1. Inventário antes de opinar
- Liste o profile inteiro (exceto `cache/scratch`, `sessions`, `logs`, `whatsapp/session`), skills do domínio (carregue com `skill_view`), `memories/`, `SOUL.md`, `cron/jobs.json` (id, schedule, deliver, skills, início do prompt), `policies/`, scripts.
- `.env`: só nomes de chaves e allowlists (`grep -E '^(X|Y)=' .env`), nunca valores de segredo.
- Procure dados "já existentes" mencionados pelo usuário fora do lugar óbvio (ex.: cadastro em `cache/*.json`); inspecione só a estrutura (chaves, contagens), sem despejar dados pessoais.
- Faça auditoria de segurança do canal (allowlist `*`, ferramentas expostas, sessões existentes). Risco ativo vira pergunta imediata ao usuário, não nota de rodapé.
- Confirme mecanismos do Hermes na doc local (`~/.hermes/hermes-agent/website/docs/...`) e no `--help`, não de memória.

## 2. Perguntas em lote, antes de escrever
Uma chamada `clarify` com até 5 perguntas que MUDAM a arquitetura (onde fica o operacional, fonte da verdade, divisão de canais, aprovação de envios, risco ativo), com a opção recomendada primeiro. O resto vira lista Q-xx nos documentos, com valor padrão quando possível.

## 3. Entregáveis
1. Ambiente `uv` (`uv init --package --name <app> --python 3.12 --vcs git app`, `uv add sqlalchemy alembic`, `uv add --dev pytest ruff`, ruff/pytest no `pyproject.toml`).
2. `models.py` validado de verdade (schema criado, colunas comparadas ao ER, cada restrição violada de propósito). Inclua o script de validação como apêndice do plano para virar teste.
3. `CASOS_DE_USO.md`: decisões (D-xx), escopo dentro/fora, papéis × canais, HUs revisadas (critérios alterados marcados), UCs (ator, canal, gatilho, fluxo, exceções, gravações, testes), regras transversais, rastreabilidade, testes T-xx, perguntas Q-xx.
4. `PLANO_DE_IMPLEMENTACAO.md` (abaixo).

## 4. Formato do plano (o executor segue literalmente)
- Seção 0: regras rígidas (não alterar o modelo, não inventar dados, não ler segredos, não mexer em outro profile, `config set` em vez de editar YAML, sem envio a famílias em teste), condições de parada, definição de pronto.
- Inventário com destino de cada artefato; arquitetura em ASCII; requisitos que entram e que NÃO entram (explícito).
- Árvore de pastas com a tarefa que cria cada arquivo.
- Especificações fechadas: JSON de provenance por tipo, chaves de idempotência exatas, máquina de estados de envio, matriz de autorização, CLI (comandos, saídas, exit codes), protocolo de ferramentas, comandos do Hermes exatos.
- Fases numeradas; cada tarefa com passos, arquivos e "Pronto quando" verificável. Portões humanos explícitos (CSV de revisão → CSV de decisão). Spikes marcados quando um comportamento do runtime precisa ser confirmado antes de codar.
- Migração: fonte → destino por linha, regra de casamento determinística, ordem do apply, verificação de contagens, arquivamento antes de apagar.
- Riscos com rollback; apêndices com templates de config, scripts de cron e textos de atualização de skills/SOUL.

## 5. Verificar os documentos antes de entregar
- Blocos de código balanceados (conte as cercas).
- Extraia o apêndice de código e execute-o.
- Procure nomes de crianças e telefones completos nos docs versionados e remova.
- Commit inicial no git da app.
