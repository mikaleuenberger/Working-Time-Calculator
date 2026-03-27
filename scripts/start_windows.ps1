# WTCalculator - Windows starter (PowerShell)
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1

$ErrorActionPreference = 'Stop'

# Ensure we run from repo root
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

Write-Host "Repo: $repoRoot"

# Allow script execution for this process only
try {
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null
} catch {
    # ignore if not permitted
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating venv..."
    py -m venv .venv
}

Write-Host "Activating venv..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt

if (-not $env:WTCALC_PORT) {
    $env:WTCALC_PORT = "8081"
}

Write-Host "Starting WTCalculator on http://localhost:$env:WTCALC_PORT ..."
Start-Process "http://localhost:$env:WTCALC_PORT" | Out-Null

python main.py
