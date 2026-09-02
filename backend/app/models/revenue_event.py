from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, BigInteger, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class RevenueEvent(Base):
    __tablename__ = "revenue_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    
    # Supported Event types: payment_failure, checkout_abandonment, subscription_failure, overdue_invoice
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Amount stored in integer paise (₹1,000 = 100000 paise)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    
    # Statuses: pending, risk_assessed, in_recovery, recovered, failed, escalated, stopped
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    days_overdue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transaction_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    successful_transaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="revenue_events")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="revenue_events")
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship("RiskAssessment", back_populates="revenue_event", cascade="all, delete-orphan")
    recovery_attempts: Mapped[List["RecoveryAttempt"]] = relationship("RecoveryAttempt", back_populates="revenue_event", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="revenue_event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_revenue_events_merchant_type", "merchant_id", "event_type"),
        Index("ix_revenue_events_merchant_status", "merchant_id", "status"),
    )
