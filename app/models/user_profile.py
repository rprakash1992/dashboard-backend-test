from sqlalchemy import Column, Text, TIMESTAMP, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from app.core.dashboard_database import DashboardBase


class GenderType(PyEnum):
    male = "male"
    female = "female"
    other = "other"


class UserProfile(DashboardBase):
    __tablename__ = "user_profiles"
    __table_args__ = {"schema": "public"}

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.items.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    name = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    dob = Column(TIMESTAMP(timezone=True), nullable=True)
    picture = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    gender = Column(Enum(GenderType), nullable=True)
