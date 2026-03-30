from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.template import StageTemplate, StageTemplateStage
from ..schemas.template import (
    StageTemplateCreate, StageTemplateUpdate, StageTemplateResponse
)
from ..services.auth import get_current_user, get_current_admin

router = APIRouter()


@router.get("", response_model=List[StageTemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    templates = db.query(StageTemplate).options(
        joinedload(StageTemplate.stages)
    ).order_by(StageTemplate.name).all()
    return templates


@router.get("/{template_id}", response_model=StageTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = db.query(StageTemplate).options(
        joinedload(StageTemplate.stages)
    ).filter(StageTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("", response_model=StageTemplateResponse)
def create_template(
    template_data: StageTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    template = StageTemplate(
        name=template_data.name,
        description=template_data.description
    )
    db.add(template)
    db.flush()

    # Create stages
    for i, stage_data in enumerate(template_data.stages):
        stage = StageTemplateStage(
            template_id=template.id,
            name=stage_data.name,
            description=stage_data.description,
            order=stage_data.order if stage_data.order else i,
            is_terminal=stage_data.is_terminal,
            allow_result=stage_data.allow_result,
            require_artifact=stage_data.require_artifact,
            require_review=stage_data.require_review
        )
        db.add(stage)

    db.commit()

    return get_template(template.id, db, current_user)


@router.put("/{template_id}", response_model=StageTemplateResponse)
def update_template(
    template_id: int,
    template_data: StageTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    template = db.query(StageTemplate).filter(StageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template_data.name is not None:
        template.name = template_data.name
    if template_data.description is not None:
        template.description = template_data.description

    # Update stages if provided
    if template_data.stages is not None:
        # Get existing stage IDs
        existing_stage_ids = [s.id for s in db.query(StageTemplateStage).filter(
            StageTemplateStage.template_id == template_id
        ).all()]

        if existing_stage_ids:
            from ..models.topic import Topic, TopicStageState
            from ..models.stage_instance import TopicStageInstance

            # Clear current_stage_id from topics that reference these stages
            db.query(Topic).filter(
                Topic.current_stage_id.in_(existing_stage_ids)
            ).update({Topic.current_stage_id: None}, synchronize_session=False)

            # Delete topic_stage_states that reference these stages
            db.query(TopicStageState).filter(
                TopicStageState.stage_id.in_(existing_stage_ids)
            ).delete(synchronize_session=False)

            # Clear template_stage_id from stage instances that reference these stages
            db.query(TopicStageInstance).filter(
                TopicStageInstance.template_stage_id.in_(existing_stage_ids)
            ).update({TopicStageInstance.template_stage_id: None}, synchronize_session=False)

        # Delete existing stages
        db.query(StageTemplateStage).filter(
            StageTemplateStage.template_id == template_id
        ).delete(synchronize_session=False)

        # Create new stages
        for i, stage_data in enumerate(template_data.stages):
            stage = StageTemplateStage(
                template_id=template.id,
                name=stage_data.name,
                description=stage_data.description,
                order=stage_data.order if stage_data.order else i,
                is_terminal=stage_data.is_terminal,
                allow_result=stage_data.allow_result,
                require_artifact=stage_data.require_artifact,
                require_review=stage_data.require_review
            )
            db.add(stage)

    db.commit()

    return get_template(template.id, db, current_user)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    template = db.query(StageTemplate).filter(StageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check if template is in use
    from ..models.topic import Topic
    topics_count = db.query(Topic).filter(Topic.template_id == template_id).count()
    if topics_count > 0:
        raise HTTPException(status_code=400, detail=f"Template is used by {topics_count} topics")

    # Delete stages first
    db.query(StageTemplateStage).filter(
        StageTemplateStage.template_id == template_id
    ).delete()

    db.delete(template)
    db.commit()

    return {"message": "Template deleted"}
