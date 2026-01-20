from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.topic import TopicType, TopicResult, TopicUrgency, StageStatus
from .user import UserResponse

# backend/app/schemas/topic.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
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
    slot: Optional[SlotRefResponse] = None  # ✅  新增：前端 chip 需要
    percentage: int
    is_forced: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: TopicType
    urgency: TopicUrgency = TopicUrgency.P2


class TopicCreate(TopicBase):
    dri_id: int
    template_id: int
    requester_name: Optional[str] = None  # Optional if requester_user_id is provided
    requester_user_id: Optional[int] = None


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[TopicUrgency] = None
    result: Optional[TopicResult] = None
    dri_id: Optional[int] = None
    current_stage_id: Optional[int] = None


class TopicResponse(TopicBase):
    id: int
    result: TopicResult
    dri_id: int
    dri: Optional[UserResponse] = None
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
