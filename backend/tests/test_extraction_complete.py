"""
Comprehensive Verification Tests for CV Extraction, Text Sanitization,
Structured Profile Generation, Embedding Representation, and Fitment Scoring.
"""

import os
from pathlib import Path
import pytest

from app.parsers.pdf_parser import PDFParser
from app.parsers.sanitizer import sanitize_text, reconstruct_spaced_headings
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile
from app.services.llm.extractor import StructuredCandidateExtractor
from app.core.orchestrator import build_candidate_semantic_text, build_job_semantic_text
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.pipeline.scorer import calculate_deterministic_fitment
from app.pipeline.explainer import generate_fitment_explanation
from app.services.llm.gemini_provider import GeminiLLMProvider

JEREMY_PDF_PATH = r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)\Jeremy Scheppers_24.pdf"
HUGUES_PDF_PATH = r"C:\Users\srira\Downloads\Belgium\SailPoint\Hugues CREPIN.pdf"
BELGIUM_FOLDER = r"C:\Users\srira\Downloads\Belgium\Project_Managers_Belgium_(HOTLIST)"


class TestTextSanitization:
    def test_nul_byte_removal(self):
        dirty_text = "Senior IT\x00 Security Officer\x00 with 20+ years\x00 experience."
        clean = sanitize_text(dirty_text)
        assert "\x00" not in clean
        assert clean == "Senior IT Security Officer with 20+ years experience."

    def test_unicode_preservation(self):
        accented_text = "Cédric Jacquemyn, Jérôme, Hélène, Müller, Peña, François - Rue de l'Industrie."
        clean = sanitize_text(accented_text)
        assert "é" in clean
        assert "è" in clean
        assert "ü" in clean
        assert "ñ" in clean
        assert "ç" in clean
        assert clean == accented_text

    def test_replacement_char_handling(self):
        text_with_bullets = "\ufffd First duty\n\ufffd Second duty"
        clean = sanitize_text(text_with_bullets)
        assert "• First duty" in clean
        assert "• Second duty" in clean

    def test_spaced_headings_reconstruction(self):
        spaced = "W O R K   E X P E R I E N C E"
        reconstructed = reconstruct_spaced_headings(spaced)
        assert reconstructed == "WORK EXPERIENCE"


class TestJeremyScheppersExtraction:
    @pytest.fixture(autouse=True)
    def setup_doc(self):
        if not os.path.exists(JEREMY_PDF_PATH):
            pytest.skip(f"Jeremy Scheppers PDF not found at {JEREMY_PDF_PATH}")
        parser = PDFParser()
        with open(JEREMY_PDF_PATH, "rb") as f:
            self.parsed_doc = parser.parse(f.read(), "Jeremy Scheppers_24.pdf")
        self.candidate = StructuredCandidateExtractor.extract(self.parsed_doc.raw_text, "Jeremy Scheppers_24.pdf")

    def test_full_text_extracted(self):
        assert len(self.parsed_doc.raw_text) > 4000
        assert "JEREMY SCHEPPERS" in self.parsed_doc.raw_text.upper()

    def test_name_and_contact(self):
        assert self.candidate.full_name == "Jeremy Scheppers"
        assert self.candidate.email == "schepper@gmail.com"
        assert self.candidate.phone is not None
        assert "32" in self.candidate.phone
        assert "Belgium" in self.candidate.location or "Brussels" in self.candidate.location

    def test_skills_not_concatenated(self):
        # Must be individual separated strings, not 'AwsAzureCi/CdLlmAgileScrum'
        assert isinstance(self.candidate.skills, list)
        assert len(self.candidate.skills) >= 15
        assert "AWS" in self.candidate.skills
        assert "Azure" in self.candidate.skills
        assert "CI/CD" in self.candidate.skills
        assert "Scrum" in self.candidate.skills
        assert "Agile" in self.candidate.skills
        assert "Jira" in self.candidate.skills
        # Ensure no bad concatenated string exists
        assert "AwsAzureCi/CdLlmAgileScrum" not in self.candidate.skills
        for skill in self.candidate.skills:
            assert len(skill.split()) <= 4  # Skill keywords are concise phrases

    def test_career_history_not_collapsed(self):
        history = self.candidate.experience_history
        assert len(history) >= 5
        titles = [e.title for e in history]
        orgs = [e.organization for e in history if e.organization]
        assert any("Lineas" in str(o) for o in orgs)
        assert any("Winamp" in str(o) for o in orgs)
        assert any("Capgemini" in str(o) for o in orgs)
        assert self.candidate.total_experience_years >= 10.0

    def test_education_not_hallucinated(self):
        # Jeremy's CV lists no degree - must NOT hallucinate 'State University (2021)'
        edu = self.candidate.education
        assert len(edu) == 0
        assert not any("State University" in str(e.institution) for e in edu)

    def test_projects_and_certifications(self):
        certs = [c.name for c in self.candidate.certifications]
        assert "Prince2" in certs or "Scrum Master" in certs
        projs = [p.name for p in self.candidate.projects]
        assert any("ZenneValley" in p for p in projs)


class TestHuguesCrepinExtraction:
    @pytest.fixture(autouse=True)
    def setup_doc(self):
        if not os.path.exists(HUGUES_PDF_PATH):
            pytest.skip(f"Hugues Crepin PDF not found at {HUGUES_PDF_PATH}")
        parser = PDFParser()
        with open(HUGUES_PDF_PATH, "rb") as f:
            self.parsed_doc = parser.parse(f.read(), "Hugues CREPIN.pdf")
        self.candidate = StructuredCandidateExtractor.extract(self.parsed_doc.raw_text, "Hugues CREPIN.pdf")

    def test_nul_characters_omitted(self):
        assert "\x00" not in self.parsed_doc.raw_text

    def test_contact_and_experience(self):
        assert "CREPIN" in self.candidate.full_name.upper()
        assert self.candidate.email == "hugues.crepin@skynet.be"
        assert self.candidate.total_experience_years >= 15.0

    def test_certifications_and_education(self):
        certs = [c.name for c in self.candidate.certifications]
        assert any(c in certs for c in ["Prince2", "Agile Master", "ITIL", "CISSP"])
        # Education has CAP Pedagogical Certificate
        assert len(self.candidate.education) >= 1
        assert "Pedagogy" in str(self.candidate.education[0].field) or "Associate" in str(self.candidate.education[0].degree)


class TestEmbeddingAndFitment:
    def test_candidate_semantic_representation(self):
        if not os.path.exists(JEREMY_PDF_PATH):
            pytest.skip("Jeremy Scheppers PDF not found")
        parser = PDFParser()
        with open(JEREMY_PDF_PATH, "rb") as f:
            doc = parser.parse(f.read(), "Jeremy Scheppers_24.pdf")
        cand = StructuredCandidateExtractor.extract(doc.raw_text, "Jeremy Scheppers_24.pdf")
        sem_text = build_candidate_semantic_text(cand)

        # Must contain summary, skills, roles, projects, certs, domains
        assert "Jeremy Scheppers" in sem_text
        assert "Core Skills:" in sem_text
        assert "Career History:" in sem_text
        assert "Projects:" in sem_text
        assert "Certifications:" in sem_text
        assert "Industry Domains:" in sem_text

        # Embed with Sentence Transformers
        emb_service = SentenceTransformerService()
        vec = emb_service.embed_text(sem_text)
        assert len(vec) == 384
        # Verify unit norm
        import numpy as np
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-4

    def test_fitment_evaluation_grounded(self):
        if not os.path.exists(JEREMY_PDF_PATH):
            pytest.skip("Jeremy Scheppers PDF not found")
        parser = PDFParser()
        with open(JEREMY_PDF_PATH, "rb") as f:
            doc = parser.parse(f.read(), "Jeremy Scheppers_24.pdf")
        cand = StructuredCandidateExtractor.extract(doc.raw_text, "Jeremy Scheppers_24.pdf")

        job = JobProfile(
            title="Senior Agile Project Manager",
            department="Engineering Operations",
            summary="Lead agile cross-functional delivery teams and ERP rollouts.",
            required_skills=["Agile", "Scrum", "Jira", "CI/CD"],
            preferred_skills=["Salesforce", "ERP", "AWS", "Prince2"],
            min_experience_years=8.0,
            required_qualification="Bachelor's",
            key_responsibilities=["Lead sprint planning", "Coordinate release management"],
        )

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

        # Simulate cosine similarity ~0.82
        fitment = calculate_deterministic_fitment(cand, job, 0.82, weights, heuristics)
        assert fitment["composite_score"] > 0.70
        assert fitment["skill_score"] >= 0.80
        assert fitment["experience_score"] == 1.0  # Jeremy has 13 yrs >= 8 yrs required
        assert "Agile" in fitment["matched_required_skills"]
        assert "Scrum" in fitment["matched_required_skills"]
        assert "CI/CD" in fitment["matched_required_skills"]

        # Explainability
        llm = GeminiLLMProvider()
        explanation = generate_fitment_explanation(cand, job, fitment, llm)
        assert len(explanation.matched_skills) >= 3
        assert len(explanation.strengths) >= 1
        assert "Jeremy Scheppers" in explanation.recommendation_rationale
