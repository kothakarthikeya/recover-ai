from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.policy import PolicyDecisionResponse
from app.services import policy_service

router = APIRouter(prefix="/api/v1/policy", tags=["Policy Guardrails"])


@router.post("/evaluate/{event_id}", response_model=PolicyDecisionResponse)
def evaluate_policy_endpoint(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Evaluate server-side policy rules for revenue event and return authoritative decision."""
    res = policy_service.evaluate_policy_for_event(db, event_id=event_id)
    return PolicyDecisionResponse(**res)


@router.get("/{event_id}", response_model=PolicyDecisionResponse)
def get_policy_decision_endpoint(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get calculated policy decision for a revenue event."""
    res = policy_service.get_policy_decision(db, event_id=event_id)
    return PolicyDecisionResponse(**res)
