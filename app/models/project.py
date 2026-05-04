from sqlalchemy import Column, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class Project(DashboardBase):
    __tablename__ = "projects"
    __table_args__ = {"schema": "public"}

    project = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    file = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        nullable=True,
    )
    file_parameters = Column(JSON, nullable=True)
