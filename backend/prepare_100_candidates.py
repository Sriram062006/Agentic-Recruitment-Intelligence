import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.parsers.factory import parse_document
from app.services.llm.extractor import StructuredCandidateExtractor

RECRUITER_ID = "2290592f-4210-45c3-9e64-646804df5a04"

# 1. Load the 34 candidate hashes already in Supabase
output_file = Path("backend/existing_supabase_hashes.json")

# Let's get list of files on disk
source_dir = Path("data/storage/resumes/2290592f-4210-45c3-9e64-646804df5a04")
all_files = sorted(list(source_dir.glob("*.pdf")))
print(f"Total candidate files on disk: {len(all_files)}")

# Group by role
by_role = defaultdict(list)
for f in all_files:
    role = f.name.split("_")[-1].replace(".pdf", "")
    by_role[role].append(f)

print(f"Roles found: {list(by_role.keys())}")


def prepare_sql_inserts(existing_hashes_set, target_needed=66):
    sql_batches = []
    current_batch = []
    ingested_hashes = set(existing_hashes_set)
    count = 0

    # Distribute target_needed across roles
    for role, flist in by_role.items():
        for fpath in flist:
            if count >= target_needed:
                break
            with open(fpath, "rb") as fp:
                content = fp.read()
            doc = parse_document(content, fpath.name)
            if doc.file_hash in ingested_hashes:
                continue

            prof = StructuredCandidateExtractor.extract(doc.raw_text, file_name=fpath.name)
            prof.is_synthetic = False

            cand_id = str(uuid4())
            clean_filename = fpath.name
            dest_filename = f"{doc.file_hash[:16]}_{clean_filename}"
            dest_path = f"{RECRUITER_ID}/{dest_filename}"
            storage_path = f"resumes/{dest_path}"

            # Ensure local storage file exists
            local_target = Path("data/storage") / storage_path
            local_target.parent.mkdir(parents=True, exist_ok=True)
            with open(local_target, "wb") as lf:
                lf.write(content)

            prof_dict = prof.model_dump()
            prof_dict["is_synthetic"] = False
            prof_json_str = json.dumps(prof_dict).replace("'", "''")
            raw_text_escaped = doc.raw_text.replace("'", "''")
            now_iso = datetime.now(timezone.utc).isoformat()

            sql_row = f"('{cand_id}', '{RECRUITER_ID}', '{clean_filename}', '{storage_path}', '{doc.file_hash}', '{raw_text_escaped}', '{prof_json_str}'::jsonb, '{now_iso}', '{now_iso}')"
            current_batch.append(sql_row)
            ingested_hashes.add(doc.file_hash)
            count += 1

            if len(current_batch) >= 15:
                batch_sql = "INSERT INTO candidates (id, recruiter_id, file_name, storage_path, file_hash, raw_text, structured_profile, created_at, updated_at) VALUES\n" + ",\n".join(current_batch) + ";"
                sql_batches.append(batch_sql)
                current_batch = []

    if current_batch:
        batch_sql = "INSERT INTO candidates (id, recruiter_id, file_name, storage_path, file_hash, raw_text, structured_profile, created_at, updated_at) VALUES\n" + ",\n".join(current_batch) + ";"
        sql_batches.append(batch_sql)

    print(f"Prepared {count} candidate rows in {len(sql_batches)} SQL batches.")
    return sql_batches


if __name__ == "__main__":
    # Load hashes from step 4002 output
    with open("backend/temp_hashes.json", "r", encoding="utf-8") as f:
        existing_hashes = set(json.load(f))
    print(f"Loaded {len(existing_hashes)} existing hashes.")
    batches = prepare_sql_inserts(existing_hashes, target_needed=66)
    for i, b in enumerate(batches):
        p = Path(f"backend/scratch_batch_{i+1}.sql")
        p.write_text(b, encoding="utf-8")
        print(f"Wrote {p} ({len(b)} chars)")
