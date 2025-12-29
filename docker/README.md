# DataPilotFlow Docker Deployment

Complete Docker containerization of DataPilotFlow with separate services for API, Dashboard, Event Listeners, and RAG MCP Server.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DataPilotFlow Docker Architecture                   │
└─────────────────────────────────────────────────────────────────────────┘

                          External Access (Host Machine)
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────────┐ ┌──────────────┐ ┌─────────────┐
            │               │ │              │ │             │
            │   Dashboard   │ │  API Server  │ │  RAG MCP    │
            │  Port 3000    │ │  Port 8800   │ │ Port 65510  │
            │   (Vite React)│ │  (Python)    │ │ (Python)    │
            └───────┬───────┘ └──────┬───────┘ └────┬────────┘
                    │                │              │
                    └────────────────┼──────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌─────────────────────────┐      ┌─────────────────────┐
        │  Event Listeners        │      │  Infrastructure     │
        │  (No External Port)     │      │  Services           │
        │  - Job Events           │      │                     │
        │  - File Upload Events   │      │  ┌──────────────┐   │
        │  - Notification Events  │      │  │  MongoDB     │   │
        └────────┬────────────────┘      │  │ (Port 27020) │   │
                 │                       │  └──────────────┘   │
                 └───────────────────────┼──────────────────┐  │
                                         │                  │  │
                       ┌─────────────────┴──────────────┐   │  │
                       │                                │   │  │
                       ▼                                ▼   ▼  │
        ┌──────────────────────────┐  ┌──────────────────────┐│
        │  RabbitMQ Message Broker │  │  Milvus Vector DB    ││
        │  (Port 5675 external)    │  │  (Port 19530)        ││
        │  (Port 5672 internal)    │  │  + MinIO             ││
        │  + Management UI         │  │  + ETcd              ││
        │  (Port 15675)            │  └──────────────────────┘│
        └──────────────────────────┘                          │
                                                              │
                       Docker Network Bridge                  │
                     (datapilotflow-network)                │
                                                              │
└──────────────────────────────────────────────────────────────┘
                      Docker Compose (9 Services)
```

## Service Dependencies

```
┌─ Startup Order ─────────────────────────────────────────┐
│                                                          │
│ 1. Infrastructure Services (Initial)                    │
│    └─ milvus-etcd                                       │
│    └─ milvus-minio                                      │
│                                                          │
│ 2. Core Infrastructure                                  │
│    └─ MongoDB (depends on nothing)                      │
│    └─ RabbitMQ (depends on nothing)                     │
│    └─ Milvus (depends on etcd, minio)                   │
│                                                          │
│ 3. Application Services (Parallel)                      │
│    ├─ API (depends on MongoDB, Milvus, RabbitMQ)       │
│    ├─ Event Listeners (depends on RabbitMQ, MongoDB)   │
│    └─ RAG MCP (depends on Milvus, MongoDB)             │
│                                                          │
│ 4. Frontend Layer (Sequential)                          │
│    └─ Dashboard (depends on API healthy)               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available
- 50GB disk space for data volumes

### Start All Services

```bash
cd docker
docker-compose up -d
```

### Verify All Services Are Running

```bash
docker-compose ps
```

Expected output:
```
NAME                               STATUS              PORTS
datapilotflow-api-server           healthy (starting)  0.0.0.0:8800->8800/tcp
datapilotflow-dashboard-frontend   healthy (starting)  0.0.0.0:3000->3000/tcp
datapilotflow-event-listeners      running             (no ports)
datapilotflow-mcp-rag              healthy (starting)  0.0.0.0:65510->65510/tcp
datapilotflow-mongodb          healthy             0.0.0.0:27020->27017/tcp
datapilotflow-rabbitmq         healthy             0.0.0.0:5675->5672/tcp
datapilotflow-milvus           healthy             0.0.0.0:19530->19530/tcp
datapilotflow-milvus-etcd      healthy             (no ports)
datapilotflow-milvus-minio     healthy             (no ports)
```

## Access Services

Once all services are healthy, access them at:

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:3000 | Frontend web application |
| **API Server** | http://localhost:8800 | REST API endpoints |
| **API Health** | http://localhost:8800/health | API health check |
| **RabbitMQ UI** | http://localhost:15675 | Message queue management (user: datapilotflow, pass: datapilotflow123) |
| **MinIO Console** | http://localhost:9002 | Object storage management (user: minioadmin, pass: minioadmin) |
| **Milvus WebUI** | http://localhost:9091 | Vector database management |

## Application Services

### 1. API Server (Port 8800)

- **Purpose**: REST API backend for DataPilotFlow
- **Docker Image**: Python 3.13-slim
- **Dockerfile**: `docker/services/api/Dockerfile`
- **Dependencies**: MongoDB, Milvus, RabbitMQ
- **Entry Point**: `run_api_server.py`
- **Health Check**: HTTP GET `/health`

**Key Environment Variables**:
```env
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8800
MONGO_HOST=mongodb
VECTOR_DB_HOST=milvus
RABBITMQ_HOST=rabbitmq
```

### 2. Dashboard (Port 3000)

- **Purpose**: Frontend web application for user interface
- **Docker Image**: Node.js 20-alpine (multi-stage build)
- **Dockerfile**: `docker/services/dashboard/Dockerfile`
- **Dependencies**: API Server (service_healthy)
- **Technology**: Vite + React + TypeScript
- **Health Check**: HTTP GET on root `/`

**Build Process**:
- Stage 1: Build Vite app → creates `/dist`
- Stage 2: Serve static files with `serve` package

### 3. Event Listeners (No External Port)

- **Purpose**: Background event processing
- **Docker Image**: Python 3.13-slim
- **Dockerfile**: `docker/services/events/Dockerfile`
- **Dependencies**: RabbitMQ, MongoDB
- **Entry Point**: `run_all_event_listeners.py`
- **Internal Communication**: RabbitMQ message queue

**Event Types Processed**:
- Job Events
- File Upload Events
- Notification Events

### 4. RAG MCP Server (Port 65510)

- **Purpose**: Knowledge retrieval via Model Context Protocol
- **Docker Image**: Python 3.13-slim
- **Dockerfile**: `docker/services/mcp-agent/Dockerfile`
- **Dependencies**: Milvus, MongoDB
- **Entry Point**: `run_rag_mcp_server.py`
- **Health Check**: HTTP GET on root `/`

**Key Environment Variables**:
```env
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=65510
VECTOR_DB_HOST=milvus
```

## Infrastructure Services

### MongoDB (Port 27020)

- **Image**: mongo:7.0
- **Purpose**: Document database for application data
- **Port Mapping**: 27020 (external) → 27017 (internal)
- **Data Volume**: `../data/datapilotflow-mongodb/`
- **Health Check**: MongoDB ping command

### RabbitMQ (Port 5675)

- **Image**: rabbitmq:3.12-management
- **Purpose**: Message broker for event-driven architecture
- **Ports**:
  - 5675 (external) → 5672 (internal AMQP)
  - 15675 (external) → 15672 (internal Management UI)
- **Data Volume**: `../data/datapilotflow-rabbitmq/`
- **Credentials**: datapilotflow / datapilotflow123
- **Health Check**: RabbitMQ diagnostics ping

### Milvus (Port 19530)

- **Image**: milvus:latest
- **Purpose**: Vector database for similarity search
- **Port**: 19530
- **Dependencies**:
  - Milvus ETcd (metadata storage)
  - Milvus MinIO (object storage)
- **Data Volumes**:
  - `../data/datapilotflow-milvus/`
  - `../data/datapilotflow-milvus-etcd/`
  - `../data/datapilotflow-milvus-minio/`
- **Health Check**: HTTP health check endpoint

## Common Operations

### View Logs

```bash
# Dashboard logs
docker-compose logs -f dashboard

# API Server logs
docker-compose logs -f api

# Event Listeners logs
docker-compose logs -f event-listeners

# RAG MCP Server logs
docker-compose logs -f mcp-rag-agent

# All services logs
docker-compose logs -f

# Specific number of lines
docker-compose logs --tail=100 api
```

### Restart Services

```bash
# Restart individual service
docker-compose restart dashboard
docker-compose restart api
docker-compose restart event-listeners

# Restart all application services
docker-compose restart api dashboard event-listeners mcp-rag-agent

# Restart all services (including infrastructure)
docker-compose restart
```

### Stop Services

```bash
# Stop all services (keeps containers)
docker-compose stop

# Stop specific service
docker-compose stop api

# Stop and remove containers (keeps volumes/data)
docker-compose down

# Stop and remove everything including volumes (deletes all data!)
docker-compose down -v
```

### Execute Commands in Containers

```bash
# Open shell in API container
docker-compose exec api bash

# Run command in container
docker-compose exec api python --version

# Connect to MongoDB
docker-compose exec mongodb mongosh --host mongodb
```

## Network Architecture

All services communicate through a Docker bridge network: `datapilotflow-network`

**Internal Hostnames** (accessible between containers):
- `api` → datapilotflow-api-server:8800
- `dashboard` → datapilotflow-dashboard:3000
- `event-listeners` → datapilotflow-event-listeners (no port)
- `mcp-rag-agent` → datapilotflow-mcp-rag:65510
- `mongodb` → datapilotflow-mongodb:27017
- `rabbitmq` → datapilotflow-rabbitmq:5672
- `milvus` → datapilotflow-milvus:19530

## Health Checks

Each service has health checks configured:

```bash
# Check health of specific service
docker inspect datapilotflow-api-server | grep -A 5 "Health"

# Monitor health status
watch docker-compose ps

# Manual health checks
curl http://localhost:8800/health      # API
curl http://localhost:3000/            # Dashboard
curl http://localhost:65510/           # RAG MCP
```

## Data Persistence

All data is persisted in the `../data/` directory:

```
../data/
├── datapilotflow-mongodb/        # MongoDB data files
├── datapilotflow-rabbitmq/       # RabbitMQ data and logs
├── datapilotflow-milvus/         # Milvus vector data
├── datapilotflow-milvus-etcd/    # Milvus metadata
└── datapilotflow-milvus-minio/   # Milvus object storage
```

### Backup Data

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /tmp/backup

# Backup entire data directory
tar -czf datapilotflow-backup.tar.gz ../data/
```

### Reset All Data

**WARNING**: This deletes all data!

```bash
docker-compose down -v
rm -rf ../data/
```

## Scaling Services

### Scale Event Listeners

```bash
# Run 3 instances of event listeners
docker-compose up -d --scale event-listeners=3
```

### Scale API Server

```bash
# Run 2 instances of API server (requires load balancer)
docker-compose up -d --scale api=2
```

Note: Scaling requires an external load balancer (nginx, HAProxy) for request distribution.

## Performance Optimization

### Increase MongoDB Performance

```bash
docker-compose exec mongodb mongosh -u datapilotflow -p datapilotflow123 << 'EOF'
use datapilotflow
db.conversations.createIndex({ user_id: 1 })
db.messages.createIndex({ conversation_id: 1 })
db.knowledge_chunks.createIndex({ source: 1 })
EOF
```

### Configure Milvus Cache

Edit `docker-compose.yml` and add to milvus environment:
```yaml
services:
  milvus:
    environment:
      - QUERYNODE_CACHE_SIZE=2147483648  # 2GB cache
```

### RabbitMQ Optimization

```bash
docker-compose exec rabbitmq rabbitmqctl set_parameter global max_page_size 134217728
```

## Troubleshooting

### Dashboard won't start

```bash
# Check API is healthy first
docker-compose ps api

# Check dashboard logs
docker-compose logs dashboard

# Verify API is accessible
curl http://localhost:8800/health
```

### Event Listeners crashing

```bash
# Check logs
docker-compose logs event-listeners

# Verify RabbitMQ is running
docker-compose exec rabbitmq rabbitmq-diagnostics ping

# Check message queues
docker-compose exec rabbitmq rabbitmqctl list_queues
```

### API can't connect to database

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Test MongoDB connection
docker-compose exec api mongosh --host mongodb --eval "db.adminCommand('ping')"

# Check environment variables
docker-compose exec api env | grep MONGO
```

### High memory usage

```bash
# Check container memory
docker stats

# View specific service memory
docker stats datapilotflow-api-server

# Limit container memory in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Port conflicts

```bash
# Check which process is using a port
lsof -i :3000   # Dashboard
lsof -i :8800   # API
lsof -i :5675   # RabbitMQ
```

## Production Checklist

- [ ] Change default passwords (MongoDB, RabbitMQ, MinIO)
- [ ] Configure SSL/TLS certificates
- [ ] Set up persistent volume backups
- [ ] Configure logging aggregation (ELK, Splunk, etc.)
- [ ] Set resource limits on containers
- [ ] Configure monitoring (Prometheus, Grafana)
- [ ] Set up automated alerts
- [ ] Test failover procedures
- [ ] Document runbooks for common issues
- [ ] Plan for database maintenance windows
- [ ] Set up database replication
- [ ] Configure reverse proxy/load balancer
- [ ] Enable Docker security scanning
- [ ] Set up container image registry

## File Structure

```
docker/
├── README.md                          # This file
├── DOCKER.md                          # Detailed deployment guide
├── docker-compose.yml                 # Main orchestration file
├── services/
│   ├── api/
│   │   └── Dockerfile                 # API server container
│   ├── dashboard/
│   │   └── Dockerfile                 # Frontend container
│   ├── events/
│   │   └── Dockerfile                 # Event listeners container
│   └── mcp-agent/
│       └── Dockerfile                 # RAG MCP server container
├── config/
│   └── (configuration files)
└── mongo-init/
    └── (MongoDB initialization scripts)
```

## Command Reference

```bash
# Start/Stop
docker-compose up -d                   # Start all services
docker-compose stop                    # Stop all services
docker-compose down                    # Stop and remove containers
docker-compose down -v                 # Stop and remove everything

# Status
docker-compose ps                      # Service status
docker-compose ps service-name         # Specific service status
docker stats                           # Resource usage

# Logs
docker-compose logs -f                 # All logs (follow)
docker-compose logs -f service-name    # Specific service logs
docker-compose logs --tail=100 api     # Last 100 lines

# Build
docker-compose build                   # Build all images
docker-compose build service-name      # Build specific service
docker-compose up -d --build api       # Build and restart

# Restart
docker-compose restart                 # Restart all
docker-compose restart service-name    # Restart specific service

# Execute
docker-compose exec service bash       # Shell access
docker-compose exec service cmd        # Run command

# Cleanup
docker image prune                     # Remove unused images
docker volume prune                    # Remove unused volumes
docker system prune                    # Remove all unused resources
```

## Environment Variables

All services use environment variables defined in `docker-compose.yml`. Modify them for:
- Database connections
- Service ports
- API keys
- Logging levels

See [DOCKER.md](./DOCKER.md) for complete list of per-service environment variables.

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MongoDB Docker Guide](https://hub.docker.com/_/mongo)
- [RabbitMQ Docker Guide](https://hub.docker.com/_/rabbitmq)
- [Milvus Docker Guide](https://milvus.io/docs)
- [DOCKER.md](./DOCKER.md) - Detailed deployment guide

## Support

For issues or questions:
1. Check logs: `docker-compose logs [service_name]`
2. Verify service health: `docker-compose ps`
3. Check environment variables: `docker-compose config`
4. Review this documentation
5. Consult detailed [DOCKER.md](./DOCKER.md) guide
