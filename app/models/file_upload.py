from sqlalchemy import Column, Integer, String, Text
import json
from app.core.sqlite_database import SqliteBase


class UploadItemsDetails(SqliteBase):
    __tablename__ = "upload_items_details"
    id = Column(String, primary_key=True)
    file_name = Column(Text)
    file_size = Column(Integer)
    file_last_modified = Column(Integer)
    s3 = Column(Text)
    checksum = Column(Text)
    parts = Column(Text)

    def set_s3(self, value):
        self.s3 = json.dumps(value)  # Convert dict to JSON string

    def set_checksum(self, value):
        self.checksum = json.dumps(value)  # Convert dict to JSON string

    def set_parts(self, value):
        self.parts = json.dumps(value)  # Convert dict to JSON string

    def get_s3(self):
        return json.loads(self.s3)  # Convert JSON string back to dict

    def get_checksum(self):
        return json.loads(self.checksum)  # Convert JSON string back to dict

    def get_parts(self):
        return json.loads(self.parts)  # Convert JSON string back to dict

    # def get_s3(self):
    #     if self.s3 is None:
    #         return {}
    #     result = json.loads(self.s3)
    #     return result if result is not None else {}

    # def get_checksum(self):
    #     if self.checksum is None:
    #         return {}
    #     result = json.loads(self.checksum)
    #     return result if result is not None else {}

    # def get_parts(self):
    #     if self.parts is None:
    #         return []
    #     result = json.loads(self.parts)
    #     return result if result is not None else []