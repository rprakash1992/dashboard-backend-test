from sqlalchemy import Column, Text, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.dashboard_database import DashboardBase


class Item(DashboardBase):
    __tablename__ = "items"
    __table_args__ = {"schema": "public"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=func.gen_random_uuid(),
    )
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    image = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    item_type = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True, default=func.now())
    last_modified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    system_key = Column(Text, nullable=True)
