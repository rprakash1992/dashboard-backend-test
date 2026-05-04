from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class Relation(DashboardBase):
    __tablename__ = "relations"
    __table_args__ = (
        PrimaryKeyConstraint("source_id", "target_id"),
        {"schema": "public"},
    )

    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    target_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    relation = Column(Text, nullable=False)
