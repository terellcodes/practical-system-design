"""
Chat Service - Data access layer
"""

from src.repositories.dynamodb import DynamoDBRepository

__all__ = [
    "DynamoDBRepository",
]
