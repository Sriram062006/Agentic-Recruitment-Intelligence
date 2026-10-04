"""
Repository for Recruiter Profiles.
Manages recruiter metadata linked to Supabase Auth user IDs.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas.recruiter import RecruiterProfile
from app.services.database.supabase_client import get_db


class RecruiterRepository:
    def __init__(self):
        self.db = get_db()

    def get_by_user_id(self, user_id: UUID, token: Optional[str] = None) -> Optional[RecruiterProfile]:
        if self.db.is_supabase_active:
            client = self.db.get_client(token)
            res = client.table("recruiter_profiles").select("*").eq("user_id", str(user_id)).execute()
            if not res.data:
                return None
            row = res.data[0]
            return RecruiterProfile(
                user_id=UUID(row["user_id"]),
                full_name=row["full_name"],
                role=row["role"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        # Local SQLite fallback
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recruiter_profiles WHERE user_id = ?;", (str(user_id),))
            row = cursor.fetchone()
            if not row:
                return None
            return RecruiterProfile(
                user_id=UUID(row["user_id"]),
                full_name=row["full_name"],
                role=row["role"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def update_profile(self, user_id: UUID, full_name: str, token: Optional[str] = None) -> Optional[RecruiterProfile]:
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.db.is_supabase_active:
            client = self.db.get_client(token)
            res = (
                client.table("recruiter_profiles")
                .update({"full_name": full_name, "updated_at": now_iso})
                .eq("user_id", str(user_id))
                .execute()
            )
            if not res.data:
                return None
            row = res.data[0]
            return RecruiterProfile(
                user_id=UUID(row["user_id"]),
                full_name=row["full_name"],
                role=row["role"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recruiter_profiles SET full_name = ?, updated_at = ? WHERE user_id = ?;",
                (full_name, now_iso, str(user_id)),
            )
            conn.commit()
        return self.get_by_user_id(user_id)
