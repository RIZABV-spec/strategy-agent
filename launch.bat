@echo off
title Strategy Agent

:: Check if venv exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: Check for .env file
if not exist ".env" (
    echo.
    echo ========================================
    echo  No .env file found!
    echo  Copy .env.example to .env and paste
    echo  your Anthropic API key, then re-run.
    echo ========================================
    echo.
    copy .env.example .env
    pause
    exit /b
)

echo.
echo ========================================
echo  Starting Strategy Agent...
echo  Opening http://localhost:8501
echo  Press Ctrl+C to stop
echo ========================================
echo.

streamlit run app.py
