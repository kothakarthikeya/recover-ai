from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recovery_attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_attempts.id"), nullable=False, index=True)
    
    # Event types e.g.: strategy_selected, policy_check_passed, link_generated, reminder_sent, payment_received
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    recovery_attempt: Mapped["RecoveryAttempt"] = relationship("RecoveryAttempt", back_populates="recovery_events")
