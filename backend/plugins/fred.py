import pandas as pd
import httpx
import yfinance as yf
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.plugins.base import BasePlugin
from backend.database.models import EconomicEvent
from backend.config.settings import settings

class FredPlugin(BasePlugin):
    """
    Macroeconomic Data Collector.
    Fetches series from St. Louis Fed (FRED) if API key is provided.
    Falls back to Yahoo Finance Treasury Yield indices if no key is present.
    """
    def __init__(self, **kwargs):
        super().__init__(
            plugin_id="fred_macro",
            name="FRED & Macro Yields Collector",
            **kwargs
        )
        self.api_key = settings.FRED_API_KEY

        # Mapping of FRED series IDs to human names
        self.fred_series = {
            "FEDFUNDS": "Effective Federal Funds Rate",
            "CPIAUCSL": "Consumer Price Index (CPI-U)",
            "UNRATE": "Civilian Unemployment Rate",
            "DGS10": "10-Year Treasury Constant Maturity Rate",
            "DGS2": "2-Year Treasury Constant Maturity Rate",
            "T10Y2Y": "10-Year Treasury Constant Maturity Minus 2-Year"
        }

        # Alternative Yahoo Finance tickers for yield proxies when FRED key is absent
        self.yahoo_yield_tickers = {
            "^IRX": "13-Week Treasury Bill (3M Yield)",
            "^FVX": "5-Year Treasury Note Yield",
            "^TNX": "10-Year Treasury Note Yield",
            "^TYX": "30-Year Treasury Bond Yield"
        }

    def fetch(self, series_id: str, start: str, end: str, **kwargs) -> Optional[List[Dict[str, Any]]]:
        """Fetch macroeconomic series data using FRED or Yahoo Yields depending on API key."""
        if self.api_key:
            return self.fetch_fred_series(series_id, start, end)
        else:
            return self.fetch_yahoo_macro(series_id, start, end)

    def fetch_fred_series(self, series_id: str, start: str, end: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch raw JSON observations from FRED API."""
        if not self.api_key:
            return None
            
        cache_key = f"fred_{series_id}_{start}_{end}"
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Retrieved FRED series '{series_id}' from cache")
            return cached

        self.logger.info(f"Requesting FRED series '{series_id}' from API ({start} to {end})")
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start,
            "observation_end": end
        }
        
        try:
            response = httpx.get(url, params=params, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                observations = data.get("observations", [])
                # Cache FRED series data for 1 day
                self.cache.set(cache_key, observations, expire_seconds=86400)
                return observations
            else:
                self.logger.error(f"FRED API error for '{series_id}': {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Exception querying FRED series '{series_id}': {e}")
            return None

    def fetch_yahoo_macro(self, ticker: str, start: str, end: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch macroeconomic indicators/yields from Yahoo Finance."""
        cache_key = f"yf_macro_{ticker}_{start}_{end}"
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Retrieved Yahoo macro ticker '{ticker}' from cache")
            return cached

        self.logger.info(f"Fetching Yahoo macro ticker '{ticker}' from yfinance ({start} to {end})")
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start, end=end, interval="1d")
            
            if df.empty:
                self.logger.warning(f"No macro data returned for ticker {ticker}")
                return None
                
            observations = []
            for timestamp, row in df.iterrows():
                val = row["Close"]
                if not pd.isna(val):
                    observations.append({
                        "date": timestamp.date().isoformat(),
                        "value": float(val)
                    })
            
            # Cache for 12 hours
            self.cache.set(cache_key, observations, expire_seconds=43200)
            return observations
        except Exception as e:
            self.logger.error(f"Exception querying Yahoo macro ticker '{ticker}': {e}")
            return None

    def update(self, db: Session, **kwargs) -> Dict[str, Any]:
        """
        Executes macroeconomic ingestion. Uses FRED if key is set, otherwise Yahoo Finance.
        """
        today_date = date.today()
        # Default start date is 2 years ago for seeding macro trends
        start_date_str = (today_date - timedelta(days=730)).strftime("%Y-%m-%d")
        end_date_str = today_date.strftime("%Y-%m-%d")
        
        events_saved = 0
        series_processed = []

        if self.api_key:
            self.logger.info("FRED API Key detected. Fetching official FRED series...")
            for series_id in self.fred_series.keys():
                # Get last date in DB for this series to minimize API pull range
                last_db_date = db.query(func.max(EconomicEvent.date)).filter(
                    EconomicEvent.series_id == series_id
                ).scalar()
                
                query_start = start_date_str
                if last_db_date:
                    # Next day
                    query_start = (last_db_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    
                if datetime.strptime(query_start, "%Y-%m-%d").date() >= today_date:
                    self.logger.info(f"FRED series '{series_id}' is already up to date.")
                    continue
                
                observations = self.fetch_fred_series(series_id, query_start, end_date_str)
                if observations:
                    series_processed.append(series_id)
                    to_insert = []
                    for obs in observations:
                        # Value can be '.' if missing or unreleased on that date
                        val_str = obs.get("value")
                        if val_str and val_str != ".":
                            obs_date = date.fromisoformat(obs["date"])
                            
                            # Deduplicate
                            existing = db.query(EconomicEvent).filter(
                                EconomicEvent.series_id == series_id,
                                EconomicEvent.date == obs_date
                            ).first()
                            
                            if not existing:
                                to_insert.append(
                                    EconomicEvent(
                                        series_id=series_id,
                                        date=obs_date,
                                        value=Decimal(val_str)
                                    )
                                )
                    if to_insert:
                        db.bulk_save_objects(to_insert)
                        db.commit()
                        events_saved += len(to_insert)
                        self.logger.info(f"Saved {len(to_insert)} data points for FRED series '{series_id}'")
        else:
            self.logger.info("No FRED API Key found. Using Yahoo Finance Treasury Yield Fallbacks...")
            for ticker in self.yahoo_yield_tickers.keys():
                last_db_date = db.query(func.max(EconomicEvent.date)).filter(
                    EconomicEvent.series_id == ticker
                ).scalar()
                
                query_start = start_date_str
                if last_db_date:
                    query_start = (last_db_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    
                if datetime.strptime(query_start, "%Y-%m-%d").date() >= today_date:
                    self.logger.info(f"Yahoo Yield series '{ticker}' is already up to date.")
                    continue

                observations = self.fetch_yahoo_macro(ticker, query_start, end_date_str)
                if observations:
                    series_processed.append(ticker)
                    to_insert = []
                    for obs in observations:
                        obs_date = date.fromisoformat(obs["date"])
                        
                        existing = db.query(EconomicEvent).filter(
                            EconomicEvent.series_id == ticker,
                            EconomicEvent.date == obs_date
                        ).first()
                        
                        if not existing:
                            to_insert.append(
                                EconomicEvent(
                                    series_id=ticker,
                                    date=obs_date,
                                    value=Decimal(str(obs["value"]))
                                )
                            )
                    if to_insert:
                        db.bulk_save_objects(to_insert)
                        db.commit()
                        events_saved += len(to_insert)
                        self.logger.info(f"Saved {len(to_insert)} data points for Yahoo Yield ticker '{ticker}'")

        if events_saved > 0:
            self.bus.publish("macro.updated", {
                "series_processed": series_processed,
                "records_count": events_saved,
                "timestamp": datetime.utcnow().isoformat()
            })

        return {
            "source": "FRED" if self.api_key else "Yahoo Finance",
            "series_processed": len(series_processed),
            "events_saved": events_saved
        }
