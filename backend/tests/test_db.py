import os
import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

# Add project root to system path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal, engine
from backend.database.models import Asset, Portfolio, Transaction

def test_seeded_assets():
    """Verify that default assets have been seeded and are readable."""
    db = SessionLocal()
    try:
        assets = db.query(Asset).all()
        tickers = [a.ticker for a in assets]
        
        # Verify essential tickers exist
        assert "MSFT" in tickers
        assert "AAPL" in tickers
        assert "BTC-USD" in tickers
        assert "^GSPC" in tickers
        
        # Verify counts
        assert len(assets) >= 11
        
        msft = db.query(Asset).filter(Asset.ticker == "MSFT").first()
        assert msft.name == "Microsoft Corporation"
        assert msft.asset_type == "stock"
    finally:
        db.close()

def test_seeded_portfolio():
    """Verify that a default portfolio exists."""
    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).first()
        assert portfolio is not None
        assert portfolio.name == "Aegis Master Portfolio"
        assert portfolio.cash_balance > 0
    finally:
        db.close()

def test_database_write_transaction():
    """Verify writing, committing, and deleting records is operational."""
    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.name == "Aegis Master Portfolio").first()
        assert portfolio is not None
        
        # Add a dummy deposit transaction
        from datetime import datetime
        dummy_tx = Transaction(
            portfolio_id=portfolio.id,
            transaction_type="DEPOSIT",
            size=5000.00,
            date=datetime.utcnow()
        )
        db.add(dummy_tx)
        db.commit()
        
        # Fetch it back
        saved_tx = db.query(Transaction).filter(Transaction.portfolio_id == portfolio.id, Transaction.size == 5000.00).first()
        assert saved_tx is not None
        assert saved_tx.transaction_type == "DEPOSIT"
        
        # Clean up
        db.delete(saved_tx)
        db.commit()
        
        deleted_tx = db.query(Transaction).filter(Transaction.portfolio_id == portfolio.id, Transaction.size == 5000.00).first()
        assert deleted_tx is None
        
    finally:
        db.close()
