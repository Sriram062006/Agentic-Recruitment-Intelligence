import json
import sqlite3
from pathlib import Path

step_file = Path(r"C:\Users\srira\.gemini\antigravity\brain\b69e489c-4cfe-42cd-8956-d8bb70598924\.system_generated\steps\4599\output.txt")
with open(step_file, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

res_str = raw_data["result"]
start_tag = res_str.find("[{\"json_agg\":")
end_tag = res_str.rfind("}]") + 2
json_substring = res_str[start_tag:end_tag]

parsed = json.loads(json_substring)
cands = parsed[0]["json_agg"]

print(f"Successfully loaded {len(cands)} candidates from Supabase dump")

for db_path in ["data/recruitment.db", "backend/data/recruitment.db"]:
    p = Path(db_path)
    if not p.exists():
        continue
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    cur.execute("DELETE FROM candidates;")
    for c in cands:
        prof_str = json.dumps(c["structured_profile"]) if isinstance(c["structured_profile"], dict) else str(c["structured_profile"])
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
    print(f"Restored {cnt} candidates into {db_path}")
    conn.close()
