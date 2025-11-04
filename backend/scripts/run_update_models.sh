#!/bin/bash

# Script to update model providers in the database
# This script runs the Python update script with proper environment setup

set -e

echo "=========================================="
echo "🚀 Model Provider Update Script"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"

# Check if virtual environment exists
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "✅ Virtual environment found"
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "   Please create and activate your virtual environment first"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo ""
echo "=========================================="
echo "🔄 Running model provider update..."
echo "=========================================="
echo ""

# Run the Python script
python scripts/update_model_providers.py

exit_code=$?

echo ""
echo "=========================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ Model provider update completed successfully!"
else
    echo "❌ Model provider update failed with exit code: $exit_code"
fi
echo "=========================================="

exit $exit_code
