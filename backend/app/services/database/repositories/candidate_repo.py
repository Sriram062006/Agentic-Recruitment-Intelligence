"""
Repository for Canonical Candidate entities.
Enforces the single-candidate multi-role data model and SHA-256 deduplication.
Supports live Supabase PostgreSQL with RLS and SQLite fallback.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from app.schemas.candidate import (
    CandidateContactUpdate,
    CandidateProfile,
    CandidateResponse,
)
from app.services.database.supabase_client import get_db

DEFAULT_LOCAL_RECRUITER_ID = UUID("00000000-0000-0000-0000-000000000001")


class CandidateRepository:
    def __init__(self):
        self.db = get_db()

    def create(
        self,
        file_name: str,
        storage_path: str,
        file_hash: str,
        raw_text: str,
        structured_profile: CandidateProfile,
        faiss_index_id: Optional[int] = None,
        candidate_id: Optional[UUID] = None,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> CandidateResponse:
        cid = candidate_id or uuid4()
        rid = recruiter_id or DEFAULT_LOCAL_RECRUITER_ID
        now_iso = datetime.now(timezone.utc).isoformat()
        profile_dict = structured_profile.model_dump()

        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            payload = {
                "id": str(cid),
                "recruiter_id": str(rid),
                "file_name": file_name,
                "storage_path": storage_path,
                "file_hash": file_hash,
                "raw_text": raw_text,
                "structured_profile": profile_dict,
                "faiss_index_id": faiss_index_id,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            res = client.table("candidates").insert(payload).execute()
            if not res.data:
                raise RuntimeError("Failed to insert candidate into Supabase PostgreSQL")
            row = res.data[0]
            prof_data = row["structured_profile"]
            if isinstance(prof_data, str):
                prof_data = json.loads(prof_data)
            return CandidateResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else rid,
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**prof_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO candidates (id, recruiter_id, file_name, storage_path, file_hash, raw_text, structured_profile, faiss_index_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    str(cid),
                    str(rid),
                    file_name,
                    storage_path,
                    file_hash,
                    raw_text,
                    json.dumps(profile_dict),
                    faiss_index_id,
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_by_id(cid, recruiter_id=rid)  # type: ignore

    def get_by_id(
        self,
        candidate_id: UUID,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> Optional[CandidateResponse]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("candidates").select("*").eq("id", str(candidate_id))
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.execute()
            if not res.data:
                return None
            row = res.data[0]
            prof_data = row["structured_profile"]
            if isinstance(prof_data, str):
                prof_data = json.loads(prof_data)
            return CandidateResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**prof_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE id = ?;", (str(candidate_id),))
            row = cursor.fetchone()
            if not row:
                return None

            profile_data = json.loads(row["structured_profile"])
            return CandidateResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**profile_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def get_by_hash(
        self,
        file_hash: str,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> Optional[CandidateResponse]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("candidates").select("*").eq("file_hash", file_hash)
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.execute()
            if not res.data:
                return None
            row = res.data[0]
            prof_data = row["structured_profile"]
            if isinstance(prof_data, str):
                prof_data = json.loads(prof_data)
            return CandidateResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**prof_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE file_hash = ?;", (file_hash,))
            row = cursor.fetchone()
            if not row:
                return None

            profile_data = json.loads(row["structured_profile"])
            return CandidateResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**profile_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def update_faiss_id(
        self,
        candidate_id: UUID,
        faiss_index_id: int,
        token: Optional[str] = None,
    ) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = (
                client.table("candidates")
                .update({"faiss_index_id": faiss_index_id, "updated_at": now_iso})
                .eq("id", str(candidate_id))
                .execute()
            )
            return len(res.data) > 0

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE candidates SET faiss_index_id = ?, updated_at = ? WHERE id = ?;",
                (faiss_index_id, now_iso, str(candidate_id)),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_contact_info(
        self,
        candidate_id: UUID,
        contact_update: "CandidateContactUpdate",
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> Optional[CandidateResponse]:
        """Updates editable contact details (name, email, phone, location) ONLY without modifying professional history or FAISS index."""
        cand = self.get_by_id(candidate_id, recruiter_id=recruiter_id, token=token)
        if not cand:
            return None

        prof = cand.structured_profile
        if contact_update.full_name is not None:
            prof.full_name = contact_update.full_name
            if prof.personal_information:
                prof.personal_information.full_name = contact_update.full_name
        if contact_update.email is not None:
            prof.email = contact_update.email
            if prof.personal_information:
                prof.personal_information.email = contact_update.email
        if contact_update.phone is not None:
            prof.phone = contact_update.phone
            if prof.personal_information:
                prof.personal_information.phone = contact_update.phone
        if contact_update.location is not None:
            prof.location = contact_update.location
            if prof.personal_information:
                prof.personal_information.location = contact_update.location
        if contact_update.years_of_experience is not None:
            if prof.experience_years_original_calculated is None:
                prof.experience_years_original_calculated = prof.total_experience_years
            prof.total_experience_years = round(float(contact_update.years_of_experience), 1)
            prof.experience_years_source = "manual"
            prof.experience_years_updated_by = str(recruiter_id) if recruiter_id else "recruiter"
            prof.experience_years_updated_at = datetime.now(timezone.utc).isoformat()

        now_iso = datetime.now(timezone.utc).isoformat()
        prof_dict = prof.model_dump()

        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = (
                client.table("candidates")
                .update({"structured_profile": prof_dict, "updated_at": now_iso})
                .eq("id", str(candidate_id))
            )
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.execute()
            if not res.data:
                return None
            return self.get_by_id(candidate_id, recruiter_id=recruiter_id, token=token)

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            sql = "UPDATE candidates SET structured_profile = ?, updated_at = ? WHERE id = ?"
            params = [json.dumps(prof_dict), now_iso, str(candidate_id)]
            if recruiter_id:
                sql += " AND recruiter_id = ?"
                params.append(str(recruiter_id))
            cursor.execute(sql + ";", tuple(params))
            conn.commit()

        return self.get_by_id(candidate_id, recruiter_id=recruiter_id)

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> List[CandidateResponse]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("candidates").select("*").order("created_at", desc=True)
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.range(offset, offset + limit - 1).execute()
            items = []
            for row in res.data:
                prof_data = row["structured_profile"]
                if isinstance(prof_data, str):
                    prof_data = json.loads(prof_data)
                items.append(
                    CandidateResponse(
                        id=UUID(row["id"]),
                        recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                        file_name=row["file_name"],
                        storage_path=row["storage_path"],
                        file_hash=row["file_hash"],
                        raw_text=row["raw_text"],
                        structured_profile=CandidateProfile(**prof_data),
                        faiss_index_id=row["faiss_index_id"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return items

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM candidates ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                (limit, offset),
            )
            rows = cursor.fetchall()
            items = []
            for row in rows:
                profile_data = json.loads(row["structured_profile"])
                items.append(
                    CandidateResponse(
                        id=UUID(row["id"]),
                        recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
                        file_name=row["file_name"],
                        storage_path=row["storage_path"],
                        file_hash=row["file_hash"],
                        raw_text=row["raw_text"],
                        structured_profile=CandidateProfile(**profile_data),
                        faiss_index_id=row["faiss_index_id"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return items

    def count(self, token: Optional[str] = None) -> int:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = client.table("candidates").select("id", count="exact").execute()
            return res.count or 0

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM candidates;")
            return cursor.fetchone()[0]

    def delete(
        self,
        candidate_id: UUID,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> bool:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            query = client.table("candidates").delete().eq("id", str(candidate_id))
            if recruiter_id:
                query = query.eq("recruiter_id", str(recruiter_id))
            res = query.execute()
            return len(res.data) > 0

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM candidates WHERE id = ?;", (str(candidate_id),))
            conn.commit()
            return cursor.rowcount > 0
