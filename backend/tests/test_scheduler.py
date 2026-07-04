import os
import sys
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Asset, PriceHistory, Signal
from backend.event_bus import event_bus
from backend.notifications import notification_broker
from backend.scheduler import scheduler_daemon

def test_notification_broker_price_alerts():
    db = SessionLocal()
    try:
        # Start notification broker
        notification_broker.start()
        
        # Grab AAPL asset
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        # Seed two consecutive prices to trigger a price alert (>5% change)
        # Previous price
        p1 = PriceHistory(
            asset_id=aapl.id,
            date=date.today() - timedelta(days=2),
            close=Decimal("150.00")
        )
        # New price (10% surge)
        p2 = PriceHistory(
            asset_id=aapl.id,
            date=date.today() - timedelta(days=1),
            close=Decimal("165.00")
        )
        
        # Clear all existing AAPL price records to isolate this test case
        db.query(PriceHistory).filter(PriceHistory.asset_id == aapl.id).delete()
        db.commit()
        
        db.add(p1)
        db.add(p2)
        db.commit()
        
        # Publish price.updated event matching yesterday's new price date
        event_bus.publish("price.updated", {
            "asset_id": aapl.id,
            "ticker": "AAPL",
            "close": 165.00,
            "date": (date.today() - timedelta(days=1)).isoformat()
        })
        
        # Verify a Signal was logged to DB
        sig = (
            db.query(Signal)
            .filter(Signal.asset_id == aapl.id)
            .filter(Signal.signal_type == "price_alert")
            .order_by(Signal.created_at.desc())
            .first()
        )
        assert sig is not None
        assert "percent_change" in sig.details_json
        
        # Clean up
        db.delete(sig)
        db.delete(p1)
        db.delete(p2)
        db.commit()
    finally:
        db.close()

from datetime import timedelta

def test_scheduler_manual_trigger():
    db = SessionLocal()
    try:
        # Stop scheduler daemon if running to ensure it doesn't conflict
        scheduler_daemon.stop()
        
        # Verify manual trigger doesn't crash (executes offline mocked runs)
        results = scheduler_daemon.trigger_jobs_now(db)
        
        assert "yahoo" in results
        assert "fred" in results
        assert "portfolios" in results
        assert "features" in results
        assert "theses" in results
    finally:
        db.close()
