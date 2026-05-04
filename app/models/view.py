from sqlalchemy import Column, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class View(DashboardBase):
    __tablename__ = "views"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=True)
    owner = Column(
        UUID(as_uuid=True),
        ForeignKey("public.user_profiles.id", ondelete="CASCADE"),
        nullable=True,
    )
    item_type = Column(Text, nullable=True)
    view_as = Column(Text, nullable=True)
    filters = Column(JSON, nullable=True)
    group_by = Column(Text, nullable=True)
    sort_by = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
