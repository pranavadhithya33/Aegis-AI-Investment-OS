from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.cache.manager import cache_manager, CacheManager
from backend.event_bus import event_bus, EventBus
import logging

class BasePlugin(ABC):
    """
    Base class for all data collection plugins.
    Each plugin interfaces with a specific data source (e.g. Yahoo Finance, FRED, SEC).
    """
    def __init__(
        self,
        plugin_id: str,
        name: str,
        cache: Optional[CacheManager] = None,
        bus: Optional[EventBus] = None
    ):
        self.id = plugin_id
        self.name = name
        self.cache = cache or cache_manager
        self.bus = bus or event_bus
        self.logger = logging.getLogger(f"plugin.{self.id}")

    @abstractmethod
    def fetch(self, **kwargs) -> Any:
        """
        Fetch raw data from the external API / source.
        Implementations should use self.cache to avoid redundant calls.
        """
        pass

    @abstractmethod
    def update(self, db: Session, **kwargs) -> Dict[str, Any]:
        """
        Executes the collection pipeline:
        1. Fetch raw data
        2. Parse and normalize
        3. Persist to database (SQLite)
        4. Publish events to the Event Bus (e.g. 'price.updated')
        
        Returns a dictionary summary of the operation (e.g., records_updated).
        """
        pass
