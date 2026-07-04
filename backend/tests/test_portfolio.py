import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from decimal import Decimal
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Portfolio, Transaction, Asset, PortfolioPosition, PriceHistory
from backend.portfolio.tracker import PortfolioTracker
from backend.portfolio.features import FeatureStore
from backend.portfolio.performance import PortfolioPerformance
from backend.portfolio.dividends import DividendTracker

# --- PORTFOLIO ENGINE TESTS ---
def test_portfolio_tracker_recalculation():
    db = SessionLocal()
    try:
        # 1. Create a temporary portfolio
        test_portfolio = Portfolio(name="Test Active Trading Portfolio")
        db.add(test_portfolio)
        db.commit()
        db.refresh(test_portfolio)

        # Retrieve AAPL asset ID (AAPL is seeded and populated with prices in collector tests)
        aapl_asset = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl_asset is not None, "AAPL asset must exist (should have been seeded)"

        base_time = datetime.utcnow() - timedelta(days=10)

        # 2. Add Transactions:
        # A. Deposit 100,000 USD cash
        tx1 = Transaction(
            portfolio_id=test_portfolio.id,
            transaction_type="DEPOSIT",
            size=Decimal("100000.00"),
            commission=Decimal("0.00"),
            date=base_time
        )
        db.add(tx1)

        # B. Buy 100 shares of AAPL at 150 USD (fee: 10 USD)
        tx2 = Transaction(
            portfolio_id=test_portfolio.id,
            asset_id=aapl_asset.id,
            transaction_type="BUY",
            price=Decimal("150.00"),
            size=Decimal("100.00"),
            commission=Decimal("10.00"),
            date=base_time + timedelta(days=2)
        )
        db.add(tx2)

        # C. Buy 100 shares of AAPL at 160 USD (fee: 10 USD)
        tx3 = Transaction(
            portfolio_id=test_portfolio.id,
            asset_id=aapl_asset.id,
            transaction_type="BUY",
            price=Decimal("160.00"),
            size=Decimal("100.00"),
            commission=Decimal("10.00"),
            date=base_time + timedelta(days=4)
        )
        db.add(tx3)

        # D. Sell 50 shares of AAPL at 180 USD (fee: 5 USD)
        tx4 = Transaction(
            portfolio_id=test_portfolio.id,
            asset_id=aapl_asset.id,
            transaction_type="SELL",
            price=Decimal("180.00"),
            size=Decimal("50.00"),
            commission=Decimal("5.00"),
            date=base_time + timedelta(days=6)
        )
        db.add(tx4)
        db.commit()

        # 3. Recalculate
        summary = PortfolioTracker.recalculate_portfolio(db, test_portfolio.id)
        
        # Verify Cash Balance:
        # Start: 100,000
        # Buy 1: -(100 * 150 + 10) = -15,010 -> 84,990
        # Buy 2: -(100 * 160 + 10) = -16,010 -> 68,980
        # Sell: +(50 * 180 - 5) = +8,995 -> 77,975
        assert summary["cash_balance"] == 77975.00
        
        # Verify Position holding
        pos = db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == test_portfolio.id,
            PortfolioPosition.asset_id == aapl_asset.id
        ).first()
        
        assert pos is not None
        # 100 + 100 - 50 = 150 shares
        assert pos.shares == Decimal("150.00")
        
        # Verify Average Cost basis:
        # Total cost for 200 shares = 15,010 + 16,010 = 31,020
        # Cost per share = 31,020 / 200 = 155.10
        # Sell doesn't alter cost basis for remaining shares.
        assert float(pos.average_cost) == pytest.approx(155.10)

        # --- PERFORMANCE TESTS ---
        twrr = PortfolioPerformance.calculate_twrr(db, test_portfolio.id)
        mwrr = PortfolioPerformance.calculate_mwrr(db, test_portfolio.id)
        
        assert isinstance(twrr, float)
        assert isinstance(mwrr, float)

        # --- DIVIDEND TRACKER TESTS ---
        divs = DividendTracker.calculate_portfolio_dividends(db, test_portfolio.id)
        assert divs["portfolio_id"] == test_portfolio.id
        assert "projected_annual_income" in divs
        assert "portfolio_dividend_yield" in divs

        # Clean up
        db.query(Transaction).filter(Transaction.portfolio_id == test_portfolio.id).delete()
        db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == test_portfolio.id).delete()
        db.delete(test_portfolio)
        db.commit()

    finally:
        db.close()

# --- FEATURE STORE TESTS ---
def test_feature_store():
    db = SessionLocal()
    try:
        aapl_asset = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl_asset is not None
        
        # Ensure we have price history for AAPL
        prices = db.query(PriceHistory).filter(PriceHistory.asset_id == aapl_asset.id).all()
        assert len(prices) > 0, "Price history must exist for AAPL to calculate features"
        
        features = FeatureStore.get_asset_features(db, aapl_asset.id, use_cache=False)
        
        assert features["ticker"] == "AAPL"
        assert "sma_50" in features
        assert "rsi_14" in features
        assert "max_drawdown" in features
        assert "sharpe_ratio" in features
        assert "beta" in features
    finally:
        db.close()
