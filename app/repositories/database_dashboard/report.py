from sqlalchemy.orm import Session
from typing import List, Any
import json
from app.repositories.database_dashboard.base import BaseRepository
from app.models.report import Report
from app.schemas.report import ReportSchema


class ReportRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_reports_by_ids(self, ids: List[str]) -> List[ReportSchema]:
        reports = (
            self.db.query(Report)
            .filter(
                Report.id.in_(ids),
            )
            .all()
        )
        return [ReportSchema.model_validate(f) for f in reports]

    def update_report(self, id: str, field_name: str, field_val: Any) -> ReportSchema:
        self.db.query(Report).filter(Report.id == id).update(
            {field_name: json.dumps(field_val)}, synchronize_session=False
        )

        self.db.commit()
        report = self.db.query(Report).filter(Report.id == id).first()
        return ReportSchema.model_validate(report)

    def insert_reports(self, new_reports: List[ReportSchema]) -> List[ReportSchema]:
        reports = [
            Report(
                id=new_report.id,
                project=new_report.project,
                template=new_report.template,
                data_values=new_report.data_values,
                script=new_report.script,
                views=new_report.views,
            )
            for new_report in new_reports
        ]
        self.db.add_all(reports)
        self.db.commit()
        for report in reports:
            self.db.refresh(report)
        return [ReportSchema.model_validate(f) for f in reports]
