#!/bin/bash

# Test runner script for Time Tracker
echo "Running Time Tracker Tests..."
echo "=============================="

# Activate virtual environment
source venv/bin/activate

# Install test dependencies if not already installed
pip install -r requirements.txt

# Run tests with coverage
echo "Running unit tests..."
python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

echo ""
echo "Test coverage report generated in htmlcov/index.html"
echo "=============================="
echo "Tests completed!"
