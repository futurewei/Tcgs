from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.capacity import SlotType
from .user import UserResponse


class BindingBase(BaseModel):
    # 兼容 topicId / topic_id
    topic_id: int = Field(..., alias="topicId")

    # 兼容 slotId / slot_id（旧链路）
    slot_id: Optional[int] = Field(None, alias="slotId")

    # 兼容 userId / user_id（新链路）
    user_id: Optional[int] = Field(None, alias="userId")

    percentage: int = 25

    # 兼容 isForced / is_forced
    is_forced: bool = Field(False, alias="isForced")

    class Config:
        # 允许用字段名或别名来填充
        allow_population_by_field_name = True
        # pydantic v2 / v1 都尽量兼容
        populate_by_name = True


class BindingCreate(BindingBase):
    # 兼容 isDri / is_dri
    is_dri: Optional[bool] = Field(None, alias="isDri")


class BindingUpdate(BaseModel):
    percentage: Optional[int] = None
    is_forced: Optional[bool] = Field(None, alias="isForced")
    is_dri: Optional[bool] = Field(None, alias="isDri")

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


class BindingInSlotResponse(BaseModel):
    id: int
    topic_id: int
    percentage: int
    is_forced: bool
    is_dri: bool = False

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


class BindingWithSlotResponse(BaseModel):
    id: int
    topic_id: int

    # ✅ 放宽：防止某些历史数据/异常返回炸掉
    slot_id: Optional[int] = None

    user_id: Optional[int] = None
    percentage: int
    is_forced: bool
    is_dri: bool = False
    slot: Optional[SlotResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
