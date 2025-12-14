#!/bin/bash

# Development startup script for MergeBlocker

echo "🚀 Starting MergeBlocker in development mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "❗ Please edit .env file with your configuration before running the app!"
    echo ""
    exit 1
fi

# Check if private key exists
if [ ! -f "private-key.pem" ]; then
    echo "⚠️  Warning: private-key.pem not found!"
    echo "Please generate and download your GitHub App private key."
    echo "Place it in the project root as 'private-key.pem'"
    echo ""
    exit 1
fi

# Set debug mode
export DEBUG=True

# Run the application
echo "✅ Starting Flask server..."
echo "🌐 Server will be available at http://localhost:8002"
echo "📡 Webhook endpoint: http://localhost:8002/webhook"
echo ""
echo "💡 Tip: Use ngrok to expose to the internet:"
echo "   ngrok http 8002"
echo ""

python app.py

