export interface JobProfile {
  title: string;
  department?: string;
  summary: string;
  required_skills: string[];
  preferred_skills: string[];
  min_experience_years: number;
  preferred_experience_years?: number;
  required_qualification: string;
  key_responsibilities: string[];
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
