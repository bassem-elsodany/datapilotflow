# Milvus Vector Database Credentials & Configuration

## Overview

Vector database credentials are loaded from **environment variables** with sensible defaults. The configuration is centralized in the domain package and used by the persistence layer.

---

## Credentials Loading Flow

```
Environment Variables (.env file)
           ↓
datapilotflow.domain.config.Settings
           ↓
MilvusClientWrapper.__init__()
           ↓
pymilvus.connections.connect()
```

---

## Configuration Source

**File:** [datapilotflow-domain/src/datapilotflow/domain/config.py](datapilotflow-domain/src/datapilotflow/domain/config.py#L218)

**Class:** `Settings` (Pydantic v2 Settings model)

---

## Default Credentials

| Setting | Environment Variable | Default Value | Type |
|---------|---------------------|---------------|------|
| **Host** | `VECTOR_DB_HOST` | `localhost` | string |
| **Port** | `VECTOR_DB_HTTP_PORT` | `19530` | int |
| **Username** | `VECTOR_DB_USERNAME` | `root` | string |
| **Password** | `VECTOR_DB_PASSWORD` | `Milvus` | string |
| **Scheme** | `VECTOR_DB_CONNECTION_SCHEME` | `http` | string |

### Current Connection String
```
http://root:Milvus@localhost:19530
```

---

## How Credentials Are Loaded

### 1. **Default Configuration**
When no environment variables are set, the system uses hardcoded defaults:

```python
# datapilotflow-domain/src/datapilotflow/domain/config.py (lines 218-234)

VECTOR_DB_HOST: str = Field(
    default="localhost",
    description="Vector database host address"
)

VECTOR_DB_HTTP_PORT: int = Field(
    default=19530,
    description="Vector database HTTP port"
)

VECTOR_DB_USERNAME: str = Field(
    default="root",
    description="Vector database username"
)

VECTOR_DB_PASSWORD: str = Field(
    default="Milvus",
    description="Vector database password"
)

VECTOR_DB_CONNECTION_SCHEME: str = Field(
    default="http",
    description="Vector database connection scheme (http or https)"
)
```

### 2. **Environment Variable Override**
Create a `.env` file in the backend root directory:

```bash
# .env
VECTOR_DB_HOST=your-milvus-host.com
VECTOR_DB_HTTP_PORT=19530
VECTOR_DB_USERNAME=your-username
VECTOR_DB_PASSWORD=your-password
VECTOR_DB_CONNECTION_SCHEME=https
```

### 3. **Runtime Usage in MilvusClientWrapper**

**File:** [datapilotflow-persistence/src/datapilotflow/persistence/vectordb/milvus/client.py](datapilotflow-persistence/src/datapilotflow/persistence/vectordb/milvus/client.py#L58)

```python
def __init__(
    self,
    model: Type[T],
    collection_name: str,
    vector_dimension: int,
    milvus_host: str = settings.VECTOR_DB_HOST,           # ← Loads from settings
    milvus_port: str = str(settings.VECTOR_DB_HTTP_PORT), # ← Loads from settings
    milvus_user: str = settings.VECTOR_DB_USERNAME,       # ← Loads from settings
    milvus_password: str = settings.VECTOR_DB_PASSWORD,   # ← Loads from settings
    connection_alias: Optional[str] = None,
    index_type: str = "HNSW",
    index_params: Optional[Dict[str, Any]] = None,
) -> None:
    """Initialize a connection to the Milvus instance."""

    # Connection attempt with retry logic (lines 94-120)
    for attempt in range(max_retries):
        try:
            # Connect using pymilvus
            connections.connect(
                alias=self.connection_alias,
                host=milvus_host,
                port=int(milvus_port),
                user=milvus_user,
                password=milvus_password,
                pool_size=10,
            )
```

---

## Current System State

### ✅ Connected Collections
Your Milvus instance is **currently running** at:
- **Host:** `localhost`
- **Port:** `19530`
- **Credentials:** `root:Milvus` (default)

### Active Collections
1. **BureauofExpertsofCouncilofSaudiMinisters** - 7,465 records
2. **mulesoft** - 7,989 records
3. **CanadaCriminalLaw** - 263 records
4. **MDMulesfot** - 487 records
5. **mulesoftMDS** - 493 records

**Total:** 16,697 vector embeddings

---

## Environment Variable Setup Examples

### Local Development (.env)
```bash
# Development - local Milvus instance
VECTOR_DB_HOST=localhost
VECTOR_DB_HTTP_PORT=19530
VECTOR_DB_USERNAME=root
VECTOR_DB_PASSWORD=Milvus
VECTOR_DB_CONNECTION_SCHEME=http
```

### Production (Cloud Milvus)
```bash
# Production - Zilliz Cloud instance
VECTOR_DB_HOST=in01-abc123xyz.api.gcp-us-west1.zillizcloud.com
VECTOR_DB_HTTP_PORT=443
VECTOR_DB_USERNAME=db_admin
VECTOR_DB_PASSWORD=your-secure-password-here
VECTOR_DB_CONNECTION_SCHEME=https
```

### Docker Milvus
```bash
# Docker container
VECTOR_DB_HOST=milvus
VECTOR_DB_HTTP_PORT=19530
VECTOR_DB_USERNAME=root
VECTOR_DB_PASSWORD=Milvus
VECTOR_DB_CONNECTION_SCHEME=http
```

---

## How to Test Credentials

### Option 1: Using the Inspection Script
```bash
cd datapilotflow-services
source .venv/bin/activate
python ../datapilotflow-persistence/tests/test_vectordb_collections.py
```

### Option 2: Direct Python Test
```python
from pymilvus import connections, utility

# Connect using your settings
connections.connect(
    alias="default",
    host="localhost",
    port=19530,
    user="root",
    password="Milvus",
)

# List collections
collections = utility.list_collections()
print(f"Connected! Found {len(collections)} collections")
```

### Option 3: Using MilvusClientWrapper
```python
from datapilotflow.persistence.vectordb.milvus import MilvusClientWrapper
from datapilotflow.domain.config import settings
from pydantic import BaseModel

class DummyModel(BaseModel):
    text: str

# Will use credentials from settings (env vars or defaults)
client = MilvusClientWrapper(
    model=DummyModel,
    collection_name="test_collection",
    vector_dimension=3072,
)

print(f"Connected to {settings.VECTOR_DB_HOST}:{settings.VECTOR_DB_HTTP_PORT}")
```

---

## Credential Priority (Pydantic Settings)

Pydantic Settings loads configuration in this order (first match wins):

1. **Environment Variables** - Highest priority
   ```bash
   export VECTOR_DB_HOST=prod-milvus.example.com
   ```

2. **.env File** - Mid priority (if present in working directory)
   ```bash
   VECTOR_DB_HOST=staging-milvus.example.com
   ```

3. **Python Defaults** - Lowest priority
   ```python
   default="localhost"
   ```

---

## Security Best Practices

### ❌ Don't Do This
```python
# BAD: Hardcoded credentials
client = MilvusClientWrapper(
    ...,
    milvus_user="root",
    milvus_password="Milvus",  # Visible in source code!
)
```

### ✅ Do This Instead
```python
# GOOD: Use environment variables
# Set in .env or shell environment
client = MilvusClientWrapper(
    ...,
    # Credentials loaded from settings (env vars)
)

# Verify in .gitignore:
# .env
# .env.local
# .env.*.local
```

### 🔒 For Production
1. **Use a secrets manager**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets
   - Google Secret Manager

2. **Enable Milvus authentication**
   ```python
   connections.connect(
       host="prod-milvus.example.com",
       user="your-username",
       password="your-secure-password",  # From secrets manager
   )
   ```

3. **Use HTTPS/TLS**
   ```bash
   VECTOR_DB_CONNECTION_SCHEME=https
   VECTOR_DB_HTTP_PORT=443
   ```

---

## Troubleshooting Connection Issues

### Connection Refused
```
Error: localhost:19530: [Errno 61] Connection refused
```
**Solution:** Ensure Milvus is running
```bash
docker ps | grep milvus
# If not running, start it:
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest
```

### Authentication Failed
```
Error: Unauthorized! Check username/password
```
**Solution:** Verify credentials match Milvus configuration
```bash
# Check environment
echo $VECTOR_DB_USERNAME
echo $VECTOR_DB_PASSWORD

# Or check .env file
cat .env | grep VECTOR_DB
```

### Connection Timeout
```
Error: Timeout when connecting to Milvus
```
**Solution:** Check host and port
```python
# Test connectivity
import socket
socket.create_connection(("localhost", 19530), timeout=5)
```

---

## Related Files

| File | Purpose |
|------|---------|
| [config.py](datapilotflow-domain/src/datapilotflow/domain/config.py) | Settings definition |
| [client.py](datapilotflow-persistence/src/datapilotflow/persistence/vectordb/milvus/client.py) | MilvusClientWrapper |
| [test_vectordb_collections.py](datapilotflow-persistence/tests/test_vectordb_collections.py) | Inspection script |

---

## Summary

- **Credentials source:** Environment variables with hardcoded defaults
- **Default connection:** `http://root:Milvus@localhost:19530`
- **Override method:** Set environment variables before runtime
- **Security:** Always use secrets manager in production
- **Testing:** Use provided inspection script to verify connectivity

