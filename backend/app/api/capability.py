"""API routes for Capability, CapabilityGeneration, and DeliveryIssue management."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc

from ..database import get_db
from ..models.capability import (
    Capability,
    CapabilityCategory,
    CapabilityGeneration,
    DeliveryIssue,
    ProductLine,
    CapabilityType,
    MaturityLevel,
    RiskStatus,
    GenerationStatus,
    IssuePriority,
    IssueStatus,
)
from ..models.topic import Topic
from ..models.user import User, UserRole
from ..schemas.capability import (
    CapabilityCreate,
    CapabilityUpdate,
    CapabilityResponse,
    CapabilityStats,
    GenerationCreate,
    GenerationUpdate,
    GenerationResponse,
    CapabilityCategoryCreate,
    CapabilityCategoryUpdate,
    CapabilityCategoryResponse,
    DeliveryIssueCreate,
    DeliveryIssueUpdate,
    DeliveryIssueResponse,
    CapabilitySummary,
    DeliveryIssueSummary,
)
from ..schemas.user import UserResponse
from ..services.auth import get_current_user

router = APIRouter()

GEN_STATUS_LABELS = {
    "PLANNING": "规划中",
    "RESEARCHING": "研究中",
    "ENGINEERING": "工程化",
    "PILOT": "试用",
    "PRODUCTION": "量产",
    "ARCHIVED": "已归档",
}


def _build_category_path(cat: CapabilityCategory) -> str:
    parts = [cat.name]
    current = cat
    while current.parent_id:
        current = current.parent
        if current:
            parts.append(current.name)
    return " / ".join(reversed(parts))


def _generation_to_response(gen: CapabilityGeneration) -> dict:
    related_topics_data = [
        {
            "id": t.id, "title": t.title,
            "urgency": t.urgency.value if hasattr(t, 'urgency') and t.urgency else None,
            "result": t.result.value if hasattr(t, 'result') and t.result else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in (gen.related_topics or [])
    ]

    related_issues_data = [
        {
            "id": i.id, "title": i.title,
            "priority": i.priority.value if i.priority else None,
            "status": i.status.value if i.status else None,
            "product_line": i.product_line.value if i.product_line else None,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "updated_at": i.updated_at.isoformat() if i.updated_at else None,
        }
        for i in (gen.related_issues or [])
    ]

    owner_dict = UserResponse.model_validate(gen.owner).model_dump() if gen.owner else None

    return {
        "id": gen.id,
        "capability_id": gen.capability_id,
        "name": gen.name,
        "generation_code": gen.generation_code,
        "version": gen.version,
        "status": gen.status.value if gen.status else None,
        "maturity_level": gen.maturity_level.value if gen.maturity_level else None,
        "description": gen.description,
        "key_improvements": gen.key_improvements,
        "owner_id": gen.owner_id,
        "owner": owner_dict,
        "start_date": gen.start_date.isoformat() if gen.start_date else None,
        "target_date": gen.target_date.isoformat() if gen.target_date else None,
        "release_date": gen.release_date.isoformat() if gen.release_date else None,
        "related_topic_ids": [t.id for t in (gen.related_topics or [])],
        "related_topics": related_topics_data,
        "related_issue_ids": [i.id for i in (gen.related_issues or [])],
        "related_issues": related_issues_data,
        "created_at": gen.created_at.isoformat() if gen.created_at else None,
        "updated_at": gen.updated_at.isoformat() if gen.updated_at else None,
    }


def _load_capability(db: Session, capability_id: int) -> Capability:
    cap = (
        db.query(Capability)
        .options(
            joinedload(Capability.category),
            joinedload(Capability.owner),
            joinedload(Capability.backup_owner),
            joinedload(Capability.related_topics),
            joinedload(Capability.related_issues).joinedload(DeliveryIssue.owner),
            joinedload(Capability.generations)
            .joinedload(CapabilityGeneration.owner),
        )
        .filter(Capability.id == capability_id)
        .first()
    )
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found")
    # Eager load generation topics/issues
    for gen in cap.generations or []:
        _ = gen.related_topics
        _ = gen.related_issues
    return cap


def _capability_to_response(cap: Capability, db: Optional[Session] = None) -> dict:
    category_path = None
    if cap.category:
        category_path = _build_category_path(cap.category)

    related_topics_data = [
        {
            "id": t.id, "title": t.title,
            "urgency": t.urgency.value if hasattr(t, 'urgency') and t.urgency else None,
            "result": t.result.value if hasattr(t, 'result') and t.result else None,
            "dri_id": t.dri_id,
            "dri_name": t.dri.name if t.dri else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in cap.related_topics
    ] if cap.related_topics else []

    related_issues_data = [
        {
            "id": i.id, "title": i.title,
            "priority": i.priority.value if i.priority else None,
            "status": i.status.value if i.status else None,
            "product_line": i.product_line.value if i.product_line else None,
            "project_name": i.project_name,
            "owner_name": i.owner.name if i.owner else None,
            "impact": i.impact,
            "latest_progress": i.latest_progress,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "updated_at": i.updated_at.isoformat() if i.updated_at else None,
        }
        for i in cap.related_issues
    ] if cap.related_issues else []

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    recent_30d = sum(1 for i in (cap.related_issues or []) if i.created_at and i.created_at >= thirty_days_ago)
    p0p1 = sum(1 for i in (cap.related_issues or []) if i.priority and i.priority.value in ("P0", "P1"))
    topic_count = len(cap.related_topics or [])

    owner_dict = UserResponse.model_validate(cap.owner).model_dump() if cap.owner else None
    backup_owner_dict = UserResponse.model_validate(cap.backup_owner).model_dump() if cap.backup_owner else None

    generations = [_generation_to_response(g) for g in (cap.generations or [])]

    prod_gen = _generation_to_response(cap.current_production_generation) if cap.current_production_generation else None
    research_gen = _generation_to_response(cap.current_research_generation) if cap.current_research_generation else None
    next_gen = _generation_to_response(cap.next_planning_generation) if cap.next_planning_generation else None

    return {
        "id": cap.id,
        "name": cap.name,
        "description": cap.description,
        "category_id": cap.category_id,
        "category_path": category_path,
        "product_line": cap.product_line.value if cap.product_line else None,
        "capability_type": cap.capability_type.value if cap.capability_type else None,
        "maturity_level": cap.maturity_level.value if cap.maturity_level else None,
        "risk_status": cap.risk_status.value if cap.risk_status else None,
        "maturity_evidence": cap.maturity_evidence,
        "capability_gaps": cap.capability_gaps,
        "gap_actions": cap.gap_actions,
        "knowledge_records": cap.knowledge_records,
        "knowledge_wiki_page_ids": cap.knowledge_wiki_page_ids,
        "owner_id": cap.owner_id,
        "owner": owner_dict,
        "backup_owner_id": cap.backup_owner_id,
        "backup_owner": backup_owner_dict,
        "responsibility_field_id": cap.responsibility_field_id,
        "responsibility_field_name": cap.responsibility_field_name,
        "support_member_ids": cap.support_member_ids,
        "hr_risk_note": cap.hr_risk_note,
        "care_scope": cap.care_scope,
        "tags": cap.tags or [],
        "related_topic_ids": [t.id for t in cap.related_topics] if cap.related_topics else [],
        "related_topics": related_topics_data,
        "related_issue_ids": [i.id for i in cap.related_issues] if cap.related_issues else [],
        "related_issues": related_issues_data,
        "p0p1_issue_count": p0p1,
        "recent_30d_issue_count": recent_30d,
        "topic_count": topic_count,
        "generations": generations,
        "current_production_generation_id": cap.current_production_generation_id,
        "current_production_generation": prod_gen,
        "current_research_generation_id": cap.current_research_generation_id,
        "current_research_generation": research_gen,
        "next_planning_generation_id": cap.next_planning_generation_id,
        "next_planning_generation": next_gen,
        "created_at": cap.created_at.isoformat() if cap.created_at else None,
        "updated_at": cap.updated_at.isoformat() if cap.updated_at else None,
    }


# ============================================================
# Category tree endpoints
# ============================================================

@router.get("/categories/tree", response_model=List[CapabilityCategoryResponse])
def get_category_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    roots = (
        db.query(CapabilityCategory)
        .filter(CapabilityCategory.parent_id.is_(None))
        .order_by(CapabilityCategory.display_order)
        .all()
    )

    def build_tree(cat):
        children = sorted(cat.children, key=lambda c: c.display_order) if cat.children else []
        return {
            "id": cat.id, "name": cat.name, "description": cat.description,
            "parent_id": cat.parent_id, "display_order": cat.display_order,
            "children": [build_tree(c) for c in children],
        }

    return [build_tree(r) for r in roots]


@router.get("/categories/flat", response_model=List[CapabilityCategoryResponse])
def get_categories_flat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    categories = (
        db.query(CapabilityCategory)
        .order_by(CapabilityCategory.display_order)
        .all()
    )
    result = []
    for cat in categories:
        path = _build_category_path(cat)
        children_count = len(cat.children) if cat.children else 0
        result.append({
            "id": cat.id, "name": cat.name, "description": cat.description,
            "parent_id": cat.parent_id, "display_order": cat.display_order,
            "children": [], "category_path": path, "is_leaf": children_count == 0,
        })
    return result


# ============================================================
# Capability Stats
# ============================================================

@router.get("/stats", response_model=CapabilityStats)
def get_capability_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    total = db.query(sqlfunc.count(Capability.id)).scalar() or 0
    high_risk = (
        db.query(sqlfunc.count(Capability.id))
        .filter(Capability.risk_status == RiskStatus.HIGH_RISK)
        .scalar() or 0
    )
    thirty_days_ago = now - timedelta(days=30)
    recent_issues = (
        db.query(sqlfunc.count(DeliveryIssue.id))
        .filter(DeliveryIssue.created_at >= thirty_days_ago)
        .scalar() or 0
    )
    p0_p1_issue_caps = (
        db.query(sqlfunc.count(sqlfunc.distinct(Capability.id)))
        .join(Capability.related_issues)
        .filter(DeliveryIssue.priority.in_([IssuePriority.P0, IssuePriority.P1]))
        .scalar() or 0
    )
    topic_backed = (
        db.query(sqlfunc.count(sqlfunc.distinct(Capability.id)))
        .join(Capability.related_topics)
        .scalar() or 0
    )
    no_owner = (
        db.query(sqlfunc.count(Capability.id))
        .filter(Capability.owner_id.is_(None))
        .scalar() or 0
    )
    return CapabilityStats(
        total_capabilities=total, high_risk_count=high_risk,
        recent_30d_issue_count=recent_issues, p0_p1_capability_count=p0_p1_issue_caps,
        topic_backed_count=topic_backed, no_owner_count=no_owner,
    )


# ============================================================
# Capability CRUD
# ============================================================

@router.get("", response_model=List[dict])
def list_capabilities(
    product_line: Optional[str] = Query(None),
    capability_type: Optional[str] = Query(None),
    maturity_level: Optional[str] = Query(None),
    risk_status: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    has_topic: Optional[bool] = Query(None),
    has_issue: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Capability)
        .options(
            joinedload(Capability.category),
            joinedload(Capability.owner),
            joinedload(Capability.backup_owner),
            joinedload(Capability.related_topics),
            joinedload(Capability.related_issues),
            joinedload(Capability.current_production_generation),
            joinedload(Capability.current_research_generation),
        )
    )

    if product_line:
        try:
            pl = getattr(ProductLine, product_line)
            query = query.filter(Capability.product_line == pl)
        except (AttributeError, ValueError):
            pass
    if capability_type:
        try:
            ct = getattr(CapabilityType, capability_type)
            query = query.filter(Capability.capability_type == ct)
        except (AttributeError, ValueError):
            pass
    if maturity_level:
        try:
            ml = getattr(MaturityLevel, maturity_level)
            query = query.filter(Capability.maturity_level == ml)
        except (AttributeError, ValueError):
            pass
    if risk_status:
        try:
            rs = getattr(RiskStatus, risk_status)
            query = query.filter(Capability.risk_status == rs)
        except (AttributeError, ValueError):
            pass
    if category_id is not None:
        query = query.filter(Capability.category_id == category_id)
    if owner_id is not None:
        query = query.filter(Capability.owner_id == owner_id)
    if has_topic is True:
        query = query.filter(Capability.related_topics.any())
    elif has_topic is False:
        query = query.filter(~Capability.related_topics.any())
    if has_issue is True:
        query = query.filter(Capability.related_issues.any())
    elif has_issue is False:
        query = query.filter(~Capability.related_issues.any())
    if search:
        query = query.filter(Capability.name.ilike(f"%{search}%"))

    capabilities = query.order_by(Capability.updated_at.desc()).all()
    result = [_capability_to_response(cap, db) for cap in capabilities]

    def sort_key(cap_dict):
        risk_score = 0
        if cap_dict.get("risk_status") == "HIGH_RISK":
            risk_score = 3
        elif cap_dict.get("risk_status") == "WATCH":
            risk_score = 2
        p0_p1_count = cap_dict.get("p0p1_issue_count", 0)
        issue_count = cap_dict.get("recent_30d_issue_count", 0)
        has_owner = 1 if cap_dict.get("owner_id") else 0
        return (-risk_score, -p0_p1_count, -issue_count, -has_owner)

    result.sort(key=sort_key)
    return result


# ============================================================
# DeliveryIssue CRUD (must be before /{capability_id})
# ============================================================

@router.get("/issues", response_model=List[DeliveryIssueResponse])
def list_issues(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    product_line: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    capability_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(DeliveryIssue)
        .options(
            joinedload(DeliveryIssue.owner),
            joinedload(DeliveryIssue.related_capabilities),
            joinedload(DeliveryIssue.generation),
        )
    )
    if priority:
        try:
            p = getattr(IssuePriority, priority)
            query = query.filter(DeliveryIssue.priority == p)
        except (AttributeError, ValueError):
            pass
    if status:
        try:
            s = getattr(IssueStatus, status)
            query = query.filter(DeliveryIssue.status == s)
        except (AttributeError, ValueError):
            pass
    if product_line:
        try:
            pl = getattr(ProductLine, product_line)
            query = query.filter(DeliveryIssue.product_line == pl)
        except (AttributeError, ValueError):
            pass
    if project_name:
        query = query.filter(DeliveryIssue.project_name.ilike(f"%{project_name}%"))
    if capability_id:
        query = query.filter(DeliveryIssue.related_capabilities.any(Capability.id == capability_id))
    if search:
        query = query.filter(DeliveryIssue.title.ilike(f"%{search}%"))

    issues = query.order_by(DeliveryIssue.updated_at.desc()).all()
    return issues


@router.get("/issues/{issue_id}", response_model=DeliveryIssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = (
        db.query(DeliveryIssue)
        .options(
            joinedload(DeliveryIssue.owner),
            joinedload(DeliveryIssue.related_capabilities),
            joinedload(DeliveryIssue.generation),
        )
        .filter(DeliveryIssue.id == issue_id)
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="DeliveryIssue not found")
    return issue


@router.post("/issues", response_model=DeliveryIssueResponse)
def create_issue(
    data: DeliveryIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = DeliveryIssue(
        title=data.title, description=data.description,
        product_line=getattr(ProductLine, data.product_line, ProductLine.ALL),
        project_name=data.project_name,
        priority=getattr(IssuePriority, data.priority, IssuePriority.P2),
        status=getattr(IssueStatus, data.status, IssueStatus.NEW),
        owner_id=data.owner_id, impact=data.impact,
        latest_progress=data.latest_progress,
        generation_id=data.generation_id,
    )
    if data.related_capability_ids:
        caps = db.query(Capability).filter(Capability.id.in_(data.related_capability_ids)).all()
        issue.related_capabilities = caps

    db.add(issue)
    db.commit()
    db.refresh(issue)
    return (
        db.query(DeliveryIssue)
        .options(
            joinedload(DeliveryIssue.owner),
            joinedload(DeliveryIssue.related_capabilities),
            joinedload(DeliveryIssue.generation),
        )
        .filter(DeliveryIssue.id == issue.id)
        .first()
    )


@router.put("/issues/{issue_id}", response_model=DeliveryIssueResponse)
def update_issue(
    issue_id: int,
    data: DeliveryIssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(DeliveryIssue).filter(DeliveryIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="DeliveryIssue not found")

    if data.title is not None: issue.title = data.title
    if data.description is not None: issue.description = data.description
    if data.product_line is not None: issue.product_line = getattr(ProductLine, data.product_line, ProductLine.ALL)
    if data.project_name is not None: issue.project_name = data.project_name
    if data.priority is not None: issue.priority = getattr(IssuePriority, data.priority, IssuePriority.P2)
    if data.status is not None: issue.status = getattr(IssueStatus, data.status, IssueStatus.NEW)
    if data.owner_id is not None: issue.owner_id = data.owner_id
    if data.impact is not None: issue.impact = data.impact
    if data.latest_progress is not None: issue.latest_progress = data.latest_progress
    if data.generation_id is not None: issue.generation_id = data.generation_id
    if data.related_capability_ids is not None:
        caps = db.query(Capability).filter(Capability.id.in_(data.related_capability_ids)).all()
        issue.related_capabilities = caps

    db.commit()
    return (
        db.query(DeliveryIssue)
        .options(
            joinedload(DeliveryIssue.owner),
            joinedload(DeliveryIssue.related_capabilities),
            joinedload(DeliveryIssue.generation),
        )
        .filter(DeliveryIssue.id == issue.id)
        .first()
    )


@router.delete("/issues/{issue_id}")
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(DeliveryIssue).filter(DeliveryIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="DeliveryIssue not found")
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete issues")
    db.delete(issue)
    db.commit()
    return {"message": "DeliveryIssue deleted"}


@router.get("/{capability_id}", response_model=dict)
def get_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cap = _load_capability(db, capability_id)
    return _capability_to_response(cap, db)


@router.post("", response_model=dict)
def create_capability(
    data: CapabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in [UserRole.CUSTOMER_INTERNAL, UserRole.CUSTOMER_EXTERNAL]:
        raise HTTPException(status_code=403, detail="CUSTOMER users cannot create capabilities")

    cap = Capability(
        name=data.name, description=data.description,
        category_id=data.category_id,
        product_line=getattr(ProductLine, data.product_line, ProductLine.ALL),
        capability_type=getattr(CapabilityType, data.capability_type),
        maturity_level=getattr(MaturityLevel, data.maturity_level, MaturityLevel.L1),
        risk_status=getattr(RiskStatus, data.risk_status, RiskStatus.NORMAL),
        maturity_evidence=data.maturity_evidence, capability_gaps=data.capability_gaps,
        gap_actions=data.gap_actions, knowledge_records=data.knowledge_records,
        knowledge_wiki_page_ids=data.knowledge_wiki_page_ids,
        owner_id=data.owner_id, backup_owner_id=data.backup_owner_id,
        responsibility_field_id=data.responsibility_field_id,
        responsibility_field_name=data.responsibility_field_name,
        support_member_ids=data.support_member_ids,
        hr_risk_note=data.hr_risk_note, care_scope=data.care_scope,
        tags=data.tags or [],
    )

    if data.related_topic_ids:
        topics = db.query(Topic).filter(Topic.id.in_(data.related_topic_ids)).all()
        cap.related_topics = topics
    if data.related_issue_ids:
        issues = db.query(DeliveryIssue).filter(DeliveryIssue.id.in_(data.related_issue_ids)).all()
        cap.related_issues = issues

    db.add(cap)
    db.commit()
    db.refresh(cap)

    return _capability_to_response(_load_capability(db, cap.id), db)


@router.put("/{capability_id}", response_model=dict)
def update_capability(
    capability_id: int,
    data: CapabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cap = _load_capability(db, capability_id)

    if data.name is not None: cap.name = data.name
    if data.description is not None: cap.description = data.description
    if data.category_id is not None: cap.category_id = data.category_id
    if data.product_line is not None: cap.product_line = getattr(ProductLine, data.product_line, ProductLine.ALL)
    if data.capability_type is not None: cap.capability_type = getattr(CapabilityType, data.capability_type)
    if data.maturity_level is not None: cap.maturity_level = getattr(MaturityLevel, data.maturity_level, MaturityLevel.L1)
    if data.risk_status is not None: cap.risk_status = getattr(RiskStatus, data.risk_status, RiskStatus.NORMAL)
    if data.maturity_evidence is not None: cap.maturity_evidence = data.maturity_evidence
    if data.capability_gaps is not None: cap.capability_gaps = data.capability_gaps
    if data.gap_actions is not None: cap.gap_actions = data.gap_actions
    if data.knowledge_records is not None: cap.knowledge_records = data.knowledge_records
    if data.knowledge_wiki_page_ids is not None: cap.knowledge_wiki_page_ids = data.knowledge_wiki_page_ids
    if data.owner_id is not None: cap.owner_id = data.owner_id
    if data.backup_owner_id is not None: cap.backup_owner_id = data.backup_owner_id
    if data.responsibility_field_id is not None: cap.responsibility_field_id = data.responsibility_field_id
    if data.responsibility_field_name is not None: cap.responsibility_field_name = data.responsibility_field_name
    if data.support_member_ids is not None: cap.support_member_ids = data.support_member_ids
    if data.hr_risk_note is not None: cap.hr_risk_note = data.hr_risk_note
    if data.care_scope is not None: cap.care_scope = data.care_scope
    if data.tags is not None: cap.tags = data.tags
    if data.current_production_generation_id is not None: cap.current_production_generation_id = data.current_production_generation_id
    if data.current_research_generation_id is not None: cap.current_research_generation_id = data.current_research_generation_id
    if data.next_planning_generation_id is not None: cap.next_planning_generation_id = data.next_planning_generation_id

    if data.related_topic_ids is not None:
        topics = db.query(Topic).filter(Topic.id.in_(data.related_topic_ids)).all()
        cap.related_topics = topics
    if data.related_issue_ids is not None:
        issues = db.query(DeliveryIssue).filter(DeliveryIssue.id.in_(data.related_issue_ids)).all()
        cap.related_issues = issues

    db.commit()
    return _capability_to_response(_load_capability(db, cap.id), db)


@router.delete("/{capability_id}")
def delete_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cap = _load_capability(db, capability_id)
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete capabilities")
    db.delete(cap)
    db.commit()
    return {"message": "Capability deleted"}


# ============================================================
# Generation CRUD
# ============================================================

@router.post("/{capability_id}/generations", response_model=dict)
def create_generation(
    capability_id: int,
    data: GenerationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cap = db.query(Capability).filter(Capability.id == capability_id).first()
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found")

    gen = CapabilityGeneration(
        capability_id=capability_id,
        name=data.name,
        generation_code=data.generation_code,
        version=data.version,
        status=getattr(GenerationStatus, data.status, GenerationStatus.PLANNING),
        maturity_level=getattr(MaturityLevel, data.maturity_level, MaturityLevel.L1),
        description=data.description,
        key_improvements=data.key_improvements,
        owner_id=data.owner_id,
        start_date=data.start_date,
        target_date=data.target_date,
        release_date=data.release_date,
    )

    if data.related_topic_ids:
        topics = db.query(Topic).filter(Topic.id.in_(data.related_topic_ids)).all()
        gen.related_topics = topics
    if data.related_issue_ids:
        issues = db.query(DeliveryIssue).filter(DeliveryIssue.id.in_(data.related_issue_ids)).all()
        gen.related_issues = issues

    db.add(gen)
    db.commit()
    db.refresh(gen)

    gen_full = (
        db.query(CapabilityGeneration)
        .options(
            joinedload(CapabilityGeneration.owner),
            joinedload(CapabilityGeneration.related_topics),
            joinedload(CapabilityGeneration.related_issues),
        )
        .filter(CapabilityGeneration.id == gen.id)
        .first()
    )
    return _generation_to_response(gen_full)


@router.put("/generations/{generation_id}", response_model=dict)
def update_generation(
    generation_id: int,
    data: GenerationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    gen = db.query(CapabilityGeneration).filter(CapabilityGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    if data.name is not None: gen.name = data.name
    if data.generation_code is not None: gen.generation_code = data.generation_code
    if data.version is not None: gen.version = data.version
    if data.status is not None: gen.status = getattr(GenerationStatus, data.status, gen.status)
    if data.maturity_level is not None: gen.maturity_level = getattr(MaturityLevel, data.maturity_level, gen.maturity_level)
    if data.description is not None: gen.description = data.description
    if data.key_improvements is not None: gen.key_improvements = data.key_improvements
    if data.owner_id is not None: gen.owner_id = data.owner_id
    if data.start_date is not None: gen.start_date = data.start_date
    if data.target_date is not None: gen.target_date = data.target_date
    if data.release_date is not None: gen.release_date = data.release_date
    if data.related_topic_ids is not None:
        topics = db.query(Topic).filter(Topic.id.in_(data.related_topic_ids)).all()
        gen.related_topics = topics
    if data.related_issue_ids is not None:
        issues = db.query(DeliveryIssue).filter(DeliveryIssue.id.in_(data.related_issue_ids)).all()
        gen.related_issues = issues

    db.commit()

    gen_full = (
        db.query(CapabilityGeneration)
        .options(
            joinedload(CapabilityGeneration.owner),
            joinedload(CapabilityGeneration.related_topics),
            joinedload(CapabilityGeneration.related_issues),
        )
        .filter(CapabilityGeneration.id == generation_id)
        .first()
    )
    return _generation_to_response(gen_full)


@router.delete("/generations/{generation_id}")
def delete_generation(
    generation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    gen = db.query(CapabilityGeneration).filter(CapabilityGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete generations")
    db.delete(gen)
    db.commit()
    return {"message": "Generation deleted"}

