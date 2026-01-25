from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Artifact(Base):
    """
    笔记/备注模型
    
    支持绑定到：
    - stage_instance（新）
    - stage（旧，兼容）
    """
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # 旧：绑定到模板阶段
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=True)
    # 新：绑定到阶段实例
    stage_instance_id = Column(Integer, ForeignKey("topic_stage_instances.id", ondelete="CASCADE"), nullable=True)
    
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="artifacts")
    stage = relationship("StageTemplateStage", back_populates="artifacts")
    stage_instance = relationship("TopicStageInstance", back_populates="artifacts",
                                  foreign_keys=[stage_instance_id])
    created_by = relationship("User", back_populates="created_artifacts")
    attachments = relationship("Attachment", back_populates="artifact")
