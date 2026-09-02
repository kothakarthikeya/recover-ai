from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    revenue_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("revenue_events.id"), nullable=False, index=True)
    
    # Strategy: SMART_RETRY, PAYMENT_REMINDER, PAYMENT_LINK, SUBSCRIPTION_RETRY, ESCALATE, NO_ACTION
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    # Status: pending, in_progress, successful, failed, stopped, policy_denied
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    result_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    revenue_event: Mapped["RevenueEvent"] = relationship("RevenueEvent", back_populates="recovery_attempts")
    recovery_events: Mapped[List["RecoveryEvent"]] = relationship("RecoveryEvent", back_populates="recovery_attempt", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="recovery_attempt")
