"""
Base event system for domain events.

This module provides the foundation for domain events, event handlers,
and event dispatching in the SkillPilot system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Type, TypeVar
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field

T = TypeVar("T", bound="DomainEvent")


class DomainEvent(BaseModel):
    """
    Base class for all domain events.

    Domain events represent something important that happened in the domain
    that other parts of the system might be interested in.
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique event identifier"
    )
    event_type: str = Field(description="Type of the event")
    occurred_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the event occurred"
    )
    version: int = Field(default=1, description="Event version for schema evolution")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional event metadata"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def __str__(self) -> str:
        return f"{self.event_type}({self.aggregate_id})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.event_id}, aggregate_id={self.aggregate_id})"


class EventHandler(ABC):
    """
    Abstract base class for event handlers.

    Event handlers process domain events and perform side effects
    such as updating read models, sending notifications, etc.
    """

    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """
        Handle a domain event.

        Args:
            event: The domain event to handle
        """
        pass

    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the given event.

        Args:
            event: The domain event to check

        Returns:
            True if this handler can handle the event, False otherwise
        """
        pass


class EventDispatcher:
    """
    Central event dispatcher for domain events.

    The event dispatcher manages event handlers and routes events
    to the appropriate handlers.
    """

    def __init__(self):
        self._handlers: List[EventHandler] = []
        self._event_handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def register_handler(self, handler: EventHandler) -> None:
        """
        Register an event handler.

        Args:
            handler: The event handler to register
        """
        self._handlers.append(handler)
        logger.debug(f"Registered event handler: {handler.__class__.__name__}")

    def register_handlers(self, handlers: List[EventHandler]) -> None:
        """
        Register multiple event handlers.

        Args:
            handlers: List of event handlers to register
        """
        for handler in handlers:
            self.register_handler(handler)

    def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch a domain event to all registered handlers.

        Args:
            event: The domain event to dispatch
        """
        logger.debug(f"Dispatching event: {event}")

        handled_count = 0
        for handler in self._handlers:
            try:
                if handler.can_handle(event):
                    handler.handle(event)
                    handled_count += 1
                    logger.debug(
                        f"Event {event.event_id} handled by {handler.__class__.__name__}"
                    )
            except Exception as e:
                logger.error(
                    f"Error handling event {event.event_id} with {handler.__class__.__name__}: {e}"
                )
                # Continue processing other handlers even if one fails
                continue

        logger.debug(f"Event {event.event_id} dispatched to {handled_count} handlers")

    def dispatch_multiple(self, events: List[DomainEvent]) -> None:
        """
        Dispatch multiple domain events.

        Args:
            events: List of domain events to dispatch
        """
        for event in events:
            self.dispatch(event)

    def get_handlers_for_event(
        self, event_type: Type[DomainEvent]
    ) -> List[EventHandler]:
        """
        Get all handlers that can handle a specific event type.

        Args:
            event_type: The type of event to get handlers for

        Returns:
            List of handlers that can handle the event type
        """
        return [handler for handler in self._handlers if handler.can_handle(event_type)]

    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._event_handlers.clear()
        logger.debug("Cleared all event handlers")


# Global event dispatcher instance
_event_dispatcher: EventDispatcher = None


def get_event_dispatcher() -> EventDispatcher:
    """
    Get the global event dispatcher instance.

    Returns:
        The global event dispatcher
    """
    global _event_dispatcher
    if _event_dispatcher is None:
        _event_dispatcher = EventDispatcher()
    return _event_dispatcher


def dispatch_event(event: DomainEvent) -> None:
    """
    Dispatch a domain event using the global dispatcher.

    Args:
        event: The domain event to dispatch
    """
    dispatcher = get_event_dispatcher()
    dispatcher.dispatch(event)


def dispatch_events(events: List[DomainEvent]) -> None:
    """
    Dispatch multiple domain events using the global dispatcher.

    Args:
        events: List of domain events to dispatch
    """
    dispatcher = get_event_dispatcher()
    dispatcher.dispatch_multiple(events)
