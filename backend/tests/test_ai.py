import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import (
    Asset, News, Portfolio, PortfolioPosition, InvestmentThesis, 
    DecisionSession, AgentLog, NewsSummary, Sentiment, Signal,
    FinancialStatement, PriceHistory
)
from backend.ai.manager import AIManager
from backend.ai.agents.sentiment_agent import SentimentAgent
from backend.ai.agents.fundamentals_agent import FundamentalsAgent
from backend.ai.agents.macro_agent import MacroAgent
from backend.ai.agents.portfolio_agent import PortfolioAgent
from backend.ai.decision import DecisionAgent

def test_ai_manager_mock_logging():
    db = SessionLocal()
    try:
        # Run AI manager in mock mode
        prompt = "Hello Aegis AI"
        res = AIManager.generate(
            db=db,
            prompt=prompt,
            agent_name="TestLoggerAgent",
            mock_response="Hello Human"
        )
        
        assert res == "Hello Human"
        
        # Verify log entry in DB
        log = (
            db.query(AgentLog)
            .filter(AgentLog.agent_name == "TestLoggerAgent")
            .order_by(AgentLog.timestamp.desc())
            .first()
        )
        assert log is not None
        assert log.prompt_content == prompt
        assert log.completion_content == "Hello Human"
        
        # Clean up
        db.delete(log)
        db.commit()
    finally:
        db.close()

def test_sentiment_agent():
    db = SessionLocal()
    try:
        # Fetch AAPL asset
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        # Create un-analyzed news
        news_item = News(
            asset_id=aapl.id,
            title="Apple reports record service revenues",
            url="http://example.com/aapl-records",
            content="Apple Inc. announced record-breaking quarterly service revenues.",
            source="Test News Feed",
            published_at=datetime.utcnow()
        )
        db.add(news_item)
        db.commit()
        db.refresh(news_item)
        
        # Run agent
        analysis = SentimentAgent.analyze_news(db, news_item)
        
        assert "summary" in analysis
        assert "sentiment_score" in analysis
        assert isinstance(analysis["sentiment_score"], float)
        
        # Verify NewsSummary was saved
        summary_rec = db.query(NewsSummary).filter(NewsSummary.news_id == news_item.id).first()
        assert summary_rec is not None
        assert summary_rec.summary == analysis["summary"]
        
        # Verify Sentiment was logged
        sent = (
            db.query(Sentiment)
            .filter(Sentiment.asset_id == aapl.id)
            .order_by(Sentiment.id.desc())
            .first()
        )
        assert sent is not None
        assert float(sent.score) == pytest.approx(analysis["sentiment_score"])
        
        # Clean up
        db.delete(summary_rec)
        db.delete(sent)
        db.delete(news_item)
        db.commit()
    finally:
        db.close()

def test_fundamentals_agent():
    db = SessionLocal()
    try:
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        # Seed a test statement if none exists
        stmt = db.query(FinancialStatement).filter(
            FinancialStatement.asset_id == aapl.id,
            FinancialStatement.period == "2025-Q1"
        ).first()
        if not stmt:
            stmt = FinancialStatement(
                asset_id=aapl.id,
                period="2025-Q1",
                period_type="quarterly",
                revenue=Decimal("90000.00"),
                net_income=Decimal("20000.00"),
                free_cash_flow=Decimal("15000.00"),
                total_assets=Decimal("350000.00"),
                total_liabilities=Decimal("200000.00"),
                total_debt=Decimal("100000.00")
            )
            db.add(stmt)
            db.commit()
            
        analysis = FundamentalsAgent.analyze_fundamentals(db, aapl.id)
        
        assert "overall_rating" in analysis
        assert "fcf_growth_assessment" in analysis
        assert "warnings" in analysis
        
    finally:
        db.close()

def test_macro_agent():
    db = SessionLocal()
    try:
        analysis = MacroAgent.analyze_macro(db)
        
        assert "macro_risk_score" in analysis
        assert "regime_description" in analysis
        assert "outlook" in analysis
    finally:
        db.close()

def test_portfolio_agent():
    db = SessionLocal()
    try:
        # Create temporary portfolio
        port = Portfolio(name="Optimizer Test Portfolio", cash_balance=Decimal("100000.00"))
        db.add(port)
        db.commit()
        db.refresh(port)
        
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        pos = PortfolioPosition(
            portfolio_id=port.id,
            asset_id=aapl.id,
            shares=Decimal("100.00"),
            average_cost=Decimal("150.00")
        )
        db.add(pos)
        db.commit()
        
        # Run agent
        opt = PortfolioAgent.optimize_portfolio(db, port.id)
        
        assert "diversification_score" in opt
        assert "rebalancing_recommendation" in opt
        assert "suggested_actions" in opt
        
        # Verify Signal was saved
        sig = (
            db.query(Signal)
            .filter(Signal.signal_type == "portfolio_rebalance_alert")
            .order_by(Signal.created_at.desc())
            .first()
        )
        assert sig is not None
        
        # Clean up
        db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == port.id).delete()
        db.delete(port)
        db.delete(sig)
        db.commit()
    finally:
        db.close()

def test_decision_agent_evaluation():
    db = SessionLocal()
    try:
        aapl = db.query(Asset).filter(Asset.ticker == "AAPL").first()
        assert aapl is not None
        
        # Create a test thesis
        thesis = InvestmentThesis(
            asset_id=aapl.id,
            thesis_text="Buy AAPL because services segments are expanding and P/E ratio is sound.",
            success_criteria_json=json.dumps(["Price above 160", "Services revenue growth > 10%"]),
            review_date=date.today() + timedelta(days=30),
            status="active"
        )
        db.add(thesis)
        db.commit()
        db.refresh(thesis)
        
        # Run agent to evaluate thesis
        eval_res = DecisionAgent.evaluate_thesis(db, thesis.id)
        
        assert "status" in eval_res
        assert "reasoning" in eval_res
        
        # Verify updated DB state
        db.refresh(thesis)
        assert thesis.status == eval_res["status"]
        assert thesis.outcome_text is not None
        
        # Clean up
        db.delete(thesis)
        db.commit()
    finally:
        db.close()

def test_decision_agent_session():
    db = SessionLocal()
    try:
        # Create port
        port = Portfolio(name="Session Test Portfolio", cash_balance=Decimal("200000.00"))
        db.add(port)
        db.commit()
        db.refresh(port)
        
        question = "Should we purchase MSFT shares today given standard macro alerts?"
        
        res = DecisionAgent.conduct_decision_session(
            db=db,
            portfolio_id=port.id,
            question=question,
            asset_ticker="AAPL"
        )
        
        assert "final_decision" in res
        assert "reasoning_summary" in res
        
        # Verify DecisionSession entry is logged
        sess = (
            db.query(DecisionSession)
            .filter(DecisionSession.question == question)
            .first()
        )
        assert sess is not None
        assert sess.final_decision == res["final_decision"]
        assert sess.outcome_status == "pending"
        
        # Clean up
        db.delete(sess)
        db.delete(port)
        db.commit()
    finally:
        db.close()
