# Phase 1: PostgreSQL Horizontal Scaling - Read Replicas + Connection Pooling

## Overview

Phase 1 implements **read replicas** with **connection pooling** to horizontally scale PostgreSQL reads. This allows you to:
- Distribute read queries across multiple PostgreSQL instances
- Handle more concurrent read operations
- Improve read performance and reduce load on the primary database
- Maintain a single source of truth for writes

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Application Layer               │
│  (Read/Write Router Logic)          │
└──────┬───────────────────┬───────────┘
       │                   │
       │ Writes            │ Reads
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│   Primary    │    │   PgBouncer  │
│  PostgreSQL  │◄───┤  (Pooler)    │
│  (Master)    │    └──────┬───────┘
└──────────────┘           │
       │                   │
       │ Streaming         │ Load Balanced
       │ Replication       │ Reads
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│   Replica 1  │    │   Replica 2  │
│  PostgreSQL  │    │  PostgreSQL  │
│  (Read-Only) │    │  (Read-Only) │
└──────────────┘    └──────────────┘
```

## Components Required

### 1. PostgreSQL Primary (Master)
- Handles all write operations (INSERT, UPDATE, DELETE)
- Streams changes to replicas via WAL (Write-Ahead Logging)
- Current setup already has this

### 2. PostgreSQL Read Replicas (Standbys)
- Receive replicated data from primary
- Handle read-only queries (SELECT)
- Can have multiple replicas for load distribution
- Automatically sync via streaming replication

### 3. Connection Pooler (PgBouncer or PgPool-II)
- **PgBouncer**: Lightweight, transaction-level pooling
- **PgPool-II**: More features, includes load balancing and query routing
- Manages connection pools to reduce overhead
- Routes reads to replicas, writes to primary

### 4. Application Changes
- Read/Write splitting logic
- Connection pool management for primary vs replicas
- Health checks and failover handling

## Simplified Approaches: Using Libraries & Tools

### Option A: Use PgPool-II (Recommended - Minimal Code Changes)

**PgPool-II** handles all connection management automatically. Your application connects to a single endpoint, and PgPool-II routes:
- Writes → Primary
- Reads → Replicas (with load balancing)

**Advantages:**
- ✅ No application code changes needed
- ✅ Automatic read/write splitting
- ✅ Built-in load balancing
- ✅ Connection pooling
- ✅ Health checks and failover

**Your application code stays the same:**
```python
# No changes needed! Just connect to pgpool instead of postgres
DATABASE_URL=postgresql://dapruser:daprpassword@pgpool:5432/daprdb
```

**Setup:** See Step 1.4 below for PgPool-II configuration.

### Option B: Use PgCat (Modern Alternative)

**PgCat** is a newer connection pooler with similar features to PgPool-II:

- ✅ Automatic read/write splitting
- ✅ Sharding support
- ✅ Better performance for high concurrency
- ✅ RESTful admin API

**Setup:**
```yaml
pgcat:
  image: postgresml/pgcat:latest
  container_name: pgcat
  environment:
    PGCAT_CONFIG: |
      [databases.postgres]
      host = "postgres-primary"
      port = 5432
      database = "daprdb"
      user = "dapruser"
      password = "daprpassword"
      
      [pools.postgres]
      database = "postgres"
      pool_size = 25
      pool_mode = "transaction"
      
      [sharding]
      shards = [
        {host = "postgres-primary", port = 5432, weight = 0},  # Primary
        {host = "postgres-replica-1", port = 5432, weight = 1}, # Replica 1
        {host = "postgres-replica-2", port = 5432, weight = 1}, # Replica 2
      ]
  ports:
    - "6432:6432"
```

### Option C: Use SQLAlchemy with Async Support

If you're using **SQLAlchemy** (with `databases` library or `asyncpg`), you can use SQLAlchemy's built-in read/write splitting:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Primary (writes)
write_engine = create_async_engine(
    "postgresql+asyncpg://dapruser:daprpassword@postgres-primary:5432/daprdb"
)

# Replicas (reads) - SQLAlchemy can handle multiple URLs
read_engine = create_async_engine(
    "postgresql+asyncpg://dapruser:daprpassword@postgres-replica-1:5432/daprdb",
    # Can specify multiple replicas
)

# Use bind parameter in queries to route
async with AsyncSession(write_engine) as session:
    # Write operation
    session.add(user)
    await session.commit()

async with AsyncSession(read_engine) as session:
    # Read operation
    result = await session.query(User).filter(User.id == user_id).first()
```

**Note:** This still requires manual routing in your code, but SQLAlchemy handles connection pooling.

## Scaling Replicas: Docker Compose Options

### Option 1: Docker Compose with Swarm Mode (Recommended for Production-like Setup)

Docker Swarm allows you to specify replica counts directly:

```yaml
version: '3.8'

services:
  postgres-primary:
    image: postgres:15
    # ... primary config ...
    
  postgres-replica:
    image: postgres:15
    deploy:
      replicas: 3  # Just specify the number!
    environment:
      POSTGRES_USER: dapruser
      POSTGRES_PASSWORD: daprpassword
      POSTGRES_DB: daprdb
    # ... replica config ...
```

**To use Swarm mode:**
```bash
docker swarm init
docker stack deploy -c docker-compose.yml postgres-cluster
```

**Limitations:** Each replica needs unique configuration (replication slots, etc.), so you'll still need initialization scripts that handle dynamic replica setup.

### Option 2: Script-Based Dynamic Replica Generation

Create a script that generates docker-compose.yml with N replicas:

**Create `scripts/generate-replicas.sh`:**
```bash
#!/bin/bash
REPLICA_COUNT=${1:-2}  # Default to 2 replicas

cat > docker-compose.replicas.yml <<EOF
services:
  postgres-primary:
    # ... primary config ...
  
EOF

for i in $(seq 1 $REPLICA_COUNT); do
  cat >> docker-compose.replicas.yml <<EOF
  postgres-replica-${i}:
    image: postgres:15
    container_name: postgres-replica-${i}
    environment:
      POSTGRES_USER: dapruser
      POSTGRES_PASSWORD: daprpassword
      POSTGRES_DB: daprdb
      REPLICA_NUMBER: ${i}
    volumes:
      - postgres_replica${i}_data:/var/lib/postgresql/data
      - ./scripts/postgres-replica-init.sh:/docker-entrypoint-initdb.d/init-replica.sh
    # ... rest of config ...
    
EOF
done

echo "Generated docker-compose.replicas.yml with $REPLICA_COUNT replicas"
```

**Usage:**
```bash
./scripts/generate-replicas.sh 5  # Generate 5 replicas
docker-compose -f docker-compose.replicas.yml up -d
```

### Option 3: Use Environment Variable for Replica Count

Use a template approach with `envsubst`:

**docker-compose.template.yml:**
```yaml
services:
  postgres-primary:
    # ... config ...
    
  # This will be expanded by envsubst
  postgres-replica-%REPLICA_NUM%:
    image: postgres:15
    # ... config ...
```

**Generate with:**
```bash
export REPLICA_COUNT=3
for i in $(seq 1 $REPLICA_COUNT); do
  export REPLICA_NUM=$i
  envsubst < docker-compose.template.yml >> docker-compose.generated.yml
done
```

## Production Deployment Patterns

### Pattern 1: Managed Database Services (Easiest)

**AWS RDS PostgreSQL:**
```bash
# Just specify replica count - AWS handles everything!
aws rds create-db-instance-read-replica \
  --db-instance-identifier myapp-replica-1 \
  --source-db-instance-identifier myapp-primary \
  --db-instance-class db.t3.medium

# Or use Terraform
resource "aws_db_instance" "replica" {
  count              = var.replica_count  # Just set this!
  identifier         = "myapp-replica-${count.index + 1}"
  replicate_source_db = aws_db_instance.primary.id
  instance_class     = "db.t3.medium"
}
```

**Google Cloud SQL:**
```bash
gcloud sql instances create myapp-replica-1 \
  --master-instance-name=myapp-primary \
  --replica-type=READ
```

**Azure Database:**
```bash
az postgres flexible-server replica create \
  --replica-name myapp-replica-1 \
  --resource-group mygroup \
  --source-server myapp-primary
```

**Benefits:**
- ✅ Just specify replica count
- ✅ Automatic replication setup
- ✅ Automatic backups
- ✅ Monitoring and alerts
- ✅ Easy scaling up/down

### Pattern 2: Kubernetes with StatefulSets

**Kubernetes StatefulSet** allows you to specify replica count and handles initialization:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-replica
spec:
  serviceName: postgres-replica
  replicas: 3  # Just specify the number!
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: REPLICA_NUMBER
          valueFrom:
            fieldRef:
              fieldPath: metadata.name  # Gets postgres-replica-0, -1, -2
        - name: PRIMARY_HOST
          value: postgres-primary
        # Init container handles replication setup
        initContainers:
        - name: init-replica
          image: postgres:15
          command:
          - /bin/bash
          - /scripts/init-replica.sh
          env:
          - name: REPLICA_NUMBER
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
```

**Scaling:**
```bash
kubectl scale statefulset postgres-replica --replicas=5
# Kubernetes handles creating new replicas automatically!
```

### Pattern 3: Terraform + Custom Scripts

**Terraform** can provision infrastructure and call scripts:

```hcl
variable "replica_count" {
  description = "Number of PostgreSQL read replicas"
  type        = number
  default     = 2
}

resource "docker_container" "postgres_replica" {
  count = var.replica_count
  
  name  = "postgres-replica-${count.index + 1}"
  image = docker_image.postgres.image_id
  
  env = [
    "POSTGRES_USER=dapruser",
    "POSTGRES_PASSWORD=daprpassword",
    "REPLICA_NUMBER=${count.index + 1}",
  ]
  
  # Provisioner runs script to set up replication
  provisioner "local-exec" {
    command = "./scripts/setup-replica.sh ${count.index + 1}"
  }
}
```

**Usage:**
```bash
terraform apply -var="replica_count=5"
```

### Pattern 4: Patroni (High Availability + Auto-Scaling)

**Patroni** manages PostgreSQL clusters with automatic failover and can integrate with Kubernetes/Consul:

```yaml
# patroni-config.yaml
scope: postgres-cluster
namespace: /db/
name: postgres-primary

restapi:
  listen: 0.0.0.0:8008
  connect_address: postgres-primary:8008

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 30
    maximum_lag_on_failover: 1048576

postgresql:
  parameters:
    wal_level: replica
    max_wal_senders: 10
    max_replication_slots: 10
```

**With Kubernetes Operator:**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
spec:
  instances: 3  # Primary + 2 replicas
  postgresql:
    parameters:
      max_connections: "200"
```

## Recommended Approach by Use Case

| Use Case | Recommended Solution | Replica Management |
|----------|---------------------|-------------------|
| **Development** | Docker Compose + PgPool-II | Manual configuration |
| **Small Production** | Managed Service (RDS/Cloud SQL) | Set replica count in UI/CLI |
| **Medium Production** | Kubernetes + StatefulSets | `kubectl scale` command |
| **Large Production** | Terraform + Managed Service | Infrastructure as Code |
| **Custom Requirements** | Patroni + Kubernetes Operator | Operator handles scaling |

## Implementation Steps

### Step 1: Infrastructure Setup (Docker Compose)

#### 1.1 Configure PostgreSQL Primary for Replication

Add replication configuration to the primary PostgreSQL:

```yaml
postgres-primary:
  image: postgres:15
  container_name: postgres-primary
  restart: unless-stopped
  environment:
    POSTGRES_USER: dapruser
    POSTGRES_PASSWORD: daprpassword
    POSTGRES_DB: daprdb
    # Enable replication
    POSTGRES_REPLICATION_USER: replicator
    POSTGRES_REPLICATION_PASSWORD: replicator_password
  ports:
    - "5432:5432"
  volumes:
    - postgres_primary_data:/var/lib/postgresql/data
    - ./scripts/postgres-primary-init.sh:/docker-entrypoint-initdb.d/init-replication.sh
  command: >
    postgres
    -c wal_level=replica
    -c max_wal_senders=3
    -c max_replication_slots=3
    -c hot_standby=on
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U dapruser -d daprdb"]
    interval: 10s
    timeout: 5s
    retries: 5
```

#### 1.2 Create PostgreSQL Read Replicas

```yaml
postgres-replica-1:
  image: postgres:15
  container_name: postgres-replica-1
  restart: unless-stopped
  environment:
    POSTGRES_USER: dapruser
    POSTGRES_PASSWORD: daprpassword
    POSTGRES_DB: daprdb
    PGUSER: postgres
  volumes:
    - postgres_replica1_data:/var/lib/postgresql/data
    - ./scripts/postgres-replica-init.sh:/docker-entrypoint-initdb.d/init-replica.sh
  command: >
    postgres
    -c hot_standby=on
    -c max_standby_streaming_delays=30s
  depends_on:
    postgres-primary:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U dapruser -d daprdb && pg_is_in_recovery"]
    interval: 10s
    timeout: 5s
    retries: 5

postgres-replica-2:
  image: postgres:15
  container_name: postgres-replica-2
  restart: unless-stopped
  environment:
    POSTGRES_USER: dapruser
    POSTGRES_PASSWORD: daprpassword
    POSTGRES_DB: daprdb
    PGUSER: postgres
  volumes:
    - postgres_replica2_data:/var/lib/postgresql/data
    - ./scripts/postgres-replica-init.sh:/docker-entrypoint-initdb.d/init-replica.sh
  command: >
    postgres
    -c hot_standby=on
    -c max_standby_streaming_delays=30s
  depends_on:
    postgres-primary:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U dapruser -d daprdb && pg_is_in_recovery"]
    interval: 10s
    timeout: 5s
    retries: 5
```

#### 1.3 Add PgBouncer Connection Pooler

```yaml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  container_name: pgbouncer
  restart: unless-stopped
  environment:
    DATABASES_HOST: postgres-primary
    DATABASES_PORT: 5432
    DATABASES_USER: dapruser
    DATABASES_PASSWORD: daprpassword
    DATABASES_DBNAME: daprdb
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 1000
    PGBOUNCER_DEFAULT_POOL_SIZE: 25
    PGBOUNCER_MIN_POOL_SIZE: 5
    PGBOUNCER_RESERVE_POOL_SIZE: 5
    PGBOUNCER_RESERVE_POOL_TIMEOUT: 3
    PGBOUNCER_MAX_DB_CONNECTIONS: 0
    PGBOUNCER_MAX_USER_CONNECTIONS: 0
  ports:
    - "6432:6432"
  depends_on:
    postgres-primary:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "pg_isready", "-h", "localhost", "-p", "6432", "-U", "dapruser"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Note**: PgBouncer is simpler but only pools connections. For automatic read/write splitting, you'd need **PgPool-II** instead.

#### 1.4 Alternative: PgPool-II (Recommended for Read/Write Splitting)

PgPool-II can automatically route reads to replicas and writes to primary:

```yaml
pgpool:
  image: pgpool/pgpool:latest
  container_name: pgpool
  restart: unless-stopped
  environment:
    PGPOOL_BACKEND_HOSTNAME0: postgres-primary
    PGPOOL_BACKEND_PORT0: 5432
    PGPOOL_BACKEND_WEIGHT0: 0  # 0 = primary (writes only)
    PGPOOL_BACKEND_FLAG0: ALLOW_TO_FAILOVER
    
    PGPOOL_BACKEND_HOSTNAME1: postgres-replica-1
    PGPOOL_BACKEND_PORT1: 5432
    PGPOOL_BACKEND_WEIGHT1: 1  # 1 = read replica
    PGPOOL_BACKEND_FLAG1: ALLOW_TO_FAILOVER
    
    PGPOOL_BACKEND_HOSTNAME2: postgres-replica-2
    PGPOOL_BACKEND_PORT2: 5432
    PGPOOL_BACKEND_WEIGHT2: 1  # 1 = read replica
    PGPOOL_BACKEND_FLAG2: ALLOW_TO_FAILOVER
    
    PGPOOL_POSTGRES_USERNAME: dapruser
    PGPOOL_POSTGRES_PASSWORD: daprpassword
    PGPOOL_POSTGRES_DBNAME: daprdb
    
    PGPOOL_ENABLE_LOAD_BALANCING: "yes"
    PGPOOL_NUM_INIT_CHILDREN: 32
    PGPOOL_MAX_POOL: 4
  ports:
    - "5433:5432"
  depends_on:
    postgres-primary:
      condition: service_healthy
    postgres-replica-1:
      condition: service_healthy
    postgres-replica-2:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "pg_isready", "-h", "localhost", "-p", "5432", "-U", "dapruser"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Step 2: Replication Setup Scripts

#### 2.1 Primary Initialization Script

Create `scripts/postgres-primary-init.sh`:

```bash
#!/bin/bash
set -e

# Create replication user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO replicator;
    GRANT USAGE ON SCHEMA public TO replicator;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO replicator;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO replicator;
EOSQL

echo "Replication user created"
```

#### 2.2 Replica Initialization Script

Create `scripts/postgres-replica-init.sh`:

```bash
#!/bin/bash
set -e

# Remove default data directory
rm -rf /var/lib/postgresql/data/*

# Perform base backup from primary
PGPASSWORD=replicator_password pg_basebackup \
    -h postgres-primary \
    -D /var/lib/postgresql/data \
    -U replicator \
    -v \
    -P \
    -W \
    -R

# Configure replication
cat >> /var/lib/postgresql/data/postgresql.conf <<EOF
hot_standby = on
max_standby_streaming_delays = 30s
EOF

echo "Replica initialized from primary"
```

### Step 3: Application Code Changes

#### 3.1 Update PostgresConfig to Support Multiple Connections

Modify `common/common/database/postgres.py`:

```python
@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration"""
    # Primary (write) connection
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"
    
    # Read replica connections (optional)
    read_replicas: List[Dict[str, Any]] = None
    
    # Connection pool settings
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    
    def __post_init__(self):
        if self.read_replicas is None:
            self.read_replicas = []
```

#### 3.2 Create Read/Write Connection Manager

Create `common/common/database/postgres_rw.py`:

```python
"""
PostgreSQL Read/Write connection manager

Manages separate connection pools for:
- Primary (writes)
- Read replicas (reads with load balancing)
"""

import logging
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import asyncpg

from common.database.postgres import PostgresConfig, create_postgres_pool

logger = logging.getLogger(__name__)


@dataclass
class ReadWriteConfig:
    """Configuration for read/write splitting"""
    primary: PostgresConfig
    replicas: List[PostgresConfig]
    replica_load_balance: str = "round_robin"  # or "random"


class ReadWriteConnectionManager:
    """Manages read and write connections"""
    
    def __init__(self, config: ReadWriteConfig):
        self.config = config
        self.primary_pool: Optional[asyncpg.Pool] = None
        self.replica_pools: List[asyncpg.Pool] = []
        self.replica_index = 0  # For round-robin
    
    async def initialize(self):
        """Initialize all connection pools"""
        # Initialize primary pool
        self.primary_pool = await create_postgres_pool(self.config.primary)
        logger.info("Primary PostgreSQL pool initialized")
        
        # Initialize replica pools
        for replica_config in self.config.replicas:
            pool = await create_postgres_pool(replica_config)
            self.replica_pools.append(pool)
            logger.info(f"Read replica pool initialized: {replica_config.host}:{replica_config.port}")
    
    async def close(self):
        """Close all connection pools"""
        if self.primary_pool:
            await self.primary_pool.close()
        
        for pool in self.replica_pools:
            await pool.close()
    
    def get_write_pool(self) -> asyncpg.Pool:
        """Get connection pool for writes (primary)"""
        if self.primary_pool is None:
            raise RuntimeError("Primary pool not initialized")
        return self.primary_pool
    
    def get_read_pool(self) -> asyncpg.Pool:
        """Get connection pool for reads (replica with load balancing)"""
        if not self.replica_pools:
            # Fallback to primary if no replicas
            return self.get_write_pool()
        
        if self.config.replica_load_balance == "random":
            return random.choice(self.replica_pools)
        else:  # round_robin
            pool = self.replica_pools[self.replica_index]
            self.replica_index = (self.replica_index + 1) % len(self.replica_pools)
            return pool
```

#### 3.3 Update Repository to Use Read/Write Splitting

Modify `services/user-service/src/repositories/postgres.py`:

```python
from src.database import get_read_pool, get_write_pool

class PostgresRepository:
    """Repository for PostgreSQL operations with read/write splitting"""
    
    async def create(self, name: str, email: str) -> User:
        """Create a new user - uses WRITE pool (primary)"""
        pool = get_write_pool()  # Changed from get_pg_pool()
        
        async with pool.acquire() as conn:
            # ... rest of the code
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID - uses READ pool (replica)"""
        pool = get_read_pool()  # Changed from get_pg_pool()
        
        async with pool.acquire() as conn:
            # ... rest of the code
    
    async def update(self, user_id: int, name: Optional[str], email: Optional[str]) -> Optional[User]:
        """Update a user - uses WRITE pool (primary)"""
        pool = get_write_pool()  # Changed from get_pg_pool()
        
        async with pool.acquire() as conn:
            # ... rest of the code
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user - uses WRITE pool (primary)"""
        pool = get_write_pool()  # Changed from get_pg_pool()
        
        async with pool.acquire() as conn:
            # ... rest of the code
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users - uses READ pool (replica)"""
        pool = get_read_pool()  # Changed from get_pg_pool()
        
        async with pool.acquire() as conn:
            # ... rest of the code
```

#### 3.4 Update Database Initialization

Modify `services/user-service/src/database.py`:

```python
from common.database.postgres_rw import ReadWriteConnectionManager, ReadWriteConfig
from src.config import POSTGRES_PRIMARY_CONFIG, POSTGRES_REPLICA_CONFIGS

_rw_manager: Optional[ReadWriteConnectionManager] = None

async def init_postgres() -> ReadWriteConnectionManager:
    """Initialize PostgreSQL with read/write splitting"""
    global _rw_manager
    
    config = ReadWriteConfig(
        primary=POSTGRES_PRIMARY_CONFIG,
        replicas=POSTGRES_REPLICA_CONFIGS,
        replica_load_balance="round_robin"
    )
    
    _rw_manager = ReadWriteConnectionManager(config)
    await _rw_manager.initialize()
    
    # Create tables on primary (they'll replicate to replicas)
    async with _rw_manager.get_write_pool().acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)
    
    logger.info("PostgreSQL initialized with read/write splitting")
    return _rw_manager

def get_write_pool() -> asyncpg.Pool:
    """Get write pool (primary)"""
    if _rw_manager is None:
        raise RuntimeError("PostgreSQL not initialized")
    return _rw_manager.get_write_pool()

def get_read_pool() -> asyncpg.Pool:
    """Get read pool (replica)"""
    if _rw_manager is None:
        raise RuntimeError("PostgreSQL not initialized")
    return _rw_manager.get_read_pool()

# Keep get_pg_pool for backward compatibility (defaults to read)
def get_pg_pool() -> asyncpg.Pool:
    """Get PostgreSQL pool (defaults to read pool)"""
    return get_read_pool()
```

#### 3.5 Update Configuration

Modify `services/user-service/src/config.py`:

```python
import os
from typing import List
from common.database import PostgresConfig

# Primary database (writes)
POSTGRES_PRIMARY_CONFIG = PostgresConfig.from_url(
    os.getenv("DATABASE_URL_PRIMARY", "postgresql://dapruser:daprpassword@postgres-primary:5432/daprdb")
)

# Read replicas (reads)
POSTGRES_REPLICA_CONFIGS: List[PostgresConfig] = [
    PostgresConfig.from_url(
        os.getenv("DATABASE_URL_REPLICA_1", "postgresql://dapruser:daprpassword@postgres-replica-1:5432/daprdb")
    ),
    PostgresConfig.from_url(
        os.getenv("DATABASE_URL_REPLICA_2", "postgresql://dapruser:daprpassword@postgres-replica-2:5432/daprdb")
    ),
]
```

### Step 4: Environment Variables

Update `docker-compose.yml` for user-service:

```yaml
user-service:
  environment:
    # Primary (writes)
    - DATABASE_URL_PRIMARY=postgresql://dapruser:daprpassword@postgres-primary:5432/daprdb
    # Read replicas
    - DATABASE_URL_REPLICA_1=postgresql://dapruser:daprpassword@postgres-replica-1:5432/daprdb
    - DATABASE_URL_REPLICA_2=postgresql://dapruser:daprpassword@postgres-replica-2:5432/daprdb
    # Or use PgPool-II for automatic routing
    - DATABASE_URL=postgresql://dapruser:daprpassword@pgpool:5432/daprdb
```

## How It Works

### Read Operations
1. Application receives a GET request
2. Repository calls `get_read_pool()`
3. Connection manager selects a replica (round-robin or random)
4. Query executes on replica
5. Result returned to application

### Write Operations
1. Application receives a POST/PUT/DELETE request
2. Repository calls `get_write_pool()`
3. Connection manager returns primary pool
4. Write executes on primary
5. Changes stream to replicas via WAL replication
6. Result returned to application

### Replication Lag Handling

**Problem**: Replicas may lag behind primary (typically < 1 second)

**Solutions**:
1. **Read-after-write consistency**: After writes, read from primary for a short time
2. **Sticky sessions**: Route user's reads to primary after they write
3. **Accept eventual consistency**: Most reads don't need immediate consistency
4. **Monitor lag**: Track replication lag and route reads accordingly

## Monitoring & Health Checks

### Check Replication Status

```sql
-- On primary
SELECT * FROM pg_stat_replication;

-- On replica
SELECT pg_is_in_recovery();  -- Returns true if replica
SELECT pg_last_wal_receive_lsn();  -- Last received WAL
SELECT pg_last_wal_replay_lsn();   -- Last replayed WAL
```

### Monitor Lag

```sql
-- On replica
SELECT 
    EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;
```

### Health Check Endpoints

Add to your health check:

```python
async def check_postgres_health():
    """Check both primary and replica health"""
    try:
        # Check primary
        async with get_write_pool().acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check replicas
        for i, pool in enumerate(get_replica_pools()):
            async with pool.acquire() as conn:
                lag = await conn.fetchval(
                    "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))"
                )
                if lag > 10:  # More than 10 seconds lag
                    logger.warning(f"Replica {i} lagging: {lag}s")
        
        return True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False
```

## Performance Considerations

### Connection Pool Sizing

- **Primary pool**: Smaller (fewer writes)
  - `min_connections: 5`
  - `max_connections: 20`

- **Replica pools**: Larger (more reads)
  - `min_connections: 10` per replica
  - `max_connections: 50` per replica

### Load Balancing Strategy

- **Round-robin**: Even distribution, predictable
- **Random**: Better for uneven replica performance
- **Weighted**: Based on replica capacity/performance

## Failure Handling

### Replica Failure
- Application automatically falls back to primary
- Health checks detect failed replicas
- Remove from rotation until healthy

### Primary Failure
- **Not handled automatically** (requires manual failover)
- Consider using Patroni or repmgr for automatic failover
- Or use managed services (RDS, Cloud SQL) with automatic failover

## Benefits

✅ **Scalability**: Add more replicas as read load increases  
✅ **Performance**: Distribute read load across multiple servers  
✅ **Availability**: Replicas can serve reads if primary has issues  
✅ **Backup**: Replicas can be used for backups without impacting primary  
✅ **Analytics**: Use replicas for reporting/analytics queries  

## Limitations

⚠️ **Write bottleneck**: All writes still go to single primary  
⚠️ **Replication lag**: Reads may see slightly stale data  
⚠️ **Complexity**: More moving parts to manage  
⚠️ **Cost**: More database instances = higher cost  

## Quick Start: Minimal Code Approach

### Using PgPool-II (Recommended for Quick Setup)

**This is the easiest approach - you only need to change your connection string!**

**1. Generate docker-compose with replicas:**
```bash
# Generate configuration with 3 replicas
./scripts/generate-postgres-replicas.sh 3 docker-compose.replicas.yml
```

**2. Update docker-compose.yml (or use the generated file):**
```yaml
services:
  postgres-primary:
    # ... existing primary config ...
    
  postgres-replica:
    image: postgres:15
    deploy:
      replicas: 2  # Just change this number!
    environment:
      POSTGRES_USER: dapruser
      POSTGRES_PASSWORD: daprpassword
      POSTGRES_DB: daprdb
    # ... replica config ...
    
  pgpool:
    image: pgpool/pgpool:latest
    environment:
      PGPOOL_BACKEND_HOSTNAME0: postgres-primary
      PGPOOL_BACKEND_PORT0: 5432
      PGPOOL_BACKEND_WEIGHT0: 0
      PGPOOL_BACKEND_HOSTNAME1: postgres-replica
      PGPOOL_BACKEND_PORT1: 5432
      PGPOOL_BACKEND_WEIGHT1: 1
      PGPOOL_ENABLE_LOAD_BALANCING: "yes"
    ports:
      - "5433:5432"
```

**2. Update your application config:**
```python
# services/user-service/src/config.py
POSTGRES_CONFIG = PostgresConfig.from_url(
    os.getenv("DATABASE_URL", "postgresql://dapruser:daprpassword@pgpool:5432/daprdb")
    #                    ^^^^^^ Just point to pgpool instead of postgres!
)
```

**3. No code changes needed!** Your existing repository code works as-is.

### Using Script-Based Replica Generation

**Create `scripts/generate-docker-compose.sh`:**
```bash
#!/bin/bash
REPLICA_COUNT=${1:-2}

# Generate replica services
REPLICA_SERVICES=""
for i in $(seq 1 $REPLICA_COUNT); do
  REPLICA_SERVICES+="
  postgres-replica-${i}:
    image: postgres:15
    container_name: postgres-replica-${i}
    environment:
      POSTGRES_USER: dapruser
      POSTGRES_PASSWORD: daprpassword
      POSTGRES_DB: daprdb
      REPLICA_NUMBER: ${i}
    volumes:
      - postgres_replica${i}_data:/var/lib/postgresql/data
      - ./scripts/postgres-replica-init.sh:/docker-entrypoint-initdb.d/init-replica.sh
    command: >
      postgres
      -c hot_standby=on
    depends_on:
      postgres-primary:
        condition: service_healthy
"
done

# Generate PgPool config
PGPOOL_BACKENDS="PGPOOL_BACKEND_HOSTNAME0: postgres-primary
PGPOOL_BACKEND_PORT0: 5432
PGPOOL_BACKEND_WEIGHT0: 0"

for i in $(seq 1 $REPLICA_COUNT); do
  PGPOOL_BACKENDS+="
PGPOOL_BACKEND_HOSTNAME${i}: postgres-replica-${i}
PGPOOL_BACKEND_PORT${i}: 5432
PGPOOL_BACKEND_WEIGHT${i}: 1"
done

cat > docker-compose.replicas.yml <<EOF
services:
  postgres-primary:
    # ... your primary config ...
    
${REPLICA_SERVICES}
  
  pgpool:
    image: pgpool/pgpool:latest
    environment:
${PGPOOL_BACKENDS}
      PGPOOL_POSTGRES_USERNAME: dapruser
      PGPOOL_POSTGRES_PASSWORD: daprpassword
      PGPOOL_POSTGRES_DBNAME: daprdb
      PGPOOL_ENABLE_LOAD_BALANCING: "yes"
    ports:
      - "5433:5432"
EOF

echo "Generated docker-compose.replicas.yml with $REPLICA_COUNT replicas"
```

**Usage:**
```bash
chmod +x scripts/generate-docker-compose.sh
./scripts/generate-docker-compose.sh 5  # Generate 5 replicas
docker-compose -f docker-compose.replicas.yml up -d
```

## Summary: Answering Your Questions

### Q1: Is there a library that handles connection management?

**Yes!** You have three main options:

1. **PgPool-II** (Recommended)
   - ✅ Zero application code changes
   - ✅ Automatic read/write splitting
   - ✅ Just change your connection string to point to `pgpool` instead of `postgres`
   - ✅ Handles load balancing, connection pooling, health checks

2. **PgCat** (Modern alternative)
   - ✅ Similar to PgPool-II
   - ✅ Better performance for high concurrency
   - ✅ RESTful admin API

3. **Custom Python library** (What we showed earlier)
   - ⚠️ Requires code changes
   - ✅ More control
   - ✅ Better for custom requirements

**Recommendation:** Use PgPool-II for simplicity. Your existing code works without changes!

### Q2: Can I specify replica count in docker-compose instead of listing each?

**Yes, with limitations:**

1. **Docker Swarm Mode** - Use `deploy.replicas`:
   ```yaml
   postgres-replica:
     deploy:
       replicas: 3  # Just specify the number!
   ```
   But: Requires Swarm mode and each replica still needs unique config

2. **Script Generation** - Generate docker-compose.yml dynamically:
   ```bash
   ./scripts/generate-docker-compose.sh 5  # Creates 5 replicas
   ```
   ✅ Works with regular Docker Compose
   ✅ Flexible and customizable

3. **Kubernetes** - Best for production:
   ```yaml
   replicas: 5  # Kubernetes handles everything
   ```
   ✅ Automatic initialization
   ✅ Service discovery
   ✅ Health checks

**Recommendation:** Use script generation for development, Kubernetes for production.

### Q3: What does this look like in production?

**Production options (from simplest to most control):**

1. **Managed Services** (Easiest)
   ```bash
   # AWS RDS
   aws rds create-db-instance-read-replica --count 5
   
   # Google Cloud SQL
   gcloud sql instances create replica-1 --replica-count=5
   
   # Azure Database
   az postgres flexible-server replica create --count 5
   ```
   ✅ Just specify replica count
   ✅ Everything else is automatic

2. **Kubernetes**
   ```bash
   kubectl scale statefulset postgres-replica --replicas=5
   ```
   ✅ One command to scale
   ✅ Automatic initialization

3. **Terraform**
   ```hcl
   variable "replica_count" { default = 5 }
   resource "aws_db_instance" "replica" {
     count = var.replica_count
   }
   ```
   ✅ Infrastructure as Code
   ✅ Version controlled
   ✅ Repeatable

**Recommendation:** 
- **Small/Medium:** Managed services (RDS, Cloud SQL)
- **Large/Custom:** Kubernetes + Operators or Terraform

## Next Steps

After Phase 1 is stable, consider:
- **Phase 2**: Sharding for write scaling (Citus)
- **Automatic failover**: Patroni, repmgr, or managed services
- **Read replicas in different regions**: For geographic distribution
- **Partitioning**: For very large tables

