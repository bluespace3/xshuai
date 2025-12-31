@echo off
REM Remove Ollama from Windows Startup
REM This script removes the Ollama startup shortcut

set "startupFolder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "shortcutPath=%startupFolder%\Start-Ollama.lnk"

if exist "%shortcutPath%" (
    del "%shortcutPath%"
    echo Ollama startup shortcut removed successfully!
) else (
    echo Ollama startup shortcut not found.
)

pause