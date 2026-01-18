from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .user import UserResponse


class WikiRevisionBase(BaseModel):
    content: str


class WikiRevisionCreate(WikiRevisionBase):
    page_id: int


class WikiRevisionResponse(WikiRevisionBase):
    id: int
    page_id: int
    version: int
    created_by: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WikiPageBase(BaseModel):
    title: str
    parent_id: Optional[int] = None


class WikiPageCreate(WikiPageBase):
    direction_id: int
    content: Optional[str] = None


class WikiPageUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[int] = None


class WikiPageResponse(WikiPageBase):
    id: int
    direction_id: int
    current_revision_id: Optional[int] = None
    current_revision: Optional[WikiRevisionResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WikiDirectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class WikiDirectionCreate(WikiDirectionBase):
    pass


class WikiDirectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


class WikiDirectionResponse(WikiDirectionBase):
    id: int
    pages: List[WikiPageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
