from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    url = Column(String, nullable=False)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    artifact = relationship("Artifact", back_populates="attachments")
