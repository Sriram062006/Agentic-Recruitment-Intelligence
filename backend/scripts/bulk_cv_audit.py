"""
Bulk CV Ingestion and Extraction Audit Script.
Tests 20 real PDF/DOCX resumes from the candidate pool and verifies end-to-end extraction quality,
deduplication, Unicode safety, and database persistence.
"""

import glob
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Configure UTF-8 output if possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.parsers.factory import parse_document
from app.services.llm.extractor import StructuredCandidateExtractor
from app.services.database.repositories.candidate_repo import CandidateRepository


def run_bulk_audit(sample_size: int = 20):
    folder = r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)"
    files = glob.glob(os.path.join(folder, "*.*"))
    pdf_and_docx = [f for f in files if f.endswith(".pdf") or f.endswith(".docx")]
    selected_files = pdf_and_docx[:sample_size]

    print("============================================================")
    print(f"BULK CV EXTRACTION & AUDIT (Target: {len(selected_files)} CVs)")
    print("============================================================")

    total_cvs = len(selected_files)
    successfully_parsed = 0
    successfully_extracted = 0
    successfully_persisted = 0
    duplicates = 0
    failed = 0
    extraction_failures = 0
    database_failures = 0

    repo = CandidateRepository()
    seen_hashes = set()

    results = []

    for idx, filepath in enumerate(selected_files, start=1):
        filename = os.path.basename(filepath)
        print(f"\n[{idx}/{total_cvs}] Processing: {filename}")

        # 1. Parse
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            doc = parse_document(content, filename)
            successfully_parsed += 1
            print(f"  [OK] Parsed ({doc.page_or_section_count} pages/sections, {len(doc.raw_text)} chars)")
        except Exception as pe:
            print(f"  [FAIL] Parsing FAILED: {pe}")
            failed += 1
            continue

        # Check hash
        if doc.file_hash in seen_hashes:
            print(f"  [DUP] Duplicate hash detected ({doc.file_hash[:8]})")
            duplicates += 1
            continue
        seen_hashes.add(doc.file_hash)

        # 2. Extract
        try:
            profile = StructuredCandidateExtractor.extract(doc.raw_text, file_name=filename)
            successfully_extracted += 1
            print(
                f"  [OK] Extracted: {profile.full_name} | {profile.total_experience_years} yrs exp | "
                f"{len(profile.skills)} skills | {len(profile.experience_history)} roles | "
                f"{len(profile.education)} degrees | {len(profile.certifications)} certs"
            )
        except Exception as ee:
            print(f"  [FAIL] Extraction FAILED: {ee}")
            extraction_failures += 1
            failed += 1
            continue

        # 3. Persist
        try:
            saved = repo.create(
                file_name=filename,
                storage_path=f"test_pool/{doc.file_hash[:16]}_{filename}",
                file_hash=doc.file_hash,
                raw_text=doc.raw_text,
                structured_profile=profile,
            )
            successfully_persisted += 1
            print(f"  [OK] Persisted to DB (ID: {saved.id})")
        except Exception as de:
            print(f"  [FAIL] DB Persistence FAILED: {de}")
            database_failures += 1
            failed += 1
            continue

        results.append({
            "filename": filename,
            "name": profile.full_name,
            "skills_count": len(profile.skills),
            "exp_years": profile.total_experience_years,
            "roles_count": len(profile.experience_history),
            "degree": profile.highest_qualification,
        })

    print("\n============================================================")
    print("BULK AUDIT SUMMARY")
    print("============================================================")
    print(f"Total CVs Tested:          {total_cvs}")
    print(f"Successfully Parsed:       {successfully_parsed}")
    print(f"Successfully Extracted:    {successfully_extracted}")
    print(f"Successfully Persisted:    {successfully_persisted}")
    print(f"Duplicates:                {duplicates}")
    print(f"Extraction Failures:       {extraction_failures}")
    print(f"Database Failures:         {database_failures}")
    print(f"Total Failed:              {failed}")
    rate = (successfully_persisted / total_cvs) * 100 if total_cvs > 0 else 0
    print(f"Success Rate:              {rate:.1f}%")
    print("============================================================")


if __name__ == "__main__":
    run_bulk_audit(20)
