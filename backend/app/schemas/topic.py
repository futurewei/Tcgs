from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.topic import TopicType, TopicResult, TopicUrgency, StageStatus
from ..models.deliverable import DeliverableType
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


class ArtifactResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: int
    title: str
    content: Optional[str] = None
    created_by: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: int
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
    is_dri: bool = False  # NEW: indicates if this is the DRI binding
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Stage Deliverable schemas
class StageDeliverableResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: int
    name: str
    type: DeliverableType
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
    stage_id: int
    name: str
    type: DeliverableType = DeliverableType.LINK
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
    # DRI is now determined by first binding, not a separate field
    initial_dri_slot_id: Optional[int] = None  # Optional: first slot to bind as DRI
    initial_dri_percentage: int = 25  # Default percentage for DRI binding


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[TopicUrgency] = None
    result: Optional[TopicResult] = None
    current_stage_id: Optional[int] = None


class TopicResponse(TopicBase):
    id: int
    result: TopicResult
    template_id: int
    template: Optional[StageTemplateResponse] = None
    current_stage_id: Optional[int] = None
    requester_name: str
    requester_user_id: Optional[int] = None
    requester_user: Optional[UserResponse] = None
    stage_states: List[TopicStageStateResponse] = []
    artifacts: List[ArtifactResponse] = []
    reviews: List[ReviewResponse] = []
    bindings: List[BindingResponse] = []
    deliverables: List[StageDeliverableResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactCreate(BaseModel):
    topic_id: int
    stage_id: int
    title: str
    content: Optional[str] = None


class ReviewCreate(BaseModel):
    topic_id: int
    stage_id: int
    content: str


# Stage action schemas
class StageAdvanceRequest(BaseModel):
    """Request to advance or backward a stage"""
    pass  # No body needed, stage_id comes from URL


class ChangeDRIRequest(BaseModel):
    """Request to change the DRI of a topic"""
    new_dri_slot_id: int  # The slot that should become the new DRI
