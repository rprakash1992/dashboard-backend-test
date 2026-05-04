from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any

# import repositories
from app.repositories.database_dashboard.report import ReportRepository
from app.repositories.database_dashboard.project import ProjectRepository

# import schemas
from app.schemas.report import ReportSchema, InsertReportResponse
from app.schemas.relation import RelationSchema, RelationType
from app.schemas.item import ItemType, NewItemSchema

# import services
from app.services.role import RoleService
from app.services.relation import RelationService
from app.services.item import ItemService


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)
        self.project_repo = ProjectRepository(db)
        self.relation_service = RelationService(db)
        self.item_service = ItemService(db)

    def fetch_reports_by_ids(
        self,
        loggedin_user_id: str,
        selected_workspace_id: str,
        reports_ids: List[str],
    ) -> List[ReportSchema]:
        """
        Fetches the reports based on report ids.

        Args:
            selected_workspace_id (str): id of workspace selected by user
            loggedin_user_id (str): id of logged in user
            reports_ids (List[str]): list of report ids to be fetched
        Returns:
            Returns the list of fetched reports
        """
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_content_permission = role_service.has_read_content_permission(
            ItemType.REPORT
        )

        if not has_read_content_permission:
            return []

        return self.repo.get_reports_by_ids(reports_ids)

    def insert_report(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        project: str,
        template: str,
    ) -> InsertReportResponse:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(ItemType.REPORT)

        if not has_create_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to create report."
            )

        item = NewItemSchema(
            title=title,
            item_type=ItemType.REPORT,
            description=description,
            image=image,
            tags=tags,
        )
        new_item_response = self.item_service.insert_item(
            selected_workspace_id, loggedin_user_id, item
        )
        new_item_id = new_item_response.id

        projects_response = self.project_repo.get_projects_by_ids([project])[0]
        file_parameters = projects_response.file_parameters

        new_report = ReportSchema(
            id=new_item_id,
            project=project,
            template=template,
            data_values=file_parameters,
        )
        new_report_response = self.repo.insert_reports([new_report])

        # we need to make the report as the "dependent" of it's project because a report is generated from a project
        # so, create a relation between project and report where report is dependent of project
        # this relation is used for displaying traceability
        new_relation = RelationSchema(
            source_id=project,
            target_id=new_item_id,
            relation=RelationType.DEPENDENT,
        )
        self.relation_service.insert_relation(new_relation)
        return InsertReportResponse(
            item=new_item_response, report=new_report_response[0]
        )

    # def insert_reports(
    #     self,
    #     loggedin_user_id: str,
    #     selected_workspace_id: str,
    #     reports_data: List[ReportSchema],
    #     db: Session,
    # ):
    #     """
    #     Inserts reports to the "reports" table.

    #     Args:
    #         selected_workspace_id (str): id of workspace selected by user
    #         loggedin_user_id (str): id of logged in user
    #         reports_data (List[ReportSchema]): list of new reports to be inserted
    #     Returns:
    #         Returns the list of newly inserted reports
    #     """
    #     role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
    #     has_create_permission = role_service.has_create_item_permission(ItemType.REPORT)

    #     if not has_create_permission:
    #         raise HTTPException(
    #             status_code=403, detail="Unauthorized: Not permitted to create report."
    #         )

    #     reports = self.repo.insert_reports(reports_data)

    #     for report in reports:
    #         report_id = report.id
    #         project_id = report.project

    #         # we need to make the report as the "dependent" of it's project because a report is generated from a project
    #         # so, create a relation between project and report where report is dependent of project
    #         new_relation = RelationSchema(
    #             source_id=project_id,
    #             target_id=report_id,
    #             relation=RelationType.DEPENDENT,
    #         )
    #         self.relation_service.insert_relation(new_relation)

    #     return reports

    def update_report_by_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        report_id: str,
        field_name: str,
        field_value: Any,
    ) -> ReportSchema:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_edit_report_permission = role_service.has_update_content_permission(
            ItemType.REPORT
        )

        if not has_edit_report_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to edit report."
            )

        updated_report = self.repo.update_report(report_id, field_name, field_value)

        if not updated_report:
            raise HTTPException(status_code=403, detail="Invalid report id.")

        return updated_report
