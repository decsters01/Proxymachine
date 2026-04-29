#!/bin/bash

echo "🚀 Starting Proxygenesis AI v2.0 - Enhanced Edition"
echo "=================================================="

# Create necessary directories
mkdir -p database ml_enhanced api utils models data

# Check if database exists, if not initialize
if [ ! -f "proxygenesis.db" ]; then
    echo "📦 Initializing database..."
    python3 -c "from database.db_manager import init_database; init_database()"
fi

# Install dependencies if needed
if ! python3 -c "import xgboost" 2>/dev/null; then
    echo "📦 Installing enhanced dependencies..."
    python3 -m pip install -r requirements.txt --quiet
fi

# Start the web server with API
echo "🌐 Starting web server on port 8000..."
echo "📖 API Documentation: http://localhost:8001/docs"
echo ""

# Run both servers (web UI + API)
python3 -c "
import asyncio
import uvicorn
from webapp.server import app as web_app
from api.server import app as api_app
import threading

def run_api():
    uvicorn.run(api_app, host='0.0.0.0', port=8001, log_level='info')

def run_web():
    uvicorn.run(web_app, host='0.0.0.0', port=8000, log_level='info')

print('✅ Starting Web UI on port 8000...')
print('✅ Starting API Server on port 8001...')
print('')
print('🌐 Web Interface: http://localhost:8000')
print('📖 API Docs: http://localhost:8001/docs')
print('')

# Start API in a separate thread
api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

# Run web server in main thread
run_web()
"
