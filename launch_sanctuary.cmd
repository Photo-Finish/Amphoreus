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

rem --- keep temp on D: (C: is nearly full) ---
set TEMP=D:\temp
set TMP=D:\temp
if not exist D:\temp mkdir D:\temp

rem --- locate the project root (folder of this script) ---
set ROOT=%~dp0
set PYTHON=%ROOT%..\.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found at %PYTHON%
    echo         Expected the venv at: D:\Workspace\.venv
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

echo [3/3] Running the interface (keep this window open)...
echo       Close this window to stop the interface.
echo ============================================================
"%PYTHON%" -m streamlit run "%ROOT%src\ui_app.py" --server.headless true --server.port 8501

endlocal
