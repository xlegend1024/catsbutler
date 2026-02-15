from __future__ import annotations

import logging
from typing import Any

from .config_service import get_selected_model, save_config

logger = logging.getLogger(__name__)

_cached_models: list[dict] | None = None


def _detect_mode(model: Any) -> str:
    """Derive recommended mode from model metadata."""
    device = getattr(model, "device_type", "") or ""
    ep = getattr(model, "execution_provider", "") or ""
    combined = f"{device} {ep}".lower()
    if "npu" in combined or "qnn" in combined or "openvino" in combined:
        return "NPU"
    if "gpu" in combined or "cuda" in combined or "directml" in combined:
        return "GPU"
    return "CPU"


def _fetch_foundry_models() -> list[dict]:
    """Query Foundry Local REST API for cached models.

    Uses direct HTTP calls to avoid FoundryLocalManager SDK issues.
    """
    global _cached_models
    try:
        from .runtime_service import list_cached_models_http

        model_ids = list_cached_models_http()
        models: list[dict] = []
        seen: set[str] = set()
        for model_id in model_ids:
            if model_id in seen:
                continue
            seen.add(model_id)
            models.append(
                {
                    "id": model_id,
                    "displayName": model_id,
                    "availability": "available",
                    "recommendedMode": _detect_mode_str(model_id),
                }
            )
        _cached_models = models
        return models
    except Exception as exc:
        logger.warning("Failed to query Foundry Local models: %s", exc)
        if _cached_models is not None:
            return _cached_models
        return []


def _detect_mode_str(model_id: str) -> str:
    """Derive recommended mode from model ID string."""
    lowered = model_id.lower()
    if "npu" in lowered or "qnn" in lowered or "openvino" in lowered:
        return "NPU"
    if "gpu" in lowered or "cuda" in lowered or "directml" in lowered:
        return "GPU"
    return "CPU"


def list_models() -> list[dict]:
    return _fetch_foundry_models()


def set_selected_model(model_id: str) -> dict:
    return save_config({"selectedModelId": model_id})
