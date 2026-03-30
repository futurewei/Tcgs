"""
Stage Instance API - 阶段实例管理

支持：
- 创建/更新/删除阶段实例
- 拖拽重排
- 复制（用于算法分叉）
- 插入新阶段
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import json

from ..database import get_db
from ..models import Topic, TopicStageInstance, StageInstanceStatus, TechPoint, TechPointContributor, User, AuditLog
from ..models.audit import AuditAction
from ..models.review import ReviewComment
from ..services.auth import get_current_user

router = APIRouter(prefix="/topics/{topic_id}/stages", tags=["stage-instances"])


# ============ Schemas ============

class StageInstanceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    order: Optional[float] = None
    is_terminal: bool = False
    allow_result: bool = False
    require_artifact: bool = False
    require_review: bool = False
    objective: Optional[str] = None
    success_criteria: Optional[str] = None
    failure_criteria: Optional[str] = None
    insert_after_id: Optional[int] = None  # 插入到哪个阶段之后

class StageInstanceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[float] = None
    is_terminal: Optional[bool] = None
    allow_result: Optional[bool] = None
    require_artifact: Optional[bool] = None
    require_review: Optional[bool] = None
    objective: Optional[str] = None
    success_criteria: Optional[Any] = None  # JSON array for checklist
    failure_criteria: Optional[Any] = None  # JSON array for checklist
    required_outputs: Optional[Any] = None  # JSON array for output list
    conclusion: Optional[str] = None
    status: Optional[str] = None


class ReviewCommentCreate(BaseModel):
    content: str


class StageCompleteRequest(BaseModel):
    """阶段完成确认请求"""
    completion_note: Optional[str] = None  # 完成说明
    remaining_issues: Optional[str] = None  # 遗留问题/风险
    force: bool = False  # 是否强制完成（跳过校验）


class StageMoveRequest(BaseModel):
    """阶段跃迁请求"""
    direction: str  # forward / back
    completion_note: Optional[str] = None
    remaining_issues: Optional[str] = None


class StageReorderRequest(BaseModel):
    stage_ids: List[int]  # 新顺序的 stage_id 列表

class StageCopyRequest(BaseModel):
    source_stage_id: int
    insert_after_id: Optional[int] = None  # 插入到哪个阶段之后

class TechPointCreate(BaseModel):
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    approach: Optional[str] = None
    first_author_id: int

class TechPointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    approach: Optional[str] = None
    conclusion: Optional[str] = None
    status: Optional[str] = None

class ContributorAdd(BaseModel):
    user_id: int
    contribution: Optional[str] = None
    contribution_percentage: Optional[int] = None


# ============ Stage Instance Routes ============

@router.get("")
def list_stage_instances(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课题的所有阶段实例"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    stages = db.query(TopicStageInstance).filter(
        TopicStageInstance.topic_id == topic_id
    ).order_by(TopicStageInstance.order).all()
    
    return [_serialize_stage_instance(s, db=db) for s in stages]


@router.post("")
def create_stage_instance(
    topic_id: int,
    data: StageInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新阶段实例"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 计算 order
    order = data.order
    if order is None:
        if data.insert_after_id:
            # 插入到指定阶段之后
            after_stage = db.query(TopicStageInstance).filter(
                TopicStageInstance.id == data.insert_after_id
            ).first()
            if after_stage:
                # 找下一个阶段
                next_stage = db.query(TopicStageInstance).filter(
                    TopicStageInstance.topic_id == topic_id,
                    TopicStageInstance.order > after_stage.order
                ).order_by(TopicStageInstance.order).first()
                if next_stage:
                    order = (after_stage.order + next_stage.order) / 2
                else:
                    order = after_stage.order + 1
            else:
                order = 0
        else:
            # 添加到末尾
            last_stage = db.query(TopicStageInstance).filter(
                TopicStageInstance.topic_id == topic_id
            ).order_by(TopicStageInstance.order.desc()).first()
            order = (last_stage.order + 1) if last_stage else 0
    
    stage = TopicStageInstance(
        topic_id=topic_id,
        name=data.name,
        description=data.description,
        order=order,
        is_terminal=data.is_terminal,
        allow_result=data.allow_result,
        require_artifact=data.require_artifact,
        require_review=data.require_review,
        objective=data.objective,
        success_criteria=data.success_criteria,
        failure_criteria=data.failure_criteria,
        status=StageInstanceStatus.PENDING,
        created_by_id=current_user.id
    )
    db.add(stage)
    db.flush()  # 获取 stage.id，但不 commit

    # 审计日志
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.STAGE_CHANGE,
        entity_type="TopicStageInstance",
        entity_id=stage.id,
        new_value=json.dumps({"action": "create", "topic_id": topic_id, "name": data.name})
    ))
    db.commit()
    db.refresh(stage)
    
    return _serialize_stage_instance(stage, db=db)


@router.get("/{stage_id}")
def get_stage_instance(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取阶段实例详情（包含技术点）"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    return _serialize_stage_instance(stage, include_tech_points=True, db=db)


@router.put("/{stage_id}")
def update_stage_instance(
    topic_id: int,
    stage_id: int,
    data: StageInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新阶段实例"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    update_data = data.dict(exclude_unset=True)
    
    # 处理状态变更
    if "status" in update_data:
        new_status = StageInstanceStatus(update_data["status"])
        if new_status == StageInstanceStatus.ACTIVE and stage.status != StageInstanceStatus.ACTIVE:
            stage.started_at = datetime.utcnow()
        elif new_status == StageInstanceStatus.DONE and stage.status != StageInstanceStatus.DONE:
            stage.completed_at = datetime.utcnow()
            stage.completed_by_id = current_user.id
        update_data["status"] = new_status
    
    for key, value in update_data.items():
        setattr(stage, key, value)
    
    db.commit()
    db.refresh(stage)
    
    return _serialize_stage_instance(stage, db=db)


@router.delete("/{stage_id}")
def delete_stage_instance(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除阶段实例"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    # 审计日志
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.STAGE_CHANGE,
        entity_type="TopicStageInstance",
        entity_id=stage_id,
        new_value=json.dumps({"action": "delete", "topic_id": topic_id, "name": stage.name})
    ))
    
    db.delete(stage)
    db.commit()
    
    return {"success": True}


# ============ 阶段跃迁 API ============

def _validate_stage_completion(stage: TopicStageInstance, db: Session) -> dict:
    """
    校验阶段是否满足完成条件
    返回: {"valid": bool, "errors": list, "warnings": list}
    """
    errors = []
    warnings = []
    
    # 1. 检查是否需要交付物
    if stage.require_artifact:
        from ..models.deliverable import StageDeliverable
        deliverable_count = db.query(StageDeliverable).filter(
            StageDeliverable.stage_instance_id == stage.id
        ).count()
        if deliverable_count == 0:
            errors.append("该阶段需要上传交付物才能完成")
    
    # 2. 检查必交输出物是否已交付
    if stage.required_outputs:
        undelivered = [o for o in stage.required_outputs if o.get('required') and not o.get('delivered')]
        if undelivered:
            names = [o.get('name', '未命名') for o in undelivered]
            errors.append(f"以下必交输出物未完成: {', '.join(names)}")
    
    # 3. 检查成功判据中的必须项是否已勾选
    if stage.success_criteria:
        unchecked_required = [c for c in stage.success_criteria if c.get('required') and not c.get('checked')]
        if unchecked_required:
            texts = [c.get('text', '未命名')[:20] for c in unchecked_required]
            errors.append(f"以下必须成功判据未勾选: {', '.join(texts)}")
    
    # 4. 检查是否有未解决的阻塞风险
    from .risks import TopicRisk
    blocking_risks = db.query(TopicRisk).filter(
        TopicRisk.stage_instance_id == stage.id,
        TopicRisk.level == 'red',
        TopicRisk.is_resolved == False
    ).count()
    if blocking_risks > 0:
        warnings.append(f"该阶段有 {blocking_risks} 个未解决的阻塞风险")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


@router.post("/{stage_id}/validate")
def validate_stage_completion(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """校验阶段是否可以完成"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    return _validate_stage_completion(stage, db)


@router.post("/{stage_id}/complete")
def complete_stage(
    topic_id: int,
    stage_id: int,
    data: StageCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """完成阶段（带校验）"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    # 校验
    if not data.force:
        validation = _validate_stage_completion(stage, db)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "阶段完成条件不满足",
                    "errors": validation["errors"],
                    "warnings": validation["warnings"]
                }
            )
    
    # 更新状态
    stage.status = StageInstanceStatus.DONE
    stage.completed_at = datetime.utcnow()
    stage.completed_by_id = current_user.id
    stage.completion_note = data.completion_note
    stage.remaining_issues = data.remaining_issues
    
    # 审计日志
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.STAGE_CHANGE,
        entity_type="TopicStageInstance",
        entity_id=stage_id,
        new_value=json.dumps({
            "action": "complete",
            "topic_id": topic_id,
            "name": stage.name,
            "completion_note": data.completion_note,
            "remaining_issues": data.remaining_issues
        })
    ))
    
    db.commit()
    db.refresh(stage)
    
    return _serialize_stage_instance(stage, db=db)


@router.post("/{stage_id}/reopen")
def reopen_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新打开已完成的阶段"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    if stage.status != StageInstanceStatus.DONE:
        raise HTTPException(status_code=400, detail="只能重新打开已完成的阶段")
    
    # 更新状态
    stage.status = StageInstanceStatus.ACTIVE
    stage.completed_at = None
    stage.completed_by_id = None
    
    # 审计日志
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.STAGE_CHANGE,
        entity_type="TopicStageInstance",
        entity_id=stage_id,
        new_value=json.dumps({"action": "reopen", "topic_id": topic_id, "name": stage.name})
    ))
    
    db.commit()
    db.refresh(stage)
    
    return _serialize_stage_instance(stage, db=db)


@router.post("/{stage_id}/move")
def move_stage(
    topic_id: int,
    stage_id: int,
    data: StageMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    阶段跃迁（Move Forward / Move Back）
    - Forward: 完成当前阶段，激活下一阶段
    - Back: 重新激活上一阶段
    """
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    # 获取所有阶段（按顺序）
    all_stages = db.query(TopicStageInstance).filter(
        TopicStageInstance.topic_id == topic_id
    ).order_by(TopicStageInstance.order).all()
    
    current_idx = next((i for i, s in enumerate(all_stages) if s.id == stage_id), -1)
    if current_idx == -1:
        raise HTTPException(status_code=400, detail="阶段不在课题中")
    
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    
    if data.direction == "forward":
        # 校验当前阶段是否可以完成
        validation = _validate_stage_completion(stage, db)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "阶段完成条件不满足",
                    "errors": validation["errors"],
                    "warnings": validation["warnings"]
                }
            )
        
        # 完成当前阶段
        stage.status = StageInstanceStatus.DONE
        stage.completed_at = datetime.utcnow()
        stage.completed_by_id = current_user.id
        stage.completion_note = data.completion_note
        stage.remaining_issues = data.remaining_issues
       
        is_last_stage = (current_idx == len(all_stages) - 1)

       # ✅ 终止阶段 + 允许结项：如果已经是最后阶段 => 自动把课题结项
        if stage.is_terminal and stage.allow_result and is_last_stage:
            # 你这里也可以扩展：如果 data 里允许传 result，就用传入的
            # 现在按你的按钮语义：点“完成”默认 SUCCESS
            topic.result = TopicResult.SUCCESS

            # ✅ 结项后：释放所有人力占用（删除该 topic 下所有 bindings）
            db.query(Binding).filter(Binding.topic_id == topic_id).delete(synchronize_session=False)

            # 可选：清掉 dri_id（避免 profile 统计还认为有 DRI）
            topic.dri_id = None

            # 可选：current_stage_instance_id 设成当前 stage（或 None 都行）
            topic.current_stage_instance_id = stage.id

        else:
            # 激活下一阶段
            if current_idx + 1 < len(all_stages):
                next_stage = all_stages[current_idx + 1]
                if next_stage.status == StageInstanceStatus.PENDING:
                    next_stage.status = StageInstanceStatus.ACTIVE
                    next_stage.started_at = datetime.utcnow()
                topic.current_stage_instance_id = next_stage.id

        action = "stage_move_forward"
 
    elif data.direction == "back":
        if current_idx == 0:
            raise HTTPException(status_code=400, detail="已经是第一个阶段")
        
        # 重置当前阶段为待开始
        stage.status = StageInstanceStatus.PENDING
        stage.started_at = None
        
        # 重新激活上一阶段
        prev_stage = all_stages[current_idx - 1]
        prev_stage.status = StageInstanceStatus.ACTIVE
        prev_stage.completed_at = None
        prev_stage.completed_by_id = None
        
        # 更新课题的当前阶段
        topic.current_stage_instance_id = prev_stage.id
        
        action = "stage_move_back"
    else:
        raise HTTPException(status_code=400, detail="direction 必须是 forward 或 back")
    
    # 审计日志
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.STAGE_CHANGE,
        entity_type="TopicStageInstance",
        entity_id=stage_id,
        new_value=json.dumps({
            "action": action,
            "topic_id": topic_id,
            "name": stage.name,
            "direction": data.direction
        })
    ))
    
    db.commit()
    
    # 返回更新后的所有阶段
    db.refresh(stage)
    return {
        "success": True,
        "currentStage": _serialize_stage_instance(stage, db=db),
        "allStages": [_serialize_stage_instance(s, db=db) for s in all_stages]
    }


@router.post("/reorder")
def reorder_stages(
    topic_id: int,
    data: StageReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新排序阶段（支持拖拽）"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 更新每个阶段的 order
    for idx, stage_id in enumerate(data.stage_ids):
        stage = db.query(TopicStageInstance).filter(
            TopicStageInstance.id == stage_id,
            TopicStageInstance.topic_id == topic_id
        ).first()
        if stage:
            stage.order = float(idx)
    
    db.commit()
    
    # 返回新顺序
    stages = db.query(TopicStageInstance).filter(
        TopicStageInstance.topic_id == topic_id
    ).order_by(TopicStageInstance.order).all()
    
    return [_serialize_stage_instance(s, db=db) for s in stages]


@router.post("/copy")
def copy_stage(
    topic_id: int,
    data: StageCopyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复制阶段（用于算法分叉）"""
    source = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == data.source_stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="源阶段不存在")
    
    # 计算 order
    if data.insert_after_id:
        after_stage = db.query(TopicStageInstance).filter(
            TopicStageInstance.id == data.insert_after_id
        ).first()
        if after_stage:
            next_stage = db.query(TopicStageInstance).filter(
                TopicStageInstance.topic_id == topic_id,
                TopicStageInstance.order > after_stage.order
            ).order_by(TopicStageInstance.order).first()
            if next_stage:
                order = (after_stage.order + next_stage.order) / 2
            else:
                order = after_stage.order + 1
        else:
            order = source.order + 0.5
    else:
        order = source.order + 0.5
    
    # 复制阶段
    new_stage = TopicStageInstance(
        topic_id=topic_id,
        name=f"{source.name} (副本)",
        description=source.description,
        order=order,
        is_terminal=source.is_terminal,
        allow_result=source.allow_result,
        require_artifact=source.require_artifact,
        require_review=source.require_review,
        objective=source.objective,
        success_criteria=source.success_criteria,
        failure_criteria=source.failure_criteria,
        status=StageInstanceStatus.PENDING,
        cloned_from_id=source.id,
        created_by_id=current_user.id
    )
    db.add(new_stage)
    db.flush()  # 获取 new_stage.id

    # 审计日志
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.STAGE_CHANGE,
        entity_type="TopicStageInstance",
        entity_id=new_stage.id,
        new_value=json.dumps({"action": "copy", "topic_id": topic_id, "source_id": source.id})
    ))
    db.commit()
    
    db.refresh(new_stage)

    return _serialize_stage_instance(new_stage, db=db)


@router.post("/{stage_id}/activate")
def activate_stage(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """激活阶段（设为当前阶段）"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    
    # 更新状态
    if stage.status == StageInstanceStatus.PENDING:
        stage.status = StageInstanceStatus.ACTIVE
        stage.started_at = datetime.utcnow()
    
    # 更新课题的当前阶段
    topic.current_stage_instance_id = stage_id
    
    db.commit()
    db.refresh(stage)
    
    return _serialize_stage_instance(stage, db=db)


# ============ Review Comment Routes ============

@router.get("/{stage_id}/reviews")
def list_stage_reviews(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取阶段的所有评审意见"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")

    reviews = db.query(ReviewComment).filter(
        ReviewComment.stage_instance_id == stage_id
    ).order_by(ReviewComment.created_at.desc()).all()

    result = []
    for r in reviews:
        user_data = None
        if r.created_by:
            user_data = {"id": r.created_by.id, "name": r.created_by.name}
        result.append({
            "id": r.id,
            "stageInstanceId": r.stage_instance_id,
            "content": r.content,
            "createdBy": user_data,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        })

    return result


@router.post("/{stage_id}/reviews")
def create_stage_review(
    topic_id: int,
    stage_id: int,
    data: ReviewCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加评审意见"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")

    review = ReviewComment(
        topic_id=topic_id,
        stage_instance_id=stage_id,
        content=data.content,
        created_by_id=current_user.id
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    user_data = None
    if review.created_by:
        user_data = {"id": review.created_by.id, "name": review.created_by.name}

    return {
        "id": review.id,
        "stageInstanceId": review.stage_instance_id,
        "content": review.content,
        "createdBy": user_data,
        "createdAt": review.created_at.isoformat() if review.created_at else None,
    }


@router.delete("/{stage_id}/reviews/{review_id}")
def delete_stage_review(
    topic_id: int,
    stage_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除评审意见"""
    review = db.query(ReviewComment).filter(
        ReviewComment.id == review_id,
        ReviewComment.stage_instance_id == stage_id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="评审意见不存在")

    # 只有创建者或管理员可以删除
    if review.created_by_id != current_user.id and current_user.role != 'ADMIN':
        raise HTTPException(status_code=403, detail="无权删除此评审意见")

    db.delete(review)
    db.commit()

    return {"success": True}


# ============ Tech Point Routes ============

@router.get("/{stage_id}/tech-points")
def list_tech_points(
    topic_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取阶段的所有技术点"""
    points = db.query(TechPoint).filter(
        TechPoint.stage_id == stage_id
    ).order_by(TechPoint.order).all()
    
    return [_serialize_tech_point(p, db) for p in points]


@router.post("/{stage_id}/tech-points")
def create_tech_point(
    topic_id: int,
    stage_id: int,
    data: TechPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建技术点"""
    stage = db.query(TopicStageInstance).filter(
        TopicStageInstance.id == stage_id,
        TopicStageInstance.topic_id == topic_id
    ).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    # 计算 order
    last_point = db.query(TechPoint).filter(
        TechPoint.stage_id == stage_id
    ).order_by(TechPoint.order.desc()).first()
    order = (last_point.order + 1) if last_point else 0
    
    point = TechPoint(
        stage_id=stage_id,
        name=data.name,
        description=data.description,
        hypothesis=data.hypothesis,
        approach=data.approach,
        first_author_id=data.first_author_id,
        order=order,
        status="draft"
    )
    db.add(point)
    db.commit()
    db.refresh(point)
    
    return _serialize_tech_point(point, db)


@router.put("/{stage_id}/tech-points/{point_id}")
def update_tech_point(
    topic_id: int,
    stage_id: int,
    point_id: int,
    data: TechPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新技术点"""
    point = db.query(TechPoint).filter(
        TechPoint.id == point_id,
        TechPoint.stage_id == stage_id
    ).first()
    if not point:
        raise HTTPException(status_code=404, detail="技术点不存在")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(point, key, value)
    
    db.commit()
    db.refresh(point)
    
    return _serialize_tech_point(point, db)


@router.delete("/{stage_id}/tech-points/{point_id}")
def delete_tech_point(
    topic_id: int,
    stage_id: int,
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除技术点"""
    point = db.query(TechPoint).filter(
        TechPoint.id == point_id,
        TechPoint.stage_id == stage_id
    ).first()
    if not point:
        raise HTTPException(status_code=404, detail="技术点不存在")
    
    db.delete(point)
    db.commit()
    
    return {"success": True}


@router.post("/{stage_id}/tech-points/{point_id}/contributors")
def add_contributor(
    topic_id: int,
    stage_id: int,
    point_id: int,
    data: ContributorAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加技术点贡献者"""
    point = db.query(TechPoint).filter(
        TechPoint.id == point_id,
        TechPoint.stage_id == stage_id
    ).first()
    if not point:
        raise HTTPException(status_code=404, detail="技术点不存在")
    
    # 检查是否已存在
    existing = db.query(TechPointContributor).filter(
        TechPointContributor.tech_point_id == point_id,
        TechPointContributor.user_id == data.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该贡献者已存在")
    
    contributor = TechPointContributor(
        tech_point_id=point_id,
        user_id=data.user_id,
        contribution=data.contribution,
        contribution_percentage=data.contribution_percentage
    )
    db.add(contributor)
    db.commit()
    db.refresh(contributor)
    
    return {"id": contributor.id, "user_id": contributor.user_id}


# ============ Helpers ============

def _serialize_stage_instance(stage: TopicStageInstance, include_tech_points: bool = False, db: Session = None) -> dict:
    """Serialize a stage instance, with resilient handling of relationship fields.

    In some cases (e.g., after commit/refresh, or when objects are detached/expired),
    accessing relationship attributes like stage.created_by may raise.
    We defensively resolve createdBy/completedBy using either the relationship or a DB lookup.
    """
    # -------- safe relationship resolution --------
    created_by_data = None
    completed_by_data = None

    try:
        if getattr(stage, 'created_by', None):
            created_by_data = {"id": stage.created_by.id, "name": stage.created_by.name}
    except Exception:
        if db and getattr(stage, 'created_by_id', None):
            user = db.query(User).filter(User.id == stage.created_by_id).first()
            if user:
                created_by_data = {"id": user.id, "name": user.name}

    try:
        if getattr(stage, 'completed_by', None):
            completed_by_data = {"id": stage.completed_by.id, "name": stage.completed_by.name}
    except Exception:
        if db and getattr(stage, 'completed_by_id', None):
            user = db.query(User).filter(User.id == stage.completed_by_id).first()
            if user:
                completed_by_data = {"id": user.id, "name": user.name}

    # Serialize reviews if require_review is enabled
    reviews_data = []
    if getattr(stage, 'require_review', False):
        try:
            for r in stage.reviews:
                review_user = None
                try:
                    if r.created_by:
                        review_user = {"id": r.created_by.id, "name": r.created_by.name}
                except Exception:
                    if db and r.created_by_id:
                        user = db.query(User).filter(User.id == r.created_by_id).first()
                        if user:
                            review_user = {"id": user.id, "name": user.name}
                reviews_data.append({
                    "id": r.id,
                    "stageInstanceId": r.stage_instance_id,
                    "content": r.content,
                    "createdBy": review_user,
                    "createdAt": r.created_at.isoformat() if r.created_at else None,
                })
        except Exception:
            pass

    result = {
        "id": stage.id,
        "topicId": stage.topic_id,
        "name": stage.name,
        "description": stage.description,
        "order": stage.order,
        "isTerminal": stage.is_terminal,
        "allowResult": stage.allow_result,
        "requireArtifact": stage.require_artifact,
        "requireReview": stage.require_review,
        "status": stage.status.value if stage.status else "pending",
        "startedAt": stage.started_at.isoformat() if stage.started_at else None,
        "completedAt": stage.completed_at.isoformat() if stage.completed_at else None,
        "completedById": stage.completed_by_id,
        "completedBy": completed_by_data,
        "completionNote": stage.completion_note,
        "remainingIssues": stage.remaining_issues,
        "objective": stage.objective,
        "successCriteria": stage.success_criteria,
        "failureCriteria": stage.failure_criteria,
        "requiredOutputs": stage.required_outputs,
        "conclusion": stage.conclusion,
        "clonedFromId": stage.cloned_from_id,
        "createdAt": stage.created_at.isoformat() if stage.created_at else None,
        "createdBy": created_by_data,
        "reviews": reviews_data,
    }

    if include_tech_points:
        result["techPoints"] = [_serialize_tech_point(p, db) for p in stage.tech_points]
        # deliverables
        from ..models.deliverable import StageDeliverable  # noqa: F401
        result["deliverables"] = [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type.value if d.type else "link",
                "category": d.category.value if d.category else "other",
                "url": d.url,
                "description": d.description,
                "createdAt": d.created_at.isoformat() if d.created_at else None,
                "createdBy": {"id": d.created_by.id, "name": d.created_by.name} if d.created_by else None,
                "techPointId": d.tech_point_id,
            }
            for d in stage.deliverables
        ]

    return result


def _serialize_tech_point(point: TechPoint, db: Session = None) -> dict:
    # 尝试通过 user_id 找到对应的 Slot 名字
    first_author_name = None
    first_author_id = None
    if point.first_author:
        first_author_id = point.first_author.id
        first_author_name = point.first_author.name  # 默认使用 User 名字
        # 尝试查找关联的 Slot
        if db:
            from ..models.capacity import CapacitySlot
            slot = db.query(CapacitySlot).filter(CapacitySlot.user_id == point.first_author.id).first()
            if slot:
                first_author_name = slot.name  # 使用 Slot 名字
    
    return {
        "id": point.id,
        "stageId": point.stage_id,
        "name": point.name,
        "description": point.description,
        "hypothesis": point.hypothesis,
        "approach": point.approach,
        "conclusion": point.conclusion,
        "status": point.status,
        "order": point.order,
        "firstAuthor": {
            "id": first_author_id,
            "name": first_author_name
        } if point.first_author else None,
        "contributors": [
            {
                "id": c.id,
                "userId": c.user_id,
                "userName": c.user.name if c.user else None,
                "contribution": c.contribution,
                "contributionPercentage": c.contribution_percentage
            }
            for c in point.contributors
        ],
        "createdAt": point.created_at.isoformat() if point.created_at else None
    }
