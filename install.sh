#!/bin/bash

# Time Tracker - Dependency Installation Script
echo "Installing Time Tracker Dependencies..."
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "To run the application:"
echo "  ./run.sh"
echo ""
echo "To run tests:"
echo "  ./run_tests.sh"
echo ""
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
