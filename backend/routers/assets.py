from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date

from backend.database.connection import SessionLocal
from backend.database.models import Asset, PriceHistory, FinancialStatement, News
from backend.scheduler import scheduler_daemon

router = APIRouter(prefix="/assets", tags=["assets"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[Dict[str, Any]])
def list_assets(db: Session = Depends(get_db)):
    """List all active investment assets (stocks, indexes, crypto)."""
    assets = db.query(Asset).filter(Asset.is_active == True).all()
    return [
        {
            "id": a.id,
            "ticker": a.ticker,
            "name": a.name,
            "asset_type": a.asset_type,
            "sector": a.sector,
            "country": a.country,
            "currency": a.currency
        } for a in assets
    ]

@router.get("/{ticker}", response_model=Dict[str, Any])
def get_asset(ticker: str, db: Session = Depends(get_db)):
    """Get single asset metadata by ticker symbol."""
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")
    return {
        "id": asset.id,
        "ticker": asset.ticker,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "sector": asset.sector,
        "country": asset.country,
        "currency": asset.currency,
        "is_active": asset.is_active
    }

@router.get("/{ticker}/price", response_model=List[Dict[str, Any]])
def get_price_history(ticker: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get historical daily prices for a ticker."""
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")
        
    prices = (
        db.query(PriceHistory)
        .filter(PriceHistory.asset_id == asset.id)
        .order_by(PriceHistory.date.desc())
        .limit(limit)
        .all()
    )
    # Reverse to return chronological order
    prices.reverse()
    return [
        {
            "date": p.date.isoformat(),
            "open": float(p.open) if p.open else None,
            "high": float(p.high) if p.high else None,
            "low": float(p.low) if p.low else None,
            "close": float(p.close),
            "volume": p.volume
        } for p in prices
    ]

@router.get("/{ticker}/financials", response_model=List[Dict[str, Any]])
def get_financial_statements(ticker: str, db: Session = Depends(get_db)):
    """Get corporate financial statements for a ticker."""
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    statements = (
        db.query(FinancialStatement)
        .filter(FinancialStatement.asset_id == asset.id)
        .order_by(FinancialStatement.period.desc())
        .all()
    )
    return [
        {
            "period": s.period,
            "period_type": s.period_type,
            "revenue": float(s.revenue) if s.revenue else None,
            "net_income": float(s.net_income) if s.net_income else None,
            "operating_cash_flow": float(s.operating_cash_flow) if s.operating_cash_flow else None,
            "free_cash_flow": float(s.free_cash_flow) if s.free_cash_flow else None,
            "total_assets": float(s.total_assets) if s.total_assets else None,
            "total_liabilities": float(s.total_liabilities) if s.total_liabilities else None,
            "total_debt": float(s.total_debt) if s.total_debt else None,
            "eps": float(s.eps) if s.eps else None,
            "date": s.date.isoformat() if s.date else None
        } for s in statements
    ]

@router.get("/{ticker}/news", response_model=List[Dict[str, Any]])
def get_news(ticker: str, db: Session = Depends(get_db)):
    """Get recent news and news summaries for a ticker."""
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    news_list = (
        db.query(News)
        .filter(News.asset_id == asset.id)
        .order_by(News.published_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": n.id,
            "title": n.title,
            "url": n.url,
            "content": n.content,
            "source": n.source,
            "published_at": n.published_at.isoformat(),
            "summary": n.summary.summary if n.summary else None,
            "sentiment_score": float(n.summary.sentiment_score) if n.summary else None
        } for n in news_list
    ]

@router.post("/sync", response_model=Dict[str, Any])
def trigger_data_sync(db: Session = Depends(get_db)):
    """Manually trigger background collection and update jobs immediately."""
    results = scheduler_daemon.trigger_jobs_now(db)
    return {
        "status": "success",
        "message": "Manual data sync executed.",
        "results": {
            "yahoo_series_count": results.get("yahoo", {}).get("series_processed", 0),
            "fred_series_count": results.get("fred", {}).get("series_processed", 0),
            "recalculated_portfolios": len(results.get("portfolios", []))
        }
    }
