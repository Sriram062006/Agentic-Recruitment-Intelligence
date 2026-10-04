"""
Database layer supporting Supabase PostgreSQL with local SQLite persistence fallback.
Ensures zero-friction development and reproducible testing while strictly implementing
the frozen database schema, Row Level Security, foreign keys, and unique constraints.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("database")


class DatabaseClient:
    def __init__(self, db_path: str = "data/recruitment.db", settings: Optional[Settings] = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = settings or get_settings()
        self.supabase = None
        self._is_supabase_active = False

        if (
            self.settings.supabase_url
            and self.settings.supabase_key
            and "your-project" not in self.settings.supabase_url
            and "your_supabase" not in self.settings.supabase_url
        ):
            try:
                from supabase import create_client
                self.supabase = create_client(
                    self.settings.supabase_url, self.settings.supabase_key
                )
                self._is_supabase_active = True
                logger.info("Live Supabase PostgreSQL ACTIVE at %s", self.settings.supabase_url)
            except Exception as e:
                logger.warning("Could not connect to live Supabase, using local DB: %s", e)
                self._is_supabase_active = False
        else:
            logger.info("Operating in local persistent DB mode at %s", self.db_path)

        # Initialize local fallback schema
        self._init_local_schema()

    @property
    def is_supabase_active(self) -> bool:
        return self._is_supabase_active and self.supabase is not None

    def get_client(self, token: Optional[str] = None):
        """Returns a Supabase client, scoped with user token if provided for RLS enforcement."""
        if not self.is_supabase_active:
            return None
        if token:
            from supabase import create_client, ClientOptions
            return create_client(
                self.settings.supabase_url,
                self.settings.supabase_key,
                options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),
            )
        return self.supabase

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_local_schema(self) -> None:
        """Initializes tables mirroring the Supabase PostgreSQL DDL migration."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiter_profiles (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'recruiter',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                recruiter_id TEXT NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
                title TEXT NOT NULL,
                department TEXT,
                storage_path TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                structured_profile TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                recruiter_id TEXT NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
                file_name TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                structured_profile TEXT NOT NULL,
                faiss_index_id INTEGER UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT unique_recruiter_file_hash UNIQUE (recruiter_id, file_hash)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id TEXT PRIMARY KEY,
                recruiter_id TEXT NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
                status TEXT NOT NULL DEFAULT 'PENDING',
                total_candidates INTEGER NOT NULL DEFAULT 0,
                total_jobs INTEGER NOT NULL DEFAULT 0,
                total_evaluations INTEGER NOT NULL DEFAULT 0,
                config TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error_message TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_evaluations (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES evaluation_runs(id) ON DELETE CASCADE,
                recruiter_id TEXT NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
                candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                semantic_score REAL NOT NULL,
                skill_score REAL NOT NULL,
                experience_score REAL NOT NULL,
                qualification_score REAL NOT NULL,
                composite_score REAL NOT NULL,
                rank_in_role INTEGER NOT NULL,
                explainability TEXT NOT NULL,
                created_at TEXT NOT NULL,
                CONSTRAINT unique_run_candidate_job UNIQUE (run_id, candidate_id, job_id)
            );
            """)
            conn.commit()


# Global database client singleton
_db_instance: Optional[DatabaseClient] = None


def get_db(settings: Optional[Settings] = None, force_new: bool = False) -> DatabaseClient:
    global _db_instance
    if settings is not None:
        return DatabaseClient(settings=settings)
    if _db_instance is None or force_new:
        _db_instance = DatabaseClient()
    return _db_instance
