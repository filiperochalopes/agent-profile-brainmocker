#!/usr/bin/env python3
"""Retenção dos logs do bmoca: 90 dias em logs/ (agent.log e segmentos rotacionados); mais antigos vão
compactados (gzip) para logs/archive/, retenção indefinida. Só mexe em segmentos já rotacionados
(agent.log.N, errors.log.N, gateway.log.N), que são imutáveis; nunca no arquivo ativo."""
from __future__ import annotations

import gzip
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

LOGS = Path("/Users/filipelopes/.hermes/profiles/bmoca/logs")
ARCHIVE = LOGS / "archive"
KEEP_DAYS = 90
SEGMENT = re.compile(r"^(agent|errors|gateway)\.log\.\d+$")


def main(dry_run: bool = False) -> int:
    cutoff = time.time() - KEEP_DAYS * 86400
    moved = 0
    for p in sorted(LOGS.iterdir()):
        if not (p.is_file() and SEGMENT.match(p.name)) or p.stat().st_mtime >= cutoff:
            continue
        stamp = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y%m%d-%H%M%S")
        dest = ARCHIVE / f"{p.name.split('.log')[0]}-{stamp}.log.gz"
        print(("DRY " if dry_run else "") + f"{p.name} -> {dest.name}")
        if dry_run:
            continue
        ARCHIVE.mkdir(mode=0o700, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        with p.open("rb") as src, gzip.open(tmp, "wb") as out:
            shutil.copyfileobj(src, out)
        tmp.chmod(0o600)
        tmp.rename(dest)
        with gzip.open(dest, "rb") as chk:  # confere leitura antes de apagar o original
            while chk.read(1 << 20):
                pass
        p.unlink()
        moved += 1
    print(f"arquivados: {moved}")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
