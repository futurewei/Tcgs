"""API routes for AlgoDelivery management."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models.algo_delivery import AlgoDelivery
from ..models.audit import AuditAction
from ..models.user import User, UserRole
from ..schemas.algo_delivery import (
    AlgoDeliveryCreate,
    AlgoDeliveryResponse,
    AlgoDeliveryUpdate,
)
from ..services.audit import AuditService
from ..services.auth import get_current_user

router = APIRouter()


def _load_delivery(db: Session, delivery_id: int) -> AlgoDelivery:
    """Load a delivery with all relationships."""
    delivery = (
        db.query(AlgoDelivery)
        .options(
            joinedload(AlgoDelivery.owner),
            joinedload(AlgoDelivery.delivered_by),
            joinedload(AlgoDelivery.created_by),
        )
        .filter(AlgoDelivery.id == delivery_id)
        .first()
    )
    if not delivery:
        raise HTTPException(status_code=404, detail="AlgoDelivery not found")
    return delivery


def _can_edit(user: User, delivery: AlgoDelivery) -> bool:
    """Check if user can edit/delete a delivery."""
    return user.role == UserRole.ADMIN or user.id == delivery.created_by_id


@router.get("", response_model=List[AlgoDeliveryResponse])
def list_deliveries(
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all algo deliveries.
    Supports filtering by month (format: YYYY-MM).
    """
    query = db.query(AlgoDelivery).options(
        joinedload(AlgoDelivery.owner),
        joinedload(AlgoDelivery.delivered_by),
        joinedload(AlgoDelivery.created_by),
    )

    if month:
        query = query.filter(AlgoDelivery.month == month)

    deliveries = query.order_by(AlgoDelivery.month.desc(), AlgoDelivery.id.desc()).all()
    return deliveries


@router.get("/{delivery_id}", response_model=AlgoDeliveryResponse)
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single algo delivery by ID."""
    return _load_delivery(db, delivery_id)


@router.post("", response_model=AlgoDeliveryResponse)
def create_delivery(
    data: AlgoDeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new algo delivery.
    CUSTOMER users cannot create deliveries.
    """
    # Permission check: CUSTOMER users cannot create
    if current_user.role in [UserRole.CUSTOMER_INTERNAL, UserRole.CUSTOMER_EXTERNAL]:
        raise HTTPException(
            status_code=403, detail="CUSTOMER users cannot create deliveries"
        )

    # Validate owner exists
    owner = db.query(User).filter(User.id == data.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")

    delivery = AlgoDelivery(
        month=data.month,
        capability_name=data.capability_name,
        archive_url=data.archive_url,
        upgrade_description=data.upgrade_description,
        video_url=data.video_url,
        owner_id=data.owner_id,
        created_by_id=current_user.id,
        delivered=False,
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    AuditService.log(
        db,
        AuditAction.ALGO_DELIVERY_CREATE,
        "AlgoDelivery",
        delivery.id,
        current_user,
        new_value={
            "month": delivery.month,
            "capability_name": delivery.capability_name,
            "owner_id": delivery.owner_id,
        },
    )

    return _load_delivery(db, delivery.id)


@router.put("/{delivery_id}", response_model=AlgoDeliveryResponse)
def update_delivery(
    delivery_id: int,
    data: AlgoDeliveryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an algo delivery.
    Only the creator or admin can update.
    Setting delivered=True will auto-fill delivered_at and delivered_by_id.
    """
    delivery = _load_delivery(db, delivery_id)

    # Permission check
    if not _can_edit(current_user, delivery):
        raise HTTPException(
            status_code=403, detail="Only creator or admin can update this delivery"
        )

    old_values = {
        "capability_name": delivery.capability_name,
        "archive_url": delivery.archive_url,
        "upgrade_description": delivery.upgrade_description,
        "video_url": delivery.video_url,
        "owner_id": delivery.owner_id,
        "delivered": delivery.delivered,
    }

    # Update fields
    if data.capability_name is not None:
        delivery.capability_name = data.capability_name
    if data.archive_url is not None:
        delivery.archive_url = data.archive_url
    if data.upgrade_description is not None:
        delivery.upgrade_description = data.upgrade_description
    if data.video_url is not None:
        delivery.video_url = data.video_url
    if data.owner_id is not None:
        # Validate new owner exists
        owner = db.query(User).filter(User.id == data.owner_id).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Owner user not found")
        delivery.owner_id = data.owner_id

    # Handle delivery status change
    if data.delivered is not None and data.delivered != delivery.delivered:
        delivery.delivered = data.delivered
        if data.delivered:
            # Mark as delivered: set timestamp and who delivered
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.delivered_by_id = current_user.id
        else:
            # Unmark as delivered: clear the tracking fields
            delivery.delivered_at = None
            delivery.delivered_by_id = None

    db.commit()

    AuditService.log(
        db,
        AuditAction.ALGO_DELIVERY_UPDATE,
        "AlgoDelivery",
        delivery.id,
        current_user,
        old_value=old_values,
        new_value={
            "capability_name": delivery.capability_name,
            "archive_url": delivery.archive_url,
            "upgrade_description": delivery.upgrade_description,
            "video_url": delivery.video_url,
            "owner_id": delivery.owner_id,
            "delivered": delivery.delivered,
        },
    )

    return _load_delivery(db, delivery.id)


@router.delete("/{delivery_id}")
def delete_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an algo delivery.
    Only the creator or admin can delete.
    """
    delivery = _load_delivery(db, delivery_id)

    # Permission check
    if not _can_edit(current_user, delivery):
        raise HTTPException(
            status_code=403, detail="Only creator or admin can delete this delivery"
        )

    AuditService.log(
        db,
        AuditAction.ALGO_DELIVERY_DELETE,
        "AlgoDelivery",
        delivery.id,
        current_user,
        old_value={
            "month": delivery.month,
            "capability_name": delivery.capability_name,
            "owner_id": delivery.owner_id,
        },
    )

    db.delete(delivery)
    db.commit()

    return {"message": "AlgoDelivery deleted"}
