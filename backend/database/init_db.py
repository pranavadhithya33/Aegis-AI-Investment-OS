import logging
import sys
from pathlib import Path

# Add project root to path so we can import from backend
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import engine, Base, SessionLocal
from backend.database.models import Asset, Portfolio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("db_init")

# Default seeding data
DEFAULT_ASSETS = [
    # Stocks
    {"ticker": "MSFT", "name": "Microsoft Corporation", "asset_type": "stock", "sector": "Technology", "country": "USA", "currency": "USD"},
    {"ticker": "AAPL", "name": "Apple Inc.", "asset_type": "stock", "sector": "Technology", "country": "USA", "currency": "USD"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "asset_type": "stock", "sector": "Technology", "country": "USA", "currency": "USD"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "asset_type": "stock", "sector": "Communication Services", "country": "USA", "currency": "USD"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "asset_type": "stock", "sector": "Consumer Cyclical", "country": "USA", "currency": "USD"},
    # ETFs
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust", "asset_type": "etf", "sector": "Diversified", "country": "USA", "currency": "USD"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "asset_type": "etf", "sector": "Technology", "country": "USA", "currency": "USD"},
    # Crypto
    {"ticker": "BTC-USD", "name": "Bitcoin USD", "asset_type": "crypto", "sector": "Currency", "country": "Global", "currency": "USD"},
    {"ticker": "ETH-USD", "name": "Ethereum USD", "asset_type": "crypto", "sector": "Currency", "country": "Global", "currency": "USD"},
    # Indices
    {"ticker": "^GSPC", "name": "S&P 500 Index", "asset_type": "index", "sector": "Market", "country": "USA", "currency": "USD"},
    {"ticker": "^IXIC", "name": "NASDAQ Composite", "asset_type": "index", "sector": "Market", "country": "USA", "currency": "USD"}
]

def init_db():
    logger.info("Initializing database...")
    
    # Create the data folder if it does not exist
    db_file_dir = project_root / "data"
    db_file_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all tables defined in models.py
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")
    
    # Start a database session
    db = SessionLocal()
    try:
        # Seed Assets
        logger.info("Checking and seeding default asset universe...")
        seeded_assets_count = 0
        for asset_data in DEFAULT_ASSETS:
            # Check if asset already exists
            existing_asset = db.query(Asset).filter(Asset.ticker == asset_data["ticker"]).first()
            if not existing_asset:
                asset = Asset(**asset_data)
                db.add(asset)
                seeded_assets_count += 1
        
        # Seed Portfolio
        logger.info("Checking and seeding default portfolio...")
        existing_portfolio = db.query(Portfolio).first()
        seeded_portfolio = False
        if not existing_portfolio:
            portfolio = Portfolio(name="Aegis Master Portfolio", cash_balance=100000.00)
            db.add(portfolio)
            db.flush()
            
            # Seed starting cash transaction
            from backend.database.models import Transaction
            from datetime import datetime
            starting_tx = Transaction(
                portfolio_id=portfolio.id,
                transaction_type="DEPOSIT",
                size=100000.00,
                commission=0.00,
                date=datetime.utcnow()
            )
            db.add(starting_tx)
            seeded_portfolio = True
            
        db.commit()
        
        if seeded_assets_count > 0:
            logger.info(f"Seeded {seeded_assets_count} new assets into the universe.")
        else:
            logger.info("Asset universe is already seeded.")
            
        if seeded_portfolio:
            logger.info("Seeded default 'Aegis Master Portfolio' with $100,000 cash balance.")
        else:
            logger.info("Portfolio already exists.")
            
        logger.info("Database bootstrap completed successfully.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error occurred during database initialization: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
