from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .user import UserResponse


class WikiRevisionBase(BaseModel):
    content: str


class WikiRevisionCreate(WikiRevisionBase):
    page_id: Optional[int] = None  # 可选，因为 URL 中已有 page_id


class WikiRevisionResponse(WikiRevisionBase):
    id: int
    page_id: int
    version: int
    created_by: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Comments (评论) ============

class WikiCommentBase(BaseModel):
    content: str


class WikiCommentCreate(WikiCommentBase):
    parent_id: Optional[int] = None  # 回复的父评论 ID


class WikiCommentResponse(WikiCommentBase):
    id: int
    page_id: int
    parent_id: Optional[int] = None
    created_by: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    replies: List["WikiCommentResponse"] = []

    class Config:
        from_attributes = True


# ============ Pages ============

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
    created_by_id: Optional[int] = None
    created_by: Optional[UserResponse] = None
    view_count: int = 0
    like_count: int = 0
    user_liked: bool = False
    comments: List[WikiCommentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Directions ============

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


# 解决循环引用
WikiCommentResponse.model_rebuild()
