import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Portfolio, PortfolioPosition, Asset, PriceHistory
from backend.simulation.backtester import BacktestEngine
from backend.simulation.monte_carlo import MonteCarloSimulator

def test_backtest_engine_sma_cross():
    db = SessionLocal()
    try:
        # Run backtest for AAPL (AAPL price history is seeded in collector tests)
        today = date.today()
        start = today - timedelta(days=365)
        end = today
        
        # Test SMA crossover strategy
        res = BacktestEngine.run_backtest(
            db,
            ticker="AAPL",
            strategy_name="sma_cross",
            start_date=start,
            end_date=end,
            initial_cash=10000.0
        )
        
        assert res["ticker"] == "AAPL"
        assert res["strategy"] == "sma_cross"
        assert res["initial_value"] == 10000.0
        assert "cumulative_return" in res
        assert "cagr" in res
        assert "max_drawdown" in res
        assert isinstance(res["trades"], list)
        assert len(res["equity_curve"]) > 0
        
        # Test RSI strategy
        res_rsi = BacktestEngine.run_backtest(
            db,
            ticker="AAPL",
            strategy_name="rsi_bounds",
            start_date=start,
            end_date=end,
            initial_cash=10000.0
        )
        assert res_rsi["strategy"] == "rsi_bounds"
        
    finally:
        db.close()

def test_monte_carlo_simulator():
    db = SessionLocal()
    try:
        # 1. Create a portfolio with cash and holdings
        test_portfolio = Portfolio(name="Simulation Portfolio", cash_balance=Decimal("50000.00"))
        db.add(test_portfolio)
        db.commit()
        db.refresh(test_portfolio)
        
        # Find AAPL asset
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        pos = PortfolioPosition(
            portfolio_id=test_portfolio.id,
            asset_id=aapl.id,
            shares=Decimal("100.00"),
            average_cost=Decimal("150.00")
        )
        db.add(pos)
        db.commit()
        
        # 2. Run simulation
        sim_res = MonteCarloSimulator.run_simulation(
            db,
            portfolio_id=test_portfolio.id,
            projection_days=30,
            num_simulations=50
        )
        
        # Verify length of lists
        assert len(sim_res["days"]) == 31
        assert len(sim_res["p5"]) == 31
        assert len(sim_res["p50"]) == 31
        assert len(sim_res["p95"]) == 31
        assert sim_res["holdings_simulated"] == 1
        assert sim_res["starting_value"] > 50000.0
        
        # 3. Test Cash-only Portfolio Monte Carlo
        cash_portfolio = Portfolio(name="Cash Only Portfolio", cash_balance=Decimal("20000.00"))
        db.add(cash_portfolio)
        db.commit()
        db.refresh(cash_portfolio)
        
        cash_sim = MonteCarloSimulator.run_simulation(
            db,
            portfolio_id=cash_portfolio.id,
            projection_days=10,
            num_simulations=10
        )
        
        # All values should be equal to the initial cash (20,000 USD)
        assert cash_sim["starting_value"] == 20000.0
        assert cash_sim["p5"] == [20000.0] * 11
        assert cash_sim["p50"] == [20000.0] * 11
        assert cash_sim["p95"] == [20000.0] * 11
        
        # Clean up
        db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == test_portfolio.id).delete()
        db.delete(test_portfolio)
        db.delete(cash_portfolio)
        db.commit()
        
    finally:
        db.close()
