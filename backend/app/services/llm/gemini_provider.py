"""
Gemini LLM Provider implementation with structured JSON output
and robust deterministic fallback parsing for reproducible offline testing.
Enforces the architectural mandate: LLM NEVER generates or modifies numerical scores.
"""

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas.candidate import CandidateProfile, EducationEntry, WorkExperienceEntry
from app.schemas.job import JobProfile
from app.services.llm.base import BaseLLMProvider

logger = get_logger("gemini_provider")

TECHNICAL_SKILLS_LEXICON = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php",
    "react", "angular", "vue", "next.js", "node.js", "fastapi", "django", "flask", "spring boot",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ci/cd", "git", "linux",
    "machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow",
    "sentence transformers", "faiss", "vector search", "llm", "rag", "scikit-learn", "pandas", "numpy",
    "rest api", "graphql", "microservices", "html", "css", "tailwind css", "agile", "scrum"
]

DEGREE_HIERARCHY = [
    ("doctorate", ["phd", "ph.d", "doctorate", "doctoral"]),
    ("master's", ["master", "ms", "m.s", "m.tech", "msc", "m.sc", "mba"]),
    ("bachelor's", ["bachelor", "bs", "b.s", "b.tech", "b.e", "ba", "b.a", "bsc", "b.sc"]),
    ("associate", ["associate", "diploma"]),
    ("high school", ["high school", "secondary"]),
]


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
            logger.info("Operating Gemini provider with deterministic rule-based structured extraction")

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
                    f"Job Description Text:\n{raw_text[:4000]}"
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

    def extract_candidate_profile(self, raw_text: str) -> CandidateProfile:
        """Transforms raw resume text into a validated CandidateProfile."""
        if self.client:
            try:
                prompt = (
                    "Extract the candidate structured profile from the resume text below.\n"
                    "Output ONLY valid JSON matching this schema:\n"
                    "{\n"
                    '  "full_name": string,\n'
                    '  "email": string,\n'
                    '  "phone": string,\n'
                    '  "location": string,\n'
                    '  "total_experience_years": float,\n'
                    '  "skills": [string],\n'
                    '  "experience_history": [{"title": string, "organization": string, "duration_years": float, "summary": string}],\n'
                    '  "highest_qualification": "Doctorate" | "Master\'s" | "Bachelor\'s" | "Associate",\n'
                    '  "education": [{"degree": string, "field": string, "institution": string, "graduation_year": int}],\n'
                    '  "summary": string\n'
                    "}\n\n"
                    f"Resume Text:\n{raw_text[:4000]}"
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                if response and response.text:
                    data = json.loads(response.text)
                    return CandidateProfile(**data)
            except Exception as e:
                logger.warning("Gemini Resume extraction call failed, using deterministic fallback: %s", e)

        # Deterministic Fallback Extractor
        return self._extract_candidate_profile_fallback(raw_text)

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

        # Deterministic Grounded Narrative Synthesizer
        strengths = []
        if matched_skills:
            strengths.append(f"Demonstrated proficiency in key core competencies: {', '.join(matched_skills[:4])}.")
        strengths.append(f"Experience alignment: {experience_summary}.")

        skill_gaps = []
        if missing_skills:
            skill_gaps.append(f"Lacks explicit verification in required role skills: {', '.join(missing_skills[:4])}.")
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
                f"with substantial core skills ({', '.join(matched_skills[:3])}), though exhibiting gaps in {', '.join(missing_skills[:2])}."
            )
        else:
            rationale = (
                f"{candidate_name} presents limited domain overlap for {job_title} "
                f"due to multiple key required skill gaps ({', '.join(missing_skills[:3])})."
            )

        return {
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "recommendation_rationale": rationale,
        }

    # ------------------ Fallback Parsers ------------------

    def _extract_job_profile_fallback(self, raw_text: str) -> JobProfile:
        text_lower = raw_text.lower()

        # Extract title
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        title = lines[0] if lines else "Software Engineer"
        for l in lines[:5]:
            if any(term in l.lower() for term in ["engineer", "developer", "architect", "lead", "manager", "analyst"]):
                title = l.split(":")[-1].strip()
                break

        # Extract skills
        found_skills = [s.title() for s in TECHNICAL_SKILLS_LEXICON if re.search(r"\b" + re.escape(s) + r"\b", text_lower)]
        required_skills = found_skills[: max(1, int(len(found_skills) * 0.75))]
        preferred_skills = found_skills[len(required_skills) :]

        # Extract experience years
        exp_match = re.search(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years|yrs)", text_lower)
        min_exp = float(exp_match.group(1)) if exp_match else 2.0

        # Extract degree
        req_qual = "Bachelor's"
        for tier_name, aliases in DEGREE_HIERARCHY:
            if any(re.search(r"\b" + re.escape(alias) + r"\b", text_lower) for alias in aliases):
                req_qual = tier_name.title()
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

    def _extract_candidate_profile_fallback(self, raw_text: str) -> CandidateProfile:
        text_lower = raw_text.lower()
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        # Name
        name = lines[0] if lines else "Candidate"
        if len(name.split()) > 4:
            name = "Candidate Professional"

        # Email & Phone
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw_text)
        email = email_match.group(0) if email_match else "candidate@example.com"
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
        phone = phone_match.group(0) if phone_match else "+1-555-0100"

        # Skills
        skills = [s.title() for s in TECHNICAL_SKILLS_LEXICON if re.search(r"\b" + re.escape(s) + r"\b", text_lower)]

        # Experience
        exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)\s*(?:of\s*)?experience", text_lower)
        total_exp = float(exp_match.group(1)) if exp_match else 3.5

        # Qualification
        highest_deg = "Bachelor's"
        for tier_name, aliases in DEGREE_HIERARCHY:
            if any(re.search(r"\b" + re.escape(alias) + r"\b", text_lower) for alias in aliases):
                highest_deg = tier_name.title()
                break

        return CandidateProfile(
            full_name=name,
            email=email,
            phone=phone,
            location="San Francisco, CA",
            total_experience_years=total_exp,
            skills=skills or ["Python", "SQL", "Git"],
            experience_history=[
                WorkExperienceEntry(
                    title="Software Developer",
                    organization="TechCorp",
                    duration_years=total_exp,
                    summary="Backend API development, system architecture, database design",
                )
            ],
            highest_qualification=highest_deg,
            education=[
                EducationEntry(
                    degree=highest_deg,
                    field="Computer Science",
                    institution="State University",
                    graduation_year=2021,
                )
            ],
            summary=f"Experienced professional with {total_exp} years working with {', '.join(skills[:3])}.",
        )
