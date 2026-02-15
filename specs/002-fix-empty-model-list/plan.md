# Implementation Plan: Fix Empty Model List Failure

**Branch**: `002-fix-empty-model-list` | **Date**: 2026-02-15 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/002-fix-empty-model-list/spec.md`

## Summary

When no models are cached in Foundry Local (fresh install or service offline), the model list endpoint and frontend initialization fail silently, leaving the UI broken. This fix ensures `GET /models` returns a valid empty list, the frontend handles partial load failures via `Promise.allSettled`, and the `ModelSelector` shows actionable empty-state guidance.

## Technical Context

**Language/Version**: Python 3.11, TypeScript (React 18)  
**Primary Dependencies**: FastAPI, Fluent UI React v9, httpx  
**Storage**: JSON config files (no change)  
**Testing**: pytest (backend), manual verification (frontend)  
**Target Platform**: Windows (Surface NPU/GPU devices)  
**Project Type**: Web application (Python API + React frontend)  
**Performance Goals**: No latency regression; startup should not block on model listing  
**Constraints**: Offline-capable after initial setup; local-first (constitution)  
**Scale/Scope**: Bug fix — 4 files modified, ~30 lines changed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First AI | PASS | No cloud dependencies added |
| II. Beginner-Friendly | PASS | Empty-state message provides actionable guidance |
| III. API-First Architecture | PASS | Fix is in API layer; frontend consumes API |
| IV. Modern UX | PASS | Fluent UI MessageBar for empty-state |
| V. Progressive Enhancement | PASS | App adapts to missing models gracefully |
| Quality: Type hints | PASS | No new untyped code |
| Quality: Testing | PASS | Existing contract tests cover endpoint shape |
| Quality: Security | PASS | No new inputs or attack surface |

**Post-Phase 1 re-check**: All gates still PASS. No new violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-empty-model-list/
├── plan.md              # This file
├── research.md          # Phase 0 output — decisions on fallback, Promise.allSettled, empty UX
├── data-model.md        # Phase 1 output — no schema changes, state transition diagrams
├── quickstart.md        # Phase 1 output — reproduce & verify steps
├── contracts/           # Phase 1 output — OpenAPI patch showing empty list as valid
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (created by /speckit.tasks — NOT this command)
```

### Source Code (files to modify)

```text
src/
├── api/
│   ├── foundry_api.py                    # Verify /models endpoint handles empty list
│   └── services/
│       └── model_service.py              # Remove fabricated fallback; return honest []
└── ui/
    └── src/
        ├── App.tsx                        # Replace Promise.all with Promise.allSettled
        └── components/
            └── options/
                └── ModelSelector.tsx      # Add empty-state message
```

**Structure Decision**: No new files or directories. This is a targeted bug fix modifying 4 existing files across backend and frontend.

## Complexity Tracking

No constitution violations. This is a minimal bug fix aligned with all principles.

## Change Details

### Change 1: `src/api/services/model_service.py`

**What**: In `_fetch_foundry_models()`, remove the `except` branch that fabricates a model from `config.selectedModelId`. When `list_cached_models_http()` returns empty, return `[]`. When it throws, log the error and return `_cached_models` if available, otherwise `[]`.

**Why**: BF-001, BF-004 — fabricating a model that doesn't exist causes downstream load failures.

### Change 2: `src/ui/src/App.tsx`

**What**: Replace `Promise.all()` with `Promise.allSettled()` in `refreshAll()`. Process each result independently — fulfilled results update state, rejected results are logged.

**Why**: BF-003 — one endpoint failure should not prevent all state from loading.

### Change 3: `src/ui/src/components/options/ModelSelector.tsx`

**What**: When `models.length === 0`, render a disabled dropdown with "No models available" placeholder and a `MessageBar` with guidance text.

**Why**: BF-002, BF-006 — user needs to know what to do when no models exist.

### Change 4: `src/api/foundry_api.py` (verify only)

**What**: Confirm that the `/models` endpoint returns `ModelListResponse(items=[])` without error when `model_service.list_models()` returns `[]`. No code change expected — just verification.

**Why**: BF-005 — defense in depth.
