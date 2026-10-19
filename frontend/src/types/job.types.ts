export interface JobProfile {
  title: string;
  department?: string;
  company_or_client?: string;
  location?: string;
  remote_work?: string;
  start_date?: string;
  end_date?: string;
  work_regime?: string;
  summary: string;
  context_or_project_background?: string;
  required_skills: string[];
  preferred_skills: string[];
  must_have_requirements?: string[];
  should_have_requirements?: string[];
  min_experience_years: number;
  max_experience_years?: number;
  preferred_experience_years?: number;
  required_qualification: string;
  preferred_qualifications?: string[];
  certifications?: string[];
  required_certifications?: string[];
  languages?: string[];
  key_responsibilities: string[];
  seniority?: string;
  technical_environment?: string[];
  tools?: string[];
  technologies?: string[];
  frameworks?: string[];
  platforms?: string[];
  methodologies?: string[];
  domain?: string;
  stakeholder_requirements?: string[];
  management_requirements?: string[];
  compliance_requirements?: string[];
  other_requirements?: string[];
  extraction_status?: string;
  extraction_confidence?: number;
  source_text?: string;
}

export interface JobResponse {
  id: string;
  title: string;
  department?: string;
  storage_path: string;
  raw_content: string;
  structured_profile: JobProfile;
  created_at: string;
  updated_at: string;
}
