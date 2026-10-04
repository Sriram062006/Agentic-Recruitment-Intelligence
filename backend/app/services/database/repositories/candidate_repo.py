"""
Repository for Canonical Candidate entities.
Enforces the single-candidate multi-role data model and SHA-256 deduplication.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from app.schemas.candidate import CandidateProfile, CandidateResponse
from app.services.database.supabase_client import get_db


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
    ) -> CandidateResponse:
        cid = candidate_id or uuid4()
        now_iso = datetime.now(timezone.utc).isoformat()
        profile_json = structured_profile.model_dump_json()

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO candidates (id, file_name, storage_path, file_hash, raw_text, structured_profile, faiss_index_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    str(cid),
                    file_name,
                    storage_path,
                    file_hash,
                    raw_text,
                    profile_json,
                    faiss_index_id,
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_by_id(cid)  # type: ignore

    def get_by_id(self, candidate_id: UUID) -> Optional[CandidateResponse]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE id = ?;", (str(candidate_id),))
            row = cursor.fetchone()
            if not row:
                return None

            profile_data = json.loads(row["structured_profile"])
            return CandidateResponse(
                id=UUID(row["id"]),
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**profile_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def get_by_hash(self, file_hash: str) -> Optional[CandidateResponse]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE file_hash = ?;", (file_hash,))
            row = cursor.fetchone()
            if not row:
                return None

            profile_data = json.loads(row["structured_profile"])
            return CandidateResponse(
                id=UUID(row["id"]),
                file_name=row["file_name"],
                storage_path=row["storage_path"],
                file_hash=row["file_hash"],
                raw_text=row["raw_text"],
                structured_profile=CandidateProfile(**profile_data),
                faiss_index_id=row["faiss_index_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def update_faiss_id(self, candidate_id: UUID, faiss_index_id: int) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE candidates SET faiss_index_id = ?, updated_at = ? WHERE id = ?;",
                (faiss_index_id, now_iso, str(candidate_id)),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_all(self, limit: int = 100, offset: int = 0) -> List[CandidateResponse]:
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

    def count(self) -> int:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM candidates;")
            return cursor.fetchone()[0]

    def delete(self, candidate_id: UUID) -> bool:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM candidates WHERE id = ?;", (str(candidate_id),))
            conn.commit()
            return cursor.rowcount > 0
