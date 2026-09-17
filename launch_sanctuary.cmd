@echo off
rem ============================================================
rem  Project Amphoreus - The Sanctuary of the Chrysos Heirs
rem  Starts the interface first (Python boot). Closing this window
rem  does NOT stop Streamlit.
rem ============================================================
setlocal
title Project Amphoreus - The Sanctuary of the Chrysos Heirs

if exist D:\ (
    set TEMP=D:\temp
    set TMP=D:\temp
    if not exist D:\temp mkdir D:\temp
)

set ROOT=%~dp0
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

rem --- Senses model mode (unified | quality) --------------------------------
rem   unified : ONE model (gemma3n) hears music AND sees pictures
rem   quality : qwen3-vl:8b (vision) + gemma3n (audio)
set SENSES_MODE=unified

set NO_PROXY=127.0.0.1,localhost
set no_proxy=127.0.0.1,localhost
set PYTHONUNBUFFERED=1
set STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

"%PYTHON%" "%ROOT%tools\boot_sanctuary.py" %*
set _ec=%errorlevel%
if not "%_ec%"=="0" (
    echo.
    echo Boot did not finish. See world_runtime\ui.log.err
    pause
    exit /b %_ec%
)
echo.
echo Press any key to close this launcher window.
pause >nul
endlocal
