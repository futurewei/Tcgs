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
    """
    课题模型
    
    新增字段：
    - background: 课题背景（WHY - 为什么要做，不做会怎样）
    - user_goal: 用户视角目标（WHAT - 用用户/业务语言描述，禁止纯技术黑话）
    """
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # 课题背景（WHY）
    background = Column(Text, nullable=True)
    # 用户视角目标（WHAT）
    user_goal = Column(Text, nullable=True)
    
    type = Column(Enum(TopicType), nullable=False)
    urgency = Column(Enum(TopicUrgency), default=TopicUrgency.P2)
    result = Column(Enum(TopicResult), default=TopicResult.OPEN)

    # DRI is now determined by binding.is_dri, not this field
    # Keep dri_id for backward compatibility but it's deprecated
    dri_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 模板（用于初始化阶段实例）
    template_id = Column(Integer, ForeignKey("stage_templates.id"), nullable=True)
    # 当前阶段实例（改为引用 stage_instances）
    current_stage_instance_id = Column(Integer, ForeignKey("topic_stage_instances.id", use_alter=True), nullable=True)
    
    # 保留旧字段用于向后兼容
    current_stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=True)

    requester_name = Column(String, nullable=False)
    requester_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)  # 课题关闭时间（result 变为 SUCCESS/UNSOLVABLE 时自动设置）

    # Relationships
    dri = relationship("User", back_populates="dri_topics", foreign_keys=[dri_id])
    requester_user = relationship("User", foreign_keys=[requester_user_id])
    template = relationship("StageTemplate", back_populates="topics")
    current_stage = relationship("StageTemplateStage", foreign_keys=[current_stage_id])
    
    # 新的阶段实例关系
    stage_instances = relationship("TopicStageInstance", back_populates="topic", 
                                   order_by="TopicStageInstance.order",
                                   cascade="all, delete-orphan",
                                   foreign_keys="TopicStageInstance.topic_id")
    current_stage_instance = relationship("TopicStageInstance", 
                                          foreign_keys=[current_stage_instance_id],
                                          post_update=True)
    
    # 旧的阶段状态（保留用于向后兼容）
    stage_states = relationship("TopicStageState", back_populates="topic")
    
    artifacts = relationship("Artifact", back_populates="topic")
    reviews = relationship("ReviewComment", back_populates="topic")
    bindings = relationship("Binding", back_populates="topic", cascade="all, delete-orphan")
    deliverables = relationship("StageDeliverable", back_populates="topic", cascade="all, delete-orphan")
    core_ideas = relationship("CoreIdea", back_populates="topic", cascade="all, delete-orphan",
                              order_by="CoreIdea.created_at.desc()")
    tech_points = relationship("TechPoint", back_populates="topic", cascade="all, delete-orphan",
                               foreign_keys="TechPoint.topic_id", order_by="TechPoint.created_at.desc()")

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
    
    @property
    def active_stage_instance(self):
        """获取当前活跃的阶段实例"""
        if self.current_stage_instance:
            return self.current_stage_instance
        # Fallback: 找第一个 ACTIVE 状态的
        for si in self.stage_instances:
            if si.status.value == 'active':
                return si
        # 再 Fallback: 找第一个 PENDING 状态的
        for si in self.stage_instances:
            if si.status.value == 'pending':
                return si
        return None


class TopicStageState(Base):
    """
    旧的阶段状态模型（保留用于向后兼容）
    新系统使用 TopicStageInstance
    """
    __tablename__ = "topic_stage_states"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=False)
    status = Column(Enum(StageStatus), default=StageStatus.PENDING)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    topic = relationship("Topic", back_populates="stage_states")
    stage = relationship("StageTemplateStage", back_populates="topic_stage_states")
