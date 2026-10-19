export interface FitmentWeightsConfig {
  semantic_weight: number;
  skill_weight: number;
  experience_weight: number;
  qualification_weight: number;
}

export interface HeuristicConfig {
  alpha_skill_weight: number;
  beta_experience_penalty: number;
  fitment_strong_threshold: number;
  fitment_moderate_threshold: number;
}

export interface EvaluationConfigRequest {
  job_ids?: string[];
  candidate_ids?: string[];
  weights?: FitmentWeightsConfig;
  heuristics?: HeuristicConfig;
  evaluation_engine?: "ai_fitment" | "deterministic" | string;
}

export interface ExperienceComparison {
  required_years: number;
  candidate_years: number;
  delta_years: number;
  meets_requirement: boolean;
}

export interface QualificationComparison {
  required_degree: string;
  candidate_degree: string;
  status: string;
}

export interface RequirementAnalysisItem {
  requirement: string;
  type?: "MUST_HAVE" | "SHOULD_HAVE" | "RESPONSIBILITY" | "QUALIFICATION" | string;
  status: "MATCHED" | "PARTIALLY MATCHED" | "PARTIALLY_MATCHED" | "MISSING" | "UNKNOWN" | string;
  evidence: string;
  validation_status?: "VERIFIED" | "PARTIALLY_VERIFIED" | "UNSUPPORTED" | string;
}

export interface ExplainabilityPayload {
  fitment_score?: number;
  fitment_category?: string;
  confidence?: number;
  matched_skills: string[];
  missing_skills: string[];
  matched_preferred_skills: string[];
  missing_preferred_skills: string[];
  experience_comparison?: {
    required_years: number;
    candidate_years: number;
    delta_years: number;
    meets_requirement: boolean;
  };
  qualification_comparison?: {
    required_degree: string;
    candidate_degree: string;
    status: string;
  };
  strengths: string[];
  skill_gaps: string[];
  risk_flags?: string[];
  uncertainty_flags?: string[];
  recommendation_rationale: string;
  requirement_analysis?: RequirementAnalysisItem[];
  recruiter_recommendation?: string;
  missing_skills_analysis?: {
    skill: string;
    status: string;
    classification: string;
    evidence_notes: string;
  }[];
  recruiter_verification_questions?: string[];
  score_consistency?: {
    status: string;
    flags: string[];
    original_score: number;
    adjusted_score: number;
  };
  model_metadata?: {
    provider?: string;
    model?: string;
    prompt_version?: string;
    evaluated_at?: string;
  };
}

export interface MatrixCell {
  candidate_id: string;
  job_id: string;
  composite_score: number;
  rank_in_role: number;
  fitment_tier: string;
}

export interface EvaluationMatrixResponse {
  run_id: string;
  candidates: { id: string; name: string }[];
  jobs: { id: string; title: string }[];
  cells: MatrixCell[];
  total_evaluations: number;
}

export interface LeaderboardEntry {
  rank: number;
  candidate_id: string;
  candidate_name: string;
  total_experience_years: number;
  highest_qualification: string;
  composite_score: number;
  semantic_score: number;
  skill_score: number;
  experience_score: number;
  qualification_score: number;
  matched_skills_count: number;
  missing_skills_count: number;
  fitment_category?: string;
  recruiter_recommendation?: string;
}

export interface EvaluationRunResponse {
  id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  total_candidates: number;
  total_jobs: number;
  total_evaluations: number;
  config: Record<string, any>;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}
