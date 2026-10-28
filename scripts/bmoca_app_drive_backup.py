#!/usr/bin/env python3
"""Upload a verified BMoca App SQL dump to the configured private Drive folder."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PROFILE = Path(__file__).resolve().parents[1]
APP = PROFILE / "app"
SETTINGS = APP / "config" / "settings.toml"
TOKEN = PROFILE / "google_token.json"
STAGING = PROFILE / "data" / "backups" / "drive-staging"


def folder_id() -> str:
    configured = os.environ.get("BMOCA_APP_DRIVE_FOLDER_ID")
    if configured:
        return configured
    raw = tomllib.loads(SETTINGS.read_text(encoding="utf-8"))
    try:
        return str(raw["backup"]["drive"]["folder_id"])
    except KeyError as exc:
        raise RuntimeError("Configure backup.drive.folder_id or BMOCA_APP_DRIVE_FOLDER_ID") from exc


def credentials() -> Credentials:
    creds = Credentials.from_authorized_user_file(TOKEN)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
        os.chmod(TOKEN, 0o600)
    if not creds.valid:
        raise RuntimeError("Google Drive credentials are not valid")
    return creds


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5(path: Path) -> str:
    digest = hashlib.md5()  # nosec B324: Drive returns MD5 for upload integrity verification.
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_dump() -> tuple[Path, Path]:
    STAGING.mkdir(parents=True, exist_ok=True)
    os.chmod(STAGING, 0o700)
    command = [str(APP / ".venv" / "bin" / "bmoca-app"), "db", "dump", "--quiet", "--output-dir", str(STAGING)]
    subprocess.run(command, check=True, cwd=APP, capture_output=True, text=True)
    dumps = sorted(STAGING.glob("bmoca-app-*.sql.gz"), key=lambda item: item.stat().st_mtime)
    if not dumps:
        raise RuntimeError("BMoca App did not create a SQL dump")
    dump = dumps[-1]
    manifest = dump.with_suffix(dump.suffix + ".sha256")
    if not manifest.exists():
        raise RuntimeError("BMoca App did not create a checksum manifest")
    expected = manifest.read_text(encoding="utf-8").split()[0]
    if sha256(dump) != expected:
        raise RuntimeError("Local SQL dump checksum does not match its manifest")
    return dump, manifest


def upload(service, parent: str, path: Path) -> dict:
    media = MediaFileUpload(path, resumable=True)
    return service.files().create(
        body={"name": path.name, "parents": [parent]},
        media_body=media,
        fields="id,name,size,md5Checksum,parents",
        supportsAllDrives=True,
    ).execute()


def main() -> int:
    dump, manifest = run_dump()
    service = build("drive", "v3", credentials=credentials(), cache_discovery=False)
    parent = folder_id()
    metadata = service.files().get(
        fileId=parent, fields="id,mimeType,capabilities(canAddChildren)", supportsAllDrives=True
    ).execute()
    if metadata.get("mimeType") != "application/vnd.google-apps.folder" or not metadata.get(
        "capabilities", {}
    ).get("canAddChildren"):
        raise RuntimeError("Configured Google Drive target is not writable as a folder")

    uploaded_dump = upload(service, parent, dump)
    if uploaded_dump.get("size") != str(dump.stat().st_size) or uploaded_dump.get("md5Checksum") != md5(dump):
        raise RuntimeError("Drive did not confirm the uploaded SQL dump bytes")
    uploaded_manifest = upload(service, parent, manifest)
    if uploaded_manifest.get("size") != str(manifest.stat().st_size):
        raise RuntimeError("Drive did not confirm the uploaded checksum manifest")

    dump.unlink()
    manifest.unlink()
    print(f"Drive backup confirmed: {uploaded_dump['id']} {uploaded_dump['name']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"BMoca App Drive backup failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
