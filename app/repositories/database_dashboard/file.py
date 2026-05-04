from sqlalchemy.orm import Session
from typing import List, Any, Optional
from app.schemas.file import FileSchema
from app.models.file import File
from app.repositories.database_dashboard.base import BaseRepository


class FileRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_file_by_id(self, file_id: str) -> Optional[FileSchema]:
        file = self.db.query(File).filter(File.id == file_id).first()
        return FileSchema.model_validate(file) if file else None

    def get_files_by_ids(self, file_ids: List[str]) -> List[FileSchema]:
        files = self.db.query(File).filter(File.id.in_(file_ids)).all()
        return [FileSchema.model_validate(f) for f in files]

    def get_files_by_field_and_name_field_val(
        self,
        field_name: str,
        field_val: Any,
    ) -> List[FileSchema]:
        if not hasattr(File, field_name):
            raise ValueError(f"Invalid field: {field_name}")

        files = self.db.query(File).filter(getattr(File, field_name) == field_val).all()
        return [FileSchema.model_validate(f) for f in files]

    def get_files_in_ids_and_field_name_and_field_val(
        self,
        ids: List[str],
        field_name: str,
        field_val: Any,
    ) -> List[FileSchema]:
        files = (
            self.db.query(File)
            .filter(File.id.in_(ids), getattr(File, field_name) == field_val)
            .all()
        )
        return [FileSchema.model_validate(f) for f in files]

    def update_file_field_by_id(
        self, id: str, field_name: str, field_val: Any
    ) -> FileSchema:
        self.db.query(File).filter(
            File.id == id,
        ).update({field_name: field_val}, synchronize_session=False)
        self.db.commit()
        file = self.db.query(File).filter(File.id == id).first()
        return FileSchema.model_validate(file)

    def update_file_record(self, file: FileSchema) -> Optional[FileSchema]:
        self.db.query(File).filter(
            File.id == file.id,
        ).update(file.model_dump(exclude_unset=True), synchronize_session=False)
        self.db.commit()
        updated = self.db.query(File).filter(File.id == file.id).first()
        return FileSchema.model_validate(updated) if updated else None

    def insert_files(self, new_files: List[FileSchema]) -> List[FileSchema]:
        files = [
            File(
                id=new_file.id,
                url=new_file.url,
                downloader_type=new_file.downloader_type,
                downloader_args=new_file.downloader_args,
                cache_state=new_file.cache_state,
                local_cache_file_path=new_file.local_cache_file_path,
                mime_type=new_file.mime_type,
                is_uploaded=new_file.is_uploaded,
                parent=new_file.parent,
            )
            for new_file in new_files
        ]
        self.db.add_all(files)
        self.db.commit()
        for file in files:
            self.db.refresh(file)
        return [FileSchema.model_validate(f) for f in files]
