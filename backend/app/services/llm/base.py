"""
Abstract Base Provider for Large Language Models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobProfile


class BaseLLMProvider(ABC):
    @abstractmethod
    def extract_job_profile(self, raw_text: str) -> JobProfile:
        """Transforms unstructured job description text into a structured JobProfile."""
        pass

    @abstractmethod
    def extract_candidate_profile(self, raw_text: str) -> CandidateProfile:
        """Transforms unstructured candidate resume text into a canonical CandidateProfile."""
        pass

    @abstractmethod
    def synthesize_fitment_explanation(
        self,
        candidate_name: str,
        job_title: str,
        matched_skills: List[str],
        missing_skills: List[str],
        experience_summary: str,
        qualification_summary: str,
    ) -> Dict[str, Any]:
        """Synthesizes human-readable strengths, skill gaps, and recommendation rationale from deterministic evidence."""
        pass
