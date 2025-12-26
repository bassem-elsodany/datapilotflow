"""
Confluence integration domain events.

This module defines domain events related to Confluence API integration.
"""

from typing import Optional

from pydantic import Field

from .base import DomainEvent


class ConfluenceContentExtracted(DomainEvent):
    """
    Event published when Confluence content is successfully extracted via API.

    This event is triggered after pages are fetched from Confluence using the API
    and converted to documents ready for processing.
    """

    event_type: str = Field(
        default="confluence_content_extracted", description="Type of the event"
    )

    # Event-specific payload
    job_id: str = Field(description="ID of the knowledge job")
    pages_fetched: int = Field(description="Number of Confluence pages fetched")
    attachments_fetched: int = Field(
        description="Number of attachments extracted", default=0
    )
    total_content_size: int = Field(
        description="Total content size in bytes", default=0
    )
    extraction_duration_seconds: float = Field(
        description="Time taken to extract content"
    )
    confluence_mode: str = Field(description="Confluence extraction mode used")
    space_keys: Optional[str] = Field(
        default=None, description="Space keys processed (comma-separated)"
    )

    def __init__(self, **data):
        super().__init__(**data)
