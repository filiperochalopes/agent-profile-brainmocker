#!/usr/bin/env python3
"""Guarda de acesso à Evolution API para sessões do Telegram.

Uso: evo_guard.py METHOD PATH [--body JSON]
Identidade vem do ambiente da sessão (HERMES_SESSION_PLATFORM / HERMES_SESSION_USER_ID),
nunca de argumentos. Política em policies/evolution_access.json. Padrão: negar.
"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request, urllib.error

HOME = "/Users/filipelopes/.hermes/profiles/bmoca"
POLICY = os.environ.get("EVO_POLICY", f"{HOME}/policies/evolution_access.json")
AUDIT = f"{HOME}/policies/evolution_audit.jsonl"
BASE = "https://wpp.orango.io"

# Rotas permitidas para NÃO-admins (leitura/ envio de texto por instância). Tudo fora disso é negado.
ALLOWED = [
    ("GET", r"^/instance/fetchInstances$", None),
    ("POST", r"^/chat/findChats/(?P<i>[^/?]+)$", "i"),
    ("POST", r"^/chat/findMessages/(?P<i>[^/?]+)$", "i"),
    ("GET", r"^/group/participants/(?P<i>[^/?]+)(\?groupJid=[^&]+)?$", "i"),
    ("POST", r"^/message/sendText/(?P<i>[^/?]+)$", "i"),
    ("POST", r"^/chat/getBase64FromMediaMessage/(?P<i>[^/?]+)$", "i"),
]


def audit(**k):
    k["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(AUDIT, "a") as f:
        f.write(json.dumps(k, ensure_ascii=False) + "\n")


def deny(msg, **k):
    audit(decision="deny", reason=msg, **k)
    print(f"NEGADO: {msg}", file=sys.stderr)
    sys.exit(3)


def key():
    r = subprocess.run(["security", "find-generic-password", "-a", os.environ.get("USER", "filipelopes"),
                        "-s", "EVOLUTION_API_KEY", "-w"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("keychain lookup failed")
    return r.stdout.strip()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    method, path = sys.argv[1].upper(), sys.argv[2]
    body = None
    if "--body" in sys.argv:
        body = json.loads(sys.argv[sys.argv.index("--body") + 1])
    pol = json.load(open(POLICY))
    platform = os.environ.get("HERMES_SESSION_PLATFORM", "")
    uid = os.environ.get("HERMES_SESSION_USER_ID", "")
    ctx = dict(platform=platform, user_id=uid, method=method, path=path)

    allowed_instances, admin = None, False
    if platform == "telegram":
        u = pol["telegram_users"].get(uid)
        if not u:
            deny("usuário do Telegram sem permissão cadastrada", **ctx)
        admin = u.get("role") == "admin"
        allowed_instances = None if admin else u["instances"]
    elif platform in pol.get("trusted_platforms", []):
        admin = True  # cron/desktop/cli: sessões do próprio dono
    else:
        deny("plataforma/identidade desconhecida (variáveis de sessão ausentes)", **ctx)

    inst = None
    if not admin:
        for m, rx, grp in ALLOWED:
            mt = re.match(rx, path)
            if m == method and mt:
                inst = urllib.parse.unquote(mt.group("i")) if grp else None
                break
        else:
            deny("rota não permitida para este usuário", **ctx)
        if grp and inst not in allowed_instances:
            deny(f"instância '{inst}' não autorizada para este usuário", **ctx)

    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"apikey": key(), "Content-Type": "application/json"})
    op = urllib.request.build_opener(NoRedirect)
    try:
        with op.open(req, timeout=60) as r:
            status, out = r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        status, out = e.code, e.read().decode(errors="replace")[:500]

    if not admin and re.match(r"^/instance/fetchInstances", path) and isinstance(out, list):
        out = [{k: v for k, v in i.items() if k not in ("token", "apikey", "Setting", "_count")}
               for i in out if i.get("name") in allowed_instances]
    audit(decision="allow", status=status, instance=inst, **ctx)
    print(json.dumps({"status": status, "data": out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
