from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date

from backend.database.connection import SessionLocal
from backend.database.models import AgentLog, InvestmentThesis, Asset
from backend.ai.decision import DecisionAgent

router = APIRouter(prefix="/ai", tags=["ai"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class DecisionSessionRequest(BaseModel):
    portfolio_id: int
    question: str = Field(..., example="Should we buy AAPL today?")
    asset_ticker: Optional[str] = None

class ThesisEvaluationRequest(BaseModel):
    thesis_id: int

class ThesisCreate(BaseModel):
    asset_ticker: str
    thesis_text: str
    success_criteria_json: str
    review_date: str

class ThesisUpdate(BaseModel):
    thesis_text: Optional[str] = None
    success_criteria_json: Optional[str] = None
    review_date: Optional[str] = None
    status: Optional[str] = None

@router.post("/decision-session", response_model=Dict[str, Any])
def run_decision_session(payload: DecisionSessionRequest, db: Session = Depends(get_db)):
    """Runs a multi-agent consensus session and logs reasoning/outcome logs."""
    try:
        results = DecisionAgent.conduct_decision_session(
            db=db,
            portfolio_id=payload.portfolio_id,
            question=payload.question,
            asset_ticker=payload.asset_ticker
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision session failed: {str(e)}")

@router.post("/evaluate-thesis", response_model=Dict[str, Any])
def evaluate_thesis(payload: ThesisEvaluationRequest, db: Session = Depends(get_db)):
    """Checks success/failure boundaries for an active thesis."""
    try:
        results = DecisionAgent.evaluate_thesis(db=db, thesis_id=payload.thesis_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thesis evaluation failed: {str(e)}")

@router.get("/theses", response_model=List[Dict[str, Any]])
def list_theses(db: Session = Depends(get_db)):
    """Retrieve all logged investment theses."""
    theses = db.query(InvestmentThesis).order_by(InvestmentThesis.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "asset_ticker": t.asset.ticker,
            "thesis_text": t.thesis_text,
            "success_criteria_json": t.success_criteria_json,
            "review_date": t.review_date.isoformat(),
            "status": t.status,
            "outcome_text": t.outcome_text,
            "created_at": t.created_at.isoformat()
        } for t in theses
    ]

@router.post("/thesis", response_model=Dict[str, Any])
def create_thesis(payload: ThesisCreate, db: Session = Depends(get_db)):
    """Create a new investment thesis for tracking."""
    asset = db.query(Asset).filter(Asset.ticker == payload.asset_ticker.upper()).first()
    if not asset:
        raise HTTPException(status_code=400, detail=f"Asset {payload.asset_ticker} not found in database universe.")
    
    try:
        rev_date = date.fromisoformat(payload.review_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review_date format. Must be YYYY-MM-DD.")
    
    thesis = InvestmentThesis(
        asset_id=asset.id,
        thesis_text=payload.thesis_text,
        success_criteria_json=payload.success_criteria_json,
        review_date=rev_date,
        status="active"
    )
    db.add(thesis)
    db.commit()
    db.refresh(thesis)
    
    return {
        "status": "success",
        "thesis_id": thesis.id
    }

@router.put("/thesis/{thesis_id}", response_model=Dict[str, Any])
def update_thesis(thesis_id: int, payload: ThesisUpdate, db: Session = Depends(get_db)):
    """Update details or manual outcome status of an existing thesis."""
    thesis = db.query(InvestmentThesis).filter(InvestmentThesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
        
    if payload.thesis_text is not None:
        thesis.thesis_text = payload.thesis_text
    if payload.success_criteria_json is not None:
        thesis.success_criteria_json = payload.success_criteria_json
    if payload.review_date is not None:
        try:
            thesis.review_date = date.fromisoformat(payload.review_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid review_date format. Must be YYYY-MM-DD.")
    if payload.status is not None:
        thesis.status = payload.status
        
    thesis.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success"}

@router.delete("/thesis/{thesis_id}", response_model=Dict[str, Any])
def delete_thesis(thesis_id: int, db: Session = Depends(get_db)):
    """Delete an investment thesis."""
    thesis = db.query(InvestmentThesis).filter(InvestmentThesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    db.delete(thesis)
    db.commit()
    return {"status": "success"}

@router.get("/logs", response_model=List[Dict[str, Any]])
def list_agent_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve chronological audit trails of prompts, LLM responses, and tokens."""
    logs = (
        db.query(AgentLog)
        .order_by(AgentLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "agent_name": l.agent_name,
            "prompt_content": l.prompt_content,
            "completion_content": l.completion_content,
            "prompt_tokens": l.prompt_tokens,
            "completion_tokens": l.completion_tokens,
            "timestamp": l.timestamp.isoformat()
        } for l in logs
    ]
