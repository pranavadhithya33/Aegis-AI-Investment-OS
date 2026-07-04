from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, 
    BigInteger, Text, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.connection import Base

# --- UTILS ---
def utc_now():
    return datetime.utcnow()

# --- 1. ASSETS ---
class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # stock, etf, crypto, index
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    prices: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="asset", cascade="all, delete-orphan")
    financials: Mapped[List["FinancialStatement"]] = relationship("FinancialStatement", back_populates="asset", cascade="all, delete-orphan")
    news: Mapped[List["News"]] = relationship("News", back_populates="asset")
    sentiments: Mapped[List["Sentiment"]] = relationship("Sentiment", back_populates="asset", cascade="all, delete-orphan")
    signals: Mapped[List["Signal"]] = relationship("Signal", back_populates="asset", cascade="all, delete-orphan")
    theses: Mapped[List["InvestmentThesis"]] = relationship("InvestmentThesis", back_populates="asset", cascade="all, delete-orphan")
    positions: Mapped[List["PortfolioPosition"]] = relationship("PortfolioPosition", back_populates="asset")

# --- 2. PRICE HISTORY ---
class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    high: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    low: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("asset_id", "date", name="uq_asset_price_date"),
    )

# --- 3. FINANCIAL STATEMENTS ---
class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., '2025-Q1', '2024-FY'
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)  # quarterly, annual
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    cash_and_equiv: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    total_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Filing date

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="financials")

    __table_args__ = (
        UniqueConstraint("asset_id", "period", name="uq_asset_financial_period"),
    )

# --- 4. NEWS ---
class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="news")
    summary: Mapped[Optional["NewsSummary"]] = relationship("NewsSummary", back_populates="news", cascade="all, delete-orphan")

# --- 5. NEWS SUMMARIES ---
class NewsSummary(Base):
    __tablename__ = "news_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)  # -1.0000 to +1.0000
    entities_mentioned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    news: Mapped["News"] = relationship("News", back_populates="summary")

# --- 6. ECONOMIC EVENTS ---
class EconomicEvent(Base):
    __tablename__ = "economic_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., 'CPIAUCSL'
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    __table_args__ = (
        UniqueConstraint("series_id", "date", name="uq_economic_series_date"),
    )

# --- 7. AI REPORTS ---
class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly, quarterly, thesis
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown
    status: Mapped[str] = mapped_column(String(20), default="final", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

# --- 8. DECISION SESSIONS ---
class DecisionSession(Base):
    __tablename__ = "decision_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON representation of evidence
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    final_decision: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, validated, invalidated

# --- 9. PORTFOLIO ---
class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0.00, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    positions: Mapped[List["PortfolioPosition"]] = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    watchlists: Mapped[List["Watchlist"]] = relationship("Watchlist", back_populates="portfolio", cascade="all, delete-orphan")

# --- 10. PORTFOLIO POSITIONS ---
class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0.000000, nullable=False)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0000, nullable=False)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="positions")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="positions")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="uq_portfolio_asset"),
    )

# --- 11. TRANSACTIONS ---
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"), nullable=True)  # Null for cash transfers
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # BUY, SELL, DEPOSIT, WITHDRAW
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)  # Null for cash transfers
    size: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)  # Number of shares or cash amount
    commission: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0000, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")
    asset: Mapped[Optional["Asset"]] = relationship("Asset")

# --- 12. WATCHLIST ---
class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="watchlists")
    asset: Mapped["Asset"] = relationship("Asset")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="uq_watchlist_portfolio_asset"),
    )

# --- 13. SENTIMENT ---
class Sentiment(Base):
    __tablename__ = "sentiment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)  # -1.0000 to +1.0000
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # Reddit, News, Google Trends
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="sentiments")

    __table_args__ = (
        UniqueConstraint("asset_id", "source", "date", name="uq_asset_source_date"),
    )

# --- 14. HISTORICAL BACKTESTS ---
class HistoricalBacktest(Base):
    __tablename__ = "historical_backtests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of CAGR, Sharpe, Drawdown, etc.
    details_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of equity curve / trades
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

# --- 15. SIGNALS ---
class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # moving_average_cross, macro_alert, earnings_beat
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warning, critical
    details_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON metrics
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="signals")

# --- 16. AGENT LOGS ---
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_content: Mapped[str] = mapped_column(Text, nullable=False)
    completion_content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False, index=True)

# --- 17. SYSTEM LOGS ---
class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    log_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False, index=True)

# --- 18. INVESTMENT THESES ---
class InvestmentThesis(Base):
    __tablename__ = "investment_theses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    thesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of targets
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, fulfilled, failed, abandoned
    outcome_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="theses")
