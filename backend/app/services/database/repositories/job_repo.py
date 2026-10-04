"""
Repository for Job entities.
Supports live Supabase PostgreSQL with Row Level Security (RLS) enforcement
and transparent SQLite local development fallback.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.schemas.job import JobProfile, JobResponse
from app.services.database.supabase_client import get_db

DEFAULT_LOCAL_RECRUITER_ID = UUID("00000000-0000-0000-0000-000000000001")


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
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> JobResponse:
        jid = job_id or uuid4()
        rid = recruiter_id or DEFAULT_LOCAL_RECRUITER_ID
        now_iso = datetime.now(timezone.utc).isoformat()
        profile_dict = structured_profile.model_dump()

        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            payload = {
                "id": str(jid),
                "recruiter_id": str(rid),
                "title": title,
                "department": department,
                "storage_path": storage_path,
                "raw_content": raw_content,
                "structured_profile": profile_dict,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            res = client.table("jobs").insert(payload).execute()
            if not res.data:
                raise RuntimeError("Failed to insert Job into Supabase PostgreSQL")
            row = res.data[0]
            prof_data = row["structured_profile"]
            if isinstance(prof_data, str):
                prof_data = json.loads(prof_data)
            return JobResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else rid,
                title=row["title"],
                department=row["department"],
                storage_path=row["storage_path"],
                raw_content=row["raw_content"],
                structured_profile=JobProfile(**prof_data),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        # Local SQLite fallback
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO jobs (id, recruiter_id, title, department, storage_path, raw_content, structured_profile, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    str(jid),
                    str(rid),
                    title,
                    department,
                    storage_path,
                    raw_content,
                    json.dumps(profile_dict),
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_by_id(jid, recruiter_id=rid)  # type: ignore

    def get_by_id(
        self,
        job_id: UUID,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> Optional[JobResponse]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("jobs").select("*").eq("id", str(job_id))
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.execute()
            if not res.data:
                return None
            row = res.data[0]
            prof_data = row["structured_profile"]
            if isinstance(prof_data, str):
                prof_data = json.loads(prof_data)
            return JobResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                title=row["title"],
                department=row["department"],
                storage_path=row["storage_path"],
                raw_content=row["raw_content"],
                structured_profile=JobProfile(**prof_data),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?;", (str(job_id),))
            row = cursor.fetchone()
            if not row:
                return None

            profile_data = json.loads(row["structured_profile"])
            return JobResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
                title=row["title"],
                department=row["department"],
                storage_path=row["storage_path"],
                raw_content=row["raw_content"],
                structured_profile=JobProfile(**profile_data),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> List[JobResponse]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("jobs").select("*").order("created_at", desc=True)
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.range(offset, offset + limit - 1).execute()
            items = []
            for row in res.data:
                prof_data = row["structured_profile"]
                if isinstance(prof_data, str):
                    prof_data = json.loads(prof_data)
                items.append(
                    JobResponse(
                        id=UUID(row["id"]),
                        recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                        title=row["title"],
                        department=row["department"],
                        storage_path=row["storage_path"],
                        raw_content=row["raw_content"],
                        structured_profile=JobProfile(**prof_data),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return items

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
                        recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
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

    def count(self, token: Optional[str] = None) -> int:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = client.table("jobs").select("id", count="exact").execute()
            return res.count or 0

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs;")
            return cursor.fetchone()[0]

    def delete(
        self,
        job_id: UUID,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> bool:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("jobs").delete().eq("id", str(job_id))
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.execute()
            return len(res.data) > 0

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs WHERE id = ?;", (str(job_id),))
            conn.commit()
            return cursor.rowcount > 0
