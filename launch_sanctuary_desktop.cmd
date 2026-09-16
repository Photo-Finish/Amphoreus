@echo off
rem ============================================================
rem  Amphoreus Sanctuary — DESKTOP WINDOW (Stage-2 shell)
rem  Same Streamlit UI in a native window. Always uses the project
rem  venv + tools\desktop_sanctuary.py so code changes are picked up.
rem  Browser launcher remains: launch_sanctuary.cmd
rem ============================================================
setlocal
title Amphoreus Sanctuary (Desktop)

if exist D:\ (
    set TEMP=D:\temp
    set TMP=D:\temp
    if not exist D:\temp mkdir D:\temp
)

set ROOT=%~dp0
set PYTHON=%ROOT%.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=%ROOT%..\.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Project venv not found.
    echo         Expected: %ROOT%.venv\Scripts\python.exe
    echo         or:       %ROOT%..\.venv\Scripts\python.exe
    pause
    exit /b 1
)

echo Starting the Sanctuary desktop window via Python...
"%PYTHON%" "%ROOT%tools\desktop_sanctuary.py"
if errorlevel 1 pause
endlocal
