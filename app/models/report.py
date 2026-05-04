from sqlalchemy import Column, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class Report(DashboardBase):
    __tablename__ = "reports"
    __table_args__ = {"schema": "public"}

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    project = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        nullable=True,
    )
    template = Column(Text, nullable=True)
    data_values = Column(JSON, nullable=True)
    script = Column(Text, nullable=True)
    views = Column(JSON, nullable=True)
