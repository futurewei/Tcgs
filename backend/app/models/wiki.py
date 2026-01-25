from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, BigInteger
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

    pages = relationship("WikiPage", back_populates="direction")


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id = Column(Integer, primary_key=True, index=True)
    direction_id = Column(Integer, ForeignKey("wiki_directions.id"), nullable=False)
    title = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=True)
    current_revision_id = Column(Integer, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 文章创建者
    
    # 浏览量 - 使用 BigInteger 防止整数溢出
    view_count = Column(BigInteger, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    direction = relationship("WikiDirection", back_populates="pages")
    parent = relationship("WikiPage", remote_side=[id], backref="children")
    revisions = relationship("WikiRevision", back_populates="page", order_by="desc(WikiRevision.version)")
    comments = relationship("WikiComment", back_populates="page", order_by="WikiComment.created_at")
    likes = relationship("WikiLike", back_populates="page")
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    @property
    def like_count(self):
        return len(self.likes) if self.likes else 0


class WikiRevision(Base):
    __tablename__ = "wiki_revisions"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    page = relationship("WikiPage", back_populates="revisions")
    created_by = relationship("User", back_populates="wiki_revisions")


class WikiComment(Base):
    """文档评论"""
    __tablename__ = "wiki_comments"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("wiki_comments.id", ondelete="CASCADE"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    page = relationship("WikiPage", back_populates="comments")
    created_by = relationship("User")
    parent = relationship("WikiComment", remote_side=[id], backref="replies")


class WikiLike(Base):
    """文档点赞（一个用户只能点赞一次）"""
    __tablename__ = "wiki_likes"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    page = relationship("WikiPage", back_populates="likes")
    user = relationship("User")
