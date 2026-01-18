from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from math import ceil
from ..database import get_db
from ..models.user import User, UserRole
from ..models.topic import Topic, TopicStageState, StageStatus
from ..models.template import StageTemplate, StageTemplateStage
from ..models.artifact import Artifact
from ..models.review import ReviewComment
from ..models.audit import AuditAction
from ..schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse,
    ArtifactCreate, ArtifactResponse,
    ReviewCreate, ReviewResponse
)
from ..schemas.common import PaginatedResponse
from ..services.auth import get_current_user, get_current_admin
from ..services.audit import AuditService

router = APIRouter()


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
        joinedload(Topic.bindings)
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
        query = query.filter(Topic.dri_id == dri_id)

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
    topic = db.query(Topic).options(
        joinedload(Topic.dri),
        joinedload(Topic.requester_user),
        joinedload(Topic.template).joinedload(StageTemplate.stages),
        joinedload(Topic.stage_states).joinedload(TopicStageState.stage),
        joinedload(Topic.artifacts).joinedload(Artifact.created_by),
        joinedload(Topic.reviews).joinedload(ReviewComment.created_by),
        joinedload(Topic.bindings)
    ).filter(Topic.id == topic_id).first()

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

    # Validate DRI is not EXTERNAL or CUSTOMER
    dri = db.query(User).filter(User.id == topic_data.dri_id).first()
    if not dri:
        raise HTTPException(status_code=400, detail="DRI not found")
    if dri.role == UserRole.EXTERNAL:
        raise HTTPException(status_code=400, detail="EXTERNAL users cannot be DRI")
    if dri.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=400, detail="CUSTOMER users cannot be DRI")

    # Validate requester
    requester_name = topic_data.requester_name
    if topic_data.requester_user_id is not None:
        requester_user = db.query(User).filter(User.id == topic_data.requester_user_id).first()
        if not requester_user:
            raise HTTPException(status_code=400, detail="Requester user not found")
        if requester_user.role != UserRole.CUSTOMER:
            raise HTTPException(status_code=400, detail="Only CUSTOMER users can be requester")
        # Auto-fill requester_name from user name when requester_user_id is provided
        requester_name = requester_user.name
    else:
        # If requester_user_id is None, requester_name must have value
        if not topic_data.requester_name or not topic_data.requester_name.strip():
            raise HTTPException(status_code=400, detail="requester_name is required when requester_user_id is not provided")
        requester_name = topic_data.requester_name.strip()

    # Validate template exists
    template = db.query(StageTemplate).options(
        joinedload(StageTemplate.stages)
    ).filter(StageTemplate.id == topic_data.template_id).first()
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")

    # Create topic
    topic = Topic(
        title=topic_data.title,
        description=topic_data.description,
        type=topic_data.type,
        urgency=topic_data.urgency,
        dri_id=topic_data.dri_id,
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

    db.commit()
    db.refresh(topic)

    AuditService.log(db, AuditAction.TOPIC_CREATE, "Topic", topic.id, current_user,
                     new_value={"title": topic.title, "type": topic.type.value})

    return get_topic(topic.id, db, current_user)


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

    # Check permissions
    if current_user.role != UserRole.ADMIN and topic.dri_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    old_values = {}

    # Handle DRI change
    if topic_data.dri_id is not None and topic_data.dri_id != topic.dri_id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admin can change DRI")

        new_dri = db.query(User).filter(User.id == topic_data.dri_id).first()
        if not new_dri:
            raise HTTPException(status_code=400, detail="New DRI not found")
        if new_dri.role == UserRole.EXTERNAL:
            raise HTTPException(status_code=400, detail="EXTERNAL users cannot be DRI")
        if new_dri.role == UserRole.CUSTOMER:
            raise HTTPException(status_code=400, detail="CUSTOMER users cannot be DRI")

        old_values["dri_id"] = topic.dri_id
        topic.dri_id = topic_data.dri_id

        AuditService.log(db, AuditAction.DRI_CHANGE, "Topic", topic.id, current_user,
                         old_value={"dri_id": old_values["dri_id"]},
                         new_value={"dri_id": topic.dri_id})

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

    return get_topic(topic.id, db, current_user)


@router.post("/{topic_id}/stages/{stage_id}/advance", response_model=TopicResponse)
def advance_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # CUSTOMER cannot advance stage
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot advance stage")
    
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions
    if current_user.role != UserRole.ADMIN and topic.dri_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Mark current stage as done
    current_state = db.query(TopicStageState).filter(
        TopicStageState.topic_id == topic_id,
        TopicStageState.stage_id == topic.current_stage_id
    ).first()
    if current_state:
        current_state.status = StageStatus.DONE

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
                     old_value={"stage_id": old_stage_id},
                     new_value={"stage_id": stage_id})

    return get_topic(topic.id, db, current_user)


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

    # Reviews are append-only
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
