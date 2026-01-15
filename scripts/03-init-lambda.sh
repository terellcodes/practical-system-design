#!/bin/bash
# Deploy Lambda function and configure S3 notifications in LocalStack

set -e

echo "🚀 Deploying upload-processor Lambda..."

LAMBDA_NAME="upload-processor"
WORK_DIR="/tmp/lambda-build"

# Wait for Lambda service to be ready
sleep 3

# Create working directory
rm -rf $WORK_DIR
mkdir -p $WORK_DIR

# Check if Lambda source exists
if [ ! -f "/lambda/upload-processor/handler.py" ]; then
    echo "❌ Lambda source not found at /lambda/upload-processor/handler.py"
    exit 1
fi

# Copy Lambda source
cp /lambda/upload-processor/handler.py $WORK_DIR/

# Install dependencies
echo "📦 Installing Lambda dependencies..."
pip install kafka-python -t $WORK_DIR --quiet

# Create deployment package
echo "📦 Creating deployment package..."
cd $WORK_DIR
zip -r9 /tmp/lambda.zip . > /dev/null

# Delete existing function if it exists
awslocal lambda delete-function --function-name $LAMBDA_NAME 2>/dev/null || true

# Create Lambda function
echo "☁️  Creating Lambda function..."
awslocal lambda create-function \
    --function-name $LAMBDA_NAME \
    --runtime python3.9 \
    --handler handler.handler \
    --zip-file fileb:///tmp/lambda.zip \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --timeout 30 \
    --memory-size 256 \
    --environment "Variables={KAFKA_BOOTSTRAP_SERVERS=kafka:29092,KAFKA_TOPIC=upload-completed}"

sleep 2

# Add permission for S3 to invoke Lambda
echo "🔐 Adding S3 invoke permission..."
awslocal lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id s3-trigger \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::chat-media \
    2>/dev/null || true

# Get Lambda ARN
LAMBDA_ARN=$(awslocal lambda get-function --function-name $LAMBDA_NAME --query 'Configuration.FunctionArn' --output text)

# Configure S3 bucket notification
echo "🔔 Configuring S3 bucket notifications..."
awslocal s3api put-bucket-notification-configuration \
    --bucket chat-media \
    --notification-configuration "{
        \"LambdaFunctionConfigurations\": [{
            \"Id\": \"upload-trigger\",
            \"LambdaFunctionArn\": \"$LAMBDA_ARN\",
            \"Events\": [\"s3:ObjectCreated:*\"],
            \"Filter\": {
                \"Key\": {
                    \"FilterRules\": [{
                        \"Name\": \"prefix\",
                        \"Value\": \"chats/\"
                    }]
                }
            }
        }]
    }"

echo "✅ Lambda deployment complete!"
echo "🎉 Upload processor ready - S3 → Lambda → Kafka"