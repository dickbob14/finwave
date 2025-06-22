#!/bin/bash
# Setup script for Templates UI

echo "🎨 Setting up Templates UI"
echo "========================"

# Install required dependencies
echo "📦 Installing dependencies..."
npm install react-hot-toast date-fns

# Create environment file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local"
    cat > .env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Add authentication token
# NEXT_PUBLIC_API_TOKEN=your_token_here
EOF
    echo "✅ Created .env.local"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To run the frontend:"
echo "   npm run dev"
echo ""
echo "📋 The templates page will be available at:"
echo "   http://localhost:3000/templates"
echo ""
echo "⚠️  Make sure the backend is running:"
echo "   cd ../backend && uvicorn app.main:app --reload"