# backend/app/api/topics.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func
from typing import Optional, List
from math import ceil
from datetime import datetime
from pydantic import BaseModel

from ..database import get_db
from ..models.user import User, UserRole
from ..models.topic import Topic, TopicStageState, StageStatus, TopicType, TopicResult
from ..models.template import StageTemplate, StageTemplateStage
from ..models.artifact import Artifact
from ..models.review import ReviewComment
from ..models.deliverable import StageDeliverable
from ..models.capacity import Binding, CapacitySlot
from ..models.audit import AuditAction
from ..models.stage_instance import TopicStageInstance, StageInstanceStatus
from ..schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse,
    ArtifactCreate, ArtifactResponse,
    ReviewCreate, ReviewResponse,
    StageDeliverableCreate, StageDeliverableResponse,
    ChangeDRIRequest
)
from ..schemas.common import PaginatedResponse
from ..services.auth import get_current_user, get_current_admin
from ..services.audit import AuditService

router = APIRouter()


# =========================
# DRI slot resolve helpers
# =========================

def _ensure_user_has_slot(db: Session, user: User) -> CapacitySlot:
    """
    保证 user 至少有一个 CapacitySlot。
    - 有就返回第一个（按 id 升序）
    - 没有就创建一个默认 slot（name 对齐 user.name）
    """
    slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == user.id).order_by(CapacitySlot.id.asc()).first()
    if slot:
        return slot

    try:
        new_slot = CapacitySlot(
            name=user.name,
            user_id=user.id,
            total_capacity=100
        )
        db.add(new_slot)
        db.flush()
        return new_slot
    except TypeError:
        new_slot = CapacitySlot(
            name=user.name,
            user_id=user.id
        )
        db.add(new_slot)
        db.flush()
        return new_slot


def _resolve_slot_by_id_or_user_id(db: Session, maybe_slot_or_user_id: int) -> CapacitySlot:
    """
    兼容前端传参：
    - 可能传 CapacitySlot.id（老逻辑）
    - 也可能传 User.id（新逻辑）
    """
    slot = db.query(CapacitySlot).filter(CapacitySlot.id == maybe_slot_or_user_id).first()
    if slot:
        return slot

    user = db.query(User).filter(User.id == maybe_slot_or_user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Initial DRI slot/user not found")

    return _ensure_user_has_slot(db, user)


def _get_topic_with_relations(db: Session, topic_id: int):
    """Helper to get topic with all relations loaded"""
    return db.query(Topic).options(
        joinedload(Topic.dri),
        joinedload(Topic.requester_user),
        joinedload(Topic.template).joinedload(StageTemplate.stages),
        joinedload(Topic.stage_states).joinedload(TopicStageState.stage),
        joinedload(Topic.stage_instances),
        joinedload(Topic.artifacts).joinedload(Artifact.created_by),
        joinedload(Topic.reviews).joinedload(ReviewComment.created_by),
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Topic.deliverables).joinedload(StageDeliverable.created_by)
    ).filter(Topic.id == topic_id).first()


def user_can_view_all_topics(user: User) -> bool:
    """
    ADMIN, MEMBER, REVIEWER 可以查看所有课题
    CUSTOMER, EXTERNAL 只能查看关联的课题
    """
    return user.role in [UserRole.ADMIN, UserRole.MEMBER, UserRole.REVIEWER]


def filter_topics_by_user_access(query, user: User, db: Session):
    """
    CUSTOMER: 只能看到自己作为需求方的课题
    EXTERNAL: 只能看到自己被分配到的课题（通过 Binding -> CapacitySlot -> user_id）
    """
    if user.role == UserRole.CUSTOMER:
        query = query.filter(Topic.requester_user_id == user.id)
    elif user.role == UserRole.EXTERNAL:
        subquery = db.query(Binding.topic_id).join(CapacitySlot).filter(
            CapacitySlot.user_id == user.id
        ).distinct()
        query = query.filter(Topic.id.in_(subquery))
    return query


def check_topic_access(topic: Topic, user: User, db: Session) -> bool:
    if user_can_view_all_topics(user):
        return True

    if user.role == UserRole.CUSTOMER:
        return topic.requester_user_id == user.id
    elif user.role == UserRole.EXTERNAL:
        binding = db.query(Binding).join(CapacitySlot).filter(
            Binding.topic_id == topic.id,
            CapacitySlot.user_id == user.id
        ).first()
        return binding is not None

    return False


# =========================
# Result gating helpers
# =========================

def _is_admin(user: User) -> bool:
    return getattr(user, "role", None) == UserRole.ADMIN


def _can_non_admin_change_result(topic: Topic) -> bool:
    """
    非 admin：只有当“当前 StageInstance”满足 allow_result 且 is_terminal 才允许结项。

    ✅ 重要：你现在 create_topic 已经在用 current_stage_instance_id，
    所以判断必须基于 current_stage_instance_id，而不是 current_stage_id。
    """
    cur_inst_id = getattr(topic, "current_stage_instance_id", None)
    if not cur_inst_id:
        return False

    instances = getattr(topic, "stage_instances", None) or []
    cur = next((x for x in instances if getattr(x, "id", None) == cur_inst_id), None)
    if not cur:
        return False

    return bool(getattr(cur, "is_terminal", False) and getattr(cur, "allow_result", False))


# =========================
# Topics
# =========================

@router.get("", response_model=PaginatedResponse[TopicResponse])
def list_topics(
    search: Optional[str] = None,
    type: Optional[str] = None,
    urgency: Optional[str] = None,
    result: Optional[str] = None,
    dri_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Topic).options(
        joinedload(Topic.dri),
        joinedload(Topic.template).joinedload(StageTemplate.stages),
        joinedload(Topic.stage_states).joinedload(TopicStageState.stage),
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Topic.stage_instances)  # ✅ dashboard 如要用 instance 状态也能拿到
    )

    query = filter_topics_by_user_access(query, current_user, db)

    if search:
        query = query.filter(
            (Topic.title.ilike(f"%{search}%")) |
            (Topic.id == int(search) if search.isdigit() else False)
        )
    if type:
        query = query.filter(Topic.type == type)
    if urgency:
        query = query.filter(Topic.urgency == urgency)
    if result:
        query = query.filter(Topic.result == result)

    if dri_id:
        query = query.join(Binding, isouter=True).join(CapacitySlot, isouter=True).filter(
            Binding.is_dri == True,
            CapacitySlot.user_id == dri_id
        )

    total = query.count()
    topics = query.order_by(Topic.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=[TopicResponse.model_validate(t) for t in topics],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 1
    )


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    topic = _get_topic_with_relations(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if not check_topic_access(topic, current_user, db):
        raise HTTPException(status_code=403, detail="You don't have permission to view this topic")

    return topic


@router.post("", response_model=TopicResponse)
def create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create topics")

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can create topics")

    # Validate requester
    requester_name = topic_data.requester_name
    if topic_data.requester_user_id is not None:
        requester_user = db.query(User).filter(User.id == topic_data.requester_user_id).first()
        if not requester_user:
            raise HTTPException(status_code=400, detail="Requester user not found")
        if requester_user.role != UserRole.CUSTOMER:
            raise HTTPException(status_code=400, detail="Only CUSTOMER users can be requester")
        requester_name = requester_user.name
    else:
        if not topic_data.requester_name or not topic_data.requester_name.strip():
            raise HTTPException(
                status_code=400,
                detail="requester_name is required when requester_user_id is not provided"
            )
        requester_name = topic_data.requester_name.strip()

    # Validate template exists
    template = db.query(StageTemplate).options(
        joinedload(StageTemplate.stages)
    ).filter(StageTemplate.id == topic_data.template_id).first()
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")

    topic = Topic(
        title=topic_data.title,
        description=topic_data.description,
        background=topic_data.background,
        user_goal=topic_data.user_goal,
        type=topic_data.type,
        urgency=topic_data.urgency,
        template_id=topic_data.template_id,
        requester_name=requester_name,
        requester_user_id=topic_data.requester_user_id,
    )
    db.add(topic)
    db.flush()

    # 旧逻辑：只为演进课题创建 stage_states + current_stage_id
    if topic_data.type != TopicType.UNCERTAINTY:
        for i, stage in enumerate(template.stages):
            state = TopicStageState(
                topic_id=topic.id,
                stage_id=stage.id,
                status=StageStatus.ACTIVE if i == 0 else StageStatus.PENDING
            )
            db.add(state)
            if i == 0:
                topic.current_stage_id = stage.id

    # 新逻辑：创建 Stage Instances
    first_instance = None
    if topic_data.type != TopicType.UNCERTAINTY:
        for i, stage in enumerate(template.stages):
            instance = TopicStageInstance(
                topic_id=topic.id,
                name=stage.name,
                description=stage.description,
                order=float(i),
                is_terminal=stage.is_terminal,
                allow_result=stage.allow_result,
                require_artifact=stage.require_artifact,
                status=StageInstanceStatus.ACTIVE if i == 0 else StageInstanceStatus.PENDING,
                template_stage_id=stage.id,
                created_by_id=current_user.id
            )
            if i == 0:
                instance.started_at = datetime.utcnow()
                first_instance = instance
            db.add(instance)

    db.flush()

    if first_instance:
        topic.current_stage_instance_id = first_instance.id

    # ========= Initial DRI binding =========
    def resolve_initial_dri_slot(slot_or_user_id: int) -> Optional[CapacitySlot]:
        slot = db.query(CapacitySlot).filter(CapacitySlot.id == slot_or_user_id).first()
        if slot:
            return slot

        slots = db.query(CapacitySlot).filter(CapacitySlot.user_id == slot_or_user_id).all()
        if not slots:
            return None

        try:
            internal = [s for s in slots if getattr(s, "type", None) and str(getattr(s, "type")).upper().find("EXTERNAL") < 0]
            if internal:
                return internal[0]
        except Exception:
            pass

        return slots[0]

    if topic_data.initial_dri_slot_id:
        slot = resolve_initial_dri_slot(int(topic_data.initial_dri_slot_id))
        if not slot:
            raise HTTPException(
                status_code=400,
                detail=f"Initial DRI slot not found (received={topic_data.initial_dri_slot_id}). "
                       f"Expected CapacitySlot.id, but userId is also supported now. "
                       f"Please ensure the user has at least one CapacitySlot."
            )

        binding = Binding(
            topic_id=topic.id,
            slot_id=slot.id,
            user_id=slot.user_id,  # ✅补齐：后续权限判断/统计更稳
            percentage=topic_data.initial_dri_percentage,
            is_dri=True
        )
        db.add(binding)

        if slot.user_id:
            topic.dri_id = slot.user_id

    db.commit()
    db.refresh(topic)

    AuditService.log(
        db,
        AuditAction.TOPIC_CREATE,
        "Topic",
        topic.id,
        current_user,
        new_value={"title": topic.title, "type": topic.type.value}
    )

    topic = _get_topic_with_relations(db, topic.id)
    return TopicResponse.model_validate(topic)


@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot update topics")

    # ✅ 必须用 relations 版本：否则 bindings/template/stage_instances 可能不全，导致校验/权限/同步失败
    topic = _get_topic_with_relations(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    old_values = {}

    # =========================
    # Result change - 只有 ADMIN 可以操作
    # =========================
    if topic_data.result is not None and topic_data.result != topic.result:
        # ✅ result 变更（标记已解决/无法完成）只允许 ADMIN
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="只有管理员可以变更课题状态（已解决/无法完成）")

        old_result = topic.result
        old_values["result"] = old_result.value

        topic.result = topic_data.result

        # 自动设置/清除 closed_at
        if topic_data.result in [TopicResult.SUCCESS, TopicResult.UNSOLVABLE]:
            # 关闭课题时设置关闭时间
            topic.closed_at = datetime.utcnow()
        elif topic_data.result == TopicResult.OPEN:
            # 重新打开课题时清除关闭时间
            topic.closed_at = None

        AuditService.log(
            db,
            AuditAction.RESULT_CHANGE,
            "Topic",
            topic.id,
            current_user,
            old_value={"result": old_values["result"]},
            new_value={"result": topic.result.value}
        )

    # =========================
    # Other fields - 所有登录用户（非 CUSTOMER）可以操作
    # =========================
    if topic_data.title is not None:
        topic.title = topic_data.title
    if topic_data.description is not None:
        topic.description = topic_data.description
    if topic_data.background is not None:
        topic.background = topic_data.background
    if topic_data.user_goal is not None:
        topic.user_goal = topic_data.user_goal
    if topic_data.urgency is not None:
        topic.urgency = topic_data.urgency

    db.commit()
    return _get_topic_with_relations(db, topic.id)


# =========================
# Stage advance/backward
# =========================

@router.post("/{topic_id}/stages/{stage_id}/advance", response_model=TopicResponse)
def advance_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot advance stage")

    # ✅ 要同时拿到 bindings + stage_states + stage_instances + template
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot),
        joinedload(Topic.stage_states),
        joinedload(Topic.stage_instances),
        joinedload(Topic.template).joinedload(StageTemplate.stages)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    dri_binding = next((b for b in (topic.bindings or []) if b.is_dri), None)
    is_dri = bool(dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id)

    if current_user.role != UserRole.ADMIN and not is_dri:
        raise HTTPException(status_code=403, detail="Not authorized")

    # -------------------------
    # 旧逻辑：TopicStageState + current_stage_id
    # -------------------------
    current_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == topic.current_stage_id
    ).first()
    if current_state:
        current_state.status = StageStatus.DONE
        current_state.completed_at = datetime.utcnow()

    new_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == stage_id
    ).first()
    if new_state:
        new_state.status = StageStatus.ACTIVE

    old_stage_id = topic.current_stage_id
    topic.current_stage_id = stage_id

    # -------------------------
    # ✅ 新逻辑：StageInstance + current_stage_instance_id
    #    解决 “detail 点到了最后，但 dashboard 颜色还停第一阶段”
    # -------------------------
    cur_inst_id = getattr(topic, "current_stage_instance_id", None)

    # 1) 当前 instance -> DONE
    if cur_inst_id:
        cur_inst = next((i for i in (topic.stage_instances or []) if i.id == cur_inst_id), None)
        if cur_inst:
            cur_inst.status = StageInstanceStatus.DONE
            cur_inst.completed_at = datetime.utcnow()

    # 2) 目标 instance -> ACTIVE
    # stage_id 是模板 stage id，所以要通过 template_stage_id 找对应 instance
    target_inst = next((i for i in (topic.stage_instances or []) if getattr(i, "template_stage_id", None) == stage_id), None)
    if target_inst:
        target_inst.status = StageInstanceStatus.ACTIVE
        if not getattr(target_inst, "started_at", None):
            target_inst.started_at = datetime.utcnow()
        topic.current_stage_instance_id = target_inst.id

    db.commit()

    AuditService.log(
        db,
        AuditAction.STAGE_CHANGE,
        "Topic",
        topic.id,
        current_user,
        old_value={"stage_id": old_stage_id, "action": "advance"},
        new_value={"stage_id": stage_id}
    )

    return _get_topic_with_relations(db, topic.id)


@router.post("/{topic_id}/stages/{stage_id}/backward", response_model=TopicResponse)
def backward_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot change stage")

    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot),
        joinedload(Topic.template).joinedload(StageTemplate.stages),
        joinedload(Topic.stage_states),
        joinedload(Topic.stage_instances)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    dri_binding = next((b for b in (topic.bindings or []) if b.is_dri), None)
    is_dri = bool(dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id)

    if current_user.role != UserRole.ADMIN and not is_dri:
        raise HTTPException(status_code=403, detail="Not authorized")

    target_stage = next((s for s in (topic.template.stages or []) if s.id == stage_id), None)
    if not target_stage:
        raise HTTPException(status_code=400, detail="Target stage not found")

    current_stage = next((s for s in (topic.template.stages or []) if s.id == topic.current_stage_id), None)
    if current_stage and target_stage.order >= current_stage.order:
        raise HTTPException(status_code=400, detail="Can only go backward to previous stages")

    # -------------------------
    # 旧逻辑：stage_states
    # -------------------------
    current_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == topic.current_stage_id
    ).first()
    if current_state:
        current_state.status = StageStatus.PENDING
        current_state.completed_at = None

    for stage in (topic.template.stages or []):
        if stage.order > target_stage.order:
            state = db.query(TopicStageState).filter(
                TopicStageState.topic_id == topic_id,
                TopicStageState.stage_id == stage.id
            ).first()
            if state:
                state.status = StageStatus.PENDING
                state.completed_at = None

    target_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == stage_id
    ).first()
    if target_state:
        target_state.status = StageStatus.ACTIVE
        target_state.completed_at = None

    old_stage_id = topic.current_stage_id
    topic.current_stage_id = stage_id

    # -------------------------
    # ✅ 新逻辑：stage_instances 同步
    # -------------------------
    # 用模板 stage 的 order 做比较，然后映射到对应 instance（template_stage_id）
    stage_order_map = {s.id: s.order for s in (topic.template.stages or [])}

    # 当前 instance 设回 PENDING（对应旧逻辑“当前阶段回退成 pending”）
    cur_inst_id = getattr(topic, "current_stage_instance_id", None)
    if cur_inst_id:
        cur_inst = next((i for i in (topic.stage_instances or []) if i.id == cur_inst_id), None)
        if cur_inst:
            cur_inst.status = StageInstanceStatus.PENDING
            cur_inst.completed_at = None

    # 大于 target 的全部 pending；target active
    for inst in (topic.stage_instances or []):
        tsid = getattr(inst, "template_stage_id", None)
        if not tsid or tsid not in stage_order_map:
            continue

        if stage_order_map[tsid] > target_stage.order:
            inst.status = StageInstanceStatus.PENDING
            inst.completed_at = None

    target_inst = next((i for i in (topic.stage_instances or []) if getattr(i, "template_stage_id", None) == stage_id), None)
    if target_inst:
        target_inst.status = StageInstanceStatus.ACTIVE
        target_inst.completed_at = None
        if not getattr(target_inst, "started_at", None):
            target_inst.started_at = datetime.utcnow()
        topic.current_stage_instance_id = target_inst.id

    db.commit()

    AuditService.log(
        db,
        AuditAction.STAGE_CHANGE,
        "Topic",
        topic.id,
        current_user,
        old_value={"stage_id": old_stage_id, "action": "backward"},
        new_value={"stage_id": stage_id}
    )

    return _get_topic_with_relations(db, topic.id)


@router.post("/{topic_id}/change-dri", response_model=TopicResponse)
def change_dri(
    topic_id: int,
    request: ChangeDRIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change the DRI of a topic to a different slot/person.
    Permission: Only ADMIN or current DRI can change DRI

    ✅ 兼容 request.new_dri_slot_id：
    - 可能是 slot_id
    - 也可能是 user_id（前端选人）
    """
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    old_dri_binding = next((b for b in (topic.bindings or []) if b.is_dri), None)
    old_dri_name = None
    old_dri_user_id = None
    if old_dri_binding and old_dri_binding.slot:
        old_dri_name = old_dri_binding.slot.name
        old_dri_user_id = old_dri_binding.slot.user_id

    is_admin = current_user.role == UserRole.ADMIN
    is_current_dri = bool(old_dri_user_id and old_dri_user_id == current_user.id)

    if not is_admin and not is_current_dri:
        raise HTTPException(status_code=403, detail="只有管理员或当前 DRI 本人可以更换负责人")

    new_slot = _resolve_slot_by_id_or_user_id(db, int(request.new_dri_slot_id))

    existing_binding = next((b for b in (topic.bindings or []) if b.slot_id == new_slot.id), None)

    if existing_binding:
        if old_dri_binding and old_dri_binding.id != existing_binding.id:
            old_dri_binding.is_dri = False
        existing_binding.is_dri = True
    else:
        if old_dri_binding:
            old_dri_binding.is_dri = False

        new_binding = Binding(
            topic_id=topic_id,
            slot_id=new_slot.id,
            user_id=new_slot.user_id,  # ✅补齐：保持一致
            percentage=25,
            is_dri=True
        )
        db.add(new_binding)

    if new_slot.user_id:
        topic.dri_id = new_slot.user_id

    db.commit()
    db.refresh(topic)

    try:
        AuditService.log(
            db,
            AuditAction.DRI_CHANGE,
            "Topic",
            topic.id,
            current_user,
            old_value={"dri_slot": old_dri_name},
            new_value={"dri_slot": new_slot.name}
        )
    except Exception as e:
        print(f"Audit log failed: {e}")

    return _get_topic_with_relations(db, topic.id)


# =========================
# Artifacts
# =========================

@router.get("/{topic_id}/artifacts", response_model=List[ArtifactResponse])
def list_artifacts(
    topic_id: int,
    stage_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Artifact).options(
        joinedload(Artifact.created_by)
    ).filter(Artifact.topic_id == topic_id)

    if stage_id:
        query = query.filter(Artifact.stage_id == stage_id)

    return query.order_by(Artifact.created_at.desc()).all()


@router.post("/{topic_id}/artifacts", response_model=ArtifactResponse)
def create_artifact(
    topic_id: int,
    artifact_data: ArtifactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create artifacts")

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    artifact = Artifact(
        topic_id=topic_id,
        stage_id=artifact_data.stage_id,
        title=artifact_data.title,
        content=artifact_data.content,
        created_by_id=current_user.id
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return artifact


# =========================
# Reviews
# =========================

@router.get("/{topic_id}/reviews", response_model=List[ReviewResponse])
def list_reviews(
    topic_id: int,
    stage_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ReviewComment).options(
        joinedload(ReviewComment.created_by)
    ).filter(ReviewComment.topic_id == topic_id)

    if stage_id:
        query = query.filter(ReviewComment.stage_id == stage_id)

    return query.order_by(ReviewComment.created_at.asc()).all()


@router.post("/{topic_id}/reviews", response_model=ReviewResponse)
def create_review(
    topic_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create reviews")

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    review = ReviewComment(
        topic_id=topic_id,
        stage_id=review_data.stage_id,
        content=review_data.content,
        created_by_id=current_user.id
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.delete("/{topic_id}")
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    AuditService.log(db, AuditAction.TOPIC_DELETE, "Topic", topic.id, current_user,
                     old_value={"title": topic.title})

    db.delete(topic)
    db.commit()

    return {"message": "Topic deleted"}


# =========================
# Stage Deliverables
# =========================

@router.get("/{topic_id}/deliverables", response_model=List[StageDeliverableResponse])
def list_deliverables(
    topic_id: int,
    stage_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StageDeliverable).options(
        joinedload(StageDeliverable.created_by)
    ).filter(StageDeliverable.topic_id == topic_id)

    if stage_id:
        query = query.filter(StageDeliverable.stage_id == stage_id)

    return query.order_by(StageDeliverable.created_at.desc()).all()


@router.post("/{topic_id}/deliverables", response_model=StageDeliverableResponse)
def create_deliverable(
    topic_id: int,
    deliverable_data: StageDeliverableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create deliverables")

    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    dri_binding = next((b for b in (topic.bindings or []) if b.is_dri), None)
    is_dri = bool(dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id)

    if current_user.role != UserRole.ADMIN and not is_dri:
        raise HTTPException(status_code=403, detail="Not authorized to add deliverables")

    deliverable = StageDeliverable(
        topic_id=topic_id,
        stage_id=deliverable_data.stage_id,
        name=deliverable_data.name,
        type=deliverable_data.type,
        url=deliverable_data.url,
        description=deliverable_data.description,
        file_name=deliverable_data.file_name,
        file_size=deliverable_data.file_size,
        mime_type=deliverable_data.mime_type,
        created_by_id=current_user.id
    )
    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)

    return deliverable


@router.delete("/{topic_id}/deliverables/{deliverable_id}")
def delete_deliverable(
    topic_id: int,
    deliverable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot delete deliverables")

    deliverable = db.query(StageDeliverable).filter(
        StageDeliverable.id == deliverable_id,
        StageDeliverable.topic_id == topic_id
    ).first()

    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot)
    ).filter(Topic.id == topic_id).first()

    dri_binding = next((b for b in (topic.bindings or []) if b.is_dri), None)
    is_dri = bool(dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id)

    if (current_user.role != UserRole.ADMIN and
        not is_dri and
        deliverable.created_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this deliverable")

    db.delete(deliverable)
    db.commit()

    return {"message": "Deliverable deleted"}


# ============ Topic-level Tech Points (算法思想) ============

class TopicTechPointCreate(BaseModel):
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    first_author_id: int

class TopicTechPointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    approach: Optional[str] = None
    conclusion: Optional[str] = None
    status: Optional[str] = None


@router.get("/{topic_id}/members")
def get_topic_members(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user)
    ).filter(Topic.id == topic_id).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    members = []
    for binding in (topic.bindings or []):
        if binding.slot:
            user = binding.slot.user
            member = {
                "slotId": binding.slot.id,
                "slotName": binding.slot.name,
                "slotType": binding.slot.type.value if binding.slot.type else None,
                "userId": user.id if user else None,
                "userName": binding.slot.name,
                "userRole": user.role.value if user else None,
                "isDri": binding.is_dri,
            }
            members.append(member)

    return members


@router.get("/{topic_id}/tech-points")
def list_topic_tech_points(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ..models.stage_instance import TechPoint

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    tech_points = db.query(TechPoint).options(
        joinedload(TechPoint.first_author)
    ).filter(TechPoint.topic_id == topic_id).order_by(TechPoint.created_at.desc()).all()

    return [{
        "id": tp.id,
        "name": tp.name,
        "description": tp.description,
        "hypothesis": tp.hypothesis,
        "approach": tp.approach,
        "conclusion": tp.conclusion,
        "status": tp.status,
        "firstAuthorId": tp.first_author_id,
        "firstAuthorName": tp.first_author.name if tp.first_author else None,
        "createdAt": tp.created_at.isoformat() if tp.created_at else None,
    } for tp in tech_points]


@router.post("/{topic_id}/tech-points")
def create_topic_tech_point(
    topic_id: int,
    data: TopicTechPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ..models.stage_instance import TechPoint

    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create tech points")

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    author = db.query(User).filter(User.id == data.first_author_id).first()
    if not author:
        raise HTTPException(status_code=400, detail="First author not found")

    max_order = db.query(sql_func.max(TechPoint.order)).filter(
        TechPoint.topic_id == topic_id
    ).scalar() or 0

    tech_point = TechPoint(
        topic_id=topic_id,
        name=data.name,
        description=data.description,
        hypothesis=data.hypothesis,
        first_author_id=data.first_author_id,
        order=max_order + 1,
    )
    db.add(tech_point)
    db.commit()
    db.refresh(tech_point)

    return {
        "id": tech_point.id,
        "name": tech_point.name,
        "description": tech_point.description,
        "hypothesis": tech_point.hypothesis,
        "approach": tech_point.approach,
        "conclusion": tech_point.conclusion,
        "status": tech_point.status,
        "firstAuthorId": tech_point.first_author_id,
        "firstAuthorName": author.name,
        "createdAt": tech_point.created_at.isoformat() if tech_point.created_at else None,
    }


@router.put("/{topic_id}/tech-points/{point_id}")
def update_topic_tech_point(
    topic_id: int,
    point_id: int,
    data: TopicTechPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ..models.stage_instance import TechPoint

    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot update tech points")

    tech_point = db.query(TechPoint).filter(
        TechPoint.id == point_id,
        TechPoint.topic_id == topic_id
    ).first()

    if not tech_point:
        raise HTTPException(status_code=404, detail="Tech point not found")

    if data.name is not None:
        tech_point.name = data.name
    if data.description is not None:
        tech_point.description = data.description
    if data.hypothesis is not None:
        tech_point.hypothesis = data.hypothesis
    if data.approach is not None:
        tech_point.approach = data.approach
    if data.conclusion is not None:
        tech_point.conclusion = data.conclusion
    if data.status is not None:
        tech_point.status = data.status

    db.commit()
    db.refresh(tech_point)

    return {
        "id": tech_point.id,
        "name": tech_point.name,
        "description": tech_point.description,
        "hypothesis": tech_point.hypothesis,
        "approach": tech_point.approach,
        "conclusion": tech_point.conclusion,
        "status": tech_point.status,
        "firstAuthorId": tech_point.first_author_id,
        "firstAuthorName": tech_point.first_author.name if tech_point.first_author else None,
        "createdAt": tech_point.created_at.isoformat() if tech_point.created_at else None,
    }


@router.delete("/{topic_id}/tech-points/{point_id}")
def delete_topic_tech_point(
    topic_id: int,
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ..models.stage_instance import TechPoint

    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot delete tech points")

    tech_point = db.query(TechPoint).filter(
        TechPoint.id == point_id,
        TechPoint.topic_id == topic_id
    ).first()

    if not tech_point:
        raise HTTPException(status_code=404, detail="Tech point not found")

    db.delete(tech_point)
    db.commit()

    return {"message": "Tech point deleted"}

