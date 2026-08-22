@echo off
rem ============================================================
rem  Amphoreus Sanctuary — DESKTOP WINDOW (new Stage-2 shell)
rem  Opens the same Streamlit UI in a native window, not a browser tab.
rem  Original browser launcher remains: launch_sanctuary.cmd
rem ============================================================
setlocal
title Amphoreus Sanctuary (Desktop)

if exist D:\ (
    set TEMP=D:\temp
    set TMP=D:\temp
    if not exist D:\temp mkdir D:\temp
)

set ROOT=%~dp0
set EXE=%ROOT%AmphoreusSanctuary.exe
set PYTHON=%ROOT%.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=%ROOT%..\.venv\Scripts\python.exe

if exist "%EXE%" (
    start "" "%EXE%"
    exit /b 0
)

if not exist "%PYTHON%" (
    echo [ERROR] Neither AmphoreusSanctuary.exe nor the project venv was found.
    echo         Build the exe:  powershell -ExecutionPolicy Bypass -File tools\build_desktop_exe.ps1
    pause
    exit /b 1
)

echo AmphoreusSanctuary.exe not found — running the desktop shell via Python.
"%PYTHON%" "%ROOT%tools\desktop_sanctuary.py"
if errorlevel 1 pause
endlocal
