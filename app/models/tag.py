from sqlalchemy import Column, Text, BigInteger
from app.core.dashboard_database import DashboardBase


class Tag(DashboardBase):
    __tablename__ = "tags"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, primary_key=True, nullable=False)
    description = Column(Text, nullable=True)
