# Quickstart: Verifying the Empty Model List Fix

**Branch**: `002-fix-empty-model-list`

## Prerequisites

- Python 3.11+
- Node.js 18+
- Foundry Local CLI installed (`foundry --version`)

## Reproduce the Bug (before fix)

1. Stop the Foundry service and clear cached models:
   ```bash
   foundry service stop
   ```
2. Start the backend API:
   ```bash
   cd src/api
   python foundry_api.py
   ```
3. Start the frontend:
   ```bash
   cd src/ui
   npm run dev
   ```
4. Open `http://localhost:5173` — the UI will show a blank/broken state with no model dropdown and no service status.

## Verify the Fix (after fix)

1. With Foundry service stopped and no models cached, start the backend:
   ```bash
   cd src/api
   python foundry_api.py
   ```
2. Start the frontend:
   ```bash
   cd src/ui
   npm run dev
   ```
3. Open `http://localhost:5173`:
   - Service status badge should show "offline" or "stopped"
   - Model dropdown should show "No models available" placeholder
   - An info message should guide: "Download a model using `foundry model download <alias>` to get started"
4. Start the Foundry service and download a model:
   ```bash
   foundry service start
   foundry model download Phi-4-mini-instruct-cuda-gpu:5
   ```
5. Click refresh or reload the page — the model should appear in the dropdown.

## Run Tests

```bash
# Backend contract test
cd C:\Users\hyssh\workspace\catsbutler
python -m pytest test/contract/test_runtime_contract.py -v

# Verify /models endpoint returns [] gracefully
curl http://localhost:8000/models
# Expected: {"items": []}
```
