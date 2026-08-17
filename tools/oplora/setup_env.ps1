# Amphoreus OPLoRA env setup (Windows / RTX 50-series)
# Run from repo root in PowerShell:
#   .\tools\oplora\setup_env.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

$env:HF_HOME = "D:\hf-cache"
$env:HUGGINGFACE_HUB_CACHE = "D:\hf-cache\hub"
$env:PIP_CACHE_DIR = "D:\hf-cache\pip"
New-Item -ItemType Directory -Force -Path $env:HF_HOME, $env:HUGGINGFACE_HUB_CACHE, $env:PIP_CACHE_DIR, (Join-Path $Root "tools\oplora\outputs"), (Join-Path $Root "tools\oplora\data") | Out-Null

$Venv = Join-Path $Root ".venv-oplora"
if (-not (Test-Path $Venv)) {
    python -m venv $Venv
}

& "$Venv\Scripts\python.exe" -m pip install --upgrade pip wheel
# Blackwell (sm_120) needs cu128 — prefer nightly on Windows if stable lacks kernels
& "$Venv\Scripts\python.exe" -m pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128
& "$Venv\Scripts\python.exe" -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
& "$Venv\Scripts\python.exe" (Join-Path $PSScriptRoot "check_env.py")
