from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from pathlib import Path

from .path_service import ensure_storage_dirs, STORAGE_DIR

CONFIG_PATH = STORAGE_DIR / "config.json"
DEFAULT_MODEL = os.getenv("FOUNDRY_LOCAL_MODEL_NAME") or "Phi-4-mini-instruct-cuda-gpu:5"
FOUNDRY_PORT = int(os.getenv("FOUNDRY_LOCAL_PORT", "8089"))
FOUNDRY_ENDPOINT = f"http://127.0.0.1:{FOUNDRY_PORT}/v1"


def _default_config() -> dict:
    return {
        "selectedModelId": DEFAULT_MODEL,
        "autoStartService": False,
        "maxTokens": 2048,
        "updatedAt": datetime.now(UTC).isoformat(),
    }


def load_config(include_secrets: bool = False) -> dict:
    ensure_storage_dirs()
    if not CONFIG_PATH.exists():
        save_config(_default_config())
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return data


def save_config(payload: dict) -> dict:
    ensure_storage_dirs()
    current = _default_config()
    if CONFIG_PATH.exists():
        current.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))

    for key in ["selectedModelId", "autoStartService", "maxTokens"]:
        if key in payload:
            current[key] = payload[key]

    current["updatedAt"] = datetime.now(UTC).isoformat()
    CONFIG_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_config(include_secrets=False)


def get_selected_model() -> str:
    return load_config(include_secrets=True).get("selectedModelId") or DEFAULT_MODEL
