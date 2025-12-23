# User Service - Distributed System with Dapr

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Dapr](https://img.shields.io/badge/Dapr-1.14+-purple.svg)](https://dapr.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

A production-ready FastAPI microservice demonstrating distributed state management using Dapr. This project implements a User CRUD API with **Cache-Aside** and **Write-Through** caching patterns using PostgreSQL as the primary data store and Redis for caching.

---

## 📚 Table of Contents

- [Features](#-features)
- [Important Notes](#-important-notes)
- [Architecture Overview](#architecture-overview)
- [Caching Patterns](#caching-patterns-implemented)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start-for-returning-users)
- [Full Setup Instructions](#full-setup-instructions-first-time)
- [API Endpoints](#api-endpoints)
- [Testing Examples](#testing-with-curl)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)

---

## 🚀 Features

- ✅ **RESTful API** - Full CRUD operations for user management
- ✅ **Distributed State Management** - PostgreSQL for persistence, Redis for caching
- ✅ **Dapr Integration** - Portable, cloud-native sidecar architecture
- ✅ **Smart Caching** - Cache-Aside pattern with automatic cache invalidation
- ✅ **Write-Through Pattern** - Consistent data between cache and database
- ✅ **Docker Compose** - One-command infrastructure setup
- ✅ **Clean Logs** - Startup script filters noisy Dapr warnings
- ✅ **No Port Conflicts** - Custom Redis on port 6380

## 📌 Important Notes

- **Service Port**: Application runs on **port 8001** (to avoid conflicts with other services)
- **Dapr Init**: Use `dapr init --slim` for cleanest setup (skips default Redis/Zipkin containers)
- **Redis Port**: Custom Redis runs on **port 6380** (standard Redis port 6379 mapped to host 6380)
- **Startup Script**: Use `./start.sh` to automatically filter out noisy placement/scheduler warnings
- **Quick Start**: See [Quick Start](#quick-start-for-returning-users) section below for fast setup

## Architecture Overview

This project demonstrates a **cloud-native microservice architecture** using Dapr to abstract infrastructure concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Service                             │
│                   (FastAPI + Dapr SDK)                          │
│                                                                  │
│  • Business logic focused on user management                     │
│  • No direct database/cache dependencies                         │
│  • Portable across cloud providers                              │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
            ┌─────────────────┐     ┌─────────────────┐
            │   Dapr Sidecar  │     │   Dapr Sidecar  │
            │  (State Store)  │     │    (Cache)      │
            └────────┬────────┘     └────────┬────────┘
                     │                       │
                     ▼                       ▼
            ┌─────────────────┐     ┌─────────────────┐
            │   PostgreSQL    │     │      Redis      │
            │  (Port 5432)    │     │   (Port 6380)   │
            └─────────────────┘     └─────────────────┘
```

**Key Benefits:**
- **Abstraction**: App code doesn't know about PostgreSQL or Redis
- **Portability**: Switch databases by changing component YAML files
- **Consistency**: Dapr provides unified state management API
- **Observability**: Built-in metrics, tracing, and logging

## Caching Patterns Implemented

### Cache-Aside Pattern (GET /users/{id})
1. Check Redis cache first
2. On cache miss, fetch from PostgreSQL
3. Populate cache with 1-hour TTL
4. Return data

### Write-Through Pattern (POST/PUT)
1. Save to PostgreSQL (primary store)
2. Update Redis cache
3. Return success

### Cache Invalidation (DELETE)
1. Delete from PostgreSQL
2. Remove from Redis cache

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Download Docker](https://www.docker.com/products/docker-desktop)
- **Dapr CLI** - [Install Dapr](https://docs.dapr.io/getting-started/install-dapr-cli/)

### Verify Installations

```bash
python3 --version   # Should be 3.9+
docker --version    # Should be 20.10+
dapr --version      # Should be 1.10+
```

## Project Structure

```
project/
├── app.py                  # FastAPI application with CRUD endpoints
├── start.sh                # Startup script (filters noisy logs)
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Infrastructure (PostgreSQL + Redis)
├── components/
│   ├── statestore.yaml     # Dapr PostgreSQL state store config
│   └── cache.yaml          # Dapr Redis cache config (port 6380)
└── README.md               # This file
```

## Quick Start (For Returning Users)

If you've already set up everything once, use these commands to get running quickly:

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Run the application (using the startup script)
./start.sh
```

**Or manually:**

```bash
source venv/bin/activate
dapr run \
  --app-id user-service \
  --app-port 8001 \
  --dapr-http-port 3500 \
  --resources-path ./components \
  -- python app.py 2>&1 | grep -v "Failed to connect to placement\|Failed to connect to scheduler"
```

Access the service at **http://localhost:8001**

---

## Full Setup Instructions (First Time)

### Step 1: Clone and Navigate to Project

```bash
cd /path/to/project
```

### Step 2: Create Python Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Dapr (First Time Only)

You have two options:

**Option A: Slim Install (Recommended)**
```bash
dapr init --slim
```
This skips Dapr's default Redis/Zipkin containers since we manage our own infrastructure.

**Option B: Standard Install**
```bash
dapr init
```
If you use this, you'll need to stop `dapr_redis` before running (see Step 6).

### Step 5: Start Infrastructure

```bash
docker-compose up -d
```

Verify containers are running:

```bash
docker ps | grep dapr
```

You should see:
- `dapr-postgres` running on port 5432
- `dapr-redis` running on port **6380** (host) → 6379 (container)

### Step 6: Run the Application

**Using the startup script (recommended):**
```bash
./start.sh
```
This automatically filters out noisy placement/scheduler warnings.

**Or run manually:**
```bash
source venv/bin/activate
dapr run \
  --app-id user-service \
  --app-port 8001 \
  --dapr-http-port 3500 \
  --resources-path ./components \
  -- python app.py 2>&1 | grep -v "Failed to connect to placement\|Failed to connect to scheduler"
```

**Note:** If you used **standard `dapr init`** (not slim), first stop the default Redis:
```bash
docker stop dapr_redis
```

The service will be available at:
- **API Endpoint**: http://localhost:8001
- **OpenAPI Docs**: http://localhost:8001/docs
- **Dapr Sidecar**: http://localhost:3500

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/users` | Create a new user |
| GET | `/users/{user_id}` | Get user by ID (cache-aside) |
| PUT | `/users/{user_id}` | Update user (write-through) |
| DELETE | `/users/{user_id}` | Delete user (cache invalidation) |

## Testing with cURL

### Health Check

```bash
curl -X GET http://localhost:8001/health
```

Expected Response:
```json
{
  "status": "healthy",
  "service": "user-service",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

### Create a User

```bash
curl -X POST http://localhost:8001/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com"
  }'
```

Expected Response:
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "created_at": "2024-01-15T10:30:00.000000"
}
```

### Create Another User

```bash
curl -X POST http://localhost:8001/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@example.com"
  }'
```

### Get a User (First request - Cache Miss)

```bash
curl -X GET http://localhost:8001/users/1
```

Check the application logs - you should see:
```
CACHE MISS: User 1 not in cache
User 1 found in state store
User 1 cached with TTL 3600s
```

### Get the Same User Again (Cache Hit)

```bash
curl -X GET http://localhost:8001/users/1
```

Check the application logs - you should see:
```
CACHE HIT: User 1 found in cache
```

### Update a User

```bash
curl -X PUT http://localhost:8001/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john.smith@example.com"
  }'
```

Expected Response:
```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john.smith@example.com",
  "created_at": "2024-01-15T10:30:00.000000"
}
```

### Partial Update (Only Email)

```bash
curl -X PUT http://localhost:8001/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new.email@example.com"
  }'
```

### Delete a User

```bash
curl -X DELETE http://localhost:8001/users/1
```

Expected Response:
```json
{
  "message": "User 1 deleted successfully",
  "user_id": 1
}
```

### Try to Get Deleted User (404)

```bash
curl -X GET http://localhost:8001/users/1
```

Expected Response:
```json
{
  "detail": "User with ID 1 not found"
}
```

## Common Commands

### Start Everything
```bash
# Start infrastructure
docker-compose up -d

# Start the application (filtered output)
./start.sh
```

### Check Service Status
```bash
# Health check
curl http://localhost:8001/health

# View running containers
docker ps | grep dapr

# Check Dapr status
dapr list
```

### View Logs
```bash
# Docker containers
docker-compose logs -f postgres
docker-compose logs -f redis

# Dapr logs (shown in terminal when running)
```

## Viewing the Dapr Dashboard

Launch the Dapr dashboard to monitor components and applications:

```bash
dapr dashboard
```

Open http://localhost:8080 in your browser to see:
- Running applications
- Component configurations
- Service invocation metrics

## Verify Cache Behavior

### Check Redis Cache Directly

```bash
# Connect to Redis
docker exec -it dapr-redis redis-cli

# List all keys
KEYS *

# Get a specific user (replace with actual key)
GET "user-service||user-1"

# Exit Redis CLI
exit
```

### Check PostgreSQL State Store

```bash
# Connect to PostgreSQL
docker exec -it dapr-postgres psql -U dapruser -d daprdb

# List tables
\dt

# View state store data
SELECT * FROM state;

# Exit PostgreSQL
\q
```

## Configuration

### Environment Variables

You can customize the PostgreSQL connection via environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | dapruser | PostgreSQL username |
| `POSTGRES_PASSWORD` | daprpassword | PostgreSQL password |
| `POSTGRES_DB` | daprdb | Database name |

### Redis Port Configuration

This project uses a custom Redis instance on **port 6380** (host) which maps to port 6379 inside the container.

**Current Configuration:**
- `docker-compose.yml`: Maps host port 6380 → container port 6379
- `components/cache.yaml`: Connects to `localhost:6380`
- This avoids conflicts with any services using the standard Redis port (6379)

**To change the Redis port:**
1. Update `docker-compose.yml`:
   ```yaml
   ports:
     - "YOUR_PORT:6379"
   ```
2. Update `components/cache.yaml`:
   ```yaml
   - name: redisHost
     value: "localhost:YOUR_PORT"
   ```
3. Restart: `docker-compose down && docker-compose up -d`

### Cache TTL

The cache TTL is set to 1 hour (3600 seconds). To modify, update `CACHE_TTL_SECONDS` in `app.py`:

```python
CACHE_TTL_SECONDS = 3600  # 1 hour
```

## Troubleshooting

### Issue: Noisy placement/scheduler warnings

**Problem**: You see repeated errors like:
```
Failed to connect to placement localhost:50005
Failed to connect to scheduler localhost:50006
```

**Explanation**: These are harmless. Dapr tries to connect to placement (for actors) and scheduler services, but we don't use those features.

**Solution**: Use the provided startup script that filters these messages:
```bash
./start.sh
```

Or add the grep filter manually:
```bash
dapr run ... -- python app.py 2>&1 | grep -v "Failed to connect to placement\|Failed to connect to scheduler"
```

### Issue: Dapr components not loading

**Solution**: Ensure the components directory path is correct. Note: `--components-path` is deprecated, use `--resources-path`:
```bash
dapr run --resources-path ./components ...
```

### Issue: Cannot connect to PostgreSQL/Redis

**Solution**: Verify Docker containers are running:
```bash
docker-compose ps
docker-compose logs postgres
docker-compose logs redis
```

Check if containers are healthy:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep dapr
```

### Issue: Port 8001 already in use

**Solution**: Stop existing services or use different ports:
```bash
# Check what's using port 8001
lsof -i :8001

# Kill the process if needed
kill -9 <PID>

# Or run on a different port (update app.py accordingly)
dapr run --app-port 8002 ... -- python app.py
```

### Issue: Dapr not initialized

**Solution**: Initialize Dapr:
```bash
dapr init --slim  # Recommended for this project
# OR
dapr init         # Standard install (requires stopping dapr_redis)
```

### Issue: Zipkin connection refused warnings

**Message**: `request to http://localhost:9411/api/v2/spans failed: connection refused`

**Explanation**: This is normal! Dapr tries to send traces to Zipkin (a distributed tracing tool) but we haven't set it up. This warning doesn't affect functionality.

**Solution (optional)**: To eliminate the warning, either:
1. Ignore it (recommended for development)
2. Start Zipkin: `docker start dapr_zipkin`
3. Disable tracing in Dapr configuration

### View Application Logs

When running with `dapr run`, logs are streamed to the console. Look for:
- `CACHE HIT` - Data found in Redis (fast path)
- `CACHE MISS` - Data not in Redis, fetched from PostgreSQL
- `User X saved to state store` - Write-through pattern
- `User X cached with TTL 3600s` - Cache population
- Error messages for debugging

## Cleanup

### Stop the Application

Press `Ctrl+C` in the terminal running the Dapr application.

### Stop Infrastructure

```bash
# Stop your custom containers
docker-compose down

# If you stopped dapr_redis earlier, you can restart it
docker start dapr_redis 2>/dev/null || true
```

### Remove Volumes (Full Cleanup)

⚠️ **Warning**: This will delete all data in PostgreSQL and Redis!

```bash
docker-compose down -v
```

### Uninstall Dapr (if needed)

```bash
# Remove all Dapr containers and binaries
dapr uninstall --all

# Or just remove containers, keep binaries
dapr uninstall
```

## What You'll Learn

This project demonstrates key **System Design** and **Distributed Systems** concepts:

### 1. **Caching Strategies**
- **Cache-Aside Pattern**: Application checks cache first, falls back to database
- **Write-Through Pattern**: Writes go to both database and cache simultaneously
- **Cache Invalidation**: Removing stale data when updates occur

### 2. **State Management**
- **Persistent State**: PostgreSQL for durable, consistent data storage
- **Ephemeral State**: Redis for fast, temporary data with TTL
- **State Abstraction**: Using Dapr SDK to decouple application from infrastructure

### 3. **Microservices Architecture**
- **Sidecar Pattern**: Dapr runs alongside your app, handling cross-cutting concerns
- **Service Mesh Concepts**: Observability, state management, and service-to-service communication
- **Polyglot Support**: Dapr works with any language (Python, Go, Java, .NET, etc.)

### 4. **Infrastructure as Code**
- **Docker Compose**: Declarative infrastructure setup
- **Component-Based Configuration**: Swappable data stores via YAML
- **Environment Isolation**: Local development mirrors production topology

### 5. **Operational Excellence**
- **Health Checks**: `/health` endpoint for monitoring
- **Structured Logging**: Application and infrastructure logs
- **Graceful Degradation**: Cache failures don't crash the app

### 6. **Performance Optimization**
- **Read Optimization**: Redis cache reduces database load
- **Write Optimization**: Async operations where possible
- **TTL Strategy**: Automatic cache expiration prevents stale data

---

## Production Considerations

For production deployments, consider:

1. **Secrets Management**: Use Dapr secret stores for database credentials
2. **TLS/SSL**: Enable SSL for PostgreSQL and Redis connections
3. **Monitoring**: Add Prometheus metrics and distributed tracing with Zipkin/Jaeger
4. **Rate Limiting**: Implement rate limiting middleware
5. **Authentication**: Add JWT or API key authentication
6. **High Availability**: Run multiple replicas with load balancing
7. **Kubernetes**: Deploy on Kubernetes with Dapr sidecar injection
8. **Circuit Breakers**: Add resilience patterns for external dependencies
9. **Backup Strategy**: Automated PostgreSQL backups and Redis snapshots
10. **APM**: Application Performance Monitoring with tools like DataDog or New Relic

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║               User Service - Quick Reference                  ║
╠══════════════════════════════════════════════════════════════╣
║ START:      docker-compose up -d && ./start.sh              ║
║ STOP:       Ctrl+C, then: docker-compose down               ║
║ HEALTH:     curl http://localhost:8001/health               ║
║ API DOCS:   http://localhost:8001/docs                      ║
║                                                              ║
║ PORTS:                                                       ║
║   8001 - FastAPI Application                                ║
║   3500 - Dapr HTTP API                                      ║
║   5432 - PostgreSQL                                         ║
║   6380 - Redis Cache                                        ║
║                                                              ║
║ COMPONENTS:                                                  ║
║   • statestore.yaml - PostgreSQL config                     ║
║   • cache.yaml      - Redis config (port 6380)             ║
║                                                              ║
║ DEBUG:                                                       ║
║   • Check containers: docker ps | grep dapr                 ║
║   • View logs:        docker-compose logs -f                ║
║   • Dapr status:      dapr list                            ║
║   • Redis data:       docker exec dapr-redis redis-cli     ║
║   • Postgres data:    docker exec -it dapr-postgres psql    ║
╚══════════════════════════════════════════════════════════════╝
```

---

## License

MIT License - Feel free to use this for learning and production.

---

**Built with ❤️ using FastAPI, Dapr, PostgreSQL, and Redis**

