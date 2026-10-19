# Research Dataset Specification & Annotation Protocol

**Project:** Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation  
**Document:** Dataset Metadata, Extraction Grounding, and Annotation Guidelines  
**Version:** 1.0.0  
**Status:** Approved & Verified

---

## 1. Candidate Pool Dataset Overview

The evaluation suite utilizes real curriculum vitae documents sourced from European IT recruitment pools (Belgium Hotlist). Documents are processed in their native format (`PDF` and `DOCX`) without manual text pre-filtering.

### 1.1 Evaluated Candidate Profiles (Sample of 10 Real Candidates)

| # | Candidate Identifier | Source File | Extracted Tenure | Highest Degree | Total Skills Extracted | Sample Canonical Skills |
| :-: | :--- | :--- | :-: | :---: | :-: | :--- |
| **1** | **Jeremy Scheppers** | `Jeremy Scheppers_24.pdf` | 13.0 yrs | Bachelor's | 32 | AWS, Agentic AI, Agile, Azure, B2B, CI/CD, Jira, Scrum Master |
| **2** | **Hugues Crepin** | `Hugues CREPIN.pdf` | 20.0 yrs | Associate | 23 | AWS, Active Directory, Azure AD, DevSecOps, IAM, SAML, ITIL |
| **3** | **Amel Bouzaid** | `Amel Bouzaid_3.pdf` | 1.0 yrs | Bachelor's | 5 | Agile, Agile Coach, Linux, SAP, Stakeholder Management |
| **4** | **Annesophie Drincqbier** | `Anne - Sophie Drincqbier_18.pdf` | 35.0 yrs | Master's | 5 | Office 365, Prince2, Project Management, SAP, SQL |
| **5** | **Joachim Kersemans** | `Joachim Kersemans_10.pdf` | 9.0 yrs | High School | 6 | AWS, Active Directory, Agile, Azure, Office 365, ITIL |
| **6** | **ANN DE SPIEGELEIRE** | `ANN DE SPIEGELEIRE_17.pdf` | 15.0 yrs | Master's | 11 | Agile, Scrum, Project Management, Change Management |
| **7** | **Brants Tino** | `Brants Tino_26.pdf` | 18.0 yrs | Bachelor's | 14 | Project Management, SAP, ITIL, Telecom, Stakeholder Mgmt |
| **8** | **Bruno Stevens** | `Bruno stevens_11.pdf` | 12.0 yrs | Bachelor's | 16 | Agile, Scrum Master, Prince2, JIRA, Confluence, ERP |
| **9** | **Hans Veldman** | `C.V. Harmannus Robert..._30.docx` | 22.0 yrs | Master's | 19 | Program Management, PMP, Agile, Cloud, Enterprise Architecture |
| **10**| **Christophe D'Hoore** | `CHRISTOPHE D'HOORE_26.pdf` | 14.0 yrs | Master's | 12 | Business Analysis, Agile, Scrum, Requirements Engineering |

---

## 2. Benchmark Job Descriptions (Enterprise Target Roles)

Five distinct enterprise job roles were defined representing diverse technological stacks and seniority requirements:

1. **Role 1 — Senior IT Project Manager & Agile Transformation Lead**
   - *Department:* Program Management Office
   - *Min Experience:* 8.0 Years | *Min Degree:* Bachelor's
   - *Required Skills:* Agile, Scrum, Project Management, Stakeholder Management, Jira
   - *Preferred Skills:* Prince2, PMP, SAFe, Cloud Migration, Azure

2. **Role 2 — Cloud Infrastructure & DevOps Lead**
   - *Department:* Cloud Operations
   - *Min Experience:* 5.0 Years | *Min Degree:* Bachelor's
   - *Required Skills:* AWS, Azure, Docker, Kubernetes, CI/CD, Linux
   - *Preferred Skills:* Terraform, GitHub Actions, Python, Prometheus

3. **Role 3 — Identity & Access Management (IAM) Security Architect**
   - *Department:* Information Security
   - *Min Experience:* 6.0 Years | *Min Degree:* Bachelor's
   - *Required Skills:* IAM, Active Directory, Azure AD, SAML, OAuth
   - *Preferred Skills:* CISSP, DevSecOps, SailPoint, OIDC

4. **Role 4 — Senior Python & GenAI Platform Engineer**
   - *Department:* AI Research & Innovation
   - *Min Experience:* 4.0 Years | *Min Degree:* Master's
   - *Required Skills:* Python, FastAPI, SQL, Docker, REST API
   - *Preferred Skills:* LLM, Agentic AI, LangChain, Vector Databases, PostgreSQL

5. **Role 5 — Enterprise SAP Solutions & Release Manager**
   - *Department:* Enterprise Systems
   - *Min Experience:* 10.0 Years | *Min Degree:* Master's
   - *Required Skills:* SAP, ERP, Release Management, Project Management
   - *Preferred Skills:* Office 365, SQL, Process Modelling

---

## 3. Human Ground Truth Annotation Template & Protocol

To enable quantitative Information Retrieval accuracy validation in future academic phases, human recruitment experts must populate the following evaluation matrix:

### 3.1 Relevance Grading Scale
- **Grade 3 (Highly Relevant):** Candidate exceeds minimum experience, holds all required skills, and has verified domain relevance.
- **Grade 2 (Relevant / Viable):** Candidate meets core requirements with minor addressable skill or tool deficits.
- **Grade 1 (Marginal):** Underqualified tenure or missing core mandatory technologies; transferable profile.
- **Grade 0 (Irrelevant):** Distinct specialization with negligible domain or skills overlap.

### 3.2 Candidate $\times$ Role Annotation Template

| Candidate Name | Target Job Role | Human Judge 1 (0-3) | Human Judge 2 (0-3) | Consensus Relevance | Notes / Primary Justification |
| :--- | :--- | :---: | :---: | :---: | :--- |
| Jeremy Scheppers | Senior IT Project Manager | `[Pending]` | `[Pending]` | `[Pending]` | Strong PMO/Scrum background, Prince2 certified |
| Jeremy Scheppers | Cloud & DevOps Lead | `[Pending]` | `[Pending]` | `[Pending]` | Has AWS/Azure and CI/CD, but primary focus is PM |
| Jeremy Scheppers | IAM Security Architect | `[Pending]` | `[Pending]` | `[Pending]` | Lacks IAM/SAML focus |
| Hugues Crepin | IAM Security Architect | `[Pending]` | `[Pending]` | `[Pending]` | 20 yrs IAM Service Manager, CISSP certified |
| Hugues Crepin | Senior IT Project Manager | `[Pending]` | `[Pending]` | `[Pending]` | Substantial managerial tenure, Prince2 certified |
| Amel Bouzaid | Senior IT Project Manager | `[Pending]` | `[Pending]` | `[Pending]` | 1 yr tenure vs 8 yrs required (shortfall) |
| Anne-Sophie Drincqbier| Enterprise SAP Release Mgr | `[Pending]` | `[Pending]` | `[Pending]` | 35 yrs experience, strong SAP background |

> [!IMPORTANT]
> **Academic Integrity Statement:** Because human consensus ground truth labels have not yet been produced by double-blind recruitment panels, quantitative IR metrics (Precision@K, Recall@K, NDCG@K) are classified as **NOT AVAILABLE** for production claims and are reserved for future experimental benchmarking.
