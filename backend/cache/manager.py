import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import logging
from backend.config.settings import settings

logger = logging.getLogger("cache_manager")

class CacheManager:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        # Use SHA-256 to hash the key to a safe filename
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache if it exists and is not expired.
        Returns None if missing or expired.
        """
        path = self._get_cache_path(key)
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            
            # Check expiration
            expire_at_str = cached_data.get("expire_at")
            if expire_at_str:
                expire_at = datetime.fromisoformat(expire_at_str)
                if datetime.utcnow() > expire_at:
                    # Expired, clean it up
                    self.delete(key)
                    return None
            
            return cached_data.get("data")
        except Exception as e:
            logger.error(f"Error reading cache for key '{key}': {e}")
            return None

    def set(self, key: str, data: Any, expire_seconds: Optional[int] = 86400) -> bool:
        """
        Store data in cache. 
        expire_seconds defaults to 1 day (86400 seconds).
        Pass None or -1 for infinite caching.
        """
        path = self._get_cache_path(key)
        expire_at = None
        if expire_seconds and expire_seconds > 0:
            expire_at = (datetime.utcnow() + timedelta(seconds=expire_seconds)).isoformat()
            
        cached_data = {
            "key": key,
            "created_at": datetime.utcnow().isoformat(),
            "expire_at": expire_at,
            "data": data
        }
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error writing cache for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Remove a specific key from cache."""
        path = self._get_cache_path(key)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"Error deleting cache file for key '{key}': {e}")
                return False
        return False

    def clear(self) -> int:
        """Delete all cache files in the cache directory. Returns files cleared."""
        deleted_count = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting cache file during clear: {e}")
        logger.info(f"Cleared {deleted_count} cached items.")
        return deleted_count

# Global cache instance
cache_manager = CacheManager()
