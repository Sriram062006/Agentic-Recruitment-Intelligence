"""
Repository for Recruiter Profiles and Admin User Management.
Manages recruiter metadata linked to Supabase Auth user IDs.
Supports live Supabase PostgreSQL and local SQLite fallback.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from app.schemas.recruiter import AdminStatsResponse, AdminUserListItem, RecruiterProfile
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
                full_name=row.get("full_name", "Recruiter"),
                email=row.get("email"),
                role=row.get("role", "recruiter"),
                is_active=bool(row.get("is_active", True)),
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
            row_dict = dict(row)
            return RecruiterProfile(
                user_id=UUID(row_dict["user_id"]),
                full_name=row_dict.get("full_name", "Recruiter"),
                email=row_dict.get("email"),
                role=row_dict.get("role", "recruiter"),
                is_active=bool(row_dict.get("is_active", 1)),
                created_at=datetime.fromisoformat(row_dict["created_at"]),
                updated_at=datetime.fromisoformat(row_dict["updated_at"]),
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
            return self.get_by_user_id(user_id, token=token)

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recruiter_profiles SET full_name = ?, updated_at = ? WHERE user_id = ?;",
                (full_name, now_iso, str(user_id)),
            )
            conn.commit()
        return self.get_by_user_id(user_id)

    def list_all_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        token: Optional[str] = None,
    ) -> List[AdminUserListItem]:
        """Lists users with aggregated counts for Admin management."""
        if self.db.is_supabase_active:
            client = self.db.get_client(token)
            query = client.table("recruiter_profiles").select("*")
            if role:
                query = query.eq("role", role)
            if search:
                # Filter on full_name or email
                query = query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
            
            res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            users = []
            for row in res.data:
                u_id = row["user_id"]
                # Get entity counts for user
                cand_res = client.table("candidates").select("id", count="exact").eq("recruiter_id", u_id).execute()
                job_res = client.table("jobs").select("id", count="exact").eq("recruiter_id", u_id).execute()
                run_res = client.table("evaluation_runs").select("id", count="exact").eq("recruiter_id", u_id).execute()
                
                users.append(
                    AdminUserListItem(
                        user_id=UUID(row["user_id"]),
                        full_name=row.get("full_name", "Recruiter"),
                        email=row.get("email"),
                        role=row.get("role", "recruiter"),
                        is_active=bool(row.get("is_active", True)),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        candidates_count=cand_res.count or 0,
                        jobs_count=job_res.count or 0,
                        runs_count=run_res.count or 0,
                    )
                )
            return users

        # SQLite fallback
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT 
                    rp.*,
                    (SELECT COUNT(*) FROM candidates c WHERE c.recruiter_id = rp.user_id) as candidates_count,
                    (SELECT COUNT(*) FROM jobs j WHERE j.recruiter_id = rp.user_id) as jobs_count,
                    (SELECT COUNT(*) FROM evaluation_runs r WHERE r.recruiter_id = rp.user_id) as runs_count
                FROM recruiter_profiles rp
                WHERE 1=1
            """
            params: List[object] = []
            if role:
                sql += " AND rp.role = ?"
                params.append(role)
            if search:
                sql += " AND (rp.full_name LIKE ? OR rp.email LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            sql += " ORDER BY rp.created_at DESC LIMIT ? OFFSET ?;"
            params.extend([limit, offset])

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            users = []
            for r in rows:
                rd = dict(r)
                users.append(
                    AdminUserListItem(
                        user_id=UUID(rd["user_id"]),
                        full_name=rd.get("full_name", "Recruiter"),
                        email=rd.get("email"),
                        role=rd.get("role", "recruiter"),
                        is_active=bool(rd.get("is_active", 1)),
                        created_at=datetime.fromisoformat(rd["created_at"]),
                        updated_at=datetime.fromisoformat(rd["updated_at"]),
                        candidates_count=rd.get("candidates_count", 0),
                        jobs_count=rd.get("jobs_count", 0),
                        runs_count=rd.get("runs_count", 0),
                    )
                )
            return users

    def update_role(self, user_id: UUID, new_role: str, token: Optional[str] = None) -> Optional[RecruiterProfile]:
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.db.is_supabase_active:
            client = self.db.get_client(token)
            res = (
                client.table("recruiter_profiles")
                .update({"role": new_role, "updated_at": now_iso})
                .eq("user_id", str(user_id))
                .execute()
            )
            if not res.data:
                return None
            return self.get_by_user_id(user_id, token=token)

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recruiter_profiles SET role = ?, updated_at = ? WHERE user_id = ?;",
                (new_role, now_iso, str(user_id)),
            )
            conn.commit()
        return self.get_by_user_id(user_id)

    def update_status(self, user_id: UUID, is_active: bool, token: Optional[str] = None) -> Optional[RecruiterProfile]:
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.db.is_supabase_active:
            client = self.db.get_client(token)
            res = (
                client.table("recruiter_profiles")
                .update({"is_active": is_active, "updated_at": now_iso})
                .eq("user_id", str(user_id))
                .execute()
            )
            if not res.data:
                return None
            return self.get_by_user_id(user_id, token=token)

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recruiter_profiles SET is_active = ?, updated_at = ? WHERE user_id = ?;",
                (1 if is_active else 0, now_iso, str(user_id)),
            )
            conn.commit()
        return self.get_by_user_id(user_id)

    def get_admin_stats(self, token: Optional[str] = None) -> AdminStatsResponse:
        """Computes system-wide operational metrics for Admin overview."""
        if self.db.is_supabase_active:
            client = self.db.get_client(token)
            u_res = client.table("recruiter_profiles").select("user_id, is_active", count="exact").execute()
            total_users = u_res.count or len(u_res.data)
            
            # Active recruiters
            act_res = client.table("recruiter_profiles").select("user_id", count="exact").eq("is_active", True).execute()
            active_recruiters = act_res.count or len(act_res.data)

            c_res = client.table("candidates").select("id", count="exact").execute()
            total_candidates = c_res.count or len(c_res.data)

            j_res = client.table("jobs").select("id", count="exact").execute()
            total_jobs = j_res.count or len(j_res.data)

            r_res = client.table("evaluation_runs").select("id", count="exact").execute()
            total_runs = r_res.count or len(r_res.data)

            e_res = client.table("candidate_evaluations").select("id", count="exact").execute()
            total_evaluations = e_res.count or len(e_res.data)

            return AdminStatsResponse(
                total_users=total_users,
                active_recruiters=active_recruiters,
                total_candidates=total_candidates,
                total_jobs=total_jobs,
                total_runs=total_runs,
                total_evaluations=total_evaluations,
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM recruiter_profiles;")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM recruiter_profiles WHERE is_active = 1;")
            active_recruiters = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM candidates;")
            total_candidates = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM jobs;")
            total_jobs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM evaluation_runs;")
            total_runs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM candidate_evaluations;")
            total_evaluations = cursor.fetchone()[0]

            return AdminStatsResponse(
                total_users=total_users,
                active_recruiters=active_recruiters,
                total_candidates=total_candidates,
                total_jobs=total_jobs,
                total_runs=total_runs,
                total_evaluations=total_evaluations,
            )
