from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from math import ceil
from ..database import get_db
from ..models.user import User, UserRole
from ..models.audit import AuditAction
from ..models.capacity import CapacitySlot, SlotType
from ..schemas.user import UserCreate, UserUpdate, UserResponse
from ..schemas.common import PaginatedResponse
from ..services.auth import AuthService, get_current_user, get_current_admin
from ..services.audit import AuditService

router = APIRouter()


def sync_user_slot(db: Session, user: User):
    """同步用户的 Slot（创建或更新）"""
    # 只有 MEMBER/REVIEWER/EXTERNAL 需要 Slot
    needs_slot = user.role in [UserRole.MEMBER, UserRole.REVIEWER, UserRole.EXTERNAL]
    
    # 查找现有 Slot
    existing_slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == user.id).first()
    
    if needs_slot:
        slot_type = SlotType.EXTERNAL if user.role == UserRole.EXTERNAL else SlotType.ALGO
        if existing_slot:
            # 更新现有 Slot
            existing_slot.name = user.name
            existing_slot.type = slot_type
        else:
            # 创建新 Slot
            new_slot = CapacitySlot(
                name=user.name,
                type=slot_type,
                user_id=user.id,
                total_capacity=100
            )
            db.add(new_slot)
    elif existing_slot:
        # 用户角色变更为不需要 Slot 的角色，检查是否有 binding
        if not existing_slot.bindings:
            db.delete(existing_slot)


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """列出所有用户 - 仅限 Admin"""
    total = db.query(User).count()
    users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size)
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=AuthService.get_password_hash(user_data.password),
        role=user_data.role
    )
    db.add(user)
    db.flush()  # 获取 user.id
    
    # 自动创建关联的 Slot
    sync_user_slot(db, user)
    
    db.commit()
    db.refresh(user)

    AuditService.log(db, AuditAction.USER_CREATE, "User", user.id, current_user,
                     new_value={"email": user.email, "role": user.role.value})

    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_values = {"email": user.email, "name": user.name, "role": user.role.value}

    if user_data.email is not None:
        user.email = user_data.email
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.password is not None:
        user.hashed_password = AuthService.get_password_hash(user_data.password)

    # 同步更新关联的 Slot
    sync_user_slot(db, user)
    
    db.commit()
    db.refresh(user)

    AuditService.log(db, AuditAction.USER_UPDATE, "User", user.id, current_user,
                     old_value=old_values,
                     new_value={"email": user.email, "name": user.name, "role": user.role.value})

    return user


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role.value
    user.role = role_data["role"]
    db.commit()
    db.refresh(user)

    AuditService.log(db, AuditAction.USER_UPDATE, "User", user.id, current_user,
                     old_value={"role": old_role},
                     new_value={"role": user.role.value})

    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    AuditService.log(db, AuditAction.USER_DELETE, "User", user.id, current_user,
                     old_value={"email": user.email, "name": user.name})

    db.delete(user)
    db.commit()

    return {"message": "User deleted"}
