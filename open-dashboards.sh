#!/bin/bash

# =============================================================================
# Open Admin Dashboards
# =============================================================================
# This script opens all three database admin dashboards in your default browser
#
# Dashboards:
#   - pgAdmin (PostgreSQL)      - http://localhost:5050
#   - Redis Commander (Redis)   - http://localhost:8081
#   - DynamoDB Admin (DynamoDB) - http://localhost:8082
# =============================================================================

set -e

echo "🚀 Opening Admin Dashboards..."
echo ""

# Check if Docker containers are running
echo "📋 Checking if dashboards are running..."
if ! docker ps | grep -q "pgadmin\|redis-commander\|dynamodb-admin"; then
    echo "⚠️  Warning: Some dashboard containers might not be running."
    echo "   Run 'docker-compose up -d' to start all services."
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🌐 Opening dashboards in your browser..."
echo ""

# Wait a moment for user to read
sleep 1

# Open all three dashboards
echo "   📊 Opening pgAdmin (PostgreSQL)..."
open http://localhost:5050

sleep 1

echo "   📊 Opening Redis Commander..."
open http://localhost:8081

sleep 1

echo "   📊 Opening DynamoDB Admin..."
open http://localhost:8082

echo ""
echo "✅ All dashboards opened!"
echo ""
echo "📚 Credentials & Info:"
echo "   ┌─────────────────────────────────────────────────────┐"
echo "   │ pgAdmin (http://localhost:5050)                     │"
echo "   │   Login: admin@admin.com / admin                    │"
echo "   │                                                       │"
echo "   │ Redis Commander (http://localhost:8081)             │"
echo "   │   No login required                                 │"
echo "   │                                                       │"
echo "   │ DynamoDB Admin (http://localhost:8082)              │"
echo "   │   No login required                                 │"
echo "   └─────────────────────────────────────────────────────┘"
echo ""
echo "💡 Tip: Bookmark these URLs for quick access!"
echo ""
echo "📖 See admin-dashboards-guide.md for detailed usage instructions."
echo ""

