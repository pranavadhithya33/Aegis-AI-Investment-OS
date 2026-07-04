import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger("knowledge.normalizer")

class Normalizer:
    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """Strip HTML tags, extra whitespace, and standardize quotes."""
        if not text:
            return ""
        # Strip HTML tags
        cleaned = re.sub(r"<[^>]+>", "", text)
        # Normalize spaces
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    @staticmethod
    def to_decimal(value: Any) -> Optional[Decimal]:
        """Safely convert any numeric value or numeric string to Decimal."""
        if value is None:
            return None
        # Handle nan values
        if isinstance(value, float):
            import math
            if math.isnan(value) or math.isinf(value):
                return None
        try:
            # Clean string representing float/int
            val_str = str(value).strip().replace(",", "")
            if not val_str or val_str.lower() in ("none", "null", "nan", "na", "."):
                return None
            return Decimal(val_str)
        except (ValueError, InvalidOperation):
            logger.warning(f"Could not convert value '{value}' to Decimal")
            return None

    @staticmethod
    def to_date(value: Any) -> Optional[date]:
        """Safely parse various date formats into standard datetime.date."""
        if not value:
            return None
        if isinstance(value, date):
            if isinstance(value, datetime):
                return value.date()
            return value
        if isinstance(value, (int, float)):
            # Assume Unix timestamp (seconds or milliseconds)
            try:
                if value > 1e11:  # Milliseconds
                    value = value / 1000.0
                return datetime.utcfromtimestamp(value).date()
            except Exception:
                return None

        # String parsing
        val_str = str(value).strip()
        # Common ISO formats
        for fmt in (
            "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", 
            "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y", "%b %d, %Y"
        ):
            try:
                # Truncate timezone offset if present (e.g. +00:00)
                if "+" in val_str:
                    val_str = val_str.split("+")[0]
                return datetime.strptime(val_str, fmt).date()
            except ValueError:
                continue

        logger.warning(f"Could not parse date string '{value}'")
        return None

    @classmethod
    def normalize_news(cls, raw_news: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a raw news article record."""
        return {
            "title": cls.clean_text(raw_news.get("title", "Untitled")),
            "url": str(raw_news.get("url", "")).strip(),
            "content": cls.clean_text(raw_news.get("content", "")),
            "source": cls.clean_text(raw_news.get("source", "Unknown")),
            "published_at": cls.to_date(raw_news.get("published_at")) or date.today()
        }
