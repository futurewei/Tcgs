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

    # 导入相关模型
    from ..models.topic import Topic
    from ..models.wiki import WikiPage, WikiRevision, WikiComment, WikiLike
    from ..models.algo_delivery import AlgoDelivery
    from ..models.audit import AuditLog
    from ..models.artifact import Artifact
    from ..models.review import ReviewComment
    from ..models.stage_instance import StageDeliverable

    # 检查是否有 DRI 课题
    dri_topics_count = db.query(Topic).filter(Topic.dri_id == user_id).count()
    if dri_topics_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：该用户是 {dri_topics_count} 个课题的 DRI，请先转移课题负责人"
        )

    # 检查是否有容量绑定
    user_slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == user_id).first()
    if user_slot and user_slot.bindings:
        raise HTTPException(
            status_code=400,
            detail="无法删除：该用户有容量绑定记录，请先解除绑定"
        )

    # 检查是否有 Wiki 修订版本（这些不能设为 NULL）
    wiki_revisions_count = db.query(WikiRevision).filter(WikiRevision.created_by_id == user_id).count()
    if wiki_revisions_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：该用户有 {wiki_revisions_count} 个 Wiki 修订记录"
        )

    # 检查是否有 Wiki 评论
    wiki_comments_count = db.query(WikiComment).filter(WikiComment.created_by_id == user_id).count()
    if wiki_comments_count > 0:
        # 删除用户的评论
        db.query(WikiComment).filter(WikiComment.created_by_id == user_id).delete(synchronize_session=False)

    # 检查是否有算法交付记录作为责任人
    algo_owner_count = db.query(AlgoDelivery).filter(AlgoDelivery.owner_id == user_id).count()
    if algo_owner_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：该用户是 {algo_owner_count} 个算法能力的责任人，请先转移责任人"
        )

    # 检查是否有算法交付记录作为创建者
    algo_creator_count = db.query(AlgoDelivery).filter(AlgoDelivery.created_by_id == user_id).count()
    if algo_creator_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：该用户创建了 {algo_creator_count} 个算法能力记录"
        )

    # 删除用户的 Slot（如果没有绑定）
    if user_slot:
        db.delete(user_slot)

    # 将 WikiPage 的创建者设为 NULL（这个字段是 nullable=True）
    db.query(WikiPage).filter(WikiPage.created_by_id == user_id).update(
        {WikiPage.created_by_id: None}, synchronize_session=False
    )

    # 删除用户的点赞记录
    db.query(WikiLike).filter(WikiLike.user_id == user_id).delete(synchronize_session=False)

    # 将算法交付的交付确认者设为 NULL（这个字段是 nullable=True）
    db.query(AlgoDelivery).filter(AlgoDelivery.delivered_by_id == user_id).update(
        {AlgoDelivery.delivered_by_id: None}, synchronize_session=False
    )

    # 审计日志保留，将 user_id 设为 NULL
    db.query(AuditLog).filter(AuditLog.user_id == user_id).update(
        {AuditLog.user_id: None}, synchronize_session=False
    )

    # 先记录删除日志（在删除用户之前）
    AuditService.log(db, AuditAction.USER_DELETE, "User", user.id, current_user,
                     old_value={"email": user.email, "name": user.name})

    db.delete(user)
    db.commit()

    return {"message": "User deleted"}
