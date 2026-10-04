"""
Repository for Job entities.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.schemas.job import JobProfile, JobResponse, JobSummary
from app.services.database.supabase_client import get_db


class JobRepository:
    def __init__(self):
        self.db = get_db()

    def create(
        self,
        title: str,
        department: Optional[str],
        storage_path: str,
        raw_content: str,
        structured_profile: JobProfile,
        job_id: Optional[UUID] = None,
    ) -> JobResponse:
        jid = job_id or uuid4()
        now_iso = datetime.now(timezone.utc).isoformat()
        profile_json = structured_profile.model_dump_json()

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO jobs (id, title, department, storage_path, raw_content, structured_profile, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    str(jid),
                    title,
                    department,
                    storage_path,
                    raw_content,
                    profile_json,
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_by_id(jid)  # type: ignore

    def get_by_id(self, job_id: UUID) -> Optional[JobResponse]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?;", (str(job_id),))
            row = cursor.fetchone()
            if not row:
                return None

            profile_data = json.loads(row["structured_profile"])
            return JobResponse(
                id=UUID(row["id"]),
                title=row["title"],
                department=row["department"],
                storage_path=row["storage_path"],
                raw_content=row["raw_content"],
                structured_profile=JobProfile(**profile_data),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def list_all(self, limit: int = 100, offset: int = 0) -> List[JobResponse]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                (limit, offset),
            )
            rows = cursor.fetchall()
            items = []
            for row in rows:
                profile_data = json.loads(row["structured_profile"])
                items.append(
                    JobResponse(
                        id=UUID(row["id"]),
                        title=row["title"],
                        department=row["department"],
                        storage_path=row["storage_path"],
                        raw_content=row["raw_content"],
                        structured_profile=JobProfile(**profile_data),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return items

    def count(self) -> int:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs;")
            return cursor.fetchone()[0]

    def delete(self, job_id: UUID) -> bool:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs WHERE id = ?;", (str(job_id),))
            conn.commit()
            return cursor.rowcount > 0
