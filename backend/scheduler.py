import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.database.models import Portfolio, Asset, InvestmentThesis
from backend.plugins.yahoo import YahooFinancePlugin
from backend.plugins.fred import FredPlugin
from backend.portfolio.tracker import PortfolioTracker
from backend.portfolio.features import FeatureStore
from backend.ai.decision import DecisionAgent

logger = logging.getLogger("scheduler")

class SchedulerDaemon:
    """
    Manages daily and weekly automated updates (prices, macro indicators, portfolio states, 
    quantitative indicators, and thesis reviews).
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_daily_run: Optional[datetime] = None
        self.last_weekly_run: Optional[datetime] = None

    def start(self):
        """Starts the scheduler thread in the background."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="AegisScheduler")
        self._thread.start()
        logger.info("Scheduler Daemon thread started successfully.")

    def stop(self):
        """Stops the scheduler thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Scheduler Daemon thread stopped.")

    def trigger_jobs_now(self, db: Session) -> Dict[str, Any]:
        """
        Manually triggers all daily collection and audit jobs immediately.
        Useful for verification and manual sync requests.
        """
        logger.info("Manually triggering all Aegis AI background jobs.")
        results = {}

        # 1. Update Yahoo Finance Prices
        try:
            yahoo = YahooFinancePlugin()
            results["yahoo"] = yahoo.update(db)
        except Exception as e:
            logger.error(f"Yahoo update failed: {e}")
            results["yahoo"] = {"error": str(e)}

        # 2. Update Fred/Macro yields
        try:
            fred = FredPlugin()
            results["fred"] = fred.update(db)
        except Exception as e:
            logger.error(f"Fred update failed: {e}")
            results["fred"] = {"error": str(e)}

        # 3. Recalculate Portfolios
        try:
            portfolios = db.query(Portfolio).all()
            recalc_ports = []
            for p in portfolios:
                recalc_ports.append(PortfolioTracker.recalculate_portfolio(db, p.id))
            results["portfolios"] = recalc_ports
        except Exception as e:
            logger.error(f"Portfolio recalculation failed: {e}")
            results["portfolios"] = {"error": str(e)}

        # 4. Refresh Quant Features
        try:
            assets = db.query(Asset).filter(Asset.is_active == True).all()
            recalc_features = []
            for a in assets:
                recalc_features.append(FeatureStore.get_asset_features(db, a.id, use_cache=False))
            results["features"] = recalc_features
        except Exception as e:
            logger.error(f"Feature calculation failed: {e}")
            results["features"] = {"error": str(e)}

        # 5. Evaluate Active Thesis items
        try:
            theses = db.query(InvestmentThesis).filter(InvestmentThesis.status == "active").all()
            evaluated = []
            for t in theses:
                evaluated.append({
                    "thesis_id": t.id,
                    "ticker": t.asset.ticker,
                    "result": DecisionAgent.evaluate_thesis(db, t.id)
                })
            results["theses"] = evaluated
        except Exception as e:
            logger.error(f"Thesis evaluations failed: {e}")
            results["theses"] = {"error": str(e)}

        return results

    def _run_loop(self):
        """Main scheduler execution loop checking schedules every hour."""
        # Wait a short period on startup before running checks
        time.sleep(5)
        
        while not self._stop_event.is_set():
            now = datetime.utcnow()
            
            # Daily Tasks check (run if never run or > 24 hours since last run)
            if not self.last_daily_run or (now - self.last_daily_run) >= timedelta(days=1):
                db = SessionLocal()
                try:
                    self.trigger_jobs_now(db)
                    self.last_daily_run = now
                except Exception as e:
                    logger.error(f"Error in scheduler daily loop execution: {e}")
                finally:
                    db.close()

            # Weekly Tasks check (run if never run or > 7 days since last run)
            if not self.last_weekly_run or (now - self.last_weekly_run) >= timedelta(days=7):
                # Trigger weekly audits (e.g. news updates or full audits)
                self.last_weekly_run = now
                logger.info("Weekly scheduler tasks triggered.")

            # Sleep 1 hour, checking stop event periodically (every 5 seconds)
            for _ in range(720):
                if self._stop_event.is_set():
                    break
                time.sleep(5)

# Singleton scheduler instance
scheduler_daemon = SchedulerDaemon()
