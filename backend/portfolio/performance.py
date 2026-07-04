from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np

from backend.database.models import Portfolio, Transaction, PriceHistory, PortfolioPosition

class PortfolioPerformance:
    """
    Computes advanced portfolio performance return metrics:
    - Time-Weighted Rate of Return (TWRR)
    - Money-Weighted Rate of Return (MWRR / IRR)
    """

    @classmethod
    def get_portfolio_value_on_date(cls, db: Session, portfolio_id: int, target_date: date) -> Decimal:
        """
        Calculates the total value (cash + assets) of a portfolio at a specific historical date.
        """
        # Replay transactions up to target_date
        transactions = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .filter(Transaction.date <= datetime.combine(target_date, datetime.max.time()))
            .order_by(Transaction.date.asc(), Transaction.id.asc())
        ).all()

        cash_balance = Decimal("0")
        holdings: Dict[int, Decimal] = {}  # asset_id -> shares

        for tx in transactions:
            tx_type = tx.transaction_type.upper()
            size = tx.size or Decimal("0")
            price = tx.price or Decimal("0")
            commission = tx.commission or Decimal("0")
            
            if tx_type == "DEPOSIT":
                cash_balance += size
            elif tx_type == "WITHDRAW":
                cash_balance -= size
            elif tx_type == "BUY" and tx.asset_id:
                cash_balance -= (size * price + commission)
                holdings[tx.asset_id] = holdings.get(tx.asset_id, Decimal("0")) + size
            elif tx_type == "SELL" and tx.asset_id:
                cash_balance += (size * price - commission)
                holdings[tx.asset_id] = holdings.get(tx.asset_id, Decimal("0")) - size
                if holdings[tx.asset_id] <= 0:
                    holdings.pop(tx.asset_id)

        # Value assets on this target date
        assets_value = Decimal("0")
        for asset_id, shares in holdings.items():
            # Get closest price on or before target_date
            price_rec = (
                db.query(PriceHistory)
                .filter(PriceHistory.asset_id == asset_id)
                .filter(PriceHistory.date <= target_date)
                .order_by(PriceHistory.date.desc())
                .first()
            )
            price = price_rec.close if price_rec else Decimal("0")
            assets_value += shares * price

        return cash_balance + assets_value

    @classmethod
    def calculate_twrr(cls, db: Session, portfolio_id: int) -> float:
        """
        Time-Weighted Rate of Return (TWRR).
        Breaks the timeline into sub-periods separated by external cash flows (DEPOSIT/WITHDRAW),
        calculates returns for each sub-period, and compounds them.
        """
        # Get all external cash flows sorted chronologically
        cash_flows = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .filter(Transaction.transaction_type.in_(["DEPOSIT", "WITHDRAW"]))
            .order_by(Transaction.date.asc())
        ).all()

        if not cash_flows:
            return 0.0

        # Sub-periods start date and values
        start_date = cash_flows[0].date.date()
        today = date.today()

        if start_date >= today:
            return 0.0

        sub_periods: List[float] = []
        current_start_val = Decimal("0")
        current_date = start_date

        for i, cf in enumerate(cash_flows):
            cf_date = cf.date.date()
            cf_type = cf.transaction_type.upper()
            cf_amount = cf.size
            
            # Value right before the cash flow
            val_before_cf = cls.get_portfolio_value_on_date(db, portfolio_id, cf_date - timedelta(days=1))
            
            if i > 0 and current_start_val > 0:
                # Calculate return for sub-period prior to this cash flow
                sub_return = float((val_before_cf - current_start_val) / current_start_val)
                sub_periods.append(sub_return)
            
            # Start value for the next sub-period includes the cash flow
            current_start_val = val_before_cf + (cf_amount if cf_type == "DEPOSIT" else -cf_amount)
            current_date = cf_date

        # Compound with the final sub-period up to today
        final_val = cls.get_portfolio_value_on_date(db, portfolio_id, today)
        if current_start_val > 0:
            final_return = float((final_val - current_start_val) / current_start_val)
            sub_periods.append(final_return)

        # Compound all returns: TWRR = PROD(1 + R_i) - 1
        twrr = 1.0
        for r in sub_periods:
            twrr *= (1.0 + r)
        
        return twrr - 1.0

    @classmethod
    def calculate_mwrr(cls, db: Session, portfolio_id: int) -> float:
        """
        Money-Weighted Rate of Return (MWRR / IRR).
        Solves for the rate 'r' that equates the initial investment and subsequent cash flows
        to the ending portfolio value using a bisection solver.
        """
        # Retrieve all external cash flows (DEPOSIT/WITHDRAW)
        cash_flows = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .filter(Transaction.transaction_type.in_(["DEPOSIT", "WITHDRAW"]))
            .order_by(Transaction.date.asc())
        ).all()

        if not cash_flows:
            return 0.0

        start_date = cash_flows[0].date.date()
        end_date = date.today()
        
        # Cash flows: (days_from_start, cash_flow_amount)
        # Deposits are negative (cash into portfolio), withdrawals are positive (cash out of portfolio)
        # Final portfolio value is treated as positive terminal cash flow
        flows: List[Dict[str, Any]] = []
        for cf in cash_flows:
            days = (cf.date.date() - start_date).days
            amount = float(cf.size)
            if cf.transaction_type.upper() == "DEPOSIT":
                # Cash flowing in
                flows.append({"days": days, "amount": -amount})
            else:
                # Cash flowing out
                flows.append({"days": days, "amount": amount})

        # Add final terminal value as positive inflow (cash back to investor)
        terminal_val = float(cls.get_portfolio_value_on_date(db, portfolio_id, end_date))
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return 0.0
            
        flows.append({"days": total_days, "amount": terminal_val})

        # Bisection solver to solve for r (annual IRR)
        # NPV = Sum( CF_t / (1 + r)^(t / 365) )
        def calculate_npv(r_annual: float) -> float:
            npv = 0.0
            for f in flows:
                t_years = f["days"] / 365.0
                npv += f["amount"] / ((1.0 + r_annual) ** t_years)
            return npv

        # Bisection range: -90% to +1000%
        low = -0.90
        high = 10.0
        
        # Check signs of NPV at boundaries
        npv_low = calculate_npv(low)
        npv_high = calculate_npv(high)
        
        if npv_low * npv_high > 0:
            # If both have the same sign, we can't find a root in this range.
            # Return simple rate of return as backup
            total_invested = sum(-f["amount"] for f in flows if f["amount"] < 0)
            if total_invested > 0:
                return (terminal_val - total_invested) / total_invested
            return 0.0

        for _ in range(100):
            mid = (low + high) / 2.0
            npv_mid = calculate_npv(mid)
            if abs(npv_mid) < 1e-6:
                return mid
            if npv_mid * npv_low < 0:
                high = mid
            else:
                low = mid
                npv_low = npv_mid

        return (low + high) / 2.0
