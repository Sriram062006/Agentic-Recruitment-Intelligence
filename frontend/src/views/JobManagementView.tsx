import React, { useEffect, useState } from "react";
import {
  fetchJobs,
  uploadJobs,
  downloadJobFile,
  openJobFileInNewTab,
} from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { JobResponse } from "@/types/job.types";
import {
  Briefcase,
  Upload,
  RefreshCw,
  Clock,
  GraduationCap,
  AlertCircle,
  CheckCircle2,
  Eye,
  Download,
  FileText,
  X,
  ListChecks,
  Sparkles,
  ChevronDown,
  ChevronUp,
  MapPin,
  Globe,
  Calendar,
  Layers,
  ShieldCheck,
} from "lucide-react";

export const JobManagementView: React.FC = () => {
  const { isViewer } = useAuth();
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobResponse | null>(null);
  const [showRawText, setShowRawText] = useState<boolean>(false);

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
          {isViewer ? (
            <div className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2 text-xs font-semibold text-amber-800">
              <Eye className="h-4 w-4 text-amber-600" />
              <span>Read-Only Viewer</span>
            </div>
          ) : (
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
          )}
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
                    Required Skills ({job.structured_profile.required_skills.length})
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

              <div className="mt-4 border-t pt-3 flex items-center justify-between text-[11px] text-gray-400">
                <span>Created: {new Date(job.created_at).toLocaleDateString()}</span>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => openJobFileInNewTab(job.id)}
                    title="View original JD document"
                    className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600"
                  >
                    <FileText className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedJob(job);
                      setShowRawText(false);
                    }}
                    className="rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-300"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Full Job Description Modal */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fade-in">
          <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl sm:p-8">
            <div className="flex items-start justify-between border-b pb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">{selectedJob.structured_profile.title}</h3>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-gray-600">
                  <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">{selectedJob.structured_profile.department || "General"}</span>
                  {selectedJob.structured_profile.company_or_client && (
                    <span className="font-semibold text-gray-800 bg-gray-100 px-2 py-0.5 rounded">{selectedJob.structured_profile.company_or_client}</span>
                  )}
                  {selectedJob.structured_profile.location && (
                    <span className="inline-flex items-center gap-1 text-gray-600">
                      <MapPin className="h-3 w-3 text-gray-400" />
                      <span>{selectedJob.structured_profile.location}</span>
                    </span>
                  )}
                  {selectedJob.structured_profile.remote_work && (
                    <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                      <Globe className="h-3 w-3 text-emerald-500" />
                      <span>{selectedJob.structured_profile.remote_work}</span>
                    </span>
                  )}
                  <span className="text-gray-400">•</span>
                  <span>Min {selectedJob.structured_profile.min_experience_years} yrs</span>
                  <span className="text-gray-400">•</span>
                  <span>{selectedJob.structured_profile.required_qualification}</span>
                  <span className="inline-flex items-center gap-1 text-blue-700 bg-blue-50 px-2 py-0.5 rounded text-[11px] font-semibold">
                    <ShieldCheck className="h-3 w-3 text-blue-600" />
                    <span>Source Verified</span>
                  </span>
                </div>

                {/* Additional Metadata Strip */}
                {(selectedJob.structured_profile.start_date || selectedJob.structured_profile.languages?.length || selectedJob.structured_profile.work_regime) && (
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-gray-500">
                    {selectedJob.structured_profile.start_date && (
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="h-3 w-3 text-gray-400" />
                        <span>Period: {selectedJob.structured_profile.start_date} {selectedJob.structured_profile.end_date ? `to ${selectedJob.structured_profile.end_date}` : ""}</span>
                      </span>
                    )}
                    {selectedJob.structured_profile.work_regime && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-700">
                        {selectedJob.structured_profile.work_regime}
                      </span>
                    )}
                    {selectedJob.structured_profile.languages && selectedJob.structured_profile.languages.length > 0 && (
                      <span className="inline-flex items-center gap-1 text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                        <span>Languages: {selectedJob.structured_profile.languages.join(", ")}</span>
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => openJobFileInNewTab(selectedJob.id)}
                  className="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 shadow-xs"
                >
                  <Eye className="h-3.5 w-3.5 text-gray-500" />
                  <span>View File</span>
                </button>
                <button
                  onClick={() => downloadJobFile(selectedJob.id, `${selectedJob.title}.pdf`)}
                  className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 shadow-xs"
                >
                  <Download className="h-3.5 w-3.5 text-blue-600" />
                  <span>Download JD</span>
                </button>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="mt-5 space-y-5 text-xs text-gray-700">
              {/* Executive Overview */}
              <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-4 space-y-1.5">
                <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-blue-800 text-[11px]">
                  <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                  <span>Role Overview & Context</span>
                </div>
                <p className="leading-relaxed text-gray-700">
                  {selectedJob.structured_profile.summary}
                </p>
              </div>

              {/* Key Responsibilities */}
              {selectedJob.structured_profile.key_responsibilities &&
                selectedJob.structured_profile.key_responsibilities.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-indigo-700 text-[11px]">
                      <ListChecks className="h-3.5 w-3.5 text-indigo-600" />
                      <span>Key Responsibilities ({selectedJob.structured_profile.key_responsibilities.length})</span>
                    </div>
                    <ul className="space-y-1.5 rounded-xl border border-indigo-100 bg-indigo-50/20 p-4 list-disc pl-6 text-gray-700">
                      {selectedJob.structured_profile.key_responsibilities.map((resp, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {resp}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Must-Have Requirements */}
              {selectedJob.structured_profile.must_have_requirements &&
                selectedJob.structured_profile.must_have_requirements.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-emerald-800 text-[11px]">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                      <span>Must-Have Mandatory Requirements ({selectedJob.structured_profile.must_have_requirements.length})</span>
                    </div>
                    <ul className="space-y-1.5 rounded-xl border border-emerald-100 bg-emerald-50/20 p-4 list-disc pl-6 text-gray-700">
                      {selectedJob.structured_profile.must_have_requirements.map((req, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {req}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Should-Have Requirements */}
              {selectedJob.structured_profile.should_have_requirements &&
                selectedJob.structured_profile.should_have_requirements.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-amber-800 text-[11px]">
                      <Layers className="h-3.5 w-3.5 text-amber-600" />
                      <span>Should-Have / Desired Requirements ({selectedJob.structured_profile.should_have_requirements.length})</span>
                    </div>
                    <ul className="space-y-1.5 rounded-xl border border-amber-100 bg-amber-50/20 p-4 list-disc pl-6 text-gray-700">
                      {selectedJob.structured_profile.should_have_requirements.map((req, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {req}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Required Skills */}
              <div className="space-y-2">
                <div className="font-bold uppercase tracking-wider text-gray-500 text-[11px]">
                  Must-Have Required Skills ({selectedJob.structured_profile.required_skills.length})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {selectedJob.structured_profile.required_skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-md bg-blue-50 border border-blue-100 px-2.5 py-1 text-xs font-semibold text-blue-800"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Preferred Skills */}
              {selectedJob.structured_profile.preferred_skills &&
                selectedJob.structured_profile.preferred_skills.length > 0 && (
                  <div className="space-y-2">
                    <div className="font-bold uppercase tracking-wider text-gray-500 text-[11px]">
                      Preferred / Nice-to-Have Skills ({selectedJob.structured_profile.preferred_skills.length})
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedJob.structured_profile.preferred_skills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-md bg-emerald-50 border border-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              {/* Tools & Methodologies */}
              {(selectedJob.structured_profile.tools?.length || selectedJob.structured_profile.methodologies?.length) && (
                <div className="grid gap-3 sm:grid-cols-2">
                  {selectedJob.structured_profile.tools && selectedJob.structured_profile.tools.length > 0 && (
                    <div className="space-y-1.5 rounded-lg border border-gray-100 bg-gray-50/50 p-3">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                        Tools & Technologies ({selectedJob.structured_profile.tools.length})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {selectedJob.structured_profile.tools.map((t) => (
                          <span key={t} className="rounded bg-white border border-gray-200 px-1.5 py-0.5 text-[11px] font-medium text-gray-700">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedJob.structured_profile.methodologies && selectedJob.structured_profile.methodologies.length > 0 && (
                    <div className="space-y-1.5 rounded-lg border border-gray-100 bg-gray-50/50 p-3">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                        Delivery Methodologies ({selectedJob.structured_profile.methodologies.length})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {selectedJob.structured_profile.methodologies.map((m) => (
                          <span key={m} className="rounded bg-white border border-gray-200 px-1.5 py-0.5 text-[11px] font-medium text-gray-700">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Raw JD Text Toggle */}
              <div className="border-t pt-4 space-y-2">
                <button
                  onClick={() => setShowRawText(!showRawText)}
                  className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-100"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span>Raw Document Content</span>
                  </div>
                  {showRawText ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {showRawText && (
                  <div className="rounded-lg border border-gray-200 bg-gray-900 p-4 text-[11px] font-mono text-gray-200 max-h-60 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {selectedJob.raw_content}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
