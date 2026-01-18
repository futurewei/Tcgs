from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="artifacts")
    stage = relationship("StageTemplateStage", back_populates="artifacts")
    created_by = relationship("User", back_populates="created_artifacts")
    attachments = relationship("Attachment", back_populates="artifact")
