# DataPilotFlow Docker Deployment Guide

This guide covers deploying DataPilotFlow using Docker containers with separate services for API, Event Listeners, RAG MCP Server, and Dashboard.

## Overview

DataPilotFlow is deployed as 5 independent services plus infrastructure:

### Application Services
- **API Server** (Port 8800) - REST API for client requests
- **Dashboard** (Port 3000) - Frontend web application
- **Event Listeners** (No exposed port) - Background event processing
- **RAG MCP Server** (Port 65510) - Knowledge retrieval service

### Infrastructure Services
- **MongoDB** (Port 27020) - Document database
- **RabbitMQ** (Port 5675) - Message broker
- **Milvus** (Port 19530) - Vector database (with etcd + MinIO)

---

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

Verify all services are healthy:
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
datapilotflow-mongodb              healthy             0.0.0.0:27020->27017/tcp
datapilotflow-rabbitmq             healthy             0.0.0.0:5675->5672/tcp
datapilotflow-milvus               healthy             0.0.0.0:19530->19530/tcp
```

### Access Services

- **Dashboard**: http://localhost:3000
- **API Server**: http://localhost:8800
- **API Health**: http://localhost:8800/health
- **RabbitMQ Management**: http://localhost:15675 (user: datapilotflow, pass: datapilotflow123)
- **MinIO Console**: http://localhost:9002 (user: minioadmin, pass: minioadmin)
- **Milvus WebUI**: http://localhost:9091

---

## Docker Architecture

### Directory Structure

```
docker/
├── Dockerfile (original - kept for reference)
├── docker-compose.yml (main orchestration)
├── services/
│   ├── api/
│   │   └── Dockerfile (API server only)
│   ├── dashboard/
│   │   └── Dockerfile (Frontend web application)
│   ├── events/
│   │   └── Dockerfile (event listeners)
│   └── mcp-agent/
│       └── Dockerfile (RAG MCP server)
├── config/
│   └── (configuration files)
├── mongo-init/
│   └── (MongoDB initialization scripts)
└── DOCKER.md (this file)
```

### Service Dependencies

```
api
├── mongodb (healthy)
├── milvus (healthy)
└── rabbitmq (healthy)

dashboard
└── api (healthy)

event-listeners
├── rabbitmq (healthy)
└── mongodb (healthy)

mcp-rag-agent
├── milvus (healthy)
└── mongodb (healthy)

milvus
├── milvus-etcd
└── milvus-minio
```

---

## Environment Variables

### API Server (`api`)

```env
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8800
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB_NAME=datapilotflow
VECTOR_DB_HOST=milvus
VECTOR_DB_HTTP_PORT=19530
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=datapilotflow
RABBITMQ_PASS=datapilotflow123
```

### Event Listeners (`event-listeners`)

```env
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=datapilotflow
RABBITMQ_PASS=datapilotflow123
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB_NAME=datapilotflow
LOG_LEVEL=INFO
```

### RAG MCP Server (`mcp-rag-agent`)

```env
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=65510
VECTOR_DB_HOST=milvus
VECTOR_DB_HTTP_PORT=19530
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB_NAME=datapilotflow
```

---

## Common Operations

### View Logs

**Dashboard logs:**
```bash
docker-compose logs -f dashboard
```

**API Server logs:**
```bash
docker-compose logs -f api
```

**Event Listeners logs:**
```bash
docker-compose logs -f event-listeners
```

**RAG MCP Server logs:**
```bash
docker-compose logs -f mcp-rag-agent
```

**All services:**
```bash
docker-compose logs -f
```

### Restart Services

**Restart dashboard only:**
```bash
docker-compose restart dashboard
```

**Restart API server only:**
```bash
docker-compose restart api
```

**Restart event listeners only:**
```bash
docker-compose restart event-listeners
```

**Restart all application services:**
```bash
docker-compose restart api dashboard event-listeners mcp-rag-agent
```

**Restart all services (including infrastructure):**
```bash
docker-compose restart
```

### Stop Services

**Stop all services:**
```bash
docker-compose stop
```

**Stop specific service:**
```bash
docker-compose stop api
```

### Remove Services

**Remove all containers (keeps volumes):**
```bash
docker-compose down
```

**Remove all containers and volumes:**
```bash
docker-compose down -v
```

### Rebuild Images

**Rebuild API service:**
```bash
docker-compose build api
```

**Rebuild all application services:**
```bash
docker-compose build api event-listeners mcp-rag-agent
```

**Rebuild and restart:**
```bash
docker-compose up -d --build api
```

---

## Health Checks

Each service has health checks configured. View health status:

```bash
docker-compose ps
```

Check specific service health:
```bash
docker inspect datapilotflow-api-server | grep -A 5 "Health"
```

Manual health checks:
```bash
# API Server
curl http://localhost:8800/health

# RabbitMQ
curl -u datapilotflow:datapilotflow123 http://localhost:15675/api/health/checks/alarms

# Milvus
curl http://localhost:9091/healthz

# MongoDB
mongosh --host localhost:27020 -u datapilotflow -p datapilotflow123 --eval "db.adminCommand('ping')"
```

---

## Scaling Services

### Scale Event Listeners

Event listeners can be scaled to handle higher throughput:

```bash
# Run 3 instances of event listeners
docker-compose up -d --scale event-listeners=3
```

Note: Uses port mapping with incremented ports (event-listeners, event-listeners_2, event-listeners_3)

### Scale API Server

For high-traffic scenarios, scale the API:

```bash
# Run 2 instances of API server (requires load balancer)
docker-compose up -d --scale api=2
```

Note: Requires external load balancer (nginx, HAProxy) for request distribution.

---

## Data Persistence

### Data Volumes

All data is persisted in `../data/` directory:

```
../data/
├── datapilotflow-mongodb/     (MongoDB data)
├── datapilotflow-rabbitmq/    (RabbitMQ data)
├── datapilotflow-milvus/      (Milvus vector data)
├── datapilotflow-milvus-etcd/ (Milvus metadata)
└── datapilotflow-milvus-minio/ (Milvus object storage)
```

### Backup Data

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /tmp/backup

# Backup Milvus
docker-compose exec milvus-minio mc mirror minio/data ./backup/minio
```

### Reset Data

WARNING: This deletes all data!

```bash
docker-compose down -v
```

---

## Troubleshooting

### Service won't start

1. Check logs:
```bash
docker-compose logs api
```

2. Verify dependencies are healthy:
```bash
docker-compose ps
```

3. Check port conflicts:
```bash
lsof -i :8800  # Check if port 8800 is in use
```

### Event Listeners crashing

1. Check RabbitMQ connectivity:
```bash
docker-compose logs event-listeners
```

2. Verify RabbitMQ is running:
```bash
docker-compose exec rabbitmq rabbitmq-diagnostics ping
```

3. Check message queues:
```bash
docker-compose exec rabbitmq rabbitmqctl list_queues
```

### API Server can't connect to database

1. Check MongoDB:
```bash
docker-compose logs mongodb
```

2. Test MongoDB connection:
```bash
docker-compose exec api mongosh --host mongodb --eval "db.adminCommand('ping')"
```

3. Verify environment variables:
```bash
docker-compose exec api env | grep MONGO
```

### High memory usage

1. Check container memory:
```bash
docker stats
```

2. Limit container memory in docker-compose.yml:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

3. Restart service:
```bash
docker-compose restart api
```

---

## Performance Optimization

### Database Indexes

Create MongoDB indexes for better performance:

```bash
docker-compose exec mongodb mongosh -u datapilotflow -p datapilotflow123 << 'EOF'
use datapilotflow
db.conversations.createIndex({ user_id: 1 })
db.messages.createIndex({ conversation_id: 1 })
db.knowledge_chunks.createIndex({ source: 1 })
EOF
```

### Vector Search Tuning

Configure Milvus parameters in environment:

```yaml
services:
  milvus:
    environment:
      - COMMON_STORAGETYPE=local
      - QUERYNODE_CACHE_SIZE=2147483648  # 2GB cache
```

### RabbitMQ Optimization

Configure RabbitMQ for high throughput:

```bash
docker-compose exec rabbitmq rabbitmqctl set_parameter global max_page_size 134217728
```

---

## Production Deployment Checklist

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
- [ ] Set up database replication (optional)
- [ ] Configure reverse proxy/load balancer

---

## Docker Compose Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Check service status
docker-compose ps

# Execute command in container
docker-compose exec [service_name] [command]

# Build images
docker-compose build [service_name]

# Restart services
docker-compose restart [service_name]

# View resource usage
docker stats

# Clean up unused images
docker image prune

# Clean up unused volumes
docker volume prune
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MongoDB Docker Guide](https://hub.docker.com/_/mongo)
- [RabbitMQ Docker Guide](https://hub.docker.com/_/rabbitmq)
- [Milvus Docker Guide](https://milvus.io/docs)

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs [service_name]`
2. Review this documentation
3. Check service health: `docker-compose ps`
4. Verify environment variables: `docker-compose config`
5. Consult DataPilotFlow documentation

Last updated: 2025-12-29
