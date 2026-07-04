import json
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.ai.manager import AIManager
from backend.database.models import News, NewsSummary, Sentiment

class SentimentAgent:
    """
    Agent 1: News Sentiment & Summarization Agent.
    Analyzes raw news articles, scores sentiment, and summarizes content.
    """

    @classmethod
    def analyze_news(cls, db: Session, news_item: News) -> Dict[str, Any]:
        """
        Runs sentiment analysis on a news item.
        Saves output to NewsSummary and updates Sentiment index.
        """
        # Formulate prompt
        prompt = f"""
        Analyze the financial sentiment and summarize the following news article.
        Title: {news_item.title}
        Source: {news_item.source}
        Content: {news_item.content or "No content available."}
        
        Respond ONLY with a valid JSON object matching this schema:
        {{
            "summary": "A 1-2 sentence concise summary.",
            "sentiment_score": 0.352,
            "entities_mentioned": ["AAPL", "Microsoft"]
        }}
        
        Note: The sentiment_score MUST be a float between -1.0 (very bearish/negative) and +1.0 (very bullish/positive).
        """

        # System instructions
        system_instruction = "You are a professional financial research analyst. Analyze sentiment objectively. Output ONLY JSON."

        # Fetch completion
        # Provide a standard mock response for tests or fallbacks
        mock_output = json.dumps({
            "summary": f"News report regarding {news_item.title[:30]}.",
            "sentiment_score": 0.4500,
            "entities_mentioned": [news_item.asset.ticker] if news_item.asset else []
        })

        ai_response = AIManager.generate(
            db=db,
            prompt=prompt,
            system_instruction=system_instruction,
            agent_name="SentimentAgent",
            mock_response=mock_output
        )

        # Parse JSON safely
        parsed = cls._parse_json_response(ai_response, mock_output)
        
        # Save to NewsSummary
        summary_rec = db.query(NewsSummary).filter(NewsSummary.news_id == news_item.id).first()
        if not summary_rec:
            summary_rec = NewsSummary(
                news_id=news_item.id,
                summary=parsed["summary"],
                sentiment_score=Decimal(str(parsed["sentiment_score"])),
                entities_mentioned=json.dumps(parsed["entities_mentioned"])
            )
            db.add(summary_rec)
        else:
            summary_rec.summary = parsed["summary"]
            summary_rec.sentiment_score = Decimal(str(parsed["sentiment_score"]))
            summary_rec.entities_mentioned = json.dumps(parsed["entities_mentioned"])

        # If news_item is linked to an asset, save to Sentiment table
        if news_item.asset_id:
            sentiment_rec = Sentiment(
                asset_id=news_item.asset_id,
                score=Decimal(str(parsed["sentiment_score"])),
                source=news_item.source,
                date=news_item.published_at.date()
            )
            db.add(sentiment_rec)

        db.commit()
        return parsed

    @staticmethod
    def _parse_json_response(text: str, fallback_json: str) -> Dict[str, Any]:
        """Utility to extract JSON blocks safely from LLM text responses."""
        try:
            # Clean enclosing markdown blocks if present
            cleaned = text.strip()
            if cleaned.startswith("```"):
                # strip code block tags
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
            return json.loads(cleaned)
        except Exception:
            return json.loads(fallback_json)
