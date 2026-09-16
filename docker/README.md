# docker

**Container orchestration — nine services, one command.**

This directory contains the `docker-compose.yml` and all Dockerfiles for the DataPilotFlow production deployment.

---

## Services

| Container | Image | Port | Description |
|-----------|-------|------|-------------|
| `datapilotflow-api-server` | Built from `services/api/Dockerfile` | 8800 | REST API + WebSocket |
| `datapilotflow-dashboard` | Built from `services/dashboard/Dockerfile` | 3000 | React frontend |
| `datapilotflow-event-listeners` | Built from `services/events/Dockerfile` | — | Background job processor |
| `datapilotflow-mcp-rag` | Built from `services/mcp-agent/Dockerfile` | 65510 | RAG MCP server |
| `datapilotflow-mongodb` | `mongo:7.0` | 27020 | Document store |
| `datapilotflow-rabbitmq` | `rabbitmq:3.12-management` | 5675 / 15675 | Message broker |
| `datapilotflow-milvus` | `milvusdb/milvus:v2.6.2` | 19530 / 9091 | Vector database |
| `datapilotflow-milvus-minio` | `quay.io/minio/minio` | 9000 / 9002 | Object storage for Milvus |
| `datapilotflow-milvus-etcd` | `quay.io/coreos/etcd:v3.5.18` | 2379 | Metadata store for Milvus |

---

## Startup Order

Services start in dependency order with health checks at each stage:

```
Stage 1 — Infrastructure (no dependencies)
  mongodb, rabbitmq, milvus-etcd, milvus-minio

Stage 2 — Vector database (depends on etcd + minio)
  milvus

Stage 3 — Application services (depend on infrastructure)
  api-server        (requires mongodb, milvus, rabbitmq)
  event-listeners   (requires mongodb, milvus, rabbitmq)
  mcp-rag-agent     (requires milvus, mongodb)

Stage 4 — Frontend (depends on api)
  dashboard
```

---

## Directory Structure

```
docker/
├── docker-compose.yml            # Full stack definition
├── docker-compose.dev.yml        # Development overrides
├── Dockerfile                    # Shared base Dockerfile
├── startup.sh                    # Startup helper script
├── mongo-init/
│   └── init-datapilotflow.js     # MongoDB database initialization
├── config/                       # Service configuration files
└── services/
    ├── api/Dockerfile            # API server image
    ├── dashboard/Dockerfile      # Dashboard image
    ├── events/Dockerfile         # Event listeners image
    └── mcp-agent/Dockerfile      # RAG MCP agent image
```

---

## Starting the Stack

```bash
cd docker
docker-compose up -d

# Check all services are healthy
docker-compose ps

# Follow logs for a specific service
docker-compose logs -f datapilotflow-api-server
docker-compose logs -f datapilotflow-event-listeners
```

---

## Stopping and Cleanup

```bash
# Stop all services (preserves data volumes)
docker-compose down

# Stop and remove all data volumes
docker-compose down -v
```

---

## Data Persistence

All stateful data is stored in `../data/` relative to the `docker/` directory:

| Service | Volume Path |
|---------|-------------|
| MongoDB | `../data/datapilotflow-mongodb` |
| Milvus | `../data/datapilotflow-milvus` |
| Milvus MinIO | `../data/datapilotflow-milvus-minio` |
| Milvus ETcd | `../data/datapilotflow-milvus-etcd` |
| RabbitMQ | `../data/datapilotflow-rabbitmq` |
| API logs | `../logs/api` |
| Event listener logs | `../logs/event-listeners` |
| MCP agent logs | `../logs/mcp-rag-agent` |
| File uploads | `../data/upload` |

---

## Health Checks

Each service defines a health check:

| Service | Check |
|---------|-------|
| API Server | `GET http://localhost:8800/health` |
| Dashboard | `wget http://localhost:3000/` |
| RAG MCP | `GET http://localhost:65510/health` |
| MongoDB | `mongosh --eval "db.adminCommand('ping')"` |
| RabbitMQ | `rabbitmq-diagnostics ping` |
| Milvus | `GET http://localhost:9091/healthz` |
| MinIO | `GET http://localhost:9000/minio/health/live` |
| ETcd | `etcdctl endpoint health` |

---

## Configuration

All environment variables are set directly in `docker-compose.yml`. To change credentials or connection settings, edit the `environment` block of the relevant service before starting the stack. See the root [README](../README.md#configuration) for the full variable reference.
