"""
Profile API - 个人档案和贡献统计
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..database import get_db
from ..models.user import User
from ..models.topic import Topic, TopicResult
from ..models.capacity import CapacitySlot, Binding
from ..models.stage_instance import TopicStageInstance, TechPoint, TechPointContributor
from ..models.deliverable import StageDeliverable
from ..models.audit import AuditLog, AuditAction
from ..services.auth import get_current_user

router = APIRouter()


class ProfileStats(BaseModel):
    userId: int
    userName: str
    userEmail: str
    slotName: Optional[str] = None
    slotType: Optional[str] = None
    
    # 课题统计
    driTopicCount: int = 0
    participantTopicCount: int = 0
    completedTopicCount: int = 0
    inProgressTopicCount: int = 0
    unsolvableTopicCount: int = 0
    
    # 效率指标
    avgClosureDays: Optional[float] = None
    
    # 技术点统计
    firstAuthorTechPoints: int = 0
    contributorTechPoints: int = 0
    
    # 交付物统计
    deliverableCount: int = 0


class DeliverableItem(BaseModel):
    id: int
    name: str
    type: str
    category: str
    url: Optional[str] = None
    topicId: int
    topicTitle: str
    stageId: Optional[int] = None
    stageName: Optional[str] = None
    techPointId: Optional[int] = None
    techPointName: Optional[str] = None
    isFirstAuthor: bool = False
    createdAt: datetime
    

class TimelineEvent(BaseModel):
    id: int
    action: str
    actionLabel: str
    entityType: str
    entityId: int
    entityName: Optional[str] = None
    topicId: Optional[int] = None
    topicTitle: Optional[str] = None
    details: Optional[str] = None
    createdAt: datetime


def get_action_label(action: str) -> str:
    labels = {
        'topic_create': '创建课题',
        'topic_update': '更新课题',
        'topic_close': '关闭课题',
        'stage_create': '创建阶段',
        'stage_update': '更新阶段',
        'stage_complete': '完成阶段',
        'stage_delete': '删除阶段',
        'tech_point_create': '创建技术点',
        'tech_point_update': '更新技术点',
        'deliverable_create': '上传交付物',
        'deliverable_delete': '删除交付物',
        'binding_create': '加入课题',
        'binding_delete': '退出课题',
        'review_create': '提交评审',
        'slot_create': '创建人员',
        'slot_update': '更新人员',
        'slot_delete': '删除人员',
    }
    return labels.get(action, action)


@router.get("/users/{user_id}/profile")
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户档案和统计"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取关联的 slot
    slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == user_id).first()
    
    # 获取用户的所有 bindings
    bindings = db.query(Binding).filter(
        Binding.slot_id == slot.id if slot else False
    ).all() if slot else []
    
    binding_topic_ids = [b.topic_id for b in bindings]
    dri_topic_ids = [b.topic_id for b in bindings if b.is_dri]
    participant_topic_ids = [b.topic_id for b in bindings if not b.is_dri]
    
    # 课题统计
    topics = db.query(Topic).filter(Topic.id.in_(binding_topic_ids)).all() if binding_topic_ids else []
    
    completed_count = sum(1 for t in topics if t.result == TopicResult.SUCCESS)
    in_progress_count = sum(1 for t in topics if t.result == TopicResult.OPEN)
    unsolvable_count = sum(1 for t in topics if t.result == TopicResult.UNSOLVABLE)
    
    # 计算平均闭环周期（仅计算已完成的课题）
    completed_topics = [t for t in topics if t.result == TopicResult.SUCCESS and t.updated_at and t.created_at]
    if completed_topics:
        total_days = sum((t.updated_at - t.created_at).days for t in completed_topics)
        avg_days = total_days / len(completed_topics)
    else:
        avg_days = None
    
    # 技术点统计
    first_author_count = db.query(func.count(TechPoint.id)).filter(
        TechPoint.first_author_id == user_id
    ).scalar() or 0
    
    contributor_count = db.query(func.count(TechPointContributor.id)).filter(
        TechPointContributor.user_id == user_id
    ).scalar() or 0
    
    # 交付物统计
    deliverable_count = db.query(func.count(StageDeliverable.id)).filter(
        StageDeliverable.created_by_id == user_id
    ).scalar() or 0
    
    return {
        "userId": user.id,
        "userName": user.name,
        "userEmail": user.email,
        "slotName": slot.name if slot else None,
        "slotType": slot.type.value if slot else None,
        "driTopicCount": len(dri_topic_ids),
        "participantTopicCount": len(participant_topic_ids),
        "completedTopicCount": completed_count,
        "inProgressTopicCount": in_progress_count,
        "unsolvableTopicCount": unsolvable_count,
        "avgClosureDays": round(avg_days, 1) if avg_days else None,
        "firstAuthorTechPoints": first_author_count,
        "contributorTechPoints": contributor_count,
        "deliverableCount": deliverable_count,
    }


@router.get("/users/{user_id}/topics")
def get_user_topics(
    user_id: int,
    role: str = None,  # dri, participant, all
    status: str = None,  # open, success, unsolvable
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户参与的课题列表"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取关联的 slot
    slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == user_id).first()
    if not slot:
        return {"items": [], "total": 0, "page": page, "pageSize": page_size}
    
    # 基础查询：通过 binding 关联
    query = db.query(Topic).join(Binding).filter(Binding.slot_id == slot.id)
    
    # 角色过滤
    if role == 'dri':
        query = query.filter(Binding.is_dri == True)
    elif role == 'participant':
        query = query.filter(Binding.is_dri == False)
    
    # 状态过滤
    if status == 'open':
        query = query.filter(Topic.result == TopicResult.OPEN)
    elif status == 'success':
        query = query.filter(Topic.result == TopicResult.SUCCESS)
    elif status == 'unsolvable':
        query = query.filter(Topic.result == TopicResult.UNSOLVABLE)
    
    total = query.count()
    
    topics = query.order_by(Topic.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 获取每个课题的 DRI 信息
    items = []
    for t in topics:
        # 找这个用户在这个课题中的角色
        user_binding = db.query(Binding).filter(
            Binding.topic_id == t.id,
            Binding.slot_id == slot.id
        ).first()
        
        # 找课题的 DRI
        dri_binding = db.query(Binding).options(
            joinedload(Binding.slot)
        ).filter(
            Binding.topic_id == t.id,
            Binding.is_dri == True
        ).first()
        
        items.append({
            "id": t.id,
            "title": t.title,
            "type": t.type.value,
            "urgency": t.urgency.value,
            "result": t.result.value,
            "isDri": user_binding.is_dri if user_binding else False,
            "driName": dri_binding.slot.name if dri_binding and dri_binding.slot else None,
            "createdAt": t.created_at.isoformat() if t.created_at else None,
            "updatedAt": t.updated_at.isoformat() if t.updated_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/users/{user_id}/techpoints")
def get_user_techpoints(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的技术点列表（作为第一作者）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(TechPoint).options(
        joinedload(TechPoint.stage).joinedload(TopicStageInstance.topic)
    ).filter(TechPoint.first_author_id == user_id)
    
    total = query.count()
    
    techpoints = query.order_by(
        TechPoint.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for tp in techpoints:
        items.append({
            "id": tp.id,
            "name": tp.name,
            "description": tp.description,
            "status": tp.status,
            "hypothesis": tp.hypothesis,
            "stageName": tp.stage.name if tp.stage else None,
            "topicId": tp.stage.topic_id if tp.stage else None,
            "topicTitle": tp.stage.topic.title if tp.stage and tp.stage.topic else None,
            "createdAt": tp.created_at.isoformat() if tp.created_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/users/{user_id}/deliverables")
def get_user_deliverables(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的交付物列表"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 查询用户创建的交付物
    query = db.query(StageDeliverable).options(
        joinedload(StageDeliverable.topic),
        joinedload(StageDeliverable.stage_instance),
        joinedload(StageDeliverable.tech_point),
    ).filter(StageDeliverable.created_by_id == user_id)
    
    total = query.count()
    
    deliverables = query.order_by(
        StageDeliverable.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    # 查询用户作为第一作者的技术点关联的交付物
    tech_point_ids = db.query(TechPoint.id).filter(
        TechPoint.first_author_id == user_id
    ).all()
    tech_point_ids = [tp[0] for tp in tech_point_ids]
    
    items = []
    for d in deliverables:
        is_first_author = d.tech_point_id in tech_point_ids if d.tech_point_id else False
        items.append({
            "id": d.id,
            "name": d.name,
            "type": d.type.value if d.type else "link",
            "category": d.category.value if d.category else "other",
            "url": d.url,
            "topicId": d.topic_id,
            "topicTitle": d.topic.title if d.topic else None,
            "stageId": d.stage_instance_id,
            "stageName": d.stage_instance.name if d.stage_instance else None,
            "techPointId": d.tech_point_id,
            "techPointName": d.tech_point.name if d.tech_point else None,
            "isFirstAuthor": is_first_author,
            "createdAt": d.created_at.isoformat() if d.created_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/users/{user_id}/timeline")
def get_user_timeline(
    user_id: int,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的活动时间线"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 查询审计日志
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    
    total = query.count()
    
    logs = query.order_by(
        AuditLog.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for log in logs:
        # 尝试获取关联的课题信息
        topic_id = None
        topic_title = None
        entity_name = None
        
        if log.entity_type == 'Topic':
            topic_id = log.entity_id
            topic = db.query(Topic).filter(Topic.id == log.entity_id).first()
            if topic:
                topic_title = topic.title
                entity_name = topic.title
        elif log.entity_type == 'TopicStageInstance':
            stage = db.query(TopicStageInstance).filter(TopicStageInstance.id == log.entity_id).first()
            if stage:
                entity_name = stage.name
                topic_id = stage.topic_id
                topic = db.query(Topic).filter(Topic.id == stage.topic_id).first()
                if topic:
                    topic_title = topic.title
        elif log.entity_type == 'TechPoint':
            tp = db.query(TechPoint).filter(TechPoint.id == log.entity_id).first()
            if tp:
                entity_name = tp.name
                stage = db.query(TopicStageInstance).filter(TopicStageInstance.id == tp.stage_id).first()
                if stage:
                    topic_id = stage.topic_id
                    topic = db.query(Topic).filter(Topic.id == stage.topic_id).first()
                    if topic:
                        topic_title = topic.title
        elif log.entity_type == 'StageDeliverable':
            d = db.query(StageDeliverable).filter(StageDeliverable.id == log.entity_id).first()
            if d:
                entity_name = d.name
                topic_id = d.topic_id
                topic = db.query(Topic).filter(Topic.id == d.topic_id).first()
                if topic:
                    topic_title = topic.title
        elif log.entity_type == 'Binding':
            b = db.query(Binding).filter(Binding.id == log.entity_id).first()
            if b:
                topic_id = b.topic_id
                topic = db.query(Topic).filter(Topic.id == b.topic_id).first()
                if topic:
                    topic_title = topic.title
                    entity_name = topic.title
        
        items.append({
            "id": log.id,
            "action": log.action.value if log.action else str(log.action),
            "actionLabel": get_action_label(log.action.value if log.action else ''),
            "entityType": log.entity_type,
            "entityId": log.entity_id,
            "entityName": entity_name,
            "topicId": topic_id,
            "topicTitle": topic_title,
            "details": log.details,
            "createdAt": log.created_at.isoformat() if log.created_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/slots/{slot_id}/profile")
def get_slot_profile(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """通过 slot ID 获取档案（适用于没有关联用户的 slot）"""
    slot = db.query(CapacitySlot).filter(CapacitySlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # 如果有关联用户，返回用户档案
    if slot.user_id:
        return get_user_profile(slot.user_id, db, current_user)
    
    # 没有关联用户，基于 slot 统计
    bindings = db.query(Binding).filter(Binding.slot_id == slot_id).all()
    binding_topic_ids = [b.topic_id for b in bindings]
    dri_topic_ids = [b.topic_id for b in bindings if b.is_dri]
    participant_topic_ids = [b.topic_id for b in bindings if not b.is_dri]
    
    topics = db.query(Topic).filter(Topic.id.in_(binding_topic_ids)).all() if binding_topic_ids else []
    
    completed_count = sum(1 for t in topics if t.result == TopicResult.SUCCESS)
    in_progress_count = sum(1 for t in topics if t.result == TopicResult.OPEN)
    unsolvable_count = sum(1 for t in topics if t.result == TopicResult.UNSOLVABLE)
    
    # 计算平均闭环周期
    completed_topics = [t for t in topics if t.result == TopicResult.SUCCESS and t.updated_at and t.created_at]
    if completed_topics:
        total_days = sum((t.updated_at - t.created_at).days for t in completed_topics)
        avg_days = total_days / len(completed_topics)
    else:
        avg_days = None
    
    return {
        "userId": None,
        "userName": slot.name,
        "userEmail": None,
        "slotName": slot.name,
        "slotType": slot.type.value if slot.type else None,
        "driTopicCount": len(dri_topic_ids),
        "participantTopicCount": len(participant_topic_ids),
        "completedTopicCount": completed_count,
        "inProgressTopicCount": in_progress_count,
        "unsolvableTopicCount": unsolvable_count,
        "avgClosureDays": round(avg_days, 1) if avg_days else None,
        "firstAuthorTechPoints": 0,
        "contributorTechPoints": 0,
        "deliverableCount": 0,
    }
