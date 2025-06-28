#!/bin/bash

echo "🚀 Setting up FinWave development environment..."

# Check if backend is running
if ! curl -s http://localhost:8000/api/oauth/integrations > /dev/null; then
    echo "❌ Backend not running. Please start the FastAPI backend first."
    exit 1
fi

echo "✅ Backend is running"

# Call quick setup endpoint
echo "🔧 Setting up demo data..."
curl -X GET http://localhost:8000/api/oauth/dev/quick_setup

# Seed metrics data
echo "📊 Seeding financial data..."
curl -X POST "http://localhost:8000/api/templates/3statement/refresh?start_date=2024-01-01"

echo "✅ Setup complete!"
echo "🌐 Opening browser at http://localhost:3000"

# Open browser (works on macOS, Linux, and Windows)
if command -v open > /dev/null; then
    open http://localhost:3000
elif command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v start > /dev/null; then
    start http://localhost:3000
else
    echo "Please open http://localhost:3000 in your browser"
fi
