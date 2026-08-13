@echo off
rem ============================================================
rem  Project Amphoreus - The Sanctuary of the Chrysos Heirs
rem  One-click launcher: starts Ollama, opens the browser,
rem  and runs the visual interface.
rem
rem  Double-click this file (or the desktop shortcut).
rem ============================================================
setlocal
title Project Amphoreus - The Sanctuary of the Chrysos Heirs

rem --- keep temp on D: if a D: drive exists (C: may be nearly full) ---
if exist D:\ (
    set TEMP=D:\temp
    set TMP=D:\temp
    if not exist D:\temp mkdir D:\temp
)

rem --- locate the project root (folder of this script) ---
set ROOT=%~dp0
rem Prefer a venv INSIDE the repo (.venv); fall back to the sibling venv (..\.venv)
set PYTHON=%ROOT%.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=%ROOT%..\.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found at %ROOT%.venv  (nor ..\.venv)
    echo         Create it:  python -m venv .venv
    echo         then:       .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo ============================================================
echo   Project Amphoreus - The Sanctuary of the Chrysos Heirs
echo ============================================================
echo [1/3] Checking the Ollama server...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if %errorlevel% equ 1 (
    echo       Server not running - starting it...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%tools\start_ollama.ps1"
) else (
    echo       Ollama server already running.
)

echo [2/3] Opening the interface in your browser...
start "" http://localhost:8501

rem --- Senses model mode (unified | quality) --------------------------------
rem   unified : ONE model (gemma3n, 8B E2B) hears music AND sees pictures
rem   quality : qwen3-vl:8b (vision) + gemma3n (audio) — best per channel
rem   (verified 2026-08-11: qwen3-omni is NOT on Ollama; gemma3n = "gemma3n")
rem   The model mapping is resolved by src/core/senses.py from SENSES_MODE /
rem   .env — this variable just picks the option.
set SENSES_MODE=unified

echo [3/3] Running the interface (keep this window open)...
echo       Senses mode: %SENSES_MODE%  (mapping in .env; unified=gemma3n, quality=qwen3-vl:8b+gemma3n)
echo       Close this window to stop the interface.
echo ============================================================
"%PYTHON%" -m streamlit run "%ROOT%src\ui_app.py" --server.headless true --server.port 8501

endlocal
