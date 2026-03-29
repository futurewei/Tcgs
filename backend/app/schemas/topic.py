from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from ..models.topic import TopicType, TopicResult, TopicUrgency, StageStatus
from ..models.deliverable import DeliverableType, DeliverableCategory
from ..models.stage_instance import StageInstanceStatus
from .user import UserResponse
from .capacity import SlotType


class SlotRefResponse(BaseModel):
    id: int
    name: str
    type: SlotType
    user_id: Optional[int] = None
    total_capacity: int = 100

    class Config:
        from_attributes = True


class StageTemplateStageResponse(BaseModel):
    id: int
    template_id: int
    name: str
    description: Optional[str] = None
    order: int
    is_terminal: bool
    allow_result: bool
    require_artifact: bool

    class Config:
        from_attributes = True


class StageTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    stages: List[StageTemplateStageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicStageStateResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: int
    stage: StageTemplateStageResponse
    status: StageStatus
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ New Stage Instance Schemas ============

class TechPointContributorResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    contribution: Optional[str] = None
    contribution_percentage: Optional[int] = None

    class Config:
        from_attributes = True


class TechPointResponse(BaseModel):
    id: int
    stage_id: int
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    approach: Optional[str] = None
    conclusion: Optional[str] = None
    status: str
    order: float
    first_author: Optional[UserResponse] = None
    contributors: List[TechPointContributorResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StageInstanceResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    description: Optional[str] = None
    order: float
    is_terminal: bool
    allow_result: bool
    require_artifact: bool
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    objective: Optional[str] = None
    success_criteria: Optional[Any] = None  # JSON array for checklist
    failure_criteria: Optional[Any] = None  # JSON array for checklist
    required_outputs: Optional[Any] = None  # JSON array for output list
    conclusion: Optional[str] = None
    cloned_from_id: Optional[int] = None
    created_by: Optional[UserResponse] = None
    created_at: Optional[datetime] = None
    tech_points: List[TechPointResponse] = []

    class Config:
        from_attributes = True


# ============ Existing Schemas ============

class ArtifactResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: Optional[int] = None
    stage_instance_id: Optional[int] = None
    title: str
    content: Optional[str] = None
    created_by: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: Optional[int] = None
    stage_instance_id: Optional[int] = None
    content: str
    created_by: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BindingResponse(BaseModel):
    id: int
    topic_id: int
    slot_id: int
    slot: Optional[SlotRefResponse] = None
    percentage: int
    is_forced: bool
    is_dri: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Stage Deliverable schemas
class StageDeliverableResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: Optional[int] = None
    stage_instance_id: Optional[int] = None
    tech_point_id: Optional[int] = None
    name: str
    type: DeliverableType
    category: DeliverableCategory = DeliverableCategory.OTHER
    url: str
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_by: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StageDeliverableCreate(BaseModel):
    stage_id: Optional[int] = None
    stage_instance_id: Optional[int] = None
    tech_point_id: Optional[int] = None
    name: str
    type: DeliverableType = DeliverableType.LINK
    category: DeliverableCategory = DeliverableCategory.OTHER
    url: str
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: TopicType
    urgency: TopicUrgency = TopicUrgency.P2


class TopicCreate(TopicBase):
    template_id: int
    requester_name: Optional[str] = None
    requester_user_id: Optional[int] = None
    # 课题背景（WHY）
    background: Optional[str] = None
    # 用户视角目标（WHAT）
    user_goal: Optional[str] = None
    # DRI is now determined by first binding
    initial_dri_slot_id: Optional[int] = None
    initial_dri_percentage: int = 25


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    background: Optional[str] = None
    user_goal: Optional[str] = None
    urgency: Optional[TopicUrgency] = None
    result: Optional[TopicResult] = None
    current_stage_id: Optional[int] = None
    current_stage_instance_id: Optional[int] = None


class TopicResponse(TopicBase):
    id: int
    result: TopicResult
    template_id: Optional[int] = None
    template: Optional[StageTemplateResponse] = None
    current_stage_id: Optional[int] = None
    current_stage_instance_id: Optional[int] = None
    # 课题背景和用户目标
    background: Optional[str] = None
    user_goal: Optional[str] = None
    requester_name: str
    requester_user_id: Optional[int] = None
    requester_user: Optional[UserResponse] = None
    # 旧的阶段状态（兼容）
    stage_states: List[TopicStageStateResponse] = []
    # 新的阶段实例
    stage_instances: List[StageInstanceResponse] = []
    artifacts: List[ArtifactResponse] = []
    reviews: List[ReviewResponse] = []
    bindings: List[BindingResponse] = []
    deliverables: List[StageDeliverableResponse] = []
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None  # 课题关闭时间

    class Config:
        from_attributes = True


class ArtifactCreate(BaseModel):
    topic_id: int
    stage_id: Optional[int] = None
    stage_instance_id: Optional[int] = None
    title: str
    content: Optional[str] = None


class ReviewCreate(BaseModel):
    topic_id: int
    stage_id: Optional[int] = None
    stage_instance_id: Optional[int] = None
    content: str


# Stage action schemas
class StageAdvanceRequest(BaseModel):
    """Request to advance or backward a stage"""
    pass


class ChangeDRIRequest(BaseModel):
    """Request to change the DRI of a topic"""
    new_dri_slot_id: int
