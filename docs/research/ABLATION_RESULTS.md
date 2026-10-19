# Multi-Criteria Scoring Ablation & Sensitivity Analysis

**Project:** Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation  
**Document:** Sensitivity Analysis Across Weight Regimes  
**Status:** MEASURED & VERIFIED

---

## 1. Experimental Setup & Configurations

To observe how candidate rankings and fitment scores respond to shifting recruiter priorities, three real candidates were evaluated against the **Senior IT Project Manager & Agile Transformation Lead** role under four distinct parameter regimes:

1. **Regime A — Baseline (Balanced):**  
   $w_{\text{sem}} = 0.35, \quad w_{\text{skill}} = 0.35, \quad w_{\text{exp}} = 0.20, \quad w_{\text{qual}} = 0.10$
2. **Regime B — Semantic-Heavy:**  
   $w_{\text{sem}} = 0.55, \quad w_{\text{skill}} = 0.20, \quad w_{\text{exp}} = 0.15, \quad w_{\text{qual}} = 0.10$
3. **Regime C — Skill-Heavy:**  
   $w_{\text{sem}} = 0.20, \quad w_{\text{skill}} = 0.55, \quad w_{\text{exp}} = 0.15, \quad w_{\text{qual}} = 0.10$
4. **Regime D — Experience-Heavy:**  
   $w_{\text{sem}} = 0.20, \quad w_{\text{skill}} = 0.20, \quad w_{\text{exp}} = 0.50, \quad w_{\text{qual}} = 0.10$

---

## 2. Measured Candidate Fitment Scores Across Regimes

Target Job: **Senior IT Project Manager** (Required Skills: Agile, Scrum, Project Management, Stakeholder Management, Jira; Min Exp: 8.0 Years; Degree: Bachelor's).

| Candidate Name | Extracted Tenure | Extracted Skills Count | Baseline ($S_{\text{final}}$) | Semantic-Heavy | Skill-Heavy | Experience-Heavy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Jeremy Scheppers** | 13.0 yrs | 32 skills | **0.8504** (Rank 1) | **0.8069** (Rank 1) | **0.8725** (Rank 1) | **0.9145** (Rank 1) |
| **Hugues Crepin** | 20.0 yrs | 23 skills | **0.6923** (Rank 2) | **0.6316** (Rank 2) | **0.7133** (Rank 2) | **0.8113** (Rank 2) |
| **Amel Bouzaid** | 1.0 yrs | 5 skills | **0.4510** (Rank 3) | **0.4953** (Rank 3) | **0.4222** (Rank 3) | **0.4044** (Rank 3) |

---

## 3. Component Score Breakdown

| Candidate | Semantic Alignment ($S_{\text{sem}}$) | Skill Recall ($S_{\text{skill}}$) | Experience Alignment ($S_{\text{exp}}$) | Qualification Tier ($S_{\text{qual}}$) |
| :--- | :---: | :---: | :---: | :---: |
| **Jeremy Scheppers** | 0.6926 | 0.8800 | 1.0000 (13 yrs $\ge$ 8 yrs) | 1.0000 (Bachelor's $\ge$ Bachelor's) |
| **Hugues Crepin** | 0.4865 | 0.7200 | 1.0000 (20 yrs $\ge$ 8 yrs) | 0.7000 (Associate vs Bachelor's) |
| **Amel Bouzaid** | 0.5290 | 0.3200 | 0.2691 (1 yr vs 8 yrs shortfall) | 1.0000 (Bachelor's $\ge$ Bachelor's) |

---

## 4. Key Scientific Observations

1. **Ranking Stability:** Candidate ranking order (Jeremy > Hugues > Amel) remained stable across all 4 weight configurations because Jeremy dominates in both direct skill overlap and semantic alignment.
2. **Tenure Penalty Sensitivity:** In the **Experience-Heavy** regime ($w_{\text{exp}} = 0.50$), Hugues Crepin's score jumped from $0.6923$ to **$0.8113$** (+17.2%) due to his 20-year career history. Conversely, Amel Bouzaid's score plummeted from $0.4510$ down to **$0.4044$** (-10.3%) because the 7-year experience shortfall was heavily penalized.
3. **Semantic Dilution vs Precision:** Under **Semantic-Heavy** ($w_{\text{sem}} = 0.55$), Amel's score increased to $0.4953$ because dense vector embeddings capture general vocabulary similarity without penalizing specific missing tools. The hybrid composite score effectively mitigates this semantic false-positive risk.
