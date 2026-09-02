from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    revenue_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("revenue_events.id"), nullable=False, index=True)
    
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    recovery_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    revenue_at_risk_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Integer paise
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    revenue_event: Mapped["RevenueEvent"] = relationship("RevenueEvent", back_populates="risk_assessments")
