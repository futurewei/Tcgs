from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    REVIEWER = "REVIEWER"
    EXTERNAL = "EXTERNAL"
    CUSTOMER = "CUSTOMER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    dri_topics = relationship("Topic", back_populates="dri", foreign_keys="Topic.dri_id")
    created_artifacts = relationship("Artifact", back_populates="created_by")
    created_reviews = relationship("ReviewComment", back_populates="created_by")
    wiki_revisions = relationship("WikiRevision", back_populates="created_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    created_deliverables = relationship("StageDeliverable", back_populates="created_by")
