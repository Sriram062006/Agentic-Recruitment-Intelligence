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
  MapPin,
  Briefcase,
  GraduationCap,
  Award,
  FolderGit2,
  Globe,
  FileText,
  ChevronDown,
  ChevronUp,
  Layers,
  Sparkles,
} from "lucide-react";

export const CandidatePoolView: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateResponse | null>(null);
  const [showRawText, setShowRawText] = useState<boolean>(false);

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
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const formData = new FormData();
      Array.from(files).forEach((file) => formData.append("files", file));
      const res = await uploadCandidates(formData);
      setUploadSuccess(`Successfully ingested and indexed ${res.length} candidate(s).`);
      loadCandidates();
    } catch (err: any) {
      setUploadError(err.message || "Upload and ingestion failed.");
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-gray-900">Candidate Pool</h2>
          <p className="text-sm text-gray-500">
            Canonical candidate repository. Profiles are extracted, structured, and indexed in FAISS for multi-role evaluation.
          </p>
        </div>

        {/* Upload Button */}
        <div>
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700">
            <Upload className="h-4 w-4" />
            <span>Upload Resumes</span>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.doc"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Alerts */}
      {uploadError && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}
      {uploadSuccess && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* Controls & Search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <form onSubmit={handleSearch} className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by candidate name or skill..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-9 pr-4 text-xs text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </form>

        <button
          onClick={() => loadCandidates()}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Candidates Table */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-gray-200">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading candidates...
          </div>
        </div>
      ) : candidates.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center">
          <Users className="h-10 w-10 text-gray-300" />
          <h3 className="mt-3 text-sm font-semibold text-gray-900">No candidates in pool</h3>
          <p className="mt-1 text-xs text-gray-500">
            Upload PDF or DOCX candidate resumes to begin multi-role fitment analysis.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="border-b border-gray-200 bg-gray-50 text-[11px] font-bold uppercase tracking-wider text-gray-500">
              <tr>
                <th className="p-3.5 pl-6">Candidate</th>
                <th className="p-3.5">Experience</th>
                <th className="p-3.5">Qualification</th>
                <th className="p-3.5">Top Skills</th>
                <th className="p-3.5">Vector Status</th>
                <th className="p-3.5 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {candidates.map((cand) => (
                <tr key={cand.id} className="hover:bg-gray-50/70 transition-colors">
                  <td className="p-3.5 pl-6">
                    <div className="font-bold text-gray-900">{cand.structured_profile.full_name}</div>
                    <div className="text-[11px] text-gray-400 truncate max-w-xs">{cand.file_name}</div>
                  </td>
                  <td className="p-3.5 font-semibold text-gray-800">
                    {cand.structured_profile.total_experience_years} yrs
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
                      onClick={() => {
                        setSelectedCandidate(cand);
                        setShowRawText(false);
                      }}
                      className="rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-300"
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
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm animate-fade-in">
          <div className="h-full w-full max-w-2xl overflow-y-auto bg-white p-6 sm:p-8 shadow-2xl">
            {/* Header */}
            <div className="flex items-start justify-between border-b pb-5">
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  {selectedCandidate.structured_profile.full_name}
                </h3>
                <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                  <span className="font-mono text-gray-400">{selectedCandidate.file_name}</span>
                  <span>•</span>
                  <span>SHA: {selectedCandidate.file_hash.substring(0, 12)}...</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-6 space-y-6 text-xs text-gray-700">
              {/* 1. Candidate Overview Card */}
              <div className="rounded-xl border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200/60 pb-3">
                  <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
                    {selectedCandidate.structured_profile.email && (
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3.5 w-3.5 text-blue-600" />
                        <span>{selectedCandidate.structured_profile.email}</span>
                      </div>
                    )}
                    {selectedCandidate.structured_profile.phone && (
                      <div className="flex items-center gap-1.5">
                        <Phone className="h-3.5 w-3.5 text-emerald-600" />
                        <span>{selectedCandidate.structured_profile.phone}</span>
                      </div>
                    )}
                    {selectedCandidate.structured_profile.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-rose-500" />
                        <span>{selectedCandidate.structured_profile.location}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-center">
                  <div className="rounded-lg bg-white p-2.5 border border-gray-100">
                    <div className="text-[10px] uppercase font-bold text-gray-400">Total Experience</div>
                    <div className="text-sm font-bold text-gray-900 mt-0.5">
                      {selectedCandidate.structured_profile.total_experience_years} yrs
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-2.5 border border-gray-100">
                    <div className="text-[10px] uppercase font-bold text-gray-400">Highest Degree</div>
                    <div className="text-sm font-bold text-gray-900 mt-0.5">
                      {selectedCandidate.structured_profile.highest_qualification}
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-2.5 border border-gray-100">
                    <div className="text-[10px] uppercase font-bold text-gray-400">Verified Skills</div>
                    <div className="text-sm font-bold text-blue-700 mt-0.5">
                      {selectedCandidate.structured_profile.skills.length} skills
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-2.5 border border-gray-100">
                    <div className="text-[10px] uppercase font-bold text-gray-400">FAISS Vector</div>
                    <div className="text-sm font-bold text-emerald-600 mt-0.5 flex items-center justify-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Indexed
                    </div>
                  </div>
                </div>
              </div>

              {/* 2. Professional Summary */}
              {(selectedCandidate.structured_profile.professional_summary || selectedCandidate.structured_profile.summary) && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-500">
                    <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                    <span>Professional Executive Summary</span>
                  </div>
                  <div className="rounded-lg border border-blue-100 bg-blue-50/40 p-3.5 text-gray-700 leading-relaxed">
                    {selectedCandidate.structured_profile.professional_summary || selectedCandidate.structured_profile.summary}
                  </div>
                </div>
              )}

              {/* 3. Canonical Skills */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold uppercase tracking-wider text-gray-500">
                    Canonical Skills ({selectedCandidate.structured_profile.skills.length})
                  </h4>
                </div>

                {/* Categorized Skills if available */}
                {selectedCandidate.structured_profile.skills_by_category &&
                Object.keys(selectedCandidate.structured_profile.skills_by_category).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(selectedCandidate.structured_profile.skills_by_category).map(([category, catSkills]) => (
                      <div key={category} className="space-y-1.5">
                        <div className="text-[11px] font-semibold text-gray-500 flex items-center gap-1">
                          <Layers className="h-3 w-3 text-gray-400" />
                          {category}
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {catSkills.map((s) => (
                            <span
                              key={s}
                              className="rounded-md bg-blue-50 border border-blue-100 px-2.5 py-1 text-xs font-medium text-blue-800"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCandidate.structured_profile.skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-md bg-blue-50 border border-blue-100 px-2.5 py-1 text-xs font-medium text-blue-800"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 4. Verified Work Experience */}
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-500">
                  <Briefcase className="h-3.5 w-3.5 text-gray-500" />
                  <span>Verified Career History ({selectedCandidate.structured_profile.experience_history.length} roles)</span>
                </div>

                {selectedCandidate.structured_profile.experience_history.length === 0 ? (
                  <div className="text-gray-400 italic">No explicit tenure entries found.</div>
                ) : (
                  <div className="space-y-3">
                    {selectedCandidate.structured_profile.experience_history.map((exp, idx) => (
                      <div key={idx} className="rounded-xl border border-gray-200 bg-white p-4 space-y-2 shadow-xs">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <div className="font-bold text-sm text-gray-900">{exp.title}</div>
                            <div className="text-xs text-gray-600 font-medium mt-0.5">
                              {exp.organization || "Organization"} {exp.location ? `• ${exp.location}` : ""}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {(exp.start_date || exp.end_date) && (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
                                {exp.start_date || ""} - {exp.end_date || "Present"}
                              </span>
                            )}
                            <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-[10px] font-bold text-blue-700">
                              {exp.duration_years} yrs
                            </span>
                          </div>
                        </div>

                        {/* Responsibilities list */}
                        {exp.responsibilities && exp.responsibilities.length > 0 ? (
                          <ul className="mt-2 space-y-1 pl-4 list-disc text-gray-700 text-xs">
                            {exp.responsibilities.map((resp, rIdx) => (
                              <li key={rIdx} className="leading-relaxed">
                                {resp}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          exp.summary && <p className="mt-1.5 text-xs text-gray-600">{exp.summary}</p>
                        )}

                        {/* Tech tags */}
                        {exp.technologies && exp.technologies.length > 0 && (
                          <div className="mt-2.5 pt-2 border-t border-gray-100 flex flex-wrap items-center gap-1.5">
                            <span className="text-[10px] font-bold uppercase text-gray-400">Tech:</span>
                            {exp.technologies.map((t, tIdx) => (
                              <span
                                key={tIdx}
                                className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 5. Education */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-500">
                  <GraduationCap className="h-3.5 w-3.5 text-gray-500" />
                  <span>Education & Qualifications</span>
                </div>

                {selectedCandidate.structured_profile.education.length === 0 ? (
                  <div className="rounded-lg border border-gray-100 bg-gray-50/50 p-3 text-gray-500 italic">
                    No academic degrees specified in resume. Candidate evaluated via professional experience.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedCandidate.structured_profile.education.map((edu, idx) => (
                      <div key={idx} className="rounded-lg border border-gray-200 bg-white p-3 flex justify-between items-center">
                        <div>
                          <div className="font-bold text-gray-900">{edu.degree}</div>
                          <div className="text-xs text-gray-500 mt-0.5">
                            {edu.institution || "Higher Education Institution"} {edu.field ? `• ${edu.field}` : ""}
                          </div>
                        </div>
                        {edu.graduation_year && (
                          <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700">
                            {edu.graduation_year}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 6. Certifications */}
              {selectedCandidate.structured_profile.certifications &&
                selectedCandidate.structured_profile.certifications.length > 0 && (
                  <div className="space-y-2.5">
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-500">
                      <Award className="h-3.5 w-3.5 text-amber-600" />
                      <span>Certifications & Accreditations</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {selectedCandidate.structured_profile.certifications.map((cert, idx) => (
                        <div key={idx} className="rounded-lg border border-amber-200/60 bg-amber-50/30 p-2.5">
                          <div className="font-bold text-gray-900">{cert.name}</div>
                          <div className="text-[11px] text-gray-500 mt-0.5">
                            {cert.issuing_organization || "Accredited Body"} {cert.year ? `• ${cert.year}` : ""}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* 7. Projects */}
              {selectedCandidate.structured_profile.projects &&
                selectedCandidate.structured_profile.projects.length > 0 && (
                  <div className="space-y-2.5">
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-500">
                      <FolderGit2 className="h-3.5 w-3.5 text-indigo-600" />
                      <span>Notable Projects & Research</span>
                    </div>
                    <div className="space-y-2">
                      {selectedCandidate.structured_profile.projects.map((proj, idx) => (
                        <div key={idx} className="rounded-lg border border-gray-200 bg-white p-3 space-y-1.5">
                          <div className="font-bold text-gray-900">{proj.name}</div>
                          {proj.description && <p className="text-gray-600 leading-relaxed">{proj.description}</p>}
                          {proj.technologies && proj.technologies.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {proj.technologies.map((t, tIdx) => (
                                <span
                                  key={tIdx}
                                  className="rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-medium text-indigo-700"
                                >
                                  {t}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* 8. Languages & Domains */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {selectedCandidate.structured_profile.languages &&
                  selectedCandidate.structured_profile.languages.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-1 font-bold uppercase tracking-wider text-gray-400">
                        <Globe className="h-3 w-3" />
                        <span>Languages</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedCandidate.structured_profile.languages.map((lang) => (
                          <span
                            key={lang}
                            className="rounded bg-emerald-50 border border-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-800"
                          >
                            {lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                {selectedCandidate.structured_profile.domains &&
                  selectedCandidate.structured_profile.domains.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-1 font-bold uppercase tracking-wider text-gray-400">
                        <Layers className="h-3 w-3" />
                        <span>Industry Domains</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedCandidate.structured_profile.domains.map((dom) => (
                          <span
                            key={dom}
                            className="rounded bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-700"
                          >
                            {dom}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </div>

              {/* 9. Source Document Details & Raw Text Preview */}
              <div className="border-t pt-4 space-y-2">
                <button
                  onClick={() => setShowRawText(!showRawText)}
                  className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-100"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span>Source Document & Extracted Text</span>
                  </div>
                  {showRawText ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {showRawText && (
                  <div className="rounded-lg border border-gray-200 bg-gray-900 p-4 text-[11px] font-mono text-gray-200 max-h-60 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {selectedCandidate.raw_text}
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
