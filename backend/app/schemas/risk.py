from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class RiskAssessmentResponse(BaseModel):
    id: str
    revenue_event_id: str
    risk_score: float
    recovery_probability: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    revenue_at_risk_paise: int
    expected_recovery_amount_paise: int
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchRiskAnalysisRequest(BaseModel):
    event_ids: List[str]


class BatchRiskAnalysisResponse(BaseModel):
    events_analyzed: int
    total_revenue_at_risk_paise: int
    estimated_recoverable_revenue_paise: int
    risk_level_counts: Dict[str, int]
    assessments: List[RiskAssessmentResponse]
