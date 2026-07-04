from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.database.models import (
    Portfolio, PortfolioPosition, Transaction, PriceHistory
)

class PortfolioTracker:
    """
    Computes portfolio positions, average cost basis, and cash balances
    by replaying transaction histories from the database.
    """
    
    @staticmethod
    def recalculate_portfolio(db: Session, portfolio_id: int) -> Dict[str, Any]:
        """
        Replays all transactions for a given portfolio to rebuild cash balances
        and portfolio positions.
        """
        # Fetch the portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio ID {portfolio_id} not found")

        # Fetch transactions sorted chronologically
        transactions = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.date.asc(), Transaction.id.asc())
        ).all()

        # Temporary tracking structures
        cash_balance = Decimal("0")
        holdings: Dict[int, Dict[str, Any]] = {} # asset_id -> {shares, average_cost}

        for tx in transactions:
            tx_type = tx.transaction_type.upper()
            size = tx.size or Decimal("0")
            price = tx.price or Decimal("0")
            commission = tx.commission or Decimal("0")
            
            if tx_type == "DEPOSIT":
                cash_balance += size
            elif tx_type == "WITHDRAW":
                cash_balance -= size
                
            elif tx_type == "BUY":
                if not tx.asset_id:
                    continue
                total_cost = (size * price) + commission
                # Deduct cash
                cash_balance -= total_cost
                
                # Update holding cost basis
                if tx.asset_id not in holdings:
                    holdings[tx.asset_id] = {
                        "shares": size,
                        "average_cost": total_cost / size if size > 0 else Decimal("0")
                    }
                else:
                    curr_qty = holdings[tx.asset_id]["shares"]
                    curr_cost = holdings[tx.asset_id]["average_cost"]
                    new_qty = curr_qty + size
                    if new_qty > 0:
                        new_cost = ((curr_qty * curr_cost) + total_cost) / new_qty
                    else:
                        new_cost = Decimal("0")
                    holdings[tx.asset_id] = {
                        "shares": new_qty,
                        "average_cost": new_cost
                    }
                    
            elif tx_type == "SELL":
                if not tx.asset_id:
                    continue
                total_proceeds = (size * price) - commission
                # Add cash
                cash_balance += total_proceeds
                
                # Update holding
                if tx.asset_id in holdings:
                    curr_qty = holdings[tx.asset_id]["shares"]
                    curr_cost = holdings[tx.asset_id]["average_cost"]
                    new_qty = curr_qty - size
                    
                    if new_qty <= 0:
                        # Holding completely liquidated
                        holdings.pop(tx.asset_id)
                    else:
                        # Cost basis remains the same for remaining shares under average cost method
                        holdings[tx.asset_id] = {
                            "shares": new_qty,
                            "average_cost": curr_cost
                        }

        # Clear existing holdings in DB to overwrite with fresh state
        db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == portfolio_id).delete()
        
        # Save positions
        for asset_id, h_info in holdings.items():
            pos = PortfolioPosition(
                portfolio_id=portfolio_id,
                asset_id=asset_id,
                shares=h_info["shares"],
                average_cost=h_info["average_cost"]
            )
            db.add(pos)
            
        # Update Portfolio cash balance
        portfolio.cash_balance = cash_balance
        db.commit()

        # Compute current asset and total portfolio values
        total_asset_value = Decimal("0")
        holdings_summary = []

        for asset_id, h_info in holdings.items():
            latest_price_rec = (
                db.query(PriceHistory)
                .filter(PriceHistory.asset_id == asset_id)
                .order_by(PriceHistory.date.desc())
                .first()
            )
            current_price = latest_price_rec.close if latest_price_rec else Decimal("0")
            market_value = h_info["shares"] * current_price
            total_asset_value += market_value
            
            holdings_summary.append({
                "asset_id": asset_id,
                "shares": float(h_info["shares"]),
                "average_cost": float(h_info["average_cost"]),
                "current_price": float(current_price),
                "market_value": float(market_value)
            })

        total_val = total_asset_value + cash_balance

        return {
            "portfolio_id": portfolio_id,
            "cash_balance": float(cash_balance),
            "total_value": float(total_val),
            "asset_value": float(total_asset_value),
            "holdings": holdings_summary
        }
