import React, { useEffect, useState } from "react";
import { fetchCandidates, uploadCandidates } from "@/lib/api-client";
import { CandidateResponse } from "@/types/candidate.types";
import {
  Users,
  Upload,
  Search,
  RefreshCw,
  Mail,
  Phone,
  CheckCircle2,
  AlertCircle,
  X,
} from "lucide-react";

export const CandidatePoolView: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateResponse | null>(null);

  const loadCandidates = async (query?: string) => {
    setIsLoading(true);
    try {
      const data = await fetchCandidates(query);
      setCandidates(data);
    } catch (err: any) {
      console.error("Failed to load candidates", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadCandidates(searchQuery);
  };

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
      const result = await uploadCandidates(formData);
      setUploadSuccess(`Successfully ingested ${result.length} Candidate Resume(s).`);
      await loadCandidates();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload resumes");
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
          <h2 className="text-lg font-bold text-gray-900">Candidate Pool Management</h2>
          <p className="text-xs text-gray-500">
            Canonical candidate profiles indexed in FAISS for multi-role evaluation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50">
            <Upload className="h-4 w-4" />
            <span>{isUploading ? "Ingesting..." : "Bulk Upload Resumes (PDF/DOCX)"}</span>
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
            onClick={() => loadCandidates(searchQuery)}
            title="Refresh candidate pool"
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

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search candidates by name or skill (e.g. Python, Docker, React)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-4 text-xs text-gray-800 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="rounded-lg bg-gray-900 px-4 py-2 text-xs font-semibold text-white hover:bg-gray-800"
        >
          Search
        </button>
      </form>

      {/* Candidates Table */}
      {isLoading ? (
        <div className="flex h-48 items-center justify-center text-xs text-gray-500">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-blue-600" />
          Loading Candidate Pool...
        </div>
      ) : candidates.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
          <Users className="mx-auto h-10 w-10 text-gray-300" />
          <h3 className="mt-3 text-sm font-semibold text-gray-900">No Candidates Found</h3>
          <p className="mt-1 text-xs text-gray-500">
            {searchQuery ? "No matches for your search query." : "Upload resumes to populate the candidate pool."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b bg-gray-50/70 font-semibold text-gray-600">
                <th className="p-3.5 pl-6">Candidate Name</th>
                <th className="p-3.5">Verified Experience</th>
                <th className="p-3.5">Highest Qualification</th>
                <th className="p-3.5">Key Skills</th>
                <th className="p-3.5">FAISS Status</th>
                <th className="p-3.5 pr-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {candidates.map((cand) => (
                <tr key={cand.id} className="hover:bg-slate-50/50">
                  <td className="p-3.5 pl-6 font-semibold text-gray-900">
                    <div>{cand.structured_profile.full_name}</div>
                    <div className="text-[11px] font-normal text-gray-400">{cand.file_name}</div>
                  </td>
                  <td className="p-3.5">
                    <span className="font-medium text-gray-900">
                      {cand.structured_profile.total_experience_years} yrs
                    </span>
                  </td>
                  <td className="p-3.5">
                    <span className="rounded bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-700">
                      {cand.structured_profile.highest_qualification}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <div className="flex max-w-xs flex-wrap gap-1">
                      {cand.structured_profile.skills.slice(0, 4).map((s) => (
                        <span
                          key={s}
                          className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-700"
                        >
                          {s}
                        </span>
                      ))}
                      {cand.structured_profile.skills.length > 4 && (
                        <span className="text-[10px] text-gray-400">
                          +{cand.structured_profile.skills.length - 4}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="p-3.5">
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Indexed
                    </span>
                  </td>
                  <td className="p-3.5 pr-6 text-right">
                    <button
                      onClick={() => setSelectedCandidate(cand)}
                      className="rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                    >
                      View Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Candidate Profile Slide-Out Drawer */}
      {selectedCandidate && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm">
          <div className="h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h3 className="text-base font-bold text-gray-900">
                  {selectedCandidate.structured_profile.full_name}
                </h3>
                <p className="text-xs text-gray-400">{selectedCandidate.file_name}</p>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-6 space-y-6 text-xs text-gray-700">
              {/* Contact info */}
              <div className="space-y-1">
                {selectedCandidate.structured_profile.email && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Mail className="h-3.5 w-3.5 text-gray-400" />
                    <span>{selectedCandidate.structured_profile.email}</span>
                  </div>
                )}
                {selectedCandidate.structured_profile.phone && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Phone className="h-3.5 w-3.5 text-gray-400" />
                    <span>{selectedCandidate.structured_profile.phone}</span>
                  </div>
                )}
              </div>

              {/* Skills */}
              <div className="space-y-2">
                <h4 className="font-bold uppercase tracking-wider text-gray-400">Canonical Skills</h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCandidate.structured_profile.skills.map((s) => (
                    <span
                      key={s}
                      className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-800"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Work Experience Timeline */}
              <div className="space-y-3">
                <h4 className="font-bold uppercase tracking-wider text-gray-400">
                  Verified Career History ({selectedCandidate.structured_profile.total_experience_years} yrs total)
                </h4>
                {selectedCandidate.structured_profile.experience_history.map((exp, idx) => (
                  <div key={idx} className="rounded-lg border border-gray-100 bg-gray-50/50 p-3">
                    <div className="font-bold text-gray-900">{exp.title}</div>
                    <div className="text-[11px] text-gray-500">{exp.organization || "Company"} • {exp.duration_years} yrs</div>
                    {exp.summary && <p className="mt-1 text-[11px] text-gray-600">{exp.summary}</p>}
                  </div>
                ))}
              </div>

              {/* Education */}
              <div className="space-y-2">
                <h4 className="font-bold uppercase tracking-wider text-gray-400">Education</h4>
                {selectedCandidate.structured_profile.education.map((edu, idx) => (
                  <div key={idx} className="rounded-lg border border-gray-100 bg-gray-50/50 p-3">
                    <div className="font-bold text-gray-900">{edu.degree} {edu.field ? `in ${edu.field}` : ""}</div>
                    <div className="text-[11px] text-gray-500">{edu.institution || "University"} {edu.graduation_year ? `(${edu.graduation_year})` : ""}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
