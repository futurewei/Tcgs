from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class DeliverableType(str, enum.Enum):
    FILE = "file"
    LINK = "link"


class StageDeliverable(Base):
    """
    Stage-level deliverables/attachments.
    Each stage can have multiple deliverables representing outputs/deliverables for that stage.
    """
    __tablename__ = "stage_deliverables"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=False)
    
    # Deliverable info
    name = Column(String, nullable=False)  # Display name
    type = Column(Enum(DeliverableType), default=DeliverableType.LINK, nullable=False)
    url = Column(String, nullable=False)  # URL for link type, or file storage path for file type
    description = Column(Text, nullable=True)  # Optional description
    
    # File metadata (for file type)
    file_name = Column(String, nullable=True)  # Original filename
    file_size = Column(Integer, nullable=True)  # File size in bytes
    mime_type = Column(String, nullable=True)  # MIME type
    
    # Audit
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="deliverables")
    stage = relationship("StageTemplateStage", back_populates="deliverables")
    created_by = relationship("User", back_populates="created_deliverables")
