#!/bin/bash

# Setup script for Self-Correcting Technical Architect
# This script initializes the development environment and configures API keys

set -e  # Exit on error

echo "================================"
echo "Self-Correcting Technical Architect"
echo "Environment Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Update .env with your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - E2B_API_KEY"
else
    echo "✅ .env file already exists"
fi
echo ""

# Create logs directory
mkdir -p logs
echo "✅ Logs directory ready"
echo ""

echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys (OPENAI_API_KEY, E2B_API_KEY)"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the agent: python -m src.main"
echo ""
