from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.dashboard_database import DashboardBase


class Role(DashboardBase):
    __tablename__ = 'roles'
    __table_args__ = (
        PrimaryKeyConstraint('id', 'item_type', "action"),
        {'schema': 'public'}
    )

    id = Column(UUID(as_uuid=True), ForeignKey(
        'public.items.id', ondelete='CASCADE'), nullable=False)
    item_type = Column(Text, nullable=True)
    action = Column(Text, nullable=True)
    sections = Column(ARRAY(Text), nullable=True)
