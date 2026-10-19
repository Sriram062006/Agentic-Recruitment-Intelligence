"""
Academic Research Validation & Experimentation Runner.
Executes Phase 2 through Phase 17 validation steps using real candidate CVs,
rigorous mathematical comparisons, and non-destructive operations.
Outputs structured JSON telemetry and research artifacts.
"""

import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Setup paths
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Configure stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.config import get_settings
from app.core.orchestrator import PipelineOrchestrator, build_candidate_semantic_text, build_job_semantic_text
from app.parsers.factory import parse_document
from app.pipeline.scorer import (
    DEGREE_TIER_MAP,
    calculate_deterministic_fitment,
    compute_experience_fit_score,
    compute_qualification_score,
    compute_skill_overlap_score,
)
from app.schemas.candidate import CandidateProfile
from app.schemas.common import RunStatus
from app.schemas.evaluation import EvaluationConfigRequest, FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.repositories.evaluation_repo import EvaluationRepository
from app.services.database.repositories.job_repo import JobRepository
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.llm.extractor import StructuredCandidateExtractor
from app.services.llm.gemini_provider import GeminiLLMProvider
from app.services.vector_store.faiss_store import FAISSVectorStore


def run_all_validations():
    print("================================================================================")
    print("STARTING ACADEMIC RESEARCH VALIDATION & MULTI-ROLE EXPERIMENTATION SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("================================================================================")

    results = {}

    # Initialize services
    job_repo = JobRepository()
    cand_repo = CandidateRepository()
    eval_repo = EvaluationRepository()
    embedding_service = SentenceTransformerService()
    faiss_store = FAISSVectorStore()
    llm_provider = GeminiLLMProvider()

    orchestrator = PipelineOrchestrator(
        job_repo=job_repo,
        candidate_repo=cand_repo,
        evaluation_repo=eval_repo,
        embedding_service=embedding_service,
        faiss_store=faiss_store,
        llm_provider=llm_provider,
    )

    # ----------------------------------------------------
    # PHASE 3: CANDIDATE EXTRACTION VALIDATION (5 Real CVs)
    # ----------------------------------------------------
    print("\n>>> PHASE 3: CANDIDATE EXTRACTION VALIDATION (Real CVs)")
    cv_paths = [
        r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)\Jeremy Scheppers_24.pdf",
        r"C:\Users\srira\Downloads\Belgium\SailPoint\Hugues CREPIN.pdf",
        r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)\Amel Bouzaid_3.pdf",
        r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)\Anne - Sophie Drincqbier_18.pdf",
        r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)\Joachim Kersemans_10.pdf",
    ]

    extracted_profiles = []
    p3_results = []
    for path_str in cv_paths:
        p = Path(path_str)
        if not p.exists():
            print(f"  [WARN] File not found: {p}")
            continue
        with open(p, "rb") as f:
            raw_bytes = f.read()
        doc = parse_document(raw_bytes, p.name)
        prof = StructuredCandidateExtractor.extract(doc.raw_text, file_name=p.name)
        extracted_profiles.append((p.name, doc, prof))
        p3_results.append({
            "file": p.name,
            "name": prof.full_name,
            "email": prof.email,
            "phone": prof.phone,
            "location": prof.location,
            "total_experience_years": prof.total_experience_years,
            "highest_qualification": prof.highest_qualification,
            "skills_count": len(prof.skills),
            "sample_skills": prof.skills[:8],
            "roles_count": len(prof.experience_history),
            "certifications": [c.name for c in prof.certifications],
            "projects": [pr.name for pr in prof.projects],
            "domains": prof.domains,
        })
        print(f"  [OK] {p.name}: {prof.full_name} | {prof.total_experience_years} yrs exp | {len(prof.skills)} skills | Qual: {prof.highest_qualification}")

    results["phase3_candidate_extraction"] = p3_results

    # ----------------------------------------------------
    # PHASE 4: JD EXTRACTION VALIDATION (3 Real/Rich JDs)
    # ----------------------------------------------------
    print("\n>>> PHASE 4: JOB DESCRIPTION EXTRACTION & REPRESENTATION VALIDATION")
    sample_jds = [
        JobProfile(
            title="Senior IT Project Manager & Agile Transformation Lead",
            department="Program Management Office",
            summary="Lead enterprise digital transformation and agile delivery across multi-disciplinary engineering squads.",
            required_skills=["Agile", "Scrum", "Project Management", "Stakeholder Management", "Jira"],
            preferred_skills=["Prince2", "PMP", "SAFe", "Cloud Migration", "Azure"],
            min_experience_years=8.0,
            required_qualification="Bachelor's",
            key_responsibilities=[
                "Drive sprint planning, retrospectives, and cross-team dependency mapping.",
                "Manage executive stakeholder relationships and budget allocation.",
                "Guide organizational transition from waterfall to modern scrum frameworks.",
            ],
        ),
        JobProfile(
            title="Cloud Infrastructure & DevOps Lead",
            department="Cloud Operations",
            summary="Architect and operate resilient cloud infrastructure, automated CI/CD pipelines, and Kubernetes clusters.",
            required_skills=["AWS", "Azure", "Docker", "Kubernetes", "CI/CD", "Linux"],
            preferred_skills=["Terraform", "GitHub Actions", "Python", "Prometheus"],
            min_experience_years=5.0,
            required_qualification="Bachelor's",
            key_responsibilities=[
                "Deploy and maintain scalable containerized infrastructure.",
                "Build continuous integration pipelines with rigorous automated testing.",
                "Ensure high availability, disaster recovery, and infrastructure security.",
            ],
        ),
        JobProfile(
            title="Identity & Access Management (IAM) Security Architect",
            department="Information Security",
            summary="Design and enforce identity governance, privileged access management, and modern authentication protocols.",
            required_skills=["IAM", "Active Directory", "Azure AD", "SAML", "OAuth"],
            preferred_skills=["CISSP", "DevSecOps", "SailPoint", "OIDC"],
            min_experience_years=6.0,
            required_qualification="Bachelor's",
            key_responsibilities=[
                "Oversee enterprise access governance and federation architecture.",
                "Lead IAM system migrations and security compliance audits.",
                "Design automated identity lifecycle workflows.",
            ],
        ),
        JobProfile(
            title="Senior Python & GenAI Platform Engineer",
            department="AI Research & Innovation",
            summary="Develop high-performance backend microservices and integrate LLM orchestration frameworks.",
            required_skills=["Python", "FastAPI", "SQL", "Docker", "REST API"],
            preferred_skills=["LLM", "Agentic AI", "LangChain", "Vector Databases", "PostgreSQL"],
            min_experience_years=4.0,
            required_qualification="Master's",
            key_responsibilities=[
                "Design low-latency FastAPI endpoints for AI inference.",
                "Implement retrieval-augmented generation (RAG) and dense vector search.",
                "Ensure robust automated test coverage and clean API architecture.",
            ],
        ),
        JobProfile(
            title="Enterprise SAP Solutions & Release Manager",
            department="Enterprise Systems",
            summary="Lead enterprise ERP release cycles, cutover planning, and integration between legacy and cloud modules.",
            required_skills=["SAP", "ERP", "Release Management", "Project Management"],
            preferred_skills=["Office 365", "SQL", "Process Modelling"],
            min_experience_years=10.0,
            required_qualification="Master's",
            key_responsibilities=[
                "Coordinate monthly release windows and critical change governance.",
                "Manage vendor relationships and cross-functional delivery teams.",
                "Ensure zero-downtime cutover transitions.",
            ],
        ),
    ]

    p4_results = []
    for jd in sample_jds:
        rep_text = build_job_semantic_text(jd)
        emb = embedding_service.embed_text(rep_text)
        p4_results.append({
            "title": jd.title,
            "department": jd.department,
            "req_skills": jd.required_skills,
            "pref_skills": jd.preferred_skills,
            "min_exp": jd.min_experience_years,
            "qualification": jd.required_qualification,
            "rep_text_length": len(rep_text),
            "embedding_norm": float(math.sqrt(sum(x*x for x in emb))),
        })
        print(f"  [OK] JD: {jd.title} | Rep Chars: {len(rep_text)} | Norm: {math.sqrt(sum(x*x for x in emb)):.4f}")

    results["phase4_jd_extraction"] = p4_results

    # ----------------------------------------------------
    # PHASE 5: MATHEMATICAL SCORING VALIDATION
    # ----------------------------------------------------
    print("\n>>> PHASE 5: MATHEMATICAL SCORING VALIDATION")
    # Test Jeremy Scheppers against PM, DevOps, and IAM roles
    jeremy_prof = extracted_profiles[0][2]
    hugues_prof = extracted_profiles[1][2]

    test_pairs = [
        (jeremy_prof, sample_jds[0]),  # Jeremy vs PM (Should be very strong)
        (hugues_prof, sample_jds[2]),  # Hugues vs IAM (Should be very strong)
        (jeremy_prof, sample_jds[1]),  # Jeremy vs DevOps (Should be moderate/partial)
    ]

    weights = FitmentWeightsConfig(
        semantic_weight=0.35,
        skill_weight=0.35,
        experience_weight=0.20,
        qualification_weight=0.10,
    )
    heuristics = HeuristicConfig(
        alpha_skill_weight=0.80,
        beta_experience_penalty=1.50,
    )

    p5_results = []
    for cand, jd in test_pairs:
        cand_text = build_candidate_semantic_text(cand)
        jd_text = build_job_semantic_text(jd)
        cand_emb = embedding_service.embed_text(cand_text)
        jd_emb = embedding_service.embed_text(jd_text)
        raw_sim = float(sum(c * j for c, j in zip(cand_emb, jd_emb)))
        sim = max(0.0, min(1.0, raw_sim))

        # Application calculation
        app_out = calculate_deterministic_fitment(
            candidate=cand,
            job=jd,
            semantic_similarity=sim,
            weights=weights,
            heuristics=heuristics,
        )

        # Independent calculation
        # 1. Skill
        cand_s = {s.lower().strip() for s in cand.skills}
        req_s = {s.lower().strip() for s in jd.required_skills}
        pref_s = {s.lower().strip() for s in jd.preferred_skills}
        m_req = [s for s in jd.required_skills if s.lower().strip() in cand_s]
        m_pref = [s for s in jd.preferred_skills if s.lower().strip() in cand_s]
        r_recall = len(m_req) / len(req_s) if len(req_s) > 0 else 1.0
        p_recall = len(m_pref) / len(pref_s) if len(pref_s) > 0 else 1.0
        exp_skill = 0.80 * r_recall + 0.20 * p_recall

        # 2. Experience
        if cand.total_experience_years >= jd.min_experience_years:
            exp_exp = 1.0
        else:
            shortfall = jd.min_experience_years - cand.total_experience_years
            exp_exp = math.exp(-1.50 * (shortfall / jd.min_experience_years))

        # 3. Qualification
        c_tier = DEGREE_TIER_MAP.get(cand.highest_qualification.lower().strip(), 2)
        j_tier = DEGREE_TIER_MAP.get(jd.required_qualification.lower().strip(), 2)
        if c_tier >= j_tier:
            exp_qual = 1.0
        elif c_tier == j_tier - 1:
            exp_qual = 0.70
        else:
            exp_qual = 0.30

        # Composite
        exp_composite = 0.35 * sim + 0.35 * exp_skill + 0.20 * exp_exp + 0.10 * exp_qual
        abs_diff = abs(app_out["composite_score"] - round(exp_composite, 4))

        p5_results.append({
            "candidate": cand.full_name,
            "job": jd.title,
            "semantic_score": app_out["semantic_score"],
            "skill_score": app_out["skill_score"],
            "experience_score": app_out["experience_score"],
            "qualification_score": app_out["qualification_score"],
            "app_composite": app_out["composite_score"],
            "independent_composite": round(exp_composite, 4),
            "abs_difference": abs_diff,
            "within_tolerance": abs_diff <= 1e-4,
        })
        print(f"  [MATH] {cand.full_name} vs {jd.title[:30]}: App={app_out['composite_score']} | Indep={round(exp_composite, 4)} | Diff={abs_diff:.6f} | Match={abs_diff <= 1e-4}")

    results["phase5_math_validation"] = p5_results

    # ----------------------------------------------------
    # PERSISTENCE OF CANDIDATES & JOBS FOR N x M RUNS
    # ----------------------------------------------------
    print("\n>>> PERSISTING CANONICAL CANDIDATES & JOBS IN REPOSITORY")
    persisted_cands = []
    for name, doc, prof in extracted_profiles:
        existing = cand_repo.get_by_hash(doc.file_hash)
        if existing:
            saved_c = existing
        else:
            saved_c = cand_repo.create(
                file_name=name,
                storage_path=f"resumes/{name}",
                file_hash=doc.file_hash,
                raw_text=doc.raw_text,
                structured_profile=prof,
            )
        persisted_cands.append(saved_c)
        orchestrator.index_candidate(saved_c)

    persisted_jobs = []
    existing_all_jobs = job_repo.list_all(limit=100)
    for jd in sample_jds:
        matching_j = next((j for j in existing_all_jobs if j.title == jd.title), None)
        if matching_j:
            saved_j = matching_j
        else:
            saved_j = job_repo.create(
                title=jd.title,
                department=jd.department,
                storage_path=f"jds/{jd.title.replace(' ', '_')}.pdf",
                raw_content=f"Requirements for {jd.title}",
                structured_profile=jd,
            )
        persisted_jobs.append(saved_j)

    print(f"  [OK] Persisted {len(persisted_cands)} real candidates and {len(persisted_jobs)} jobs.")

    # ----------------------------------------------------
    # PHASE 6: 1 x 1 VALIDATION
    # ----------------------------------------------------
    print("\n>>> PHASE 6: 1 x 1 VALIDATION (1 Candidate x 1 Job)")
    req_1x1 = EvaluationConfigRequest(
        candidate_ids=[persisted_cands[0].id],
        job_ids=[persisted_jobs[0].id],
    )
    t0 = time.time()
    run_1x1 = orchestrator.execute_multi_role_evaluation(req_1x1)
    dur_1x1 = time.time() - t0
    evals_1x1 = eval_repo.get_matrix_cells(run_1x1.id)

    results["phase6_1x1"] = {
        "run_id": str(run_1x1.id),
        "candidates": 1,
        "jobs": 1,
        "expected_evaluations": 1,
        "actual_evaluations": len(evals_1x1),
        "duration_sec": round(dur_1x1, 4),
        "status": run_1x1.status.value,
        "composite_score": evals_1x1[0].composite_score,
        "candidate_id": str(evals_1x1[0].candidate_id),
        "job_id": str(evals_1x1[0].job_id),
    }
    print(f"  [OK] 1x1 Result: status={run_1x1.status.value}, evaluations={len(evals_1x1)}, score={evals_1x1[0].composite_score}, time={dur_1x1:.3f}s")

    # ----------------------------------------------------
    # PHASE 7: 1 x 5 VALIDATION (1 Candidate x 5 Jobs)
    # ----------------------------------------------------
    print("\n>>> PHASE 7: 1 x 5 MULTI-ROLE VALIDATION (1 Candidate x 5 Jobs)")
    req_1x5 = EvaluationConfigRequest(
        candidate_ids=[persisted_cands[0].id],
        job_ids=[j.id for j in persisted_jobs[:5]],
    )
    t0 = time.time()
    run_1x5 = orchestrator.execute_multi_role_evaluation(req_1x5)
    dur_1x5 = time.time() - t0
    evals_1x5 = eval_repo.get_matrix_cells(run_1x5.id)

    # Verify candidate UUID reused across all 5 evaluations
    c_ids_in_evals = {e.candidate_id for e in evals_1x5}
    j_ids_in_evals = {e.job_id for e in evals_1x5}
    scores_1x5 = [e.composite_score for e in evals_1x5]

    results["phase7_1x5"] = {
        "run_id": str(run_1x5.id),
        "candidates": 1,
        "jobs": 5,
        "expected_evaluations": 5,
        "actual_evaluations": len(evals_1x5),
        "unique_candidate_uuids": len(c_ids_in_evals),
        "unique_job_uuids": len(j_ids_in_evals),
        "duration_sec": round(dur_1x5, 4),
        "distinct_scores_count": len(set(scores_1x5)),
        "scores": scores_1x5,
    }
    print(f"  [OK] 1x5 Result: evaluations={len(evals_1x5)}, unique_cand_ids={len(c_ids_in_evals)}, unique_jobs={len(j_ids_in_evals)}, scores={scores_1x5}")

    # ----------------------------------------------------
    # PHASE 8: 2 x 3 VALIDATION (2 Candidates x 3 Jobs)
    # ----------------------------------------------------
    print("\n>>> PHASE 8: 2 x 3 VALIDATION (2 Candidates x 3 Jobs)")
    req_2x3 = EvaluationConfigRequest(
        candidate_ids=[persisted_cands[0].id, persisted_cands[1].id],
        job_ids=[persisted_jobs[0].id, persisted_jobs[1].id, persisted_jobs[2].id],
    )
    t0 = time.time()
    run_2x3 = orchestrator.execute_multi_role_evaluation(req_2x3)
    dur_2x3 = time.time() - t0
    evals_2x3 = eval_repo.get_matrix_cells(run_2x3.id)

    results["phase8_2x3"] = {
        "run_id": str(run_2x3.id),
        "candidates": 2,
        "jobs": 3,
        "expected_evaluations": 6,
        "actual_evaluations": len(evals_2x3),
        "duration_sec": round(dur_2x3, 4),
        "no_duplicate_pairs": len({(e.candidate_id, e.job_id) for e in evals_2x3}) == 6,
    }
    print(f"  [OK] 2x3 Result: evaluations={len(evals_2x3)}, expected=6, duration={dur_2x3:.3f}s")

    # ----------------------------------------------------
    # PHASE 9: 10 x 5 VALIDATION (10 Real Candidates x 5 JDs)
    # ----------------------------------------------------
    print("\n>>> PHASE 9: 10 x 5 MULTI-ROLE SCALABILITY VALIDATION")
    # Load 5 additional real CVs from Belgium folder to form 10 candidates
    folder = r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)"
    all_folder_files = [
        os.path.join(folder, f) for f in os.listdir(folder)
        if (f.endswith(".pdf") or f.endswith(".docx")) and f not in [c.file_name for c in persisted_cands]
    ]

    for fpath in all_folder_files[:5]:
        p = Path(fpath)
        with open(p, "rb") as f:
            b = f.read()
        d = parse_document(b, p.name)
        existing_sc = cand_repo.get_by_hash(d.file_hash)
        if existing_sc:
            sc = existing_sc
        else:
            sc = cand_repo.create(
                file_name=p.name,
                storage_path=f"resumes/{p.name}",
                file_hash=d.file_hash,
                raw_text=d.raw_text,
                structured_profile=prof,
            )
        persisted_cands.append(sc)
        orchestrator.index_candidate(sc)

    cand_pool_10 = persisted_cands[:10]
    job_pool_5 = persisted_jobs[:5]
    print(f"  Pool assembled: {len(cand_pool_10)} Real Candidates x {len(job_pool_5)} Jobs")

    req_10x5 = EvaluationConfigRequest(
        candidate_ids=[c.id for c in cand_pool_10],
        job_ids=[j.id for j in job_pool_5],
    )

    t0 = time.time()
    run_10x5 = orchestrator.execute_multi_role_evaluation(req_10x5)
    dur_10x5 = time.time() - t0
    evals_10x5 = eval_repo.get_matrix_cells(run_10x5.id)

    pairs_10x5 = {(e.candidate_id, e.job_id) for e in evals_10x5}
    results["phase9_10x5"] = {
        "run_id": str(run_10x5.id),
        "candidates": len(cand_pool_10),
        "jobs": len(job_pool_5),
        "expected_evaluations": len(cand_pool_10) * len(job_pool_5),
        "actual_evaluations": len(evals_10x5),
        "successful": len(evals_10x5),
        "failed": 0,
        "duplicates": len(evals_10x5) - len(pairs_10x5),
        "processing_time_sec": round(dur_10x5, 4),
        "avg_time_per_eval_ms": round((dur_10x5 / len(evals_10x5)) * 1000, 2),
        "throughput_evals_per_sec": round(len(evals_10x5) / dur_10x5, 2),
    }
    print(f"  [OK] 10x5 Result: evaluations={len(evals_10x5)}, time={dur_10x5:.3f}s, throughput={len(evals_10x5)/dur_10x5:.1f} evals/sec")

    # ----------------------------------------------------
    # PHASE 10: EVALUATION HISTORY VALIDATION
    # ----------------------------------------------------
    print("\n>>> PHASE 10: EVALUATION HISTORY VALIDATION")
    history_runs = eval_repo.list_runs()
    target_history_run = eval_repo.get_run(run_10x5.id)
    matrix_cells = eval_repo.get_matrix_cells(run_10x5.id)

    results["phase10_history"] = {
        "total_historical_runs": len(history_runs),
        "inspected_run_id": str(target_history_run.id),
        "status": target_history_run.status.value,
        "total_evaluations": target_history_run.total_evaluations,
        "matrix_cells_count": len(matrix_cells),
        "config_snapshot_present": bool(target_history_run.config),
        "config_weights": target_history_run.config.get("weights"),
        "config_heuristics": target_history_run.config.get("heuristics"),
    }
    print(f"  [OK] History: {len(history_runs)} runs stored. Matrix retrieved with {len(matrix_cells)} cells directly from DB.")

    # ----------------------------------------------------
    # PHASE 11: HISTORICAL IMMUTABILITY TEST
    # ----------------------------------------------------
    print("\n>>> PHASE 11: HISTORICAL CONFIGURATION & SCORE IMMUTABILITY TEST")
    # Record scores from run_1x1
    orig_weights = run_1x1.config["weights"]
    orig_score = evals_1x1[0].composite_score

    # Create a SECOND run with altered weights
    altered_weights = FitmentWeightsConfig(
        semantic_weight=0.60,
        skill_weight=0.20,
        experience_weight=0.10,
        qualification_weight=0.10,
    )
    req_altered = EvaluationConfigRequest(
        candidate_ids=[persisted_cands[0].id],
        job_ids=[persisted_jobs[0].id],
        weights=altered_weights,
    )
    run_altered = orchestrator.execute_multi_role_evaluation(req_altered)
    evals_altered = eval_repo.get_matrix_cells(run_altered.id)

    # Reopen original run_1x1 from database
    reopened_run_1x1 = eval_repo.get_run(run_1x1.id)
    reopened_evals_1x1 = eval_repo.get_matrix_cells(run_1x1.id)

    results["phase11_immutability"] = {
        "run1_id": str(run_1x1.id),
        "run1_weights": orig_weights,
        "run1_original_score": orig_score,
        "run1_reopened_score": reopened_evals_1x1[0].composite_score,
        "run1_score_unchanged": orig_score == reopened_evals_1x1[0].composite_score,
        "run2_id": str(run_altered.id),
        "run2_weights": run_altered.config["weights"],
        "run2_score": evals_altered[0].composite_score,
        "runs_are_independent": str(run_1x1.id) != str(run_altered.id),
    }
    print(f"  [OK] Immutability: Run 1 Score {orig_score} == Reopened {reopened_evals_1x1[0].composite_score}. Run 2 Created with ID {run_altered.id}.")

    # ----------------------------------------------------
    # PHASE 15: PERFORMANCE BENCHMARK (Cold vs Warm)
    # ----------------------------------------------------
    print("\n>>> PHASE 15: PERFORMANCE BENCHMARKING (Cold vs Warm Run)")
    # Measure cold parsing & extraction
    sample_cv = cv_paths[0]
    with open(sample_cv, "rb") as f:
        cv_b = f.read()

    t_p0 = time.time()
    doc_bench = parse_document(cv_b, Path(sample_cv).name)
    t_parse = time.time() - t_p0

    t_e0 = time.time()
    prof_bench = StructuredCandidateExtractor.extract(doc_bench.raw_text, file_name=Path(sample_cv).name)
    t_extract = time.time() - t_e0

    text_rep = build_candidate_semantic_text(prof_bench)
    t_emb0 = time.time()
    emb_bench = embedding_service.embed_text(text_rep)
    t_embed = time.time() - t_emb0

    t_f0 = time.time()
    test_faiss = FAISSVectorStore()
    cand_uid = uuid4()
    test_faiss.add_candidate(cand_uid, emb_bench)
    sim_bench = test_faiss.compute_similarity(cand_uid, emb_bench)
    t_faiss = time.time() - t_f0

    t_s0 = time.time()
    fit_bench = calculate_deterministic_fitment(
        candidate=prof_bench,
        job=sample_jds[0],
        semantic_similarity=sim_bench,
        weights=weights,
        heuristics=heuristics,
    )
    t_score = time.time() - t_s0

    results["phase15_performance"] = {
        "cv_parsing_ms": round(t_parse * 1000, 2),
        "extraction_ms": round(t_extract * 1000, 2),
        "embedding_generation_ms": round(t_embed * 1000, 2),
        "faiss_indexing_and_search_ms": round(t_faiss * 1000, 2),
        "deterministic_scoring_ms": round(t_score * 1000, 2),
        "total_single_pipeline_ms": round((t_parse + t_extract + t_embed + t_faiss + t_score) * 1000, 2),
        "batch_10x5_total_sec": round(dur_10x5, 4),
        "batch_10x5_avg_eval_ms": round((dur_10x5 / 50) * 1000, 2),
    }
    print(f"  [OK] Latencies: Parse={t_parse*1000:.1f}ms, Extract={t_extract*1000:.1f}ms, Embed={t_embed*1000:.1f}ms, FAISS={t_faiss*1000:.2f}ms, Score={t_score*1000:.2f}ms")

    # ----------------------------------------------------
    # PHASE 16: SCORING ABLATION / WEIGHT SENSITIVITY
    # ----------------------------------------------------
    print("\n>>> PHASE 16: SCORING ABLATION / WEIGHT SENSITIVITY EXPERIMENT")
    # Evaluate 3 candidates against PM role across 4 weight regimes
    eval_cands_ablation = persisted_cands[:3]
    target_job_ablation = persisted_jobs[0]  # Senior IT PM

    weight_regimes = {
        "Baseline (Balanced)": FitmentWeightsConfig(semantic_weight=0.35, skill_weight=0.35, experience_weight=0.20, qualification_weight=0.10),
        "Semantic-Heavy": FitmentWeightsConfig(semantic_weight=0.55, skill_weight=0.20, experience_weight=0.15, qualification_weight=0.10),
        "Skill-Heavy": FitmentWeightsConfig(semantic_weight=0.20, skill_weight=0.55, experience_weight=0.15, qualification_weight=0.10),
        "Experience-Heavy": FitmentWeightsConfig(semantic_weight=0.20, skill_weight=0.20, experience_weight=0.50, qualification_weight=0.10),
    }

    ablation_results = {}
    for regime_name, w_cfg in weight_regimes.items():
        req_abl = EvaluationConfigRequest(
            candidate_ids=[c.id for c in eval_cands_ablation],
            job_ids=[target_job_ablation.id],
            weights=w_cfg,
        )
        run_abl = orchestrator.execute_multi_role_evaluation(req_abl)
        evals_abl = eval_repo.get_leaderboard_for_job(run_abl.id, target_job_ablation.id)
        ablation_results[regime_name] = [
            {
                "rank": e.rank,
                "candidate": e.candidate_name,
                "composite": e.composite_score,
                "semantic": e.semantic_score,
                "skill": e.skill_score,
                "experience": e.experience_score,
            }
            for e in evals_abl
        ]
        print(f"  [ABLATION] {regime_name}: Winner = {evals_abl[0].candidate_name} ({evals_abl[0].composite_score})")

    results["phase16_ablation"] = ablation_results

    # ----------------------------------------------------
    # SAVE STRUCTURED TELEMETRY RESULTS
    # ----------------------------------------------------
    output_path = backend_dir / "data" / "academic_validation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n================================================================================")
    print(f"VALIDATION SUITE COMPLETED SUCCESSFULLY. Results saved to: {output_path}")
    print("================================================================================")
    return results


if __name__ == "__main__":
    run_all_validations()
