"""
Core Idea Model - 算法思想演进追踪

每一条 Core Idea 是一个可被审计的认知资产，记录算法研发过程中的关键思想。
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


# 多对多关系表：Core Idea 关联的阶段
idea_stage_association = Table(
    'idea_stage_association',
    Base.metadata,
    Column('idea_id', Integer, ForeignKey('core_ideas.id'), primary_key=True),
    Column('stage_instance_id', Integer, ForeignKey('topic_stage_instances.id'), primary_key=True)
)


# 类型和状态常量
class IdeaType:
    PROBLEM_REDEFINE = "problem_redefine"  # 问题重定义
    ALGORITHM_HYPOTHESIS = "algorithm_hypothesis"  # 算法假设
    MODEL_STRUCTURE = "model_structure"  # 模型结构
    PARAMETER_STRATEGY = "parameter_strategy"  # 参数策略
    DATA_PERSPECTIVE = "data_perspective"  # 数据视角
    ENGINEERING_TRADEOFF = "engineering_tradeoff"  # 工程取舍


class IdeaStatus:
    HYPOTHESIZING = "hypothesizing"  # 假设中
    VERIFIED = "verified"  # 已验证
    REJECTED = "rejected"  # 被否决
    SUPERSEDED = "superseded"  # 被替代


class CoreIdea(Base):
    """算法核心思想"""
    __tablename__ = "core_ideas"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # 基本信息 - 使用字符串类型存储
    title = Column(String(500), nullable=False)  # 一句话概括
    idea_type = Column(String(50), nullable=False)  # 类型
    status = Column(String(50), default=IdeaStatus.HYPOTHESIZING)  # 状态
    
    # 提出人（必须是人）
    proposer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    proposer_name = Column(String(200), nullable=True)  # 存储提出人显示名（Slot 名字）
    
    # 核心内容（四段论）
    idea_body = Column(Text)  # Idea 本体（是什么）
    motivation = Column(Text)  # 出现动机（为什么）
    evidence = Column(Text)  # 关键证据（支撑材料）
    impact = Column(Text)  # 影响与落点
    
    # 被替代时，指向新的 Idea
    superseded_by_id = Column(Integer, ForeignKey("core_ideas.id"), nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    topic = relationship("Topic", back_populates="core_ideas")
    proposer = relationship("User", foreign_keys=[proposer_id])
    superseded_by = relationship("CoreIdea", remote_side=[id], foreign_keys=[superseded_by_id])
    
    # 多对多：关联的阶段
    related_stages = relationship(
        "TopicStageInstance",
        secondary=idea_stage_association,
        backref="related_ideas"
    )
