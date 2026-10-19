"""
AI-Based Contextual Fitment Engine.
Evaluates the COMPLETE Candidate Profile against the COMPLETE Job Description.
Generates evidence-grounded 0–100 AI Fitment Scores, Category tiers, Confidence,
Strengths, Gaps, Risk Flags, Uncertainty Flags, Recommendation, and Auditable
Requirement Analysis with Post-LLM Evidence Validation.
"""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import (
    EvidenceValidationStatus,
    ExplainabilityPayload,
    FitmentCategory,
    RecommendationVerdict,
)
from app.schemas.job import JobProfile
from app.services.llm.gemini_provider import GeminiLLMProvider

logger = get_logger("ai_fitment")


def validate_evidence_claim(
    evidence_text: str,
    status: str,
    candidate: CandidateProfile,
    candidate_raw_text: str = "",
) -> str:
    """
    Post-LLM Evidence Validation Layer.
    Audits claims cited by the LLM against the candidate's source profile and raw CV text.
    Returns EvidenceValidationStatus: VERIFIED, PARTIALLY_VERIFIED, or UNSUPPORTED.
    """
    if status == "MISSING":
        # Verifying absence is legitimate
        return EvidenceValidationStatus.VERIFIED.value

    if not evidence_text or evidence_text.lower().startswith("no explicit") or evidence_text.lower().startswith("not mentioned"):
        return EvidenceValidationStatus.VERIFIED.value

    # Build reference search corpus from all candidate verified sections
    reference_tokens: Set[str] = set()

    # 1. Skills and Tools
    for s in candidate.skills + candidate.tools_and_technologies:
        for token in re.findall(r"\w+", s.lower()):
            if len(token) > 2:
                reference_tokens.add(token)

    # 2. Experience History (titles, organizations, responsibilities, tech, projects, metrics)
    for exp in candidate.experience_history:
        for field in [exp.title, exp.organization or "", exp.client or "", exp.domain or ""]:
            for token in re.findall(r"\w+", field.lower()):
                if len(token) > 2:
                    reference_tokens.add(token)
        for resp in exp.responsibilities + exp.achievements + exp.technologies + exp.methodologies + exp.project_names:
            for token in re.findall(r"\w+", resp.lower()):
                if len(token) > 2:
                    reference_tokens.add(token)

    # 3. Certifications & Education
    for c in candidate.certifications:
        for token in re.findall(r"\w+", c.name.lower()):
            if len(token) > 2:
                reference_tokens.add(token)
    for ed in candidate.education:
        for field in [ed.degree, ed.field or "", ed.institution or ""]:
            for token in re.findall(r"\w+", field.lower()):
                if len(token) > 2:
                    reference_tokens.add(token)

    # 4. Raw text tokens
    if candidate_raw_text:
        for token in re.findall(r"\w+", candidate_raw_text.lower()):
            if len(token) > 2:
                reference_tokens.add(token)

    # Extract substantive tokens from the cited evidence claim
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this", "have", "been", "role", "years",
        "verified", "candidate", "demonstrates", "experience", "profile", "projects", "team",
        "work", "worked", "using", "used", "duties", "such", "also", "into", "their", "across"
    }
    evidence_tokens = [
        t for t in re.findall(r"\w+", evidence_text.lower())
        if len(t) > 2 and t not in stop_words
    ]

    if not evidence_tokens:
        return EvidenceValidationStatus.PARTIALLY_VERIFIED.value

    matched_tokens = [t for t in evidence_tokens if t in reference_tokens]
    match_ratio = len(matched_tokens) / len(evidence_tokens)

    if match_ratio >= 0.50:
        return EvidenceValidationStatus.VERIFIED.value
    elif match_ratio >= 0.20 or len(matched_tokens) >= 2:
        return EvidenceValidationStatus.PARTIALLY_VERIFIED.value
    else:
        logger.warning(
            "Evidence claim unsupported by candidate source: '%s' (matched %d/%d tokens)",
            evidence_text[:80],
            len(matched_tokens),
            len(evidence_tokens),
        )
        return EvidenceValidationStatus.UNSUPPORTED.value


EQUIVALENTS_MAP: Dict[str, List[str]] = {
    "kubernetes": ["docker", "container", "openshift", "helm", "ecs", "eks"],
    "aws": ["azure", "gcp", "google cloud", "cloud"],
    "azure": ["aws", "gcp", "cloud"],
    "gcp": ["aws", "azure", "cloud"],
    "postgresql": ["mysql", "sqlite", "sql server", "oracle db", "sql"],
    "mysql": ["postgresql", "sqlite", "sql server", "sql"],
    "react": ["angular", "vue", "vue.js", "next.js", "frontend"],
    "angular": ["react", "vue", "frontend"],
    "vue": ["react", "angular", "frontend"],
    "django": ["fastapi", "flask", "python"],
    "fastapi": ["django", "flask", "python"],
    "flask": ["fastapi", "django", "python"],
    "spring": ["spring boot", "java"],
    "spring boot": ["spring", "java"],
    "scrum": ["agile", "kanban", "safe"],
    "agile": ["scrum", "kanban", "safe"],
    "kanban": ["scrum", "agile"],
    "terraform": ["cloudformation", "ansible", "pulumi", "iac"],
    "ci/cd": ["jenkins", "github actions", "gitlab ci", "devops"],
}


def classify_missing_skills(
    missing_skills: List[str],
    candidate: CandidateProfile,
    candidate_raw_text: str = "",
) -> List[Dict[str, Any]]:
    cand_skills_lower = {s.lower().strip() for s in candidate.skills + candidate.tools_and_technologies}
    raw_lower = candidate_raw_text.lower() if candidate_raw_text else ""
    summary_lower = (candidate.professional_summary or candidate.summary or "").lower()

    analysis = []
    for skill in missing_skills:
        s_low = skill.lower().strip()
        equivs = EQUIVALENTS_MAP.get(s_low, [])
        found_equiv = [eq for eq in equivs if eq in cand_skills_lower]

        if found_equiv:
            analysis.append({
                "skill": skill,
                "status": "PARTIALLY_EVIDENCED",
                "classification": "Equivalent Skill",
                "evidence_notes": f"Candidate possesses verified equivalent experience in {', '.join(found_equiv).title()}."
            })
        elif s_low in raw_lower or s_low in summary_lower:
            analysis.append({
                "skill": skill,
                "status": "UNVERIFIED",
                "classification": "Not Evidenced",
                "evidence_notes": "Mentioned in summary or introductory text but lacks verified tenure responsibilities."
            })
        elif any(part in cand_skills_lower for part in s_low.split() if len(part) > 3):
            analysis.append({
                "skill": skill,
                "status": "PARTIALLY_EVIDENCED",
                "classification": "Partially Evidenced",
                "evidence_notes": "Candidate demonstrates experience with related technologies in this domain."
            })
        else:
            analysis.append({
                "skill": skill,
                "status": "MISSING",
                "classification": "Clearly Missing",
                "evidence_notes": "Not referenced in work history, projects, certifications, or profile keywords."
            })
    return analysis


def generate_recruiter_verification_questions(
    missing_analysis: List[Dict[str, Any]],
    candidate: CandidateProfile,
    job: JobProfile,
) -> List[str]:
    questions: List[str] = []
    for item in missing_analysis[:2]:
        sk = item["skill"]
        cls_type = item["classification"]
        if cls_type == "Equivalent Skill":
            questions.append(
                f"How has your practical experience with equivalent technologies prepared you to rapidly adapt to {sk}?"
            )
        elif cls_type == "Not Evidenced":
            questions.append(
                f"Your profile mentions familiarity with {sk}; could you describe a production initiative where you implemented it?"
            )
        else:
            questions.append(
                f"The role relies on {sk}; what has been your exposure to this area, and how do you approach ramping up?"
            )

    if candidate.total_experience_years < job.min_experience_years:
        questions.append(
            f"Given the role targets {job.min_experience_years} years of seniority, can you share how your intensive {candidate.total_experience_years} years have prepared you for senior-level responsibilities?"
        )
    elif candidate.experience_history:
        questions.append(
            f"How does your tenure at {candidate.experience_history[0].organization or 'your recent role'} align with {job.title} expectations?"
        )

    if job.key_responsibilities:
        questions.append(
            f"Can you provide a concrete example of how you approached '{job.key_responsibilities[0][:70]}' in prior projects?"
        )

    return questions[:4]


def audit_score_consistency(
    fitment_score: float,
    req_coverage: float,
    exp_ratio: float,
    must_have_count: int,
    matched_must_have_count: int,
) -> Dict[str, Any]:
    flags = []
    status = "CONSISTENT"
    adjusted_score = fitment_score

    # Anomaly 1: High Match / Low Score
    if req_coverage >= 0.85 and exp_ratio >= 1.0 and fitment_score < 70.0:
        status = "WARNING_FLAGGED"
        msg = f"SCORE_CONSISTENCY_WARNING: High match ({int(req_coverage*100)}% coverage, {exp_ratio:.1f}x experience) contradicted by low score ({fitment_score})."
        flags.append(msg)
        adjusted_score = max(fitment_score, 78.0)

    # Anomaly 2: Low Match / High Score
    missing_ratio = (must_have_count - matched_must_have_count) / max(1, must_have_count) if must_have_count else 0.0
    if (missing_ratio >= 0.50 or exp_ratio < 0.50) and fitment_score >= 85.0:
        status = "WARNING_FLAGGED"
        msg = f"SCORE_CONSISTENCY_WARNING: Low match (major mandatory deficits or experience shortfall) contradicted by high score ({fitment_score})."
        flags.append(msg)
        adjusted_score = min(fitment_score, 68.0)

    return {
        "status": status,
        "flags": flags,
        "original_score": fitment_score,
        "adjusted_score": round(adjusted_score, 1),
    }


def map_score_to_category(score: float) -> Tuple[str, str]:
    if score >= 90.0:
        return FitmentCategory.EXCELLENT_FIT.value, RecommendationVerdict.STRONGLY_RECOMMEND.value
    elif score >= 80.0:
        return FitmentCategory.STRONG_FIT.value, RecommendationVerdict.RECOMMEND.value
    elif score >= 70.0:
        return FitmentCategory.GOOD_FIT.value, RecommendationVerdict.RECOMMEND.value
    elif score >= 60.0:
        return FitmentCategory.PARTIAL_FIT.value, RecommendationVerdict.CONSIDER.value
    elif score >= 40.0:
        return FitmentCategory.WEAK_FIT.value, RecommendationVerdict.DO_NOT_RECOMMEND.value
    else:
        return FitmentCategory.POOR_FIT.value, RecommendationVerdict.DO_NOT_RECOMMEND.value


class AIFitmentEvaluator:
    """
    Production AI Fitment Engine using Google Gemini with structured output,
    evidence validation, missing skills analysis, recruiter verification questions,
    and internal score consistency auditing.
    """

    def __init__(self, llm_provider: Optional[GeminiLLMProvider] = None):
        self.llm_provider = llm_provider or GeminiLLMProvider()
        settings = get_settings()
        self.fitment_model_preferred = getattr(settings, "gemini_fitment_model", "gemini-3.1-pro-preview")
        self.model_name = self.fitment_model_preferred
        self.active_model_used = None
        self.prompt_version = "v3.0-reasoning-grounded"

    def evaluate_fitment(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_raw_text: str = "",
        semantic_similarity: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Executes comprehensive AI fitment evaluation of candidate vs job.
        Returns a dictionary containing:
        - composite_score (0.0000 - 1.0000 float for Postgres storage)
        - semantic_score, skill_score, experience_score, qualification_score
        - explainability (ExplainabilityPayload with 0-100 fitment_score)
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Attempt Gemini LLM contextual fitment analysis if client is active and quota is not exhausted
        if self.llm_provider.client and not getattr(self, "_quota_exhausted", False):
            try:
                ai_result = self._evaluate_with_gemini(candidate, job, candidate_raw_text)
                if ai_result:
                    return self._build_final_evaluation_payload(
                        ai_result, candidate, job, candidate_raw_text, semantic_similarity, now_iso
                    )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    self._quota_exhausted = True
                logger.warning("Gemini AI fitment evaluation failed; falling back to contextual evaluator: %s", e)

        # Fallback to intelligent deterministic fitment evaluator
        fallback_result = self._evaluate_with_fallback(candidate, job, candidate_raw_text, semantic_similarity)
        return self._build_final_evaluation_payload(
            fallback_result, candidate, job, candidate_raw_text, semantic_similarity, now_iso, is_fallback=True
        )

    def _evaluate_with_gemini(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_raw_text: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Invokes Google Gemini with model routing fallback chain."""
        settings = get_settings()
        models_to_try = [
            getattr(settings, "gemini_fitment_model", "gemini-3.1-pro-preview"),
            "gemini-2.5-pro",
            "gemini-1.5-pro",
            "gemini-2.5-flash",
        ]
        unique_models = list(dict.fromkeys([m for m in models_to_try if m]))

        # Format dossiers
        candidate_dossier = (
            f"CANDIDATE DOSSIER:\n"
            f"Name: {candidate.full_name}\n"
            f"Total Experience: {candidate.total_experience_years} years (Source: {candidate.experience_years_source})\n"
            f"Highest Qualification: {candidate.highest_qualification}\n"
            f"Summary: {candidate.professional_summary or candidate.summary or 'N/A'}\n"
            f"Core Skills: {', '.join(candidate.skills)}\n"
            f"Tools & Platforms: {', '.join(candidate.tools_and_technologies)}\n"
            f"Languages: {', '.join(candidate.languages)}\n"
            f"Certifications: {', '.join(c.name for c in candidate.certifications) if candidate.certifications else 'None'}\n"
            f"Education: {'; '.join(f'{e.degree} from {e.institution}' for e in candidate.education) if candidate.education else 'None'}\n"
        )
        if candidate.experience_history:
            candidate_dossier += "\nVERIFIED CAREER HISTORY:\n" + "\n".join(
                f"- {e.title} at {e.organization or e.client or 'Enterprise'} ({e.duration_years} yrs): "
                f"Responsibilities: {'; '.join(e.responsibilities[:5])}. Tech: {', '.join(e.technologies[:5])}. Methodologies: {', '.join(e.methodologies)}"
                for e in candidate.experience_history
            )
        if candidate.projects:
            candidate_dossier += "\nPROJECTS:\n" + "\n".join(
                f"- {p.name}: {p.description or 'Delivered'}. Tech: {', '.join(p.technologies)}"
                for p in candidate.projects[:5]
            )

        job_dossier = (
            f"JOB ROLE REQUIREMENTS:\n"
            f"Title: {job.title}\n"
            f"Department: {job.department or 'Engineering'}\n"
            f"Minimum Experience: {job.min_experience_years} years\n"
            f"Preferred Experience: {job.preferred_experience_years or job.min_experience_years} years\n"
            f"Required Qualification: {job.required_qualification}\n"
            f"Required Skills: {', '.join(job.required_skills)}\n"
            f"Preferred Skills: {', '.join(job.preferred_skills) if job.preferred_skills else 'None'}\n"
            f"Must-Have Requirements: {'; '.join(job.must_have_requirements) if job.must_have_requirements else 'None'}\n"
            f"Should-Have Requirements: {'; '.join(job.should_have_requirements) if job.should_have_requirements else 'None'}\n"
            f"Key Responsibilities:\n" + "\n".join(f"- {r}" for r in job.key_responsibilities[:10])
        )

        prompt = (
            "You are an expert recruitment fitment evaluation and talent intelligence engine.\n"
            "Evaluate the COMPLETE Candidate Profile against the COMPLETE Job Description.\n"
            "Score the candidate holistically on a 0 to 100 scale based on factual evidence.\n\n"
            "SCORE CALIBRATION TIERS:\n"
            "- EXCELLENT_FIT: 90 - 100 (Candidate exceeds or fully satisfies all must-haves, depth of experience, and key skills)\n"
            "- STRONG_FIT: 80 - 89 (Candidate meets core requirements with strong alignment and minor non-critical gaps)\n"
            "- GOOD_FIT: 70 - 79 (Candidate meets majority of requirements but has noticeable skill or experience gaps)\n"
            "- PARTIAL_FIT: 60 - 69 (Candidate has relevant fundamentals but significant missing must-haves)\n"
            "- WEAK_FIT: 40 - 59 (Limited alignment, substantial shortfalls in core skills or experience)\n"
            "- POOR_FIT: 0 - 39 (Unrelated domain, missing critical mandatory qualifications)\n\n"
            "CONTEXTUAL CALIBRATION RULES:\n"
            "1. Score represents OVERALL FIT. Candidates do not need 100% of preferred skills to receive 90–97.\n"
            "2. If candidate satisfies all must-haves, core skills, and seniority, score in 90-98 range.\n"
            "3. If candidate is missing non-critical nice-to-haves, score in 80-89 range.\n"
            "4. Only penalize severely for missing mandatory must-haves or major experience deficit.\n"
            "5. You must ONLY cite evidence explicitly present in the candidate's dossier.\n\n"
            "Output ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "fitment_score": float (0-100),\n'
            '  "fitment_category": "EXCELLENT_FIT" | "STRONG_FIT" | "GOOD_FIT" | "PARTIAL_FIT" | "WEAK_FIT" | "POOR_FIT",\n'
            '  "confidence": float (0.0 - 1.0),\n'
            '  "recommendation": "STRONGLY_RECOMMEND" | "RECOMMEND" | "CONSIDER" | "DO_NOT_RECOMMEND",\n'
            '  "strengths": [string],\n'
            '  "skill_gaps": [string],\n'
            '  "risk_flags": [string],\n'
            '  "uncertainty_flags": [string],\n'
            '  "recommendation_rationale": string,\n'
            '  "matched_skills": [string],\n'
            '  "missing_skills": [string],\n'
            '  "requirement_analysis": [\n'
            '    {\n'
            '      "requirement": string,\n'
            '      "type": "MUST_HAVE" | "SHOULD_HAVE" | "RESPONSIBILITY" | "QUALIFICATION",\n'
            '      "status": "MATCHED" | "PARTIALLY_MATCHED" | "MISSING",\n'
            '      "evidence": string\n'
            '    }\n'
            '  ]\n'
            "}\n\n"
            f"{candidate_dossier}\n\n"
            f"Raw CV Text Snippet:\n{candidate_raw_text[:10000]}\n\n"
            f"{job_dossier}"
        )

        for model_name in unique_models:
            try:
                response = self.llm_provider.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.0},
                )
                if response and response.text:
                    self.active_model_used = model_name
                    self.model_name = model_name
                    return json.loads(response.text)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    self._quota_exhausted = True
                    raise
                logger.info("Model %s unavailable (%s), trying fallback model", model_name, e)
                continue

        return None

    def _evaluate_with_fallback(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_raw_text: str = "",
        semantic_similarity: float = 0.5,
    ) -> Dict[str, Any]:
        """Intelligent, deterministic evidence-grounded fitment fallback with calibrated scoring."""
        cand_skills_lower = {s.lower().strip() for s in candidate.skills + candidate.tools_and_technologies}
        req_skills = job.required_skills or []
        must_haves = job.must_have_requirements or []

        matched_req = [s for s in req_skills if s.lower().strip() in cand_skills_lower]
        missing_req = [s for s in req_skills if s.lower().strip() not in cand_skills_lower]

        req_coverage = (len(matched_req) / len(req_skills)) if req_skills else 1.0
        exp_ratio = min(1.3, candidate.total_experience_years / max(1.0, float(job.min_experience_years)))

        # Calibrated 0-100 scoring:
        # Full skill + full exp + semantic match = 92-96
        base_score = (
            (req_coverage * 52.0)
            + (min(1.0, exp_ratio) * 28.0)
            + (max(0.0, min(1.0, semantic_similarity)) * 20.0)
        )
        fitment_score = round(max(10.0, min(97.0, base_score)), 1)

        category, verdict = map_score_to_category(fitment_score)

        strengths = []
        if matched_req:
            strengths.append(f"Demonstrates verified capability in core required competencies: {', '.join(matched_req[:6])}.")
        if candidate.total_experience_years >= job.min_experience_years:
            strengths.append(
                f"Meets seniority benchmark with {candidate.total_experience_years} years of verified experience (vs {job.min_experience_years} required)."
            )

        skill_gaps = []
        if missing_req:
            skill_gaps.append(f"Requires verification in role must-have competencies: {', '.join(missing_req[:5])}.")

        risk_flags = []
        if candidate.total_experience_years < job.min_experience_years:
            shortfall = round(job.min_experience_years - candidate.total_experience_years, 1)
            risk_flags.append(f"Experience shortfall: {candidate.total_experience_years} yrs verified vs {job.min_experience_years} yrs required (-{shortfall} yrs).")

        uncertainty_flags = []
        if not candidate.certifications:
            uncertainty_flags.append("No active vendor certifications recorded in profile.")

        rationale = (
            f"{candidate.full_name} evaluated for {job.title} with AI fitment score of {fitment_score}/100 ({category.replace('_', ' ')}). "
            f"Coverage: {len(matched_req)}/{len(req_skills)} required skills, {candidate.total_experience_years} years verified experience."
        )

        req_analysis = self.llm_provider._analyze_requirements_fallback(
            candidate,
            [{"requirement": r, "type": "MUST_HAVE"} for r in (must_haves or req_skills)],
            candidate_raw_text,
        )

        return {
            "fitment_score": fitment_score,
            "fitment_category": category,
            "confidence": 0.90,
            "recommendation": verdict,
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "risk_flags": risk_flags,
            "uncertainty_flags": uncertainty_flags,
            "recommendation_rationale": rationale,
            "matched_skills": matched_req,
            "missing_skills": missing_req,
            "requirement_analysis": req_analysis,
        }

    def _build_final_evaluation_payload(
        self,
        ai_data: Dict[str, Any],
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_raw_text: str,
        semantic_similarity: float,
        timestamp_iso: str,
        is_fallback: bool = False,
    ) -> Dict[str, Any]:
        """Validates evidence claims, computes missing skills analysis, recruiter questions, and consistency check."""
        raw_score = float(ai_data.get("fitment_score", 50.0))
        fitment_score = round(max(0.0, min(100.0, raw_score)), 1)

        matched_skills = ai_data.get("matched_skills", [])
        missing_skills = ai_data.get("missing_skills", [])
        raw_req_analysis = ai_data.get("requirement_analysis", [])

        # Post-LLM Evidence Validation
        validated_req_analysis = []
        matched_must_have_count = 0
        must_have_count = 0
        for item in raw_req_analysis:
            r_type = item.get("type", "MUST_HAVE")
            if r_type == "MUST_HAVE":
                must_have_count += 1
            status = item.get("status", "MISSING")
            if status == "MATCHED":
                matched_must_have_count += 1
            evidence = item.get("evidence", "")
            val_status = validate_evidence_claim(evidence, status, candidate, candidate_raw_text)
            validated_req_analysis.append({
                "requirement": item.get("requirement", ""),
                "type": r_type,
                "status": status,
                "evidence": evidence,
                "validation_status": val_status,
            })

        # Score Consistency Review
        req_coverage = len(matched_skills) / max(1, len(job.required_skills)) if job.required_skills else 1.0
        exp_ratio = candidate.total_experience_years / max(1.0, float(job.min_experience_years))
        consistency_audit = audit_score_consistency(
            fitment_score=fitment_score,
            req_coverage=req_coverage,
            exp_ratio=exp_ratio,
            must_have_count=must_have_count,
            matched_must_have_count=matched_must_have_count,
        )
        if consistency_audit["status"] == "WARNING_FLAGGED":
            logger.info("Score consistency review adjusted score from %s to %s", fitment_score, consistency_audit["adjusted_score"])
            fitment_score = consistency_audit["adjusted_score"]

        category, verdict = map_score_to_category(fitment_score)
        confidence = round(float(ai_data.get("confidence", 0.90)), 2)

        # Missing Skills Analysis
        missing_analysis = classify_missing_skills(missing_skills, candidate, candidate_raw_text)

        # Recruiter Verification Questions
        recruiter_questions = generate_recruiter_verification_questions(missing_analysis, candidate, job)

        # Sub-scores
        skill_score = round(len(matched_skills) / max(1, len(job.required_skills)) * 100.0, 1)
        exp_score = round(min(1.0, candidate.total_experience_years / max(1.0, float(job.min_experience_years))) * 100.0, 1)
        qual_score = 100.0 if candidate.highest_qualification in ["Master's", "Doctorate", "PhD"] else 80.0
        sem_score = round(max(0.0, min(1.0, semantic_similarity)) * 100.0, 1)

        model_meta = {
            "provider": "Google Gemini" if not is_fallback else "Contextual Evaluator",
            "model": getattr(self, "active_model_used", None) or self.model_name,
            "model_version": "3.1-pro" if not is_fallback else "v3.0",
            "prompt_version": self.prompt_version,
            "evaluated_at": timestamp_iso,
        }

        explainability = ExplainabilityPayload(
            fitment_score=fitment_score,
            fitment_category=category,
            confidence=confidence,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_preferred_skills=[],
            missing_preferred_skills=[],
            strengths=ai_data.get("strengths", []),
            skill_gaps=ai_data.get("skill_gaps", []),
            risk_flags=ai_data.get("risk_flags", []),
            uncertainty_flags=ai_data.get("uncertainty_flags", []),
            recommendation_rationale=ai_data.get("recommendation_rationale", "Fitment evaluation completed."),
            requirement_analysis=validated_req_analysis,
            recruiter_recommendation=verdict,
            missing_skills_analysis=missing_analysis,
            recruiter_verification_questions=recruiter_questions,
            score_consistency=consistency_audit,
            model_metadata=model_meta,
        )

        return {
            "composite_score": round(fitment_score / 100.0, 4),
            "semantic_score": round(sem_score / 100.0, 4),
            "skill_score": round(skill_score / 100.0, 4),
            "experience_score": round(exp_score / 100.0, 4),
            "qualification_score": round(qual_score / 100.0, 4),
            "explainability": explainability,
        }
