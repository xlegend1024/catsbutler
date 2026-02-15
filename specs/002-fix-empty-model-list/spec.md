# Bug Specification: Empty Model List Causes Startup Failure

**Feature Branch**: `002-fix-empty-model-list`  
**Created**: 2026-02-15  
**Status**: Draft  
**Parent**: `001-foundry-chat-stock`  
**Input**: Bug report: "When there is no model in Foundry Local, it fails to load model in the model list"

## Problem Statement

When a user has no models cached in Microsoft Foundry Local (fresh install, or models cleared), the application fails to display the model list. This blocks the entire UI initialization because `Promise.all` in the frontend's `refreshAll()` treats any single endpoint failure as a total failure, leaving all UI state uninitialized.

## Root Cause Analysis

### Backend (Python API)

1. **`list_cached_models_http()`** in `runtime_service.py` returns `[]` when the Foundry service is unreachable or has no cached models — this is silent, not an error.
2. **`_fetch_foundry_models()`** in `model_service.py` only has a fallback in the `except` branch. When `list_cached_models_http()` returns an empty list (no exception), the function returns `[]` with no guidance.
3. **Startup lifespan** calls `model_service.list_models()` which may fail if Foundry service is not running, but the error is silently caught. No retry or user notification.

### Frontend (React UI)

4. **`refreshAll()`** in `App.tsx` uses `Promise.all()` — if *any* endpoint (e.g., `/service/status`, `/models`) errors with a network/500 error, the entire initialization fails silently via `.catch(() => {})`.
5. **`ModelSelector`** renders an empty `<Dropdown>` with no guidance when `models` array is empty — confusing for users.

## User Scenarios & Testing

### Scenario 1 — No models cached, Foundry service running

**Given** the Foundry Local service is running but no models are downloaded,  
**When** the user opens the application,  
**Then** the model dropdown shows "No models available — download a model to get started" with guidance.

### Scenario 2 — No models cached, Foundry service NOT running

**Given** the Foundry Local service is not running and no models are downloaded,  
**When** the user opens the application,  
**Then** the service status shows "offline", the model dropdown shows an empty-state message, and `refreshAll()` does not crash the UI.

### Scenario 3 — Models become available after initial empty load

**Given** the model list was initially empty,  
**When** the user downloads a model and clicks refresh or restarts the app,  
**Then** the model list populates with the newly available models.

## Requirements

### Functional Requirements

- **BF-001**: `GET /models` endpoint MUST return a valid `ModelListResponse` with `items: []` (not an error) when no models are cached.
- **BF-002**: Frontend `ModelSelector` MUST show an empty-state message when the model list is empty.
- **BF-003**: Frontend `refreshAll()` MUST handle partial endpoint failures gracefully — successful responses should still populate their respective state.
- **BF-004**: Backend `_fetch_foundry_models()` MUST NOT return a fabricated model entry when no models actually exist.
- **BF-005**: Application startup (lifespan) MUST NOT crash or hang when no models are available.
- **BF-006**: Error messages MUST be user-friendly and actionable (constitution principle II).

### Edge Cases

- Foundry service starts after app loads (late availability).
- Foundry service returns HTTP 500 on `/openai/models`.
- Network timeout on model list request.
- Config references a model ID that no longer exists in cache.
