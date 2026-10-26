"""Cliente mínimo da Evolution API (wpp.orango.io) para jobs locais do Filipe.

A chave é lida do Keychain apenas dentro do processo local, nunca impressa.
"""
import json, os, subprocess, urllib.request, urllib.error

BASE = "https://wpp.orango.io"


def _key():
    r = subprocess.run(
        ["security", "find-generic-password", "-a", os.environ.get("USER", "filipelopes"),
         "-s", "EVOLUTION_API_KEY", "-w"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("keychain lookup failed")
    return r.stdout.strip()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"apikey": _key(), "Content-Type": "application/json"})
    try:
        with _opener.open(req, timeout=120) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:500]
