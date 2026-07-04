from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import yfinance as yf

from backend.database.models import Portfolio, PortfolioPosition, Asset
from backend.cache.manager import cache_manager

class DividendTracker:
    """
    Calculates portfolio dividend metrics and projects annual dividend income.
    """

    @staticmethod
    def get_asset_dividend_data(ticker: str) -> Dict[str, float]:
        """
        Retrieves dividend rate and yield for a given ticker.
        Checks cache first, then queries yfinance.
        """
        cache_key = f"yf_fundamentals_{ticker}"
        cached = cache_manager.get(cache_key)
        
        # If cache exists, check if raw yfinance info is nested or query info directly
        # In our yahoo plugin, we cache a custom dict. Let's fallback to yfinance if keys are missing.
        dividend_rate = 0.0
        dividend_yield = 0.0

        try:
            # We can check cache. Let's store raw info to make this fully reliable.
            raw_info_key = f"yf_raw_info_{ticker}"
            info = cache_manager.get(raw_info_key)
            
            if not info:
                # Fetch fresh info
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                # Cache raw info for 7 days
                cache_manager.set(raw_info_key, info, expire_seconds=604800)

            if info:
                dividend_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate") or 0.0
                dividend_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield") or 0.0
                
        except Exception:
            # If yfinance fails, return zeros
            pass

        return {
            "dividend_rate": float(dividend_rate),
            "dividend_yield": float(dividend_yield)
        }

    @classmethod
    def calculate_portfolio_dividends(cls, db: Session, portfolio_id: int) -> Dict[str, Any]:
        """
        Calculates projected annual dividend income and weighted dividend yield
        for the given portfolio.
        """
        # Fetch current positions
        positions = (
            db.query(PortfolioPosition)
            .filter(PortfolioPosition.portfolio_id == portfolio_id)
            .all()
        )

        total_portfolio_value = Decimal("0")
        total_projected_income = Decimal("0")
        position_details = []

        # Determine total portfolio asset value + cash balance
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        cash = portfolio.cash_balance if portfolio else Decimal("0")
        
        # Gather position market values
        for pos in positions:
            asset = db.query(Asset).filter(Asset.id == pos.asset_id).first()
            if not asset:
                continue
            
            # Fetch latest price
            latest_price_rec = (
                pos.asset.prices[-1] if pos.asset.prices else None
            )
            # Safe price fallback
            price = latest_price_rec.close if latest_price_rec else pos.average_cost
            market_value = pos.shares * price
            total_portfolio_value += market_value

            # Get dividend info
            div_data = cls.get_asset_dividend_data(asset.ticker)
            div_rate = Decimal(str(div_data["dividend_rate"]))
            div_yield = Decimal(str(div_data["dividend_yield"]))

            # Projected Income = shares * dividend_rate
            projected_income = pos.shares * div_rate
            total_projected_income += projected_income

            position_details.append({
                "ticker": asset.ticker,
                "shares": float(pos.shares),
                "market_value": float(market_value),
                "dividend_rate": float(div_rate),
                "dividend_yield": float(div_yield),
                "projected_annual_income": float(projected_income)
            })

        total_value = total_portfolio_value + cash
        weighted_yield = Decimal("0")
        
        if total_portfolio_value > 0:
            # Yield weighted by market value of assets
            total_weighted_yield = sum(
                Decimal(str(pos["market_value"])) * Decimal(str(pos["dividend_yield"]))
                for pos in position_details
            )
            weighted_yield = total_weighted_yield / total_portfolio_value

        return {
            "portfolio_id": portfolio_id,
            "total_value": float(total_value),
            "cash_balance": float(cash),
            "projected_annual_income": float(total_projected_income),
            "portfolio_dividend_yield": float(weighted_yield),
            "positions": position_details
        }
