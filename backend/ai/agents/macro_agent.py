import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.ai.manager import AIManager
from backend.database.models import EconomicEvent, Signal

class MacroAgent:
    """
    Agent 3: Macroeconomic Outlook Agent.
    Evaluates macro indicators (interest rates, yields, inflation) to define risk regimes.
    """

    @classmethod
    def analyze_macro(cls, db: Session) -> Dict[str, Any]:
        """
        Gathers recent economic events, assesses risk, and returns macro parameters.
        """
        # Fetch 30 most recent macro data points
        events = (
            db.query(EconomicEvent)
            .order_by(EconomicEvent.date.desc())
            .limit(50)
            .all()
        )

        macro_data = []
        for e in events:
            macro_data.append({
                "series_id": e.series_id,
                "date": e.date.isoformat(),
                "value": float(e.value)
            })

        # Formulate prompt
        prompt = f"""
        Analyze the following macroeconomic data points (yield curve values, CPI, rates):
        Macro Indicators: {json.dumps(macro_data, indent=2)}
        
        Respond ONLY with a valid JSON object matching this schema:
        {{
            "macro_risk_score": 0.42,
            "regime_description": "1-sentence review of the economic environment.",
            "outlook": "Bullish / Neutral / Bearish",
            "signals": ["Macro signal 1", "Macro signal 2"]
        }}
        
        Note: macro_risk_score MUST be a float between 0.0 (very low risk) and 1.0 (very high risk).
        """

        # System instructions
        system_instruction = "You are a chief global macro strategist. Assess risk objectively. Output ONLY JSON."

        # Fetch AI response
        mock_output = json.dumps({
            "macro_risk_score": 0.35,
            "regime_description": "Yield curve remains normalized; inflation is moderating toward targets.",
            "outlook": "Neutral",
            "signals": []
        })

        ai_response = AIManager.generate(
            db=db,
            prompt=prompt,
            system_instruction=system_instruction,
            agent_name="MacroAgent",
            mock_response=mock_output
        )

        parsed = cls._parse_json_response(ai_response, mock_output)

        # Generate database Signal if risk score is high or outlook is bearish
        if parsed["macro_risk_score"] > 0.7 or parsed["outlook"] == "Bearish":
            sig_details = {
                "macro_risk_score": parsed["macro_risk_score"],
                "regime": parsed["regime_description"],
                "signals": parsed["signals"]
            }
            sig = Signal(
                signal_type="macro_outlook_alert",
                severity="critical" if parsed["macro_risk_score"] > 0.8 else "warning",
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
