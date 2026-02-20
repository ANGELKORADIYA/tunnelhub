#!/bin/bash

# TunnelHub Quick Start Script for Linux/Mac

echo "============================================"
echo "   TunnelHub - Quick Start"
echo "============================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env file and add your ngrok tokens!"
    echo ""
    read -p "Press Enter to continue after editing .env..."
fi

# Start the server
echo ""
echo "Starting TunnelHub server..."
echo ""
echo "Dashboard: http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
