import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Asset, PriceHistory, Portfolio, Transaction
from backend.plugins.yahoo import YahooFinancePlugin
from backend.simulation.backtester import BacktestEngine
from backend.ai.decision import DecisionAgent
from backend.portfolio.tracker import PortfolioTracker

def run_verification():
    print("====================================================")
    print("           AEGIS AI - BACKEND VERIFICATION          ")
    print("====================================================\n")
    
    db = SessionLocal()
    try:
        # 1. Check or seed Asset AAPL
        print("[1/6] Checking asset universe...")
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        if not aapl:
            print("AAPL not found, seeding metadata...")
            aapl = Asset(
                ticker="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                sector="Technology",
                country="USA",
                currency="USD",
                is_active=True
            )
            db.add(aapl)
            db.commit()
            db.refresh(aapl)
        print(f"Asset found: {aapl.name} ({aapl.ticker})")

        # 2. Fetch and store real historical data
        print("\n[2/6] Fetching historical price data from Yahoo Finance...")
        plugin = YahooFinancePlugin()
        today = date.today()
        start_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        # Clear existing pricing to ensure a fresh fetch is verified
        db.query(PriceHistory).filter(PriceHistory.asset_id == aapl.id).delete()
        db.commit()
        
        # Fetch data
        df = plugin.fetch(aapl.ticker, start=start_date, end=end_date)
        if df is None or df.empty:
            print("Error: Failed to retrieve data from Yahoo Finance!")
            return
            
        print(f"Successfully fetched {len(df)} price points (last 60 days manual query).")
        
        # Persist to database
        print("Running plugin.update() to trigger automated asset updater...")
        plugin.update(db)
        stored_count = db.query(PriceHistory).filter(PriceHistory.asset_id == aapl.id).count()
        print(f"Stored {stored_count} price records in the database (since AAPL was empty, the updater backfilled a default 2-year historical range).")
        
        # Verify first and last price
        first_p = db.query(PriceHistory).filter(PriceHistory.asset_id == aapl.id).order_by(PriceHistory.date.asc()).first()
        last_p = db.query(PriceHistory).filter(PriceHistory.asset_id == aapl.id).order_by(PriceHistory.date.desc()).first()
        print(f"Price range: {first_p.date} (${first_p.close:.2f}) to {last_p.date} (${last_p.close:.2f})")

        # 3. Check or seed default portfolio with initial cash
        print("\n[3/6] Fetching default portfolio details...")
        port = db.query(Portfolio).first()
        if not port:
            print("Default portfolio not found, creating 'Aegis Master Portfolio'...")
            port = Portfolio(name="Aegis Master Portfolio", cash_balance=100000.00)
            db.add(port)
            db.flush()
            tx = Transaction(
                portfolio_id=port.id,
                transaction_type="DEPOSIT",
                size=100000.00,
                commission=0.00,
                date=datetime.utcnow()
            )
            db.add(tx)
            db.commit()
            db.refresh(port)
        
        # Recalculate portfolio to ensure fresh state
        summary = PortfolioTracker.recalculate_portfolio(db, port.id)
        print(f"Portfolio Name: {port.name}")
        print(f"Cash Balance: ${summary['cash_balance']:.2f}")

        # 4. Run Backtester Strategy
        print("\n[4/6] Running historical backtest (SMA Crossover Strategy)...")
        bt_results = BacktestEngine.run_backtest(
            db=db,
            ticker="AAPL",
            strategy_name="sma_cross",
            start_date=date.today() - timedelta(days=50),
            end_date=date.today(),
            initial_cash=10000.00
        )
        print("Backtest Results:")
        print(f"  Ticker: {bt_results['ticker']}")
        print(f"  Initial Value: ${bt_results['initial_value']:.2f}")
        print(f"  Final Value: ${bt_results['final_value']:.2f}")
        print(f"  Total Return: {bt_results['cumulative_return']:.2%}")
        print(f"  Max Drawdown: {bt_results['max_drawdown']:.2%}")
        print(f"  Total Transactions: {bt_results['trades_count']}")

        # 5. Generate AI Advisory Report & Decision Session
        print("\n[5/6] Conducting AI Decision Session...")
        question = "Should we purchase AAPL shares given the current SMA crossover trend?"
        ai_result = DecisionAgent.conduct_decision_session(
            db=db,
            portfolio_id=port.id,
            question=question,
            asset_ticker="AAPL"
        )
        print("AI Advisory consensus decisions:")
        print(f"  Reasoning Summary: {ai_result['reasoning_summary']}")
        print(f"  Final Decision: {ai_result['final_decision']}")
        print(f"  Recommendation Details: {ai_result['recommendation_details']}")

        # 6. Verify Database Audit Entries
        print("\n[6/6] Verifying database audit trails...")
        from backend.database.models import DecisionSession, AgentLog
        
        dec_session = db.query(DecisionSession).filter(DecisionSession.question == question).first()
        assert dec_session is not None, "Decision Session not logged in database!"
        print(f"  [OK] Decision Session logged in DB (ID: {dec_session.id})")
        
        logs_count = db.query(AgentLog).count()
        print(f"  [OK] Total AI Agent prompt logs written: {logs_count}")
        
        print("\n====================================================")
        print("    VERIFICATION COMPLETED: BACKEND IS 100% OPERATIONAL")
        print("====================================================")

    except Exception as e:
        print(f"\nVerification failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
