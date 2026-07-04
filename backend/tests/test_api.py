import os
import sys
from pathlib import Path
from datetime import date, timedelta
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.main import app
from backend.database.connection import SessionLocal
from backend.database.models import Asset

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_assets_api():
    response = client.get("/api/assets/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_portfolio_lifecycle_api():
    # 1. Create Portfolio
    create_resp = client.post("/api/portfolio/", json={"name": "API Test Portfolio"})
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert data["status"] == "success"
    portfolio_id = data["portfolio"]["id"]
    
    # 2. Add cash deposit
    dep_resp = client.post(
        f"/api/portfolio/{portfolio_id}/transaction",
        json={
            "transaction_type": "DEPOSIT",
            "size": 15000.0,
            "commission": 0.0
        }
    )
    assert dep_resp.status_code == 200
    assert dep_resp.json()["portfolio_summary"]["cash_balance"] == 15000.0

    # 3. Add buy transaction (AAPL)
    buy_resp = client.post(
        f"/api/portfolio/{portfolio_id}/transaction",
        json={
            "asset_ticker": "AAPL",
            "transaction_type": "BUY",
            "size": 10.0,
            "price": 150.0,
            "commission": 10.0
        }
    )
    assert buy_resp.status_code == 200
    summary = buy_resp.json()["portfolio_summary"]
    
    # Cash: 15,000 - (10 * 150 + 10) = 13,490
    assert summary["cash_balance"] == 13490.0
    
    # 4. Get performance metrics
    perf_resp = client.get(f"/api/portfolio/{portfolio_id}/performance")
    assert perf_resp.status_code == 200
    assert "twrr" in perf_resp.json()
    assert "mwrr" in perf_resp.json()

    # 5. Get holdings
    holdings_resp = client.get(f"/api/portfolio/{portfolio_id}/holdings")
    assert holdings_resp.status_code == 200
    assert len(holdings_resp.json()) == 1

    # 6. Get dividends
    div_resp = client.get(f"/api/portfolio/{portfolio_id}/dividends")
    assert div_resp.status_code == 200
    assert "projected_annual_income" in div_resp.json()

    # Clean up portfolio via db session directly
    db = SessionLocal()
    try:
        from backend.database.models import Portfolio, Transaction, PortfolioPosition
        db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).delete()
        db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == portfolio_id).delete()
        db.query(Portfolio).filter(Portfolio.id == portfolio_id).delete()
        db.commit()
    finally:
        db.close()

def test_simulation_apis():
    # Seed historical price data for backtest execution
    db = SessionLocal()
    today = date.today()
    start = today - timedelta(days=90)
    try:
        from backend.database.models import PriceHistory, Asset
        from decimal import Decimal
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        # Seed 35 prices ending today
        prices_to_add = []
        for i in range(35):
            d = today - timedelta(days=i)
            # Check if price already exists for this day
            exists = db.query(PriceHistory).filter(PriceHistory.asset_id == aapl.id, PriceHistory.date == d).first()
            if not exists:
                p = PriceHistory(
                    asset_id=aapl.id,
                    date=d,
                    open=Decimal("150.00"),
                    high=Decimal("155.00"),
                    low=Decimal("148.00"),
                    close=Decimal("150.00") + Decimal(str(i % 5)),
                    volume=1000000
                )
                prices_to_add.append(p)
        if prices_to_add:
            db.add_all(prices_to_add)
            db.commit()
    finally:
        db.close()

    # 1. Backtest Endpoint
    resp = client.post(
        "/api/simulation/backtest",
        json={
            "ticker": "AAPL",
            "strategy_name": "sma_cross",
            "start_date": start.isoformat(),
            "end_date": today.isoformat(),
            "initial_cash": 5000.0
        }
    )
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "AAPL"
    
    # 2. Monte Carlo Endpoint
    # Create temp portfolio
    create_resp = client.post("/api/portfolio/", json={"name": "API MC Portfolio"})
    port_id = create_resp.json()["portfolio"]["id"]
    
    mc_resp = client.post(
        "/api/simulation/monte-carlo",
        json={
            "portfolio_id": port_id,
            "projection_days": 10,
            "num_simulations": 10
        }
    )
    assert mc_resp.status_code == 200
    assert len(mc_resp.json()["p5"]) == 11

    # Clean up
    db = SessionLocal()
    try:
        from backend.database.models import Portfolio
        db.query(Portfolio).filter(Portfolio.id == port_id).delete()
        db.commit()
    finally:
        db.close()

def test_ai_apis():
    # Create temp portfolio
    create_resp = client.post("/api/portfolio/", json={"name": "API AI Portfolio"})
    port_id = create_resp.json()["portfolio"]["id"]

    # 1. Decision Session
    resp = client.post(
        "/api/ai/decision-session",
        json={
            "portfolio_id": port_id,
            "question": "Should we BUY AAPL stocks today?",
            "asset_ticker": "AAPL"
        }
    )
    assert resp.status_code == 200
    assert "final_decision" in resp.json()

    # 2. Log API
    logs_resp = client.get("/api/ai/logs")
    assert logs_resp.status_code == 200
    assert isinstance(logs_resp.json(), list)
    assert len(logs_resp.json()) > 0

    # Clean up
    db = SessionLocal()
    try:
        from backend.database.models import Portfolio, DecisionSession
        db.query(Portfolio).filter(Portfolio.id == port_id).delete()
        db.query(DecisionSession).filter(DecisionSession.question == "Should we BUY AAPL stocks today?").delete()
        db.commit()
    finally:
        db.close()
