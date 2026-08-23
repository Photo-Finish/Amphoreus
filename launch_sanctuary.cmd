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
    echo [ERROR] Python venv not found at %ROOT%.venv  or %ROOT%..\.venv
    echo         Create it:  python -m venv .venv
    echo         then:       .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

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
powershell -NoProfile -Command ^
  "$py='%PYTHON%'; $root='%ROOT%'; $alive=$false; ^
   try { $alive = (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'world_engine' }) -ne $null } catch {}; ^
   if (-not $alive) { ^
     Start-Process -FilePath $py -ArgumentList '-m','src.world.world_engine','--interval','900' -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput ($root+'world_runtime\engine.log') -RedirectStandardError ($root+'world_runtime\engine.log.err'); ^
     Write-Host '      World engine started (interval 900s).' ^
   } else { Write-Host '      World engine already running.' }"

echo [3/4] Starting the interface in the background...
set UI_OWNS=0
del "%ROOT%world_runtime\ui_launcher_owns.txt" 2>nul
powershell -NoProfile -Command ^
  "if (Test-Path '%ROOT%world_runtime\ui_launcher_owns.txt') { Remove-Item '%ROOT%world_runtime\ui_launcher_owns.txt' -Force -ErrorAction SilentlyContinue }; ^
   $ok = $false; ^
   try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true } } catch {}; ^
   if ($ok) { Write-Host '      Interface already running on port 8501 (reusing).'; exit 0 }; ^
   $p = Start-Process -FilePath '%PYTHON%' -ArgumentList @('-m','streamlit','run','%ROOT%src\ui_app.py','--server.headless','true','--server.port','8501','--server.address','127.0.0.1','--browser.gatherUsageStats','false') -WorkingDirectory '%ROOT%' -WindowStyle Minimized -RedirectStandardOutput '%ROOT%world_runtime\ui.log' -RedirectStandardError '%ROOT%world_runtime\ui.log.err' -PassThru; ^
   $p.Id | Out-File -FilePath '%ROOT%world_runtime\ui.pid' -Encoding ascii -NoNewline; ^
   '1' | Out-File -FilePath '%ROOT%world_runtime\ui_launcher_owns.txt' -Encoding ascii -NoNewline; ^
   Write-Host ('      Streamlit started (pid ' + $p.Id + ').')"
if exist "%ROOT%world_runtime\ui_launcher_owns.txt" set UI_OWNS=1

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
if "%UI_OWNS%"=="1" (
echo   This window owns the interface — close it to stop Streamlit.
) else (
echo   Interface was already running — closing this window will NOT stop it.
)
echo   Senses mode: %SENSES_MODE%
echo   Press any key (or close this window^) when you are done here.
echo ============================================================
pause >nul

rem --- closing this window stops the interface only if we started it ---
if "%UI_OWNS%"=="1" (
powershell -NoProfile -Command "$id = $null; if (Test-Path '%ROOT%world_runtime\ui.pid') { $id = Get-Content '%ROOT%world_runtime\ui.pid' -ErrorAction SilentlyContinue }; if ($id) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; $owner = (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess; if ($owner) { Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue }; Remove-Item '%ROOT%world_runtime\ui_launcher_owns.txt' -Force -ErrorAction SilentlyContinue"
)

endlocal
