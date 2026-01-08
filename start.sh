#!/bin/bash

# BYTE Backend Quick Start Script
# Makes it super easy to start the backend

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║      🚀 BYTE Security Agent - Backend Startup           ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Starting backend with Gemini 2.5 Pro thinking support..."
echo ""

# Check if python3 exists
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Create one with: cp .env.example .env"
    echo "And add your GOOGLE_API_KEY"
    echo ""
fi

# Start the server from backend directory
cd backend && python3 run.py
