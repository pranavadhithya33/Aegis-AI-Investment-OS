import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger("event_bus")

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        """Register a callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Registered subscriber for event: {event_type}")

    def publish(self, event_type: str, data: Any):
        """Publish an event to all registered subscribers."""
        logger.info(f"Event published: '{event_type}'")
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                # Execute synchronously
                handler(data)
            except Exception as e:
                logger.error(
                    f"Error in subscriber handler '{handler.__name__}' for event '{event_type}': {e}",
                    exc_info=True
                )

# Global Event Bus instance
event_bus = EventBus()
