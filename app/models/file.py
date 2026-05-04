from sqlalchemy import (
    Column, Boolean, Text, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.core.dashboard_database import DashboardBase


class File(DashboardBase):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), ForeignKey('public.items.id',
                ondelete='CASCADE'), primary_key=True, nullable=False)
    url = Column(Text, nullable=False)
    downloader_type = Column(Text, nullable=True)
    downloader_args = Column(JSON, nullable=True)
    cache_state = Column(Text, nullable=True)
    local_cache_file_path = Column(
        Text, nullable=True)
    mime_type = Column(Text, nullable=True)
    is_uploaded = Column(Boolean, nullable=True)
    parent = Column(UUID(as_uuid=True), ForeignKey('public.files.id',
                                                   ondelete='CASCADE'), nullable=True)
