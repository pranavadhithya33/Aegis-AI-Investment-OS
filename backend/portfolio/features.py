import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.database.models import PriceHistory, Asset, EconomicEvent
from backend.cache.manager import cache_manager

class FeatureStore:
    """
    Calculates and caches quantitative features (technical and risk metrics)
    for watchlisted and portfolio assets.
    """

    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < window:
            return None
        return float(prices.rolling(window=window).mean().iloc[-1])

    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index (RSI)."""
        if len(prices) < window + 1:
            return None
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return float(val) if not pd.isna(val) else None

    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> Optional[float]:
        """Calculate maximum peak-to-trough drawdown."""
        if prices.empty:
            return None
        cumulative_max = prices.cummax()
        drawdown = (prices - cumulative_max) / cumulative_max
        return float(drawdown.min())

    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.04) -> Optional[float]:
        """
        Calculate annualized Sharpe Ratio based on daily returns.
        risk_free_rate is expressed as an annual rate (e.g. 0.04 for 4%).
        """
        if len(returns) < 5:
            return None
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = returns - daily_rf
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()
        
        if std_excess == 0 or pd.isna(std_excess):
            return 0.0
            
        daily_sharpe = mean_excess / std_excess
        # Annualize
        return float(daily_sharpe * np.sqrt(252))

    @staticmethod
    def calculate_beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> Optional[float]:
        """Calculate Beta relative to S&P 500 or equivalent benchmark index."""
        # Align series by date index
        df = pd.concat([asset_returns, benchmark_returns], axis=1, join="inner")
        if len(df) < 10:
            return None
        
        cov = df.cov().iloc[0, 1]
        market_var = df.iloc[:, 1].var()
        
        if market_var == 0 or pd.isna(market_var):
            return 1.0
            
        return float(cov / market_var)

    @classmethod
    def get_asset_features(cls, db: Session, asset_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Retrieves pricing, computes metrics, and caches features.
        Risk-free rate is queried dynamically from our economic yield data (e.g. 10Y Yield).
        """
        cache_key = f"features_asset_{asset_id}"
        if use_cache:
            cached = cache_manager.get(cache_key)
            if cached:
                return cached

        # Fetch asset info
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset ID {asset_id} not found")

        # Fetch 2 years of daily price history
        prices_rec = (
            db.query(PriceHistory)
            .filter(PriceHistory.asset_id == asset_id)
            .order_by(PriceHistory.date.asc())
            .all()
        )
        
        if not prices_rec:
            return {
                "ticker": asset.ticker,
                "sma_50": None, "sma_200": None, "rsi_14": None,
                "max_drawdown": None, "sharpe_ratio": None, "beta": None
            }

        df_prices = pd.Series(
            [float(p.close) for p in prices_rec],
            index=pd.to_datetime([p.date for p in prices_rec])
        )
        daily_returns = df_prices.pct_change().dropna()

        # Dynamic risk-free rate: read 10Y Yield (^TNX or DGS10) from EconomicEvent
        rf_rate = 0.04  # Default 4%
        rf_event = (
            db.query(EconomicEvent)
            .filter(EconomicEvent.series_id.in_(["DGS10", "^TNX"]))
            .order_by(EconomicEvent.date.desc())
            .first()
        )
        if rf_event:
            # Yield indices (like ^TNX) represent 4.25% as 4.25. Convert to 0.0425
            rf_rate = float(rf_event.value) / 100.0 if rf_event.value > 1.0 else float(rf_event.value)

        # Compute benchmark returns (e.g., ^GSPC index) for Beta
        beta_val = None
        benchmark_asset = db.query(Asset).filter(Asset.ticker == "^GSPC").first()
        if benchmark_asset and benchmark_asset.id != asset_id:
            bench_prices_rec = (
                db.query(PriceHistory)
                .filter(PriceHistory.asset_id == benchmark_asset.id)
                .order_by(PriceHistory.date.asc())
                .all()
            )
            if bench_prices_rec:
                df_bench = pd.Series(
                    [float(p.close) for p in bench_prices_rec],
                    index=pd.to_datetime([p.date for p in bench_prices_rec])
                )
                bench_returns = df_bench.pct_change().dropna()
                beta_val = cls.calculate_beta(daily_returns, bench_returns)

        features = {
            "ticker": asset.ticker,
            "sma_50": cls.calculate_sma(df_prices, 50),
            "sma_200": cls.calculate_sma(df_prices, 200),
            "rsi_14": cls.calculate_rsi(df_prices, 14),
            "max_drawdown": cls.calculate_max_drawdown(df_prices),
            "sharpe_ratio": cls.calculate_sharpe_ratio(daily_returns, risk_free_rate=rf_rate),
            "beta": beta_val if beta_val is not None else 1.0
        }

        # Cache feature metrics for 24 hours (86,400 seconds)
        cache_manager.set(cache_key, features, expire_seconds=86400)
        return features
