# Tasks: Fix Empty Model List Failure

**Branch**: `002-fix-empty-model-list` | **Date**: 2026-02-15 | **Plan**: [plan.md](plan.md)

## Phase 1: Backend Fix

**Purpose**: Ensure `GET /models` returns an honest empty list when no models are cached, instead of fabricating a fake model entry.

- [X] T001 [US2] Remove fabricated fallback model in `_fetch_foundry_models()` exception handler — return `[]` instead of fake model from config in src/api/services/model_service.py
- [X] T002 [US2] Verify `/models` endpoint returns `{"items": []}` without error when `model_service.list_models()` returns `[]` in src/api/foundry_api.py (verify only — no code change expected)

**Checkpoint**: `GET /models` returns `{"items": []}` when Foundry service is down or has no cached models. No 500 errors.

---

## Phase 2: Frontend Fix

**Purpose**: Make frontend resilient to partial API failures and provide clear UX when model list is empty.

- [X] T003 [US2] Replace `Promise.all` with `Promise.allSettled` in `refreshAll()` — process each result independently in src/ui/src/App.tsx
- [X] T004 [US2] Add empty-state rendering in `ModelSelector` — show disabled dropdown with "No models available" and guidance message in src/ui/src/components/options/ModelSelector.tsx

**Checkpoint**: App loads correctly even when `/models` or `/service/status` endpoints fail. Model dropdown shows actionable guidance when models list is empty.

---

## Dependencies & Execution Order

- **Phase 1** → **Phase 2**: Frontend fix depends on backend returning clean empty list
- T001 and T002 are sequential (T002 verifies T001)
- T003 and T004 are independent [P] — can run in parallel
