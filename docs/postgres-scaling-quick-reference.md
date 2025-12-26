# PostgreSQL Horizontal Scaling - Quick Reference

## TL;DR: Your Questions Answered

### Q1: Is there a library that handles connection management?

**Yes! Use PgPool-II** - It handles everything automatically:

```yaml
# docker-compose.yml
services:
  pgpool:
    image: pgpool/pgpool:latest
    environment:
      PGPOOL_BACKEND_HOSTNAME0: postgres-primary
      PGPOOL_BACKEND_WEIGHT0: 0  # Primary (writes)
      PGPOOL_BACKEND_HOSTNAME1: postgres-replica-1
      PGPOOL_BACKEND_WEIGHT1: 1  # Replica (reads)
      PGPOOL_ENABLE_LOAD_BALANCING: "yes"
```

**Your code:** Just change the connection string!
```python
# Before
DATABASE_URL=postgresql://user:pass@postgres:5432/db

# After (point to pgpool instead)
DATABASE_URL=postgresql://user:pass@pgpool:5432/db
```

**That's it!** No code changes needed. PgPool-II automatically:
- Routes writes → Primary
- Routes reads → Replicas (load balanced)
- Handles connection pooling
- Manages health checks

### Q2: Can I specify replica count instead of listing each?

**Yes! Use the provided script:**

```bash
# Generate docker-compose with 5 replicas
./scripts/generate-postgres-replicas.sh 5 docker-compose.replicas.yml

# Start everything
docker-compose -f docker-compose.replicas.yml up -d
```

The script automatically:
- Creates N replica services
- Configures PgPool-II with all replicas
- Sets up volumes and dependencies
- Configures health checks

### Q3: What about production?

**Production options (pick one):**

#### Option A: Managed Service (Easiest)
```bash
# AWS RDS - Just specify count
aws rds create-db-instance-read-replica \
  --db-instance-identifier myapp-replica-1 \
  --source-db-instance-identifier myapp-primary

# Or use Terraform
variable "replica_count" { default = 5 }
resource "aws_db_instance" "replica" {
  count = var.replica_count
}
```

#### Option B: Kubernetes
```yaml
# Just specify replicas
apiVersion: apps/v1
kind: StatefulSet
spec:
  replicas: 5  # Change this number!
```

```bash
# Scale up/down anytime
kubectl scale statefulset postgres-replica --replicas=10
```

#### Option C: Docker Swarm
```yaml
services:
  postgres-replica:
    deploy:
      replicas: 5  # Just change this!
```

## Comparison Table

| Approach | Code Changes | Replica Management | Best For |
|----------|-------------|-------------------|----------|
| **PgPool-II** | None (just connection string) | Manual config | Development, Small prod |
| **PgCat** | None | Manual config | High concurrency |
| **Custom Library** | Yes (read/write splitting) | Manual config | Custom requirements |
| **Managed Service** | None | Set count in UI/CLI | Production (easiest) |
| **Kubernetes** | None | `kubectl scale` | Production (flexible) |
| **Terraform** | None | Infrastructure as Code | Production (versioned) |

## Recommended Path

1. **Development:** Use PgPool-II + script generation
   ```bash
   ./scripts/generate-postgres-replicas.sh 2
   docker-compose -f docker-compose.replicas.yml up -d
   ```

2. **Production:** Use managed service or Kubernetes
   - AWS RDS: Set replica count in console
   - Kubernetes: `kubectl scale --replicas=5`
   - Terraform: `variable "replica_count" { default = 5 }`

## Key Takeaway

**You don't need to write connection management code!**

- **PgPool-II** handles it automatically (zero code changes)
- **Managed services** handle it automatically (just set replica count)
- **Kubernetes** handles it automatically (just scale the StatefulSet)

The custom library approach (shown in the main guide) gives you more control, but it's optional. Most use cases can use PgPool-II or managed services.

