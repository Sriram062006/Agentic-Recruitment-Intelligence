"""
Repository for Evaluation Runs and Role-Wise Candidate Evaluations.
Enforces UNIQUE(run_id, candidate_id, job_id) and manages matrix/leaderboard retrieval.
Supports live Supabase PostgreSQL with RLS and SQLite fallback.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.schemas.common import RunStatus
from app.schemas.evaluation import (
    EvaluationResultItem,
    EvaluationRunResponse,
    ExplainabilityPayload,
    LeaderboardEntry,
    MatrixCell,
)
from app.services.database.supabase_client import get_db

DEFAULT_LOCAL_RECRUITER_ID = UUID("00000000-0000-0000-0000-000000000001")


class EvaluationRepository:
    def __init__(self):
        self.db = get_db()

    def create_run(
        self,
        total_candidates: int,
        total_jobs: int,
        config: Dict,
        run_id: Optional[UUID] = None,
        recruiter_id: Optional[UUID] = None,
        token: Optional[str] = None,
    ) -> EvaluationRunResponse:
        rid = run_id or uuid4()
        rec_id = recruiter_id or DEFAULT_LOCAL_RECRUITER_ID
        now_iso = datetime.now(timezone.utc).isoformat()
        total_evals = total_candidates * total_jobs

        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            payload = {
                "id": str(rid),
                "recruiter_id": str(rec_id),
                "status": RunStatus.PENDING.value,
                "total_candidates": total_candidates,
                "total_jobs": total_jobs,
                "total_evaluations": total_evals,
                "config": config,
                "started_at": now_iso,
            }
            res = client.table("evaluation_runs").insert(payload).execute()
            if not res.data:
                raise RuntimeError("Failed to create evaluation run in Supabase")
            return self.get_run(rid, token=token)  # type: ignore

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evaluation_runs (id, recruiter_id, status, total_candidates, total_jobs, total_evaluations, config, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    str(rid),
                    str(rec_id),
                    RunStatus.PENDING.value,
                    total_candidates,
                    total_jobs,
                    total_evals,
                    json.dumps(config),
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_run(rid)  # type: ignore

    def update_run_status(
        self,
        run_id: UUID,
        status: RunStatus,
        error_message: Optional[str] = None,
        token: Optional[str] = None,
    ) -> bool:
        now_iso = (
            datetime.now(timezone.utc).isoformat()
            if status in [RunStatus.COMPLETED, RunStatus.FAILED]
            else None
        )
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            update_payload = {"status": status.value, "error_message": error_message}
            if now_iso:
                update_payload["completed_at"] = now_iso
            res = client.table("evaluation_runs").update(update_payload).eq("id", str(run_id)).execute()
            return len(res.data) > 0

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE evaluation_runs
                SET status = ?, completed_at = COALESCE(?, completed_at), error_message = ?
                WHERE id = ?;
                """,
                (status.value, now_iso, error_message, str(run_id)),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_run(self, run_id: UUID, token: Optional[str] = None) -> Optional[EvaluationRunResponse]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = client.table("evaluation_runs").select("*").eq("id", str(run_id)).execute()
            if not res.data:
                return None
            row = res.data[0]
            conf = row["config"]
            if isinstance(conf, str):
                conf = json.loads(conf)
            return EvaluationRunResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                status=RunStatus(row["status"]),
                total_candidates=row["total_candidates"],
                total_jobs=row["total_jobs"],
                total_evaluations=row["total_evaluations"],
                config=conf,
                started_at=datetime.fromisoformat(row["started_at"]),
                completed_at=(
                    datetime.fromisoformat(row["completed_at"])
                    if row.get("completed_at")
                    else None
                ),
                error_message=row.get("error_message"),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evaluation_runs WHERE id = ?;", (str(run_id),))
            row = cursor.fetchone()
            if not row:
                return None

            return EvaluationRunResponse(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
                status=RunStatus(row["status"]),
                total_candidates=row["total_candidates"],
                total_jobs=row["total_jobs"],
                total_evaluations=row["total_evaluations"],
                config=json.loads(row["config"]),
                started_at=datetime.fromisoformat(row["started_at"]),
                completed_at=(
                    datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None
                ),
                error_message=row["error_message"],
            )

    def save_bulk_evaluations(self, evaluations: List[Dict], token: Optional[str] = None) -> None:
        """Saves a batch of Candidate x Job evaluation records."""
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            supabase_batch = []
            for ev in evaluations:
                ev_id = str(ev.get("id", uuid4()))
                rid = str(ev.get("recruiter_id", DEFAULT_LOCAL_RECRUITER_ID))
                expl = ev["explainability"]
                if hasattr(expl, "model_dump"):
                    expl = expl.model_dump()
                supabase_batch.append(
                    {
                        "id": ev_id,
                        "run_id": str(ev["run_id"]),
                        "recruiter_id": rid,
                        "candidate_id": str(ev["candidate_id"]),
                        "job_id": str(ev["job_id"]),
                        "semantic_score": float(ev["semantic_score"]),
                        "skill_score": float(ev["skill_score"]),
                        "experience_score": float(ev["experience_score"]),
                        "qualification_score": float(ev["qualification_score"]),
                        "composite_score": float(ev["composite_score"]),
                        "rank_in_role": int(ev["rank_in_role"]),
                        "explainability": expl,
                        "created_at": now_iso,
                    }
                )
            if supabase_batch:
                client.table("candidate_evaluations").upsert(supabase_batch).execute()
            return

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            for ev in evaluations:
                ev_id = str(ev.get("id", uuid4()))
                rid = str(ev.get("recruiter_id", DEFAULT_LOCAL_RECRUITER_ID))
                expl = ev["explainability"]
                if hasattr(expl, "model_dump"):
                    expl = expl.model_dump()
                expl_json = json.dumps(expl)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO candidate_evaluations
                    (id, run_id, recruiter_id, candidate_id, job_id, semantic_score, skill_score, experience_score, qualification_score, composite_score, rank_in_role, explainability, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        ev_id,
                        str(ev["run_id"]),
                        rid,
                        str(ev["candidate_id"]),
                        str(ev["job_id"]),
                        float(ev["semantic_score"]),
                        float(ev["skill_score"]),
                        float(ev["experience_score"]),
                        float(ev["qualification_score"]),
                        float(ev["composite_score"]),
                        int(ev["rank_in_role"]),
                        expl_json,
                        now_iso,
                    ),
                )
            conn.commit()

    def get_matrix_cells(self, run_id: UUID, token: Optional[str] = None) -> List[MatrixCell]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = (
                client.table("candidate_evaluations")
                .select("candidate_id, job_id, composite_score, rank_in_role")
                .eq("run_id", str(run_id))
                .execute()
            )
            cells = []
            for row in res.data:
                score = float(row["composite_score"])
                tier = "Strong" if score >= 0.75 else "Moderate" if score >= 0.50 else "Low"
                cells.append(
                    MatrixCell(
                        candidate_id=UUID(row["candidate_id"]),
                        job_id=UUID(row["job_id"]),
                        composite_score=score,
                        rank_in_role=row["rank_in_role"],
                        fitment_tier=tier,
                    )
                )
            return cells

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT candidate_id, job_id, composite_score, rank_in_role
                FROM candidate_evaluations
                WHERE run_id = ?;
                """,
                (str(run_id),),
            )
            rows = cursor.fetchall()
            cells = []
            for row in rows:
                score = float(row["composite_score"])
                tier = "Strong" if score >= 0.75 else "Moderate" if score >= 0.50 else "Low"
                cells.append(
                    MatrixCell(
                        candidate_id=UUID(row["candidate_id"]),
                        job_id=UUID(row["job_id"]),
                        composite_score=score,
                        rank_in_role=row["rank_in_role"],
                        fitment_tier=tier,
                    )
                )
            return cells

    def get_leaderboard_for_job(
        self, run_id: UUID, job_id: UUID, limit: int = 50, token: Optional[str] = None
    ) -> List[LeaderboardEntry]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = (
                client.table("candidate_evaluations")
                .select("*, candidates(structured_profile)")
                .eq("run_id", str(run_id))
                .eq("job_id", str(job_id))
                .order("composite_score", desc=True)
                .limit(limit)
                .execute()
            )
            entries = []
            for idx, row in enumerate(res.data, start=1):
                cand_info = row.get("candidates") or {}
                cand_data = cand_info.get("structured_profile", {})
                if isinstance(cand_data, str):
                    cand_data = json.loads(cand_data)
                expl_data = row["explainability"]
                if isinstance(expl_data, str):
                    expl_data = json.loads(expl_data)
                entries.append(
                    LeaderboardEntry(
                        rank=idx,
                        candidate_id=UUID(row["candidate_id"]),
                        candidate_name=cand_data.get("full_name", "Candidate"),
                        total_experience_years=float(cand_data.get("total_experience_years", 0.0)),
                        highest_qualification=cand_data.get("highest_qualification", "Bachelor's"),
                        composite_score=float(row["composite_score"]),
                        semantic_score=float(row["semantic_score"]),
                        skill_score=float(row["skill_score"]),
                        experience_score=float(row["experience_score"]),
                        qualification_score=float(row["qualification_score"]),
                        matched_skills_count=len(expl_data.get("matched_skills", [])),
                        missing_skills_count=len(expl_data.get("missing_skills", [])),
                    )
                )
            return entries

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ce.*, c.structured_profile as cand_profile
                FROM candidate_evaluations ce
                JOIN candidates c ON ce.candidate_id = c.id
                WHERE ce.run_id = ? AND ce.job_id = ?
                ORDER BY ce.composite_score DESC
                LIMIT ?;
                """,
                (str(run_id), str(job_id), limit),
            )
            rows = cursor.fetchall()
            entries = []
            for idx, row in enumerate(rows, start=1):
                cand_data = json.loads(row["cand_profile"])
                expl_data = json.loads(row["explainability"])
                entries.append(
                    LeaderboardEntry(
                        rank=idx,
                        candidate_id=UUID(row["candidate_id"]),
                        candidate_name=cand_data.get("full_name", "Candidate"),
                        total_experience_years=float(cand_data.get("total_experience_years", 0.0)),
                        highest_qualification=cand_data.get("highest_qualification", "Bachelor's"),
                        composite_score=float(row["composite_score"]),
                        semantic_score=float(row["semantic_score"]),
                        skill_score=float(row["skill_score"]),
                        experience_score=float(row["experience_score"]),
                        qualification_score=float(row["qualification_score"]),
                        matched_skills_count=len(expl_data.get("matched_skills", [])),
                        missing_skills_count=len(expl_data.get("missing_skills", [])),
                    )
                )
            return entries

    def get_candidate_evaluation_for_job(
        self, run_id: UUID, candidate_id: UUID, job_id: UUID, token: Optional[str] = None
    ) -> Optional[EvaluationResultItem]:
        if self.db.is_supabase_active and token:
            client = self.db.get_client(token)
            res = (
                client.table("candidate_evaluations")
                .select("*, candidates(structured_profile), jobs(title)")
                .eq("run_id", str(run_id))
                .eq("candidate_id", str(candidate_id))
                .eq("job_id", str(job_id))
                .execute()
            )
            if not res.data:
                return None
            row = res.data[0]
            cand_info = row.get("candidates") or {}
            cand_data = cand_info.get("structured_profile", {})
            if isinstance(cand_data, str):
                cand_data = json.loads(cand_data)
            job_info = row.get("jobs") or {}
            job_title = job_info.get("title", "Job Role")
            expl_data = row["explainability"]
            if isinstance(expl_data, str):
                expl_data = json.loads(expl_data)

            return EvaluationResultItem(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if row.get("recruiter_id") else None,
                run_id=UUID(row["run_id"]),
                candidate_id=UUID(row["candidate_id"]),
                job_id=UUID(row["job_id"]),
                candidate_name=cand_data.get("full_name", "Candidate"),
                job_title=job_title,
                semantic_score=float(row["semantic_score"]),
                skill_score=float(row["skill_score"]),
                experience_score=float(row["experience_score"]),
                qualification_score=float(row["qualification_score"]),
                composite_score=float(row["composite_score"]),
                rank_in_role=row["rank_in_role"],
                explainability=ExplainabilityPayload(**expl_data),
                created_at=datetime.fromisoformat(row["created_at"]),
            )

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ce.*, c.structured_profile as cand_profile, j.title as job_title
                FROM candidate_evaluations ce
                JOIN candidates c ON ce.candidate_id = c.id
                JOIN jobs j ON ce.job_id = j.id
                WHERE ce.run_id = ? AND ce.candidate_id = ? AND ce.job_id = ?;
                """,
                (str(run_id), str(candidate_id), str(job_id)),
            )
            row = cursor.fetchone()
            if not row:
                return None

            cand_data = json.loads(row["cand_profile"])
            expl_data = json.loads(row["explainability"])
            return EvaluationResultItem(
                id=UUID(row["id"]),
                recruiter_id=UUID(row["recruiter_id"]) if "recruiter_id" in row.keys() else None,
                run_id=UUID(row["run_id"]),
                candidate_id=UUID(row["candidate_id"]),
                job_id=UUID(row["job_id"]),
                candidate_name=cand_data.get("full_name", "Candidate"),
                job_title=row["job_title"],
                semantic_score=float(row["semantic_score"]),
                skill_score=float(row["skill_score"]),
                experience_score=float(row["experience_score"]),
                qualification_score=float(row["qualification_score"]),
                composite_score=float(row["composite_score"]),
                rank_in_role=row["rank_in_role"],
                explainability=ExplainabilityPayload(**expl_data),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
