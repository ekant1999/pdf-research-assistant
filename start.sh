#!/bin/bash
# Start script for PDF Research Assistant

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting PDF Research Assistant..."
echo "📁 Project directory: $SCRIPT_DIR"
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OPENAI_API_KEY"
fi

# Start Flask backend
echo "🔧 Starting Flask backend on port 5001..."
python server.py &
FLASK_PID=$!
echo "   Flask PID: $FLASK_PID"
echo ""

# Wait a moment for Flask to start
sleep 3

# Start frontend server
echo "🎨 Starting frontend server on port 8000..."
cd frontend
python3 -m http.server 8000 > /dev/null 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"
echo ""

echo "✅ Servers started!"
echo ""
echo "📚 Frontend: http://localhost:8000"
echo "🔌 Backend API: http://localhost:5001"
echo ""
echo "⚠️  Note: If you haven't ingested PDFs yet, run:"
echo "   python ingest.py"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
wait $FLASK_PID

