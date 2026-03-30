from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StageTemplateStageBase(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 0
    is_terminal: bool = Field(default=False, alias="isTerminal")
    allow_result: bool = Field(default=False, alias="allowResult")
    require_artifact: bool = Field(default=False, alias="requireArtifact")
    require_review: bool = Field(default=False, alias="requireReview")

    class Config:
        populate_by_name = True


class StageTemplateStageCreate(StageTemplateStageBase):
    pass


class StageTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None


class StageTemplateCreate(StageTemplateBase):
    stages: List[StageTemplateStageCreate] = []


class StageTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stages: Optional[List[StageTemplateStageCreate]] = None


class StageTemplateStageResponse(BaseModel):
    id: int
    template_id: int
    name: str
    description: Optional[str] = None
    order: int = 0
    is_terminal: bool = False
    allow_result: bool = False
    require_artifact: bool = False
    require_review: bool = False

    class Config:
        from_attributes = True


class StageTemplateResponse(StageTemplateBase):
    id: int
    stages: List[StageTemplateStageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
