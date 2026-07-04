import numpy as np
import pandas as pd
from datetime import date
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.database.models import Portfolio, PortfolioPosition, PriceHistory, Asset

class MonteCarloSimulator:
    """
    Simulates future portfolio values using historical asset returns, covariances, 
    and weights via a multivariate normal Monte Carlo projection.
    """

    @classmethod
    def run_simulation(
        cls,
        db: Session,
        portfolio_id: int,
        projection_days: int = 252,
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Projects portfolio value forward based on historical returns distribution
        of the underlying assets.
        """
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio ID {portfolio_id} not found")

        positions = (
            db.query(PortfolioPosition)
            .filter(PortfolioPosition.portfolio_id == portfolio_id)
            .all()
        )

        cash = float(portfolio.cash_balance)

        if not positions:
            # Portfolio has only cash: future values are flat cash balances
            flat_path = [cash] * (projection_days + 1)
            return {
                "portfolio_id": portfolio_id,
                "days": list(range(projection_days + 1)),
                "p5": flat_path,
                "p50": flat_path,
                "p95": flat_path,
                "starting_value": cash,
                "holdings_simulated": 0
            }

        # Retrieve 1 year of historical prices for each asset in the portfolio
        asset_returns: Dict[str, pd.Series] = {}
        starting_holdings_value = 0.0
        position_values: Dict[str, float] = {}

        for pos in positions:
            asset = pos.asset
            prices_rec = (
                db.query(PriceHistory)
                .filter(PriceHistory.asset_id == asset.id)
                .order_by(PriceHistory.date.asc())
                .all()
            )
            
            if len(prices_rec) < 5:
                # Insufficient history, skip asset return simulation
                continue

            closes = [float(p.close) for p in prices_rec]
            dates = [p.date for p in prices_rec]
            
            ser = pd.Series(closes, index=pd.to_datetime(dates))
            pct_returns = ser.pct_change().dropna()
            asset_returns[asset.ticker] = pct_returns

            # Calculate current position value
            latest_price = closes[-1]
            pos_val = float(pos.shares) * latest_price
            starting_holdings_value += pos_val
            position_values[asset.ticker] = pos_val

        if not asset_returns:
            # If no assets had enough price history, return flat cash + base asset values
            total_start = cash + starting_holdings_value
            flat_path = [total_start] * (projection_days + 1)
            return {
                "portfolio_id": portfolio_id,
                "days": list(range(projection_days + 1)),
                "p5": flat_path,
                "p50": flat_path,
                "p95": flat_path,
                "starting_value": total_start,
                "holdings_simulated": 0
            }

        # Align all return series into a single DataFrame
        df_returns = pd.DataFrame(asset_returns).dropna()
        if len(df_returns) < 5:
            # Backup: return flat
            total_start = cash + starting_holdings_value
            flat_path = [total_start] * (projection_days + 1)
            return {
                "portfolio_id": portfolio_id,
                "days": list(range(projection_days + 1)),
                "p5": flat_path,
                "p50": flat_path,
                "p95": flat_path,
                "starting_value": total_start,
                "holdings_simulated": 0
            }

        # Calculate mean returns and covariance matrix
        mean_returns = df_returns.mean().values
        cov_matrix = df_returns.cov().values

        tickers = list(df_returns.columns)
        num_assets = len(tickers)

        # Initial values for simulation
        # portfolio_sims will store the total value of each simulation path over time
        # shape: (projection_days + 1, num_simulations)
        portfolio_sims = np.zeros((projection_days + 1, num_simulations))
        portfolio_sims[0, :] = cash + starting_holdings_value

        # Track simulated values of each individual asset position
        # shape: (num_assets, num_simulations)
        current_assets_values = np.zeros((num_assets, num_simulations))
        for idx, ticker in enumerate(tickers):
            current_assets_values[idx, :] = position_values[ticker]

        # Generate future random returns from multivariate normal distribution
        # daily_sim_returns shape: (projection_days, num_simulations, num_assets)
        # Using a loop to project step-by-step
        for day in range(1, projection_days + 1):
            # Sample returns for this step: size = (num_simulations,)
            # returns_sample shape: (num_simulations, num_assets)
            returns_sample = np.random.multivariate_normal(mean_returns, cov_matrix, size=num_simulations)
            
            # Update individual asset values
            for idx in range(num_assets):
                # asset_val_t = asset_val_{t-1} * (1 + return)
                current_assets_values[idx, :] *= (1.0 + returns_sample[:, idx])

            # Total portfolio value = cash + sum of all asset holdings
            portfolio_sims[day, :] = cash + np.sum(current_assets_values, axis=0)

        # Compute percentiles at each step (axis=1 calculates percentiles across the simulations)
        p5 = np.percentile(portfolio_sims, 5, axis=1)
        p50 = np.percentile(portfolio_sims, 50, axis=1)
        p95 = np.percentile(portfolio_sims, 95, axis=1)

        return {
            "portfolio_id": portfolio_id,
            "days": list(range(projection_days + 1)),
            "p5": [float(v) for v in p5],
            "p50": [float(v) for v in p50],
            "p95": [float(v) for v in p95],
            "starting_value": cash + starting_holdings_value,
            "holdings_simulated": num_assets
        }
