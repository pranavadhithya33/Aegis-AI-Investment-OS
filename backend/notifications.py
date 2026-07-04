import logging
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.event_bus import event_bus
from backend.database.connection import SessionLocal
from backend.database.models import Signal, Asset, PriceHistory

logger = logging.getLogger("notifications")

class NotificationBroker:
    """
    Subscribes to EventBus topics and dispatches alerts (system logs, database Signals, 
    and extensible notification integrations like Slack or Webhooks).
    """

    def __init__(self):
        self.started = False

    def start(self):
        """Register listeners on the Event Bus."""
        if self.started:
            return
        event_bus.subscribe("price.updated", self.handle_price_update)
        event_bus.subscribe("macro.updated", self.handle_macro_update)
        event_bus.subscribe("signal.triggered", self.handle_signal_triggered)
        self.started = True
        logger.info("Notification Broker started and subscribed to event topics.")

    def handle_price_update(self, data: Dict[str, Any]):
        """
        Triggered when new price details are ingested.
        Checks if day-over-day price move exceeds 5%, triggering an alert signal.
        """
        asset_id = data.get("asset_id")
        ticker = data.get("ticker")
        close = data.get("close")
        
        if not asset_id or not close:
            return

        db = SessionLocal()
        try:
            # Check previous price to calculate percent change
            prev_price_rec = (
                db.query(PriceHistory)
                .filter(PriceHistory.asset_id == asset_id)
                .order_by(PriceHistory.date.desc())
                .offset(1)
                .first()
            )
            
            if prev_price_rec and prev_price_rec.close > 0:
                prev_close = float(prev_price_rec.close)
                current_close = float(close)
                pct_change = (current_close - prev_close) / prev_close
                
                # Check for > 5% movement
                if abs(pct_change) >= 0.05:
                    severity = "warning" if pct_change < 0 else "info"
                    action_word = "dropped" if pct_change < 0 else "surged"
                    
                    sig_details = {
                        "ticker": ticker,
                        "current_price": current_close,
                        "previous_price": prev_close,
                        "percent_change": float(pct_change)
                    }
                    
                    # Log alert as a Signal in SQLite
                    sig = Signal(
                        asset_id=asset_id,
                        signal_type="price_alert",
                        severity=severity,
                        details_json=json.dumps(sig_details)
                    )
                    db.add(sig)
                    db.commit()
                    
                    self.dispatch_external(
                        title=f"Price Alert: {ticker} {action_word} {pct_change:.2%}",
                        message=f"{ticker} is now trading at {current_close:.2f} (prev: {prev_close:.2f})."
                    )
        except Exception as e:
            logger.error(f"Error handling price update in broker: {e}")
        finally:
            db.close()

    def handle_macro_update(self, data: Dict[str, Any]):
        """
        Triggered when macroeconomic indicators update.
        """
        series_id = data.get("series_id")
        value = data.get("value")
        logger.info(f"NotificationBroker: Received macro update for {series_id} = {value}")

    def handle_signal_triggered(self, data: Dict[str, Any]):
        """
        Triggered when a signal is published on the event bus.
        Dispatches critical signals to external targets immediately.
        """
        sig_type = data.get("signal_type", "alert")
        severity = data.get("severity", "info")
        details = data.get("details", {})
        
        if severity == "critical":
            self.dispatch_external(
                title=f"CRITICAL SIGNAL: {sig_type}",
                message=json.dumps(details, indent=2)
            )

    def dispatch_external(self, title: str, message: str):
        """
        Simulates dispatching notifications to Slack, Email, Telegram, or SMS.
        Easily configurable to utilize webhook requests in production.
        """
        print(f"\n>>> AEGIS NOTIFICATION DISPATCHED <<<\nTitle: {title}\nMessage: {message}\n====================================\n")
        logger.info(f"External notification dispatched: {title} - {message}")

# Singleton broker instance
notification_broker = NotificationBroker()
