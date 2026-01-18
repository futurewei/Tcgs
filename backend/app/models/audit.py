from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class AuditAction(str, enum.Enum):
    TOPIC_CREATE = "TOPIC_CREATE"
    TOPIC_UPDATE = "TOPIC_UPDATE"
    TOPIC_DELETE = "TOPIC_DELETE"
    DRI_CHANGE = "DRI_CHANGE"
    RESULT_CHANGE = "RESULT_CHANGE"
    STAGE_CHANGE = "STAGE_CHANGE"
    SLOT_CREATE = "SLOT_CREATE"
    SLOT_UPDATE = "SLOT_UPDATE"
    SLOT_DELETE = "SLOT_DELETE"
    BINDING_CREATE = "BINDING_CREATE"
    BINDING_UPDATE = "BINDING_UPDATE"
    BINDING_DELETE = "BINDING_DELETE"
    BINDING_FORCE = "BINDING_FORCE"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    WIKI_CREATE = "WIKI_CREATE"
    WIKI_UPDATE = "WIKI_UPDATE"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")
