# DataPilotFlow v1.0.0 — Initial Public Release

DataPilotFlow is an open, event-driven platform for building and querying enterprise knowledge bases powered by Retrieval-Augmented Generation (RAG). It automates the full pipeline from document ingestion to intelligent, source-cited conversational answers — deployable in minutes with a single Docker Compose command.

---

## What is included

### Core Platform

- **Multi-Agent Orchestration** — A supervisor agent (LangGraph) coordinates a RAG agent, tool calls, and external MCP servers
- **Event-Driven Ingestion** — Asynchronous document processing via RabbitMQ; jobs are non-blocking and resumable
- **Multiple Source Types** — PDF, Markdown, plain text, web crawling (single page, multi-page, full site), and Confluence spaces
- **Vector Search** — Milvus stores and queries high-dimensional embeddings for semantic similarity retrieval
- **MCP Server Exposure** — RAG agent exposes retrieval capabilities as a Model Context Protocol server for external agent integration
- **Real-Time Streaming** — Answers stream to the browser via WebSocket; job progress updates live
- **Tool Registry** — Connect and manage remote MCP tool servers; agents discover and invoke tools dynamically
- **Role-Based Access Control** — Admin, User, and Viewer roles with JWT authentication
- **Production Docker Deployment** — Nine containerized services with health checks, dependency ordering, and persistent data volumes

### Modules

| Module | Description |
|--------|-------------|
| `datapilotflow-domain` | Core Pydantic domain models and configuration |
| `datapilotflow-infrastructure` | MongoDB, Milvus, RabbitMQ, MinIO clients and DAOs |
| `datapilotflow-services` | Business logic, authentication, event publishing |
| `datapilotflow-api` | FastAPI REST server + WebSocket — Port 8800 |
| `datapilotflow-rag-agent` | RAG retrieval agent with MCP server — Port 65510 |
| `datapilotflow-assistant-agent` | Supervisor agent and multi-turn conversations |
| `datapilotflow-events` | RabbitMQ event listeners and publishers |
| `datapilotflow-processors` | Text extraction, chunking, embedding pipeline |
| `datapilotflow-dashboard` | React + Vite + Mantine UI frontend — Port 3000 |

---

## Quick Start

**Requirements**: Docker, Docker Compose, 10 GB free disk space.

```bash
git clone https://github.com/bassem-elsodany/datapilotflow.git
cd datapilotflow/docker
docker-compose up -d
```

Open [http://localhost:3000](http://localhost:3000) and log in with the default admin credentials:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |
| Email | `admin@datapilotflow.com` |
| Role | Platform Admin |

> Change the default password immediately after first login via **User Management > My Profile**.

Full documentation: [README](https://github.com/bassem-elsodany/datapilotflow/blob/main/README.md)

---

## License

Free for individuals — personal use, education, and non-commercial research under Apache 2.0 with Commons Clause.

Enterprise and commercial use requires a separate license. Contact: flowdatapilot@gmail.com
