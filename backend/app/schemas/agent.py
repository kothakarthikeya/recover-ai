from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.ai.strategy import RecoveryStrategy
from app.ai.diagnosis import DiagnosisCategory


class AgentRecommendationResponse(BaseModel):
    revenue_event_id: str
    diagnosis: str
    recommended_strategy: RecoveryStrategy
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    expected_recovery_amount_paise: int  # Integer paise
    recovery_probability: float
    risk_level: str
    next_step: str
    agent_version: str = "v1.0.0"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
