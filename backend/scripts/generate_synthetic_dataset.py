"""
Synthetic Candidate Dataset Generator (100 Candidates across 10 IT Role Families).
Generates realistic PDF CV documents with comprehensive career history, canonical skills,
education, and certifications across 10 IT role families with varied fitment levels.
Ingests each candidate through the real parser, Supabase storage, repository, and FAISS vector index.
Flags each candidate with is_synthetic = True.
"""

import argparse
import io
import json
import os
from pathlib import Path
import random
import sys
from typing import Optional, Set
from uuid import UUID, uuid4

import fitz  # PyMuPDF

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.core.logging import get_logger
from app.core.orchestrator import PipelineOrchestrator
from app.parsers.factory import parse_document
from app.schemas.candidate import (
    CandidateProfile,
    CertificationEntry,
    EducationEntry,
    PersonalInformation,
    ProjectEntry,
    WorkExperienceEntry,
)
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.supabase_client import get_db
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.llm.extractor import StructuredCandidateExtractor
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.vector_store.faiss_store import get_faiss_store

logger = get_logger("synthetic_generator")

# 10 IT Role Families Definition
ROLE_FAMILIES = {
    "Cloud Architect": {
        "skills": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Microservices", "Docker", "Linux", "CI/CD", "Enterprise Architecture"],
        "tools": ["AWS CloudFormation", "Terraform Cloud", "Datadog", "Helm", "Prometheus"],
        "certs": ["AWS Certified Solutions Architect - Professional", "Google Professional Cloud Architect", "Azure Solutions Architect Expert"],
        "titles": ["Lead Cloud Architect", "Principal Cloud Engineer", "Senior Enterprise Cloud Specialist", "Cloud Infrastructure Consultant", "Junior Cloud Associate"],
    },
    "DevOps Engineer": {
        "skills": ["Docker", "Kubernetes", "CI/CD", "Jenkins", "GitLab CI", "Terraform", "Ansible", "Linux", "Bash", "Prometheus", "Grafana"],
        "tools": ["ArgoCD", "Vault", "Helm", "ELK Stack", "New Relic"],
        "certs": ["Certified Kubernetes Administrator (CKA)", "AWS Certified DevOps Engineer", "HashiCorp Certified: Terraform Associate"],
        "titles": ["Lead DevOps Engineer", "Senior Site Reliability Engineer", "Platform Engineer", "DevOps Infrastructure Specialist", "Junior DevOps Support"],
    },
    "Full-Stack Developer": {
        "skills": ["TypeScript", "React", "Node.js", "Python", "FastAPI", "PostgreSQL", "Docker", "Tailwind CSS", "REST APIs", "GraphQL"],
        "tools": ["Next.js", "Express", "Prisma", "Vite", "Redis"],
        "certs": ["AWS Certified Developer - Associate", "Meta Certified Full-Stack Developer"],
        "titles": ["Staff Full-Stack Engineer", "Senior Full-Stack Developer", "Full-Stack Web Architect", "Mid-Level Software Developer", "Junior Web Developer"],
    },
    "Data Engineer": {
        "skills": ["Python", "SQL", "Apache Spark", "Airflow", "Kafka", "Snowflake", "dbt", "PostgreSQL", "BigQuery", "Docker"],
        "tools": ["Databricks", "Glue", "Delta Lake", "Trino", "Redshift"],
        "certs": ["Databricks Certified Data Engineer Professional", "Google Cloud Professional Data Engineer", "Snowflake SnowPro Core"],
        "titles": ["Principal Data Engineer", "Senior Data Platform Engineer", "ETL Pipeline Developer", "Data Warehouse Specialist", "Associate Data Analyst"],
    },
    "Machine Learning Engineer": {
        "skills": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "MLflow", "Docker", "FastAPI", "Pandas", "NLP", "LLM Fine-Tuning"],
        "tools": ["Hugging Face", "Weights & Biases", "Triton Inference Server", "Kubeflow", "vLLM"],
        "certs": ["AWS Certified Machine Learning - Specialty", "Google Cloud Professional Machine Learning Engineer"],
        "titles": ["Principal AI/ML Scientist", "Senior ML Platform Engineer", "Applied Machine Learning Engineer", "Computer Vision Specialist", "Junior ML Developer"],
    },
    "Cybersecurity Analyst": {
        "skills": ["SIEM", "SOC", "Incident Response", "Penetration Testing", "Network Security", "Vulnerability Assessment", "Firewalls", "Wireshark", "Linux", "Python"],
        "tools": ["Splunk", "CrowdStrike", "Nessus", "Burp Suite", "QRadar", "Metasploit"],
        "certs": ["CISSP", "CompTIA Security+", "CEH (Certified Ethical Hacker)", "GIAC Security Essentials (GSEC)"],
        "titles": ["Chief Information Security Officer", "Senior Cyber Threat Hunter", "Security Operations Lead", "Vulnerability Analyst", "Junior SOC Analyst"],
    },
    "Frontend Developer": {
        "skills": ["JavaScript", "TypeScript", "React", "Vue.js", "HTML5", "CSS3", "Tailwind CSS", "Redux", "Webpack", "Vite"],
        "tools": ["Next.js", "Figma", "Storybook", "Jest", "Playwright"],
        "certs": ["Meta Front-End Developer Professional", "W3C Front-End Web Developer"],
        "titles": ["Principal Frontend Architect", "Senior UI/UX Engineer", "React Specialist", "Web Application Developer", "Junior Frontend Developer"],
    },
    "Backend Developer": {
        "skills": ["Java", "Spring Boot", "Go", "Python", "Microservices", "PostgreSQL", "Kafka", "Redis", "Docker", "RESTful APIs"],
        "tools": ["Hibernate", "RabbitMQ", "Gin", "Postman", "OpenAPI/Swagger"],
        "certs": ["Oracle Certified Professional Java SE", "AWS Certified Developer"],
        "titles": ["Principal Backend Architect", "Senior Distributed Systems Engineer", "Lead Java Developer", "Golang API Engineer", "Junior Backend Programmer"],
    },
    "QA Automation Lead": {
        "skills": ["Selenium", "Playwright", "Cypress", "Python", "Java", "TestNG", "CI/CD", "API Testing", "Postman", "Jira"],
        "tools": ["Appium", "JMeter", "Allure", "Cucumber", "BrowserStack"],
        "certs": ["ISTQB Certified Tester - Advanced Level", "Selenium Certified Automation Engineer"],
        "titles": ["Head of Quality Assurance", "Senior Test Automation Architect", "Lead QA Engineer", "SDET (Software Development Engineer in Test)", "Junior QA Analyst"],
    },
    "Mobile App Developer": {
        "skills": ["Swift", "Kotlin", "Flutter", "React Native", "iOS", "Android", "Dart", "Firebase", "REST APIs", "Git"],
        "tools": ["Xcode", "Android Studio", "Fastlane", "Cocoapods", "Gradle"],
        "certs": ["Google Associate Android Developer", "Apple Certified iOS Developer"],
        "titles": ["Staff Mobile Engineer", "Senior iOS / Android Architect", "Cross-Platform Flutter Specialist", "React Native Developer", "Junior Mobile App Coder"],
    },
}

FIRST_NAMES = [
    "Alexander", "Sophia", "Marcus", "Elena", "Liam", "Olivia", "Ethan", "Chloe", "Noah", "Ava",
    "Benjamin", "Mia", "Lucas", "Amelia", "Mason", "Harper", "Logan", "Evelyn", "James", "Abigail",
    "Arjun", "Priya", "Chen", "Mei", "Santiago", "Camila", "Dmitri", "Natasha", "Kenji", "Yuki",
    "Tariq", "Fatima", "Kwame", "Amina", "Lars", "Astrid", "Mateo", "Valentina", "Kofi", "Zainab"
]

LAST_NAMES = [
    "Vance", "Lindqvist", "Kowalski", "Patel", "Nakamura", "Morales", "Dubois", "Schneider", "O'Connor", "Ivanov",
    "Chen", "Al-Mansoor", "Okafor", "Hansen", "Rossi", "Mercer", "Stirling", "Sterling", "Adler", "Svensson",
    "Gupta", "Tanaka", "Gomez", "Moreau", "Weber", "Brennan", "Novak", "Kim", "Larsson", "Diallo"
]

CITIES = [
    "Amsterdam, Netherlands", "London, United Kingdom", "Berlin, Germany", "Zurich, Switzerland",
    "San Francisco, CA, USA", "New York, NY, USA", "Toronto, Canada", "Singapore",
    "Stockholm, Sweden", "Dublin, Ireland", "Austin, TX, USA", "Seattle, WA, USA"
]

UNIVERSITIES = [
    "Delft University of Technology", "Technical University of Munich", "Imperial College London",
    "ETH Zurich", "University of California, Berkeley", "Carnegie Mellon University",
    "National University of Singapore", "University of Toronto", "University of Oxford", "KTH Royal Institute of Technology"
]


def generate_candidate_text(
    name: str,
    role_family: str,
    seniority: str,
    experience_years: float,
    city: str,
    email: str,
    phone: str,
) -> str:
    family_info = ROLE_FAMILIES[role_family]
    skills = family_info["skills"]
    tools = family_info["tools"]
    certs = family_info["certs"]

    # Select skills based on seniority
    if seniority == "Principal":
        selected_skills = skills
        degree = "Master's in Computer Science"
        selected_certs = certs[:2]
    elif seniority == "Senior":
        selected_skills = skills[:8]
        degree = "Master's in Information Technology"
        selected_certs = certs[:1]
    elif seniority == "Mid":
        selected_skills = skills[:6]
        degree = "Bachelor's in Software Engineering"
        selected_certs = certs[:1] if random.random() > 0.5 else []
    else:  # Junior / Partial
        selected_skills = skills[:4] + ["Git", "Agile"]
        degree = "Bachelor's in Computer Science"
        selected_certs = []

    skills_str = ", ".join(selected_skills)
    tools_str = ", ".join(tools)

    # Career roles
    curr_year = 2026
    start_year = int(curr_year - experience_years)
    roles_text = []

    if seniority in ["Principal", "Senior"]:
        roles_text.append(
            f"Position: {seniority} {role_family} (2022 - Present)\n"
            f"Company: Global Enterprise Cloud Corp, {city}\n"
            f"Responsibilities:\n"
            f"- Spearheaded architectural migration and high-availability operations using {skills[0]} and {skills[1]}.\n"
            f"- Mentored team of 8 engineers and introduced automated testing and deployment standards.\n"
            f"- Cut system latency by 35% and improved deployment frequency by 4x using {tools[0]}.\n"
            f"- Designed robust fault-tolerant pipelines adhering to strict ISO-27001 and SOC-2 governance.\n"
        )
        mid_start = max(start_year, 2018)
        roles_text.append(
            f"Position: {role_family} Lead (2018 - 2022)\n"
            f"Company: FinTech Dynamics B.V., {city}\n"
            f"Responsibilities:\n"
            f"- Built scalable services processing 50M+ daily transactions using {skills[2]} and {skills[3]}.\n"
            f"- Automated continuous integration pipelines with {tools[1]}.\n"
            f"- Partnered with cross-functional product owners to deliver multi-region deployments.\n"
        )
    elif seniority == "Mid":
        roles_text.append(
            f"Position: {role_family} (2023 - Present)\n"
            f"Company: TechVentures Ltd, {city}\n"
            f"Responsibilities:\n"
            f"- Developed microservices and core components utilizing {skills[0]} and {skills[1]}.\n"
            f"- Integrated monitoring dashboards with {tools[0]} and reduced incident triage time by 25%.\n"
            f"- Authored automated unit and integration tests maintaining 88% test coverage.\n"
        )
        roles_text.append(
            f"Position: Associate Software Developer (2021 - 2023)\n"
            f"Company: Apex Digital Solutions, {city}\n"
            f"Responsibilities:\n"
            f"- Contributed to feature releases and database query optimization with {skills[2]}.\n"
            f"- Collaborated in Agile Scrum sprints and code review processes.\n"
        )
    else:  # Junior
        roles_text.append(
            f"Position: Junior {role_family} (2024 - Present)\n"
            f"Company: InnoSoft Labs, {city}\n"
            f"Responsibilities:\n"
            f"- Implemented foundational modules and bug fixes using {skills[0]}.\n"
            f"- Participated in daily standups and sprint planning under senior mentorship.\n"
            f"- Automated test cases and maintained technical documentation.\n"
        )

    history_str = "\n".join(roles_text)
    uni = random.choice(UNIVERSITIES)
    grad_year = curr_year - int(experience_years) - 1

    cert_section = f"CERTIFICATIONS:\n" + "\n".join(f"- {c}" for c in selected_certs) if selected_certs else "CERTIFICATIONS: None"

    cv_text = (
        f"CURRICULUM VITAE - {name.upper()}\n"
        f"Contact: {email} | {phone} | {city}\n"
        f"Profile: Experienced {seniority} {role_family} with {experience_years} years of demonstrated track record.\n\n"
        f"EXECUTIVE SUMMARY:\n"
        f"Results-oriented {role_family} professional with deep technical expertise in {selected_skills[0]} and {selected_skills[1]}. "
        f"Demonstrated success delivering enterprise-grade resilient solutions, optimizing operational performance, and driving engineering excellence.\n\n"
        f"CORE TECHNICAL COMPETENCIES:\n"
        f"Skills: {skills_str}\n"
        f"Tools & Frameworks: {tools_str}\n\n"
        f"VERIFIED WORK EXPERIENCE:\n"
        f"{history_str}\n"
        f"EDUCATION:\n"
        f"- {degree}, {uni} (Graduated {grad_year})\n\n"
        f"{cert_section}\n\n"
        f"LANGUAGES: English (Fluent), Dutch (Professional)\n"
    )

    return cv_text


def create_pdf_bytes_from_text(text: str) -> bytes:
    """Renders formatted CV text into valid PDF binary bytes using PyMuPDF."""
    doc = fitz.open()
    # Support multi-page layout if text is long
    lines = text.splitlines()
    lines_per_page = 42

    for page_idx in range(0, len(lines), lines_per_page):
        page = doc.new_page()
        page_lines = lines[page_idx: page_idx + lines_per_page]
        y = 50
        for line in page_lines:
            page.insert_text((50, y), line, fontsize=10)
            y += 16

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_and_ingest_synthetic_dataset(
    target_count: int = 100,
    recruiter_id_str: Optional[str] = None,
    auth_token: Optional[str] = None,
):
    print("=" * 80)
    print(f"GENERATING & INGESTING {target_count} SYNTHETIC CVS ACROSS 10 IT ROLE FAMILIES")
    print("=" * 80)

    db = get_db()
    cand_repo = CandidateRepository()
    storage = SupabaseStorageService()
    orch = PipelineOrchestrator()

    # Determine recruiter ID
    recruiter_uuid = UUID(recruiter_id_str) if recruiter_id_str else UUID("2290592f-4210-45c3-9e64-646804df5a04")

    family_names = list(ROLE_FAMILIES.keys())
    per_family_count = target_count // len(family_names)

    ingested_count = 0
    generated_names = set()

    for fam_idx, role_family in enumerate(family_names, start=1):
        print(f"\n[{fam_idx}/10] Processing Role Family: '{role_family}' ({per_family_count} candidates)...")

        for cand_idx in range(per_family_count):
            # Pick a unique name
            while True:
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                full_name = f"{fname} {lname}"
                if full_name not in generated_names:
                    generated_names.add(full_name)
                    break

            # Seniority distribution across the 10 candidates
            if cand_idx in [0, 1]:
                seniority = "Principal"
                exp_years = round(random.uniform(10.0, 14.5), 1)
            elif cand_idx in [2, 3, 4]:
                seniority = "Senior"
                exp_years = round(random.uniform(5.5, 9.0), 1)
            elif cand_idx in [5, 6]:
                seniority = "Mid"
                exp_years = round(random.uniform(3.0, 5.0), 1)
            else:
                seniority = "Junior"
                exp_years = round(random.uniform(1.2, 2.5), 1)

            city = random.choice(CITIES)
            email = f"{fname.lower()}.{lname.lower()}_{fam_idx}_{cand_idx}@synthetic-talent.io"
            phone = f"+31 6 {random.randint(1000, 9999)} {random.randint(1000, 9999)}"

            # Generate realistic CV text
            cv_text = generate_candidate_text(
                name=full_name,
                role_family=role_family,
                seniority=seniority,
                experience_years=exp_years,
                city=city,
                email=email,
                phone=phone,
            )

            # Convert to PDF
            pdf_bytes = create_pdf_bytes_from_text(cv_text)
            file_name = f"{full_name.replace(' ', '_')}_{seniority}_{role_family.replace(' ', '')}.pdf"

            # Parse document
            parsed_doc = parse_document(pdf_bytes, file_name)

            # Check if duplicate exists
            existing = cand_repo.get_by_hash(parsed_doc.file_hash, recruiter_id=recruiter_uuid, token=auth_token)
            if existing:
                print(f"  - Candidate '{full_name}' already exists, skipping.")
                continue

            # Extract structured candidate profile
            structured_profile = StructuredCandidateExtractor.extract(parsed_doc.raw_text, file_name=file_name)
            structured_profile.is_synthetic = True

            # Upload to Supabase Storage bucket 'resumes'
            dest_path = f"{recruiter_uuid}/{parsed_doc.file_hash[:16]}_{file_name}"
            storage_path = storage.upload_file(
                bucket="resumes",
                destination_path=dest_path,
                content=pdf_bytes,
                content_type="application/pdf",
                token=auth_token,
            )

            # Persist in Supabase PostgreSQL
            saved_cand = cand_repo.create(
                file_name=file_name,
                storage_path=storage_path,
                file_hash=parsed_doc.file_hash,
                raw_text=parsed_doc.raw_text,
                structured_profile=structured_profile,
                recruiter_id=recruiter_uuid,
                token=auth_token,
            )

            # Index in FAISS
            faiss_id = orch.index_candidate(saved_cand)
            cand_repo.update_faiss_id(saved_cand.id, faiss_id, token=auth_token)

            ingested_count += 1
            if ingested_count % 10 == 0:
                print(f"  -> Ingested {ingested_count}/{target_count} candidates into database & FAISS...")

    print("\n" + "=" * 80)
    print(f"SUCCESS: Successfully generated and ingested {ingested_count} synthetic candidates!")
    print(f"Assigned Recruiter ID: {recruiter_uuid}")
    print("All profiles indexed in FAISS with is_synthetic = True and stored in Supabase 'resumes' bucket.")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and ingest synthetic candidate CV dataset")
    parser.add_argument("--count", type=int, default=100, help="Total synthetic candidates to generate (default 100)")
    parser.add_argument("--recruiter-id", type=str, default="2290592f-4210-45c3-9e64-646804df5a04", help="Target recruiter UUID")
    args = parser.parse_args()

    generate_and_ingest_synthetic_dataset(
        target_count=args.count,
        recruiter_id_str=args.recruiter_id,
    )
