# datapilotflow-dashboard

**React frontend — the web UI for DataPilotFlow.**

Built with React, Vite, and Mantine UI. Communicates with the API over HTTP and WebSocket. Provides all user-facing functionality: knowledge management, ingestion job monitoring, conversational AI, agent configuration, and platform administration.

---

## Responsibility

- Provide the full user interface for the DataPilotFlow platform
- Stream real-time agent responses via WebSocket
- Display job progress, vector status, and processing activity
- Manage knowledge sources, ingestion jobs, and collections
- Administer users, roles, model providers, and MCP tool servers

---

## Page Structure

```
src/pages/
├── auth/
│   └── login/                    # Login form
└── dashboard/
    ├── home/                     # Overview — stats, recent jobs, quick actions
    ├── apps/
    │   ├── knowledge/            # Conversations with knowledge bases
    │   └── knowledge-sources/    # Browse and search knowledge sources
    └── management/
        ├── knowledge/            # Knowledge sources, jobs, collections, monitoring
        ├── model-providers/      # LLM provider configuration
        ├── tools/                # Tool and MCP server registry
        └── users/                # User and role management
```

---

## Key Features

**Knowledge Management**
- Configure crawling sources (web, local files, Confluence)
- Create and run ingestion jobs
- Monitor job status with progress charts and timelines
- Inspect vector collections and individual chunk records

**Conversational AI**
- Start conversations backed by specific knowledge bases
- Streaming responses via WebSocket
- Conversation history

**Platform Administration**
- Manage users and assign roles
- Configure LLM model providers
- Register external MCP servers and manage their tools
- Monitor agent configurations (RAG and Assistant types)

---

## Tech Stack

| Concern | Library |
|---------|---------|
| Framework | React 18 + Vite |
| UI Components | Mantine Core, Mantine Charts, Mantine Dropzone |
| Icons | Tabler Icons, Lucide React, React Icons |
| Data Fetching | TanStack Query + Axios |
| Routing | React Router DOM |
| Rich Text | Tiptap |
| Markdown | react-markdown |
| Flow Diagrams | ReactFlow |
| Tables | mantine-datatable |

---

## Development

```bash
cd datapilotflow-dashboard
npm install
npm run dev
# Opens at http://localhost:5173
```

**Available scripts:**

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run typecheck` | TypeScript type checking |
| `npm run lint` | Run ESLint and Stylelint |
| `npm run test` | Run Vitest tests |

---

## Environment

The dashboard connects to the API at the URL configured during build or via the Vite dev proxy. In Docker, it is served on port `3000` and proxies API calls to `datapilotflow-api-server:8800`.

---

## Docker

In production, the dashboard is built as a static bundle and served from the Docker container on port `3000`. See `docker/services/dashboard/Dockerfile` for the build configuration.
