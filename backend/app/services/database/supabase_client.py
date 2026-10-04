"""
Database layer supporting Supabase PostgreSQL with local SQLite persistence fallback.
Ensures zero-friction development and reproducible testing while strictly implementing
the frozen database schema, foreign keys, and unique constraints.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("database")


class DatabaseClient:
    def __init__(self, db_path: str = "data/recruitment.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = get_settings()
        self.supabase = None

        if (
            self.settings.supabase_url
            and self.settings.supabase_key
            and "your_supabase" not in self.settings.supabase_url
        ):
            try:
                from supabase import create_client
                self.supabase = create_client(
                    self.settings.supabase_url, self.settings.supabase_key
                )
                logger.info("Connected to live Supabase DB at %s", self.settings.supabase_url)
            except Exception as e:
                logger.warning("Could not connect to live Supabase, using local DB: %s", e)
        else:
            logger.info("Operating in local persistent DB mode at %s", self.db_path)

        self._init_local_schema()

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
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
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
                file_name TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                raw_text TEXT NOT NULL,
                structured_profile TEXT NOT NULL,
                faiss_index_id INTEGER UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id TEXT PRIMARY KEY,
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


def get_db() -> DatabaseClient:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseClient()
    return _db_instance
