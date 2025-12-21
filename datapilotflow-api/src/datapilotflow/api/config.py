"""
DataPilotFlow API Configuration.

This configuration is specific to the API exposure layer.
Infrastructure settings are duplicated here for independent deployment.
Business logic settings are shared with domain config.
"""

from typing import Optional
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API-specific configuration with independent infrastructure settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_default=True,
    )

    # ============================================================================
    # API-Specific Settings
    # ============================================================================

    API_SERVER_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_SERVER_PORT: int = Field(
        default=65500, description="API server port", ge=1, le=65535
    )
    WEBSOCKET_TIMEOUT: int = Field(
        default=60, description="WebSocket timeout in seconds"
    )

    # API Version configuration
    # To change API version, simply update this value (e.g., "v2", "v3")
    API_VERSION: str = Field(default="v1", description="API version")

    # ============================================================================
    # MongoDB Infrastructure (Duplicated for Independence)
    # ============================================================================

    MONGO_HOST: str = Field(default="localhost", description="MongoDB host")
    MONGO_PORT: int = Field(default=27017, description="MongoDB port", ge=1, le=65535)
    MONGO_DB_NAME: str = Field(default="datapilotflow", description="MongoDB database")
    MONGO_USER: Optional[str] = Field(default=None, description="MongoDB username")
    MONGO_PASS: Optional[str] = Field(default=None, description="MongoDB password")

    MONGO_MAX_POOL_SIZE: int = Field(
        default=10, description="MongoDB max pool size", ge=1, le=100
    )
    MONGO_MIN_POOL_SIZE: int = Field(
        default=1, description="MongoDB min pool size", ge=0, le=50
    )
    MONGO_MAX_IDLE_TIME_MS: int = Field(
        default=30000, description="MongoDB max idle time (ms)", ge=1000, le=300000
    )
    MONGO_CONNECT_TIMEOUT_MS: int = Field(
        default=20000, description="MongoDB connection timeout (ms)", ge=1000, le=60000
    )
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = Field(
        default=5000,
        description="MongoDB server selection timeout (ms)",
        ge=1000,
        le=30000,
    )

    MONGO_AGENT_STATE_CHECKPOINT_ENABLED: bool = Field(
        default=False, description="Enable MongoDB agent state checkpointing"
    )
    MONGO_AGENT_STATE_CHECKPOINT_DB_NAME: str = Field(
        default="datapilotflow_agent", description="Checkpoint database name"
    )
    MONGO_AGENT_STATE_CHECKPOINT_COLLECTION: str = Field(
        default="datapilotflow_agent_state_checkpoints",
        description="Checkpoint collection name",
    )
    MONGO_AGENT_STATE_WRITES_COLLECTION: str = Field(
        default="datapilotflow_agent_state_writes", description="Writes collection name"
    )

    @computed_field
    @property
    def MONGO_CONN_STR(self) -> str:
        """MongoDB connection string."""
        if self.MONGO_USER and self.MONGO_PASS:
            user = quote_plus(self.MONGO_USER)
            pw = quote_plus(self.MONGO_PASS)
            return f"mongodb://{user}:{pw}@{self.MONGO_HOST}:{self.MONGO_PORT}/admin"
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB_NAME}"

    # ============================================================================
    # Vector Database Infrastructure (Duplicated for Independence)
    # ============================================================================

    VECTOR_DB_HOST: str = Field(default="localhost", description="Vector DB host")
    VECTOR_DB_HTTP_PORT: int = Field(
        default=19530, description="Vector DB HTTP port", ge=1, le=65535
    )
    VECTOR_DB_USERNAME: str = Field(default="root", description="Vector DB username")
    VECTOR_DB_PASSWORD: str = Field(default="Milvus", description="Vector DB password")
    VECTOR_DB_CONNECTION_SCHEME: str = Field(
        default="http", description="Vector DB connection scheme"
    )

    # ============================================================================
    # JWT Configuration
    # ============================================================================

    JWT_SECRET_KEY: str = Field(
        default="supersecret", description="JWT secret key", min_length=1
    )

    # ============================================================================
    # Business Logic Settings (Re-declared to load from .env)
    # ============================================================================

    # RAG Configuration
    RAG_TOP_K: int = Field(
        default=5, description="Number of top documents to retrieve", ge=1, le=20
    )
    RAG_SIMILARITY_THRESHOLD: float = Field(
        default=0.6,
        description="Similarity threshold for filtering RAG results",
        ge=0.0,
        le=1.0,
    )

    # Agent Tracing
    AGENT_TRACING_ENABLED: bool = Field(
        default=False, description="Enable agent tracing"
    )
    AGENT_TRACING_API_KEY: Optional[str] = Field(
        default=None, description="Agent tracing API key"
    )
    AGENT_TRACING_URL: str = Field(
        default="http://localhost:5173/api", description="Agent tracing URL"
    )
    AGENT_TRACING_PROJECT_NAME: str = Field(
        default="datapilotflow", description="Agent tracing project name"
    )
    AGENT_TRACING_DEFAULT_ENVIRONMENT: str = Field(
        default="development", description="Agent tracing environment"
    )

    # File Management
    RAG_FILE_UPLOAD_INBOUND_DIR: str = Field(
        default="./upload/inbound", description="Inbound upload directory"
    )
    RAG_FILE_UPLOAD_ARCHIVE_DIR: str = Field(
        default="./upload/archive", description="Archive upload directory"
    )
    RAG_FILE_UPLOAD_FAILED_DIR: str = Field(
        default="./upload/failed", description="Failed upload directory"
    )
    RAG_FILE_UPLOAD_OUTPUT_DIR: str = Field(
        default="./upload/output", description="Output upload directory"
    )
    RAG_INGESTION_JOBS_OUTPUT_DATA_DIR: str = Field(
        default="./ingestion_jobs_output_data",
        description="Ingestion jobs output directory",
    )

    # Knowledge Base
    KNOWLEDGE_METADATA_FILE_NAME: str = Field(
        default="config/knowledge_metadata.json", description="Knowledge metadata file"
    )


# Global API settings instance
settings = APISettings()

# API Constants derived from settings
API_PREFIX = f"/api/{settings.API_VERSION}"
API_CONFIG = {
    "version": settings.API_VERSION,
    "prefix": API_PREFIX,
    "title": "DataPilotFlow API",
    "description": "API for DataPilotFlow interview management system",
    "version_info": "1.0.0",
}
