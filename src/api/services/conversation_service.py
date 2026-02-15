from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

from .path_service import CONVERSATIONS_DIR, ensure_storage_dirs, next_conversation_path


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def list_conversations() -> list[dict]:
    ensure_storage_dirs()
    items: list[dict] = []
    for file in sorted(CONVERSATIONS_DIR.glob("*.json"), reverse=True):
        try:
            payload = _read(file)
            items.append(
                {
                    "id": payload.get("id", file.stem),
                    "title": payload.get("title", "Untitled conversation"),
                    "updatedAt": payload.get("updatedAt") or payload.get("createdAt"),
                }
            )
        except Exception:
            continue
    items.sort(key=lambda x: x.get("updatedAt") or "", reverse=True)
    return items


def get_conversation(conversation_id: str) -> dict:
    ensure_storage_dirs()
    target = CONVERSATIONS_DIR / f"{conversation_id}.json"
    if not target.exists():
        raise FileNotFoundError(conversation_id)
    return _read(target)


def save_conversation(messages: list[dict], conversation_id: str | None = None, title: str | None = None) -> dict:
    ensure_storage_dirs()
    now = datetime.now(UTC).isoformat()

    if conversation_id:
        file_path = CONVERSATIONS_DIR / f"{conversation_id}.json"
        if file_path.exists():
            existing = _read(file_path)
            created_at = existing.get("createdAt", now)
        else:
            created_at = now
    else:
        file_path = next_conversation_path()
        conversation_id = file_path.stem
        created_at = now

    computed_title = title or _derive_title(messages)
    payload = {
        "id": conversation_id,
        "title": computed_title,
        "createdAt": created_at,
        "updatedAt": now,
        "messages": messages,
    }
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _derive_title(messages: list[dict]) -> str:
    for item in messages:
        if item.get("role") == "user" and item.get("content"):
            text = item["content"].strip().replace("\n", " ")
            return text[:120] or "Untitled conversation"
    return "Untitled conversation"
