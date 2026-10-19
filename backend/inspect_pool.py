import sqlite3
import json

conn = sqlite3.connect("data/recruitment.db")
c = conn.cursor()
c.execute("SELECT id, recruiter_id, file_name, storage_path, structured_profile FROM candidates")
rows = c.fetchall()
print(f"Total rows: {len(rows)}")

recruiter_counts = {}
synthetic_flag_counts = {}
file_names = []

for row in rows:
    cid, rid, fname, spath, prof_str = row
    prof = json.loads(prof_str)
    is_syn = prof.get("is_synthetic", False)
    
    recruiter_counts[rid] = recruiter_counts.get(rid, 0) + 1
    synthetic_flag_counts[is_syn] = synthetic_flag_counts.get(is_syn, 0) + 1
    file_names.append((fname, is_syn, rid, prof.get("full_name")))

print("Recruiter counts:", recruiter_counts)
print("Synthetic flag counts:", synthetic_flag_counts)

print("\nSample Non-Synthetic (first 10):")
non_syn = [f for f in file_names if not f[1]]
for f in non_syn[:10]:
    print(f"  {f[0]} | Name: {f[3]} | Recruiter: {f[2]}")
print(f"Total Non-Synthetic: {len(non_syn)}")

print("\nSample Synthetic (first 10):")
syn = [f for f in file_names if f[1]]
for f in syn[:10]:
    print(f"  {f[0]} | Name: {f[3]} | Recruiter: {f[2]}")
print(f"Total Synthetic: {len(syn)}")
