"""
Core Ideas API - 算法思想演进管理

支持：
- 创建/更新/删除 Core Idea
- 关联阶段
- 状态流转
- 时间线查询
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models import User, Topic, TopicStageInstance
from ..models.core_idea import CoreIdea, IdeaType, IdeaStatus
from ..services.auth import get_current_user

router = APIRouter(prefix="/topics/{topic_id}/ideas", tags=["core-ideas"])


# ============ Schemas ============

class CoreIdeaCreate(BaseModel):
    title: str
    idea_type: Optional[str] = "algorithm_hypothesis"  # 默认类型
    proposer_id: int
    proposer_name: Optional[str] = None  # 提出人显示名（Slot 名字）
    idea_body: Optional[str] = None
    motivation: Optional[str] = None
    evidence: Optional[str] = None
    impact: Optional[str] = None
    related_stage_ids: Optional[List[int]] = None


class CoreIdeaUpdate(BaseModel):
    title: Optional[str] = None
    idea_type: Optional[str] = None
    status: Optional[str] = None
    idea_body: Optional[str] = None
    motivation: Optional[str] = None
    evidence: Optional[str] = None
    impact: Optional[str] = None
    related_stage_ids: Optional[List[int]] = None
    superseded_by_id: Optional[int] = None


class CoreIdeaResponse(BaseModel):
    id: int
    topicId: int
    title: str
    ideaType: str
    status: str
    proposerId: int
    proposerName: str
    ideaBody: Optional[str]
    motivation: Optional[str]
    evidence: Optional[str]
    impact: Optional[str]
    supersededById: Optional[int]
    relatedStageIds: List[int]
    relatedStageNames: List[str]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


def idea_to_response(idea: CoreIdea) -> dict:
    """Convert CoreIdea to response dict"""
    return {
        "id": idea.id,
        "topicId": idea.topic_id,
        "title": idea.title,
        "ideaType": idea.idea_type,  # 已经是字符串
        "status": idea.status,  # 已经是字符串
        "proposerId": idea.proposer_id,
        "proposerName": idea.proposer_name or (idea.proposer.name if idea.proposer else "Unknown"),
        "ideaBody": idea.idea_body,
        "motivation": idea.motivation,
        "evidence": idea.evidence,
        "impact": idea.impact,
        "supersededById": idea.superseded_by_id,
        "relatedStageIds": [s.id for s in idea.related_stages],
        "relatedStageNames": [s.name for s in idea.related_stages],
        "createdAt": idea.created_at,
        "updatedAt": idea.updated_at,
    }


# ============ Routes ============

@router.get("")
def list_ideas(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课题的所有 Core Ideas"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    ideas = db.query(CoreIdea).options(
        joinedload(CoreIdea.proposer),
        joinedload(CoreIdea.related_stages)
    ).filter(CoreIdea.topic_id == topic_id).order_by(CoreIdea.created_at.desc()).all()
    
    return [idea_to_response(idea) for idea in ideas]


@router.post("")
def create_idea(
    topic_id: int,
    data: CoreIdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建 Core Idea"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # 验证提出人
    proposer = db.query(User).filter(User.id == data.proposer_id).first()
    if not proposer:
        raise HTTPException(status_code=400, detail="Proposer not found")
    
    # 验证 idea_type，如果为空则使用默认值
    idea_type_str = data.idea_type or IdeaType.ALGORITHM_HYPOTHESIS
    # 验证是否是有效的类型值
    valid_types = [
        IdeaType.PROBLEM_REDEFINE, IdeaType.ALGORITHM_HYPOTHESIS,
        IdeaType.MODEL_STRUCTURE, IdeaType.PARAMETER_STRATEGY,
        IdeaType.DATA_PERSPECTIVE, IdeaType.ENGINEERING_TRADEOFF
    ]
    if idea_type_str not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid idea type: {idea_type_str}")
    
    idea = CoreIdea(
        topic_id=topic_id,
        title=data.title,
        idea_type=idea_type_str,
        proposer_id=data.proposer_id,
        proposer_name=data.proposer_name,  # 存储提出人显示名
        idea_body=data.idea_body,
        motivation=data.motivation,
        evidence=data.evidence,
        impact=data.impact,
    )
    db.add(idea)
    db.flush()
    
    # 关联阶段（可选）
    if data.related_stage_ids:
        stages = db.query(TopicStageInstance).filter(
            TopicStageInstance.id.in_(data.related_stage_ids),
            TopicStageInstance.topic_id == topic_id
        ).all()
        idea.related_stages = stages
    
    db.commit()
    db.refresh(idea)
    
    # 重新加载关系
    idea = db.query(CoreIdea).options(
        joinedload(CoreIdea.proposer),
        joinedload(CoreIdea.related_stages)
    ).filter(CoreIdea.id == idea.id).first()
    
    return idea_to_response(idea)


@router.get("/{idea_id}")
def get_idea(
    topic_id: int,
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个 Core Idea"""
    idea = db.query(CoreIdea).options(
        joinedload(CoreIdea.proposer),
        joinedload(CoreIdea.related_stages)
    ).filter(CoreIdea.id == idea_id, CoreIdea.topic_id == topic_id).first()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return idea_to_response(idea)


@router.put("/{idea_id}")
def update_idea(
    topic_id: int,
    idea_id: int,
    data: CoreIdeaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 Core Idea"""
    idea = db.query(CoreIdea).filter(
        CoreIdea.id == idea_id, 
        CoreIdea.topic_id == topic_id
    ).first()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    if data.title is not None:
        idea.title = data.title
    if data.idea_type is not None:
        # IdeaType 是普通类，直接赋值字符串
        valid_types = [
            IdeaType.PROBLEM_REDEFINE, IdeaType.ALGORITHM_HYPOTHESIS,
            IdeaType.MODEL_STRUCTURE, IdeaType.PARAMETER_STRATEGY,
            IdeaType.DATA_PERSPECTIVE, IdeaType.ENGINEERING_TRADEOFF
        ]
        if data.idea_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid idea type: {data.idea_type}")
        idea.idea_type = data.idea_type
    if data.status is not None:
        # IdeaStatus 是普通类，直接赋值字符串
        valid_statuses = [
            IdeaStatus.HYPOTHESIZING, IdeaStatus.VERIFIED,
            IdeaStatus.REJECTED, IdeaStatus.SUPERSEDED
        ]
        if data.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {data.status}")
        idea.status = data.status
    if data.idea_body is not None:
        idea.idea_body = data.idea_body
    if data.motivation is not None:
        idea.motivation = data.motivation
    if data.evidence is not None:
        idea.evidence = data.evidence
    if data.impact is not None:
        idea.impact = data.impact
    if data.superseded_by_id is not None:
        idea.superseded_by_id = data.superseded_by_id
        idea.status = IdeaStatus.SUPERSEDED
    
    # 更新关联阶段
    if data.related_stage_ids is not None:
        stages = db.query(TopicStageInstance).filter(
            TopicStageInstance.id.in_(data.related_stage_ids),
            TopicStageInstance.topic_id == topic_id
        ).all()
        idea.related_stages = stages
    
    db.commit()
    
    # 重新加载
    idea = db.query(CoreIdea).options(
        joinedload(CoreIdea.proposer),
        joinedload(CoreIdea.related_stages)
    ).filter(CoreIdea.id == idea.id).first()
    
    return idea_to_response(idea)


@router.delete("/{idea_id}")
def delete_idea(
    topic_id: int,
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 Core Idea"""
    idea = db.query(CoreIdea).filter(
        CoreIdea.id == idea_id, 
        CoreIdea.topic_id == topic_id
    ).first()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    db.delete(idea)
    db.commit()
    
    return {"message": "Idea deleted"}


# ============ 时间线视图 ============

@router.get("/timeline")
def get_ideas_timeline(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Core Ideas 时间线视图"""
    ideas = db.query(CoreIdea).options(
        joinedload(CoreIdea.proposer),
        joinedload(CoreIdea.related_stages)
    ).filter(CoreIdea.topic_id == topic_id).order_by(CoreIdea.created_at.asc()).all()
    
    return [idea_to_response(idea) for idea in ideas]
