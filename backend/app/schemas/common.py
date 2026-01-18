from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
