"""
S3 storage utilities for generating pre-signed URLs.

Pre-signed URLs allow clients to upload/download files directly to/from S3
without needing AWS credentials. This is the standard pattern for handling
file uploads in web applications.

Key Concepts for System Design:
- Pre-signed URLs have an expiration time (default: 1 hour for uploads)
- Client uploads directly to S3, reducing server load
- S3 events can trigger downstream processing (Lambda, SNS, etc.)
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class S3Config:
    """Configuration for S3 client"""
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None  # For LocalStack: http://localstack:4566
    access_key_id: str = "test"
    secret_access_key: str = "test"
    bucket_name: str = "chat-media"


def create_s3_client(config: S3Config):
    """
    Create a boto3 S3 client with the given configuration.
    
    Args:
        config: S3Config with connection details
    
    Returns:
        boto3 S3 client
    """
    client_config = Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}  # Required for LocalStack
    )
    
    return boto3.client(
        's3',
        region_name=config.region,
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        config=client_config
    )


def generate_s3_object_key(
    chat_id: str,
    message_id: str,
    filename: str,
    content_type: Optional[str] = None
) -> str:
    """
    Generate a unique S3 object key for an upload.
    
    Format: chats/{chat_id}/attachments/{message_id}/{uuid}_{filename}
    
    This structure allows:
    - Easy cleanup of all attachments for a chat
    - Unique keys even if same filename is uploaded multiple times
    - Preserving original filename for downloads
    
    Args:
        chat_id: The chat this attachment belongs to
        message_id: The message this attachment belongs to
        filename: Original filename
        content_type: Optional MIME type (not used in key, but could be)
    
    Returns:
        S3 object key string
    """
    # Generate a short unique prefix to avoid collisions
    unique_prefix = uuid.uuid4().hex[:8]
    
    # Sanitize filename (remove path separators, limit length)
    safe_filename = filename.replace('/', '_').replace('\\', '_')
    if len(safe_filename) > 100:
        # Keep extension if present
        parts = safe_filename.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            safe_filename = f"{name[:90]}.{ext}"
        else:
            safe_filename = safe_filename[:100]
    
    return f"chats/{chat_id}/attachments/{message_id}/{unique_prefix}_{safe_filename}"


def generate_presigned_upload_url(
    s3_client,
    bucket: str,
    object_key: str,
    content_type: str,
    expiration: int = 3600,  # 1 hour default
) -> Optional[str]:
    """
    Generate a pre-signed URL for uploading a file to S3.
    
    The client can use this URL to PUT a file directly to S3.
    
    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        object_key: The key (path) where the file will be stored
        content_type: MIME type of the file (e.g., "image/jpeg")
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Pre-signed URL string, or None if generation failed
    
    Example usage by client:
        PUT {presigned_url}
        Content-Type: image/jpeg
        Body: <file bytes>
    """
    try:
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': object_key,
                'ContentType': content_type,
            },
            ExpiresIn=expiration,
        )
        logger.info(f"Generated presigned upload URL for {bucket}/{object_key}")
        return url
    except ClientError as e:
        logger.error(f"Failed to generate presigned upload URL: {e}")
        return None


def generate_presigned_download_url(
    s3_client,
    bucket: str,
    object_key: str,
    expiration: int = 3600,  # 1 hour default
    filename: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a pre-signed URL for downloading a file from S3.
    
    The client can use this URL to GET the file directly from S3.
    
    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        object_key: The key (path) of the file to download
        expiration: URL expiration time in seconds (default: 1 hour)
        filename: Optional filename for Content-Disposition header
    
    Returns:
        Pre-signed URL string, or None if generation failed
    """
    try:
        params = {
            'Bucket': bucket,
            'Key': object_key,
        }
        
        # Set Content-Disposition to prompt download with original filename
        if filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=expiration,
        )
        logger.info(f"Generated presigned download URL for {bucket}/{object_key}")
        return url
    except ClientError as e:
        logger.error(f"Failed to generate presigned download URL: {e}")
        return None
