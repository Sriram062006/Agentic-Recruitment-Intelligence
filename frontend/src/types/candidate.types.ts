export interface WorkExperienceEntry {
  title: string;
  organization?: string;
  duration_years: number;
  summary?: string;
}

export interface EducationEntry {
  degree: string;
  field?: string;
  institution?: string;
  graduation_year?: number;
}

export interface CandidateProfile {
  full_name: string;
  email?: string;
  phone?: string;
  location?: string;
  total_experience_years: number;
  skills: string[];
  experience_history: WorkExperienceEntry[];
  highest_qualification: string;
  education: EducationEntry[];
  summary?: string;
}

export interface CandidateResponse {
  id: string;
  file_name: string;
  storage_path: string;
  file_hash: string;
  raw_text: string;
  structured_profile: CandidateProfile;
  faiss_index_id?: number;
  created_at: string;
  updated_at: string;
}
