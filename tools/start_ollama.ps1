# start_ollama.ps1 — start the Ollama server with the project's models dir.
#
# The server must point at models\ollama (OLLAMA_MODELS), otherwise the app
# returns "model not found". This script kills any stale ollama processes
# (including a tray-app instance that may serve a stale directory), then starts
# a detached server so it keeps running after the terminal closes.
#
# Usage:  powershell -File tools\start_ollama.ps1
$ErrorActionPreference = 'Continue'

# Portable paths: everything is derived from this script's location, so the
# script works from any checkout. Override with env vars if your layout differs.
$root = Split-Path $PSScriptRoot -Parent
$modelsDir = Join-Path $root 'models\ollama'
$ollamaExe = $env:OLLAMA_EXE
if (-not $ollamaExe) {
    $ollamaExe = (Get-Command ollama -ErrorAction SilentlyContinue).Source
}
if (-not $ollamaExe) {
    # last-resort default: the standard Ollama install location
    $ollamaExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
}

$env:OLLAMA_MODELS = $modelsDir
$env:OLLAMA_HOST = '127.0.0.1:11434'
# Default context window for every request (default 4096 was too small — long
# music-audio and big canon prompts got truncated). 8192 doubles the headroom;
# raise further if RAM allows (each token of context costs KV-cache memory).
$env:OLLAMA_CONTEXT_LENGTH = '8192'
# 2026-08-14: with only ~11 GB free RAM, gemma3:27b failed to load at 8192 ctx
# ("failed to allocate CUDA_Host buffer of size ~11.1 GB" -> HTTP 500 from every
# call). Flash attention + a quantized (q8_0) KV cache cut the KV-cache memory
# drastically, letting the 27B model load at 8192 on this machine again.
$env:OLLAMA_FLASH_ATTENTION = '1'
$env:OLLAMA_KV_CACHE_TYPE = 'q8_0'

# 1. Stop any stale ollama processes (tray app may serve the wrong models dir).
#    Also kill orphaned llama-server children: when the server is force-killed,
#    its model-loading child keeps the loaded model's VRAM forever, which makes
#    bigger models fail with "cudaMalloc failed / CUDA_Host buffer" (2026-08-10).
Get-Process -Name '*ollama*','llama-server' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 2. Start a detached server (survives terminal close).
Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden

# 3. Wait for it to listen.
Start-Sleep -Seconds 5
$conn = Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "OK  Ollama server listening on 127.0.0.1:11434 (models: $env:OLLAMA_MODELS)"
    $tags = curl.exe -s --max-time 10 "http://127.0.0.1:11434/api/tags" 2>$null
    if ($tags -match 'gemma3:27b') {
        Write-Host "OK  Heir model visible: gemma3:27b"
    } else {
        Write-Host "WARN  Server is up but gemma3:27b not visible yet: $tags"
    }
} else {
    Write-Host "FAILED  Server did not start. Check: $ollamaExe"
}
