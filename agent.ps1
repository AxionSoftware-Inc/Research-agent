$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found at: $venvPython" -ForegroundColor Red
    exit 1
}

$env:PYTHONPATH = $root
& $venvPython (Join-Path $root "run_agent.py") @args
