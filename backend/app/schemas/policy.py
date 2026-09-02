from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.ai.strategy import RecoveryStrategy


class PolicyDecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"


class RuleIdEnum(str, Enum):
    ALREADY_RECOVERED = "ALREADY_RECOVERED"
    CUSTOMER_OPT_OUT = "CUSTOMER_OPT_OUT"
    RECOVERY_WINDOW_EXPIRED = "RECOVERY_WINDOW_EXPIRED"
    MAX_ATTEMPTS_EXCEEDED = "MAX_ATTEMPTS_EXCEEDED"
    LOW_RECOVERY_PROBABILITY = "LOW_RECOVERY_PROBABILITY"
    HIGH_VALUE_TRANSACTION = "HIGH_VALUE_TRANSACTION"
    STRATEGY_INCOMPATIBLE = "STRATEGY_INCOMPATIBLE"
    STANDARD_ELIGIBILITY = "STANDARD_ELIGIBILITY"


class PolicyDecisionResponse(BaseModel):
    revenue_event_id: str
    decision: PolicyDecisionEnum
    reason: str
    rule_id: RuleIdEnum
    recommended_strategy: Optional[RecoveryStrategy] = None
    requires_human_approval: bool = False
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)
