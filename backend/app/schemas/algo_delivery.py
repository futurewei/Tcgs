"""Schema definitions for AlgoDelivery API."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from .user import UserResponse


class AlgoDeliveryBase(BaseModel):
    """Base schema for AlgoDelivery."""
    month: str = Field(..., description="Month in YYYY-MM format")
    capability_name: str = Field(..., max_length=200)
    archive_url: Optional[str] = Field(None, max_length=500)
    upgrade_description: Optional[str] = None
    video_url: Optional[str] = Field(None, max_length=500)
    owner_id: int


class AlgoDeliveryCreate(AlgoDeliveryBase):
    """Schema for creating a new AlgoDelivery."""
    pass


class AlgoDeliveryUpdate(BaseModel):
    """Schema for updating an AlgoDelivery."""
    capability_name: Optional[str] = Field(None, max_length=200)
    archive_url: Optional[str] = Field(None, max_length=500)
    upgrade_description: Optional[str] = None
    video_url: Optional[str] = Field(None, max_length=500)
    owner_id: Optional[int] = None
    delivered: Optional[bool] = None  # Mark as delivered


class AlgoDeliveryResponse(BaseModel):
    """Schema for AlgoDelivery response."""
    id: int
    month: str
    capability_name: str
    archive_url: Optional[str] = None
    upgrade_description: Optional[str] = None
    video_url: Optional[str] = None
    owner_id: int
    owner: Optional[UserResponse] = None
    delivered: bool
    delivered_at: Optional[datetime] = None
    delivered_by_id: Optional[int] = None
    delivered_by: Optional[UserResponse] = None
    created_by_id: int
    created_by: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
