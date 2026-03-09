#!/bin/bash
# Master script to test and run Intelli-Credit system
# Usage: ./RUN_ME.sh

set -e  # Exit on error

echo ""
echo "======================================================================"
echo "           INTELLI-CREDIT MASTER RUNNER"
echo "======================================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your GROQ_API_KEY"
    echo ""
    echo "Run this command to edit:"
    echo "  nano .env"
    echo ""
    echo "Then run this script again: ./RUN_ME.sh"
    echo ""
    exit 1
fi

# Check if GROQ_API_KEY is set
if ! grep -q "GROQ_API_KEY=gsk_" .env 2>/dev/null; then
    echo "⚠️  GROQ_API_KEY not configured in .env"
    echo ""
    echo "Please edit .env and add your GROQ_API_KEY:"
    echo "  nano .env"
    echo ""
    echo "Then run this script again: ./RUN_ME.sh"
    echo ""
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo ""
else
    echo "⚠️  Virtual environment not found at venv/"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Run all tests
echo "======================================================================"
echo "STEP 1: Running All Tests"
echo "======================================================================"
echo ""

python run_all_tests.py

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Tests failed! Please fix errors before running the app."
    exit 1
fi

echo ""
echo "======================================================================"
echo "STEP 2: Launch Options"
echo "======================================================================"
echo ""
echo "All tests passed! Choose what to do next:"
echo ""
echo "  1. Launch Streamlit app (recommended)"
echo "  2. Exit"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "======================================================================"
        echo "Launching Streamlit App..."
        echo "======================================================================"
        echo ""
        echo "The app will open in your browser at: http://localhost:8501"
        echo ""
        echo "Press Ctrl+C to stop the server"
        echo ""
        streamlit run app.py
        ;;
    2)
        echo ""
        echo "To launch the app later, run:"
        echo "  cd intelli_credit"
        echo "  source venv/bin/activate"
        echo "  streamlit run app.py"
        echo ""
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
