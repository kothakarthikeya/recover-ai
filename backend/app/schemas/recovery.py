from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.ai.strategy import RecoveryStrategy
from app.schemas.policy import PolicyDecisionEnum


class RecoveryAttemptStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    STOPPED = "STOPPED"
    ESCALATED = "ESCALATED"


class RecoveryExecuteResponse(BaseModel):
    revenue_event_id: str
    attempt_id: str
    strategy: RecoveryStrategy
    policy_decision: PolicyDecisionEnum
    attempt_status: RecoveryAttemptStatusEnum
    event_status: str
    amount_attempted_paise: int
    amount_recovered_paise: int
    provider_reference: Optional[str] = None
    message: str
    requires_human_approval: bool = False
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchRecoveryRequest(BaseModel):
    merchant_id: Optional[str] = None
    limit: Optional[int] = 50


class BatchRecoveryResponse(BaseModel):
    total_opportunities: int
    eligible_count: int
    executed_count: int
    successful_count: int
    failed_count: int
    blocked_count: int
    escalated_count: int
    total_amount_attempted_paise: int
    total_amount_recovered_paise: int
    expected_recovery_amount_paise: int
    recovery_rate_percent: float
    results: List[RecoveryExecuteResponse]


class OpportunityResponse(BaseModel):
    revenue_event_id: str
    merchant_id: str
    customer_name: str
    event_type: str
    amount_paise: int
    recovery_probability: float
    expected_recovery_amount_paise: int
    risk_level: str
    recommended_strategy: RecoveryStrategy
    policy_decision: PolicyDecisionEnum
    event_time: datetime

    model_config = ConfigDict(from_attributes=True)
