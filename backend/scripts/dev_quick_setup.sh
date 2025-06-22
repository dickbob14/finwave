#!/usr/bin/env bash
# Quick setup script for FinWave demo environment

set -e  # Exit on error

echo "🚀 FinWave Quick Setup Starting..."

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found. Copy .env.example to .env and fill in credentials."
    exit 1
fi

# Check for required env vars
if [ -z "$QB_CLIENT_ID" ] || [ -z "$QB_CLIENT_SECRET" ]; then
    echo "❌ QuickBooks credentials not found in .env"
    echo "Please add QB_CLIENT_ID and QB_CLIENT_SECRET to your .env file"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Initialize database
echo "📊 Initializing database..."
make init-db

# Create demo workspace and sync QuickBooks data
echo "🏢 Creating demo workspace and syncing QuickBooks sandbox data..."
python backend/scripts/seed_demo.py

# Run all scheduler jobs to populate data
echo "⚡ Running initial data sync and calculations..."
make scheduler-all

# Start the backend API in the background
echo "🖥️  Starting backend API..."
cd backend && uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 5

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start the frontend
echo "🎨 Starting frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ FinWave is ready!"
echo ""
echo "🔗 Frontend: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "📧 Login: admin@demo.finwave.io"
echo "🔑 Password: password"
echo ""
echo "💡 The QuickBooks sandbox data for Craig's Design & Landscaping Services has been loaded."
echo "   Generate your first board report by clicking 'Generate Report' in the UI!"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait