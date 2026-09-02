from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.schemas.revenue import SingleRevenueImportItem


def get_revenue_overview(db: Session, merchant_id: Optional[str] = None) -> Dict[str, Any]:
    query = db.query(RevenueEvent)
    customer_query = db.query(Customer)
    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)
        customer_query = customer_query.filter(Customer.merchant_id == merchant_id)

    total_events_count = query.count()
    total_customers_count = customer_query.count()

    # Total Revenue (sum of all events amount)
    total_revenue_res = query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar()
    total_revenue_paise = int(total_revenue_res or 0)

    # Revenue At Risk (sum of pending, in_recovery, or risk_assessed status amounts)
    risk_statuses = ["pending", "risk_assessed", "in_recovery"]
    risk_query = query.filter(RevenueEvent.status.in_(risk_statuses))
    revenue_at_risk_res = risk_query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar()
    revenue_at_risk_paise = int(revenue_at_risk_res or 0)

    # Breakdown by event_type
    type_counts = (
        query.with_entities(RevenueEvent.event_type, func.count(RevenueEvent.id))
        .group_by(RevenueEvent.event_type)
        .all()
    )
    by_event_type = {t: count for t, count in type_counts}

    # Breakdown by status
    status_counts = (
        query.with_entities(RevenueEvent.status, func.count(RevenueEvent.id))
        .group_by(RevenueEvent.status)
        .all()
    )
    by_status = {s: count for s, count in status_counts}

    return {
        "total_revenue_paise": total_revenue_paise,
        "revenue_at_risk_paise": revenue_at_risk_paise,
        "total_events_count": total_events_count,
        "total_customers_count": total_customers_count,
        "by_event_type": by_event_type,
        "by_status": by_status
    }


def get_revenue_events(
    db: Session,
    merchant_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    event_type: Optional[str] = None,
    status_val: Optional[str] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    query = db.query(RevenueEvent)

    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)
    if event_type:
        query = query.filter(RevenueEvent.event_type == event_type)
    if status_val:
        query = query.filter(RevenueEvent.status == status_val)
    if min_amount is not None:
        query = query.filter(RevenueEvent.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(RevenueEvent.amount <= max_amount)
    if start_date:
        query = query.filter(RevenueEvent.event_time >= start_date)
    if end_date:
        query = query.filter(RevenueEvent.event_time <= end_date)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    items = (
        query.order_by(RevenueEvent.event_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_revenue_event_by_id(db: Session, event_id: str) -> RevenueEvent:
    event = db.query(RevenueEvent).filter(RevenueEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue event with ID '{event_id}' not found"
        )
    return event


def import_revenue_events(
    db: Session,
    merchant_id: str,
    events: List[SingleRevenueImportItem]
) -> int:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Merchant with ID '{merchant_id}' does not exist"
        )

    import uuid
    created_objects = []
    for item in events:
        customer = db.query(Customer).filter(Customer.id == item.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with ID '{item.customer_id}' does not exist"
            )

        event = RevenueEvent(
            id=f"rev_{uuid.uuid4().hex[:12]}",
            merchant_id=merchant_id,
            customer_id=item.customer_id,
            event_type=item.event_type,
            amount=item.amount,
            currency=item.currency,
            status="pending",
            failure_reason=item.failure_reason,
            days_overdue=item.days_overdue,
            event_time=item.event_time or datetime.utcnow()
        )
        created_objects.append(event)

    try:
        db.bulk_save_objects(created_objects)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import revenue events due to database error"
        )

    return len(created_objects)
