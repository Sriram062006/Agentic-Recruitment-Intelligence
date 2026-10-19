import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

ctx = ssl.create_default_context()
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYWxhd216ZG5kaGxtcmVrd3Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTExMzM2NTAsImV4cCI6MjEwNjcwOTY1MH0.4dIPXY3Y85ApHkUK1nMFx7s1o53-J4eQVhACt7SQLbA"

folder = Path("backend/data/storage/resumes/2290592f-4210-45c3-9e64-646804df5a04")
files = list(folder.glob("*.*"))

for f in files:
    content = f.read_bytes()
    clean_name = re.sub(r"[^a-zA-Z0-9_\.]", "_", f.name)
    dest_path = f"2290592f-4210-45c3-9e64-646804df5a04/{clean_name}"
    quoted_path = urllib.parse.quote(dest_path)
    dest_url = f"https://xbalawmzdndhlmrekwvu.supabase.co/storage/v1/object/resumes/{quoted_path}"
    req = urllib.request.Request(
        dest_url,
        data=content,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/pdf",
            "x-upsert": "true",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        print(f"Uploaded {dest_path}: status {resp.status}")

    orig_prefix = f.name[:16]
    patch_url = f"https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates?file_hash=like.{orig_prefix}*"
    patch_req = urllib.request.Request(
        patch_url,
        data=f'{{"storage_path": "resumes/{dest_path}"}}'.encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(patch_req, context=ctx) as presp:
        print(f"Patched candidate storage_path to resumes/{dest_path}")
