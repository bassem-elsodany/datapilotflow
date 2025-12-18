import sys
import time
from enum import Enum
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus, urlparse

from loguru import logger
from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Remove default handler if it exists
try:
    logger.remove(0)
except ValueError:
    pass  # Handler doesn't exist, which is fine

logger.add(
    sys.stderr,
    format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {name} | {file}:{line} | {message} | {extra}",
    level="INFO",
)
logger.add(
    "logs/datapilotflow.log",
    format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {name} | {file}:{line} | {message} | {extra}",
    level="DEBUG",
    rotation="00:00",
    retention="30 days",
    compression="zip",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="",  # No prefix for environment variables
        validate_default=True,
    )

    # --- API Configuration ---
    API_SERVER_HOST: str = Field(
        default="0.0.0.0", description="API server host", min_length=1
    )
    # API Configuration
    API_SERVER_PORT: int = Field(
        default=65500, description="API server port", ge=1, le=65535
    )

    # WebSocket timeout configuration
    WEBSOCKET_TIMEOUT: int = Field(
        default=60, description="WebSocket timeout in seconds"
    )

    # --- RAG MCP Server Configuration ---
    RAG_MCP_HOST: str = Field(
        default="0.0.0.0", description="RAG MCP server host", min_length=1
    )
    RAG_MCP_PORT: int = Field(
        default=65510, description="RAG MCP server port", ge=1, le=65535
    )

    # --- JWT Configuration ---
    JWT_SECRET_KEY: str = Field(
        default="supersecret",
        description="Secret key for JWT token signing",
        min_length=1,
    )

    # --- MongoDB Configuration ---
    MONGO_HOST: str = Field(
        default="localhost", description="MongoDB host address", min_length=1
    )
    MONGO_PORT: int = Field(default=27017, description="MongoDB port", ge=1, le=65535)
    MONGO_DB_NAME: str = Field(
        default="datapilotflow", description="MongoDB database name", min_length=1
    )
    MONGO_USER: Optional[str] = Field(
        default=None,
        description="MongoDB username (optional)",
    )
    MONGO_PASS: Optional[str] = Field(
        default=None,
        description="MongoDB password (optional)",
    )

    MONGO_AGENT_STATE_CHECKPOINT_DB_NAME: str = Field(
        default="datapilotflow_agent",
        description="MongoDB database name for state checkpoints",
        min_length=1,
    )
    MONGO_AGENT_STATE_CHECKPOINT_COLLECTION: str = Field(
        default="datapilotflow_agent_state_checkpoints",
        description="MongoDB collection for state checkpoints",
        min_length=1,
    )
    MONGO_AGENT_STATE_WRITES_COLLECTION: str = Field(
        default="datapilotflow_agent_state_writes",
        description="MongoDB collection for state writes",
        min_length=1,
    )

    # --- MongoDB Connection Options ---
    MONGO_MAX_POOL_SIZE: int = Field(
        default=10, description="Maximum MongoDB connection pool size", ge=1, le=100
    )
    MONGO_MIN_POOL_SIZE: int = Field(
        default=1, description="Minimum MongoDB connection pool size", ge=0, le=50
    )
    MONGO_MAX_IDLE_TIME_MS: int = Field(
        default=30000,
        description="Maximum idle time for MongoDB connections in milliseconds",
        ge=1000,
        le=300000,
    )
    MONGO_CONNECT_TIMEOUT_MS: int = Field(
        default=20000,
        description="MongoDB connection timeout in milliseconds",
        ge=1000,
        le=60000,
    )
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = Field(
        default=5000,
        description="MongoDB server selection timeout in milliseconds",
        ge=1000,
        le=30000,
    )

    @computed_field
    @property
    def MONGO_CONN_STR(self) -> str:
        """Return a MongoDB connection string using host/port/user/pass/db."""
        host = self.MONGO_HOST
        port = self.MONGO_PORT
        db = self.MONGO_DB_NAME
        if self.MONGO_USER and self.MONGO_PASS:
            user = quote_plus(self.MONGO_USER)
            pw = quote_plus(self.MONGO_PASS)
            # For root users, authenticate against admin database
            return f"mongodb://{user}:{pw}@{host}:{port}/admin"
        return f"mongodb://{host}:{port}/{db}"

    # --- Agent Tracing Configuration ---

    AGENT_TRACING_ENABLED: bool = Field(
        default=False,
        description="Whether to enable agent tracing and prompt versioning",
    )

    AGENT_TRACING_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for tracing agent activities",
    )

    AGENT_TRACING_URL: str = Field(
        default="http://localhost:5173/api",
        description="URL for tracing agent activities",
    )

    AGENT_TRACING_PROJECT_NAME: str = Field(
        default="datapilotflow",
        description="Project name for tracing agent activities",
    )

    AGENT_TRACING_DEFAULT_ENVIRONMENT: str = Field(
        default="development",
        description="Default environment for tracing agent activities",
    )

    # --- RAG Configuration ---

    RAG_TOP_K: int = Field(
        default=5, description="Number of top documents to retrieve", ge=1, le=20
    )

    RAG_SIMILARITY_THRESHOLD: float = Field(
        default=0.6,
        description="Similarity threshold for filtering RAG results (minimum score to include)",
        ge=0.0,
        le=1.0,
    )

    # --- File Paths Configuration ---
    BASE_DIR: Path = Field(
        default=Path(__file__).parent.parent,  # backend/ directory
        description="Base directory of the application",
    )
    EVALUATION_DATASET_FILE_PATH: Path = Field(
        default=Path("data/evaluation_dataset.json"),
        description="Path to evaluation dataset",
    )
    KNOWLEDGE_METADATA_FILE_NAME: str = Field(
        default="config/knowledge_metadata.json",
        description="Name of the knowledge metadata JSON file.",
        min_length=1,
    )

    @computed_field
    @property
    def EXTRACTION_METADATA_FILE_PATH(self) -> Path:
        """Computed path for extraction metadata."""
        return Path(self.KNOWLEDGE_METADATA_FILE_NAME)

    # --- Vector Database Configuration ---
    VECTOR_DB_HOST: str = Field(
        default="localhost", description="Vector database host address", min_length=1
    )
    VECTOR_DB_HTTP_PORT: int = Field(
        default=19530, description="Vector database HTTP port", ge=1, le=65535
    )
    VECTOR_DB_USERNAME: str = Field(
        default="root", description="Vector database username", min_length=1
    )
    VECTOR_DB_PASSWORD: str = Field(
        default="Milvus", description="Vector database password", min_length=1
    )
    VECTOR_DB_CONNECTION_SCHEME: str = Field(
        default="http",
        description="Vector database connection scheme (http or https)",
        min_length=1,
    )

    # --- RabbitMQ Configuration ---
    RABBITMQ_HOST: str = Field(
        default="localhost", description="RabbitMQ host address", min_length=1
    )
    RABBITMQ_PORT: int = Field(
        default=5672, description="RabbitMQ AMQP port", ge=1, le=65535
    )
    RABBITMQ_USER: str = Field(
        default="skillpilot", description="RabbitMQ username", min_length=1
    )
    RABBITMQ_PASS: str = Field(
        default="skillpilot123", description="RabbitMQ password", min_length=1
    )
    RABBITMQ_VHOST: str = Field(
        default="/", description="RabbitMQ virtual host", min_length=1
    )

    RABBITMQ_MESSAGE_TTL: int = Field(
        default=86400000,
        description="RabbitMQ message TTL in milliseconds",
        ge=60000,  # 1 minute
        le=604800000,  # 1 week
    )

    RABBITMQ_HEARTBEAT: int = Field(
        default=300, description="RabbitMQ heartbeat in seconds", ge=60, le=3600
    )

    RAG_FILE_UPLOAD_INBOUND_DIR: str = Field(
        default="./upload/inbound",
        description="Directory for inbound file uploads",
        min_length=1,
    )
    RAG_FILE_UPLOAD_ARCHIVE_DIR: str = Field(
        default="./upload/archive",
        description="Directory for archived file uploads",
        min_length=1,
    )
    RAG_FILE_UPLOAD_FAILED_DIR: str = Field(
        default="./upload/failed",
        description="Directory for failed file uploads",
        min_length=1,
    )

    RAG_FILE_UPLOAD_OUTPUT_DIR: str = Field(
        default="./upload/output",
        description="Directory for output file uploads",
        min_length=1,
    )

    RAG_INGESTION_JOBS_OUTPUT_DATA_DIR: str = Field(
        default="./ingestion_jobs_output_data",
        description="Directory for ingestion jobs data",
        min_length=1,
    )

    # Removed storage backend helper methods - we always use MongoDB
    # Removed vector database config methods - using general configuration


def suppress_resource_warnings():
    """Suppress common ResourceWarnings that are not critical to application functionality.

    This function suppresses warnings from:
    - SQLite connections (from Playwright and other libraries)
    - Python's inspect module
    - asyncio module
    - Other common sources of ResourceWarnings

    These warnings are typically caused by third-party libraries not properly
    closing database connections, but they don't affect the application's functionality.
    """
    import warnings

    # Suppress SQLite ResourceWarnings from Playwright and other libraries
    warnings.filterwarnings("ignore", category=ResourceWarning, module="inspect")
    warnings.filterwarnings("ignore", category=ResourceWarning, module="asyncio")
    warnings.filterwarnings(
        "ignore", category=ResourceWarning, module="concurrent.futures"
    )

    # Suppress specific ResourceWarning patterns
    warnings.filterwarnings(
        "ignore", message=".*unclosed database.*", category=ResourceWarning
    )
    warnings.filterwarnings(
        "ignore", message=".*unclosed file.*", category=ResourceWarning
    )


# Call the function when the module is imported
suppress_resource_warnings()


# Global settings instance
settings = Settings()
