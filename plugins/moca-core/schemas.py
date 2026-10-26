"""Schemas das ferramentas moca_* (o modelo NUNCA vê/define recent_messages nem identidade)."""

from __future__ import annotations


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or [], "additionalProperties": False}


_S = {"type": "string"}

SCHEMAS = {
    "contexto": {
        "description": "Devolve quem está falando (identificado pelo sistema), papéis, crianças vinculadas e se o número é compartilhado.",
        "parameters": _obj({}),
    },
    "quem_sou": {
        "description": "Igual a moca_contexto: identidade, papéis e crianças vinculadas do remetente.",
        "parameters": _obj({}),
    },
    "registrar_feedback": {
        "description": "Registra um relato privado da família ou da equipe. original_text deve ser copiado EXATAMENTE da mensagem; summary é a sua síntese curta.",
        "parameters": _obj(
            {
                "topic": {"type": "string", "enum": ["crianca", "encontro", "aplicacao"]},
                "student_ref": {**_S, "description": "ref da criança (#xxxxxxxx), só quando topic=crianca"},
                "speaker_ref": {**_S, "description": "ref de quem escreve, só quando o número é compartilhado"},
                "original_text": _S,
                "summary": {**_S, "maxLength": 600},
                "event_date_text": {**_S, "description": "como a pessoa disse a data (hoje, ontem, DD/MM); omita se não disse"},
                "domain_code": _S,
                "activity_text": _S,
            },
            ["topic", "original_text", "summary"],
        ),
    },
    "corrigir_feedback": {
        "description": "Corrige um relato anterior do próprio autor (cria nova versão; o original é preservado).",
        "parameters": _obj(
            {"document_ref": _S, "original_text": _S, "summary": {**_S, "maxLength": 600}, "reason": _S},
            ["document_ref", "original_text", "summary", "reason"],
        ),
    },
    "buscar_orientacoes": {
        "description": "Busca orientações aprovadas e publicadas pela equipe, compatíveis com o remetente.",
        "parameters": _obj({"query": _S}, ["query"]),
    },
    "abrir_caso": {
        "description": "Encaminha uma pergunta à equipe (use só com o consentimento do remetente e quando não houver orientação aplicável).",
        "parameters": _obj(
            {"question_text": _S, "summary": {**_S, "maxLength": 600}, "domain_code": _S, "student_ref": _S, "speaker_ref": _S},
            ["question_text", "summary"],
        ),
    },
    "meus_casos": {
        "description": "Lista os casos atribuídos ao profissional que está falando.",
        "parameters": _obj({"status": {"type": "string", "enum": ["open", "assigned", "answered", "all"]}}),
    },
    "responder_caso": {
        "description": "Responde a um caso atribuído ao profissional; a resposta é entregue ao autor da pergunta.",
        "parameters": _obj({"case_ref": _S, "answer_text": _S}, ["case_ref", "answer_text"]),
    },
}

NEEDS_RECENT_MESSAGES = {"registrar_feedback", "corrigir_feedback", "abrir_caso"}
