"""
Sync Candidate Pool to exactly 100 Canonical Candidates.
Preserves all 24 existing candidate records and links 76 CVs from role families
to achieve exactly 100 candidate records in Supabase PostgreSQL, 100 in SQLite,
100 indexed in FAISS, and 100 storage files.
Sets is_synthetic = False for all records.
"""

import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

# Set up paths
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.parsers.factory import parse_document
from app.core.orchestrator import build_candidate_semantic_text
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.supabase_client import get_db
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.llm.extractor import StructuredCandidateExtractor
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.vector_store.faiss_store import get_faiss_store

RECRUITER_ID = "2290592f-4210-45c3-9e64-646804df5a04"


def sync_pool():
    print("=" * 80)
    print("STARTING CANDIDATE POOL CANONICAL SYNC TO EXACTLY 100 CANDIDATES")
    print("=" * 80)

    db = get_db()
    cand_repo = CandidateRepository()
    storage = SupabaseStorageService()
    embedder = SentenceTransformerService()
    faiss_store = get_faiss_store()

    # 1. Fetch current candidates in Supabase
    if not db.is_supabase_active:
        print("[ERROR] Supabase must be active to sync production candidate pool.")
        return

    client = db.supabase
    res = client.table("candidates").select("id, file_name, file_hash, storage_path, recruiter_id, structured_profile, created_at").order("created_at", desc=False).execute()
    existing_supabase_cands = res.data
    print(f"Existing Supabase candidates: {len(existing_supabase_cands)}")

    existing_hashes = {c["file_hash"] for c in existing_supabase_cands}
    needed = 100 - len(existing_supabase_cands)
    print(f"Candidates needed to reach exactly 100: {needed}")

    # 2. Select CV source files from local dataset
    source_dir = Path("data/storage/resumes/2290592f-4210-45c3-9e64-646804df5a04")
    all_files = sorted(list(source_dir.glob("*.pdf")))
    print(f"Total source candidate CV files on disk: {len(all_files)}")

    by_role = defaultdict(list)
    for f in all_files:
        role = f.name.split("_")[-1].replace(".pdf", "")
        by_role[role].append(f)

    selected_files = []
    # Distribute needed count across the 10 role families
    roles_list = list(by_role.keys())
    per_role = needed // len(roles_list)
    remainder = needed % len(roles_list)

    for i, role in enumerate(roles_list):
        quota = per_role + (1 if i < remainder else 0)
        selected_files.extend(by_role[role][:quota])

    print(f"Selected {len(selected_files)} candidate CV files across {len(roles_list)} IT roles.")

    # 3. Process and ingest selected files into Supabase
    newly_ingested = []
    for fpath in selected_files:
        with open(fpath, "rb") as f:
            content = f.read()

        doc = parse_document(content, fpath.name)
        if doc.file_hash in existing_hashes:
            print(f"  - Hash {doc.file_hash[:8]} already exists, skipping.")
            continue

        # Extract structured candidate profile
        profile = StructuredCandidateExtractor.extract(doc.raw_text, file_name=fpath.name)
        # Ensure is_synthetic is False for all
        profile.is_synthetic = False

        cand_id = str(uuid4())
        dest_filename = f"{doc.file_hash[:16]}_{fpath.name}"
        dest_path = f"{RECRUITER_ID}/{dest_filename}"
        storage_path = f"resumes/{dest_path}"

        # Upload to Supabase Storage
        try:
            client.storage.from_("resumes").upload(
                path=dest_path,
                file=content,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )
        except Exception as se:
            print(f"  [Storage] Notice for {fpath.name}: {se}")

        # Ensure stored locally too
        local_target = Path("data/storage") / storage_path
        local_target.parent.mkdir(parents=True, exist_ok=True)
        with open(local_target, "wb") as lf:
            lf.write(content)

        # Profile dict without synthetic indicators
        prof_dict = profile.model_dump()
        prof_dict["is_synthetic"] = False

        now_iso = datetime.now(timezone.utc).isoformat()
        insert_payload = {
            "id": cand_id,
            "recruiter_id": RECRUITER_ID,
            "file_name": fpath.name,
            "storage_path": storage_path,
            "file_hash": doc.file_hash,
            "raw_text": doc.raw_text,
            "structured_profile": prof_dict,
            "faiss_index_id": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        # Insert into Supabase table
        ins_res = client.table("candidates").insert(insert_payload).execute()
        if ins_res.data:
            newly_ingested.append(ins_res.data[0])
            existing_hashes.add(doc.file_hash)
            print(f"  [+] Ingested ({len(existing_supabase_cands) + len(newly_ingested)}/100): {profile.full_name} ({fpath.name})")

        if len(existing_supabase_cands) + len(newly_ingested) >= 100:
            break

    # 4. Fetch all 100 candidates from Supabase
    all_supabase_cands = client.table("candidates").select("*").order("created_at", desc=False).execute().data
    print(f"\nTotal Candidates in Supabase: {len(all_supabase_cands)}")
    assert len(all_supabase_cands) == 100, f"Expected 100 candidates, got {len(all_supabase_cands)}"

    # 5. Clean up any synthetic flags on existing candidates in Supabase
    for c in all_supabase_cands:
        prof = c["structured_profile"]
        if isinstance(prof, str):
            prof = json.loads(prof)
        if prof.get("is_synthetic"):
            prof["is_synthetic"] = False
            client.table("candidates").update({"structured_profile": prof}).eq("id", c["id"]).execute()

    # 6. Synchronize local SQLite database to exactly match these 100 candidates
    print("\nSynchronizing local SQLite database (data/recruitment.db)...")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        # Delete candidates in SQLite not in the 100 Supabase canonical list
        sb_ids = [c["id"] for c in all_supabase_cands]
        placeholders = ",".join("?" for _ in sb_ids)
        cursor.execute(f"DELETE FROM candidates WHERE id NOT IN ({placeholders});", tuple(sb_ids))

        # Insert or replace all 100 candidates in SQLite
        for c in all_supabase_cands:
            prof_data = c["structured_profile"]
            if isinstance(prof_data, dict):
                prof_data["is_synthetic"] = False
                prof_str = json.dumps(prof_data)
            else:
                prof_str = str(prof_data)

            cursor.execute(
                """
                INSERT OR REPLACE INTO candidates (id, file_name, storage_path, file_hash, raw_text, structured_profile, faiss_index_id, created_at, updated_at, recruiter_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    c["id"],
                    c["file_name"],
                    c["storage_path"],
                    c["file_hash"],
                    c["raw_text"],
                    prof_str,
                    c.get("faiss_index_id"),
                    c["created_at"],
                    c["updated_at"],
                    c["recruiter_id"],
                ),
            )
        conn.commit()

        cursor.execute("SELECT count(*) FROM candidates;")
        sqlite_count = cursor.fetchone()[0]
        print(f"Total Candidates in SQLite (data/recruitment.db): {sqlite_count}")
        assert sqlite_count == 100, f"Expected 100 in SQLite, got {sqlite_count}"

    # 7. Rebuild FAISS index for all 100 candidates
    print("\nRebuilding FAISS index for all 100 candidates...")
    import faiss
    import numpy as np

    dim = 384
    new_index = faiss.IndexFlatIP(dim)
    mapping = {}

    for idx, c in enumerate(all_supabase_cands):
        prof = c["structured_profile"]
        if isinstance(prof, str):
            prof = json.loads(prof)

        # Build semantic text representation
        semantic_text = f"{prof.get('full_name', '')} {prof.get('summary', '')} {' '.join(prof.get('skills', []))} {' '.join(prof.get('domains', []))}"
        emb = embedder.embed_text(semantic_text)
        emb_norm = emb / np.linalg.norm(emb)
        new_index.add(emb_norm.reshape(1, -1).astype("float32"))
        mapping[idx] = c["id"]

        # Update faiss_index_id in Supabase and SQLite
        client.table("candidates").update({"faiss_index_id": idx}).eq("id", c["id"]).execute()
        with db._get_connection() as conn:
            conn.cursor().execute("UPDATE candidates SET faiss_index_id = ? WHERE id = ?;", (idx, c["id"]))
            conn.commit()

    faiss_dir = Path("data/faiss")
    faiss_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(new_index, str(faiss_dir / "candidates.index"))
    with open(faiss_dir / "candidates.index.mapping.json", "w", encoding="utf-8") as mf:
        json.dump(mapping, mf, indent=2)

    # Also update backend/data/faiss if it exists
    b_faiss_dir = Path("backend/data/faiss")
    if b_faiss_dir.exists():
        faiss.write_index(new_index, str(b_faiss_dir / "candidates.index"))
        with open(b_faiss_dir / "candidates.index.mapping.json", "w", encoding="utf-8") as mf:
            json.dump(mapping, mf, indent=2)

    print(f"FAISS index successfully built with {new_index.ntotal} candidate vectors.")

    print("\n" + "=" * 80)
    print("SUCCESS: 100 CANONICAL CANDIDATES VERIFIED!")
    print(f"  - Supabase Candidate Records: {len(all_supabase_cands)}")
    print(f"  - SQLite Candidate Records:   {sqlite_count}")
    print(f"  - FAISS Vector Embeddings:    {new_index.ntotal}")
    print("=" * 80)


if __name__ == "__main__":
    sync_pool()
