from __future__ import annotations

import os
from pathlib import Path


_ENV_PATH = Path(__file__).resolve().parent.parent / '.env'


def load_local_env() -> None:
    if not _ENV_PATH.exists():
        return

    for raw_line in _ENV_PATH.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def env(key: str, default: str = '') -> str:
    load_local_env()
    return os.getenv(key, default).strip()
