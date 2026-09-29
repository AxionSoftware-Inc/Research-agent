$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment is not installed yet: $venvPython"
    exit 1
}
$env:VLM_MODEL = if ($env:VLM_MODEL) { $env:VLM_MODEL } else { "qwen3.5-35b-a3b-vlm-q4" }
& $venvPython -m uvicorn research_assistant:app --host 127.0.0.1 --port 8765

