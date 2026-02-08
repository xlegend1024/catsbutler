Local Foundry chat with Fluent UI React frontend.

## How to run

### 1) Install Foundry Local (PowerShell)

```powershell
winget install Microsoft.FoundryLocal
```

### 2) Install Python packages

```powershell
uv sync
```

### 3) Start the API

```powershell
python foundry_api.py
```

Optional model override:

```powershell
$env:MODEL_ID = "qwen2.5-7b-instruct-qnn-npu:2"
python foundry_api.py
```

### 4) Install UI packages

```powershell
cd ui
npm install
```

### 5) Start the UI

```powershell
npm run dev
```

Open http://localhost:5173
