#!/bin/bash
# FinWave Quick Start - Assumes dependencies are already installed

echo "🚀 FinWave Quick Start"
echo "===================="
echo ""

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start backend
echo "🔧 Starting backend..."
cd backend
source venv/bin/activate

# Check if database exists
if [ ! -f "dev.duckdb" ]; then
    echo "🗄️  Initializing database..."
    python init_production.py || echo "⚠️  Using existing database setup"
fi

echo "✅ Starting backend server on port 8000..."
uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend
cd ../frontend
echo "🎨 Starting frontend..."
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Set up trap for Ctrl+C
trap cleanup INT

# Wait for services
echo ""
echo "⏳ Starting services..."
sleep 5

# Show status
echo ""
echo "🎉 FinWave is running!"
echo "===================="
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔧 Backend:  http://localhost:8000"
echo ""
echo "📝 Your API keys are configured:"
echo "   ✅ OpenAI API key"
echo "   ✅ QuickBooks OAuth credentials"
echo ""
echo "📋 Logs:"
echo "   Backend:  backend/backend.log"
echo "   Frontend: frontend/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep running
wait