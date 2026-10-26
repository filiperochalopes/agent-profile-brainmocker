"""Plugin moca-core: ferramentas moca_* + hooks de identidade e política (plano, 9.3)."""

from __future__ import annotations

import json
from pathlib import Path

import logging

from .bridge import PILOT_MARKER, call_moca, session_env
from .hooks import BUFFER, buffer_key, pre_llm_call, pre_tool_call
from .schemas import NEEDS_RECENT_MESSAGES, SCHEMAS

RULES_FILE = Path(__file__).resolve().parent / "prompts" / "whatsapp_rules.md"


def _make_handler(tool: str):
    def handler(args: dict, **kwargs) -> str:
        args = dict(args or {})
        if PILOT_MARKER.exists():  # spike 4.2 (handler): só presença
            logging.getLogger("moca-core").info(
                "spike4.2 handler %s: message_id=%s chat_type=%s", tool, bool(session_env("HERMES_SESSION_MESSAGE_ID")),
                bool(session_env("HERMES_SESSION_CHAT_TYPE")),
            )
        if tool in NEEDS_RECENT_MESSAGES:
            # defesa em profundidade: o buffer do plugin sempre vence o que o modelo mandou
            sid = buffer_key(kwargs.get("session_id") or "")
            args["recent_messages"] = list(BUFFER[sid])
        return json.dumps(call_moca(tool, args), ensure_ascii=False)

    return handler


def _whatsapp_rules(session_info) -> str:
    if (session_info or {}).get("platform") != "whatsapp":
        return ""
    return RULES_FILE.read_text(encoding="utf-8")


def register(ctx) -> None:
    for tool, spec in SCHEMAS.items():
        ctx.register_tool(
            name=f"moca_{tool}",
            toolset="moca",
            schema={"name": f"moca_{tool}", **spec},
            handler=_make_handler(tool),
        )
    ctx.register_hook("pre_llm_call", pre_llm_call)
    ctx.register_hook("pre_tool_call", pre_tool_call)
    ctx.register_system_prompt_section("moca-core.whatsapp-rules", _whatsapp_rules, position="after_memory", max_chars=4000)
