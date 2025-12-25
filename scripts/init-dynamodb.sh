#!/bin/bash
# Initialize DynamoDB tables in LocalStack
# This script runs automatically when LocalStack starts

echo "🚀 Initializing DynamoDB tables..."

# Wait for DynamoDB to be ready
sleep 2

# Create Chats table
echo "📦 Creating Chats table..."
awslocal dynamodb create-table \
    --table-name Chats \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null || echo "  ℹ️  Chats table already exists"

# Create ChatParticipants table with GSI
echo "📦 Creating ChatParticipants table with GSI..."
awslocal dynamodb create-table \
    --table-name ChatParticipants \
    --attribute-definitions \
        AttributeName=chatId,AttributeType=S \
        AttributeName=participantId,AttributeType=S \
    --key-schema \
        AttributeName=chatId,KeyType=HASH \
        AttributeName=participantId,KeyType=RANGE \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"participantId-index\",
                \"KeySchema\": [
                    {\"AttributeName\": \"participantId\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"chatId\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null || echo "  ℹ️  ChatParticipants table already exists"

echo "📦 Creating Messages table..."
awslocal dynamodb create-table \
    --table-name Messages \
    --attribute-definitions \
        AttributeName=chatId,AttributeType=S \
        AttributeName=createdAt,AttributeType=N \
    --key-schema \
        AttributeName=chatId,KeyType=HASH \
        AttributeName=createdAt,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null || echo "  ℹ️  Messages table already exists"

# Create Inbox table (user-centric message view)
echo "📦 Creating Inbox table..."
awslocal dynamodb create-table \
    --table-name Inbox \
    --attribute-definitions \
        AttributeName=recipientId,AttributeType=S \
        AttributeName=createdAt,AttributeType=N \
    --key-schema \
        AttributeName=recipientId,KeyType=HASH \
        AttributeName=createdAt,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null || echo "  ℹ️  Inbox table already exists"

# List tables to verify
echo ""
echo "✅ DynamoDB tables created:"
awslocal dynamodb list-tables

echo ""
echo "🎉 DynamoDB initialization complete!"

