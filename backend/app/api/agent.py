from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agent import AgentRecommendationResponse
from app.services import agent_service

router = APIRouter(prefix="/api/v1/agent", tags=["AI Recovery Agent"])


@router.post("/analyze/{event_id}", response_model=AgentRecommendationResponse)
def analyze_event_by_agent(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Analyze revenue loss event and generate diagnosis + strategy recommendation."""
    rec = agent_service.analyze_and_recommend(db, event_id=event_id)
    return AgentRecommendationResponse(**rec)


@router.post("/recommend/{event_id}", response_model=AgentRecommendationResponse)
def recommend_strategy_by_agent(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Recommend recovery strategy for revenue event."""
    rec = agent_service.analyze_and_recommend(db, event_id=event_id)
    return AgentRecommendationResponse(**rec)


@router.get("/{event_id}", response_model=AgentRecommendationResponse)
def get_agent_recommendation_for_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get AI recommendation details for a revenue event."""
    rec = agent_service.get_agent_recommendation(db, event_id=event_id)
    return AgentRecommendationResponse(**rec)
