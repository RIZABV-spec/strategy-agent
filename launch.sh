#!/bin/bash

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "========================================"
    echo "  No .env file found!"
    echo "  Copy .env.example to .env and paste"
    echo "  your Anthropic API key, then re-run."
    echo "========================================"
    echo ""
    cp .env.example .env
    exit 1
fi

echo ""
echo "========================================"
echo "  Starting Strategy Agent..."
echo "  Opening http://localhost:8501"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

streamlit run app.py
