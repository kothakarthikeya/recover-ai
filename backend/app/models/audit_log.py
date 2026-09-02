from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    revenue_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("revenue_events.id"), nullable=False, index=True)
    recovery_attempt_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("recovery_attempts.id"), nullable=True)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="SYSTEM_AGENT", nullable=False)
    policy_result: Mapped[str] = mapped_column(String(50), nullable=False)  # ALLOWED, DENIED, ESCALATED, STOPPED
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Amount recovered in integer paise (if applicable)
    amount_recovered_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    revenue_event: Mapped["RevenueEvent"] = relationship("RevenueEvent", back_populates="audit_logs")
    recovery_attempt: Mapped[Optional["RecoveryAttempt"]] = relationship("RecoveryAttempt", back_populates="audit_logs")
