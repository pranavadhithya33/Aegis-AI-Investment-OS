import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.ai.manager import AIManager
from backend.database.models import Asset, FinancialStatement, Signal

class FundamentalsAgent:
    """
    Agent 2: Corporate Fundamentals Analyser Agent.
    Evaluates income sheets, leverage ratios, cash flow generation, and flags warnings.
    """

    @classmethod
    def analyze_fundamentals(cls, db: Session, asset_id: int) -> Dict[str, Any]:
        """
        Retrieves financial statements for the asset, conducts ratio analysis,
        and generates warnings and health ratings.
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset ID {asset_id} not found")

        # Fetch financial statements
        statements = (
            db.query(FinancialStatement)
            .filter(FinancialStatement.asset_id == asset_id)
            .order_by(FinancialStatement.period.desc())
            .all()
        )

        # Prepare statement data for prompt
        fin_data = []
        for s in statements:
            fin_data.append({
                "period": s.period,
                "revenue": float(s.revenue) if s.revenue else None,
                "net_income": float(s.net_income) if s.net_income else None,
                "operating_cash_flow": float(s.operating_cash_flow) if s.operating_cash_flow else None,
                "free_cash_flow": float(s.free_cash_flow) if s.free_cash_flow else None,
                "total_assets": float(s.total_assets) if s.total_assets else None,
                "total_liabilities": float(s.total_liabilities) if s.total_liabilities else None,
                "cash_and_equiv": float(s.cash_and_equiv) if s.cash_and_equiv else None,
                "total_debt": float(s.total_debt) if s.total_debt else None,
                "eps": float(s.eps) if s.eps else None
            })

        # Formulate prompt
        prompt = f"""
        Analyze the following corporate financials for {asset.ticker} ({asset.name}):
        Financials: {json.dumps(fin_data, indent=2)}
        
        Respond ONLY with a valid JSON object matching this schema:
        {{
            "fcf_growth_assessment": "1-sentence review of free cash flows.",
            "debt_sustainability": "1-sentence review of liabilities and total debt.",
            "overall_rating": "Strong / Average / Risk",
            "warnings": ["Warning 1", "Warning 2"]
        }}
        """

        # System instruction
        system_instruction = "You are a senior quantitative risk analyst. Evaluate financials conservatively. Output ONLY JSON."

        # Fetch AI response
        mock_output = json.dumps({
            "fcf_growth_assessment": "Stable cash generation with positive free cash flow.",
            "debt_sustainability": "Conservative leverage profile; interest is well-covered.",
            "overall_rating": "Strong",
            "warnings": []
        })

        ai_response = AIManager.generate(
            db=db,
            prompt=prompt,
            system_instruction=system_instruction,
            agent_name="FundamentalsAgent",
            mock_response=mock_output
        )

        parsed = cls._parse_json_response(ai_response, mock_output)

        # If warnings exist or rating is Risk, trigger a database Signal alert
        if parsed["overall_rating"] == "Risk" or parsed["warnings"]:
            sig_details = {
                "fcf_growth": parsed["fcf_growth_assessment"],
                "debt_sustainability": parsed["debt_sustainability"],
                "warnings": parsed["warnings"]
            }
            sig = Signal(
                asset_id=asset_id,
                signal_type="fundamentals_alert",
                severity="warning" if parsed["overall_rating"] == "Risk" else "info",
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
