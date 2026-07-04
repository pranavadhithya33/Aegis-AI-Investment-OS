from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import date
from pydantic import BaseModel, Field

from backend.database.connection import SessionLocal
from backend.simulation.backtester import BacktestEngine
from backend.simulation.monte_carlo import MonteCarloSimulator

router = APIRouter(prefix="/simulation", tags=["simulation"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic validation models
class BacktestRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")
    strategy_name: str = Field(..., description="sma_cross, rsi_bounds")
    start_date: date
    end_date: date
    initial_cash: float = 10000.0

class MonteCarloRequest(BaseModel):
    portfolio_id: int
    projection_days: int = 252
    num_simulations: int = 250

@router.post("/backtest", response_model=Dict[str, Any])
def run_strategy_backtest(payload: BacktestRequest, db: Session = Depends(get_db)):
    """Runs a historical backtest of a strategy on an asset ticker."""
    try:
        results = BacktestEngine.run_backtest(
            db=db,
            ticker=payload.ticker,
            strategy_name=payload.strategy_name,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_cash=payload.initial_cash
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@router.post("/monte-carlo", response_model=Dict[str, Any])
def run_portfolio_monte_carlo(payload: MonteCarloRequest, db: Session = Depends(get_db)):
    """Runs a future Monte Carlo return simulation on a portfolio."""
    try:
        results = MonteCarloSimulator.run_simulation(
            db=db,
            portfolio_id=payload.portfolio_id,
            projection_days=payload.projection_days,
            num_simulations=payload.num_simulations
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monte Carlo failed: {str(e)}")
