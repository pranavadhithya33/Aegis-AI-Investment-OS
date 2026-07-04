import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Asset

class EntityResolver:
    """
    Resolves tickers and company names to database Asset IDs.
    Also parses free text to detect mentions of assets in news articles.
    """
    def __init__(self, db: Session):
        self.db = db
        self.ticker_map: Dict[str, int] = {}
        self.name_map: Dict[str, int] = {}
        self._load_universe()

    def _normalize_name(self, name: str) -> str:
        """Helper to lowercase, remove punctuation, and strip common corporate suffixes."""
        name = name.lower()
        # Remove punctuation
        name = re.sub(r"[^\w\s]", "", name)
        # Remove common corporate suffixes
        suffixes = r"\b(inc|corp|co|corporation|incorporated|ltd|limited|plc|group|sa|ag)\b"
        name = re.sub(suffixes, "", name)
        return " ".join(name.split()).strip()

    def _load_universe(self):
        """Loads all active assets into internal fast-lookup maps."""
        assets = self.db.query(Asset).filter(Asset.is_active == True).all()
        for asset in assets:
            # Map ticker
            self.ticker_map[asset.ticker.upper()] = asset.id
            
            # Map normalized asset name
            norm_name = self._normalize_name(asset.name)
            if norm_name:
                self.name_map[norm_name] = asset.id
                
            # Map ticker name itself as a secondary key
            norm_ticker = self._normalize_name(asset.ticker)
            if norm_ticker:
                self.name_map[norm_ticker] = asset.id

    def resolve_ticker(self, ticker: str) -> Optional[int]:
        """Directly map a ticker symbol to its database Asset ID."""
        return self.ticker_map.get(ticker.upper())

    def resolve_name(self, name: str) -> Optional[int]:
        """Resolve a full company/asset name to its database Asset ID."""
        if not name:
            return None
            
        # Check ticker map first
        name_upper = name.strip().upper()
        if name_upper in self.ticker_map:
            return self.ticker_map[name_upper]
            
        norm = self._normalize_name(name)
        # Check exact normalized name match
        if norm in self.name_map:
            return self.name_map[norm]
            
        # Check substring matches for longer company names
        for key, asset_id in self.name_map.items():
            if len(norm) > 3 and (norm in key or key in norm):
                return asset_id
                
        return None

    def scan_text(self, text: str) -> List[int]:
        """
        Scan a body of text (e.g. news article body) to identify
        which active database Asset IDs are mentioned.
        """
        if not text:
            return []
            
        found_ids = set()
        
        # 1. Scan for tickers using word boundaries
        for ticker, asset_id in self.ticker_map.items():
            escaped_ticker = re.escape(ticker)
            # Match word boundary for ticker (e.g., AAPL, but not AppleAAPL)
            if re.search(rf"\b{escaped_ticker}\b", text, re.IGNORECASE):
                found_ids.add(asset_id)
                
        # 2. Scan for full names
        text_lower = text.lower()
        for norm_name, asset_id in self.name_map.items():
            # Skip scanning extremely short names to avoid false positives
            if len(norm_name) > 4 and norm_name in text_lower:
                found_ids.add(asset_id)
                
        return list(found_ids)
