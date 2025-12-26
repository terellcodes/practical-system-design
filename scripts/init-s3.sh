#!/bin/bash
# Initialize S3 buckets in LocalStack
# This script runs automatically when LocalStack starts

echo "🚀 Initializing S3 buckets..."

# Wait for S3 to be ready
sleep 2

# Create chat-media bucket for file uploads
echo "📦 Creating chat-media bucket..."
awslocal s3 mb s3://chat-media 2>/dev/null || echo "  ℹ️  chat-media bucket already exists"

# Configure CORS for the bucket (allows browser uploads)
echo "🔧 Configuring CORS for chat-media bucket..."
awslocal s3api put-bucket-cors --bucket chat-media --cors-configuration '{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}'

# List buckets to verify
echo ""
echo "✅ S3 buckets created:"
awslocal s3 ls

echo ""
echo "🎉 S3 initialization complete!"
