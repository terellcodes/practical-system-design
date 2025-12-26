"""
Lambda function to process S3 upload events and produce to Kafka.

This function is triggered by S3 when a file is uploaded to the chat-media bucket.
It extracts the message details from the S3 object key and produces a message
to the Kafka 'upload-completed' topic.

S3 Object Key Format:
    chats/{chat_id}/attachments/{message_id}/{unique_prefix}_{filename}

Example:
    chats/chat-abc123/attachments/msg-def456/a1b2c3d4_photo.jpg
"""

import json
import logging
import os
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Kafka configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'upload-completed')


def parse_s3_key(key: str) -> dict:
    """
    Parse S3 object key to extract chat_id and message_id.
    
    Args:
        key: S3 object key in format: chats/{chat_id}/attachments/{message_id}/{filename}
    
    Returns:
        dict with chat_id, message_id, filename
    
    Raises:
        ValueError if key format is invalid
    """
    # URL decode the key (S3 events URL-encode special characters)
    decoded_key = unquote_plus(key)
    
    parts = decoded_key.split('/')
    
    # Expected: ['chats', chat_id, 'attachments', message_id, filename]
    if len(parts) < 5 or parts[0] != 'chats' or parts[2] != 'attachments':
        raise ValueError(f"Invalid S3 key format: {key}")
    
    return {
        'chat_id': parts[1],
        'message_id': parts[3],
        'filename': parts[4] if len(parts) > 4 else None,
    }


def produce_to_kafka(message: dict) -> bool:
    """
    Produce a message to Kafka.
    
    Args:
        message: dict to serialize and send to Kafka
    
    Returns:
        bool indicating success
    """
    try:
        from kafka import KafkaProducer
        
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            # Short timeouts for Lambda
            request_timeout_ms=10000,
            api_version_auto_timeout_ms=5000,
        )
        
        future = producer.send(KAFKA_TOPIC, value=message)
        # Wait for send to complete (with timeout)
        record_metadata = future.get(timeout=10)
        
        logger.info(f"Message sent to Kafka topic {record_metadata.topic} "
                   f"partition {record_metadata.partition} offset {record_metadata.offset}")
        
        producer.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to produce to Kafka: {e}")
        return False


def handler(event, context):
    """
    Lambda handler for S3 upload events.
    
    Args:
        event: S3 event notification
        context: Lambda context
    
    Returns:
        dict with statusCode and body
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    processed = 0
    errors = []
    
    for record in event.get('Records', []):
        try:
            # Extract S3 details
            s3_info = record.get('s3', {})
            bucket = s3_info.get('bucket', {}).get('name')
            key = s3_info.get('object', {}).get('key')
            size = s3_info.get('object', {}).get('size', 0)
            event_name = record.get('eventName', '')
            
            logger.info(f"Processing: bucket={bucket}, key={key}, event={event_name}")
            
            if not bucket or not key:
                logger.warning(f"Missing bucket or key in record: {record}")
                continue
            
            # Parse the S3 key to extract message details
            try:
                parsed = parse_s3_key(key)
            except ValueError as e:
                logger.warning(f"Skipping non-attachment object: {e}")
                continue
            
            # Build Kafka message
            kafka_message = {
                'message_id': parsed['message_id'],
                'chat_id': parsed['chat_id'],
                's3_bucket': bucket,
                's3_key': key,
                'filename': parsed['filename'],
                'size': size,
                'event_type': 'upload_completed',
            }
            
            # Produce to Kafka
            if produce_to_kafka(kafka_message):
                processed += 1
                logger.info(f"Successfully processed upload for message {parsed['message_id']}")
            else:
                errors.append(f"Failed to produce to Kafka for {key}")
                
        except Exception as e:
            error_msg = f"Error processing record: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Return response
    response = {
        'statusCode': 200 if not errors else 207,  # 207 Multi-Status if partial success
        'body': json.dumps({
            'processed': processed,
            'errors': errors,
        })
    }
    
    logger.info(f"Handler complete: {response}")
    return response


# For local testing
if __name__ == '__main__':
    # Simulate S3 event
    test_event = {
        'Records': [{
            'eventName': 'ObjectCreated:Put',
            's3': {
                'bucket': {'name': 'chat-media'},
                'object': {
                    'key': 'chats/chat-abc123/attachments/msg-def456/a1b2c3d4_photo.jpg',
                    'size': 102400
                }
            }
        }]
    }
    
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
