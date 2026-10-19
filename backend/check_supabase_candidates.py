import os
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, os.path.abspath("backend"))

from app.services.database.supabase_client import get_db

db = get_db()
print("is_supabase_active:", db.is_supabase_active)

if db.is_supabase_active:
    client = db.supabase
    res = client.table("candidates").select("id, recruiter_id, file_name, is_synthetic").execute()
    print("Supabase candidates count:", len(res.data))
    r_counts = {}
    syn_counts = {}
    for r in res.data:
        rid = str(r.get("recruiter_id"))
        r_counts[rid] = r_counts.get(rid, 0) + 1
        syn = r.get("is_synthetic")
        syn_counts[syn] = syn_counts.get(syn, 0) + 1
    print("Supabase by recruiter_id:", r_counts)
    print("Supabase by is_synthetic:", syn_counts)
    print("Sample Supabase candidates:", res.data[:3])

with db._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM candidates;")
    print("SQLite count:", cursor.fetchone()[0])
    cursor.execute("SELECT recruiter_id, count(*) FROM candidates GROUP BY recruiter_id;")
    print("SQLite by recruiter_id:", cursor.fetchall())
    cursor.execute("SELECT is_synthetic, count(*) FROM candidates GROUP BY is_synthetic;")
    print("SQLite by is_synthetic:", cursor.fetchall())
