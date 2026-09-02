from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_spent_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # Integer paise
    successful_tx_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tx_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="customers")
    revenue_events: Mapped[List["RevenueEvent"]] = relationship("RevenueEvent", back_populates="customer", cascade="all, delete-orphan")
