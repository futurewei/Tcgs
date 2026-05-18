"""Capability model for algorithm capability asset management."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum, ARRAY, Table, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class ProductLine(str, enum.Enum):
    HUD = "HUD"
    LIGHT = "LIGHT"
    PROJECTION = "PROJECTION"
    ALL = "ALL"


class CapabilityType(str, enum.Enum):
    DISPLAY_ALGO = "DISPLAY_ALGO"
    SPATIAL_STABILITY = "SPATIAL_STABILITY"
    PERCEPTION_FUSION = "PERCEPTION_FUSION"
    PARAM_GENERALIZATION = "PARAM_GENERALIZATION"
    REALTIME_PERFORMANCE = "REALTIME_PERFORMANCE"
    CALIBRATION_CONSISTENCY = "CALIBRATION_CONSISTENCY"
    ENGINEERING_FRAMEWORK = "ENGINEERING_FRAMEWORK"
    INTERACTION_EXPRESSION = "INTERACTION_EXPRESSION"


class MaturityLevel(str, enum.Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


class RiskStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    HIGH_RISK = "HIGH_RISK"


class GenerationStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    ENGINEERING = "ENGINEERING"
    PILOT = "PILOT"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


# ============================================================
# Capability Taxonomy (Cascading category tree)
# ============================================================

class CapabilityCategory(Base):
    """Hierarchical capability taxonomy tree."""

    __tablename__ = "capability_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("capability_categories.id"), nullable=True, index=True)
    display_order = Column(Integer, nullable=False, default=0)

    parent = relationship("CapabilityCategory", remote_side=[id], back_populates="children")
    children = relationship("CapabilityCategory", back_populates="parent", order_by="CapabilityCategory.display_order")
    capabilities = relationship("Capability", back_populates="category")


# ============================================================
# Association tables
# ============================================================

capability_topic_association = Table(
    "capability_topics",
    Base.metadata,
    Column("capability_id", Integer, ForeignKey("capabilities.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)

capability_issue_association = Table(
    "capability_issues",
    Base.metadata,
    Column("capability_id", Integer, ForeignKey("capabilities.id"), primary_key=True),
    Column("issue_id", Integer, ForeignKey("delivery_issues.id"), primary_key=True),
)

generation_topic_association = Table(
    "generation_topics",
    Base.metadata,
    Column("generation_id", Integer, ForeignKey("capability_generations.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)

generation_issue_association = Table(
    "generation_issues",
    Base.metadata,
    Column("generation_id", Integer, ForeignKey("capability_generations.id"), primary_key=True),
    Column("issue_id", Integer, ForeignKey("delivery_issues.id"), primary_key=True),
)


# ============================================================
# CapabilityGeneration
# ============================================================

class CapabilityGeneration(Base):
    """A specific generation/version of a Capability."""

    __tablename__ = "capability_generations"

    id = Column(Integer, primary_key=True, index=True)
    capability_id = Column(Integer, ForeignKey("capabilities.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    generation_code = Column(String(20), nullable=False)
    version = Column(String(50), nullable=True)

    status = Column(Enum(GenerationStatus), nullable=False, default=GenerationStatus.PLANNING, index=True)
    maturity_level = Column(Enum(MaturityLevel), nullable=False, default=MaturityLevel.L1, index=True)

    description = Column(Text, nullable=True)
    key_improvements = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    start_date = Column(Date, nullable=True)
    target_date = Column(Date, nullable=True)
    release_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    capability = relationship("Capability", back_populates="generations", foreign_keys=[capability_id])
    owner = relationship("User", foreign_keys=[owner_id])

    related_topics = relationship(
        "Topic",
        secondary=generation_topic_association,
        backref="related_generations",
    )

    related_issues = relationship(
        "DeliveryIssue",
        secondary=generation_issue_association,
        backref="related_generations",
    )


# ============================================================
# Capability
# ============================================================

class Capability(Base):
    """Core model for algorithm capability asset management."""

    __tablename__ = "capabilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    category_id = Column(Integer, ForeignKey("capability_categories.id"), nullable=True, index=True)

    product_line = Column(Enum(ProductLine), nullable=False, default=ProductLine.ALL, index=True)
    capability_type = Column(Enum(CapabilityType), nullable=False, index=True)
    maturity_level = Column(Enum(MaturityLevel), nullable=False, default=MaturityLevel.L1, index=True)
    risk_status = Column(Enum(RiskStatus), nullable=False, default=RiskStatus.NORMAL, index=True)

    maturity_evidence = Column(Text, nullable=True)
    capability_gaps = Column(Text, nullable=True)
    gap_actions = Column(Text, nullable=True)
    knowledge_records = Column(Text, nullable=True)
    knowledge_wiki_page_ids = Column(String(500), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    backup_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    responsibility_field_id = Column(Integer, nullable=True)
    responsibility_field_name = Column(String(200), nullable=True)

    support_member_ids = Column(String(500), nullable=True)
    hr_risk_note = Column(Text, nullable=True)
    care_scope = Column(Text, nullable=True)

    tags = Column(ARRAY(String), nullable=True, default=[])

    # Generation pointers
    current_production_generation_id = Column(Integer, ForeignKey("capability_generations.id"), nullable=True)
    current_research_generation_id = Column(Integer, ForeignKey("capability_generations.id"), nullable=True)
    next_planning_generation_id = Column(Integer, ForeignKey("capability_generations.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("CapabilityCategory", back_populates="capabilities")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_capabilities")
    backup_owner = relationship("User", foreign_keys=[backup_owner_id], backref="backup_capabilities")

    generations = relationship("CapabilityGeneration", back_populates="capability", order_by="CapabilityGeneration.created_at",
                               foreign_keys="[CapabilityGeneration.capability_id]")

    current_production_generation = relationship("CapabilityGeneration", foreign_keys=[current_production_generation_id],
                                                  post_update=True)
    current_research_generation = relationship("CapabilityGeneration", foreign_keys=[current_research_generation_id],
                                                post_update=True)
    next_planning_generation = relationship("CapabilityGeneration", foreign_keys=[next_planning_generation_id],
                                             post_update=True)

    related_topics = relationship(
        "Topic",
        secondary=capability_topic_association,
        backref="related_capabilities",
    )

    related_issues = relationship(
        "DeliveryIssue",
        secondary=capability_issue_association,
        backref="related_capabilities",
    )


class IssuePriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class IssueStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    FIXING = "FIXING"
    VERIFYING = "VERIFYING"
    CLOSED = "CLOSED"


class DeliveryIssue(Base):
    """Model for delivery-focused issues that may expose capability gaps."""

    __tablename__ = "delivery_issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    product_line = Column(Enum(ProductLine), nullable=False, index=True)
    project_name = Column(String(200), nullable=True)
    priority = Column(Enum(IssuePriority), nullable=False, default=IssuePriority.P2, index=True)
    status = Column(Enum(IssueStatus), nullable=False, default=IssueStatus.NEW, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    impact = Column(Text, nullable=True)
    latest_progress = Column(Text, nullable=True)
    generation_id = Column(Integer, ForeignKey("capability_generations.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_id], backref="owned_issues")
    generation = relationship("CapabilityGeneration", foreign_keys=[generation_id], backref="delivery_issues")
