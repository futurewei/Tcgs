"""
Risk API - 风险/阻塞管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from ..database import get_db
from ..models.user import User
from ..models.stage_instance import TopicRisk, RiskLevel
from ..services.auth import get_current_user

router = APIRouter()


class RiskCreate(BaseModel):
    topic_id: int
    stage_instance_id: Optional[int] = None
    level: str = "yellow"  # red, yellow, green
    blocker_type: str
    blocker_name: Optional[str] = None
    description: str
    expected_resolve_date: Optional[datetime] = None
    owner_id: Optional[int] = None


class RiskUpdate(BaseModel):
    level: Optional[str] = None
    blocker_type: Optional[str] = None
    blocker_name: Optional[str] = None
    description: Optional[str] = None
    expected_resolve_date: Optional[datetime] = None
    owner_id: Optional[int] = None
    is_resolved: Optional[bool] = None
    resolution_note: Optional[str] = None


class RiskResponse(BaseModel):
    id: int
    topic_id: int
    stage_instance_id: Optional[int] = None
    level: str
    blocker_type: str
    blocker_name: Optional[str] = None
    description: str
    expected_resolve_date: Optional[datetime] = None
    owner_id: Optional[int] = None
    owner: Optional[dict] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_by_id: Optional[int] = None
    created_by: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def serialize_user(user):
    if not user:
        return None
    return {"id": user.id, "name": user.name, "email": user.email}


@router.get("/topics/{topic_id}/risks", response_model=List[RiskResponse])
def list_risks(
    topic_id: int,
    include_resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课题的所有风险"""
    query = db.query(TopicRisk).options(
        joinedload(TopicRisk.owner),
        joinedload(TopicRisk.created_by)
    ).filter(TopicRisk.topic_id == topic_id)
    
    if not include_resolved:
        query = query.filter(TopicRisk.is_resolved == False)
    
    risks = query.order_by(
        TopicRisk.is_resolved,
        TopicRisk.level.desc(),
        TopicRisk.created_at.desc()
    ).all()
    
    return [
        {
            **r.__dict__,
            "level": r.level.value if r.level else "yellow",
            "owner": serialize_user(r.owner),
            "created_by": serialize_user(r.created_by),
        }
        for r in risks
    ]


@router.post("/risks", response_model=RiskResponse)
def create_risk(
    data: RiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建风险"""
    risk = TopicRisk(
        topic_id=data.topic_id,
        stage_instance_id=data.stage_instance_id,
        level=RiskLevel(data.level) if data.level else RiskLevel.YELLOW,
        blocker_type=data.blocker_type,
        blocker_name=data.blocker_name,
        description=data.description,
        expected_resolve_date=data.expected_resolve_date,
        owner_id=data.owner_id,
        created_by_id=current_user.id
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    risk = db.query(TopicRisk).options(
        joinedload(TopicRisk.owner),
        joinedload(TopicRisk.created_by)
    ).filter(TopicRisk.id == risk.id).first()
    
    return {
        **risk.__dict__,
        "level": risk.level.value if risk.level else "yellow",
        "owner": serialize_user(risk.owner),
        "created_by": serialize_user(risk.created_by),
    }


@router.put("/risks/{risk_id}", response_model=RiskResponse)
def update_risk(
    risk_id: int,
    data: RiskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新风险"""
    risk = db.query(TopicRisk).filter(TopicRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    if data.level is not None:
        risk.level = RiskLevel(data.level)
    if data.blocker_type is not None:
        risk.blocker_type = data.blocker_type
    if data.blocker_name is not None:
        risk.blocker_name = data.blocker_name
    if data.description is not None:
        risk.description = data.description
    if data.expected_resolve_date is not None:
        risk.expected_resolve_date = data.expected_resolve_date
    if data.owner_id is not None:
        risk.owner_id = data.owner_id
    if data.is_resolved is not None:
        risk.is_resolved = data.is_resolved
        if data.is_resolved:
            risk.resolved_at = datetime.utcnow()
    if data.resolution_note is not None:
        risk.resolution_note = data.resolution_note
    
    db.commit()
    db.refresh(risk)
    
    risk = db.query(TopicRisk).options(
        joinedload(TopicRisk.owner),
        joinedload(TopicRisk.created_by)
    ).filter(TopicRisk.id == risk.id).first()
    
    return {
        **risk.__dict__,
        "level": risk.level.value if risk.level else "yellow",
        "owner": serialize_user(risk.owner),
        "created_by": serialize_user(risk.created_by),
    }


@router.delete("/risks/{risk_id}")
def delete_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除风险"""
    risk = db.query(TopicRisk).filter(TopicRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    db.delete(risk)
    db.commit()
    return {"message": "Risk deleted"}
