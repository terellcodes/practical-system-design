"""
Shared database utilities

Provides connection factories for:
- PostgreSQL (via asyncpg)
- Redis (via redis-py)
- DynamoDB (via boto3)

Any service can use these to connect to any database.
"""

from common.database.postgres import (
    create_postgres_pool,
    PostgresConfig,
)

from common.database.redis import (
    create_redis_client,
    RedisConfig,
)

from common.database.dynamodb import (
    create_dynamodb_resource,
    DynamoDBConfig,
)

__all__ = [
    # PostgreSQL
    "create_postgres_pool",
    "PostgresConfig",
    # Redis
    "create_redis_client",
    "RedisConfig",
    # DynamoDB
    "create_dynamodb_resource",
    "DynamoDBConfig",
]

