@echo off
REM Ollama Startup Script for Windows
REM This script starts Ollama service in the background

echo Starting Ollama service...
start "" "ollama" serve

echo Ollama service started successfully!
timeout /t 3 /nobreak >nul