from sqlalchemy.orm import Session
from typing import List, Any
from app.repositories.database_dashboard.base import BaseRepository
from app.models.job import Job
from app.schemas.job import JobSchema


class JobRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_job_by_id(self, job_id: str) -> JobSchema:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        return JobSchema.model_validate(job)

    def get_jobs_by_ids(self, job_ids: List[str]) -> List[JobSchema]:
        jobs = self.db.query(Job).filter(Job.id.in_(job_ids)).all()
        return [JobSchema.model_validate(f) for f in jobs]

    def update_job_by_id(self, id: str, field_name: str, field_val: Any) -> JobSchema:
        self.db.query(Job).filter(Job.id == id).update(
            {field_name: field_val}, synchronize_session=False
        )
        self.db.commit()
        job = self.db.query(Job).filter(Job.id == id).first()
        return JobSchema.model_validate(job)

    def update_job_record(self, file: JobSchema) -> JobSchema:
        self.db.query(Job).filter(Job.id == file.id).update(
            file.model_dump(exclude_unset=True), synchronize_session=False
        )
        self.db.commit()
        job = self.db.query(Job).filter(Job.id == file.id).first()
        return JobSchema.model_validate(job)

    def insert_jobs(self, new_jobs: List[JobSchema]) -> List[JobSchema]:
        jobs = [
            Job(
                id=new_job.id,
                job_type=new_job.job_type,
                total_steps=new_job.total_steps,
                completed_steps=new_job.completed_steps,
                run_id=new_job.run_id,
            )
            for new_job in new_jobs
        ]
        self.db.add_all(jobs)
        self.db.commit()
        for job in jobs:
            self.db.refresh(job)
        return [JobSchema.model_validate(f) for f in jobs]
