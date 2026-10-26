#!/usr/bin/env python3
"""Arquiva no Drive as imagens e documentos do dia anterior do grupo Escola Sem Nome.

Uso: arquivar_escola_diario.py [YYYY-MM-DD]   (padrão: dia anterior, GMT-3)

Saída (stdout):
- vazia se não houver imagens nem documentos (o cron não envia nada);
- texto de notificação para o Telegram somente se houver imagens.
Logs e erros vão para stderr.
"""
import base64, datetime as dt, json, os, re, subprocess, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evo_client as evo  # noqa: E402

TZ = dt.timezone(dt.timedelta(hours=-3))
INST = "Filipe Lopes - Pessoal"
JID = "120363429552702512@g.us"
DRIVE_ROOT = "131RkBdxE_b7Z6TIKvfkFiqEcq4jZPq0_"
GAPI = "/Users/filipelopes/.hermes/profiles/bmoca/skills/productivity/google-workspace/scripts/google_api.py"
WORK = "/Users/filipelopes/.hermes/profiles/bmoca/cache/escola_arquivo"
ENV = dict(os.environ, HERMES_HOME="/Users/filipelopes/.hermes")
FOLDER_MIME = "application/vnd.google-apps.folder"


def log(msg):
    print(msg, file=sys.stderr)


def gapi(*args):
    r = subprocess.run(["python3", "-W", "ignore", GAPI, *args],
                       capture_output=True, text=True, env=ENV)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_error": (r.stdout + r.stderr)[-300:]}


def drive_list(query):
    d = gapi("drive", "search", query, "--raw-query", "--max", "500")
    return d if isinstance(d, list) else None


def fetch_media(start, end):
    inst = urllib.parse.quote(INST)
    recs, page = {}, 1
    while page <= 60:
        s, d = evo.call("POST", "/chat/findMessages/" + inst,
                        {"where": {"key": {"remoteJid": JID}}, "page": page, "offset": 100})
        if s not in (200, 201) or not isinstance(d, dict):
            raise SystemExit(f"findMessages falhou: status {s}")
        rr = d["messages"]["records"]
        if not rr:
            break
        for r in rr:
            recs.setdefault(r["key"]["id"], r)
        if min(r["messageTimestamp"] for r in rr) < start:
            break
        page += 1
    out = []
    for r in recs.values():
        ts = r["messageTimestamp"]
        if not (start <= ts < end):
            continue
        m = r.get("message") or {}
        if "imageMessage" in m:
            out.append((ts, r, "imagem", m["imageMessage"]))
        elif "documentMessage" in m:
            out.append((ts, r, "documento", m["documentMessage"]))
        elif "documentWithCaptionMessage" in m:
            inner = m["documentWithCaptionMessage"].get("message", {}).get("documentMessage")
            if inner:
                out.append((ts, r, "documento", inner))
    out.sort(key=lambda x: x[0])
    return out


def ext_for(kind, info):
    mt = info.get("mimetype") or ""
    if kind == "imagem":
        return "jpg" if "jpeg" in mt else (mt.split("/")[-1] or "jpg")
    fn = info.get("fileName") or ""
    if "." in fn:
        return fn.rsplit(".", 1)[1].lower()
    return mt.split("/")[-1] or "bin"


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", s).strip()[:120]


def main():
    if len(sys.argv) > 1:
        day = dt.date.fromisoformat(sys.argv[1])
    else:
        day = (dt.datetime.now(TZ) - dt.timedelta(days=1)).date()
    name = day.isoformat()
    start_dt = dt.datetime.combine(day, dt.time(0), tzinfo=TZ)
    start, end = start_dt.timestamp(), (start_dt + dt.timedelta(days=1)).timestamp()

    items = fetch_media(start, end)
    log(f"[{name}] mídias encontradas: {len(items)}")
    if not items:
        return  # silencioso

    n_img = sum(1 for i in items if i[2] == "imagem")
    n_doc = len(items) - n_img

    # pasta do dia (reutiliza se já existir)
    found = drive_list(f"name = '{name}' and mimeType = '{FOLDER_MIME}' "
                       f"and '{DRIVE_ROOT}' in parents and trashed = false")
    if found is None:
        raise SystemExit("falha ao consultar pasta no Drive")
    if found:
        folder_id = found[0]["id"]
    else:
        d = gapi("drive", "create-folder", name, "--parent", DRIVE_ROOT)
        folder_id = d.get("id")
        if not folder_id:
            raise SystemExit(f"falha ao criar pasta: {d}")
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

    existing = drive_list(f"'{folder_id}' in parents and trashed = false")
    if existing is None:
        raise SystemExit("falha ao listar arquivos da pasta")
    existing_names = " ".join(f["name"] for f in existing)

    inst = urllib.parse.quote(INST)
    os.makedirs(os.path.join(WORK, name), exist_ok=True)
    sent, skipped, fails = 0, 0, []
    for n, (ts, r, kind, info) in enumerate(items, 1):
        mid8 = r["key"]["id"][:8]
        if mid8 in existing_names:
            skipped += 1
            continue
        s, d = evo.call("POST", "/chat/getBase64FromMediaMessage/" + inst,
                        {"message": {"key": r["key"]}, "convertToMp4": False})
        if s not in (200, 201) or not isinstance(d, dict) or "base64" not in d:
            fails.append(mid8)
            log(f"download falhou {mid8}: {s}")
            continue
        hhmmss = dt.datetime.fromtimestamp(ts, TZ).strftime("%H%M%S")
        ext = ext_for(kind, info)
        if kind == "documento" and info.get("fileName"):
            stem = safe_name(info["fileName"].rsplit(".", 1)[0]) or "documento"
            fname = f"{n:02d}_{hhmmss}_{mid8}_{stem}.{ext}"
        else:
            fname = f"{n:02d}_{hhmmss}_{mid8}.{ext}"
        path = os.path.join(WORK, name, fname)
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(d["base64"]))
        up = gapi("drive", "upload", path, "--parent", folder_id)
        if up.get("status") == "uploaded":
            sent += 1
        else:
            fails.append(mid8)
            log(f"upload falhou {fname}: {up}")

    log(f"[{name}] enviados={sent} já_existiam={skipped} falhas={len(fails)}")
    if n_img == 0:
        return  # só documentos: armazenados, sem notificação

    data_br = day.strftime("%d/%m/%Y")
    msg = (f"Documentos do grupo Escola sem nome ({data_br}) foram devidamente armazenados no Drive.\n"
           f"Imagens: {n_img} | Documentos: {n_doc} | Novos enviados: {sent}\n"
           f"Pasta: {folder_url}")
    if fails:
        msg += f"\nAtenção: {len(fails)} arquivo(s) não foram enviados; verificar manualmente."
    print(msg)


if __name__ == "__main__":
    main()
