from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

VALID_EVENT_TYPES = [
    "payment_failure",
    "checkout_abandonment",
    "subscription_failure",
    "overdue_invoice"
]

VALID_STATUSES = [
    "pending",
    "risk_assessed",
    "in_recovery",
    "recovered",
    "failed",
    "escalated",
    "stopped"
]


class CustomerSummarySchema(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    total_spent_paise: int
    successful_tx_count: int
    failed_tx_count: int
    opt_out: bool

    model_config = ConfigDict(from_attributes=True)


class RevenueEventResponse(BaseModel):
    id: str
    merchant_id: str
    customer_id: str
    event_type: str
    amount: int  # Integer paise
    currency: str
    status: str
    failure_reason: Optional[str] = None
    days_overdue: int
    transaction_count: int
    successful_transaction_count: int
    event_time: datetime
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerSummarySchema] = None

    model_config = ConfigDict(from_attributes=True)


class RevenueEventListResponse(BaseModel):
    items: List[RevenueEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RevenueOverviewResponse(BaseModel):
    total_revenue_paise: int
    revenue_at_risk_paise: int
    total_events_count: int
    total_customers_count: int
    by_event_type: Dict[str, int]
    by_status: Dict[str, int]


class SingleRevenueImportItem(BaseModel):
    customer_id: str
    event_type: str
    amount: int  # Integer paise > 0
    currency: str = "INR"
    failure_reason: Optional[str] = None
    days_overdue: int = 0
    event_time: Optional[datetime] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type '{v}'. Must be one of {VALID_EVENT_TYPES}")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Amount must be an integer (paise)")
        if v <= 0:
            raise ValueError("Amount must be a positive integer (greater than 0 paise)")
        return v


class RevenueImportRequest(BaseModel):
    merchant_id: str
    events: List[SingleRevenueImportItem]


class RevenueImportResponse(BaseModel):
    imported_count: int
    message: str
