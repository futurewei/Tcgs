from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class SlotType(str, enum.Enum):
    ALGO = "ALGO"
    EXTERNAL = "EXTERNAL"


class CapacitySlot(Base):
    __tablename__ = "capacity_slots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(SlotType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_capacity = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    bindings = relationship("Binding", back_populates="slot")


class Binding(Base):
    __tablename__ = "bindings"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("capacity_slots.id"), nullable=True)  # 保留向后兼容，新系统用 user_id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 新字段：直接关联用户
    percentage = Column(Integer, nullable=False, default=25)
    is_forced = Column(Boolean, default=False)
    is_dri = Column(Boolean, default=False)  # Mark if this binding is the DRI (first responsible person)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="bindings")
    slot = relationship("CapacitySlot", back_populates="bindings")
    user = relationship("User", foreign_keys=[user_id])
