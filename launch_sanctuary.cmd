@echo off
rem ============================================================
rem  Project Amphoreus - The Sanctuary of the Chrysos Heirs
rem  One-click launcher: starts Ollama if needed, starts the world
rem  engine, opens the browser, and runs the visual interface.
rem
rem  Double-click this file (or the desktop shortcut).
rem  Closing this window does NOT stop the Sanctuary.
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
    echo [ERROR] Python venv not found at %ROOT%.venv  or %ROOT%..\.venv
    echo         Create it:  python -m venv .venv
    echo         then:       .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "%ROOT%world_runtime" mkdir "%ROOT%world_runtime"

echo ============================================================
echo   Project Amphoreus - The Sanctuary of the Chrysos Heirs
echo ============================================================
echo [1/4] Checking the Ollama server...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if %errorlevel% equ 1 (
    echo       Server not running - starting it...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%tools\start_ollama.ps1"
) else (
    echo       Ollama server already running.
)

rem --- Senses model mode (unified | quality) --------------------------------
rem   unified : ONE model (gemma3n, 8B E2B) hears music AND sees pictures
rem   quality : qwen3-vl:8b (vision) + gemma3n (audio) - best per channel
rem   (verified 2026-08-11: qwen3-omni is NOT on Ollama; gemma3n = "gemma3n")
rem   The model mapping is resolved by src/core/senses.py from SENSES_MODE /
rem   .env - this variable just picks the option.
set SENSES_MODE=unified

echo [2/4] Ensuring the little Amphoreus keeps living...
powershell -NoProfile -Command "Start-Process -FilePath '%PYTHON%' -ArgumentList '-m','src.world.world_engine','--interval','900' -WorkingDirectory '%ROOT%' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%world_runtime\engine.log' -RedirectStandardError '%ROOT%world_runtime\engine.log.err'"
echo       World engine start requested.

echo [3/4] Starting the interface in the background...
powershell -NoProfile -Command ^
  "$ok = $false; ^
   try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true } } catch {}; ^
   if ($ok) { Write-Host '      Interface already running on port 8501 (reusing).'; exit 0 }; ^
   $p = Start-Process -FilePath '%PYTHON%' -ArgumentList @('-m','streamlit','run','src\ui_app.py','--server.headless','true','--server.port','8501','--server.address','127.0.0.1','--browser.gatherUsageStats','false') -WorkingDirectory '%ROOT%' -WindowStyle Minimized -RedirectStandardOutput '%ROOT%world_runtime\ui.log' -RedirectStandardError '%ROOT%world_runtime\ui.log.err' -PassThru; ^
   Write-Host ('      Streamlit started (pid ' + $p.Id + ').')"

echo [4/4] Waiting for the interface, then opening it in your browser...
set /a _n=0
:wait_ui
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if not errorlevel 1 goto ui_ready
set /a _n+=1
if %_n% geq 90 goto ui_open
goto wait_ui

:ui_ready
echo       The Sanctuary is ready.
:ui_open
powershell -NoProfile -Command "Start-Process 'http://127.0.0.1:8501/'"

echo ============================================================
echo   The Sanctuary is open in your browser:
echo       http://127.0.0.1:8501
echo   It keeps running if you close this window.
echo   Stop the world from the Control Panel, or close Streamlit in Task Manager.
echo   Senses mode: %SENSES_MODE%
echo   Press any key to close this launcher window.
echo ============================================================
pause >nul

endlocal
