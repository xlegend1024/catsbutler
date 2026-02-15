# CatsButler

Windows local AI chat app with FastAPI backend and React + Fluent UI frontend.

## Features

- Local-first chat on Microsoft Foundry Local runtime
- Service start/stop and model selection in Options panel
- Alpaca-based stock quote tool and inline line chart rendering
- Local conversation history persisted as JSON and reloadable from History menu
- Thin frontend architecture (business logic centralized in backend APIs)

## Prerequisites

- Windows 11
- Microsoft Foundry Local
- Python 3.12+
- Node.js 20+

## Run locally

### 1) Install dependencies

```powershell
winget install Microsoft.FoundryLocal
uv sync
cd src/ui
npm install
cd ../..
```

### 2) Start backend API

```powershell
python src/api/foundry_api.py
```

Backend health check:

```powershell
curl http://127.0.0.1:8000/health
```

### 3) Start frontend

```powershell
cd src/ui
npm run dev
```

Open `http://localhost:5173`.

## Using the app

1. Open **Options** panel.
2. Start the service and select a model.
3. (Optional) Save Alpaca credentials in Config.
4. Chat in the main window.
5. Open previous sessions from **History**.

## Conversation storage

- Saved in `src/api/storage/conversations/`
- Filename format: `yyyy-MM-dd_HH-mm` with collision suffix when needed
- Each JSON file includes `id`, `title`, `createdAt`, `updatedAt`, and `messages`

## Test

```powershell
python -m pytest test/contract test/integration test/performance test/security -q
```

> Note: `test/test_chat_with_npu.py` requires `foundry_local` runtime dependency and may fail in environments without that package.
