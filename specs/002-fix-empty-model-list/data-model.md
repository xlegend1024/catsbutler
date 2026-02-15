# Data Model: Empty Model List Bug Fix

**Branch**: `002-fix-empty-model-list` | **Date**: 2026-02-15

## Entities

No new entities are introduced. This fix modifies behavior of existing entities.

### ModelProfile (existing — no schema change)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `string` | Model identifier from Foundry Local |
| `displayName` | `string` | Human-readable model name |
| `availability` | `enum: available, downloading, unavailable` | Status |
| `recommendedMode` | `enum: NPU, GPU, CPU, unknown` | Hardware mode |

### ModelListResponse (existing — no schema change)

| Field | Type | Notes |
|-------|------|-------|
| `items` | `ModelProfile[]` | **Can now be empty `[]` without error** |

## State Transitions

### Model List Loading States

```
┌────────────┐     GET /models     ┌───────────────┐
│  loading   │ ──────────────────> │  items: [...]  │  (normal: models exist)
│            │                     │  items: []     │  (empty: no models cached)
└────────────┘                     └───────────────┘
       │                                   │
       │  network/500 error                │  empty list
       ▼                                   ▼
┌────────────┐                     ┌───────────────────────────┐
│   error    │                     │  show empty-state message │
│  (logged)  │                     │  "No models available"    │
└────────────┘                     └───────────────────────────┘
```

### Frontend `refreshAll()` — Before vs After

**Before** (broken):
```
Promise.all([status, models, config, ...])
  → ANY failure → catch(() => {}) → ALL state remains default → broken UI
```

**After** (fixed):
```
Promise.allSettled([status, models, config, ...])
  → Each result processed independently
  → Fulfilled → update state
  → Rejected → log warning, keep previous state
```

## Validation Rules

- `GET /models` MUST always return HTTP 200 with `{ items: [...] }` — never 500 for empty models.
- Frontend MUST NOT assume `models.length > 0` in any render path.
- `selectedModelId` in config MAY reference a model not in the current list (stale config) — UI should handle gracefully.
