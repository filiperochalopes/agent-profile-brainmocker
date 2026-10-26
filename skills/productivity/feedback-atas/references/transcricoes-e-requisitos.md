# Transcrições de reuniões e planos derivados

## 1. Preparar e preservar a fonte
- Leia integralmente a transcrição e identifique mídias realmente disponíveis; não use uma visualização truncada como fonte completa.
- Preserve o original em local durável antes da substituição. Scratch serve para montagem intermediária, não como única cópia de segurança a entregar.
- Confirme participantes pelo cadastro disponível sem resolver apelidos ou nomes parecidos como equivalentes automaticamente.

## 2. Organizar as falas
Use cabeçalho com participantes informados, fonte, disponibilidade de áudio e lacunas de data/local. Numere turnos para facilitar correções e agrupe por temas sem alterar a ordem lógica do diálogo.

Separe três níveis de certeza:
- Confirmado: fonte identifica o remetente ou o participante validou a fala.
- Inferido: dinâmica do texto sugere o participante; identificação provisória explícita em cada turno.
- Não identificado: autoria ou limites do turno insuficientes.

Com áudio, separe segmentação de vozes de identificação nominal; obtenha um trecho reconhecido por participante para mapear vozes. Só documente escuta e timestamps quando realmente disponíveis. Em texto automático, preserve expressões ambíguas com nota editorial em vez de repará-las silenciosamente quando mudam permissões, nomes ou decisões.

Uma transcrição organizada não é uma ata aprovada. Preserve trechos finais incertos separadamente quando seu significado não for confiável; não derive requisitos de brincadeiras, ruído ou erros de reconhecimento.

## 3. Criar o plano separado quando solicitado
Estruture o segundo documento em:
1. Objetivo, escopo e exclusões.
2. Atores e matriz de permissões.
3. Histórias de usuário com prioridade e critérios observáveis.
4. Requisitos funcionais e não funcionais rastreáveis às histórias.
5. Casos de uso: ator, pré-condição, fluxo, exceções e pós-condição.
6. Guardrails e mecanismos técnicos necessários.
7. Skills existentes a reaproveitar, extensões e novas skills propostas.
8. Dados e arquitetura mínima.
9. Integração e operação verificadas na documentação aplicável.
10. Testes de aceite, fases, pendências e follow-up.

Identifique a proveniência das afirmações: discutido na reunião, proposta adicional, documentação oficial ou estado local observado. Preserve a distinção entre planejamento e execução; comandos de configuração não executados não são evidência de integração funcional.

## 4. Planejar automações pedagógicas com segurança
- Separe cadastro, feedback privado, conhecimento aprovado, encaminhamento, relatórios, grupos e operação em blocos de casos de uso; um único fluxo genérico não cobre suas diferentes permissões.
- Distinga skills procedimentais de controles executáveis: autorização por criança, segregação de dados, aprovação de publicação e validação de destinos exigem backend/configuração/testes, não apenas instruções ao modelo.
- Não trate administrador de grupo, administrador de comandos e papel pedagógico como a mesma permissão; menor privilégio precisa ser aprovado explicitamente quando a reunião cogita acesso amplo.
- Vincule fatos a fontes e datas; diferencie dificuldade do responsável ao aplicar a atividade de dificuldade observada da criança.
- Não use o repositório de atas de adultos como banco de históricos infantis sem arquitetura própria; as regras de minimização e acesso são distintas.
- Mantenha dados individuais fora de memória global, skills e base de conhecimento para famílias; o contexto compartilhado pode atravessar sessões.
- Trate aprovação como estado associado à versão e ao destino; alterar qualquer um exige nova revisão.

## 5. Verificar integrações sem prometer implementação
Para Hermes, carregue `hermes-agent` e consulte documentação oficial e ajuda da CLI antes de recomendar comandos. Diferencie adaptador WhatsApp nativo de acesso pela Evolution API; controles de um caminho não se aplicam automaticamente ao outro.

Antes de sugerir instalar ou reiniciar gateway, consulte seu status e identifique compartilhamento/multiplexação; uma ação no host pode afetar outros profiles. Mantenha mudanças fora do escopo da criação documental até haver autorização.

Compare caminhos de integração por requisitos reais: número dedicado, grupos comuns, áudio, webhook, regras de mensagens proativas e riscos operacionais. Não prometa paridade de recursos entre adaptadores nem trate status de gateway como comprovação de pareamento e roteamento do número.

## 6. Conferir e entregar
- Verifique que o arquivo solicitado foi efetivamente atualizado e que a cópia bruta continua íntegra.
- Conte histórias, casos de uso ou propostas por código antes de declarar totais.
- Entregue os documentos com uma explicação curta de autoria provisória, decisões pendentes e próxima etapa.
- Explicite o que não foi executado: pareamento, configuração, criação de skills, implantação de backend ou envio de mensagens, conforme aplicável.
