import io
import pandas as pd
import yfinance as yf
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.plugins.base import BasePlugin
from backend.database.models import Asset, PriceHistory, FinancialStatement

class YahooFinancePlugin(BasePlugin):
    """
    Yahoo Finance Collector Plugin.
    Fetches daily price history, asset metadata, and financial statements.
    """
    def __init__(self, **kwargs):
        super().__init__(
            plugin_id="yahoo_finance",
            name="Yahoo Finance Collector",
            **kwargs
        )

    def fetch(self, ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data from Yahoo Finance.
        Uses cache to avoid repeating requests on the same calendar day.
        """
        cache_key = f"yf_prices_{ticker}_{start}_{end}"
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Retrieved prices from cache for {ticker} ({start} to {end})")
            # Convert JSON back to DataFrame using StringIO
            return pd.read_json(io.StringIO(cached))

        self.logger.info(f"Fetching fresh prices from Yahoo Finance for {ticker} ({start} to {end})")
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start, end=end, interval="1d")
            
            if df.empty:
                self.logger.warning(f"No pricing data found for ticker {ticker}")
                return None
                
            # Cache the raw JSON representation for 12 hours
            # To preserve pandas timestamp structures, we convert to JSON
            self.cache.set(cache_key, df.to_json(), expire_seconds=43200)
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch prices for {ticker} from Yahoo Finance: {e}")
            return None

    def fetch_fundamentals(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch financial statements and asset profile info from Yahoo Finance.
        Caches results for 7 days since fundamentals update slowly.
        """
        cache_key = f"yf_fundamentals_{ticker}"
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Retrieved fundamentals from cache for {ticker}")
            return cached

        self.logger.info(f"Fetching fresh fundamentals from Yahoo Finance for {ticker}")
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            fundamentals = {
                "sector": info.get("sector"),
                "country": info.get("country"),
                "name": info.get("longName") or info.get("shortName") or ticker,
                "currency": info.get("currency", "USD"),
                "financials": []
            }

            # Gather annual financial statements if it's a corporate stock
            # yfinance returns a pandas DataFrame where index is statement items and columns are dates
            try:
                # We fetch annual income statement, balance sheet, and cash flow
                income = ticker_obj.financials
                balance = ticker_obj.balance_sheet
                cashflow = ticker_obj.cashflow
                
                if income is not None and not income.empty:
                    # Get the columns (which are statement dates)
                    dates = income.columns
                    for col_date in dates:
                        # Extract key metrics
                        period_str = str(col_date.year) + "-FY"
                        date_val = col_date.date().isoformat()
                        
                        def get_val(df, keys: List[str]) -> Optional[float]:
                            if df is None or df.empty:
                                return None
                            # Search through alternative keys in yfinance representation
                            for key in keys:
                                if key in df.index:
                                    val = df.loc[key][col_date]
                                    # Handle series or single value
                                    if isinstance(val, pd.Series):
                                        val = val.iloc[0]
                                    if not pd.isna(val):
                                        return float(val)
                            return None

                        revenue = get_val(income, ["Total Revenue", "Revenue"])
                        net_income = get_val(income, ["Net Income"])
                        eps = get_val(income, ["Diluted EPS", "Basic EPS"])
                        
                        op_cash = get_val(cashflow, ["Operating Cash Flow", "Cash Flow From Operating Activities", "Total Cash From Operating Activities"])
                        fcf = get_val(cashflow, ["Free Cash Flow"])
                        
                        total_assets = get_val(balance, ["Total Assets"])
                        total_liab = get_val(balance, ["Total Liabilities Net Minority Interest", "Total Liabilities"])
                        cash = get_val(balance, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash"])
                        debt = get_val(balance, ["Total Debt"])

                        fundamentals["financials"].append({
                            "period": period_str,
                            "period_type": "annual",
                            "date": date_val,
                            "revenue": revenue,
                            "net_income": net_income,
                            "operating_cash_flow": op_cash,
                            "free_cash_flow": fcf,
                            "total_assets": total_assets,
                            "total_liabilities": total_liab,
                            "cash_and_equiv": cash,
                            "total_debt": debt,
                            "eps": eps
                        })
            except Exception as fe:
                self.logger.warning(f"Failed to fetch detailed financial statements for {ticker}: {fe}")

            # Cache the result for 7 days (604,800 seconds)
            self.cache.set(cache_key, fundamentals, expire_seconds=604800)
            return fundamentals
        except Exception as e:
            self.logger.error(f"Failed to fetch fundamentals for {ticker}: {e}")
            return None

    def update(self, db: Session, **kwargs) -> Dict[str, Any]:
        """
        Run the collection pipeline for active assets.
        """
        # 1. Fetch active assets from database
        active_assets = db.query(Asset).filter(Asset.is_active == True).all()
        self.logger.info(f"Running update for {len(active_assets)} active assets...")
        
        updated_prices_count = 0
        updated_fundamentals_count = 0
        updated_tickers = []
        
        today_date = date.today()
        # Fetch up to tomorrow to ensure we capture today's full data depending on timezone
        end_date_str = (today_date + timedelta(days=1)).strftime("%Y-%m-%d")

        for asset in active_assets:
            # A. Update Asset Profile & Fundamentals
            if asset.asset_type == "stock":
                fund_data = self.fetch_fundamentals(asset.ticker)
                if fund_data:
                    # Update metadata if missing
                    if not asset.sector and fund_data.get("sector"):
                        asset.sector = fund_data["sector"]
                    if not asset.country and fund_data.get("country"):
                        asset.country = fund_data["country"]
                    if fund_data.get("currency"):
                        asset.currency = fund_data["currency"]
                        
                    # Save financial statements
                    for fs_data in fund_data.get("financials", []):
                        # Check if statement already exists
                        existing_fs = db.query(FinancialStatement).filter(
                            FinancialStatement.asset_id == asset.id,
                            FinancialStatement.period == fs_data["period"]
                        ).first()
                        
                        if not existing_fs:
                            fs = FinancialStatement(
                                asset_id=asset.id,
                                period=fs_data["period"],
                                period_type=fs_data["period_type"],
                                date=date.fromisoformat(fs_data["date"]) if fs_data.get("date") else None,
                                revenue=Decimal(str(fs_data["revenue"])) if fs_data.get("revenue") is not None else None,
                                net_income=Decimal(str(fs_data["net_income"])) if fs_data.get("net_income") is not None else None,
                                operating_cash_flow=Decimal(str(fs_data["operating_cash_flow"])) if fs_data.get("operating_cash_flow") is not None else None,
                                free_cash_flow=Decimal(str(fs_data["free_cash_flow"])) if fs_data.get("free_cash_flow") is not None else None,
                                total_assets=Decimal(str(fs_data["total_assets"])) if fs_data.get("total_assets") is not None else None,
                                total_liabilities=Decimal(str(fs_data["total_liabilities"])) if fs_data.get("total_liabilities") is not None else None,
                                cash_and_equiv=Decimal(str(fs_data["cash_and_equiv"])) if fs_data.get("cash_and_equiv") is not None else None,
                                total_debt=Decimal(str(fs_data["total_debt"])) if fs_data.get("total_debt") is not None else None,
                                eps=Decimal(str(fs_data["eps"])) if fs_data.get("eps") is not None else None,
                            )
                            db.add(fs)
                            updated_fundamentals_count += 1
                            
                    db.commit()

            # B. Fetch historical price updates
            # Determine start date: last recorded date in db + 1 day, or default to 2 years ago
            last_price_date = db.query(func.max(PriceHistory.date)).filter(PriceHistory.asset_id == asset.id).scalar()
            
            if last_price_date:
                # Add 1 day
                start_date_str = (last_price_date + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                # 2 years historical default
                start_date_str = (today_date - timedelta(days=730)).strftime("%Y-%m-%d")
                
            # If start_date is today or later, we can skip (prices already up to date)
            start_date_val = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_val >= today_date:
                self.logger.info(f"Prices for {asset.ticker} are already up to date (last date: {last_price_date})")
                continue

            df = self.fetch(asset.ticker, start=start_date_str, end=end_date_str)
            if df is not None and not df.empty:
                prices_to_insert = []
                for timestamp, row in df.iterrows():
                    # Parse timestamp (can be timezone aware index)
                    row_date = timestamp.date()
                    
                    # Double check we don't insert duplicate dates
                    existing = db.query(PriceHistory).filter(
                        PriceHistory.asset_id == asset.id,
                        PriceHistory.date == row_date
                    ).first()
                    
                    if not existing:
                        prices_to_insert.append(
                            PriceHistory(
                                asset_id=asset.id,
                                date=row_date,
                                open=Decimal(str(row["Open"])) if not pd.isna(row["Open"]) else None,
                                high=Decimal(str(row["High"])) if not pd.isna(row["High"]) else None,
                                low=Decimal(str(row["Low"])) if not pd.isna(row["Low"]) else None,
                                close=Decimal(str(row["Close"])),
                                volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
                            )
                        )
                
                if prices_to_insert:
                    db.bulk_save_objects(prices_to_insert)
                    db.commit()
                    updated_prices_count += len(prices_to_insert)
                    updated_tickers.append(asset.ticker)
                    self.logger.info(f"Saved {len(prices_to_insert)} price points for {asset.ticker}")
                    
        # Publish event if prices were updated
        if updated_tickers:
            self.bus.publish("price.updated", {
                "tickers": updated_tickers,
                "timestamp": datetime.utcnow().isoformat(),
                "records_count": updated_prices_count
            })

        return {
            "assets_processed": len(active_assets),
            "prices_saved": updated_prices_count,
            "fundamentals_saved": updated_fundamentals_count,
            "updated_tickers": updated_tickers
        }
