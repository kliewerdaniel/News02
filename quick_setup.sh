#!/bin/bash

echo "===================================="
echo "    News02 Quick Setup (Linux/Mac)"
echo "===================================="
echo ""
echo "This will automatically set up News02 with:"
echo "- Virtual environment (venv folder)"
echo "- All required dependencies"
echo "- Configuration files"
echo ""

if [ ! -f .env ]; then
    echo "'.env' not found. Copying 'settings/env/example.env' to '.env'..."
    cp settings/env/example.env .env
fi

read -p "Press Enter to continue or Ctrl+C to cancel..."

python3 auto_setup.py

echo ""
echo "Setup script completed!"
echo "Check the output above for next steps."