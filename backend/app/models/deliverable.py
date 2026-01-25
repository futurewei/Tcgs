from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class DeliverableType(str, enum.Enum):
    FILE = "file"
    LINK = "link"


class DeliverableCategory(str, enum.Enum):
    """交付物分类"""
    DEMO = "demo"           # 演示
    LOG = "log"             # 日志/数据
    CODE = "code"           # 代码
    REPORT = "report"       # 报告/文档
    DESIGN = "design"       # 设计文档
    TEST = "test"           # 测试结果
    OTHER = "other"         # 其他


class StageDeliverable(Base):
    """
    交付物模型
    
    核心变化：
    - 可以绑定到 stage_instance（新）或 stage（旧，兼容）
    - 可以绑定到 tech_point（可选）
    - 自动记录作者和时间戳
    - 支持分类
    """
    __tablename__ = "stage_deliverables"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    
    # 旧：绑定到模板阶段（保留用于向后兼容）
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=True)
    
    # 新：绑定到阶段实例
    stage_instance_id = Column(Integer, ForeignKey("topic_stage_instances.id", ondelete="CASCADE"), nullable=True)
    
    # 新：可选绑定到技术点
    tech_point_id = Column(Integer, ForeignKey("tech_points.id", ondelete="SET NULL"), nullable=True)
    
    # Deliverable info
    name = Column(String, nullable=False)  # Display name
    type = Column(Enum(DeliverableType), default=DeliverableType.LINK, nullable=False)
    category = Column(Enum(DeliverableCategory), default=DeliverableCategory.OTHER, nullable=False)
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
    stage_instance = relationship("TopicStageInstance", back_populates="deliverables",
                                  foreign_keys=[stage_instance_id])
    tech_point = relationship("TechPoint", back_populates="deliverables",
                             foreign_keys=[tech_point_id])
    created_by = relationship("User", back_populates="created_deliverables")
