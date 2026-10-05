"""
Gemini LLM Provider implementation with structured JSON output
and high-fidelity deterministic fallback extraction.
Enforces the architectural mandate: LLM NEVER generates or modifies numerical scores.
"""

import json
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobProfile
from app.services.llm.base import BaseLLMProvider
from app.services.llm.extractor import StructuredCandidateExtractor

logger = get_logger("gemini_provider")


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.client = None

        if self.api_key and "your_gemini" not in self.api_key and len(self.api_key) > 10:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized live Google Gemini Client")
            except Exception as e:
                logger.warning("Could not initialize Google GenAI Client: %s", e)
        else:
            logger.info("Operating Gemini provider with high-fidelity deterministic structured extraction")

    def extract_job_profile(self, raw_text: str) -> JobProfile:
        """Transforms raw JD text into a validated JobProfile."""
        if self.client:
            try:
                prompt = (
                    "Extract the structured job profile from the job description text below.\n"
                    "Output ONLY valid JSON matching this schema:\n"
                    "{\n"
                    '  "title": string,\n'
                    '  "department": string,\n'
                    '  "summary": string,\n'
                    '  "required_skills": [string],\n'
                    '  "preferred_skills": [string],\n'
                    '  "min_experience_years": float,\n'
                    '  "required_qualification": "Doctorate" | "Master\'s" | "Bachelor\'s" | "Associate",\n'
                    '  "key_responsibilities": [string]\n'
                    "}\n\n"
                    f"Job Description Text:\n{raw_text[:25000]}"
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                if response and response.text:
                    data = json.loads(response.text)
                    return JobProfile(**data)
            except Exception as e:
                logger.warning("Gemini JD extraction call failed, using deterministic fallback: %s", e)

        # Deterministic Fallback Extractor
        return self._extract_job_profile_fallback(raw_text)

    def extract_candidate_profile(self, raw_text: str, file_name: Optional[str] = None) -> CandidateProfile:
        """Transforms raw resume text into a validated CandidateProfile."""
        if self.client:
            try:
                prompt = (
                    "You are an expert recruitment information extraction engine.\n"
                    "Extract the candidate structured profile from the full resume text below.\n"
                    "Capture all meaningful information from summary, skills, experience, projects, education, certifications.\n"
                    "Do NOT invent information that is not explicitly present in the resume.\n"
                    "Output ONLY valid JSON matching this schema:\n"
                    "{\n"
                    '  "full_name": string,\n'
                    '  "email": string or null,\n'
                    '  "phone": string or null,\n'
                    '  "location": string or null,\n'
                    '  "professional_summary": string or null,\n'
                    '  "total_experience_years": float,\n'
                    '  "skills": [string],\n'
                    '  "skills_by_category": {string: [string]},\n'
                    '  "experience_history": [\n'
                    '    {\n'
                    '      "title": string,\n'
                    '      "organization": string or null,\n'
                    '      "location": string or null,\n'
                    '      "start_date": string or null,\n'
                    '      "end_date": string or null,\n'
                    '      "duration_years": float,\n'
                    '      "responsibilities": [string],\n'
                    '      "achievements": [string],\n'
                    '      "technologies": [string],\n'
                    '      "domain": string or null\n'
                    '    }\n'
                    '  ],\n'
                    '  "highest_qualification": "Doctorate" | "Master\'s" | "Bachelor\'s" | "Associate" | "High School",\n'
                    '  "education": [\n'
                    '    {\n'
                    '      "degree": string,\n'
                    '      "field": string or null,\n'
                    '      "institution": string or null,\n'
                    '      "graduation_year": int or null\n'
                    '    }\n'
                    '  ],\n'
                    '  "certifications": [\n'
                    '    {\n'
                    '      "name": string,\n'
                    '      "issuing_organization": string or null,\n'
                    '      "year": int or null\n'
                    '    }\n'
                    '  ],\n'
                    '  "projects": [\n'
                    '    {\n'
                    '      "name": string,\n'
                    '      "description": string or null,\n'
                    '      "technologies": [string],\n'
                    '      "responsibilities": [string]\n'
                    '    }\n'
                    '  ],\n'
                    '  "languages": [string],\n'
                    '  "domains": [string],\n'
                    '  "tools_and_technologies": [string]\n'
                    "}\n\n"
                    f"Full Resume Text:\n{raw_text[:30000]}"
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                if response and response.text:
                    data = json.loads(response.text)
                    data["summary"] = data.get("professional_summary")
                    data["work_experience"] = data.get("experience_history", [])
                    return CandidateProfile(**data)
            except Exception as e:
                logger.warning("Gemini Resume extraction call failed, falling back to deterministic extractor: %s", e)

        # High-Fidelity Deterministic Extractor (Extracts actual CV data without dummy placeholders)
        return StructuredCandidateExtractor.extract(raw_text, file_name=file_name)

    def synthesize_fitment_explanation(
        self,
        candidate_name: str,
        job_title: str,
        matched_skills: List[str],
        missing_skills: List[str],
        experience_summary: str,
        qualification_summary: str,
    ) -> Dict[str, Any]:
        """Synthesizes strengths, gaps, and rationale grounded strictly in provided evidence."""
        if self.client:
            try:
                prompt = (
                    "You are a recruitment decision explainability engine.\n"
                    "Summarize the fitment evidence for this candidate against the role.\n"
                    "Do NOT invent skills or experience not listed. Output ONLY valid JSON matching:\n"
                    "{\n"
                    '  "strengths": [string],\n'
                    '  "skill_gaps": [string],\n'
                    '  "recommendation_rationale": string\n'
                    "}\n\n"
                    f"Candidate: {candidate_name}\n"
                    f"Job Role: {job_title}\n"
                    f"Matched Skills: {', '.join(matched_skills)}\n"
                    f"Missing Skills: {', '.join(missing_skills)}\n"
                    f"Experience Alignment: {experience_summary}\n"
                    f"Qualification Alignment: {qualification_summary}\n"
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as e:
                logger.warning("Gemini explanation synthesis failed, using grounded fallback: %s", e)

        # Grounded Narrative Synthesizer
        strengths = []
        if matched_skills:
            strengths.append(f"Demonstrated proficiency in key core competencies: {', '.join(matched_skills[:5])}.")
        strengths.append(f"Experience alignment: {experience_summary}.")

        skill_gaps = []
        if missing_skills:
            skill_gaps.append(f"Lacks explicit verification in required role skills: {', '.join(missing_skills[:5])}.")
        else:
            skill_gaps.append("No critical missing required skills detected.")

        if not missing_skills:
            rationale = (
                f"{candidate_name} represents an exceptional match for {job_title}, "
                f"fully meeting all required skill criteria alongside {experience_summary} and {qualification_summary}."
            )
        elif len(matched_skills) >= len(missing_skills):
            rationale = (
                f"{candidate_name} demonstrates viable candidate potential for {job_title} "
                f"with substantial core skills ({', '.join(matched_skills[:3])}), though exhibiting gaps in {', '.join(missing_skills[:3])}."
            )
        else:
            rationale = (
                f"{candidate_name} presents limited domain overlap for {job_title} "
                f"due to multiple key required skill gaps ({', '.join(missing_skills[:4])})."
            )

        return {
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "recommendation_rationale": rationale,
        }

    # ------------------ Fallback Job Extractor ------------------

    def _extract_job_profile_fallback(self, raw_text: str) -> JobProfile:
        import re
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        title = lines[0] if lines else "Software Engineer"
        for l in lines[:5]:
            if any(term in l.lower() for term in ["engineer", "developer", "architect", "lead", "manager", "analyst"]):
                title = l.split(":")[-1].strip()
                break

        from app.services.llm.extractor import CANONICAL_SKILL_CASING, DEGREE_HIERARCHY
        text_lower = raw_text.lower()
        found_skills = [proper for kw, proper in CANONICAL_SKILL_CASING.items() if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)]
        required_skills = found_skills[: max(1, int(len(found_skills) * 0.75))]
        preferred_skills = found_skills[len(required_skills) :]

        exp_match = re.search(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years|yrs)", text_lower)
        min_exp = float(exp_match.group(1)) if exp_match else 2.0

        req_qual = "Bachelor's"
        for tier_name, aliases in DEGREE_HIERARCHY:
            if any(re.search(r"\b" + re.escape(alias) + r"\b", text_lower) for alias in aliases):
                req_qual = tier_name
                break

        return JobProfile(
            title=title,
            department="Engineering",
            summary=lines[1] if len(lines) > 1 else f"Role for {title}",
            required_skills=required_skills or ["Python", "FastAPI"],
            preferred_skills=preferred_skills,
            min_experience_years=min_exp,
            required_qualification=req_qual,
            key_responsibilities=["Develop and maintain backend services", "Collaborate with cross-functional teams"],
        )
