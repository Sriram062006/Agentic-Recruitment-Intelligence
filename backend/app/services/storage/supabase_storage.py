"""
Storage service implementation.
Supports live Supabase Storage buckets ('resumes', 'job-descriptions')
with seamless fallback to local persistent filesystem storage if Supabase credentials are not active.
"""

import os
from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.core.logging import get_logger
from app.services.storage.base import BaseStorageService

logger = get_logger("storage")


class SupabaseStorageService(BaseStorageService):
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        local_base_dir: str = "data/storage",
    ):
        settings = get_settings()
        self.supabase_url = supabase_url or settings.supabase_url
        self.supabase_key = supabase_key or settings.supabase_key
        self.local_base_dir = Path(local_base_dir)
        self.local_base_dir.mkdir(parents=True, exist_ok=True)
        self.client = None

        if self.supabase_url and self.supabase_key and "your_supabase" not in self.supabase_url:
            try:
                from supabase import create_client
                self.client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Connected to live Supabase Storage at %s", self.supabase_url)
            except Exception as e:
                logger.warning("Failed to initialize live Supabase client, using local storage: %s", e)
        else:
            logger.info("Supabase storage unconfigured/local mode, using local persistent storage at %s", self.local_base_dir)

    def upload_file(
        self,
        bucket: str,
        destination_path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        # 1. Try Supabase Storage if configured
        if self.client:
            try:
                # Ensure bucket exists or attempt upload
                self.client.storage.from_(bucket).upload(
                    path=destination_path,
                    file=content,
                    file_options={"content-type": content_type, "upsert": "true"},
                )
                logger.info("Uploaded %s to Supabase bucket '%s'", destination_path, bucket)
                return f"{bucket}/{destination_path}"
            except Exception as e:
                logger.warning("Supabase Storage upload failed, falling back to local storage: %s", e)

        # 2. Local filesystem storage
        bucket_dir = self.local_base_dir / bucket
        bucket_dir.mkdir(parents=True, exist_ok=True)
        target_file = bucket_dir / destination_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "wb") as f:
            f.write(content)
        logger.info("Stored file locally at %s", target_file)
        return f"{bucket}/{destination_path}"

    def download_file(self, bucket: str, storage_path: str) -> bytes:
        # Strip leading bucket name if included
        rel_path = storage_path
        if rel_path.startswith(f"{bucket}/"):
            rel_path = rel_path[len(bucket) + 1 :]

        if self.client:
            try:
                return self.client.storage.from_(bucket).download(rel_path)
            except Exception as e:
                logger.warning("Supabase Storage download failed, checking local storage: %s", e)

        local_file = self.local_base_dir / bucket / rel_path
        if not local_file.exists():
            raise FileNotFoundError(f"Storage object not found at {storage_path}")
        with open(local_file, "rb") as f:
            return f.read()

    def delete_file(self, bucket: str, storage_path: str) -> bool:
        rel_path = storage_path
        if rel_path.startswith(f"{bucket}/"):
            rel_path = rel_path[len(bucket) + 1 :]

        deleted = False
        if self.client:
            try:
                self.client.storage.from_(bucket).remove([rel_path])
                deleted = True
            except Exception as e:
                logger.warning("Supabase Storage delete error: %s", e)

        local_file = self.local_base_dir / bucket / rel_path
        if local_file.exists():
            os.remove(local_file)
            deleted = True

        return deleted
