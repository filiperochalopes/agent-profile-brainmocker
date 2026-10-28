# Grupos, KB pública e migração de jobs

## Plano vigente, ainda não implantado

Consultar `$PROFILE/app/docs/PLANO_EDITE_GRUPOS_KB_JOBS.md` antes de implementar interação em grupo ou migrar jobs. Decisão vigente: MVP acionado por menção nativa à Edite somente na Escola Sem Nome, inclusive em resposta citada à pergunta de terceiro. Triagem proativa sem menção está adiada. Apresentação Edite e retirada do prefixo continuam previstas; não tratar como implantação concluída. Consulta da agenda e migração de jobs são integrações separadas. A agenda Google Projeto Educacional já foi criada em outra sessão: revalidar ID, fuso e eventos pela API, não presumir que está preenchida ou integrada. O plano contém a identificação e a verificação. Não remover prefixo isoladamente enquanto houver validações legadas na app.

## Regras de implementação aprendidas

- Distinguir permissão de responder, de coletar para jobs e de enviar. Allowlist de grupo na entrada não restringe destinos de saída; grupos permitidos também podem admitir participantes fora da allowlist de DMs.
- Conferir audiência do destinatário além da permissão do remetente. A busca legada de orientações filtra por papéis/grupos do remetente e pode devolver orientação da equipe a quem pergunta no grupo de famílias; corrigir antes de liberar KB no grupo.
- Usar fatos publicados, vigência, cancelamento e fonte verificável para agenda/local. `published_at` não determina validade; documentos `reference` são internos e não podem simplesmente virar públicos. Ata ou resumo de conversa privada não é KB pública.
- Tratar a ponte Baileys instalada como transporte, não arquivo: fila/cache em RAM; GET `/messages` drena fila e não deve ser usado como consulta paralela. Implementar inbox privado com replay/ACK e cobertura temporal antes de abandonar Evolution na leitura.
- Preservar timestamp original do payload, separado de recebimento. O adapter legado não o propaga para MessageEvent; horário de construção não serve para janelas de ata.
- Triar antes do batching e das vias busy/steer para cobrir cada mensagem. `pre_gateway_dispatch` usa `skip`; `suppress`/`silent_ingest` não são ações válidas neste checkout. `post_gateway_admission` com `handled` evita agente, mas é fail-open e não deve ser a única proteção.
- Testar `reply_expected=False` no fluxo opcional: `[SILENT]` sozinho não garante silêncio de um turno humano. Não acrescentar prefixo ao marcador. Preferir decidir ausência de resposta antes do modelo.
- Migrar identidade junto com templates, validações da outbox, config, skills, prompts, autoria e testes. Identificar bot por metadados e IDs de saída; não usar prefixo ou fromMe de conta pessoal como única prova de autoria. Preservar legado.
- Inspecionar scripts dos jobs além dos prompts: o arquivo diário do Drive depende de Evolution em import e download. Trocar canal de envio não migra a coleta.
- Migrar jobs existentes sem duplicação: preservar IDs/agendas/modelos e destinos aprovados, manter fonte anterior até provar cobertura, reconciliar envio ambíguo antes de retry. Message ID indica aceitação, não leitura por participantes.

## Verificação do plano

Há probes offline de silêncio e verificação read-only de `/health` e hash da ponte no relatório/plano. Nenhum envio real foi realizado. Revalidar o checkout antes de implementar, pois futuras versões do Hermes podem mudar contratos.
