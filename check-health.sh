#!/bin/bash

# Health check script for Magento CMS Sync Tool

echo "🔍 Checking Magento CMS Sync Tool Health..."
echo "=========================================="

# Function to check if a service is running
check_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "$expected" ]; then
        echo "✅ OK (HTTP $response)"
        return 0
    else
        echo "❌ Failed (HTTP $response)"
        return 1
    fi
}

# Check backend API
check_service "Backend API" "http://localhost:8000/docs" "200"
backend_status=$?

# Check frontend
check_service "Frontend" "http://localhost:3001/" "200"
frontend_status=$?

# Check API endpoints
echo ""
echo "📡 Checking API Endpoints..."
echo "----------------------------"

check_service "Instances API" "http://localhost:8000/api/instances/" "200"
check_service "History API" "http://localhost:8000/api/history/statistics" "200"

# Check database
echo ""
echo "💾 Checking Database..."
echo "----------------------"

if [ -f "backend/cmssync.db" ]; then
    size=$(du -h backend/cmssync.db | cut -f1)
    echo "✅ Database exists (Size: $size)"
else
    echo "❌ Database not found"
fi

# Check data directory
echo ""
echo "📁 Checking Data Storage..."
echo "-------------------------"

if [ -d "backend/data/instances" ]; then
    count=$(find backend/data/instances -type d -mindepth 1 | wc -l | tr -d ' ')
    echo "✅ Data directory exists ($count instance folders)"
else
    echo "❌ Data directory not found"
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="

if [ $backend_status -eq 0 ] && [ $frontend_status -eq 0 ]; then
    echo "✅ All services are running!"
    echo ""
    echo "🌐 Access the application at: http://localhost:3001"
    echo "📚 API documentation at: http://localhost:8000/docs"
else
    echo "⚠️  Some services are not running properly."
    echo ""
    echo "To start the services, run: ./start-dev.sh"
fi