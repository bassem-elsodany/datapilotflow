import sys
import time
from enum import Enum
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus, urlparse

from loguru import logger
from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default logging configuration for libraries that import config
# Note: Run scripts should use setup_service_logging() from domain.logging
# to configure service-specific logging BEFORE importing config
# This default setup is for backward compatibility and library usage


# Check if we're running in a service context (e.g., run_api_server.py, run_processor.py)
# If so, don't create the default log file - setup_service_logging will handle it
def _is_service_context() -> bool:
    """Check if we're running in a service context."""
    try:
        # Check if the main script is a service runner (starts with 'run_')
        if len(sys.argv) > 0:
            script_name = Path(sys.argv[0]).name
            if script_name.startswith("run_") or "uvicorn" in script_name.lower():
                return True
        # Check if we're being imported by uvicorn or any service module
        import inspect

        for frame in inspect.stack():
            frame_file = str(frame.filename).lower()
            if any(
                keyword in frame_file
                for keyword in [
                    "uvicorn",
                    "run_",
                    "api_server",
                    "server.py",
                    "run_api_server",
                ]
            ):
                return True
    except Exception:
        pass
    return False


# Check if logging has already been configured by setup_service_logging()
# by checking the module-level flag in domain.logging
_logging_already_configured = False

# First, try to import and check the flag
try:
    from datapilotflow.domain.logging import _service_logging_configured

    _logging_already_configured = _service_logging_configured
except (ImportError, AttributeError):
    # Flag doesn't exist or can't be imported - will check handlers below
    pass

# If we're in a service context, don't create the default log file
if _is_service_context():
    _logging_already_configured = True

# ALWAYS check handlers as a fallback (even if flag check passed)
# This prevents file creation when domain.config is imported before setup_service_logging
if not _logging_already_configured:
    try:
        handlers = logger._core.handlers  # type: ignore
        if handlers:
            # Check if any handler is writing to a file (not just stderr)
            for handler_id, handler in handlers.items():
                sink = getattr(handler, "sink", None)
                # Check if sink is a file path (string or Path)
                if isinstance(sink, (str, Path)):
                    sink_str = str(sink)
                    # If it's a file path (contains 'log' or ends with .log) and not stderr
                    if "log" in sink_str.lower() and sink != sys.stderr:
                        _logging_already_configured = True
                        break
                # Check if sink is a file object (has 'name' attribute)
                elif hasattr(sink, "name") and sink != sys.stderr:
                    sink_name = str(getattr(sink, "name", ""))
                    if "log" in sink_name.lower():
                        _logging_already_configured = True
                        break
    except (AttributeError, TypeError, Exception):
        pass

# Also check if service-specific log files already exist in logs directory
# This prevents creating datapilotflow.log when we're in a service context
# (e.g., api.log, processor.log, etc. already exist)
if not _logging_already_configured:
    try:
        logs_dir = Path("logs")
        if logs_dir.exists():
            # Check for service-specific log files (api.log, processor.log, etc.)
            for log_file in logs_dir.glob("*.log"):
                # If any service-specific log file exists, don't create default one
                if log_file.name != "datapilotflow.log":
                    _logging_already_configured = True
                    break
    except (OSError, Exception):
        pass

# Only set up default logging if logging hasn't been configured yet
# This prevents duplicate loggers when setup_service_logging() has already been called
# OR when any file handler already exists OR when service-specific log files exist
if not _logging_already_configured:
    # Set up default logging - ONLY stderr, NO FILE HANDLERS
    # Services (API, events, MCP server, etc.) MUST use setup_service_logging()
    # to create their own service-specific log files (api.log, processor.log, etc.)
    # domain.config should NEVER create datapilotflow.log

    # Remove ALL existing handlers to ensure clean slate (but preserve any file handlers)
    handlers_to_keep = []
    try:
        handlers = logger._core.handlers  # type: ignore
        # Keep track of any file handlers that are writing to logs directory
        for handler_id, handler in handlers.items():
            sink = getattr(handler, "sink", None)
            # If this is already a file handler in logs dir, keep it
            if isinstance(sink, (str, Path)):
                sink_str = str(sink)
                if "logs" in sink_str and sink_str.endswith(".log"):
                    handlers_to_keep.append(handler_id)
            elif hasattr(sink, "name"):
                sink_name = str(getattr(sink, "name", ""))
                if "logs" in sink_name and sink_name.endswith(".log"):
                    handlers_to_keep.append(handler_id)
    except (AttributeError, TypeError, Exception):
        pass

    # Only remove and re-add if we don't have file handlers already
    if not handlers_to_keep:
        try:
            logger.remove()
        except ValueError:
            pass  # No handlers exist, which is fine

        logger.add(
            sys.stderr,
            format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {name} | {file}:{line} | {message} | {extra}",
            level="INFO",
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

    # --- MCP Server Configuration (Business Logic) ---
    # RAG Agent MCP Server
    MCP_SERVER_HOST: str = Field(
        default="0.0.0.0", description="MCP server host", min_length=1
    )
    MCP_SERVER_PORT: int = Field(
        default=65510, description="MCP server port (RAG agent)", ge=1, le=65535
    )
    MCP_SERVER_NAME: str = Field(
        default="datapilotflow-rag",
        description="MCP server name (RAG agent)",
        min_length=1,
    )
    MCP_ENABLED_TOOLS: str = Field(
        default="knowledge_expert",
        description="Comma-separated list of enabled MCP tools (RAG agent)",
        min_length=1,
    )
    MCP_LOG_LEVEL: str = Field(
        default="INFO", description="MCP server log level", min_length=1
    )
    MCP_WORKER_THREADS: int = Field(
        default=4, description="Number of MCP worker threads", ge=1, le=16
    )

    # Assistant Agent MCP Server (Optional - for future expansion)
    ASSISTANT_MCP_SERVER_PORT: int = Field(
        default=65511,
        description="Assistant MCP server port (optional, for future use)",
        ge=1,
        le=65535,
    )
    ASSISTANT_MCP_ENABLED_TOOLS: str = Field(
        default="assistant_tools",
        description="Comma-separated list of enabled Assistant MCP tools (optional)",
        min_length=1,
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

    MONGO_AGENT_STATE_CHECKPOINT_ENABLED: bool = Field(
        default=False,
        description="Whether to enable MongoDB agent state checkpointing",
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
        default=Path(__file__).parent.parent,
        description="Base directory of the application",
    )
    EVALUATION_DATASET_FILE_PATH: Path = Field(
        default=Path("data/evaluation_dataset.json"),
        description="Path to evaluation dataset",
    )

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
