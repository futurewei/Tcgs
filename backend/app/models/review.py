from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stage_template_stages.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="reviews")
    stage = relationship("StageTemplateStage", back_populates="reviews")
    created_by = relationship("User", back_populates="created_reviews")
