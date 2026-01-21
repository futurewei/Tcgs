from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func
from typing import Optional, List
from math import ceil
from datetime import datetime
from ..database import get_db
from ..models.user import User, UserRole
from ..models.topic import Topic, TopicStageState, StageStatus
from ..models.template import StageTemplate, StageTemplateStage
from ..models.artifact import Artifact
from ..models.review import ReviewComment
from ..models.deliverable import StageDeliverable
from ..models.capacity import Binding, CapacitySlot
from ..models.audit import AuditAction
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
        joinedload(Topic.artifacts).joinedload(Artifact.created_by),
        joinedload(Topic.reviews).joinedload(ReviewComment.created_by),
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user),
        joinedload(Topic.deliverables).joinedload(StageDeliverable.created_by)
    ).filter(Topic.id == topic_id).first()


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
        query = query.join(Binding).join(CapacitySlot).filter(
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
        type=topic_data.type,
        urgency=topic_data.urgency,
        template_id=topic_data.template_id,
        requester_name=requester_name,
        requester_user_id=topic_data.requester_user_id,
    )
    db.add(topic)
    db.flush()

    # Create stage states and set first stage as active
    for i, stage in enumerate(template.stages):
        state = TopicStageState(
            topic_id=topic.id,
            stage_id=stage.id,
            status=StageStatus.ACTIVE if i == 0 else StageStatus.PENDING
        )
        db.add(state)
        if i == 0:
            topic.current_stage_id = stage.id

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
    current_user: User = Depends(get_current_admin)
):
    """Change the DRI of a topic to a different slot/person"""
    topic = db.query(Topic).options(
        joinedload(Topic.bindings).joinedload(Binding.slot).joinedload(CapacitySlot.user)
    ).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Validate new DRI slot exists
    new_slot = db.query(CapacitySlot).options(
        joinedload(CapacitySlot.user)
    ).filter(CapacitySlot.id == request.new_dri_slot_id).first()
    if not new_slot:
        raise HTTPException(status_code=400, detail="New DRI slot not found")

    # Find old DRI
    old_dri_binding = next((b for b in topic.bindings if b.is_dri), None)
    old_dri_name = None
    if old_dri_binding and old_dri_binding.slot:
        old_dri_name = old_dri_binding.slot.name

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

    AuditService.log(db, AuditAction.DRI_CHANGE, "Topic", topic.id, current_user,
                     old_value={"dri_slot": old_dri_name},
                     new_value={"dri_slot": new_slot.name})

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
