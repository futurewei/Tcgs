"""Algo Delivery model for tracking algorithm capability deliveries."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class AlgoDelivery(Base):
    """Model for algorithm capability monthly deliveries."""

    __tablename__ = "algo_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(7), nullable=False, index=True)  # Format: "YYYY-MM"
    capability_name = Column(String(200), nullable=False)
    archive_url = Column(String(500), nullable=True)
    upgrade_description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)

    # Owner (responsible person)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Delivery status and tracking
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    delivered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Creator tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_deliveries")
    delivered_by = relationship("User", foreign_keys=[delivered_by_id], backref="confirmed_deliveries")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_deliveries")
