from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from ..database import get_db
from ..models.user import User, UserRole
from ..models.topic import Topic
from ..models.capacity import CapacitySlot, Binding, SlotType
from ..schemas.capacity import (
    SlotCreate, SlotUpdate, SlotResponse,
    BindingCreate, BindingUpdate, BindingWithSlotResponse
)
from ..services.auth import get_current_user, get_current_admin
from ..services.audit import AuditService
from ..models.audit import AuditAction

router = APIRouter()


# =========================
# Slots
# =========================
@router.get("/slots", response_model=List[SlotResponse])
def list_slots(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出所有人力槽位。
    自动为没有 Slot 的 MEMBER/REVIEWER/EXTERNAL 用户创建 Slot。
    """
    users_needing_slots = db.query(User).filter(
        User.role.in_([UserRole.MEMBER, UserRole.REVIEWER, UserRole.EXTERNAL]),
        ~User.id.in_(db.query(CapacitySlot.user_id).filter(CapacitySlot.user_id.isnot(None)))
    ).all()

    for user in users_needing_slots:
        slot_type = SlotType.EXTERNAL if user.role == UserRole.EXTERNAL else SlotType.ALGO
        db.add(CapacitySlot(
            name=user.name,
            type=slot_type,
            user_id=user.id,
            total_capacity=100
        ))

    if users_needing_slots:
        db.commit()

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

    AuditService.log(
        db, AuditAction.SLOT_CREATE, "CapacitySlot", slot.id, current_user,
        new_value={"name": slot.name, "type": slot.type.value}
    )

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

    AuditService.log(
        db, AuditAction.SLOT_UPDATE, "CapacitySlot", slot.id, current_user,
        old_value=old_values,
        new_value={"name": slot.name, "type": slot.type.value}
    )

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

    AuditService.log(
        db, AuditAction.SLOT_DELETE, "CapacitySlot", slot.id, current_user,
        old_value={"name": slot.name}
    )

    db.delete(slot)
    db.commit()

    return {"message": "Slot deleted"}


# =========================
# Bindings
# =========================
@router.get("/bindings", response_model=List[BindingWithSlotResponse])
def list_bindings(
    topic_id: Optional[int] = None,
    slot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Binding).options(
        joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Binding.user),
    )

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

    # Only admin can force bindings
    if binding_data.is_forced and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can force bindings")

    # 支持两种方式：user_id（新）或 slot_id（旧）
    target_user: Optional[User] = None
    slot: Optional[CapacitySlot] = None
    slot_id_final: Optional[int] = None
    user_id_final: Optional[int] = None

    if binding_data.user_id:
        # 新方式：直接用 user_id
        target_user = db.query(User).options(joinedload(User.bindings)).filter(
            User.id == binding_data.user_id
        ).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ 关键修复：用 user_id 反查 slot_id（避免 INSERT slot_id=NULL）
        slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == target_user.id).first()
        if not slot:
            raise HTTPException(status_code=400, detail=f"No capacity slot found for user_id={target_user.id}")

        slot_id_final = slot.id
        user_id_final = target_user.id

        # 检查用户工时（按 user.bindings）
        current_usage = sum(b.percentage for b in (target_user.bindings or []))
        if current_usage + binding_data.percentage > target_user.total_capacity and not binding_data.is_forced:
            raise HTTPException(status_code=400, detail="Exceeds user capacity. Use force option.")

    elif binding_data.slot_id:
        # 旧方式：用 slot_id（向后兼容）
        slot = db.query(CapacitySlot).options(
            joinedload(CapacitySlot.user),
            joinedload(CapacitySlot.bindings),
        ).filter(CapacitySlot.id == binding_data.slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")

        target_user = slot.user
        slot_id_final = slot.id
        user_id_final = slot.user_id

        current_usage = sum(b.percentage for b in (slot.bindings or []))
        if current_usage + binding_data.percentage > slot.total_capacity and not binding_data.is_forced:
            raise HTTPException(status_code=400, detail="Exceeds slot capacity. Use force option.")
    else:
        raise HTTPException(status_code=400, detail="Either user_id or slot_id is required")

    # topic
    topic = db.query(Topic).options(joinedload(Topic.bindings)).filter(
        Topic.id == binding_data.topic_id
    ).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Determine DRI
    should_be_dri = binding_data.is_dri
    if should_be_dri is None:
        existing_dri = next((b for b in (topic.bindings or []) if b.is_dri), None)
        should_be_dri = existing_dri is None

    # If setting as DRI, unset any existing DRI
    if should_be_dri:
        for b in (topic.bindings or []):
            if b.is_dri:
                b.is_dri = False

    # ✅ 最终写入：slot_id 一定非空
    binding = Binding(
        topic_id=binding_data.topic_id,
        slot_id=slot_id_final,
        user_id=user_id_final,
        percentage=binding_data.percentage,
        is_forced=binding_data.is_forced,
        is_dri=should_be_dri
    )
    db.add(binding)

    # legacy dri_id
    if should_be_dri and target_user:
        topic.dri_id = target_user.id

    db.commit()
    db.refresh(binding)

    action = AuditAction.BINDING_FORCE if binding_data.is_forced else AuditAction.BINDING_CREATE
    AuditService.log(
        db, action, "Binding", binding.id, current_user,
        new_value={
            "topic_id": binding.topic_id,
            "slot_id": binding.slot_id,
            "user_id": binding.user_id,
            "user_name": target_user.name if target_user else None,
            "percentage": binding.percentage,
            "is_dri": binding.is_dri
        }
    )

    return db.query(Binding).options(
        joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Binding.user)
    ).filter(Binding.id == binding.id).first()


@router.put("/bindings/{binding_id}", response_model=BindingWithSlotResponse)
def update_binding(
    binding_id: int,
    binding_data: BindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    binding = db.query(Binding).options(
        joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Binding.user),
        joinedload(Binding.topic).joinedload(Topic.bindings)
    ).filter(Binding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")

    old_values = {
        "percentage": binding.percentage,
        "is_forced": binding.is_forced,
        "is_dri": binding.is_dri
    }

    if binding_data.percentage is not None:
        binding.percentage = binding_data.percentage
    if binding_data.is_forced is not None:
        binding.is_forced = binding_data.is_forced

    # Handle DRI change
    if binding_data.is_dri is not None and binding_data.is_dri != binding.is_dri:
        if binding_data.is_dri:
            # set this as DRI, unset others
            for b in (binding.topic.bindings or []):
                if b.id != binding.id and b.is_dri:
                    b.is_dri = False
            binding.is_dri = True
            if binding.user_id:
                binding.topic.dri_id = binding.user_id
        else:
            binding.is_dri = False

    db.commit()

    AuditService.log(
        db, AuditAction.BINDING_UPDATE, "Binding", binding.id, current_user,
        old_value=old_values,
        new_value={
            "percentage": binding.percentage,
            "is_forced": binding.is_forced,
            "is_dri": binding.is_dri
        }
    )

    return db.query(Binding).options(
        joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Binding.user)
    ).filter(Binding.id == binding.id).first()


@router.delete("/bindings/{binding_id}")
def delete_binding(
    binding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    binding = db.query(Binding).options(
        joinedload(Binding.topic).joinedload(Topic.bindings),
        joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Binding.user),
    ).filter(Binding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")

    was_dri = binding.is_dri
    topic = binding.topic

    AuditService.log(
        db, AuditAction.BINDING_DELETE, "Binding", binding.id, current_user,
        old_value={
            "slot_id": binding.slot_id,
            "user_id": binding.user_id,
            "percentage": binding.percentage,
            "is_dri": binding.is_dri
        }
    )

    db.delete(binding)

    # If deleted DRI, re-assign
    if was_dri:
        remaining = [b for b in (topic.bindings or []) if b.id != binding_id]
        if remaining:
            remaining[0].is_dri = True
            topic.dri_id = remaining[0].user_id
        else:
            topic.dri_id = None

    db.commit()
    return {"message": "Binding deleted"}


# =========================
# Workforce (User-based)
# =========================
@router.get("/workforce")
def list_workforce(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取可分配人力列表（基于 User）
    - type=ALGO: MEMBER + REVIEWER（自有人力）
    - type=EXTERNAL: EXTERNAL（协调人力）
    - 不传: 全部
    """
    query = db.query(User).options(joinedload(User.bindings))

    if type == "ALGO":
        query = query.filter(User.role.in_([UserRole.MEMBER, UserRole.REVIEWER]))
    elif type == "EXTERNAL":
        query = query.filter(User.role == UserRole.EXTERNAL)
    else:
        query = query.filter(User.role.in_([UserRole.MEMBER, UserRole.REVIEWER, UserRole.EXTERNAL]))

    users = query.order_by(User.name).all()

    result = []
    for user in users:
        used_capacity = sum(b.percentage for b in (user.bindings or []))
        user_type = "EXTERNAL" if user.role == UserRole.EXTERNAL else "ALGO"  # ✅ REVIEWER 也算 ALGO

        result.append({
            "id": user.id,
            "name": user.name,
            "type": user_type,
            "userId": user.id,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            },
            "totalCapacity": user.total_capacity,
            "usedCapacity": used_capacity,
            "remainingCapacity": user.total_capacity - used_capacity,
            "bindings": [
                {
                    "id": b.id,
                    "topicId": b.topic_id,
                    "userId": b.user_id,
                    "percentage": b.percentage,
                    "isDri": b.is_dri,
                }
                for b in (user.bindings or [])
            ],
        })

    return result
