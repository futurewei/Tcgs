from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from typing import List
from math import ceil
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User, UserRole
from ..models.topic import Topic, TopicResult, TopicType
from ..models.capacity import CapacitySlot, Binding, SlotType
from ..models.audit import AuditLog
from ..schemas.common import PaginatedResponse
from ..services.auth import get_current_user, get_current_admin
from pydantic import BaseModel

router = APIRouter()


def to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True


class DashboardKPI(CamelModel):
    total_topics: int
    open_topics: int
    success_topics: int
    unsolvable_topics: int
    avg_cycle_days: float
    uncertainty_count: int
    evolution_count: int


class ThroughputData(CamelModel):
    month: str
    new_topics: int
    closed_topics: int
    uncertainty: int
    evolution: int


class PersonLoadData(CamelModel):
    user_id: int
    user_name: str
    dri_topics: int
    collaboration_topics: int
    total_percentage: int


class ExternalCollabData(CamelModel):
    user_id: int
    user_name: str
    topic_count: int
    stage_distribution: dict


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int
    old_value: str | None
    new_value: str | None
    user_id: int
    user: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/kpi", response_model=DashboardKPI)
def get_kpi(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total = db.query(Topic).count()
    open_count = db.query(Topic).filter(Topic.result == TopicResult.OPEN).count()
    success_count = db.query(Topic).filter(Topic.result == TopicResult.SUCCESS).count()
    unsolvable_count = db.query(Topic).filter(Topic.result == TopicResult.UNSOLVABLE).count()
    uncertainty_count = db.query(Topic).filter(Topic.type == TopicType.UNCERTAINTY).count()
    evolution_count = db.query(Topic).filter(Topic.type == TopicType.EVOLUTION).count()

    # Calculate average cycle for closed topics
    closed_topics = db.query(Topic).filter(
        Topic.result.in_([TopicResult.SUCCESS, TopicResult.UNSOLVABLE])
    ).all()

    if closed_topics:
        total_days = sum(
            (t.updated_at - t.created_at).days for t in closed_topics
        )
        avg_cycle = total_days / len(closed_topics)
    else:
        avg_cycle = 0.0

    return DashboardKPI(
        total_topics=total,
        open_topics=open_count,
        success_topics=success_count,
        unsolvable_topics=unsolvable_count,
        avg_cycle_days=avg_cycle,
        uncertainty_count=uncertainty_count,
        evolution_count=evolution_count
    )


@router.get("/throughput", response_model=List[ThroughputData])
def get_throughput(
    months: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = []
    now = datetime.utcnow()

    for i in range(months - 1, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = now

        new_topics = db.query(Topic).filter(
            Topic.created_at >= month_start,
            Topic.created_at < month_end
        ).count()

        closed_topics = db.query(Topic).filter(
            Topic.result.in_([TopicResult.SUCCESS, TopicResult.UNSOLVABLE]),
            Topic.updated_at >= month_start,
            Topic.updated_at < month_end
        ).count()

        uncertainty = db.query(Topic).filter(
            Topic.type == TopicType.UNCERTAINTY,
            Topic.created_at >= month_start,
            Topic.created_at < month_end
        ).count()

        evolution = db.query(Topic).filter(
            Topic.type == TopicType.EVOLUTION,
            Topic.created_at >= month_start,
            Topic.created_at < month_end
        ).count()

        result.append(ThroughputData(
            month=month_start.strftime("%Y-%m"),
            new_topics=new_topics,
            closed_topics=closed_topics,
            uncertainty=uncertainty,
            evolution=evolution
        ))

    return result


@router.get("/person-load", response_model=List[PersonLoadData])
def get_person_load(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取算法团队负载 - 按用户去重"""
    # 获取所有 MEMBER 和 REVIEWER 用户
    algo_users = db.query(User).filter(
        User.role.in_([UserRole.MEMBER, UserRole.REVIEWER])
    ).all()

    result = []
    for user in algo_users:
        # Count DRI topics
        dri_topics = db.query(Topic).filter(
            Topic.dri_id == user.id,
            Topic.result == TopicResult.OPEN
        ).count()

        # 获取用户的所有 bindings（通过 slot）
        user_slots = db.query(CapacitySlot).filter(
            CapacitySlot.user_id == user.id
        ).all()
        
        all_bindings = []
        for slot in user_slots:
            bindings = db.query(Binding).filter(Binding.slot_id == slot.id).all()
            all_bindings.extend(bindings)

        # Count collaboration (unique topics)
        collab_topic_ids = set(b.topic_id for b in all_bindings)
        collab_topics = len(collab_topic_ids)

        # Total percentage
        total_pct = sum(b.percentage for b in all_bindings)

        result.append(PersonLoadData(
            user_id=user.id,
            user_name=user.name,
            dri_topics=dri_topics,
            collaboration_topics=collab_topics,
            total_percentage=total_pct
        ))

    return result


@router.get("/external-collab", response_model=List[ExternalCollabData])
def get_external_collab(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取外部协作数据 - 按用户去重"""
    # 获取所有 EXTERNAL 用户
    external_users = db.query(User).filter(
        User.role == UserRole.EXTERNAL
    ).all()

    result = []
    for user in external_users:
        # 获取用户的所有 bindings（通过 slot）
        user_slots = db.query(CapacitySlot).filter(
            CapacitySlot.user_id == user.id
        ).all()
        
        all_bindings = []
        for slot in user_slots:
            bindings = db.query(Binding).options(
                joinedload(Binding.topic)
            ).filter(Binding.slot_id == slot.id).all()
            all_bindings.extend(bindings)

        # Unique topic count
        topic_ids = set(b.topic_id for b in all_bindings)
        topic_count = len(topic_ids)

        # Stage distribution
        stage_dist = {}
        for binding in all_bindings:
            if binding.topic and binding.topic.current_stage:
                stage_name = binding.topic.current_stage.name
                stage_dist[stage_name] = stage_dist.get(stage_name, 0) + 1

        result.append(ExternalCollabData(
            user_id=user.id,
            user_name=user.name,
            topic_count=topic_count,
            stage_distribution=stage_dist
        ))

    return result


@router.get("/audit-logs")
def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    total = db.query(AuditLog).count()
    logs = db.query(AuditLog).options(
        joinedload(AuditLog.user)
    ).order_by(AuditLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "action": log.action.value,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "user_id": log.user_id,
            "user": {
                "id": log.user.id,
                "name": log.user.name,
                "email": log.user.email,
                "role": log.user.role.value
            } if log.user else None,
            "created_at": log.created_at.isoformat()
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total > 0 else 1
    }
