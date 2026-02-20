@echo off
REM TunnelHub Quick Start Script for Windows

echo ============================================
echo    TunnelHub - Quick Start
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file and add your ngrok tokens!
    echo.
    pause
)

REM Start the server
echo.
echo Starting TunnelHub server...
echo.
echo Dashboard: http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py
