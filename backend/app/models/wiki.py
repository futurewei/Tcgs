from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class WikiDirection(Base):
    __tablename__ = "wiki_directions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    pages = relationship("WikiPage", back_populates="direction")


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id = Column(Integer, primary_key=True, index=True)
    direction_id = Column(Integer, ForeignKey("wiki_directions.id"), nullable=False)
    title = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=True)
    current_revision_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    direction = relationship("WikiDirection", back_populates="pages")
    parent = relationship("WikiPage", remote_side=[id], backref="children")
    revisions = relationship("WikiRevision", back_populates="page", order_by="desc(WikiRevision.version)")


class WikiRevision(Base):
    __tablename__ = "wiki_revisions"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    page = relationship("WikiPage", back_populates="revisions")
    created_by = relationship("User", back_populates="wiki_revisions")
