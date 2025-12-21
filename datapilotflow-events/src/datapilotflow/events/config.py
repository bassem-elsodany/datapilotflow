"""
DataPilotFlow Events Configuration.

This configuration is specific to the events processing layer.
Infrastructure settings are duplicated here for independent deployment.
Business logic settings are shared with domain config.
"""

from typing import Optional
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EventsSettings(BaseSettings):
    """Events service configuration with independent infrastructure settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_default=True,
    )

    # ============================================================================
    # RabbitMQ Infrastructure (Primary for Events)
    # ============================================================================

    RABBITMQ_HOST: str = Field(default="localhost", description="RabbitMQ host")
    RABBITMQ_PORT: int = Field(
        default=5672, description="RabbitMQ AMQP port", ge=1, le=65535
    )
    RABBITMQ_USER: str = Field(default="skillpilot", description="RabbitMQ username")
    RABBITMQ_PASS: str = Field(default="skillpilot123", description="RabbitMQ password")
    RABBITMQ_VHOST: str = Field(default="/", description="RabbitMQ virtual host")
    RABBITMQ_MESSAGE_TTL: int = Field(
        default=86400000,
        description="RabbitMQ message TTL (ms)",
        ge=60000,
        le=604800000,
    )
    RABBITMQ_HEARTBEAT: int = Field(
        default=300, description="RabbitMQ heartbeat (s)", ge=60, le=3600
    )

    # ============================================================================
    # MongoDB Infrastructure (For Event Persistence)
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
    # Vector Database Infrastructure
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
    # Business Logic Settings (Re-declared to load from .env)
    # ============================================================================

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


# Global events settings instance
settings = EventsSettings()
