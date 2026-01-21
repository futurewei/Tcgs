from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class TopicType(str, enum.Enum):
    UNCERTAINTY = "UNCERTAINTY"
    EVOLUTION = "EVOLUTION"


class TopicResult(str, enum.Enum):
    OPEN = "OPEN"
    SUCCESS = "SUCCESS"
    UNSOLVABLE = "UNSOLVABLE"


class TopicUrgency(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class StageStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(TopicType), nullable=False)
    urgency = Column(Enum(TopicUrgency), default=TopicUrgency.P2)
    result = Column(Enum(TopicResult), default=TopicResult.OPEN)

    # DRI is now determined by binding.is_dri, not this field
    # Keep dri_id for backward compatibility but it's deprecated
    dri_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    template_id = Column(Integer, ForeignKey("stage_templates.id"), nullable=False)
    current_stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=True)

    requester_name = Column(String, nullable=False)
    requester_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    dri = relationship("User", back_populates="dri_topics", foreign_keys=[dri_id])
    requester_user = relationship("User", foreign_keys=[requester_user_id])
    template = relationship("StageTemplate", back_populates="topics")
    current_stage = relationship("StageTemplateStage", foreign_keys=[current_stage_id])
    stage_states = relationship("TopicStageState", back_populates="topic")
    artifacts = relationship("Artifact", back_populates="topic")
    reviews = relationship("ReviewComment", back_populates="topic")
    bindings = relationship("Binding", back_populates="topic", cascade="all, delete-orphan")
    deliverables = relationship("StageDeliverable", back_populates="topic", cascade="all, delete-orphan")

    @property
    def dri_binding(self):
        """Get the DRI binding (the binding with is_dri=True)"""
        for b in self.bindings:
            if b.is_dri:
                return b
        # Fallback: return first binding if no explicit DRI
        return self.bindings[0] if self.bindings else None

    @property
    def dri_slot(self):
        """Get the DRI's slot"""
        dri_b = self.dri_binding
        return dri_b.slot if dri_b else None


class TopicStageState(Base):
    __tablename__ = "topic_stage_states"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=False)
    status = Column(Enum(StageStatus), default=StageStatus.PENDING)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    topic = relationship("Topic", back_populates="stage_states")
    stage = relationship("StageTemplateStage", back_populates="topic_stage_states")
