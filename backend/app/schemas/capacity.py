from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.capacity import SlotType
from .user import UserResponse


class BindingBase(BaseModel):
    topic_id: int
    slot_id: int
    percentage: int = 25
    is_forced: bool = False


class BindingCreate(BindingBase):
    pass


class BindingUpdate(BaseModel):
    percentage: Optional[int] = None
    is_forced: Optional[bool] = None


class BindingInSlotResponse(BaseModel):
    id: int
    topic_id: int
    percentage: int
    is_forced: bool

    class Config:
        from_attributes = True


class SlotBase(BaseModel):
    name: str
    type: SlotType
    user_id: Optional[int] = None
    total_capacity: int = 100


class SlotCreate(SlotBase):
    pass


class SlotUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[SlotType] = None
    user_id: Optional[int] = None
    total_capacity: Optional[int] = None


class SlotResponse(SlotBase):
    id: int
    user: Optional[UserResponse] = None
    bindings: List[BindingInSlotResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BindingWithSlotResponse(BindingBase):
    id: int
    slot: Optional[SlotResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
