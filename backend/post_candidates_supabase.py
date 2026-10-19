import json
import ssl
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.parsers.factory import parse_document
from app.services.llm.extractor import StructuredCandidateExtractor

RECRUITER_ID = "2290592f-4210-45c3-9e64-646804df5a04"

# 1. Fetch current candidates from Supabase
ctx = ssl.create_default_context()
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYWxhd216ZG5kaGxtcmVrd3Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTExMzM2NTAsImV4cCI6MjEwNjcwOTY1MH0.4dIPXY3Y85ApHkUK1nMFx7s1o53-J4eQVhACt7SQLbA"
url = "https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates?select=id,file_hash"

req = urllib.request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    existing = json.loads(resp.read().decode())
print(f"Existing in Supabase: {len(existing)}")

existing_hashes = {e["file_hash"] for e in existing}
needed = 100 - len(existing)
print(f"Needed to reach 100: {needed}")

if needed <= 0:
    print("Already at 100 candidates!")
    sys.exit(0)

source_dir = Path("data/storage/resumes/2290592f-4210-45c3-9e64-646804df5a04")
all_files = sorted(list(source_dir.glob("*.pdf")))

by_role = defaultdict(list)
for f in all_files:
    role = f.name.split("_")[-1].replace(".pdf", "")
    by_role[role].append(f)

payloads_to_insert = []
for role, flist in by_role.items():
    for fpath in flist:
        if len(payloads_to_insert) >= needed:
            break
        with open(fpath, "rb") as fp:
            content = fp.read()
        doc = parse_document(content, fpath.name)
        if doc.file_hash in existing_hashes:
            continue

        prof = StructuredCandidateExtractor.extract(doc.raw_text, file_name=fpath.name)
        prof.is_synthetic = False

        cand_id = str(uuid4())
        dest_filename = f"{doc.file_hash[:16]}_{fpath.name}"
        dest_path = f"{RECRUITER_ID}/{dest_filename}"
        storage_path = f"resumes/{dest_path}"

        # Ensure local storage file exists
        local_target = Path("data/storage") / storage_path
        local_target.parent.mkdir(parents=True, exist_ok=True)
        with open(local_target, "wb") as lf:
            lf.write(content)

        prof_dict = prof.model_dump()
        prof_dict["is_synthetic"] = False
        now_iso = datetime.now(timezone.utc).isoformat()

        payload = {
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
        payloads_to_insert.append(payload)
        existing_hashes.add(doc.file_hash)

print(f"Prepared {len(payloads_to_insert)} payloads to insert into Supabase.")

# Post in chunks of 10
chunk_size = 10
for i in range(0, len(payloads_to_insert), chunk_size):
    chunk = payloads_to_insert[i : i + chunk_size]
    data_bytes = json.dumps(chunk).encode("utf-8")
    post_url = "https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates"
    post_req = urllib.request.Request(
        post_url,
        data=data_bytes,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    with urllib.request.urlopen(post_req, context=ctx, timeout=15) as p_resp:
        print(f"Inserted batch {i//chunk_size + 1} ({len(chunk)} candidates). Status: {p_resp.status}")

# Verify total
req2 = urllib.request.Request("https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates?select=id", headers={"apikey": key, "Authorization": f"Bearer {key}"})
with urllib.request.urlopen(req2, context=ctx, timeout=10) as resp2:
    final_list = json.loads(resp2.read().decode())
print(f"\nFinal count in Supabase: {len(final_list)} candidates!")
