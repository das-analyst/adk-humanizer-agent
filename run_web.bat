@echo off
title ADK AI Text Humanizer Agent Web UI
cd /d "%~dp0"

echo =====================================================================
echo Checking for existing processes on port 8000...
echo =====================================================================

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Clearing previous process PID: %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo =====================================================================
echo Starting Google ADK Web UI for AI Text Humanizer Agent...
echo Access in your browser at: http://127.0.0.1:8000
echo =====================================================================
call .venv\Scripts\activate.bat
adk web --port 8000 .
pause
