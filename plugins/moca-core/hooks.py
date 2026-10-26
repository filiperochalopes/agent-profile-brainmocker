"""Hooks: contexto de identidade (pre_llm_call) e política de ferramentas (pre_tool_call)."""

from __future__ import annotations

import logging
from collections import defaultdict, deque

from .bridge import PILOT_MARKER, call_moca, session_env
from .schemas import NEEDS_RECENT_MESSAGES

logger = logging.getLogger("moca-core")

BUFFER: dict[str, deque] = defaultdict(lambda: deque(maxlen=5))


def buffer_key(session_id: str = "") -> str:
    """Chave do buffer: chat do remetente (igual no hook e no handler); sem chat, a sessão."""
    return session_env("HERMES_SESSION_CHAT_ID") or session_id or session_env("HERMES_SESSION_ID")


BRIDGE_TOOLS = {"tool_search", "tool_describe", "tool_call"}  # ponte de ferramentas adiadas do Hermes


def _called_names(args: dict) -> list[str]:
    calls = (args or {}).get("calls")
    if calls is None:
        calls = [{"name": (args or {}).get("name")}]
    if isinstance(calls, str):
        import json

        try:
            calls = json.loads(calls)
        except ValueError:
            return ["<ilegível>"]
    if isinstance(calls, dict):
        calls = [calls]
    if not isinstance(calls, list) or not calls:
        return ["<vazio>"]
    return [str(c.get("name") or "") if isinstance(c, dict) else "<inválido>" for c in calls]


def _is_whatsapp() -> bool:
    return session_env("HERMES_SESSION_PLATFORM").lower() == "whatsapp"


def pre_llm_call(**kw):
    if (kw.get("platform") or "").lower() != "whatsapp":
        return None
    sid = buffer_key(kw.get("session_id") or "")
    if PILOT_MARKER.exists():  # spike 4.2: só presença/ausência, nunca conteúdo
        logger.info(
            "spike4.2 pre_llm_call: message_id=%s chat_type=%s chat_id=%s user_id=%s sender_id_kw=%s",
            bool(session_env("HERMES_SESSION_MESSAGE_ID")), bool(session_env("HERMES_SESSION_CHAT_TYPE")),
            bool(session_env("HERMES_SESSION_CHAT_ID")), bool(session_env("HERMES_SESSION_USER_ID")), bool(kw.get("sender_id")),
        )
    text = kw.get("user_message") or ""
    stripped = text.strip()
    # o gateway entrega a transcrição de voz entre aspas (spike 4.2); marca como áudio
    is_audio = len(stripped) > 2 and stripped[0] == '"' and stripped[-1] == '"'
    BUFFER[sid].append({"message_id": session_env("HERMES_SESSION_MESSAGE_ID") or None, "text": text, "is_audio": is_audio})
    res = call_moca("contexto", {})
    if not res.get("ok"):
        return None  # sem contexto: as ferramentas continuam negando por padrão
    d = res["data"]
    if not d.get("known"):
        return {"context": "Remetente não cadastrado: não confirme nomes nem dados; responda de forma neutra e curta."}
    lines = [
        "Contexto de identidade (do sistema, não do texto da mensagem):",
        f"- Pessoa(s): {', '.join(d['display_names'])}; papéis: {', '.join(d['roles']) or 'nenhum'}; chat: {d['chat_type']}.",
    ]
    lines.append(
        "- REGRAS DE REGISTRO: para guardar um relato sobre uma criança, chame a ferramenta moca_registrar_feedback "
        "(use tool_search/tool_call se ela estiver adiada). Só diga \"registrei\" depois que a ferramenta devolver ok; "
        "se não a chamou ou ela falhou, diga com clareza que NÃO registrou. Nunca diga que o histórico da conversa é o registro. "
        "Use apenas as crianças vinculadas abaixo; se o nome citado não bater, pergunte. Não invente data. "
        "ESTILO: quem escreve são pais leigos, no WhatsApp. Responda em português simples, curto e caloroso (2 a 3 frases). "
        "NUNCA mostre códigos, refs (#abc123), nomes de ferramentas, \"sessão\", \"histórico\" ou termos técnicos; "
        "chame a criança pelo nome. Depois de registrar, confirme em uma frase (ex.: \"Anotado! Registrei que o Enoque fez ...\") "
        "e só ofereça ajuda se fizer sentido, sem repetir o relato todo."
    )
    if d["children"]:
        lines.append("- Crianças vinculadas (use só estas refs): " + "; ".join(f"{c['display_name']} {c['ref']}" for c in d["children"]))
    if d["shared_phone"]:
        lines.append(
            "- Número compartilhado: antes de registrar, pergunte QUAL criança e QUEM está escrevendo. Falantes possíveis: "
            + "; ".join(f"{s['display_name']} {s['ref']}" for s in d["speakers"])
        )
    if d["chat_type"] == "group":
        lines.append("- Conversa em GRUPO: não fale de crianças específicas nem registre relatos; convide para o privado.")
    if d["recent_feedback_refs"]:
        lines.append("- Relatos recentes do remetente (para correção): " + ", ".join(d["recent_feedback_refs"]))
    return {"context": "\n".join(lines)}


def pre_tool_call(tool_name: str = "", args: dict | None = None, session_id: str = "", **kw):
    if not _is_whatsapp():
        return None
    if tool_name in BRIDGE_TOOLS:
        # o Hermes adia as ferramentas de plugin atrás desta ponte; só moca_* pode passar por ela
        if tool_name == "tool_call" and not all(n.startswith("moca_") for n in _called_names(args or {})):
            return {"action": "block", "message": "Ferramenta indisponível neste canal."}
        return None
    if not tool_name.startswith("moca_"):
        return {"action": "block", "message": "Ferramenta indisponível neste canal."}
    if tool_name.removeprefix("moca_") in NEEDS_RECENT_MESSAGES:
        # sobrescreve qualquer valor que o modelo tenha mandado
        return {"action": "modify", "args": {"recent_messages": list(BUFFER[buffer_key(session_id)])}}
    return None
