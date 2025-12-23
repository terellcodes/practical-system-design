# Database Admin Dashboards Guide

This guide shows you how to access and use the three web-based admin dashboards for your data stores.

## 🚀 Quick Start

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the dashboards:**
   - **pgAdmin (PostgreSQL)**: http://localhost:5050
   - **Redis Commander**: http://localhost:8081
   - **DynamoDB Admin**: http://localhost:8082

---

## 1. pgAdmin - PostgreSQL Dashboard

**URL:** http://localhost:5050  
**Login:** `admin@admin.com` / `admin`

### First Time Setup:

After logging in, you need to register your PostgreSQL server:

1. **Right-click "Servers"** → **Register** → **Server**

2. **General Tab:**
   - Name: `Local Postgres` (or any name you like)

3. **Connection Tab:**
   - Host: `postgres`
   - Port: `5432`
   - Maintenance database: `daprdb`
   - Username: `dapruser`
   - Password: `daprpassword`
   - ☑️ Save password

4. **Click Save**

### Using pgAdmin:

- **Browse tables:** Servers → Local Postgres → Databases → daprdb → Schemas → public → Tables
- **Run queries:** Right-click database → **Query Tool**
- **View data:** Right-click table → **View/Edit Data** → **All Rows**

### Example Queries:

```sql
-- See all users
SELECT * FROM users;

-- Count users
SELECT COUNT(*) FROM users;

-- Search users
SELECT * FROM users WHERE email LIKE '%example%';
```

---

## 2. Redis Commander - Redis Dashboard

**URL:** http://localhost:8081  
**No login required**

### Features:

- **Browse all keys** by database (db0, db1, etc.)
- **View key values** (strings, hashes, lists, sets, sorted sets)
- **TTL information** (expiration times)
- **Add/Edit/Delete keys**
- **Search keys** by pattern

### Using Redis Commander:

1. **Select database** (default is db0 - used by user-service)
2. **Browse keys** in the left panel
3. **Click any key** to view/edit its value
4. **Search** using patterns like `user:*` or `cache:*`

### Common Operations:

- **View all keys:** Select database and browse
- **Search pattern:** Use search box with wildcards (`user:*`, `*:cache`)
- **Add new key:** Click "Add Key" button
- **Delete key:** Click trash icon next to key

### What to Look For:

Your user-service caches data in Redis with keys like:
- `user:{id}` - Cached user records

---

## 3. DynamoDB Admin - DynamoDB Dashboard

**URL:** http://localhost:8082  
**No login required**

### Features:

- **Browse tables** (Chats, ChatParticipants)
- **View all items** in a table
- **Query and scan** operations
- **Add/Edit/Delete items**
- **View table schema** (partition key, sort key, GSIs)

### Using DynamoDB Admin:

1. **Select a table** from dropdown (top-left)
2. **View items** - shows all records
3. **Add item** - click "Create" button
4. **Edit item** - click any item to modify
5. **Delete item** - select item and click delete

### Your Tables:

#### **Chats Table:**
- Partition Key: `id`
- Sort Key: `created_at`
- Contains: Chat room information

#### **ChatParticipants Table:**
- Partition Key: `chat_id`
- Sort Key: `user_id`
- Contains: Users in each chat room

### Example Scans:

Click on a table name and it will automatically show all items. You can:
- **Filter** by attribute values
- **Sort** by clicking column headers
- **Export** data as JSON

---

## 🔍 Common Tasks

### Task 1: Verify User Service is Working

1. **Check Postgres** (pgAdmin):
   ```sql
   SELECT COUNT(*) FROM users;
   ```

2. **Check Redis** (Redis Commander):
   - Look for keys like `user:*`
   - These are cached user records

### Task 2: Verify Chat Service is Working

1. **Check DynamoDB** (DynamoDB Admin):
   - Select "Chats" table → View items
   - Select "ChatParticipants" table → View items

### Task 3: Debug Cache Issues

1. **Redis Commander**: 
   - Search for the cached key
   - Check its TTL (time to live)
   - Delete key to force refresh from database

### Task 4: View User Data

1. **Source of Truth** (Postgres via pgAdmin):
   ```sql
   SELECT id, username, email, created_at FROM users;
   ```

2. **Cached Copy** (Redis Commander):
   - Search: `user:*`
   - Compare with Postgres data

---

## 🛠️ Troubleshooting

### pgAdmin won't connect to PostgreSQL:
- Make sure you used host `postgres` (not `localhost`)
- Verify credentials: `dapruser` / `daprpassword`
- Check postgres container is running: `docker ps | grep postgres`

### Redis Commander shows "Connection refused":
- Verify redis container is running: `docker ps | grep redis`
- Check Redis is healthy: `docker exec -it redis redis-cli ping`

### DynamoDB Admin shows "No tables":
- Check LocalStack is running: `docker ps | grep localstack`
- Tables should be created by init script: `scripts/init-dynamodb.sh`
- Manually run init: `docker exec localstack /etc/localstack/init/ready.d/init-dynamodb.sh`

### Can't access dashboards:
```bash
# Check all admin containers are running
docker ps | grep -E "(pgadmin|redis-commander|dynamodb-admin)"

# Check logs if any container is failing
docker logs pgadmin
docker logs redis-commander
docker logs dynamodb-admin
```

---

## 📊 Architecture Overview

```
Your Services:
├── user-service (3 replicas)
│   ├── Postgres (source of truth) ──→ pgAdmin (http://localhost:5050)
│   └── Redis (cache)              ──→ Redis Commander (http://localhost:8081)
│
└── chat-service (2 replicas)
    └── DynamoDB (messages)        ──→ DynamoDB Admin (http://localhost:8082)
```

---

## 💡 Tips

1. **pgAdmin Shortcuts:**
   - `F5` = Execute query
   - `Ctrl+T` = New query tab
   - Right-click table → Export = Download as CSV

2. **Redis Commander:**
   - Use CLI for complex operations: `docker exec -it redis redis-cli`
   - Database 0 = user-service cache
   - Watch memory usage in the dashboard

3. **DynamoDB Admin:**
   - Use "Scan" to see all items (expensive in production!)
   - Use "Query" to search by partition key (efficient)
   - Remember: DynamoDB is eventually consistent

4. **General:**
   - Bookmark all three URLs for quick access
   - Keep dashboards open in separate browser tabs
   - Use dark mode in pgAdmin: File → Preferences → Themes

---

## 🔐 Security Notes

**⚠️ For Development Only:**
- These dashboards have simple/no authentication
- Ports are exposed to host machine
- **DO NOT** use these settings in production

**For Production:**
- Use proper authentication
- Access via VPN or internal network only
- Use environment variables for passwords
- Enable SSL/TLS
- Restrict network access with firewall rules

---

## Next Steps

1. **Start your services:** `docker-compose up -d`
2. **Open all three dashboards** in your browser
3. **Configure pgAdmin** (one-time setup)
4. **Run some API requests** to generate data
5. **Watch data flow** through the dashboards in real-time

Happy debugging! 🎉

