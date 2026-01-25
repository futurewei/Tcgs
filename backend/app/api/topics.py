from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func
from typing import Optional, List
from math import ceil
from datetime import datetime
from pydantic import BaseModel
from ..database import get_db
from ..models.user import User, UserRole
from ..models.topic import Topic, TopicStageState, StageStatus, TopicType
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


def get_topic_with_relations(db: Session, topic_id: int):
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
    检查用户是否可以查看所有课题
    ADMIN, MEMBER, REVIEWER 可以查看所有课题
    CUSTOMER, EXTERNAL 只能查看关联的课题
    """
    return user.role in [UserRole.ADMIN, UserRole.MEMBER, UserRole.REVIEWER]


def filter_topics_by_user_access(query, user: User, db: Session):
    """
    根据用户权限过滤课题
    
    CUSTOMER: 只能看到自己作为需求方的课题
    EXTERNAL: 只能看到自己被分配到的课题（通过 Binding -> CapacitySlot -> user_id）
    """
    if user.role == UserRole.CUSTOMER:
        # CUSTOMER 只能看到自己作为需求方的课题
        query = query.filter(Topic.requester_user_id == user.id)
    elif user.role == UserRole.EXTERNAL:
        # EXTERNAL 只能看到自己被分配到的课题
        # 通过 Binding -> CapacitySlot -> user_id 关联
        subquery = db.query(Binding.topic_id).join(CapacitySlot).filter(
            CapacitySlot.user_id == user.id
        ).distinct()
        query = query.filter(Topic.id.in_(subquery))
    # ADMIN, MEMBER, REVIEWER 不需要过滤
    return query


def check_topic_access(topic: Topic, user: User, db: Session) -> bool:
    """
    检查用户是否有权限访问特定课题
    """
    if user_can_view_all_topics(user):
        return True
    
    if user.role == UserRole.CUSTOMER:
        return topic.requester_user_id == user.id
    elif user.role == UserRole.EXTERNAL:
        # 检查是否被分配到此课题
        binding = db.query(Binding).join(CapacitySlot).filter(
            Binding.topic_id == topic.id,
            CapacitySlot.user_id == user.id
        ).first()
        return binding is not None
    
    return False


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
        joinedload(Topic.bindings).joinedload(Binding.slot)
    )

    # 根据用户角色过滤可见课题
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
        # Filter by DRI binding's slot user
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
    topic = get_topic_with_relations(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # 检查访问权限
    if not check_topic_access(topic, current_user, db):
        raise HTTPException(status_code=403, detail="You don't have permission to view this topic")
    
    return topic


@router.post("", response_model=TopicResponse)
def create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # CUSTOMER cannot create topics
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create topics")
    
    # Only ADMIN can create topics
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
            raise HTTPException(status_code=400, detail="requester_name is required when requester_user_id is not provided")
        requester_name = topic_data.requester_name.strip()

    # Validate template exists
    template = db.query(StageTemplate).options(
        joinedload(StageTemplate.stages)
    ).filter(StageTemplate.id == topic_data.template_id).first()
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")

    # Create topic (without dri_id initially)
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

    # Create stage states and set first stage as active (旧逻辑，保留兼容)
    # 只为演进课题创建旧的 stage states
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
    # 不确定性课题：不自动创建阶段，让用户自己添加
    # 演进课题：按模板创建阶段
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
    
    # Set current stage instance
    if first_instance:
        topic.current_stage_instance_id = first_instance.id

    # If initial DRI slot is provided, create the first binding as DRI
    if topic_data.initial_dri_slot_id:
        slot = db.query(CapacitySlot).filter(CapacitySlot.id == topic_data.initial_dri_slot_id).first()
        if not slot:
            raise HTTPException(status_code=400, detail="Initial DRI slot not found")
        
        binding = Binding(
            topic_id=topic.id,
            slot_id=topic_data.initial_dri_slot_id,
            percentage=topic_data.initial_dri_percentage,
            is_dri=True
        )
        db.add(binding)
        
        # Also set legacy dri_id for backward compatibility
        if slot.user_id:
            topic.dri_id = slot.user_id

    db.commit()
    db.refresh(topic)

    AuditService.log(db, AuditAction.TOPIC_CREATE, "Topic", topic.id, current_user,
                     new_value={"title": topic.title, "type": topic.type.value})

    return get_topic_with_relations(db, topic.id)


@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # CUSTOMER cannot update topics
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot update topics")
    
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions - admin or DRI can update
    dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    is_dri = dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id
    
    if current_user.role != UserRole.ADMIN and not is_dri:
        raise HTTPException(status_code=403, detail="Not authorized")

    old_values = {}

    # Handle result change
    if topic_data.result is not None and topic_data.result != topic.result:
        old_values["result"] = topic.result.value
        topic.result = topic_data.result

        AuditService.log(db, AuditAction.RESULT_CHANGE, "Topic", topic.id, current_user,
                         old_value={"result": old_values["result"]},
                         new_value={"result": topic.result.value})

    # Other updates
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

    return get_topic_with_relations(db, topic.id)


@router.post("/{topic_id}/stages/{stage_id}/advance", response_model=TopicResponse)
def advance_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advance to the next stage"""
    # CUSTOMER cannot advance stage
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot advance stage")
    
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions
    dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    is_dri = dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id
    
    if current_user.role != UserRole.ADMIN and not is_dri:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Mark current stage as done
    current_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == topic.current_stage_id
    ).first()
    if current_state:
        current_state.status = StageStatus.DONE
        current_state.completed_at = datetime.utcnow()

    # Activate new stage
    new_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == stage_id
    ).first()
    if new_state:
        new_state.status = StageStatus.ACTIVE

    old_stage_id = topic.current_stage_id
    topic.current_stage_id = stage_id

    db.commit()

    AuditService.log(db, AuditAction.STAGE_CHANGE, "Topic", topic.id, current_user,
                     old_value={"stage_id": old_stage_id, "action": "advance"},
                     new_value={"stage_id": stage_id})

    return get_topic_with_relations(db, topic.id)


@router.post("/{topic_id}/stages/{stage_id}/backward", response_model=TopicResponse)
def backward_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Go back to a previous stage"""
    # CUSTOMER cannot change stage
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot change stage")
    
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot),
        joinedload(Topic.template).joinedload(StageTemplate.stages)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions
    dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    is_dri = dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id
    
    if current_user.role != UserRole.ADMIN and not is_dri:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate target stage exists and is before current stage
    target_stage = next((s for s in topic.template.stages if s.id == stage_id), None)
    if not target_stage:
        raise HTTPException(status_code=400, detail="Target stage not found")
    
    current_stage = next((s for s in topic.template.stages if s.id == topic.current_stage_id), None)
    if current_stage and target_stage.order >= current_stage.order:
        raise HTTPException(status_code=400, detail="Can only go backward to previous stages")

    # Mark current stage as pending (revert from active/done)
    current_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == topic.current_stage_id
    ).first()
    if current_state:
        current_state.status = StageStatus.PENDING
        current_state.completed_at = None

    # Also mark all stages after target as pending
    for stage in topic.template.stages:
        if stage.order > target_stage.order:
            state = db.query(TopicStageState).filter(
                TopicStageState.topic_id == topic_id,
                TopicStageState.stage_id == stage.id
            ).first()
            if state:
                state.status = StageStatus.PENDING
                state.completed_at = None

    # Set target stage as active
    target_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == stage_id
    ).first()
    if target_state:
        target_state.status = StageStatus.ACTIVE
        target_state.completed_at = None

    old_stage_id = topic.current_stage_id
    topic.current_stage_id = stage_id

    db.commit()

    AuditService.log(db, AuditAction.STAGE_CHANGE, "Topic", topic.id, current_user,
                     old_value={"stage_id": old_stage_id, "action": "backward"},
                     new_value={"stage_id": stage_id})

    return get_topic_with_relations(db, topic.id)


@router.post("/{topic_id}/change-dri", response_model=TopicResponse)
def change_dri(
    topic_id: int,
    request: ChangeDRIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change the DRI of a topic to a different slot/person
    
    Permission: Only ADMIN or current DRI can change DRI
    """
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Find current DRI
    old_dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    old_dri_name = None
    old_dri_user_id = None
    if old_dri_binding and old_dri_binding.slot:
        old_dri_name = old_dri_binding.slot.name
        old_dri_user_id = old_dri_binding.slot.user_id

    # Permission check: Only ADMIN or current DRI can change DRI
    is_admin = current_user.role == UserRole.ADMIN
    is_current_dri = old_dri_user_id and old_dri_user_id == current_user.id
    
    if not is_admin and not is_current_dri:
        raise HTTPException(
            status_code=403, 
            detail="只有管理员或当前 DRI 本人可以更换负责人"
        )

    # Validate new DRI slot exists
    new_slot = db.query(CapacitySlot).options(
        joinedload(CapacitySlot.user)
    ).filter(CapacitySlot.id == request.new_dri_slot_id).first()
    if not new_slot:
        raise HTTPException(status_code=400, detail="New DRI slot not found")

    # Check if new slot already has a binding
    existing_binding = next((b for b in topic.bindings if b.slot_id == request.new_dri_slot_id), None)

    if existing_binding:
        # Move DRI flag to existing binding
        if old_dri_binding and old_dri_binding.id != existing_binding.id:
            old_dri_binding.is_dri = False
        existing_binding.is_dri = True
    else:
        # Create new binding with DRI flag
        if old_dri_binding:
            old_dri_binding.is_dri = False
        
        new_binding = Binding(
            topic_id=topic_id,
            slot_id=request.new_dri_slot_id,
            percentage=25,  # Default percentage
            is_dri=True
        )
        db.add(new_binding)

    # Update legacy dri_id for backward compatibility
    if new_slot.user_id:
        topic.dri_id = new_slot.user_id

    db.commit()
    db.refresh(topic)

    try:
        AuditService.log(db, AuditAction.DRI_CHANGE, "Topic", topic.id, current_user,
                         old_value={"dri_slot": old_dri_name},
                         new_value={"dri_slot": new_slot.name})
    except Exception as e:
        # Audit log failure should not fail the main operation
        print(f"Audit log failed: {e}")

    return get_topic_with_relations(db, topic.id)


# Artifacts
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
    # CUSTOMER cannot create artifacts
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


# Reviews
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
    # CUSTOMER cannot create reviews
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


# Stage Deliverables
@router.get("/{topic_id}/deliverables", response_model=List[StageDeliverableResponse])
def list_deliverables(
    topic_id: int,
    stage_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all deliverables for a topic, optionally filtered by stage"""
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
    """Create a new deliverable for a stage"""
    # CUSTOMER cannot create deliverables
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create deliverables")
    
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions - DRI or admin can add deliverables
    dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    is_dri = dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id
    
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
    """Delete a deliverable"""
    # CUSTOMER cannot delete deliverables
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
    
    # Check permissions - DRI, creator, or admin can delete
    dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    is_dri = dri_binding and dri_binding.slot and dri_binding.slot.user_id == current_user.id
    
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
    """获取课题关联的所有人员（用于选择提出人）"""
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user)
    ).filter(Topic.id == topic_id).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    members = []
    for binding in topic.bindings:
        if binding.slot:
            user = binding.slot.user
            member = {
                "slotId": binding.slot.id,
                "slotName": binding.slot.name,
                "slotType": binding.slot.type.value if binding.slot.type else None,
                "userId": user.id if user else None,
                "userName": binding.slot.name,  # 使用 Slot 名字（如 Alice Chen）
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
    """获取课题级别的技术点/算法思想列表"""
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
    """创建课题级别的技术点/算法思想"""
    from ..models.stage_instance import TechPoint
    
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create tech points")
    
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # 验证提出人存在
    author = db.query(User).filter(User.id == data.first_author_id).first()
    if not author:
        raise HTTPException(status_code=400, detail="First author not found")
    
    # 获取最大 order
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
    """更新课题级别的技术点/算法思想"""
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
    """删除课题级别的技术点/算法思想"""
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
