# Triagem de grupos, conhecimento público e jobs nativos

## 1. Delimitar antes de alterar
1. Releia as decisões atuais de identidade em `bmoca-identity` e confirme se o pedido é planejamento ou implantação. Não altere produção durante uma análise de viabilidade.
2. Monte três listas independentes: grupos onde a assistente pode responder; fontes que pode ler; destinos de cada job. Uma fonte da equipe não autoriza respostas naquele grupo nem publicação das suas conversas às famílias.
3. Liste os jobs com `cronjob_manage(action='list')`, leia seus prompts completos e scripts chamados e produza a matriz fonte → processamento → destino → canal. Não conclua pelo nome do job nem por `deliver`: scripts podem importar Evolution, e prompts podem enviar a mais de um grupo ou contato.
4. Inspecione `config.yaml`, `app/config/channels.toml`, o plugin e a CLI com saídas mínimas. Leia segredos apenas no processo autorizado, nunca para a auditoria. Não abra `moca.db` diretamente.

## 2. Definir o contrato público da KB
1. Descubra o que a app já oferece em `services/knowledge.py`, ferramentas `moca_*` e comandos `bmoca-app guidance --help` / `bmoca-app docs --help`. Não trate um documento `reference` ou uma ata como automaticamente publicável.
2. Proponha fatos curtos e recuperáveis por assunto: próximo encontro, horário, local, link do mapa, materiais e avisos confirmados. Separe o local padrão de exceções por encontro.
3. Para cada fato, especifique valor, fonte identificável, origem, público/grupo autorizado, confirmação, vigência e substituição/revogação. Use estruturas existentes e `document.provenance`; não invente tabelas ou campos físicos sem aprovação.
4. Autorize a recuperação ANTES de entregar trechos ao modelo. Uma regra no prompt para não divulgar não substitui o filtro de acesso.
5. Use contexto recente do próprio grupo somente quando permitido e necessário, com janela limitada e origem preservada. Mensagem mais nova não é necessariamente decisão: diferencie pergunta, proposta, confirmação e cancelamento. Conflito ou fato vencido não deve virar resposta assertiva.
6. Publique decisões oriundas da equipe como fatos aprovados para as famílias, não como resumo automático de toda a conversa interna. Remover nomes não torna conteúdo sensível público.
7. Evite um log público de perguntas: dúvidas podem conter saúde, conflitos ou dados familiares. Prefira métricas mínimas de intenção/resultado sem corpo; mantenha eventuais fontes restritas com retenção definida.

## 3. Projetar o acionamento econômico por menção

O MVP vigente foi simplificado para menção nativa: não implantar o classificador de toda conversa. Use chamada + pergunta citada + agenda/KB autorizada; contexto vizinho é opcional e não deve bloquear o piloto. Agenda criada não comprova eventos existentes nem integração com ferramentas; recuperar a referência de criação na sessão e confirmar por API. Descrições de eventos só viram KB após regra editorial de público; não retornar convidados ou notas internas.

1. Valide plataforma, JID e identidade fornecidos pelo adaptador; nunca os deduza de texto. A allowlist de grupos do gateway não substitui a autorização de pessoas nas ferramentas.
2. Antes do agente, descarte eventos próprios/duplicados e mensagens sem menção nativa. Não chamar LLM, STT ou visão em mensagens comuns; conferir exceções do adapter e vias busy/steer.
3. Mensagem de terceiro respondida por outra pessoa com menção deve preservar o texto citado. Só digitar nome/número não garante marcação; nomes salvos diferentes funcionam pela identidade da menção. Não assumir contexto ao redor ou futuro. Sem pergunta citada inteligível, pedir esclarecimento.
4. Quando interpretação for necessária, proponha uma chamada curta e limitada com a pergunta e poucos fatos autorizados. Verifique a API suportada de `ctx.llm` e a configuração de modelo auxiliar; não assuma que a chamada auxiliar usa um modelo barato por padrão.
5. Em chamada explícita sem fonte suficiente, informar a ausência ou limitação sem inventar nem repetir conteúdo sensível. Não criar casos, feedbacks nem publicações como efeito colateral da consulta. Sem menção, encerrar antes do agente em vez de depender de `[SILENT]`.
6. Defina deduplicação, limite de respostas, teste de pergunta já respondida e retenção do buffer para evitar loops e repetição. Em gateway compartilhado, particione o buffer por profile/plataforma/chat.
7. Verifique o silêncio no runtime, não apenas no prompt: `gateway/response_filters.py` reconhece `[SILENT]`, mas o contrato de `silence_allowed` também depende de `reply_expected=False` ou evento interno. Prefixar o marcador com texto o descaracteriza. Consulte a skill `hermes-agent` e carregue nela a referência de hardening do gateway de mensagens.

## 4. Separar migração de envio e de leitura
1. Confirme o envio nativo com `hermes -p bmoca send --help` e o adaptador `app/src/moca/channels/hermes_send.py`. Comando de envio: `hermes -p bmoca send --to whatsapp:<JID> --json --file <arquivo>`; execute somente com autorização e destino de teste permitido.
2. Antes de remover o prefixo, localize `SEND_PREFIX` em `domain/codes.py`, validações em `services/outbox.py`, geradores de mensagens, plugin, `whatsapp.reply_prefix`, prompts e testes. Esvaziar só o prefixo do gateway não remove texto escrito no payload nem exigências do banco.
3. Atualize autoria: no bot dedicado, `fromMe` representa a conta da assistente; em conta pessoal, representa o dono da conta. Preserve o contexto da origem e use IDs de envio/outbox para excluir mensagens automáticas. Texto com o nome do bot não prova autoria.
4. Audite o histórico nativo de verdade: armazenamento persistente, consulta por chat/janela, paginação, limites, mensagens rejeitadas pelo filtro, sincronização, desconexões e mídias. Sessões de LLM não são um arquivo completo do grupo.
5. Não equipare a capacidade de envio Baileys à leitura histórica completa. Migre primeiro a saída se ela estiver validada; mantenha a fonte existente para leitura até o coletor comprovar a cobertura necessária. Preserve o guarda de acesso no Telegram enquanto houver Evolution.
6. Para o job de Drive, verifique imagens/documentos, download e arquivos já arquivados; não migre só mensagens de texto e declare o job inteiro concluído.
7. Escolha um único responsável pela entrega: script/outbox ou entrega do scheduler. Preserve janela, destinos aprovados, modelo/provider existentes, idempotência e reconciliação. Jobs concluídos não devem ser reativados.
8. Confirme se resumos diários e semanais para o mesmo público são desejados; não pause nenhum por inferência.

## 5. Critérios para sair do planejamento
- Testes offline: chamada com menção, resposta citada à pergunta de terceiro, nome salvo diferente, ausência de menção sem LLM, informação ausente/vencida/conflitante, tentativa de acesso privado e JID não autorizado.
- Testes de autorização: KB da equipe nunca aparece na consulta das famílias sem publicação; ferramenta continua restrita mesmo quando o gateway admite o grupo inteiro.
- Testes de silêncio: nada de marcador, prefixo, aviso de ferramenta ou fallback visível nas mensagens ignoradas; medir chamadas ao modelo, não estimar economia sem dados.
- Testes de coleta: janela completa, duplicatas, reinício/desconexão, mensagens próprias e mídias; ausência de cobertura deve ser explícita.
- Testes de envio autorizados: verificar ID e texto no destino exato, registrar o canal real e não reenviar timeout ambíguo.
- Leia de volta cada job alterado, confirme fontes/destinos/agenda/modelo e documente o que foi testado, o que só foi proposto e o que ainda depende de aprovação. Não anuncie migração completa com base apenas em código ou documentação.
