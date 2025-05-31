#!/bin/bash

# Start the backend
echo "Starting backend..."
cd backend
./venv/bin/python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start the frontend
echo "Starting frontend..."
cd ../frontend
PORT=3001 npm start &
FRONTEND_PID=$!

# Function to handle cleanup
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Set up trap to handle Ctrl+C
trap cleanup INT

# Wait for both processes
wait $BACKEND_PID
wait $FRONTEND_PID