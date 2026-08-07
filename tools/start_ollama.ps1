# start_ollama.ps1 — start the Ollama server with the project's models dir.
#
# The server must point at models\ollama (OLLAMA_MODELS), otherwise the app
# returns "model not found". This script kills any stale ollama processes
# (including a tray-app instance that may serve a stale directory), then starts
# a detached server so it keeps running after the terminal closes.
#
# Usage:  powershell -File tools\start_ollama.ps1
$ErrorActionPreference = 'Continue'

$ollamaExe = 'C:\Users\17501\AppData\Local\Programs\Ollama\ollama.exe'
$env:OLLAMA_MODELS = 'D:\Workspace\Amphoreus\models\ollama'
$env:OLLAMA_HOST = '127.0.0.1:11434'

# 1. Stop any stale ollama processes (tray app may serve the wrong models dir).
Get-Process -Name '*ollama*' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Start a detached server (survives terminal close).
Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden

# 3. Wait for it to listen.
Start-Sleep -Seconds 5
$conn = Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "OK  Ollama server listening on 127.0.0.1:11434 (models: $env:OLLAMA_MODELS)"
    $tags = curl.exe -s --max-time 10 "http://127.0.0.1:11434/api/tags" 2>$null
    if ($tags -match 'qwen2.5:14b-instruct' -and $tags -match 'qwen2.5vl' -and $tags -match 'qwen2.5-omni') {
        Write-Host "OK  All three models visible: qwen2.5:14b-instruct, qwen2.5vl:7b, qwen2.5-omni"
    } else {
        Write-Host "WARN  Server is up but models not all visible yet: $tags"
    }
} else {
    Write-Host "FAILED  Server did not start. Check: $ollamaExe"
}
