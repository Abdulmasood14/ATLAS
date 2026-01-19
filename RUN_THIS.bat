@echo off
REM ============================================================================
REM Financial RAG Chatbot - Quick Startup Script (Backend Only)
REM ============================================================================

echo.
echo ============================================================================
echo FINANCIAL RAG CHATBOT - BACKEND STARTUP
echo ============================================================================
echo.

cd /d "%~dp0backend"

echo [1/3] Checking Python installation...
py -3.11 --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 3.11 not found!
    echo Please install Python 3.11 from python.org
    pause
    exit /b 1
)

echo.
echo [2/3] Starting Backend Server...
echo Backend will start at: http://localhost:8000
echo API Docs will be at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

py -3.11 main.py

pause
