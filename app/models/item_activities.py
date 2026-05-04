from sqlalchemy import Column, BigInteger, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.dashboard_database import DashboardBase


class ItemActivity(DashboardBase):
    __tablename__ = "item_activities"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        nullable=False,
    )
    prev_action = Column(BigInteger, nullable=True)
    content = Column(Text, nullable=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    timestamp = Column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    activity_type = Column(Text, nullable=True)
