import numpy as np
import pandas as pd
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import PriceHistory, Asset
from backend.portfolio.features import FeatureStore

class BacktestEngine:
    """
    Event-driven backtester to simulate trading strategies on historical price series.
    """

    @classmethod
    def run_backtest(
        cls,
        db: Session,
        ticker: str,
        strategy_name: str,
        start_date: date,
        end_date: date,
        initial_cash: float = 10000.0,
        commission: float = 5.0
    ) -> Dict[str, Any]:
        """
        Runs a historical simulation for a ticker using a chosen strategy.
        Supported strategies: 'sma_cross', 'rsi_bounds'
        """
        # Fetch asset
        asset = db.query(Asset).filter(Asset.ticker == ticker).first()
        if not asset:
            raise ValueError(f"Asset '{ticker}' not found")

        # Fetch chronological price history
        prices_rec = (
            db.query(PriceHistory)
            .filter(PriceHistory.asset_id == asset.id)
            .filter(PriceHistory.date >= start_date)
            .filter(PriceHistory.date <= end_date)
            .order_by(PriceHistory.date.asc())
        ).all()

        if len(prices_rec) < 20:
            raise ValueError(f"Insufficient historical prices found for {ticker} in range.")

        # Load into a pandas DataFrame for technical calculations
        df = pd.DataFrame([
            {
                "date": p.date,
                "close": float(p.close),
                "open": float(p.open) if p.open else float(p.close),
                "high": float(p.high) if p.high else float(p.close),
                "low": float(p.low) if p.low else float(p.close),
            } for p in prices_rec
        ])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

        # Generate signals beforehand (event-driven simulation will loop day-by-day reading these signals)
        signals = cls._generate_signals(df, strategy_name)

        # Simulation states
        cash = initial_cash
        shares = 0.0
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        # Iterate day-by-day
        for curr_date, row in df.iterrows():
            close_price = row["close"]
            signal = signals.get(curr_date, 0) # 1: Buy, -1: Sell, 0: Hold

            # 1. Evaluate trades
            if signal == 1 and shares == 0:
                # Buy all-in (minus commission)
                buyable_cash = cash - commission
                if buyable_cash > 0:
                    shares_bought = buyable_cash / close_price
                    shares = shares_bought
                    cash = 0.0
                    trades.append({
                        "date": curr_date.isoformat(),
                        "type": "BUY",
                        "price": close_price,
                        "shares": shares_bought,
                        "commission": commission,
                        "cash_remaining": cash
                    })
            elif signal == -1 and shares > 0:
                # Sell all holdings
                proceeds = (shares * close_price) - commission
                cash = proceeds
                trades.append({
                    "date": curr_date.isoformat(),
                    "type": "SELL",
                    "price": close_price,
                    "shares": shares,
                    "commission": commission,
                    "cash_remaining": cash
                })
                shares = 0.0

            # 2. Record daily equity value
            portfolio_val = cash + (shares * close_price)
            equity_curve.append({
                "date": curr_date.isoformat(),
                "value": portfolio_val
            })

        # Calculate metrics
        df_equity = pd.Series([e["value"] for e in equity_curve], index=df.index)
        daily_returns = df_equity.pct_change().dropna()
        
        cumulative_return = (df_equity.iloc[-1] - initial_cash) / initial_cash
        
        # Annualized return
        total_days = (df.index[-1] - df.index[0]).days
        years = total_days / 365.25
        cagr = (df_equity.iloc[-1] / initial_cash) ** (1 / years) - 1.0 if years > 0 and df_equity.iloc[-1] > 0 else 0.0
        
        # Annualized Volatility
        vol = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0.0
        
        # Sharpe (assumed risk-free 4%)
        excess_returns = daily_returns - (0.04 / 252)
        sharpe = (excess_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0.0

        # Drawdown
        cum_max = df_equity.cummax()
        drawdown = (df_equity - cum_max) / cum_max
        max_drawdown = drawdown.min()

        return {
            "ticker": ticker,
            "strategy": strategy_name,
            "initial_value": initial_cash,
            "final_value": df_equity.iloc[-1],
            "cumulative_return": float(cumulative_return),
            "cagr": float(cagr),
            "volatility": float(vol) if not pd.isna(vol) else 0.0,
            "sharpe_ratio": float(sharpe) if not pd.isna(sharpe) else 0.0,
            "max_drawdown": float(max_drawdown) if not pd.isna(max_drawdown) else 0.0,
            "trades_count": len(trades),
            "trades": trades,
            "equity_curve": equity_curve
        }

    @staticmethod
    def _generate_signals(df: pd.DataFrame, strategy_name: str) -> Dict[Any, int]:
        """
        Generates day-by-day trading signals.
        Returns a dict mapping Date to signal: 1 (BUY), -1 (SELL), 0 (HOLD).
        """
        signals = {}
        closes = df["close"]

        if strategy_name == "sma_cross":
            # SMA Crossover Strategy (SMA-20 and SMA-50)
            sma_fast = closes.rolling(window=10).mean()
            sma_slow = closes.rolling(window=30).mean()
            
            position = 0 # 0: flat, 1: long
            for curr_date, close in closes.items():
                fast = sma_fast.loc[curr_date]
                slow = sma_slow.loc[curr_date]
                
                if pd.isna(fast) or pd.isna(slow):
                    continue
                    
                if fast > slow and position == 0:
                    signals[curr_date] = 1 # BUY
                    position = 1
                elif fast < slow and position == 1:
                    signals[curr_date] = -1 # SELL
                    position = 0
                    
        elif strategy_name == "rsi_bounds":
            # RSI Strategy (Buy < 30, Sell > 70)
            # Fetch RSI dynamically
            window = 14
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            position = 0
            for curr_date, val in rsi.items():
                if pd.isna(val):
                    continue
                if val < 30 and position == 0:
                    signals[curr_date] = 1 # BUY
                    position = 1
                elif val > 70 and position == 1:
                    signals[curr_date] = -1 # SELL
                    position = 0
        
        return signals
