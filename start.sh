#!/bin/bash

# Start User Service with Dapr
# This script filters out noisy placement/scheduler warnings

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 Starting User Service with Dapr..."
echo "📍 App Port: 8001"
echo "📍 Dapr HTTP Port: 3500"
echo "📍 Redis Port: 6380"
echo "📍 PostgreSQL Port: 5432"
echo ""

dapr run \
  --app-id user-service \
  --app-port 8001 \
  --dapr-http-port 3500 \
  --resources-path ./components \
  -- python app.py 2>&1 | grep -v "Failed to connect to placement\|Failed to connect to scheduler\|Connected to placement"

