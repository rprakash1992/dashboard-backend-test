from sqlalchemy.orm import Session
from typing import List
from app.repositories.database_dashboard.base import BaseRepository
from app.models.user_profile import UserProfile
from app.schemas.user_profile import UserProfileSchema


class UserProfileRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_user_profile_by_user_id(self, user_id: str) -> UserProfileSchema:
        user_profile = (
            self.db.query(UserProfile)
            .filter(
                UserProfile.id == user_id,
            )
            .first()
        )
        return UserProfileSchema.model_validate(user_profile)

    def get_user_profile_by_user_ids(
        self, user_ids: List[str]
    ) -> List[UserProfileSchema]:
        user_profiles = (
            self.db.query(UserProfile)
            .filter(
                UserProfile.id.in_(user_ids),
            )
            .all()
        )
        return [UserProfileSchema.model_validate(f) for f in user_profiles]

    def get_user_profile_by_name_ilike_and_neq_id(
        self, name: str, id: str
    ) -> List[UserProfileSchema]:
        user_profiles = (
            self.db.query(UserProfile)
            .filter(
                UserProfile.name.ilike(name),
                UserProfile.id != id,
            )
            .all()
        )
        return [UserProfileSchema.model_validate(f) for f in user_profiles]

    def get_user_profile_by_email_ilike_and_not_in_ids(
        self, email: str, ids: List[str]
    ) -> List[UserProfileSchema]:
        user_profiles = (
            self.db.query(UserProfile)
            .filter(UserProfile.email.ilike(email), UserProfile.id.not_in(ids))
            .all()
        )
        return [UserProfileSchema.model_validate(f) for f in user_profiles]

    def insert_user_profiles(
        self, new_profiles: List[UserProfileSchema]
    ) -> List[UserProfileSchema]:
        profiles = [
            UserProfile(
                id=new_profile.id,
                name=new_profile.name,
                email=new_profile.email,
                dob=new_profile.dob,
                picture=new_profile.picture,
                country=new_profile.country,
                phone=new_profile.phone,
                status=new_profile.status,
                gender=new_profile.gender,
            )
            for new_profile in new_profiles
        ]

        self.db.add_all(profiles)
        self.db.commit()

        for profile in profiles:
            self.db.refresh(profile)
        return [UserProfileSchema.model_validate(f) for f in profiles]

    def update_profile_by_profile_id(
        self, profile_id: str, field_name: str, field_val
    ) -> UserProfileSchema:
        self.db.query(UserProfile).filter(UserProfile.id == profile_id).update(
            {field_name: field_val}, synchronize_session=False
        )
        self.db.commit()
        profile = (
            self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        )
        return UserProfileSchema.model_validate(profile)
