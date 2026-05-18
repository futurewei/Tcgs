"""Schema definitions for Capability, CapabilityGeneration, and DeliveryIssue API."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from .user import UserResponse


# ============ CapabilityCategory Schemas ============

class CapabilityCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    display_order: int = 0


class CapabilityCategoryCreate(CapabilityCategoryBase):
    pass


class CapabilityCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    display_order: Optional[int] = None


class CapabilityCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    display_order: int = 0
    children: List["CapabilityCategoryResponse"] = []

    class Config:
        from_attributes = True


# ============ Generation Schemas ============

class GenerationStatusLabels:
    PLANNING = "规划中"
    RESEARCHING = "研究中"
    ENGINEERING = "工程化"
    PILOT = "试用"
    PRODUCTION = "量产"
    ARCHIVED = "已归档"


class GenerationResponse(BaseModel):
    id: int
    capability_id: int
    name: str
    generation_code: str
    version: Optional[str] = None
    status: str
    maturity_level: str
    description: Optional[str] = None
    key_improvements: Optional[str] = None
    owner_id: Optional[int] = None
    owner: Optional[UserResponse] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    release_date: Optional[date] = None
    related_topic_ids: List[int] = []
    related_topics: List[dict] = []
    related_issue_ids: List[int] = []
    related_issues: List[dict] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class GenerationCreate(BaseModel):
    name: str = Field(..., max_length=200)
    generation_code: str = Field(..., max_length=20)
    version: Optional[str] = None
    status: str = "PLANNING"
    maturity_level: str = "L1"
    description: Optional[str] = None
    key_improvements: Optional[str] = None
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    release_date: Optional[date] = None
    related_topic_ids: Optional[List[int]] = None
    related_issue_ids: Optional[List[int]] = None


class GenerationUpdate(BaseModel):
    name: Optional[str] = None
    generation_code: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    maturity_level: Optional[str] = None
    description: Optional[str] = None
    key_improvements: Optional[str] = None
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    release_date: Optional[date] = None
    related_topic_ids: Optional[List[int]] = None
    related_issue_ids: Optional[List[int]] = None


# ============ Capability Schemas ============

class CapabilityBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    product_line: str = Field(default="ALL")
    capability_type: str
    maturity_level: str = Field(default="L1")
    risk_status: str = Field(default="NORMAL")
    maturity_evidence: Optional[str] = None
    capability_gaps: Optional[str] = None
    gap_actions: Optional[str] = None
    knowledge_records: Optional[str] = None
    knowledge_wiki_page_ids: Optional[str] = None
    owner_id: Optional[int] = None
    backup_owner_id: Optional[int] = None
    responsibility_field_id: Optional[int] = None
    responsibility_field_name: Optional[str] = None
    support_member_ids: Optional[str] = None
    hr_risk_note: Optional[str] = None
    care_scope: Optional[str] = None
    tags: Optional[List[str]] = None
    related_topic_ids: Optional[List[int]] = None
    related_issue_ids: Optional[List[int]] = None


class CapabilityCreate(CapabilityBase):
    pass


class CapabilityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    product_line: Optional[str] = None
    capability_type: Optional[str] = None
    maturity_level: Optional[str] = None
    risk_status: Optional[str] = None
    maturity_evidence: Optional[str] = None
    capability_gaps: Optional[str] = None
    gap_actions: Optional[str] = None
    knowledge_records: Optional[str] = None
    knowledge_wiki_page_ids: Optional[str] = None
    owner_id: Optional[int] = None
    backup_owner_id: Optional[int] = None
    responsibility_field_id: Optional[int] = None
    responsibility_field_name: Optional[str] = None
    support_member_ids: Optional[str] = None
    hr_risk_note: Optional[str] = None
    care_scope: Optional[str] = None
    tags: Optional[List[str]] = None
    related_topic_ids: Optional[List[int]] = None
    related_issue_ids: Optional[List[int]] = None
    current_production_generation_id: Optional[int] = None
    current_research_generation_id: Optional[int] = None
    next_planning_generation_id: Optional[int] = None


class CapabilitySummary(BaseModel):
    id: int
    name: str
    product_line: str
    capability_type: str

    class Config:
        from_attributes = True


class DeliveryIssueSummary(BaseModel):
    id: int
    title: str
    priority: str
    status: str
    product_line: str
    project_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CapabilityResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_path: Optional[str] = None
    product_line: str
    capability_type: str
    maturity_level: str
    risk_status: str
    maturity_evidence: Optional[str] = None
    capability_gaps: Optional[str] = None
    gap_actions: Optional[str] = None
    knowledge_records: Optional[str] = None
    knowledge_wiki_page_ids: Optional[str] = None
    owner_id: Optional[int] = None
    owner: Optional[UserResponse] = None
    backup_owner_id: Optional[int] = None
    backup_owner: Optional[UserResponse] = None
    responsibility_field_id: Optional[int] = None
    responsibility_field_name: Optional[str] = None
    support_member_ids: Optional[str] = None
    hr_risk_note: Optional[str] = None
    care_scope: Optional[str] = None
    tags: Optional[List[str]] = None
    related_topic_ids: Optional[List[int]] = None
    related_topics: Optional[List[dict]] = None
    related_issue_ids: Optional[List[int]] = None
    related_issues: Optional[List[DeliveryIssueSummary]] = None
    p0p1_issue_count: int = 0
    recent_30d_issue_count: int = 0
    topic_count: int = 0
    generations: List[GenerationResponse] = []
    current_production_generation_id: Optional[int] = None
    current_production_generation: Optional[GenerationResponse] = None
    current_research_generation_id: Optional[int] = None
    current_research_generation: Optional[GenerationResponse] = None
    next_planning_generation_id: Optional[int] = None
    next_planning_generation: Optional[GenerationResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Capability Stats ============

class CapabilityStats(BaseModel):
    total_capabilities: int = 0
    high_risk_count: int = 0
    recent_30d_issue_count: int = 0
    p0_p1_capability_count: int = 0
    topic_backed_count: int = 0
    no_owner_count: int = 0


# ============ DeliveryIssue Schemas ============

class DeliveryIssueBase(BaseModel):
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    product_line: str = Field(default="ALL")
    project_name: Optional[str] = None
    priority: str = Field(default="P2")
    status: str = Field(default="NEW")
    owner_id: Optional[int] = None
    impact: Optional[str] = None
    latest_progress: Optional[str] = None
    related_capability_ids: Optional[List[int]] = None
    generation_id: Optional[int] = None


class DeliveryIssueCreate(DeliveryIssueBase):
    pass


class DeliveryIssueUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    product_line: Optional[str] = None
    project_name: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    impact: Optional[str] = None
    latest_progress: Optional[str] = None
    related_capability_ids: Optional[List[int]] = None
    generation_id: Optional[int] = None


class DeliveryIssueResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    product_line: str
    project_name: Optional[str] = None
    priority: str
    status: str
    owner_id: Optional[int] = None
    owner: Optional[UserResponse] = None
    impact: Optional[str] = None
    latest_progress: Optional[str] = None
    related_capability_ids: Optional[List[int]] = None
    generation_id: Optional[int] = None
    generation: Optional[dict] = None
    related_capabilities: Optional[List[CapabilitySummary]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
