import os
import sys
from pathlib import Path

# Add project root to system path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.database.models import Asset, PriceHistory, EconomicEvent, FinancialStatement
from backend.cache.manager import CacheManager
from backend.event_bus import EventBus
from backend.plugins.yahoo import YahooFinancePlugin
from backend.plugins.fred import FredPlugin

# --- 1. CACHE UNIT TESTS ---
def test_cache_manager_operations(tmp_path):
    """Test CacheManager setting, getting, and deleting entries."""
    cache = CacheManager(cache_dir=tmp_path)
    
    test_key = "test_item_123"
    test_data = {"ticker": "MSFT", "price": 420.50}
    
    # Store
    assert cache.set(test_key, test_data, expire_seconds=60)
    
    # Retrieve
    retrieved = cache.get(test_key)
    assert retrieved == test_data
    
    # Retrieve missing
    assert cache.get("missing_key") is None
    
    # Delete
    assert cache.delete(test_key)
    assert cache.get(test_key) is None

def test_cache_expiration(tmp_path):
    """Test that items expire properly."""
    import time
    cache = CacheManager(cache_dir=tmp_path)
    
    test_key = "expiring_item"
    test_data = "expired"
    
    # Set to expire in 1 second
    cache.set(test_key, test_data, expire_seconds=1)
    
    # Retrieve immediately
    assert cache.get(test_key) == test_data
    
    # Wait 1.1 seconds
    time.sleep(1.1)
    
    # Retrieve should now return None (expired)
    assert cache.get(test_key) is None

# --- 2. EVENT BUS UNIT TESTS ---
def test_event_bus():
    """Test subscribing and publishing events."""
    bus = EventBus()
    received_events = []
    
    def mock_handler(data):
        received_events.append(data)
        
    bus.subscribe("test.event", mock_handler)
    
    # Publish
    payload = {"message": "hello world", "value": 100}
    bus.publish("test.event", payload)
    
    assert len(received_events) == 1
    assert received_events[0] == payload

# --- 3. PLUGINS INTEGRATION TESTS ---
def test_yahoo_finance_plugin_execution():
    """Verify Yahoo Finance collector retrieves and persists pricing/fundamentals."""
    db = SessionLocal()
    try:
        # Create a test asset if it doesn't exist
        test_ticker = "AAPL"
        asset = db.query(Asset).filter(Asset.ticker == test_ticker).first()
        if not asset:
            asset = Asset(
                ticker=test_ticker,
                name="Apple Inc.",
                asset_type="stock",
                is_active=True
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)
            
        # Instantiate plugin
        plugin = YahooFinancePlugin()
        
        # We manually fetch a single day to minimize network load in tests
        today = date.today()
        start_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        
        df = plugin.fetch(test_ticker, start=start_date, end=end_date)
        assert df is not None
        assert not df.empty
        
        # Test update loop (will run for all active assets)
        summary = plugin.update(db)
        assert summary["assets_processed"] >= 1
        
        # Check if database has prices now
        prices = db.query(PriceHistory).filter(PriceHistory.asset_id == asset.id).all()
        assert len(prices) > 0
        assert prices[0].close > 0
        
        # Check if fundamentals are populated
        fundamentals = db.query(FinancialStatement).filter(FinancialStatement.asset_id == asset.id).all()
        # AAPL financials should be loaded
        assert len(fundamentals) > 0
        assert fundamentals[0].revenue > 0
        
    finally:
        db.close()

def test_fred_plugin_execution():
    """Verify FRED plugin fetches yields or falls back to Yahoo yields."""
    db = SessionLocal()
    try:
        plugin = FredPlugin()
        
        # Clear existing yield events for test isolation
        db.query(EconomicEvent).filter(
            EconomicEvent.series_id.in_(list(plugin.yahoo_yield_tickers.keys()))
        ).delete(synchronize_session=False)
        db.commit()
        
        # Execute the update loop
        summary = plugin.update(db)
        assert summary["series_processed"] > 0
        
        # Query economic events to verify data was written
        events = db.query(EconomicEvent).all()
        assert len(events) > 0
        assert events[0].value > 0
        
        # Check source type (since no FRED API key is present in env, it should be Yahoo Finance)
        assert summary["source"] == "Yahoo Finance"
        
    finally:
        db.close()
