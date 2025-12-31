@echo off
chcp 65001 >nul
setlocal

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%main.py"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

if not exist "%PY_SCRIPT%" (
    echo Error: main.py not found at %PY_SCRIPT%
    pause
    exit /b 1
)

REM Run Python script with all arguments, suppress warnings
set PYTHONWARNINGS=ignore
python "%PY_SCRIPT%" %* 2>nul