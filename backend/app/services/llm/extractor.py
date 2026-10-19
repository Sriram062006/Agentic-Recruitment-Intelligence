"""
Deterministic, High-Fidelity Candidate Profile Extractor.
Extracts complete, un-hallucinated candidate profiles directly from sanitized resume text.
Used in offline/testing mode and as a resilient fallback for live LLM providers.
"""

from datetime import datetime
import re
from typing import Dict, List, Optional, Set, Tuple

from app.core.logging import get_logger
from app.schemas.candidate import (
    CandidateProfile,
    CertificationEntry,
    EducationEntry,
    PersonalInformation,
    ProjectEntry,
    WorkExperienceEntry,
)

logger = get_logger("structured_extractor")

# Canonical Skill Dictionary with correct industry casing
CANONICAL_SKILL_CASING: Dict[str, str] = {
    # Cloud Platforms & Infrastructure
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "helm": "Helm",
    "openshift": "OpenShift",
    "cloudformation": "CloudFormation",
    "linux": "Linux",
    "ubuntu": "Ubuntu",
    "redhat": "Red Hat",
    "centos": "CentOS",
    "nginx": "Nginx",
    "apache": "Apache",

    # CI/CD & DevOps
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "continuous integration": "CI/CD",
    "continuous delivery": "CI/CD",
    "continuous deployment": "CI/CD",
    "github actions": "GitHub Actions",
    "gitlab ci": "GitLab CI",
    "jenkins": "Jenkins",
    "argocd": "ArgoCD",
    "circleci": "CircleCI",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "devops": "DevOps",
    "devsecops": "DevSecOps",
    "sre": "SRE",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "datadog": "Datadog",
    "splunk": "Splunk",
    "elk": "ELK Stack",
    "sonarqube": "SonarQube",

    # AI, ML & Data Science
    "llm": "LLM",
    "llms": "LLM",
    "large language models": "LLM",
    "genai": "GenAI",
    "generative ai": "GenAI",
    "agentic ai": "Agentic AI",
    "ai agents": "Agentic AI",
    "langchain": "LangChain",
    "langflow": "Langflow",
    "llamaindex": "LlamaIndex",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "hugging face": "Hugging Face",
    "huggingface": "Hugging Face",
    "transformers": "Transformers",
    "sentence transformers": "Sentence Transformers",
    "faiss": "FAISS",
    "chromadb": "ChromaDB",
    "pinecone": "Pinecone",
    "weaviate": "Weaviate",
    "qdrant": "Qdrant",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "opencv": "OpenCV",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",

    # Big Data & Data Engineering
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "pyspark": "PySpark",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    "airflow": "Apache Airflow",
    "apache airflow": "Apache Airflow",
    "snowflake": "Snowflake",
    "databricks": "Databricks",
    "bigquery": "BigQuery",
    "redshift": "Amazon Redshift",
    "hadoop": "Hadoop",
    "dbt": "dbt",
    "etl": "ETL",
    "elt": "ELT",
    "data warehouse": "Data Warehousing",
    "data lake": "Data Lake",

    # Programming Languages
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c#": "C#",
    "c++": "C++",
    "c/c++": "C++",
    "c programming": "C",
    "c language": "C",
    "golang": "Go",
    "go programming": "Go",
    "go language": "Go",
    "rust": "Rust",
    "php": "PHP",
    "ruby": "Ruby",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "dart": "Dart",
    "scala": "Scala",
    "r programming": "R",
    "r language": "R",
    "r studio": "R",
    "sql": "SQL",
    "bash": "Bash",
    "shell": "Shell Scripting",
    "powershell": "PowerShell",

    # Web & Frontend Frameworks
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "nuxt": "Nuxt.js",
    "angular": "Angular",
    "svelte": "Svelte",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "redux": "Redux",
    "zustand": "Zustand",
    "vite": "Vite",
    "webpack": "Webpack",

    # Backend Frameworks & Runtimes
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "nestjs": "NestJS",
    "asp.net": "ASP.NET",
    ".net": ".NET",
    ".net core": ".NET Core",
    "ruby on rails": "Ruby on Rails",
    "laravel": "Laravel",

    # Databases & Caching
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "oracle": "Oracle DB",
    "sql server": "SQL Server",
    "mssql": "SQL Server",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch",
    "neo4j": "Neo4j",

    # Architecture & APIs
    "rest api": "REST API",
    "restful": "REST API",
    "rest apis": "REST API",
    "api design": "API Design",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "microservices": "Microservices",
    "event-driven architecture": "Event-Driven Architecture",
    "system architecture": "System Architecture",
    "distributed systems": "Distributed Systems",
    "message broker": "Message Brokers",
    "rabbitmq": "RabbitMQ",
    "celery": "Celery",

    # Security & Identity
    "iam": "IAM",
    "saml": "SAML",
    "oauth": "OAuth 2.0",
    "oauth2": "OAuth 2.0",
    "oidc": "OIDC",
    "active directory": "Active Directory",
    "azure ad": "Azure AD",
    "ldap": "LDAP",
    "cybersecurity": "Cybersecurity",
    "owasp": "OWASP",
    "penetration testing": "Penetration Testing",
    "soc 2": "SOC 2",
    "iso 27001": "ISO 27001",
    "encryption": "Cryptography & Encryption",

    # Methodologies, Agile & Project Leadership
    "scrum": "Scrum",
    "scrum master": "Scrum Master",
    "agile": "Agile",
    "agile coach": "Agile Coach",
    "kanban": "Kanban",
    "safe agile": "SAFe",
    "scaled agile": "SAFe",
    "scaled agile framework": "SAFe",
    "prince2": "Prince2",
    "pmp": "PMP",
    "pmo": "PMO",
    "project management": "Project Management",
    "product management": "Product Management",
    "release management": "Release Management",
    "stakeholder management": "Stakeholder Management",
    "team leadership": "Team Leadership",
    "cross functional teams": "Cross-functional Teams",
    "process modelling": "Process Modelling",
    "business modelling": "Business Modelling",
    "change management": "Change Management",
    "tdd": "TDD",
    "bdd": "BDD",

    # Enterprise Tools & Business Platforms
    "jira": "Jira",
    "azure devops": "Azure DevOps",
    "confluence": "Confluence",
    "monday": "Monday.com",
    "salesforce": "Salesforce",
    "erp": "ERP",
    "saas": "SaaS",
    "b2b": "B2B",
    "b2b2c": "B2B2C",
    "sap": "SAP",
    "business intelligence": "Business Intelligence (BI)",
    "power bi": "Power BI",
    "tableau": "Tableau",
    "qlikview": "QlikView",
    "clickview": "QlikView",
    "o365": "Office 365",
    "office 365": "Office 365",
    "playwright": "Playwright",
    "cypress": "Cypress",
    "istqb": "ISTQB",
    "xml": "XML",
    "xslt": "XSLT",
    "scriptura": "Scriptura",
}

SKILL_CATEGORIES: Dict[str, List[str]] = {
    "Cloud & Infrastructure": ["AWS", "Azure", "GCP", "Terraform", "Docker", "Kubernetes", "Ansible", "Helm", "OpenShift", "CloudFormation", "Linux", "Ubuntu", "Nginx", "Apache"],
    "DevOps & CI/CD": ["CI/CD", "GitHub Actions", "GitLab CI", "Jenkins", "ArgoCD", "Git", "GitHub", "GitLab", "DevOps", "DevSecOps", "SRE", "Prometheus", "Grafana", "Datadog", "Splunk", "ELK Stack"],
    "AI, ML & Data": ["Agentic AI", "GenAI", "LLM", "LangChain", "Langflow", "LlamaIndex", "RAG", "PyTorch", "TensorFlow", "Scikit-learn", "Hugging Face", "Sentence Transformers", "FAISS", "ChromaDB", "Pinecone", "NLP", "Computer Vision", "Machine Learning", "Deep Learning", "Pandas", "NumPy", "Apache Spark", "PySpark", "Apache Kafka", "Apache Airflow", "Snowflake", "Databricks", "BigQuery", "Business Intelligence (BI)", "Power BI", "Tableau", "QlikView"],
    "Software & Programming": ["Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust", "PHP", "Ruby", "Kotlin", "Swift", "Dart", "Scala", "SQL", "Bash", "Shell Scripting", "PowerShell"],
    "Web & Full-Stack": ["React", "Next.js", "Vue", "Nuxt.js", "Angular", "Svelte", "HTML5", "CSS3", "Tailwind CSS", "Bootstrap", "Redux", "Zustand", "Node.js", "FastAPI", "Django", "Flask", "Spring Boot", "Express.js", "NestJS", "ASP.NET", ".NET", "Ruby on Rails"],
    "Databases & Storage": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle DB", "SQL Server", "Cassandra", "DynamoDB", "Elasticsearch", "Neo4j"],
    "Architecture & APIs": ["Microservices", "REST API", "GraphQL", "gRPC", "Event-Driven Architecture", "System Architecture", "Distributed Systems", "RabbitMQ", "Celery"],
    "Security & Identity": ["IAM", "SAML", "OAuth 2.0", "OIDC", "Active Directory", "Azure AD", "LDAP", "Cybersecurity", "OWASP", "Penetration Testing", "SOC 2", "ISO 27001"],
    "Methodologies & Leadership": ["Agile", "Scrum", "Scrum Master", "Agile Coach", "Kanban", "SAFe", "Prince2", "PMP", "PMO", "Project Management", "Product Management", "Release Management", "Stakeholder Management", "Team Leadership", "Cross-functional Teams", "Process Modelling", "TDD"],
    "Enterprise & Platforms": ["Salesforce", "ERP", "SaaS", "SAP", "Office 365", "Jira", "Confluence", "Monday.com"],
}

DEGREE_HIERARCHY: List[Tuple[str, List[str]]] = [
    ("Doctorate", ["phd", "ph.d", "doctorate", "doctoral"]),
    ("Master's", ["master", "m.s", "ms", "msc", "m.sc", "mba", "m.tech", "magister"]),
    ("Bachelor's", ["bachelor", "b.s", "bs", "bsc", "b.sc", "ba", "b.a", "b.tech", "b.e", "bachelier", "graduat", "licence"]),
    ("Associate", ["associate", "diploma", "graduat"]),
    ("High School", ["high school", "secondary", "baccalauréat"]),
]


class StructuredCandidateExtractor:
    """Extracts rich, normalized candidate information from raw resume text."""

    @classmethod
    def extract(cls, raw_text: str, file_name: Optional[str] = None) -> CandidateProfile:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        # 1. Contact, Identity & Web Links
        name = cls._extract_name(lines, file_name)
        email = cls._extract_email(raw_text)
        phone = cls._extract_phone(raw_text)
        location = cls._extract_location(raw_text)
        linkedin = cls._extract_linkedin(raw_text)
        github = cls._extract_github(raw_text)
        portfolio = cls._extract_portfolio(raw_text)
        languages = cls._extract_languages(raw_text)

        name_parts = name.split()
        first_name = name_parts[0] if name_parts else None
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None

        personal_info = PersonalInformation(
            full_name=name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            location=location,
            linkedin=linkedin,
            github=github,
            portfolio=portfolio,
        )

        # 2. Professional Summary
        summary = cls._extract_summary(raw_text, lines)

        # 3. Work Experience History
        experience_history = cls._extract_experience(raw_text, lines)
        total_exp = cls._calculate_total_experience(raw_text, experience_history)

        # 4. Education & Qualifications
        education_entries, highest_degree = cls._extract_education(raw_text, lines)

        # 5. Certifications
        certifications = cls._extract_certifications(raw_text, lines)

        # 6. Projects & Research
        projects = cls._extract_projects(raw_text, lines)

        # 7. Skills extraction & categorization
        skills, skills_by_category = cls._extract_skills(raw_text)

        # 8. Domains & Tools
        domains = cls._extract_domains(raw_text, experience_history)
        known_tools_list = [
            "Jira", "Confluence", "Monday.com", "Salesforce", "ERP", "Office 365",
            "QlikView", "SAP", "Git", "GitHub", "GitLab", "Docker", "Kubernetes",
            "Postman", "Swagger", "Power BI", "Tableau", "Terraform", "Jenkins",
            "VS Code", "PyCharm", "IntelliJ", "Linux"
        ]
        tools = [s for s in skills if s in known_tools_list]
        for t in ["Git", "Docker", "Kubernetes", "Linux", "Jira", "Confluence"]:
            if t in skills and t not in tools:
                tools.append(t)

        return CandidateProfile(
            full_name=name,
            email=email,
            phone=phone,
            location=location,
            personal_information=personal_info,
            professional_summary=summary,
            summary=summary,
            total_experience_years=total_exp,
            skills=skills,
            skills_by_category=skills_by_category,
            experience_history=experience_history,
            work_experience=experience_history,
            highest_qualification=highest_degree,
            education=education_entries,
            certifications=certifications,
            projects=projects,
            languages=languages,
            domains=domains,
            tools_and_technologies=tools,
            source_text=raw_text[:1200] if raw_text else None,
        )

    # ------------------ Contact & Identity ------------------

    @classmethod
    def _extract_name(cls, lines: List[str], file_name: Optional[str] = None) -> str:
        # Check first 8 lines for candidate name, skipping section headings
        header_filter = ["curriculum", "vitae", "resume", "cv", "page", "profile", "contact", "email", "phone", "personal details", "personal", "details", "information", "executive summary", "summary", "work history", "experience"]
        role_filter = ["scrum master", "project manager", "developer", "engineer", "architect", "practitioner", "consultant", "analyst", "lead", "it pm"]

        for line in lines[:8]:
            raw_line = line.strip()
            # Handle spaced-out characters like "J E R E M Y  S C H E P P E R S" or "J E R E M Y S C H E P P E R S"
            tokens = raw_line.split()
            if len(tokens) >= 4 and sum(len(t) == 1 for t in tokens) / len(tokens) > 0.7:
                # If there are double spaces, reconstruct words; otherwise combine
                if "  " in raw_line:
                    raw_line = " ".join("".join(chunk.split()) for chunk in raw_line.split("  ") if chunk.strip())
                else:
                    raw_line = "".join(tokens)

            # Strip document title prefixes like "CURRICULUM VITAE - " or "RESUME - "
            candidate_line = re.sub(r"^(?:curriculum\s+vitae|resume|cv)\s*[-–—:]\s*", "", raw_line, flags=re.IGNORECASE).strip()
            clean_line = re.sub(r"[•|\-–—]", "", candidate_line).strip()
            # Strip prefixes like "Full Name:" or "Name:"
            clean_line = re.sub(r"^(?:full\s*name|name)\s*:\s*", "", clean_line, flags=re.IGNORECASE).strip()
            # Skip if it ends with colon (likely a section header like "Executive Summary:")
            if clean_line.endswith(":") or clean_line.lower().endswith("summary"):
                continue
            if any(clean_line.lower() == h for h in header_filter):
                continue
            if any(r in clean_line.lower() for r in role_filter):
                continue

            words = clean_line.split()
            if 2 <= len(words) <= 6:
                if not any(f in clean_line.lower() for f in header_filter) and not "@" in clean_line and not any(ch.isdigit() for ch in clean_line):
                    return clean_line.title() if clean_line.isupper() else clean_line

        # Fallback to file name
        if file_name:
            stem = re.sub(r"\.(pdf|docx|doc)$", "", file_name, flags=re.IGNORECASE)
            stem = re.sub(r"^[0-9a-fA-F]{16}_", "", stem)  # Strip hash prefix
            stem = re.sub(r"_(?:Junior|Mid|Senior|Principal|Lead)_[A-Za-z0-9\-]+$", "", stem)  # Strip role suffix
            stem = re.sub(r"_\d+$", "", stem)  # Remove numeric suffixes like _24
            stem = re.sub(r"[_\-–—]", " ", stem).strip()
            words = [w for w in stem.split() if w.lower() not in ["cv", "resume", "profile"]]
            if words:
                return " ".join(w.capitalize() for w in words)

        return "Candidate Professional"

    @classmethod
    def _extract_email(cls, text: str) -> Optional[str]:
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        return match.group(0).lower() if match else None

    @classmethod
    def _extract_phone(cls, text: str) -> Optional[str]:
        # International and local formats
        match = re.search(r"(\+?\d{1,4}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}(?:[-.\s]?\d{2,4})?", text)
        if match:
            cand = match.group(0).strip()
            if len(re.sub(r"\D", "", cand)) >= 8:
                return cand
        return None

    @classmethod
    def _extract_linkedin(cls, text: str) -> Optional[str]:
        m = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_\-]+)", text, re.IGNORECASE)
        if m:
            return f"https://linkedin.com/in/{m.group(1)}"
        return None

    @classmethod
    def _extract_github(cls, text: str) -> Optional[str]:
        m = re.search(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-]+)", text, re.IGNORECASE)
        if m:
            return f"https://github.com/{m.group(1)}"
        return None

    @classmethod
    def _extract_portfolio(cls, text: str) -> Optional[str]:
        m = re.search(r"(?:https?://)?(?:www\.)?([a-zA-Z0-9\-]+\.(?:dev|io|me|portfolio|app|tech))", text, re.IGNORECASE)
        if m:
            return f"https://{m.group(1)}"
        return None

    @classmethod
    def _extract_location(cls, text: str) -> Optional[str]:
        loc_patterns = [
            r"(?:Luxembourg|Moutfort)",
            r"(?:Belgium|Brussels|Antwerp|Ghent|Leuven|Wallonia|Flanders|Liege|Namur)",
            r"(?:Paris|France|Lyon|Marseille|Toulouse|Bordeaux)",
            r"(?:London|UK|United Kingdom|Manchester|Edinburgh|Cambridge|Oxford)",
            r"(?:Amsterdam|Netherlands|Rotterdam|Utrecht|The Hague|Eindhoven)",
            r"(?:Berlin|Munich|Frankfurt|Germany|Hamburg|Stuttgart|Cologne)",
            r"(?:San Francisco|New York|Seattle|Austin|California|Texas|Boston|Chicago|Silicon Valley)",
            r"(?:Toronto|Vancouver|Canada|Montreal|Ontario)",
            r"(?:Sydney|Melbourne|Australia)",
            r"(?:Singapore|Zurich|Geneva|Switzerland|Dublin|Ireland|Stockholm|Sweden)",
            r"(?:Bangalore|Bengaluru|Hyderabad|Mumbai|Delhi|Pune|Chennai|India)",
        ]
        for pat in loc_patterns:
            m = re.search(r"([A-Za-z0-9\s]+,\s*" + pat + r"|" + pat + r"(?:,\s*[A-Za-z0-9\s]+)?)", text, re.IGNORECASE)
            if m:
                return m.group(0).strip(" |,-\n\t")
        return None

    @classmethod
    def _extract_languages(cls, text: str) -> List[str]:
        langs = []
        # Check language codes like EN-FR-NL
        if re.search(r"\bEN\b", text, re.I): langs.append("English (EN)")
        if re.search(r"\bFR\b", text, re.I): langs.append("French (FR)")
        if re.search(r"\bNL\b", text, re.I): langs.append("Dutch (NL)")
        if re.search(r"\bDE\b", text, re.I): langs.append("German (DE)")
        if re.search(r"\bES\b", text, re.I): langs.append("Spanish (ES)")
        if re.search(r"\bIT\b", text, re.I): langs.append("Italian (IT)")
        # Full names
        for word, label in [
            ("english", "English"),
            ("french", "French"),
            ("dutch", "Dutch"),
            ("german", "German"),
            ("spanish", "Spanish"),
            ("italian", "Italian"),
            ("portuguese", "Portuguese"),
            ("russian", "Russian"),
            ("chinese", "Chinese"),
            ("mandarin", "Mandarin"),
            ("japanese", "Japanese"),
            ("hindi", "Hindi"),
            ("arabic", "Arabic"),
        ]:
            if re.search(r"\b" + word + r"\b", text, re.I) and label not in [l.split()[0] for l in langs]:
                langs.append(label)
        return langs

    # ------------------ Professional Summary ------------------

    @classmethod
    def _extract_summary(cls, raw_text: str, lines: List[str]) -> Optional[str]:
        # Explicit section heading
        sum_idx = -1
        for i, l in enumerate(lines[:15]):
            if any(term in l.upper() for term in ["SUMMARY", "PROFILE", "ABOUT ME", "EXECUTIVE SUMMARY"]):
                sum_idx = i
                break

        if sum_idx != -1 and sum_idx + 1 < len(lines):
            # Collect lines until next heading
            collected = []
            for l in lines[sum_idx + 1 : sum_idx + 8]:
                if any(h in l.upper() for h in ["EXPERIENCE", "WORK", "EDUCATION", "SKILLS"]):
                    break
                collected.append(l)
            if collected:
                return " ".join(collected)

        # Check for opening narrative paragraph (like Jeremy Scheppers)
        for i, l in enumerate(lines[1:10]):
            if len(l.split()) >= 15 and not any(h in l.upper() for h in ["EXPERIENCE", "WORK", "EDUCATION", "SKILLS"]):
                # Paragraph found
                para = [l]
                for next_l in lines[i + 1 : i + 6]:
                    if any(h in next_l.upper() for h in ["EXPERIENCE", "WORK", "EDUCATION", "SKILLS"]) or next_l.startswith("•"):
                        break
                    para.append(next_l)
                return " ".join(para)

        return None

    # ------------------ Work Experience ------------------

    @classmethod
    def _extract_experience(cls, raw_text: str, lines: List[str]) -> List[WorkExperienceEntry]:
        experiences: List[WorkExperienceEntry] = []
        
        # Regex for finding date ranges representing roles
        # e.g., 2022 - 2025, Sept 2022 -> Jan 2026, 2018 - 2021
        date_pattern = re.compile(
            r"((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+)?(?:20\d{2}|19\d{2}))\s*"
            r"(?:-|–|—|to|->)\s*"
            r"((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+)?(?:20\d{2}|19\d{2}|Present|Current|Actuel))",
            re.IGNORECASE,
        )

        # Identify line indices where date ranges occur
        date_matches: List[Tuple[int, str, str, str]] = []
        for i, line in enumerate(lines):
            m = date_pattern.search(line)
            if m:
                date_matches.append((i, line, m.group(1), m.group(2)))

        if not date_matches:
            # Fallback single role detection
            return cls._fallback_experience(raw_text)

        for match_idx, (line_num, line_str, start_str, end_str) in enumerate(date_matches):
            # Compute duration
            duration = cls._calc_duration(start_str, end_str)

            # Detect title & company in lines adjacent to the date line
            title, company = cls._find_role_title_and_company(lines, line_num)

            # Determine boundary for responsibilities (up to next date match or major heading)
            next_line_boundary = date_matches[match_idx + 1][0] if match_idx + 1 < len(date_matches) else min(len(lines), line_num + 30)
            
            responsibilities = []
            technologies = []
            achievements = []
            
            for j in range(line_num + 1, next_line_boundary):
                cur_line = lines[j]
                if any(h in cur_line.upper() for h in ["EDUCATION", "SKILLS", "CERTIFICATIONS", "ADDITIONAL EXPERIENCE"]):
                    break
                if cur_line.startswith("•") or cur_line.startswith("-") or cur_line.startswith("*"):
                    clean_resp = cur_line.lstrip("•-* ").strip()
                    if clean_resp:
                        responsibilities.append(clean_resp)
                        # Check for metrics
                        if any(ch.isdigit() for ch in clean_resp) and any(m in clean_resp.lower() for m in ["%", "team", "people", "releases", "years", "million", "k", "budget"]):
                            achievements.append(clean_resp)
                elif len(cur_line.split()) > 4 and not date_pattern.search(cur_line):
                    # Narrative responsibility or context
                    responsibilities.append(cur_line)

                # Scan for technologies mentioned
                for kw, proper in CANONICAL_SKILL_CASING.items():
                    if re.search(r"\b" + re.escape(kw) + r"\b", cur_line, re.IGNORECASE) and proper not in technologies:
                        technologies.append(proper)

            summary = "; ".join(responsibilities[:2]) if responsibilities else f"{title} at {company or 'organization'}"

            experiences.append(
                WorkExperienceEntry(
                    title=title,
                    organization=company,
                    start_date=start_str,
                    end_date=end_str,
                    duration_years=duration,
                    responsibilities=responsibilities,
                    achievements=achievements,
                    technologies=technologies[:8],
                    summary=summary[:250],
                )
            )

        return experiences

    @classmethod
    def _find_role_title_and_company(cls, lines: List[str], date_line_idx: int) -> Tuple[str, Optional[str]]:
        title = "Professional Role"
        company = None

        # Look in preceding 2 lines and succeeding 2 lines
        candidates = []
        if date_line_idx > 0: candidates.append((lines[date_line_idx - 1], "pre"))
        if date_line_idx > 1: candidates.append((lines[date_line_idx - 2], "pre2"))
        if date_line_idx + 1 < len(lines): candidates.append((lines[date_line_idx + 1], "post"))
        if date_line_idx + 2 < len(lines): candidates.append((lines[date_line_idx + 2], "post2"))

        title_keywords = ["manager", "director", "lead", "officer", "engineer", "developer", "architect", "consultant", "coach", "master", "owner", "specialist", "analyst"]

        for cand_line, pos in candidates:
            cand_clean = cand_line.strip("•- \t")
            if any(k in cand_clean.lower() for k in title_keywords) and title == "Professional Role":
                title = cand_clean
            elif not company and len(cand_clean.split()) <= 5 and not any(k in cand_clean.lower() for k in ["experience", "work", "page"]):
                company = cand_clean

        return title, company

    MONTH_MAP = {
        "jan": 1, "january": 1, "janv": 1,
        "feb": 2, "february": 2, "fevr": 2,
        "mar": 3, "march": 3, "mars": 3,
        "apr": 4, "april": 4, "avril": 4,
        "may": 5, "mai": 5,
        "jun": 6, "june": 6, "juin": 6,
        "jul": 7, "july": 7, "juil": 7,
        "aug": 8, "august": 8, "aout": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10, "octobre": 10,
        "nov": 11, "november": 11, "novembre": 11,
        "dec": 12, "december": 12, "decembre": 12,
    }

    @classmethod
    def _parse_date_to_year_float(cls, date_str: Optional[str], is_end: bool = False) -> Optional[float]:
        if not date_str:
            return None
        cleaned = date_str.strip().lower()
        if re.search(r"\b(present|current|actuel|now|today|ongoing)\b", cleaned):
            now = datetime.now()
            return round(now.year + (now.month / 12.0), 2)

        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", cleaned)
        if not year_match:
            return None
        year = int(year_match.group(1))

        month = None
        for m_str, m_num in cls.MONTH_MAP.items():
            if re.search(r"\b" + m_str + r"\b", cleaned):
                month = m_num
                break
        if not month:
            num_m = re.search(r"\b(0?[1-9]|1[0-2])[\/\-\.](?:20\d{2}|19\d{2})\b", cleaned)
            if num_m:
                month = int(num_m.group(1))

        if month:
            val = year + ((month - 1) / 12.0 if not is_end else month / 12.0)
        else:
            val = float(year)
        return round(val, 2)

    @classmethod
    def _calc_duration(cls, start: str, end: str) -> float:
        try:
            s = cls._parse_date_to_year_float(start, is_end=False)
            e = cls._parse_date_to_year_float(end, is_end=True)
            if s is not None and e is not None and e > s:
                return round(e - s, 1)
            elif s is not None and e is not None and e == s:
                return 1.0

            s_year_match = re.search(r"(20\d{2}|19\d{2})", start)
            e_year_match = re.search(r"(20\d{2}|19\d{2})", end)
            s_year = int(s_year_match.group(1)) if s_year_match else 2020
            if re.search(r"present|current|actuel", end, re.I):
                e_year = datetime.now().year
            else:
                e_year = int(e_year_match.group(1)) if e_year_match else s_year + 1
            dur = float(max(0.5, e_year - s_year))
            return round(dur, 1)
        except Exception:
            return 1.0

    @classmethod
    def _calculate_total_experience(cls, text: str, experiences: List[WorkExperienceEntry]) -> float:
        """
        Calculates total experience ONLY from validated employment history intervals.
        Merges overlapping periods to prevent inflation (e.g. 2020-2023 and 2021-2024 = 4.0 yrs).
        Excludes education, certifications, and standalone projects.
        """
        intervals: List[Tuple[float, float]] = []
        for exp in experiences:
            s = cls._parse_date_to_year_float(exp.start_date, is_end=False)
            e = cls._parse_date_to_year_float(exp.end_date, is_end=True)
            if s is not None and e is not None and e > s:
                intervals.append((s, e))
            elif s is not None and e is not None and e == s:
                dur = exp.duration_years if exp.duration_years > 0 else 1.0
                intervals.append((s, s + dur))
            elif s is not None and exp.duration_years > 0:
                intervals.append((s, s + exp.duration_years))
            elif exp.duration_years > 0:
                intervals.append((2020.0, 2020.0 + exp.duration_years))

        if intervals:
            intervals.sort(key=lambda x: x[0])
            merged = [intervals[0]]
            for cur_s, cur_e in intervals[1:]:
                prev_s, prev_e = merged[-1]
                if cur_s <= prev_e:
                    # Overlapping or adjacent interval: merge
                    merged[-1] = (prev_s, max(prev_e, cur_e))
                else:
                    merged.append((cur_s, cur_e))
            total = sum(e - s for s, e in merged)
            return round(max(0.5, total), 1)

        m = re.search(r"(\d+)\+?\s*(?:years|yrs)\s*(?:of\s*)?experience", text, re.IGNORECASE)
        if m:
            return round(float(m.group(1)), 1)

        return 1.0

    @classmethod
    def _fallback_experience(cls, text: str) -> List[WorkExperienceEntry]:
        total_exp = 3.5
        m = re.search(r"(\d+)\+?\s*(?:years|yrs)", text, re.I)
        if m: total_exp = float(m.group(1))

        return [
            WorkExperienceEntry(
                title="Technology Professional",
                organization=None,
                duration_years=total_exp,
                summary=f"Professional experience encompassing {total_exp} years.",
            )
        ]

    # ------------------ Education ------------------

    @classmethod
    def _extract_education(cls, text: str, lines: List[str]) -> Tuple[List[EducationEntry], str]:
        entries: List[EducationEntry] = []
        highest_tier = "Bachelor's"

        edu_headers = [r"\bEDUCATION\b", r"\bACADEMIC BACKGROUND\b", r"\bFORMATION\b", r"\bDIPLOMAS?\b"]
        stop_headers = [r"\bEXPERIENCE\b", r"\bSKILLS\b", r"\bCERTIFICATIONS?\b", r"\bLANGUAGES?\b", r"\bPROJECTS?\b"]

        edu_lines = []
        in_edu = False
        for l in lines:
            clean_l = l.strip()
            if not in_edu and any(re.search(pat, clean_l, re.IGNORECASE) for pat in edu_headers) and len(clean_l.split()) <= 4:
                in_edu = True
                continue
            if in_edu:
                if any(re.search(pat, clean_l, re.IGNORECASE) for pat in stop_headers) and len(clean_l.split()) <= 4:
                    break
                edu_lines.append(clean_l)

        # Do NOT infer education from random text if no education section exists in the CV
        if not edu_lines:
            return [], "Bachelor's"

        scan_text = "\n".join(edu_lines)
        scan_lower = scan_text.lower()

        # Specific patterns for degrees that avoid matching 'Scrum Master'
        DEGREE_PATTERNS = [
            ("Doctorate", [r"\bph\.?d\b", r"\bdoctorate\b", r"\bdoctoral\b"]),
            ("Master's", [r"\bm\.?s\.?\b", r"\bmsc\b", r"\bm\.sc\b", r"\bmba\b", r"\bm\.tech\b", r"(?<!scrum\s)(?<!agile\s)\bmaster(?:'s)?(?:\s+(?:degree|of|in|en))?\b"]),
            ("Bachelor's", [r"\bb\.?s\.?\b", r"\bbsc\b", r"\bb\.sc\b", r"\bba\b", r"\bb\.a\b", r"\bb\.tech\b", r"\bbachelor(?:'s)?(?:\s+(?:degree|of|in|en))?\b", r"\bbachelier\b", r"\blicence\b"]),
            ("Associate", [r"\bassociate\b", r"\bdiploma\b", r"\bgraduat\b", r"\bcap\b", r"\bcertificat[e]?\b", r"\bcandidate\b", r"\bcandidature\b"]),
            ("High School", [r"\bhigh school\b", r"\bsecondary\b", r"\bbaccalauréat\b"]),
        ]

        for tier_name, patterns in DEGREE_PATTERNS:
            for pat in patterns:
                match = re.search(pat, scan_lower, re.IGNORECASE)
                if match:
                    highest_tier = tier_name
                    # Find graduation year in education lines
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", scan_text)
                    grad_year = int(year_match.group(1)) if year_match else None

                    # Check for field of study
                    field = None
                    if "computer science" in scan_lower: field = "Computer Science"
                    elif "information technology" in scan_lower or "infotronics" in scan_lower: field = "Information Technology"
                    elif "engineering" in scan_lower: field = "Engineering"
                    elif "business" in scan_lower or "management" in scan_lower: field = "Business & Management"
                    elif "pedagogical" in scan_lower or "pedagogie" in scan_lower: field = "Pedagogy"

                    # Check for institution
                    inst = None
                    inst_match = re.search(r"(?:at|from|,)\s+([A-Z][A-Za-z\s]+(?:University|College|Institute|School|CERIA|ULB|VUB|KUL|Polytechnique))", scan_text)
                    if inst_match:
                        inst = inst_match.group(1).strip()

                    degree_title = f"{tier_name}" + (f" in {field}" if field else "")

                    entries.append(
                        EducationEntry(
                            degree=degree_title,
                            field=field,
                            institution=inst,
                            graduation_year=grad_year,
                        )
                    )
                    break
            if entries:
                break

        return entries, highest_tier

    # ------------------ Certifications ------------------

    @classmethod
    def _extract_certifications(cls, text: str, lines: List[str]) -> List[CertificationEntry]:
        cert_list: List[CertificationEntry] = []
        known_certs = [
            ("Prince2", "AXELOS"),
            ("Scrum Master", "Scrum.org / Scrum Alliance"),
            ("Agile Master", "SCRUMstudy"),
            ("PMP", "PMI"),
            ("CAPM", "PMI"),
            ("PMI-ACP", "PMI"),
            ("AWS Certified", "Amazon Web Services"),
            ("Azure Certified", "Microsoft"),
            ("Google Cloud Certified", "Google Cloud"),
            ("GCP Certified", "Google Cloud"),
            ("ITIL", "AXELOS"),
            ("CISSP", "ISC2"),
            ("CISA", "ISACA"),
            ("CISM", "ISACA"),
            ("CEH", "EC-Council"),
            ("CompTIA Security+", "CompTIA"),
            ("CompTIA Network+", "CompTIA"),
            ("CKA", "Linux Foundation / CNCF"),
            ("CKAD", "Linux Foundation / CNCF"),
            ("CKS", "Linux Foundation / CNCF"),
            ("Terraform Associate", "HashiCorp"),
            ("Salesforce Certified", "Salesforce"),
            ("Databricks Certified", "Databricks"),
            ("Snowflake Certified", "Snowflake"),
            ("Oracle Certified", "Oracle"),
        ]

        for cert_name, issuer in known_certs:
            if re.search(r"\b" + re.escape(cert_name) + r"\b", text, re.IGNORECASE):
                # Look for year near the certification name
                m = re.search(re.escape(cert_name) + r"[^\n]{0,35}\b(20\d{2}|19\d{2})\b", text, re.I)
                yr = int(m.group(1)) if m else None
                cert_list.append(CertificationEntry(name=cert_name, issuing_organization=issuer, year=yr))

        return cert_list

    # ------------------ Projects ------------------

    @classmethod
    def _extract_projects(cls, text: str, lines: List[str]) -> List[ProjectEntry]:
        projects: List[ProjectEntry] = []

        # 1. Look for explicit project section
        proj_headers = [r"\bPROJECTS?\b", r"\bPERSONAL PROJECTS?\b", r"\bKEY PROJECTS?\b", r"\bACADEMIC PROJECTS?\b", r"\bRESEARCH WORK\b"]
        stop_headers = [r"\bEXPERIENCE\b", r"\bEDUCATION\b", r"\bSKILLS\b", r"\bCERTIFICATIONS?\b", r"\bLANGUAGES?\b"]

        proj_lines = []
        in_proj = False
        for l in lines:
            clean_l = l.strip()
            if not in_proj and any(re.search(pat, clean_l, re.IGNORECASE) for pat in proj_headers) and len(clean_l.split()) <= 4:
                in_proj = True
                continue
            if in_proj:
                if any(re.search(pat, clean_l, re.IGNORECASE) for pat in stop_headers) and len(clean_l.split()) <= 4:
                    break
                proj_lines.append(clean_l)

        if proj_lines:
            current_name = None
            current_desc = []
            for pl in proj_lines:
                if (pl.startswith("•") or pl.startswith("-") or pl.startswith("*")) and current_name:
                    current_desc.append(pl.lstrip("•-* ").strip())
                elif ":" in pl and len(pl.split(":")[0].split()) <= 5:
                    if current_name:
                        full_desc = " ".join(current_desc)
                        p_tech = [proper for kw, proper in CANONICAL_SKILL_CASING.items() if re.search(r"\b" + re.escape(kw) + r"\b", full_desc, re.I)]
                        projects.append(ProjectEntry(name=current_name, description=full_desc, technologies=p_tech[:6]))
                    parts = pl.split(":", 1)
                    current_name = parts[0].strip()
                    current_desc = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
                elif not current_name and len(pl.split()) <= 6:
                    current_name = pl
                elif current_name:
                    current_desc.append(pl)

            if current_name:
                full_desc = " ".join(current_desc)
                p_tech = [proper for kw, proper in CANONICAL_SKILL_CASING.items() if re.search(r"\b" + re.escape(kw) + r"\b", full_desc, re.I)]
                projects.append(ProjectEntry(name=current_name, description=full_desc, technologies=p_tech[:6]))

        # 2. Look for project indicator keywords anywhere if none found above
        if not projects:
            for line in lines:
                if any(term in line.lower() for term in ["zennevalley", "research project", "open source project", "hobby project", "side project", "capstone project"]):
                    clean_p = line.lstrip("•-* ").strip()
                    name = clean_p.split(":")[0] if ":" in clean_p else "AI Innovation Project"
                    desc = clean_p.split(":")[-1] if ":" in clean_p else clean_p
                    p_tech = [proper for kw, proper in CANONICAL_SKILL_CASING.items() if re.search(r"\b" + re.escape(kw) + r"\b", desc, re.I)]
                    projects.append(
                        ProjectEntry(
                            name=name,
                            description=desc,
                            technologies=p_tech[:6],
                            responsibilities=["Prototyping, implementation, and evaluation of technical deliverables"],
                        )
                    )

        return projects

    # ------------------ Skills Extraction & Categorization ------------------

    @classmethod
    def _extract_skills(cls, text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        found_skills_set: Set[str] = set()
        categorized: Dict[str, List[str]] = {cat: [] for cat in SKILL_CATEGORIES.keys()}

        # 1. Match against comprehensive canonical dictionary
        for kw, proper_name in CANONICAL_SKILL_CASING.items():
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills_set.add(proper_name)
                # Assign to categories
                for cat, items in SKILL_CATEGORIES.items():
                    if proper_name in items and proper_name not in categorized[cat]:
                        categorized[cat].append(proper_name)

        if re.search(r"\bSAFe\b", text):
            found_skills_set.add("SAFe")
            if "Methodologies & Leadership" in categorized and "SAFe" not in categorized["Methodologies & Leadership"]:
                categorized["Methodologies & Leadership"].append("SAFe")

        if re.search(r"\bBI\b", text) or "business intelligence" in text.lower():
            found_skills_set.add("Business Intelligence (BI)")
            if "AI, ML & Data" in categorized and "Business Intelligence (BI)" not in categorized["AI, ML & Data"]:
                categorized["AI, ML & Data"].append("Business Intelligence (BI)")

        # 2. Extract skills from dedicated SKILLS sections if present
        skills_section_match = re.search(
            r"S\s*K\s*I\s*L\s*L\s*S[^\n]*\n(.*?)(?=\n[A-Z\s]{4,}|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if skills_section_match:
            sec_text = skills_section_match.group(1)
            # Tokenize by commas, bullets, newlines, pipes
            tokens = re.split(r"[,•|\n\t\r\-–—/]", sec_text)
            for token in tokens:
                token_clean = re.sub(r"^[^\w]+|[^\w]+$", "", token).strip()
                if 2 <= len(token_clean) <= 35 and not any(ch.isdigit() for ch in token_clean):
                    low = token_clean.lower()
                    if low in CANONICAL_SKILL_CASING:
                        found_skills_set.add(CANONICAL_SKILL_CASING[low])
                    elif len(token_clean.split()) <= 2 and not any(w in low for w in ["result", "proven", "leader", "expert", "ability", "skill", "strong", "excellent"]):
                        found_skills_set.add(token_clean.title())

        # Clean empty categories
        categorized = {k: v for k, v in categorized.items() if v}

        skills_list = sorted(list(found_skills_set))
        return skills_list, categorized

    # ------------------ Domains ------------------

    @classmethod
    def _extract_domains(cls, text: str, experiences: List[WorkExperienceEntry]) -> List[str]:
        domains = []
        domain_keywords = {
            "Rail Freight & Logistics": ["freight", "logistics", "transport", "train", "supply chain"],
            "Digital Audio & Media": ["audio", "streaming", "music", "radio", "media", "broadcasting"],
            "Ad-Tech & Advertising": ["ad-tech", "advertising", "ssp", "dmp", "marketing"],
            "Fintech & Banking": ["banking", "fintech", "financial", "payment", "insurance"],
            "Enterprise SaaS & ERP": ["erp", "saas", "salesforce", "enterprise"],
            "Public Sector & Government": ["government", "european commission", "public sector", "bosa"],
            "Telecommunications": ["telecom", "smart metering", "metering"],
        }
        text_lower = text.lower()
        for domain_name, terms in domain_keywords.items():
            if any(t in text_lower for t in terms):
                domains.append(domain_name)
        return domains
