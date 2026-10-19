"""
Live End-to-End Validation Script for Hans Veldman CV and Senior IT Project Manager JD.
Verifies full-fidelity extraction, sentence transformer embeddings, FAISS indexing,
deterministic hybrid scoring, requirement-by-requirement audit, and grounded explanation.
"""

import json
import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.parsers.docx_parser import DOCXParser
from app.parsers.pdf_parser import PDFParser
from app.services.llm.gemini_provider import GeminiLLMProvider
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.vector_store.faiss_store import FAISSVectorStore
from app.pipeline.scorer import calculate_deterministic_fitment
from app.pipeline.explainer import generate_fitment_explanation
from app.schemas.evaluation import FitmentWeightsConfig, HeuristicConfig
from app.core.orchestrator import build_candidate_semantic_text, build_job_semantic_text

def run_validation():
    cv_path = backend_dir / "data" / "sample_validation" / "C.V. Harmannus Robert Frank (Hans) Veldman Short (1).docx"
    jd_path = backend_dir / "data" / "sample_validation" / "M_Jobs_0210_Senior IT Project Manager.pdf"

    print("=" * 80)
    print("STEP 1: DOCUMENT PARSING")
    print("=" * 80)
    docx_parser = DOCXParser()
    cv_bytes = cv_path.read_bytes()
    cv_doc = docx_parser.parse(cv_bytes, cv_path.name)
    print(f"CV File: {cv_doc.file_name}")
    print(f"CV Raw Text Length: {len(cv_doc.raw_text)} chars")
    print(f"CV Sections Count: {cv_doc.page_or_section_count}")

    pdf_parser = PDFParser()
    jd_bytes = jd_path.read_bytes()
    jd_doc = pdf_parser.parse(jd_bytes, jd_path.name)
    print(f"\nJD File: {jd_doc.file_name}")
    print(f"JD Raw Text Length: {len(jd_doc.raw_text)} chars")
    print(f"JD Page Count: {jd_doc.page_or_section_count}")

    print("\n" + "=" * 80)
    print("STEP 2: FULL-FIDELITY STRUCTURED EXTRACTION")
    print("=" * 80)
    llm_provider = GeminiLLMProvider()
    print(f"Gemini Provider Client Active: {llm_provider.client is not None}")
    print(f"Gemini Model: {llm_provider.model_name}")

    print("\nExtracting Candidate Profile...")
    cand_profile = llm_provider.extract_candidate_profile(cv_doc.raw_text, file_name=cv_doc.file_name)
    print(f"Candidate Name: {cand_profile.full_name}")
    print(f"Total Experience: {cand_profile.total_experience_years} years")
    print(f"Highest Qualification: {cand_profile.highest_qualification}")
    print(f"Career History Count: {len(cand_profile.experience_history)} positions")
    for idx, exp in enumerate(cand_profile.experience_history, 1):
        print(f"  {idx}. {exp.title} | {exp.organization or exp.client} | {exp.duration_years} yrs ({exp.start_date} - {exp.end_date})")
    print(f"Skills Extracted: {len(cand_profile.skills)} skills -> {cand_profile.skills[:10]}...")
    print(f"Certifications: {[c.name for c in cand_profile.certifications]}")
    print(f"Languages: {cand_profile.languages}")

    print("\nExtracting Job Profile...")
    job_profile = llm_provider.extract_job_profile(jd_doc.raw_text)
    print(f"Job Title: {job_profile.title}")
    print(f"Company/Client: {job_profile.company_or_client}")
    print(f"Location: {job_profile.location} | Remote: {job_profile.remote_work}")
    print(f"Min Experience: {job_profile.min_experience_years} years")
    print(f"Required Qualification: {job_profile.required_qualification}")
    print(f"Key Responsibilities Count: {len(job_profile.key_responsibilities)}")
    for idx, resp in enumerate(job_profile.key_responsibilities, 1):
        print(f"  {idx}. {resp[:80]}...")
    print(f"Must-Have Requirements Count: {len(job_profile.must_have_requirements)}")
    print(f"Should-Have Requirements Count: {len(job_profile.should_have_requirements)}")
    print(f"Required Skills: {job_profile.required_skills}")

    print("\n" + "=" * 80)
    print("STEP 3: DENSE SEMANTIC TEXT GENERATION & EMBEDDINGS")
    print("=" * 80)
    cand_sem_text = build_candidate_semantic_text(cand_profile)
    job_sem_text = build_job_semantic_text(job_profile)
    print(f"Candidate Semantic Text Length: {len(cand_sem_text)} chars")
    print(f"Job Semantic Text Length: {len(job_sem_text)} chars")

    embed_service = SentenceTransformerService("all-MiniLM-L6-v2")
    cand_vec = embed_service.embed_text(cand_sem_text)
    job_vec = embed_service.embed_text(job_sem_text)

    cand_norm = float((cand_vec ** 2).sum() ** 0.5)
    job_norm = float((job_vec ** 2).sum() ** 0.5)
    print(f"Candidate Vector Dim: {cand_vec.shape[0]}, L2 Norm: {cand_norm:.6f}")
    print(f"Job Vector Dim: {job_vec.shape[0]}, L2 Norm: {job_norm:.6f}")

    print("\n" + "=" * 80)
    print("STEP 4: VECTOR SIMILARITY & DETERMINISTIC HYBRID FITMENT")
    print("=" * 80)
    import uuid
    faiss_store = FAISSVectorStore(dimension=384)
    cand_id = uuid.uuid4()
    job_id = uuid.uuid4()
    faiss_store.add_candidate(cand_id, cand_vec)

    semantic_sim = faiss_store.compute_similarity(cand_id, job_vec)
    print(f"FAISS Inner Product (Cosine Similarity): {semantic_sim:.4f}")

    weights = FitmentWeightsConfig(
        semantic_weight=0.35,
        skill_weight=0.35,
        experience_weight=0.20,
        qualification_weight=0.10,
    )
    heuristics = HeuristicConfig(
        alpha_skill_weight=0.80,
        beta_experience_penalty=1.50,
        fitment_strong_threshold=0.75,
        fitment_moderate_threshold=0.50,
    )

    fitment_signals = calculate_deterministic_fitment(
        candidate=cand_profile,
        job=job_profile,
        semantic_similarity=semantic_sim,
        weights=weights,
        heuristics=heuristics,
    )
    print("\nDeterministic Scores:")
    print(f"  Semantic Score (S_sem):      {fitment_signals['semantic_score']:.4f}")
    print(f"  Skill Overlap Score (S_skill):{fitment_signals['skill_score']:.4f}")
    print(f"  Experience Fit Score (S_exp): {fitment_signals['experience_score']:.4f}")
    print(f"  Qualification Score (S_qual): {fitment_signals['qualification_score']:.4f}")
    print(f"  COMPOSITE FITMENT SCORE:      {fitment_signals['composite_score']:.4f} ({fitment_signals['composite_score']*100:.1f}%)")
    print(f"  Matched Required Skills:      {fitment_signals['matched_required_skills']}")
    print(f"  Missing Required Skills:      {fitment_signals['missing_required_skills']}")

    print("\n" + "=" * 80)
    print("STEP 5: REQUIREMENT-BY-REQUIREMENT AUDIT & GROUNDED EXPLAINABILITY")
    print("=" * 80)
    explainability = generate_fitment_explanation(
        candidate=cand_profile,
        job=job_profile,
        fitment_signals=fitment_signals,
        llm_provider=llm_provider,
        candidate_raw_text=cv_doc.raw_text,
    )

    print(f"\nRecruiter Recommendation: {explainability.recruiter_recommendation}")
    print(f"Recommendation Rationale: {explainability.recommendation_rationale}")

    print("\nRequirement Analysis Breakdown:")
    for idx, r in enumerate(explainability.requirement_analysis, 1):
        print(f"[{idx}] {r['type']} ({r['status']}): {r['requirement']}")
        print(f"    Evidence: {r['evidence']}")

    # Save summary report artifact
    report = {
        "candidate": cand_profile.model_dump(),
        "job": job_profile.model_dump(),
        "candidate_semantic_text": cand_sem_text,
        "job_semantic_text": job_sem_text,
        "fitment_signals": fitment_signals,
        "explainability": explainability.model_dump(),
    }
    output_path = backend_dir / "data" / "sample_validation" / "validation_result.json"
    output_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved complete validation report to {output_path}")

if __name__ == "__main__":
    run_validation()
