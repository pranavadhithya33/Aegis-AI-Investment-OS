import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.ai.manager import AIManager
from backend.database.models import Portfolio, PortfolioPosition, Signal
from backend.portfolio.tracker import PortfolioTracker
from backend.portfolio.performance import PortfolioPerformance
from backend.portfolio.dividends import DividendTracker
from backend.portfolio.features import FeatureStore

class PortfolioAgent:
    """
    Agent 4: Portfolio Optimizer Agent.
    Evaluates current holdings, risk profiles, performance returns, and recommends actions.
    """

    @classmethod
    def optimize_portfolio(cls, db: Session, portfolio_id: int) -> Dict[str, Any]:
        """
        Gathers performance and risk features of a portfolio, and generates rebalancing suggestions.
        """
        # Fetch portfolio and run basic recalculation to get fresh values
        summary = PortfolioTracker.recalculate_portfolio(db, portfolio_id)
        
        # Get returns
        twrr = PortfolioPerformance.calculate_twrr(db, portfolio_id)
        mwrr = PortfolioPerformance.calculate_mwrr(db, portfolio_id)
        
        # Get dividends
        divs = DividendTracker.calculate_portfolio_dividends(db, portfolio_id)
        
        # Get quantitative features for each position
        positions = db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == portfolio_id).all()
        position_features = []
        for pos in positions:
            asset = pos.asset
            try:
                feat = FeatureStore.get_asset_features(db, asset.id)
            except Exception:
                feat = {}
            position_features.append({
                "ticker": asset.ticker,
                "shares": float(pos.shares),
                "avg_cost": float(pos.average_cost),
                "metrics": feat
            })

        # Formulate optimizer prompt
        portfolio_state = {
            "portfolio_id": portfolio_id,
            "cash_balance": summary["cash_balance"],
            "total_value": summary["total_value"],
            "twrr_annualized": twrr,
            "mwrr_annualized": mwrr,
            "projected_dividend_income": divs["projected_annual_income"],
            "portfolio_dividend_yield": divs["portfolio_dividend_yield"],
            "holdings": position_features
        }

        prompt = f"""
        Optimize the following investment portfolio state:
        Portfolio State: {json.dumps(portfolio_state, indent=2)}
        
        Respond ONLY with a valid JSON object matching this schema:
        {{
            "diversification_score": 0.75,
            "rebalancing_recommendation": "1-sentence rebalancing review.",
            "suggested_actions": ["Action 1", "Action 2"],
            "allocation_changes": {{
                "CASH": 0.10,
                "AAPL": 0.40,
                "MSFT": 0.50
            }}
        }}
        
        Note: diversification_score MUST be a float between 0.0 (highly concentrated/risky) and 1.0 (well diversified).
        """

        # System instructions
        system_instruction = "You are a professional wealth advisor. Maximize risk-adjusted returns and preserve capital. Output ONLY JSON."

        # Fetch AI response
        mock_output = json.dumps({
            "diversification_score": 0.80,
            "rebalancing_recommendation": "Rebalance slightly toward cash; holdings are highly concentrated in tech assets.",
            "suggested_actions": ["Increase cash buffer to 10%", "Hedge equity beta volatility"],
            "allocation_changes": {"CASH": 0.10, "AAPL": 0.45, "MSFT": 0.45}
        })

        ai_response = AIManager.generate(
            db=db,
            prompt=prompt,
            system_instruction=system_instruction,
            agent_name="PortfolioAgent",
            mock_response=mock_output
        )

        parsed = cls._parse_json_response(ai_response, mock_output)

        # Save to database Signal
        sig_details = {
            "diversification_score": parsed["diversification_score"],
            "rebalancing": parsed["rebalancing_recommendation"],
            "suggested_actions": parsed["suggested_actions"],
            "allocations": parsed["allocation_changes"]
        }
        sig = Signal(
            asset_id=None,
            signal_type="portfolio_rebalance_alert",
            severity="info" if parsed["diversification_score"] > 0.6 else "warning",
            details_json=json.dumps(sig_details)
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
