# Research: Empty Model List Bug Fix

**Branch**: `002-fix-empty-model-list` | **Date**: 2026-02-15

## Research Task 1: Foundry Local `/openai/models` behavior with no cached models

**Decision**: The Foundry Local REST API (`GET /openai/models`) returns an empty JSON array `[]` when no models are cached, and returns a connection error when the service is not running. Neither case should be treated as an application error.

**Rationale**: The current `list_cached_models_http()` already handles both cases by returning `[]`. The bug is not in the HTTP call itself but in how the empty result propagates through `_fetch_foundry_models()` and ultimately to the frontend.

**Alternatives considered**:
- Raising an exception on empty list → Rejected: empty list is a valid state (fresh install).
- Polling/retrying → Rejected: adds complexity; user can manually refresh.

## Research Task 2: Best practice for `Promise.all` resilience in React refresh

**Decision**: Use `Promise.allSettled()` instead of `Promise.all()` in `refreshAll()`. Each endpoint result is processed independently: fulfilled results update state, rejected results are logged but don't block other state updates.

**Rationale**: `Promise.all()` is all-or-nothing — one failure prevents all state from loading. With `Promise.allSettled()`, the UI can show partial data (e.g., service status is available even if model list fails).

**Alternatives considered**:
- Individual try/catch per API call → Rejected: verbose and error-prone for 6+ calls.
- Wrapping each call in a helper returning `null` on failure → Viable but `Promise.allSettled` is idiomatic and clearer.

## Research Task 3: Empty-state UX for model dropdown

**Decision**: When `models` array is empty, `ModelSelector` renders a disabled `Dropdown` with placeholder text: "No models available". An info `MessageBar` below provides actionable guidance: "Download a model using `foundry model download <alias>` to get started."

**Rationale**: Aligns with constitution principle II (beginner-friendly) and principle V (graceful degradation). Users must understand *why* the list is empty and *what to do*.

**Alternatives considered**:
- Hiding the dropdown entirely → Rejected: loses discoverability of the model selection feature.
- Showing a toast notification → Rejected: too transient for a persistent state.

## Research Task 4: Fallback model fabrication in `_fetch_foundry_models()`

**Decision**: Remove the fallback that fabricates a model entry from `config.selectedModelId` when the model list is empty. Instead, return an honest empty list `[]`. The frontend handles the empty state.

**Rationale**: Fabricating a model that doesn't exist in cache causes downstream failures (e.g., `_load_model_http` will fail trying to load a non-existent model). The current fallback in the `except` branch masks real errors.

**Alternatives considered**:
- Keeping the fallback but marking it as `availability: "unavailable"` → Viable but adds complexity for questionable value.
- Returning the fallback only if the service is unreachable (not if models are empty) → Still misleading.

## Summary of Changes Required

| File | Change | Rationale |
|------|--------|-----------|
| `src/api/services/model_service.py` | Remove fabricated fallback in exception handler; return `[]` on empty | BF-001, BF-004 |
| `src/ui/src/App.tsx` | Replace `Promise.all` with `Promise.allSettled` in `refreshAll()` | BF-003 |
| `src/ui/src/components/options/ModelSelector.tsx` | Add empty-state message when `models.length === 0` | BF-002, BF-006 |
| `src/api/foundry_api.py` | Ensure `/models` endpoint doesn't crash on empty list (verify) | BF-001, BF-005 |
