$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found at: $venvPython" -ForegroundColor Red
    exit 1
}

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Starting Local Agent System (Next.js & FastAPI)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend in background
Write-Host "[1/2] Starting Agent API Backend on http://127.0.0.1:8765 ..." -ForegroundColor Green
$serverScript = Join-Path $root "agent\server.py"
$backendProcess = Start-Process -FilePath $venvPython -ArgumentList $serverScript -PassThru -WindowStyle Hidden

# 2. Wait 2 seconds for backend to start
Start-Sleep -Seconds 2

# 3. Start Next.js Frontend
Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
$frontendDir = Join-Path $root "frontend"

# Launch browser after a short delay
Start-Process "http://localhost:3000"

Set-Location $frontendDir
npm.cmd run dev
