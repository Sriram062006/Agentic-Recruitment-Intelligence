import React, { useEffect, useState } from "react";
import { fetchJobs, uploadJobs } from "@/lib/api-client";
import { JobResponse } from "@/types/job.types";
import {
  Briefcase,
  Upload,
  RefreshCw,
  Clock,
  GraduationCap,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export const JobManagementView: React.FC = () => {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const loadJobs = async () => {
    setIsLoading(true);
    try {
      const data = await fetchJobs();
      setJobs(data);
    } catch (err: any) {
      console.error("Failed to load jobs", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    for (let i = 0; i < e.target.files.length; i++) {
      formData.append("files", e.target.files[i]);
    }

    try {
      const result = await uploadJobs(formData);
      setUploadSuccess(`Successfully ingested ${result.length} Job Description(s).`);
      await loadJobs();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload job descriptions");
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Upload Section */}
      <div className="flex flex-col gap-4 rounded-xl border border-gray-200 bg-white p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Job Description Management</h2>
          <p className="text-xs text-gray-500">
            Upload and manage role profiles evaluated across the candidate pool.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50">
            <Upload className="h-4 w-4" />
            <span>{isUploading ? "Ingesting..." : "Upload JDs (PDF/DOCX)"}</span>
            <input
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
            />
          </label>
          <button
            onClick={loadJobs}
            title="Refresh jobs"
            className="rounded-lg border border-gray-200 p-2 text-gray-600 hover:bg-gray-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {uploadSuccess && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-xs font-medium text-emerald-800">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          {uploadSuccess}
        </div>
      )}

      {uploadError && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800">
          <AlertCircle className="h-4 w-4 text-rose-600" />
          {uploadError}
        </div>
      )}

      {/* Jobs Grid */}
      {isLoading ? (
        <div className="flex h-48 items-center justify-center text-xs text-gray-500">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-blue-600" />
          Loading Job Descriptions...
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
          <Briefcase className="mx-auto h-10 w-10 text-gray-300" />
          <h3 className="mt-3 text-sm font-semibold text-gray-900">No Job Descriptions</h3>
          <p className="mt-1 text-xs text-gray-500">Upload PDF or DOCX job descriptions to begin.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-gray-900">{job.structured_profile.title}</h3>
                    <span className="text-xs text-gray-400">
                      {job.structured_profile.department || "General"}
                    </span>
                  </div>
                  <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
                    Active
                  </span>
                </div>

                <p className="line-clamp-2 text-xs text-gray-600">
                  {job.structured_profile.summary || "Structured Job Profile"}
                </p>

                <div className="flex flex-wrap gap-2 text-[11px] text-gray-500">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5 text-gray-400" />
                    <span>Min {job.structured_profile.min_experience_years} yrs</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <GraduationCap className="h-3.5 w-3.5 text-gray-400" />
                    <span>{job.structured_profile.required_qualification}</span>
                  </div>
                </div>

                {/* Required Skills */}
                <div className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                    Required Skills
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {job.structured_profile.required_skills.slice(0, 5).map((s) => (
                      <span
                        key={s}
                        className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-700"
                      >
                        {s}
                      </span>
                    ))}
                    {job.structured_profile.required_skills.length > 5 && (
                      <span className="rounded bg-slate-50 px-1 py-0.5 text-[10px] text-gray-400">
                        +{job.structured_profile.required_skills.length - 5}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-4 border-t pt-3 text-[10px] text-gray-400">
                Created: {new Date(job.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
