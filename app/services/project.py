from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

# import repositories
from app.repositories.database_dashboard.project import ProjectRepository

# import schemas
from app.schemas.project import ProjectSchema, InsertProjectResponse
from app.schemas.relation import RelationSchema, RelationType
from app.schemas.item import ItemType, NewItemSchema

# import services
from app.services.role import RoleService
from app.services.relation import RelationService
from app.services.item import ItemService


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectRepository(db)
        self.relation_service = RelationService(db)
        self.item_service = ItemService(db)

    def insert_project(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        file: str,
        file_parameters: dict,
    ) -> InsertProjectResponse:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(
            ItemType.PROJECT
        )

        if not has_create_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to create project in this workspace.",
            )

        item = NewItemSchema(
            title=title,
            item_type=ItemType.PROJECT,
            description=description,
            image=image,
            tags=tags,
        )
        new_item_response = self.item_service.insert_item(
            selected_workspace_id, loggedin_user_id, item
        )
        new_item_id = new_item_response.id

        new_project = ProjectSchema(
            project=new_item_id, file=file, file_parameters=file_parameters
        )
        new_project_response = self.repo.insert_projects([new_project])

        # we need to make the project as the "dependent" of it's file because a project consists of files
        # so, create a relation between file and project where project is dependent of file
        # this relation is used for displaying traceability
        new_relation = RelationSchema(
            source_id=file, target_id=new_item_id, relation=RelationType.DEPENDENT
        )

        self.relation_service.insert_relation(new_relation)

        return InsertProjectResponse(
            item=new_item_response, project=new_project_response[0]
        )

    # def insert_projects(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     projects_data: List[ProjectSchema],
    # ) -> List[ProjectSchema]:
    #     """
    #     Inserts projects to the "projects" table.

    #     Args:
    #         selected_workspace_id (str): id of workspace selected by user
    #         loggedin_user_id (str): id of logged in user
    #         projects_data (List[ProjectSchema]): list of new projects to be inserted
    #     Returns:
    #         Returns the list of newly inserted projects
    #     """
    #     role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
    #     has_create_permission = role_service.has_create_item_permission(
    #         ItemType.PROJECT
    #     )

    #     if not has_create_permission:
    #         raise HTTPException(
    #             status_code=403, detail="Unauthorized: Not permitted to create project."
    #         )

    #     projects_response = self.repo.insert_projects(projects_data)

    #     for project in projects_response:
    #         project_id = project.project
    #         file_id = project.file

    #         # we need to make the project as the "dependent" of it's file because a project consists of files
    #         # so, create a relation between file and project where project is dependent of file
    #         new_relation = RelationSchema(
    #             source_id=file_id, target_id=project_id, relation=RelationType.DEPENDENT
    #         )

    #         self.relation_service.insert_relation(new_relation)

    #     return projects_response

    def fetch_projects_by_ids(
        self,
        loggedin_user_id: str,
        selected_workspace_id: str,
        project_ids: List[str],
    ) -> List[ProjectSchema]:
        """
        Fetches the projects based on project id.

        Args:
            selected_workspace_id (str): id of workspace selected by user
            loggedin_user_id (str): id of logged in user
            project_ids (List[str]): list of project ids to be fetched
        Returns:
            Returns the list of fetched projects
        """
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_content_permission = role_service.has_read_content_permission(
            ItemType.PROJECT
        )

        if not has_read_content_permission:
            return []

        return self.repo.get_projects_by_ids(project_ids)
