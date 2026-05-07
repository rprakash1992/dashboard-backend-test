from sqlalchemy import Column, Text, Boolean, ForeignKey
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class Role(DashboardBase):
    __tablename__ = "roles"
    __table_args__ = (
        PrimaryKeyConstraint("id", "item_type", "scope", "field"),
        {"schema": "public"},
    )

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_type = Column(Text, nullable=False)
    scope = Column(Text, nullable=False)
    field = Column(Text, nullable=False)
    can_create = Column(Boolean, nullable=False, default=False)
    can_read = Column(Boolean, nullable=False, default=False)
    can_update = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)
