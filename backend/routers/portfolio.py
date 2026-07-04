from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal

from backend.database.connection import SessionLocal
from backend.database.models import Portfolio, PortfolioPosition, Transaction, Asset
from backend.portfolio.tracker import PortfolioTracker
from backend.portfolio.performance import PortfolioPerformance
from backend.portfolio.dividends import DividendTracker

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas for input validation
class PortfolioCreate(BaseModel):
    name: str

class TransactionCreate(BaseModel):
    asset_ticker: Optional[str] = None
    transaction_type: str = Field(..., description="DEPOSIT, WITHDRAW, BUY, SELL")
    size: float = Field(..., description="Amount of cash or number of shares")
    price: Optional[float] = None
    commission: float = 0.0

@router.get("/", response_model=List[Dict[str, Any]])
def list_portfolios(db: Session = Depends(get_db)):
    """List all portfolios."""
    portfolios = db.query(Portfolio).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "cash_balance": float(p.cash_balance),
            "created_at": p.created_at.isoformat()
        } for p in portfolios
    ]

@router.post("/", response_model=Dict[str, Any])
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new investment portfolio."""
    port = Portfolio(name=payload.name, cash_balance=Decimal("0.00"))
    db.add(port)
    db.commit()
    db.refresh(port)
    return {
        "status": "success",
        "portfolio": {
            "id": port.id,
            "name": port.name,
            "cash_balance": float(port.cash_balance)
        }
    }

@router.get("/{portfolio_id}", response_model=Dict[str, Any])
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get portfolio summary."""
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    # Recalculate summary metrics dynamically
    summary = PortfolioTracker.recalculate_portfolio(db, portfolio_id)
    return summary

@router.get("/{portfolio_id}/holdings", response_model=List[Dict[str, Any]])
def get_portfolio_holdings(portfolio_id: int, db: Session = Depends(get_db)):
    """Get active holdings positions with weights and market values."""
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    summary = PortfolioTracker.recalculate_portfolio(db, portfolio_id)
    return summary["holdings"]

@router.get("/{portfolio_id}/dividends", response_model=Dict[str, Any])
def get_portfolio_dividends(portfolio_id: int, db: Session = Depends(get_db)):
    """Get projected dividend metrics and income schedules."""
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    return DividendTracker.calculate_portfolio_dividends(db, portfolio_id)

@router.get("/{portfolio_id}/performance", response_model=Dict[str, Any])
def get_portfolio_performance(portfolio_id: int, db: Session = Depends(get_db)):
    """Get TWRR and MWRR returns for the portfolio."""
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    twrr = PortfolioPerformance.calculate_twrr(db, portfolio_id)
    mwrr = PortfolioPerformance.calculate_mwrr(db, portfolio_id)
    
    return {
        "portfolio_id": portfolio_id,
        "twrr": float(twrr),
        "mwrr": float(mwrr)
    }

@router.post("/{portfolio_id}/transaction", response_model=Dict[str, Any])
def add_transaction(portfolio_id: int, payload: TransactionCreate, db: Session = Depends(get_db)):
    """Record a buy/sell trade or cash deposit/withdrawal transaction."""
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    asset_id = None
    if payload.asset_ticker:
        asset = db.query(Asset).filter(Asset.ticker == payload.asset_ticker.upper()).first()
        if not asset:
            raise HTTPException(
                status_code=400, 
                detail=f"Asset {payload.asset_ticker} not seeded. Add asset metadata first."
            )
        asset_id = asset.id

    # Create transaction
    tx = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset_id,
        transaction_type=payload.transaction_type.upper(),
        size=Decimal(str(payload.size)),
        price=Decimal(str(payload.price)) if payload.price else None,
        commission=Decimal(str(payload.commission)),
        date=datetime.utcnow()
    )
    db.add(tx)
    db.commit()

    # Recalculate portfolio state
    recalc = PortfolioTracker.recalculate_portfolio(db, portfolio_id)
    
    return {
        "status": "success",
        "transaction_id": tx.id,
        "portfolio_summary": recalc
    }

@router.get("/{portfolio_id}/transactions", response_model=List[Dict[str, Any]])
def list_transactions(portfolio_id: int, db: Session = Depends(get_db)):
    """Get all chronological transactions for a portfolio."""
    txs = (
        db.query(Transaction)
        .filter(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.date.desc())
        .all()
    )
    return [
        {
            "id": t.id,
            "asset_ticker": t.asset.ticker if t.asset else None,
            "transaction_type": t.transaction_type,
            "size": float(t.size),
            "price": float(t.price) if t.price else None,
            "commission": float(t.commission),
            "date": t.date.isoformat()
        } for t in txs
    ]
