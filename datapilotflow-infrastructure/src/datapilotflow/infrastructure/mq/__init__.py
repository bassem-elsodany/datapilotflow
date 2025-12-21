"""
Message Queue infrastructure package.

This package contains the RabbitMQ client wrapper with connection pooling.
"""

from .client import RabbitMQClient, get_rabbitmq_client, close_rabbitmq_client

__all__ = [
    "RabbitMQClient",
    "get_rabbitmq_client",
    "close_rabbitmq_client",
]

