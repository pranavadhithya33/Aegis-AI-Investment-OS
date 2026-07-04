import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date

from backend.ai.manager import AIManager
from backend.database.models import (
    InvestmentThesis, DecisionSession, Asset, PriceHistory, 
    FinancialStatement, Signal, Portfolio
)
from backend.ai.agents.sentiment_agent import SentimentAgent
from backend.ai.agents.fundamentals_agent import FundamentalsAgent
from backend.ai.agents.macro_agent import MacroAgent
from backend.ai.agents.portfolio_agent import PortfolioAgent

class DecisionAgent:
    """
    Agent 5: Investment Thesis & Decision Session Agent.
    Aggregates analytical agent results, validates investment theses, 
    and handles decision audits.
    """

    @classmethod
    def evaluate_thesis(cls, db: Session, thesis_id: int) -> Dict[str, Any]:
        """
        Gathers current metrics for a thesis asset and calls LLM to evaluate
        whether success criteria are met, failed, or remain active.
        """
        thesis = db.query(InvestmentThesis).filter(InvestmentThesis.id == thesis_id).first()
        if not thesis:
            raise ValueError(f"Thesis ID {thesis_id} not found")

        asset = thesis.asset
        
        # Gather current metrics for the asset
        latest_price_rec = (
            db.query(PriceHistory)
            .filter(PriceHistory.asset_id == asset.id)
            .order_by(PriceHistory.date.desc())
            .first()
        )
        current_price = float(latest_price_rec.close) if latest_price_rec else 0.0

        # Fetch recent financials
        statements = (
            db.query(FinancialStatement)
            .filter(FinancialStatement.asset_id == asset.id)
            .order_by(FinancialStatement.period.desc())
            .limit(2)
            .all()
        )
        fin_summary = [
            {"period": s.period, "eps": float(s.eps) if s.eps else None, "revenue": float(s.revenue) if s.revenue else None}
            for s in statements
        ]

        # Formulate prompt
        prompt = f"""
        Evaluate this investment thesis for {asset.ticker}:
        Thesis Text: {thesis.thesis_text}
        Success Criteria: {thesis.success_criteria_json}
        Current Asset Price: {current_price}
        Recent Financials: {json.dumps(fin_summary)}
        
        Determine if the success criteria are fulfilled, failed, or if the thesis is still active.
        Respond ONLY with a valid JSON object matching this schema:
        {{
            "status": "fulfilled / failed / active",
            "reasoning": "A concise explanation of the decision based on criteria.",
            "outcome_summary": "1-sentence outcome summary."
        }}
        """

        # System instruction
        system_instruction = "You are a senior investment committee chairman. Evaluate thesis criteria strictly. Output ONLY JSON."

        # Fetch AI response
        mock_output = json.dumps({
            "status": "active",
            "reasoning": "Asset price is below target price but revenue metrics are showing positive progression.",
            "outcome_summary": "Thesis remains active pending further price target validations."
        })

        ai_response = AIManager.generate(
            db=db,
            prompt=prompt,
            system_instruction=system_instruction,
            agent_name="DecisionAgent_Thesis",
            mock_response=mock_output
        )

        parsed = cls._parse_json_response(ai_response, mock_output)

        # Update thesis status in DB
        thesis.status = parsed["status"]
        thesis.outcome_text = parsed["outcome_summary"]
        thesis.updated_at = datetime.utcnow()
        db.commit()

        return parsed

    @classmethod
    def conduct_decision_session(
        cls,
        db: Session,
        portfolio_id: int,
        question: str,
        asset_ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs an aggregated decision session.
        Gathers evidence from Macro, Portfolio, Fundamentals, and Sentiment,
        compiles reasoning, makes a final recommendation, and logs details.
        """
        evidence: Dict[str, Any] = {}

        # 1. Macro Outlook Evidence
        try:
            evidence["macro"] = MacroAgent.analyze_macro(db)
        except Exception as e:
            evidence["macro"] = {"error": str(e)}

        # 2. Portfolio Optimization Evidence
        try:
            evidence["portfolio"] = PortfolioAgent.optimize_portfolio(db, portfolio_id)
        except Exception as e:
            evidence["portfolio"] = {"error": str(e)}

        # 3. Asset-specific Fundamentals & Sentiment Evidence
        asset_id = None
        if asset_ticker:
            asset = db.query(Asset).filter(Asset.ticker == asset_ticker).first()
            if asset:
                asset_id = asset.id
                try:
                    evidence["fundamentals"] = FundamentalsAgent.analyze_fundamentals(db, asset.id)
                except Exception as e:
                    evidence["fundamentals"] = {"error": str(e)}
                
                # Fetch recent news for sentiment
                news_item = (
                    pos for pos in asset.news if pos.asset_id == asset.id
                ) if hasattr(asset, "news") else None
                
                if news_item:
                    try:
                        # Grab the first news item
                        evidence["sentiment"] = SentimentAgent.analyze_news(db, list(news_item)[0])
                    except Exception as e:
                        evidence["sentiment"] = {"error": str(e)}

        # Formulate consolidated prompt
        prompt = f"""
        Conduct a decision session for Portfolio ID {portfolio_id}.
        Question: {question}
        Target Asset Ticker: {asset_ticker or "N/A"}
        
        Collected Evidence:
        {json.dumps(evidence, indent=2)}
        
        Synthesize the collective signals. Respond ONLY with a valid JSON object matching this schema:
        {{
            "reasoning_summary": "Aggregated analytical reasoning showing key drivers.",
            "final_decision": "BUY / SELL / HOLD / NO_ACTION",
            "recommendation_details": "1-sentence target action instructions.",
            "evidence_breakdown": {{
                "sentiment": "Key takeaways from news sentiment analysis.",
                "fundamentals": "Key metrics from corporate financials ratio analysis.",
                "macro": "Key macroeconomic indicators and risks analyzed.",
                "portfolio": "Key allocation or portfolio weight recommendations."
            }}
        }}
        """

        system_instruction = "You are a professional quantitative investment committee advisor. Provide objective, logical recommendations. Output ONLY JSON."

        mock_output = json.dumps({
            "reasoning_summary": f"Macro conditions are stable and fundamentals support {asset_ticker or 'portfolio adjustments'}.",
            "final_decision": "BUY" if asset_ticker else "NO_ACTION",
            "recommendation_details": f"Initiate standard size allocation for {asset_ticker or 'cash'}",
            "evidence_breakdown": {
                "sentiment": "Neutral-to-positive news sentiment with stable indicators.",
                "fundamentals": f"Healthy balance sheet ratios and solid cash conversion patterns for {asset_ticker or 'active assets'}.",
                "macro": "Yield curves normalized with low risk scores on short-term rates.",
                "portfolio": "Cash buffer is sufficient; rebalancing targets have been satisfied."
            }
        })

        ai_response = AIManager.generate(
            db=db,
            prompt=prompt,
            system_instruction=system_instruction,
            agent_name="DecisionAgent_Session",
            mock_response=mock_output
        )

        parsed = cls._parse_json_response(ai_response, mock_output)

        # Log decision session to DB
        session_log = DecisionSession(
            timestamp=datetime.utcnow(),
            question=question,
            evidence_used=json.dumps(evidence),
            reasoning_summary=parsed["reasoning_summary"],
            final_decision=parsed["final_decision"],
            outcome=parsed["recommendation_details"],
            outcome_status="pending"
        )
        db.add(session_log)
        
        # If there is a buy/sell decision, log a Signal
        if parsed["final_decision"] in ["BUY", "SELL"]:
            sig = Signal(
                asset_id=asset_id,
                signal_type="trade_decision_signal",
                severity="critical",
                details_json=json.dumps({
                    "decision": parsed["final_decision"],
                    "recommendation": parsed["recommendation_details"]
                })
            )
            db.add(sig)

        db.commit()
        return parsed

    @staticmethod
    def _parse_json_response(text: str, fallback_json: str) -> Dict[str, Any]:
        """Utility to extract JSON blocks safely from LLM text responses."""
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
            return json.loads(cleaned)
        except Exception:
            return json.loads(fallback_json)
