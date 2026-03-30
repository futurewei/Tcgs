from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class StageTemplate(Base):
    __tablename__ = "stage_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    stages = relationship("StageTemplateStage", back_populates="template", order_by="StageTemplateStage.order")
    topics = relationship("Topic", back_populates="template")


class StageTemplateStage(Base):
    __tablename__ = "stage_template_stages"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("stage_templates.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    is_terminal = Column(Boolean, default=False)
    allow_result = Column(Boolean, default=False)
    require_artifact = Column(Boolean, default=False)
    require_review = Column(Boolean, default=False)

    # Relationships
    template = relationship("StageTemplate", back_populates="stages")
    topic_stage_states = relationship("TopicStageState", back_populates="stage")
    artifacts = relationship("Artifact", back_populates="stage")
    reviews = relationship("ReviewComment", back_populates="stage")
    deliverables = relationship("StageDeliverable", back_populates="stage")
