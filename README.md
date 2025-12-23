# Practical System Design

A microservices-based distributed system for learning system design patterns.

## Architecture

```
                    ┌─────────────────────┐
                    │   NGINX Gateway     │
                    │      (Port 80)      │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    /api/users/*        /api/chats/*         /health
            │                  │
            ▼                  ▼
┌───────────────────┐  ┌───────────────────┐
│   User Service    │  │   Chat Service    │
│   (Port 8001)     │  │   (Port 8002)     │
│                   │  │                   │
│  imports common   │  │  imports common   │
└─────────┬─────────┘  └─────────┬─────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────┐
│           SHARED INFRASTRUCTURE             │
│  PostgreSQL:5432 │ Redis:6379 │ DynamoDB    │
└─────────────────────────────────────────────┘
```

## Key Design: Shared Common Package

The `common/` package contains shared code that any service can import:

```python
# Any service can import models
from common.models import User, Chat, ChatParticipant

# Any service can connect to any database
from common.database import (
    create_postgres_pool, PostgresConfig,
    create_redis_client, RedisConfig,
    create_dynamodb_resource, DynamoDBConfig,
)
```

**Benefits:**
- No code duplication across services
- Consistent models and types
- Any service can access any database
- Infrastructure is truly independent

## Project Structure

```
.
├── common/                         # Shared package (models + DB utilities)
│   ├── pyproject.toml
│   └── common/
│       ├── models/
│       │   ├── user.py             # User, UserCreate, UserUpdate
│       │   ├── chat.py             # Chat, ChatParticipant, etc.
│       │   └── responses.py        # MessageResponse, HealthResponse
│       └── database/
│           ├── postgres.py         # PostgresConfig, create_postgres_pool
│           ├── redis.py            # RedisConfig, create_redis_client
│           └── dynamodb.py         # DynamoDBConfig, create_dynamodb_resource
├── services/
│   ├── user-service/               # Uses: PostgreSQL, Redis
│   │   ├── Dockerfile
│   │   └── src/
│   └── chat-service/               # Uses: DynamoDB (could also use Redis)
│       ├── Dockerfile
│       └── src/
├── nginx/
│   └── nginx.conf                  # API Gateway routing
├── docker-compose.yml              # Infrastructure + Services
└── scripts/
    └── init-dynamodb.sh            # DynamoDB table creation
```

## Quick Start

```bash
# Start everything
docker-compose up --build

# Verify services are healthy
curl http://localhost/health

# Stop everything
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Testing the API

### Health Checks

```bash
# Gateway health
curl http://localhost/health | jq .

# User service health (via gateway)
curl http://localhost/api/users/health | jq .

# Chat service health (via gateway)
curl http://localhost/api/chats/health | jq .
```

### User Service (PostgreSQL + Redis Cache)

```bash
# Create users
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "alice@example.com"}'

curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Jones", "email": "bob@example.com"}'

# List all users
curl http://localhost/api/users | jq .

# Get single user (first request = cache miss, second = cache hit)
curl http://localhost/api/users/1 | jq .
curl http://localhost/api/users/1 | jq .  # Check logs for "CACHE HIT"

# Update user
curl -X PUT http://localhost/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated"}'

# Delete user
curl -X DELETE http://localhost/api/users/2
```

### Chat Service (DynamoDB)

```bash
# Create a chat
curl -X POST http://localhost/api/chats \
  -H "Content-Type: application/json" \
  -d '{"name": "Project Alpha", "metadata": {"type": "project"}}' | jq .

# Save the chat ID (or copy from output)
CHAT_ID="chat-XXXX"  # Replace with actual ID from above

# Get chat with participants
curl http://localhost/api/chats/$CHAT_ID | jq .

# Add participants to chat
curl -X POST http://localhost/api/chats/$CHAT_ID/participants \
  -H "Content-Type: application/json" \
  -d '{"participant_ids": ["user-1", "user-2", "user-3"]}'

# Get chat again (now with participants)
curl http://localhost/api/chats/$CHAT_ID | jq .

# Get all chats for a participant (uses GSI)
curl http://localhost/api/chats/participant/user-1 | jq .

# Remove a participant
curl -X DELETE http://localhost/api/chats/$CHAT_ID/participants/user-2

# Delete entire chat
curl -X DELETE http://localhost/api/chats/$CHAT_ID
```

### Observe Cache Behavior

```bash
# Watch the logs in real-time
docker-compose logs -f user-service

# In another terminal, make requests:
curl http://localhost/api/users/1  # First: "CACHE MISS"
curl http://localhost/api/users/1  # Second: "CACHE HIT"
```

## Direct Database Access

```bash
# PostgreSQL
docker exec -it postgres psql -U dapruser -d daprdb -c "SELECT * FROM users;"

# Redis - list all keys
docker exec -it redis redis-cli KEYS "*"

# Redis - get cached user
docker exec -it redis redis-cli GET "user:1"

# DynamoDB - scan Chats table
docker exec -it localstack awslocal dynamodb scan --table-name Chats

# DynamoDB - scan ChatParticipants table
docker exec -it localstack awslocal dynamodb scan --table-name ChatParticipants
```

## Infrastructure Access

All databases are shared resources. Any service can connect to any database:

| Resource | Internal URL | External Port |
|----------|--------------|---------------|
| PostgreSQL | `postgres:5432` | 5432 |
| Redis | `redis:6379` | 6379 |
| DynamoDB | `localstack:4566` | 4566 |

### Adding Redis to Chat Service (Example)

```python
# In chat-service/src/config.py
from common.database import RedisConfig

REDIS_CONFIG = RedisConfig.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/1")  # Use db 1 to separate from user-service
)
```

```yaml
# In docker-compose.yml, add to chat-service environment:
- REDIS_URL=redis://redis:6379/1
```

## System Design Patterns

### Cache-Aside (User Service)
```
GET /users/1
    ↓
[Check Redis] → HIT → Return cached
    ↓ MISS
[Query PostgreSQL]
    ↓
[Store in Redis with TTL]
    ↓
Return
```

### DynamoDB Data Model (Chat Service)

| Table | PK | SK | GSI |
|-------|----|----|-----|
| Chats | id | - | - |
| ChatParticipants | chatId | participantId | participantId-index |

The GSI enables "get all chats for user" queries without scanning.

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f user-service
docker-compose logs -f chat-service

# Restart a service
docker-compose restart user-service

# Rebuild a specific service
docker-compose build user-service
docker-compose up -d user-service

# Check service status
docker-compose ps
```

## Learning Objectives

1. **Shared Library Pattern** - Common code without microservice coupling
2. **Database Per Service** - Each service owns its data, but infrastructure is shared
3. **Cache-Aside Pattern** - Redis caching with TTL
4. **NoSQL Data Modeling** - DynamoDB keys, GSIs
5. **API Gateway** - NGINX routing, load balancing ready
6. **Docker Compose** - Multi-service orchestration
