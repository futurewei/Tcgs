from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from ..database import get_db
from ..models.user import User, UserRole
from ..models.capacity import CapacitySlot, Binding
from ..models.audit import AuditAction
from ..schemas.capacity import (
    SlotCreate, SlotUpdate, SlotResponse,
    BindingCreate, BindingUpdate, BindingWithSlotResponse
)
from ..services.auth import get_current_user, get_current_admin
from ..services.audit import AuditService

router = APIRouter()


@router.get("/slots", response_model=List[SlotResponse])
def list_slots(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CapacitySlot).options(
        joinedload(CapacitySlot.user),
        joinedload(CapacitySlot.bindings)
    )

    if type:
        query = query.filter(CapacitySlot.type == type)

    return query.order_by(CapacitySlot.name).all()


@router.get("/slots/{slot_id}", response_model=SlotResponse)
def get_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slot = db.query(CapacitySlot).options(
        joinedload(CapacitySlot.user),
        joinedload(CapacitySlot.bindings)
    ).filter(CapacitySlot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot


@router.post("/slots", response_model=SlotResponse)
def create_slot(
    slot_data: SlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    slot = CapacitySlot(
        name=slot_data.name,
        type=slot_data.type,
        user_id=slot_data.user_id,
        total_capacity=slot_data.total_capacity
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    AuditService.log(db, AuditAction.SLOT_CREATE, "CapacitySlot", slot.id, current_user,
                     new_value={"name": slot.name, "type": slot.type.value})

    return get_slot(slot.id, db, current_user)


@router.put("/slots/{slot_id}", response_model=SlotResponse)
def update_slot(
    slot_id: int,
    slot_data: SlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    slot = db.query(CapacitySlot).filter(CapacitySlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    old_values = {"name": slot.name, "type": slot.type.value}

    if slot_data.name is not None:
        slot.name = slot_data.name
    if slot_data.type is not None:
        slot.type = slot_data.type
    if slot_data.user_id is not None:
        slot.user_id = slot_data.user_id
    if slot_data.total_capacity is not None:
        slot.total_capacity = slot_data.total_capacity

    db.commit()

    AuditService.log(db, AuditAction.SLOT_UPDATE, "CapacitySlot", slot.id, current_user,
                     old_value=old_values,
                     new_value={"name": slot.name, "type": slot.type.value})

    return get_slot(slot.id, db, current_user)


@router.delete("/slots/{slot_id}")
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    slot = db.query(CapacitySlot).filter(CapacitySlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    AuditService.log(db, AuditAction.SLOT_DELETE, "CapacitySlot", slot.id, current_user,
                     old_value={"name": slot.name})

    db.delete(slot)
    db.commit()

    return {"message": "Slot deleted"}


# Bindings
@router.get("/bindings", response_model=List[BindingWithSlotResponse])
def list_bindings(
    topic_id: Optional[int] = None,
    slot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Binding).options(joinedload(Binding.slot))

    if topic_id:
        query = query.filter(Binding.topic_id == topic_id)
    if slot_id:
        query = query.filter(Binding.slot_id == slot_id)

    return query.all()


@router.post("/bindings", response_model=BindingWithSlotResponse)
def create_binding(
    binding_data: BindingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # CUSTOMER cannot bind capacity
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot bind capacity")
    
    # Check if admin or has force permission
    if binding_data.is_forced and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can force bindings")

    # Check capacity
    slot = db.query(CapacitySlot).filter(CapacitySlot.id == binding_data.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    current_usage = sum(b.percentage for b in slot.bindings)
    if current_usage + binding_data.percentage > slot.total_capacity and not binding_data.is_forced:
        raise HTTPException(status_code=400, detail="Exceeds slot capacity. Use force option.")

    binding = Binding(
        topic_id=binding_data.topic_id,
        slot_id=binding_data.slot_id,
        percentage=binding_data.percentage,
        is_forced=binding_data.is_forced
    )
    db.add(binding)
    db.commit()
    db.refresh(binding)

    action = AuditAction.BINDING_FORCE if binding_data.is_forced else AuditAction.BINDING_CREATE
    AuditService.log(db, action, "Binding", binding.id, current_user,
                     new_value={"slot_id": binding.slot_id, "percentage": binding.percentage})

    return db.query(Binding).options(joinedload(Binding.slot)).filter(Binding.id == binding.id).first()


@router.put("/bindings/{binding_id}", response_model=BindingWithSlotResponse)
def update_binding(
    binding_id: int,
    binding_data: BindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    binding = db.query(Binding).filter(Binding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")

    old_values = {"percentage": binding.percentage, "is_forced": binding.is_forced}

    if binding_data.percentage is not None:
        binding.percentage = binding_data.percentage
    if binding_data.is_forced is not None:
        binding.is_forced = binding_data.is_forced

    db.commit()

    AuditService.log(db, AuditAction.BINDING_UPDATE, "Binding", binding.id, current_user,
                     old_value=old_values,
                     new_value={"percentage": binding.percentage, "is_forced": binding.is_forced})

    return db.query(Binding).options(joinedload(Binding.slot)).filter(Binding.id == binding.id).first()


@router.delete("/bindings/{binding_id}")
def delete_binding(
    binding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    binding = db.query(Binding).filter(Binding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")

    AuditService.log(db, AuditAction.BINDING_DELETE, "Binding", binding.id, current_user,
                     old_value={"slot_id": binding.slot_id, "percentage": binding.percentage})

    db.delete(binding)
    db.commit()

    return {"message": "Binding deleted"}
