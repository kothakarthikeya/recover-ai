from dataclasses import dataclass
from app.core.config import settings


@dataclass
class PolicyConfig:
    max_automatic_attempts: int = getattr(settings, "MAX_AUTOMATIC_RETRY_ATTEMPTS", 2)
    high_value_threshold_paise: int = getattr(settings, "HIGH_VALUE_ESCALATION_THRESHOLD_PAISE", 10000000)
    minimum_recovery_probability: float = getattr(settings, "MIN_RECOVERY_PROBABILITY_THRESHOLD", 0.25)
    recovery_window_hours: int = getattr(settings, "RECOVERY_WINDOW_HOURS", 72)
    require_human_approval_for_high_value: bool = True


default_policy_config = PolicyConfig()
