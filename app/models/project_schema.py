from sqlalchemy import Column, BigInteger, Text, JSON
from app.core.dashboard_database import DashboardBase


class ProjectSchema(DashboardBase):
    __tablename__ = "project_schemas"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    schema = Column(JSON, nullable=False)
    ui_schema = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)
