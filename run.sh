#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n🛑 Shutting down Streaming RAG Pro services..."
    
    # Kill the backend process if it's running
    if [ -n "$BACKEND_PID" ]; then
        echo "Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill the frontend process if it's running
    if [ -n "$FRONTEND_PID" ]; then
        echo "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop docker containers
    echo "Stopping Docker containers..."
    docker-compose -f docker/docker-compose.yml stop
    
    echo "✅ Shutdown complete."
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM to run the cleanup function
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Streaming RAG Pro..."
echo "==================================="

# 1. Start Infrastructure (Docker)
echo -e "\n📦 [1/3] Starting Infrastructure (Qdrant & Redis)..."
docker-compose -f docker/docker-compose.yml up -d

# 2. Setup and Start Backend
echo -e "\n🐍 [2/3] Initializing Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment (handles both Windows/Git Bash and Unix paths)
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "Installing/Verifying backend dependencies..."
pip install -r requirements.txt -q

echo "Starting FastAPI Backend..."
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2
cd ..

# 3. Setup and Start Frontend
echo -e "\n⚛️ [3/3] Initializing Frontend..."
cd frontend

# Install node modules if they don't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (this may take a moment)..."
    npm install --silent
fi

echo "Starting Next.js Frontend..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo -e "\n==================================="
echo -e "✅ All services are booting up!"
echo -e "🌐 Frontend interface: http://localhost:3000"
echo -e "🔌 Backend API: http://localhost:8000"
echo -e "📡 Live Ingestion is running in the background."
echo -e "==================================="
echo -e "Press [Ctrl+C] to gracefully stop all services."

# Keep script running to maintain the trap and processes
wait $BACKEND_PID $FRONTEND_PID
