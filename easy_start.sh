#!/bin/bash
# FinWave Easy Startup Script
# This script handles all setup and starts both backend and frontend

set -e

echo "🚀 FinWave Easy Startup"
echo "======================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Setup backend
echo "🔧 Setting up backend..."
cd backend

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    
    # Check if we have the template
    if [ -f .enc ]; then
        cp .enc .env
    elif [ -f env.example ]; then
        cp env.example .env
    else
        echo -e "${RED}❌ No environment template found${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}⚠️  Please configure your API keys:${NC}"
    echo ""
    echo "Your .env file needs the following:"
    echo "1. OPENAI_API_KEY - Required for AI features"
    echo "2. QB_CLIENT_ID - Optional for QuickBooks integration"
    echo "3. QB_CLIENT_SECRET - Optional for QuickBooks integration"
    echo ""
    
    # Check if user wants to add keys now
    read -p "Do you want to add your OpenAI API key now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your OpenAI API key (starts with sk-): " openai_key
        if [[ $openai_key == sk-* ]]; then
            # Update the .env file
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
            else
                # Linux
                sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
            fi
            echo -e "${GREEN}✅ OpenAI API key added${NC}"
        else
            echo -e "${YELLOW}⚠️  Invalid API key format. Please add it manually to backend/.env${NC}"
        fi
    fi
    
    # Ask about QuickBooks
    read -p "Do you have QuickBooks OAuth credentials? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter QB_CLIENT_ID: " qb_client_id
        read -p "Enter QB_CLIENT_SECRET: " qb_client_secret
        
        # Update the .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/QB_CLIENT_ID=.*/QB_CLIENT_ID=$qb_client_id/" .env
            sed -i '' "s/QB_CLIENT_SECRET=.*/QB_CLIENT_SECRET=$qb_client_secret/" .env
        else
            # Linux
            sed -i "s/QB_CLIENT_ID=.*/QB_CLIENT_ID=$qb_client_id/" .env
            sed -i "s/QB_CLIENT_SECRET=.*/QB_CLIENT_SECRET=$qb_client_secret/" .env
        fi
        echo -e "${GREEN}✅ QuickBooks credentials added${NC}"
    fi
fi

# Generate security keys if needed
echo "🔐 Checking security keys..."
if grep -q "FERNET_SECRET=generate_me" .env 2>/dev/null; then
    echo "Generating FERNET_SECRET..."
    fernet_key=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/FERNET_SECRET=.*/FERNET_SECRET=$fernet_key/" .env
    else
        sed -i "s/FERNET_SECRET=.*/FERNET_SECRET=$fernet_key/" .env
    fi
fi

if grep -q "JWT_SECRET=your-super-secret" .env 2>/dev/null; then
    echo "Generating JWT_SECRET..."
    jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$jwt_secret/" .env
    else
        sed -i "s/JWT_SECRET=.*/JWT_SECRET=$jwt_secret/" .env
    fi
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt -q

# Initialize database
if [ ! -f "dev.duckdb" ]; then
    echo "🗄️  Initializing database..."
    python init_production.py || python init_db_simple.py || echo -e "${YELLOW}⚠️  Database initialization skipped${NC}"
fi

# Kill any existing backend process
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start backend
echo -e "${GREEN}✅ Starting backend server...${NC}"
uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Move to frontend
cd ../frontend

# Install frontend dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Kill any existing frontend process
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start frontend
echo -e "${GREEN}✅ Starting frontend...${NC}"
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
backend_status="❌"
frontend_status="❌"

if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    backend_status="✅"
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
    frontend_status="✅"
fi

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

# Show final status
echo ""
echo "🎉 FinWave Status"
echo "================="
echo ""
echo "Backend API: $backend_status http://localhost:8000"
echo "Frontend UI: $frontend_status http://localhost:3000"
echo "API Docs:    http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  backend/backend.log"
echo "   Frontend: frontend/frontend.log"
echo ""

# Check .env status
if grep -q "OPENAI_API_KEY=$" backend/.env 2>/dev/null || grep -q "OPENAI_API_KEY= *$" backend/.env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: OPENAI_API_KEY is not set in backend/.env${NC}"
    echo "   AI features will not work without it."
fi

echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait