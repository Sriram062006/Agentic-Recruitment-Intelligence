import os
import sys
from pathlib import Path

print("Python version:", sys.version)

# Find directories containing CVs or resumes
for root, dirs, files in os.walk("."):
    if ".git" in root or "node_modules" in root or ".venv" in root:
        continue
    if "resume" in root.lower() or "cv" in root.lower():
        print(f"Dir: {root} -> {len(files)} files")

sys.path.insert(0, os.path.abspath("backend"))

from app.services.database.repositories.candidate_repo import CandidateRepository
repo = CandidateRepository()
all_cands = repo.list_all(limit=500)
print(f"\nTotal candidates in DB: {len(all_cands)}")

by_recruiter = {}
with_profile = 0
with_storage = 0
sample_cands = []

for c in all_cands:
    rid = str(c.recruiter_id)
    by_recruiter[rid] = by_recruiter.get(rid, 0) + 1
    if c.structured_profile:
        with_profile += 1
    if c.storage_path:
        with_storage += 1
    if len(sample_cands) < 5:
        sample_cands.append(c.model_dump())

print(f"Candidates by recruiter_id: {by_recruiter}")
print(f"With structured profile: {with_profile}")
print(f"With storage_path: {with_storage}")
print("Sample candidate keys:", list(sample_cands[0].keys()) if sample_cands else "none")
if sample_cands:
    print("Sample candidate 0:", {k: sample_cands[0][k] for k in ["id", "recruiter_id", "storage_path", "source", "full_name"] if k in sample_cands[0]})

