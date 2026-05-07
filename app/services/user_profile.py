import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any

# import models
from app.models.user_profile import UserProfile
from app.models.item import Item
from app.models.relation import Relation

# import repositories
from app.repositories.database_dashboard.user_profile import UserProfileRepository

# import schemas
from app.schemas.user_profile import UserProfileSchema, PutUserProfileSchema
from app.schemas.item import ItemType

# import services
from app.services.role import RoleService
from app.services.email import EmailService
from app.services.s3_client import S3ClientService


class UserProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserProfileRepository(db)
        self.email_service = EmailService()
        self.s3_client = S3ClientService()

    def create_new_user(self, email: str, name: str, picture: str) -> str:
        print("creating new user profile ====>>>>>>>>")
        user_profile_item = Item(
            id=uuid.uuid4(),
            title=name,
            description="",
            image=picture,
            tags=[],
            item_type="user_profile",
            last_modified_at=None,
            deleted_at=None,
        )
        self.db.add(user_profile_item)
        self.db.commit()
        self.db.refresh(user_profile_item)

        new_user_profile = UserProfile(
            id=user_profile_item.id,
            name=name,
            email=email,
            dob=None,
            picture=picture,
            country=None,
            phone=None,
            status="pending",
            gender=None,
        )
        self.db.add(new_user_profile)
        self.db.commit()
        self.db.refresh(new_user_profile)

        new_personal_workspace_item = Item(
            id=uuid.uuid4(),
            title=f"Personal_{name}",
            description=f"personal workspace of {name}",
            image="",
            tags=[],
            item_type="workspace",
            last_modified_at=None,
            deleted_at=None,
            system_key="user_personal_workspace",
        )
        self.db.add(new_personal_workspace_item)
        self.db.commit()
        self.db.refresh(new_personal_workspace_item)

        # private_user_role_item = (
        #     self.db.query(Item).filter(Item.title == "private_user").first()
        # )
        # private_user_role_id = private_user_role_item.id
        # private_user_role_id = "b10f062e-fb7f-4a83-9c00-d95df1cea12f"
        private_user_role = (
            self.db.query(Item).filter(Item.system_key == "private_user_role").first()
        )
        private_user_role_id = private_user_role.id

        # personal_workspace_item = (
        #     self.db.query(Item).filter(Item.title == "personal").first()
        # )
        # personal_workspace_id = personal_workspace_item.id
        personal_workspace_item = (
            self.db.query(Item).filter(Item.system_key == "personal_workspace").first()
        )
        personal_workspace_id = personal_workspace_item.id

        system_administrator_workspace = (
            self.db.query(Item)
            .filter(Item.system_key == "system_administrator_workspace")
            .first()
        )
        system_administrator_workspace_id = system_administrator_workspace.id
        reviewer_role_id = "1f004b8b-cb07-42b9-814a-c5a157f8ab8c"

        workspace_workspace_relation = Relation(
            source_id=personal_workspace_id,
            target_id=new_personal_workspace_item.id,
            relation="child",
        )
        workspace_user_relation = Relation(
            source_id=new_personal_workspace_item.id,
            target_id=new_user_profile.id,
            relation=f"role.{private_user_role_id}",
        )
        admin_wworkspace_user_relation = Relation(
            source_id=system_administrator_workspace_id,
            target_id=new_user_profile.id,
            relation=f"role.{reviewer_role_id}",
        )
        self.db.add_all(
            [
                workspace_workspace_relation,
                workspace_user_relation,
                admin_wworkspace_user_relation,
            ]
        )
        self.db.commit()

        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self.email_service.send_new_user_registration_email(email, name)
            )
        except RuntimeError:
            pass

        return str(new_user_profile.id)

    def get_user_profile_by_user_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        required_user_id: str,
    ) -> UserProfileSchema:
        has_read_contents_permission = False

        if required_user_id == loggedin_user_id:
            has_read_contents_permission = True
        else:
            role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
            has_read_contents_permission = role_service.has_read_content_permission(
                ItemType.USERPROFILE
            )

        if not has_read_contents_permission:
            return []

        user_profiles = self.repo.get_user_profile_by_user_id(required_user_id)

        if not user_profiles:
            return []

        return user_profiles

    def get_user_profile_by_user_ids(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        required_user_ids: List[str],
    ) -> List[UserProfileSchema]:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.USERPROFILE
        )

        if not has_read_contents_permission:
            return []

        return self.repo.get_user_profile_by_user_ids(required_user_ids)

    async def update_user_profile(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        profile_id: str,
        field_name: str,
        field_value: Any,
    ) -> UserProfileSchema:
        if field_name == "email":
            raise HTTPException(status_code=403, detail="Email can't be updated.")

        is_updating_own_profile = str(loggedin_user_id) == str(profile_id)

        if field_name == "status" and is_updating_own_profile:
            raise HTTPException(
                status_code=403,
                detail="You cannot change your own profile status.",
            )

        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.USERPROFILE
        )
        has_update_contents_permission = role_service.has_update_content_permission(
            ItemType.USERPROFILE
        )

        has_update_profile_permission = (
            has_update_contents_permission and has_read_contents_permission
        ) or is_updating_own_profile

        if not has_update_profile_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to update profile content in this workspace.",
            )

        profile = self.repo.get_user_profile_by_user_id(profile_id)
        old_profile_picture = profile.picture

        email_success = False

        # if profile status is updated by administrator, then send email to user
        if field_name == "status":
            # status can only be updated by system_administrator
            has_update_profile_status_permission = (
                role_service.has_update_content_permission(
                    ItemType.USERPROFILE, "status"
                )
            )
            if not has_update_profile_status_permission:
                raise HTTPException(
                    status_code=403,
                    detail="You are not permitted to update profile status.",
                )

            updated_profile = self.repo.update_profile_by_profile_id(
                profile_id, field_name, field_value
            )
            user_name = profile.name
            user_email = profile.email

            if field_value == "active":
                email_success = await self.email_service.send_profile_activation_email(
                    user_email, user_name
                )
            else:
                email_success = (
                    await self.email_service.send_profile_deactivation_email(
                        user_email, user_name
                    )
                )

            if email_success:
                return updated_profile
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Status updated. But error while sending confirmation email to user.",
                )

        updated_profile = self.repo.update_profile_by_profile_id(
            profile_id, field_name, field_value
        )

        if field_name == "picture":
            if old_profile_picture:
                # image_key = old_profile_picture.split("/")[-1]
                # self.s3_client.delete_object(f"profile-images/{image_key}")
                image_key = old_profile_picture
                self.s3_client.delete_object(image_key)

        return updated_profile

    def update_full_user_profile(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        profile: PutUserProfileSchema,
    ):
        profile_id = profile.id
        is_updating_own_profile = str(loggedin_user_id) == str(profile_id)

        if not is_updating_own_profile:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to update profile in this workspace.",
            )

        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.USERPROFILE
        )
        has_update_contents_permission = role_service.has_update_content_permission(
            ItemType.USERPROFILE
        )

        has_update_profile_permission = (
            has_update_contents_permission and has_read_contents_permission
        ) or is_updating_own_profile

        if not has_update_profile_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to update profile in this workspace.",
            )

        name = profile.name
        dob = profile.dob
        country = profile.country
        phone = profile.phone

        self.repo.update_profile_by_profile_id(profile_id, "name", name)
        self.repo.update_profile_by_profile_id(profile_id, "dob", dob)
        self.repo.update_profile_by_profile_id(profile_id, "country", country)
        updated_profile = self.repo.update_profile_by_profile_id(
            profile_id, "phone", phone
        )

        return updated_profile

    def search_user_profiles(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        search_text: str,
    ):
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.USERPROFILE
        )

        if not has_read_contents_permission:
            return []

        user_profiles1 = self.repo.get_user_profile_by_name_ilike_and_neq_id(
            f"%{search_text}%", loggedin_user_id
        )

        user_profiles1_ids = [loggedin_user_id] + [
            user_profile.id for user_profile in user_profiles1
        ]

        user_profiles2 = self.repo.get_user_profile_by_email_ilike_and_not_in_ids(
            f"%{search_text}%", [loggedin_user_id] + user_profiles1_ids
        )

        all_user_profiles = user_profiles1 + user_profiles2

        # return only first 05 results
        return all_user_profiles[:5]
