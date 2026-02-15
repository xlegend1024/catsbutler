from __future__ import annotations

import logging
import subprocess
import time
import traceback
from datetime import datetime, UTC
from typing import Any

import httpx

from .config_service import get_selected_model, FOUNDRY_PORT, FOUNDRY_ENDPOINT

logger = logging.getLogger(__name__)

# ── Base URL for Foundry Local internal REST API (NOT the /v1 OpenAI endpoint)
_FOUNDRY_BASE = f"http://127.0.0.1:{FOUNDRY_PORT}"

_state = {
    "status": "stopped",
    "mode": "unknown",
    "activeModelId": None,
    "message": None,
    "lastUpdatedAt": datetime.now(UTC).isoformat(),
}

_model_id: str | None = None


def _stamp(**updates) -> dict:
    _state.update(updates)
    _state["lastUpdatedAt"] = datetime.now(UTC).isoformat()
    logger.debug("Runtime state → %s", _state)
    return dict(_state)


def status() -> dict:
    return dict(_state)


def detect_mode(model_id: str) -> str:
    lowered = model_id.lower()
    if "npu" in lowered or "qnn" in lowered or "openvino" in lowered:
        return "NPU"
    if "gpu" in lowered or "cuda" in lowered or "directml" in lowered:
        return "GPU"
    return "CPU"


# ── Direct HTTP helpers (bypass FoundryLocalManager SDK) ─────────

def _is_service_reachable() -> bool:
    """Check if the Foundry Local service is reachable via HTTP."""
    try:
        r = httpx.get(f"{_FOUNDRY_BASE}/openai/status", timeout=5.0)
        ok = r.status_code == 200
        logger.debug("Service reachable check → %s (status=%d)", ok, r.status_code)
        return ok
    except Exception as exc:
        logger.debug("Service reachable check → False (%s)", exc)
        return False


def _start_service() -> bool:
    """Start the Foundry Local service using the CLI and wait until it's reachable."""
    logger.warning("Foundry service not reachable — starting it via CLI ...")
    try:
        subprocess.run(
            ["foundry", "service", "start"],
            timeout=45,
            capture_output=True,
        )
    except Exception as exc:
        logger.error("foundry service start failed: %s", exc)
        return False

    for attempt in range(30):
        if _is_service_reachable():
            logger.info("Foundry service became reachable after %d attempts", attempt + 1)
            return True
        time.sleep(1)

    logger.error("Foundry service did not become reachable within 30 s")
    return False


def _ensure_service() -> None:
    """Make sure the Foundry service is reachable, starting it if necessary."""
    if not _is_service_reachable():
        if not _start_service():
            raise RuntimeError(
                f"Foundry Local service is not running on port {FOUNDRY_PORT}. "
                "Start it manually with: foundry service start"
            )


def _load_model_http(model_id: str, ttl: int = 600) -> None:
    """Load a model via the Foundry REST API (no SDK)."""
    url = f"{_FOUNDRY_BASE}/openai/load/{model_id}"
    logger.info("Loading model via HTTP  url=%s  ttl=%d", url, ttl)
    r = httpx.get(url, params={"ttl": ttl}, timeout=120.0)
    if r.status_code != 200:
        raise RuntimeError(f"Model load failed ({r.status_code}): {r.text}")
    logger.info("Model loaded successfully via HTTP")


def list_cached_models_http() -> list[str]:
    """Return list of cached model IDs via the Foundry REST API."""
    try:
        r = httpx.get(f"{_FOUNDRY_BASE}/openai/models", timeout=10.0)
        if r.status_code == 200:
            return r.json()
    except Exception as exc:
        logger.warning("list_cached_models_http failed: %s", exc)
    return []


# ── Public API (used by chat_service & model_service) ────────────

def ensure_manager(model_alias: str | None = None):
    """Ensure the Foundry service is running and the requested model is loaded.

    Returns ``(None, model_id)`` — the first element is kept for API
    compatibility but is no longer a FoundryLocalManager instance.
    """
    global _model_id
    alias = model_alias or get_selected_model()
    logger.debug("ensure_manager called  alias=%r  cached_model_id=%r", alias, _model_id)

    # Fast path: model already loaded & service reachable
    if _model_id is not None and _is_service_reachable():
        logger.debug("Returning cached model_id=%s", _model_id)
        return None, _model_id

    # Reset if stale
    _model_id = None
    _stamp(status="starting", message="Starting Foundry Local runtime...")

    try:
        _ensure_service()
        _load_model_http(alias)
        # Verify service survived model loading
        import time as _time
        _time.sleep(1)
        if not _is_service_reachable():
            logger.error("Service DIED right after model loading!")
            # Try to restart and reload
            if _start_service():
                _load_model_http(alias)
            else:
                raise RuntimeError("Service crashed during model loading and could not restart")
        _model_id = alias
        logger.info("Model ready  id=%s", _model_id)
        _stamp(status="running", mode=detect_mode(_model_id),
               activeModelId=_model_id, message="Runtime ready")
    except Exception as exc:
        logger.error("ensure_manager FAILED:\n%s", traceback.format_exc())
        _stamp(status="error", mode="unknown", message=str(exc))
        raise

    return None, _model_id


def start(model_alias: str | None = None) -> dict:
    ensure_manager(model_alias)
    return status()


def stop() -> dict:
    global _model_id
    _stamp(status="stopping", message="Stopping runtime")
    _model_id = None
    _stamp(status="stopped", mode="unknown", activeModelId=None, message="Stopped")
    return status()


def _reset_manager() -> None:
    """Reset cached model so the next ensure_manager() starts fresh."""
    global _model_id
    logger.warning("_reset_manager: clearing cached model_id")
    _model_id = None
