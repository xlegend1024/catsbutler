from __future__ import annotations

from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BASE_DIR / "storage"
CONVERSATIONS_DIR = STORAGE_DIR / "conversations"


def ensure_storage_dirs() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def timestamp_stem(now: datetime | None = None) -> str:
    reference = now or datetime.now()
    return reference.strftime("%Y-%m-%d_%H-%M")


def next_conversation_path(now: datetime | None = None) -> Path:
    ensure_storage_dirs()
    stem = timestamp_stem(now)
    candidate = CONVERSATIONS_DIR / f"{stem}.json"
    if not candidate.exists():
        return candidate

    suffix = 1
    while True:
        candidate = CONVERSATIONS_DIR / f"{stem}-{suffix:02d}.json"
        if not candidate.exists():
            return candidate
        suffix += 1
