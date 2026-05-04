from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.dashboard_database import DashboardBase


class UserFlow(DashboardBase):
    __tablename__ = "user_flows"
    __table_args__ = {"schema": "public"}

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.files.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    s3_key = Column(Text, nullable=False)
    flow_function_name = Column(Text, nullable=False)
    deployment_id = Column(UUID(as_uuid=True), nullable=False)
    deployment_name = Column(Text, nullable=False)
    flow_id = Column(UUID(as_uuid=True), nullable=False)
    parameter_schema = Column(JSONB, nullable=True)
