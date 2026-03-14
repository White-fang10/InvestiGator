# Auto-generated start script for InvestiGator

Write-Host "=========================================" -ForegroundColor DarkYellow
Write-Host "   Starting InvestiGator Platform...     " -ForegroundColor DarkYellow
Write-Host "=========================================" -ForegroundColor DarkYellow
Write-Host ""

# 1. Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    Exit
}

# 2. Check if Node is installed
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js (npm) is not installed or not in PATH." -ForegroundColor Red
    Exit
}

# 3. Start Backend in a new window
Write-Host "[INFO] Starting Python FastAPI Backend on port 8000..." -ForegroundColor Cyan
$backendPath = Join-Path $PWD "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; if (-not (Test-Path venv)) { python -m venv venv }; .\venv\Scripts\activate; pip install -r requirements.txt; python -m uvicorn app.main:app --reload --port 8000" -WindowStyle Normal

Start-Sleep -Seconds 3

# 4. Start Frontend in a new window
Write-Host "[INFO] Starting React Vite Frontend on port 5173..." -ForegroundColor Cyan
$frontendPath = Join-Path $PWD "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm install; npm run dev" -WindowStyle Normal

# 5. Optional: Check for Ollama
if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    Write-Host "[INFO] Ollama detected. You can run the AI Advisor model with: " -ForegroundColor Green
    Write-Host "       ollama run deepseek-r1:1.5b" -ForegroundColor DarkGray
} else {
    Write-Host "[WARN] Ollama not detected. AI Risk Advisor will use fallback rules." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor DarkYellow
Write-Host " Done! Two windows have been opened." -ForegroundColor Green
Write-Host " The app will be available at: http://localhost:5173" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor DarkYellow
