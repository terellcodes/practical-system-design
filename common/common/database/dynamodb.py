"""
DynamoDB connection utilities

Usage:
    from common.database import create_dynamodb_resource, DynamoDBConfig
    
    config = DynamoDBConfig(
        endpoint_url="http://localstack:4566",
        region="us-east-1",
    )
    dynamodb = create_dynamodb_resource(config)
    table = dynamodb.Table("MyTable")
"""

import logging
from dataclasses import dataclass
from typing import Optional

import boto3

logger = logging.getLogger(__name__)


@dataclass
class DynamoDBConfig:
    """DynamoDB connection configuration"""
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None  # None = use AWS, set for LocalStack
    access_key_id: str = "test"
    secret_access_key: str = "test"
    
    @property
    def is_local(self) -> bool:
        """Check if using local endpoint (LocalStack)"""
        return self.endpoint_url is not None


def create_dynamodb_resource(config: DynamoDBConfig):
    """
    Create a DynamoDB resource.
    
    Args:
        config: DynamoDB configuration
        
    Returns:
        boto3 DynamoDB resource
        
    Example:
        dynamodb = create_dynamodb_resource(config)
        table = dynamodb.Table("Chats")
        table.put_item(Item={"id": "123", "name": "My Chat"})
    """
    if config.is_local:
        logger.info(f"Connecting to DynamoDB at {config.endpoint_url} (local mode)")
        return boto3.resource(
            'dynamodb',
            endpoint_url=config.endpoint_url,
            region_name=config.region,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
        )
    else:
        logger.info(f"Connecting to DynamoDB in region {config.region} (AWS mode)")
        # Production: uses IAM role/credentials automatically
        return boto3.resource('dynamodb', region_name=config.region)

