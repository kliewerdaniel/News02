#!/bin/bash
echo "Activating News02 virtual environment..."
source venv/bin/activate
echo ""
echo "News02 environment activated!"
echo "Run: python run_web.py"
echo ""
exec "$SHELL"
