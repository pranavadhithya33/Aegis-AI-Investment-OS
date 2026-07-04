import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with check_same_thread=False (safe for SQLite in multi-threaded FastAPI)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Configure SQLite pragmas for optimal local performance and constraints
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        # WAL mode permits concurrent reads while writes are active
        cursor.execute("PRAGMA journal_mode=WAL;")
        # Normal synchrony is faster and safe in WAL mode
        cursor.execute("PRAGMA synchronous=NORMAL;")
        # Enforce foreign key constraints (disabled by default in SQLite)
        cursor.execute("PRAGMA foreign_keys=ON;")
    except Exception as e:
        logger.error(f"Error setting SQLite pragmas: {e}")
    finally:
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy 2.0 models
class Base(DeclarativeBase):
    pass

# FastAPI Dependency for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
