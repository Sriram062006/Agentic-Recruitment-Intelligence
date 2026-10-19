import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path
import faiss
import numpy as np
import sqlite3

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.services.embeddings.sentence_transformer import SentenceTransformerService

ctx = ssl.create_default_context()
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYWxhd216ZG5kaGxtcmVrd3Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTExMzM2NTAsImV4cCI6MjEwNjcwOTY1MH0.4dIPXY3Y85ApHkUK1nMFx7s1o53-J4eQVhACt7SQLbA"
url = "https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates?select=*&order=created_at.asc"

req = urllib.request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    supabase_cands = json.loads(resp.read().decode())

print(f"Fetched {len(supabase_cands)} candidates from Supabase.")
assert len(supabase_cands) == 100, f"Expected 100 candidates in Supabase, got {len(supabase_cands)}"

# 1. Sync local SQLite database
print("\nSyncing local SQLite databases (data/recruitment.db and backend/data/recruitment.db)...")
db_paths = ["data/recruitment.db", "backend/data/recruitment.db"]

for db_path in db_paths:
    if not Path(db_path).parent.exists():
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM candidates;")
    for c in supabase_cands:
        prof_data = c["structured_profile"]
        if isinstance(prof_data, dict):
            prof_data["is_synthetic"] = False
            prof_str = json.dumps(prof_data)
        else:
            prof_str = str(prof_data)

        cur.execute(
            """
            INSERT INTO candidates (id, file_name, storage_path, file_hash, raw_text, structured_profile, faiss_index_id, created_at, updated_at, recruiter_id)
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
    cur.execute("SELECT count(*) FROM candidates;")
    cnt = cur.fetchone()[0]
    print(f"  {db_path}: {cnt} candidates successfully synced.")
    assert cnt == 100

# 2. Rebuild FAISS index
print("\nRebuilding FAISS index for all 100 candidates...")
embedder = SentenceTransformerService()
dim = 384
index = faiss.IndexFlatIP(dim)
mapping = {}

update_payloads = []
for idx, c in enumerate(supabase_cands):
    prof = c["structured_profile"]
    if isinstance(prof, str):
        prof = json.loads(prof)

    name = prof.get("full_name", "")
    summary = prof.get("summary", "")
    skills = " ".join(prof.get("skills", []))
    domains = " ".join(prof.get("domains", []))
    semantic_text = f"{name} {summary} {skills} {domains}"

    emb = embedder.embed_text(semantic_text)
    emb_norm = emb / np.linalg.norm(emb)
    index.add(emb_norm.reshape(1, -1).astype("float32"))
    mapping[idx] = c["id"]

    update_payloads.append((idx, c["id"]))

# Save FAISS files
for d in ["data/faiss", "backend/data/faiss"]:
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(p / "candidates.index"))
    with open(p / "candidates.index.mapping.json", "w", encoding="utf-8") as mf:
        json.dump(mapping, mf, indent=2)
    print(f"  Saved FAISS index to {d}/candidates.index with {index.ntotal} vectors.")

# Update faiss_index_id in SQLite
for db_path in db_paths:
    if not Path(db_path).parent.exists():
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for idx, cid in update_payloads:
        cur.execute("UPDATE candidates SET faiss_index_id = ? WHERE id = ?;", (idx, cid))
    conn.commit()

# Batch update faiss_index_id in Supabase
print("\nUpdating faiss_index_id in Supabase...")
for idx, cid in update_payloads:
    patch_url = f"https://xbalawmzdndhlmrekwvu.supabase.co/rest/v1/candidates?id=eq.{cid}"
    patch_req = urllib.request.Request(
        patch_url,
        data=json.dumps({"faiss_index_id": idx}).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(patch_req, context=ctx, timeout=5) as presp:
        pass

print("FAISS index IDs successfully synced in Supabase!")
print("\n" + "=" * 80)
print("SUCCESS: ALL 100 CANONICAL CANDIDATES ARE SYNCHRONIZED AND VECTOR INDEXED!")
print("=" * 80)
