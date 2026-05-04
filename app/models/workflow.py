from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.dashboard_database import DashboardBase


class Workflow(DashboardBase):
    __tablename__ = "workflows"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    s3_key = Column(Text, nullable=True)
    flow_function_name = Column(Text, nullable=True)
    deployment_id = Column(UUID(as_uuid=True), nullable=True)
    deployment_name = Column(Text, nullable=True)
    flow_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Text, nullable=True)
    is_valid = Column(Boolean, nullable=True)
    parameter_schema = Column(JSONB, nullable=True)
