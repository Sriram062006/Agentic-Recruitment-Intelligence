import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# 1. Fetch all 100 candidates from Supabase
ctx = ssl.create_default_context()
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYWxhd216ZG5kaGxtcmVrd3Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTExMzM2NTAsImV4cCI6MjEwNjcwOTY1MH0.4dIPXY3Y85ApHkUK1nMFx7s1o53-J4eQVhACt7SQLbA"
url = "https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates?select=id,file_name,storage_path"

req = urllib.request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    candidates = json.loads(resp.read().decode())
print(f"Total candidates in Supabase: {len(candidates)}")

uploaded = 0
for cand in candidates:
    sp = cand["storage_path"]
    rel_path = sp
    if rel_path.startswith("resumes/"):
        rel_path = rel_path[len("resumes/") :]

    local_path = Path("data/storage/resumes") / rel_path
    if not local_path.exists():
        # check in data/storage/resumes/2290592f-4210-45c3-9e64-646804df5a04
        base_name = Path(rel_path).name
        # Search anywhere in data/storage
        candidates_found = list(Path("data/storage").rglob(base_name))
        if candidates_found:
            local_path = candidates_found[0]

    if not local_path.exists():
        print(f"  [WARN] Local file not found: {sp}")
        continue

    content = local_path.read_bytes()

    # Upload to Supabase Storage via REST
    dest_url = f"https://xbalawmzdndhlmrekwvu.supabase.co/storage/v1/object/resumes/{rel_path}"
    upload_req = urllib.request.Request(
        dest_url,
        data=content,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/pdf" if rel_path.endswith(".pdf") else "application/octet-stream",
            "x-upsert": "true",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(upload_req, context=ctx, timeout=10) as u_resp:
            uploaded += 1
            if uploaded % 10 == 0:
                print(f"  Uploaded {uploaded}/{len(candidates)} resume files to Supabase Storage...")
    except urllib.error.HTTPError as he:
        if he.code in (400, 409):
            # Already exists
            uploaded += 1
        else:
            print(f"  HTTP error uploading {rel_path}: {he.code}")
    except Exception as e:
        print(f"  Error uploading {rel_path}: {e}")

print(f"\nCompleted storage upload check. {uploaded} candidate files in Supabase Storage!")
