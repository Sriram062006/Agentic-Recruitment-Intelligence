export interface WorkExperienceEntry {
  title: string;
  organization?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  duration_years: number;
  responsibilities?: string[];
  achievements?: string[];
  technologies?: string[];
  domain?: string;
  summary?: string;
}

export interface EducationEntry {
  degree: string;
  field?: string;
  institution?: string;
  graduation_year?: number;
}

export interface CertificationEntry {
  name: string;
  issuing_organization?: string;
  year?: number;
}

export interface ProjectEntry {
  name: string;
  description?: string;
  technologies?: string[];
  responsibilities?: string[];
  outcomes?: string;
}

export interface PersonalInformation {
  full_name: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  github?: string;
  portfolio?: string;
}

export interface CandidateProfile {
  full_name: string;
  email?: string;
  phone?: string;
  location?: string;
  personal_information?: PersonalInformation;
  professional_summary?: string;
  summary?: string;
  total_experience_years: number;
  experience_years_source?: "calculated" | "manual" | string;
  experience_years_original_calculated?: number;
  experience_years_updated_by?: string;
  experience_years_updated_at?: string;
  skills: string[];
  skills_by_category?: Record<string, string[]>;
  experience_history: WorkExperienceEntry[];
  work_experience?: WorkExperienceEntry[];
  highest_qualification: string;
  education: EducationEntry[];
  certifications?: CertificationEntry[];
  projects?: ProjectEntry[];
  languages?: string[];
  achievements?: string[];
  domains?: string[];
  tools_and_technologies?: string[];
  source_text?: string;
  is_synthetic?: boolean;
}

export interface CandidateResponse {
  id: string;
  recruiter_id?: string;
  file_name: string;
  storage_path: string;
  file_hash: string;
  raw_text: string;
  structured_profile: CandidateProfile;
  faiss_index_id?: number;
  is_synthetic?: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidateSummary {
  id: string;
  full_name: string;
  file_name: string;
  total_experience_years: number;
  highest_qualification: string;
  skills_count: number;
  faiss_indexed: boolean;
  created_at: string;
}
