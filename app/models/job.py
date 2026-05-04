from sqlalchemy import Column, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class Job(DashboardBase):
    __tablename__ = "jobs"
    __table_args__ = {"schema": "public"}

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    job_type = Column(Text, nullable=False)
    total_steps = Column(Integer, nullable=True)
    completed_steps = Column(Integer, nullable=True)
    run_id = Column(Text, nullable=True)
