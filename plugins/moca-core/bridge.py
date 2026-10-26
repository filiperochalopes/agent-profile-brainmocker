"""Ponte para a BMoca App: chama `bmoca-app tool <nome>` em subprocesso com identidade só do adaptador."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("moca-core")

PROFILE = Path(__file__).resolve().parents[2]
APP = PROFILE / "app"
BMOCA_APP_BIN = APP / ".venv" / "bin" / "bmoca-app"
PILOT_MARKER = Path(__file__).resolve().parent / "PILOTO"

INTERNAL_ERROR = {
    "ok": False,
    "error": {
        "code": "INTERNAL",
        "user_message": "Tive um problema técnico para registrar agora. Pode tentar de novo em alguns minutos?",
        "details": {},
    },
}

_SESSION_VARS = {
    "BMOCA_APP_CALLER_PLATFORM": "HERMES_SESSION_PLATFORM",
    "BMOCA_APP_CALLER_USER_ID": "HERMES_SESSION_USER_ID",
    "BMOCA_APP_CALLER_USER_ID_ALT": "HERMES_SESSION_USER_ID_ALT",
    "BMOCA_APP_CALLER_CHAT_ID": "HERMES_SESSION_CHAT_ID",
    "BMOCA_APP_CALLER_CHAT_TYPE": "HERMES_SESSION_CHAT_TYPE",
    "BMOCA_APP_CALLER_MESSAGE_ID": "HERMES_SESSION_MESSAGE_ID",
    "BMOCA_APP_CALLER_SESSION_ID": "HERMES_SESSION_ID",
}


def session_env(name: str) -> str:
    try:
        from gateway.session_context import get_session_env

        return get_session_env(name) or ""
    except Exception:  # noqa: BLE001
        return os.environ.get(name, "")


def build_env() -> dict[str, str]:
    """Ambiente MÍNIMO: nada do ambiente do Hermes além do necessário."""
    env = {"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", ""), "LANG": "C.UTF-8"}
    for bmoca_var, hermes_var in _SESSION_VARS.items():
        value = session_env(hermes_var)
        env[bmoca_var] = value
        # Keep the legacy adapter contract available during the migration.
        env[bmoca_var.replace("BMOCA_APP_", "MOCA_")] = value
    if PILOT_MARKER.exists():
        env["BMOCA_APP_DB_FILE"] = "moca_test.db"
        env["MOCA_DB_FILE"] = "moca_test.db"
    return env


def call_moca(tool_name: str, args: dict) -> dict:
    try:
        proc = subprocess.run(
            [str(BMOCA_APP_BIN), "tool", tool_name],
            input=json.dumps(args, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(APP),
            env=build_env(),
            check=False,
        )
    except Exception as exc:  # noqa: BLE001  timeout etc.; nunca registra os argumentos
        logger.warning("moca tool %s falhou: %s", tool_name, type(exc).__name__)
        return INTERNAL_ERROR
    if proc.returncode != 0:
        logger.warning("moca tool %s saiu com código %s", tool_name, proc.returncode)
        return INTERNAL_ERROR
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        logger.warning("moca tool %s devolveu saída ilegível", tool_name)
        return INTERNAL_ERROR
