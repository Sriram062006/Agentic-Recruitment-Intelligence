export type UserRole = "admin" | "recruiter" | "viewer";

export interface RecruiterProfile {
  user_id: string;
  full_name: string;
  email?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminUserListItem {
  user_id: string;
  full_name: string;
  email?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  candidates_count?: number;
  jobs_count?: number;
  runs_count?: number;
}

export interface AdminStatsResponse {
  total_users: number;
  active_recruiters: number;
  total_candidates: number;
  total_jobs: number;
  total_runs: number;
  total_evaluations: number;
}
