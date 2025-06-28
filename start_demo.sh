#!/bin/bash
# FinWave Demo Startup Script

set -e

echo "🚀 Starting FinWave Demo Environment"
echo "==================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the FinWave root directory"
    echo "   Expected directories: backend/ and frontend/"
    exit 1
fi

# Kill any existing processes on ports 3000 and 8000
echo "🧹 Cleaning up any existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start backend
echo "🔧 Starting backend API server..."
cd backend
source venv/bin/activate 2>/dev/null || {
    echo "⚠️  Virtual environment not found. Creating it..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
}

# Initialize database if needed
if [ ! -f "dev.duckdb" ]; then
    echo "🗄️  Initializing database..."
    python init_production.py
fi

# Start backend in background
uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/docs >/dev/null 2>&1; then
        echo "✅ Backend is running!"
        break
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..10}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend is running!"
        break
    elif curl -s http://localhost:3002 >/dev/null 2>&1; then
        echo "✅ Frontend is running on port 3002!"
        FRONTEND_PORT=3002
        break
    fi
    sleep 1
done

# Show success message
echo ""
echo "🎉 FinWave is ready!"
echo ""
echo "📱 Access the application at:"
echo "   Frontend: http://localhost:${FRONTEND_PORT:-3000}"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔐 OAuth Setup:"
echo "   1. Click 'Connect Data Source' in the UI"
echo "   2. Choose your integration (QuickBooks, Salesforce, etc.)"
echo "   3. Click 'Configure OAuth App'"
echo "   4. Enter your developer credentials"
echo "   5. Complete the OAuth flow"
echo ""
echo "📝 Logs:"
echo "   Backend: backend/backend.log"
echo "   Frontend: frontend/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Set up trap for Ctrl+C
trap cleanup INT

# Keep script running
wait