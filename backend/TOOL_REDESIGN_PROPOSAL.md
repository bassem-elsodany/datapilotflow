# Tool System Redesign Proposal

## Current Problems

### Current Design (BAD):
```python
# 3 separate records for same MCP server
Tool(id="1", name="calculate", mcp_config={
    server_url="http://localhost:8880/mcp",
    tool_name="calculate",
    auth={...},
    description="static description",  # ❌ Goes stale
    tool_schema={...}  # ❌ Goes stale
})

Tool(id="2", name="convert_units", mcp_config={
    server_url="http://localhost:8880/mcp",  # ❌ Duplicate
    tool_name="convert_units",
    auth={...},  # ❌ Duplicate
    description="static description",
    tool_schema={...}
})

Tool(id="3", name="analyze_text", mcp_config={
    server_url="http://localhost:8880/mcp",  # ❌ Duplicate
    tool_name="analyze_text",
    auth={...},  # ❌ Duplicate
    description="static description",
    tool_schema={...}
})
```

**Issues:**
- ❌ Massive duplication (server URL + auth repeated N times)
- ❌ Static descriptions/schemas become stale
- ❌ Can't update auth for all tools at once
- ❌ Wrong domain model (tools belong to servers)

---

## Proposed Design (GOOD)

### New Domain Models:

```python
@dataclass
class MCPServerConfig:
    """MCP Server connection configuration."""
    
    id: str  # UUID
    user_id: str  # Owner
    name: str  # Human-readable name (e.g., "My Utilities Server")
    server_url: str  # http://localhost:8880/mcp
    server_type: str = "http"  # Only HTTP supported
    
    # Authentication (shared by all tools on this server)
    auth_type: Optional[str] = None  # "none", "bearer", "basic", "api_key"
    auth_credentials: Optional[Dict[str, str]] = None
    
    # List of enabled tool names on this server
    enabled_tools: List[str] = field(default_factory=list)  # ["calculate", "convert_units", ...]
    
    # Server metadata
    is_active: bool = True
    timeout: int = 30
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ToolType(str, Enum):
    PROMPT_BASED = "prompt_based"  # LLM-based tool
    MCP_SERVER = "mcp_server"  # Reference to MCP server


@dataclass
class Tool:
    """Unified tool configuration."""
    
    id: str
    user_id: str
    name: str  # Tool identifier for LLM
    display_name: str
    tool_type: ToolType
    is_active: bool = True
    
    # For PROMPT_BASED tools
    prompt_config: Optional[PromptBasedToolConfig] = None
    
    # For MCP_SERVER tools - just reference the server
    mcp_server_id: Optional[str] = None  # Foreign key to MCPServerConfig
    
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Database Schema:

```
Collection: mcp_servers
{
    "id": "server-uuid-123",
    "user_id": "user-123",
    "name": "My Utilities Server",
    "server_url": "http://localhost:8880/mcp",
    "auth_type": "bearer",
    "auth_credentials": {"token": "secret"},
    "enabled_tools": ["calculate", "convert_units", "analyze_text", "get_weather"],
    "is_active": true,
    "timeout": 30,
    "created_at": "2025-11-10T10:00:00Z"
}

Collection: tools
{
    "id": "tool-uuid-456",
    "user_id": "user-123",
    "name": "code_generator",  # For prompt-based
    "display_name": "Code Generator",
    "tool_type": "prompt_based",
    "prompt_config": {
        "system_prompt": "You are a code generator...",
        "temperature": 0.7
    },
    "is_active": true
}

{
    "id": "tool-uuid-789",
    "user_id": "user-123",
    "name": "mcp_utilities",  # Reference to MCP server
    "display_name": "MCP Utilities",
    "tool_type": "mcp_server",
    "mcp_server_id": "server-uuid-123",  # Points to mcp_servers collection
    "is_active": true
}
```

---

## Runtime Behavior

### When executing MCP tool:
```python
# 1. Get tool by name
tool = tool_service.get_tool_by_name("mcp_utilities")

# 2. If tool.tool_type == "mcp_server", load the server config
mcp_server = mcp_server_service.get_server(tool.mcp_server_id)

# 3. Connect to MCP server and fetch LIVE metadata
async with Client(mcp_server.server_url, auth=build_auth(mcp_server)) as client:
    tools_list = await client.list_tools()  # Fresh descriptions/schemas
    
# 4. Filter to enabled tools only
enabled_tools = [t for t in tools_list if t.name in mcp_server.enabled_tools]

# 5. Execute the tool with LIVE schema
result = await client.call_tool(name="calculate", arguments={...})
```

**Benefits:**
- ✅ Tool descriptions/schemas always fresh from MCP server
- ✅ One record per MCP server (no duplication)
- ✅ Easy to update auth for all tools
- ✅ Easy to enable/disable individual tools
- ✅ Correct domain model

---

## Migration Path

1. Create `MCPServerConfig` domain model
2. Create `mcp_servers` collection with DAO/Service
3. Add new API endpoints for MCP server management
4. Update UI to manage servers (not individual tools)
5. Deprecate old `mcp_config` in `Tool` model
6. Migrate existing tool records to new model

---

## UI Changes

### Old Flow (BAD):
```
1. User clicks "Discover Tools" → connects to MCP server
2. User selects 5 tools → creates 5 separate tool records
3. To change auth → must update 5 records
```

### New Flow (GOOD):
```
1. User creates "MCP Server" → enters URL + auth
2. User clicks "Discover Tools" → sees available tools
3. User selects 5 tools → updates ONE server record's enabled_tools list
4. To change auth → update ONE server record
```

---

## Recommendation

**Implement this redesign now before the system goes to production.**

The current design will cause:
- Data inconsistency
- Maintenance nightmare
- Poor performance (duplicate auth configs)
- Confusion for users

This redesign aligns with:
- DRY principle
- Single source of truth (MCP server)
- Proper domain modeling
- Easier maintenance

