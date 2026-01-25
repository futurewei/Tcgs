"""
Topic Stage Instance Model - 课题阶段实例

核心设计理念：
1. Stage 是一等公民 - 每个 Stage 是独立实例，可复制、可拖拽
2. 技术点(TechPoint)绑定 Stage - 而非 Topic
3. 交付物绑定 Stage/TechPoint - 形成可追溯的证据链
4. 第一作者机制 - 防止抢功，明确贡献
5. 验收标准 checklist - 量化、可验证
6. 风险/阻塞追踪 - 结构化记录
"""
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class StageInstanceStatus(str, enum.Enum):
    """阶段实例状态"""
    PENDING = "pending"      # 待开始
    ACTIVE = "active"        # 进行中
    DONE = "done"            # 已完成
    SKIPPED = "skipped"      # 跳过
    FAILED = "failed"        # 失败（留痕）


class RiskLevel(str, enum.Enum):
    """风险等级"""
    RED = "red"        # 高风险/阻塞
    YELLOW = "yellow"  # 中风险/可能阻塞
    GREEN = "green"    # 低风险/正常


class TopicStageInstance(Base):
    """
    课题阶段实例
    
    与 StageTemplateStage 的区别：
    - StageTemplateStage 是模板定义（全局共享）
    - TopicStageInstance 是实例（每个课题独立）
    
    支持：
    - 拖拽重排（order 字段）
    - 复制（用于算法分叉，cloned_from_id）
    - 插入新阶段
    - 同名阶段可多次出现
    """
    __tablename__ = "topic_stage_instances"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    
    # 阶段基本信息（从模板复制或手动创建）
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Float, nullable=False, default=0)  # 使用 Float 便于插入（如 1.5 在 1 和 2 之间）
    
    # 阶段配置
    is_terminal = Column(Boolean, default=False)      # 是否是终止阶段
    allow_result = Column(Boolean, default=False)     # 是否允许设置结果
    require_artifact = Column(Boolean, default=False) # 是否需要交付物
    
    # 阶段状态
    status = Column(Enum(StageInstanceStatus), default=StageInstanceStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============ 完成确认信息 ============
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 完成确认人
    completion_note = Column(Text, nullable=True)  # 完成说明
    remaining_issues = Column(Text, nullable=True)  # 遗留问题/风险
    
    # ============ 验收标准（结构化） ============
    # 阶段目标（一句话）
    objective = Column(Text, nullable=True)
    # 成功判据 checklist（JSON 数组）
    # 格式: [{"id": "uuid", "text": "xxx", "checked": false, "required": true}, ...]
    success_criteria = Column(JSON, nullable=True)
    # 失败判据 checklist（JSON 数组）
    # 格式: [{"id": "uuid", "text": "xxx", "checked": false}, ...]
    failure_criteria = Column(JSON, nullable=True)
    # 输出物列表（JSON 数组）
    # 格式: [{"id": "uuid", "name": "xxx", "required": true, "delivered": false}, ...]
    required_outputs = Column(JSON, nullable=True)
    # 阶段结论
    conclusion = Column(Text, nullable=True)
    
    # 追溯信息
    cloned_from_id = Column(Integer, ForeignKey("topic_stage_instances.id"), nullable=True)
    template_stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="stage_instances", foreign_keys=[topic_id])
    cloned_from = relationship("TopicStageInstance", remote_side=[id], backref="clones", foreign_keys=[cloned_from_id])
    template_stage = relationship("StageTemplateStage")
    created_by = relationship("User", foreign_keys=[created_by_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    
    # 技术点
    tech_points = relationship("TechPoint", back_populates="stage", cascade="all, delete-orphan", order_by="TechPoint.order")
    
    # 交付物（直接绑定到阶段的）
    deliverables = relationship("StageDeliverable", back_populates="stage_instance", 
                               foreign_keys="StageDeliverable.stage_instance_id",
                               cascade="all, delete-orphan")
    
    # 笔记和评审
    artifacts = relationship("Artifact", back_populates="stage_instance",
                            foreign_keys="Artifact.stage_instance_id")
    reviews = relationship("ReviewComment", back_populates="stage_instance",
                          foreign_keys="ReviewComment.stage_instance_id")


class TechPoint(Base):
    """
    技术点/算法思想
    
    核心设计：
    - 可以绑定到 Stage 或直接绑定 Topic
    - 必须有唯一的第一作者（提出人）
    - 其他贡献者是可选的
    - 所有交付件可以绑定到技术点
    """
    __tablename__ = "tech_points"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("topic_stage_instances.id", ondelete="CASCADE"), nullable=True)  # 可选
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True)  # 直接关联课题
    
    # 技术点基本信息
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Float, nullable=False, default=0)
    
    # 技术假设
    hypothesis = Column(Text, nullable=True)
    # 技术方案
    approach = Column(Text, nullable=True)
    # 结论
    conclusion = Column(Text, nullable=True)
    
    # 第一作者/提出人（必填，唯一）
    first_author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 状态
    status = Column(String, default="draft")  # draft, in_progress, completed, abandoned
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    stage = relationship("TopicStageInstance", back_populates="tech_points")
    topic = relationship("Topic", back_populates="tech_points")
    first_author = relationship("User", foreign_keys=[first_author_id])
    
    # 其他贡献者
    contributors = relationship("TechPointContributor", back_populates="tech_point", cascade="all, delete-orphan")
    
    # 绑定到此技术点的交付物
    deliverables = relationship("StageDeliverable", back_populates="tech_point",
                               foreign_keys="StageDeliverable.tech_point_id")


class TechPointContributor(Base):
    """
    技术点贡献者（除第一作者外的其他贡献者）
    """
    __tablename__ = "tech_point_contributors"

    id = Column(Integer, primary_key=True, index=True)
    tech_point_id = Column(Integer, ForeignKey("tech_points.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 贡献描述
    contribution = Column(Text, nullable=True)
    # 贡献比例（可选，用于量化）
    contribution_percentage = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tech_point = relationship("TechPoint", back_populates="contributors")
    user = relationship("User")


class TopicRisk(Base):
    """
    课题风险/阻塞追踪
    
    结构化记录：
    - 风险等级（R/Y/G）
    - 阻塞方
    - 阻塞描述
    - 预计解除时间
    - Owner
    """
    __tablename__ = "topic_risks"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    stage_instance_id = Column(Integer, ForeignKey("topic_stage_instances.id", ondelete="SET NULL"), nullable=True)
    
    # 风险等级
    level = Column(Enum(RiskLevel), nullable=False, default=RiskLevel.YELLOW)
    
    # 阻塞方/来源
    blocker_type = Column(String, nullable=False)  # 需求, 平台, 供应商, 测试, 车队资源, 其他
    blocker_name = Column(String, nullable=True)   # 具体名称
    
    # 描述
    description = Column(Text, nullable=False)
    
    # 预计解除时间
    expected_resolve_date = Column(DateTime(timezone=True), nullable=True)
    
    # Owner (负责跟进的人)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 状态
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topic = relationship("Topic", backref="risks")
    stage_instance = relationship("TopicStageInstance", backref="risks")
    owner = relationship("User", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
