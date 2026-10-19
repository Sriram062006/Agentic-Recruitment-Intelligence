import React, { useState } from "react";
import { ExplainabilityPayload } from "@/types/evaluation.types";
import { getCandidateFileUrl, getJobFileUrl } from "@/lib/api-client";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Briefcase,
  GraduationCap,
  Sparkles,
  FileText,
  ExternalLink,
  ShieldCheck,
  Cpu,
  BadgeCheck,
} from "lucide-react";

interface FitmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidateId?: string;
  jobId?: string;
  candidateName: string;
  jobTitle: string;
  compositeScore: number;
  rankInRole?: number;
  data: ExplainabilityPayload | null;
  loading: boolean;
}

export const FitmentModal: React.FC<FitmentModalProps> = ({
  isOpen,
  onClose,
  candidateId,
  jobId,
  candidateName,
  jobTitle,
  compositeScore,
  rankInRole,
  data,
  loading,
}) => {
  if (!isOpen) return null;

  const [openingDoc, setOpeningDoc] = useState<string | null>(null);

  // Determine 0-100 Score
  const scoreVal =
    data?.fitment_score ??
    (compositeScore <= 1.0 ? Math.round(compositeScore * 100) : Math.round(compositeScore));

  const scoreColor =
    scoreVal >= 85
      ? "text-emerald-700 bg-emerald-50 border-emerald-200"
      : scoreVal >= 70
      ? "text-blue-700 bg-blue-50 border-blue-200"
      : scoreVal >= 55
      ? "text-indigo-700 bg-indigo-50 border-indigo-200"
      : scoreVal >= 40
      ? "text-amber-700 bg-amber-50 border-amber-200"
      : "text-rose-700 bg-rose-50 border-rose-200";

  const handleOpenCandidateCv = async () => {
    if (!candidateId) return;
    try {
      setOpeningDoc("cv");
      const url = await getCandidateFileUrl(candidateId);
      window.open(url, "_blank");
    } catch (e) {
      console.error("Failed to open candidate CV file:", e);
    } finally {
      setOpeningDoc(null);
    }
  };

  const handleOpenJobDescription = async () => {
    if (!jobId) return;
    try {
      setOpeningDoc("jd");
      const url = await getJobFileUrl(jobId);
      window.open(url, "_blank");
    } catch (e) {
      console.error("Failed to open job description file:", e);
    } finally {
      setOpeningDoc(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex flex-col gap-4 border-b border-gray-100 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
                AI Fitment Evaluation Report
              </span>
              {rankInRole && (
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                  Role Rank #{rankInRole}
                </span>
              )}
              {data?.fitment_category && (
                <span className="rounded-full bg-slate-900 px-2.5 py-0.5 text-xs font-bold text-white uppercase tracking-wider">
                  {data.fitment_category.replace(/_/g, " ")}
                </span>
              )}
              {data?.recruiter_recommendation && (
                <span
                  className={`rounded-full px-3 py-0.5 text-xs font-bold uppercase tracking-wider ${
                    data.recruiter_recommendation.includes("STRONGLY") || data.recruiter_recommendation.includes("STRONG")
                      ? "border border-emerald-300 bg-emerald-100 text-emerald-800"
                      : data.recruiter_recommendation.includes("RECOMMEND")
                      ? "border border-blue-300 bg-blue-100 text-blue-800"
                      : data.recruiter_recommendation.includes("CONSIDER") || data.recruiter_recommendation.includes("PARTIAL")
                      ? "border border-amber-300 bg-amber-100 text-amber-800"
                      : "border border-rose-300 bg-rose-100 text-rose-800"
                  }`}
                >
                  {data.recruiter_recommendation.replace(/_/g, " ")}
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-gray-900">{candidateName}</h2>
            <p className="text-sm text-gray-500">
              Evaluated against: <span className="font-semibold text-gray-800">{jobTitle}</span>
            </p>

            {/* Direct Document Viewing Buttons */}
            <div className="flex flex-wrap items-center gap-2 pt-2">
              {candidateId && (
                <button
                  onClick={handleOpenCandidateCv}
                  disabled={openingDoc === "cv"}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700 transition hover:bg-blue-100 disabled:opacity-50"
                  title="View original uploaded resume file in storage"
                >
                  <FileText className="h-3.5 w-3.5 text-blue-600" />
                  <span>{openingDoc === "cv" ? "Opening CV..." : "View Original CV"}</span>
                  <ExternalLink className="h-3 w-3 opacity-60" />
                </button>
              )}
              {jobId && (
                <button
                  onClick={handleOpenJobDescription}
                  disabled={openingDoc === "jd"}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 transition hover:bg-indigo-100 disabled:opacity-50"
                  title="View original uploaded job description document"
                >
                  <Briefcase className="h-3.5 w-3.5 text-indigo-600" />
                  <span>{openingDoc === "jd" ? "Opening JD..." : "View Original Job Description"}</span>
                  <ExternalLink className="h-3 w-3 opacity-60" />
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className={`rounded-xl border px-5 py-2.5 text-center shadow-xs ${scoreColor}`}>
              <div className="text-3xl font-black">{scoreVal}<span className="text-lg font-bold">/100</span></div>
              <div className="text-[10px] font-bold uppercase tracking-wider">AI Fitment Score</div>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex h-64 items-center justify-center space-x-2 text-gray-500">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
              <span>Synthesizing grounded evidence & AI assessment...</span>
            </div>
          ) : !data ? (
            <div className="py-12 text-center text-gray-500">No explanation payload available.</div>
          ) : (
            <div className="space-y-6">
              {/* AI Model Metadata Pill & Confidence */}
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-purple-600" />
                  <span>
                    Model: <strong className="text-gray-800">{data.model_metadata?.provider || "Google Gemini"}</strong> ({data.model_metadata?.model || "gemini-2.5-flash"})
                  </span>
                  <span className="text-gray-300">•</span>
                  <span>Version: <strong>{data.model_metadata?.prompt_version || "v2.0-evidence-grounded"}</strong></span>
                </div>
                {data.confidence && (
                  <div className="flex items-center gap-1 font-semibold text-emerald-700">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    <span>Evaluation Confidence: {Math.round(data.confidence * 100)}%</span>
                  </div>
                )}
              </div>

              {/* Recommendation Rationale */}
              <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-5">
                <div className="mb-2 flex items-center gap-2 text-sm font-bold text-blue-900">
                  <Sparkles className="h-4 w-4 text-blue-600" />
                  AI Fitment Assessment & Recommendation
                </div>
                <p className="text-sm leading-relaxed text-blue-950">
                  {data.recommendation_rationale}
                </p>
              </div>

              {/* Requirement-by-Requirement Coverage & Post-LLM Evidence Validation */}
              {data.requirement_analysis && data.requirement_analysis.length > 0 && (
                <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-bold text-gray-900">
                      <Briefcase className="h-4 w-4 text-indigo-600" />
                      Requirement-by-Requirement Grounded Audit & Evidence Validation
                    </div>
                    <span className="text-xs font-semibold text-gray-500">
                      {data.requirement_analysis.filter((r) => r.status === "MATCHED").length} of{" "}
                      {data.requirement_analysis.length} Satisfied
                    </span>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-gray-100">
                    <table className="w-full text-left text-xs">
                      <thead className="border-b border-gray-100 bg-gray-50 font-semibold text-gray-600">
                        <tr>
                          <th className="p-2.5">Requirement Criteria</th>
                          <th className="w-24 p-2.5">Type</th>
                          <th className="w-28 p-2.5 text-center">Match Status</th>
                          <th className="w-28 p-2.5 text-center">Validation</th>
                          <th className="p-2.5">Cited Source Evidence</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {data.requirement_analysis.map((req, idx) => (
                          <tr key={idx} className="transition hover:bg-slate-50/70">
                            <td className="p-2.5 font-medium leading-snug text-gray-800">
                              {req.requirement}
                            </td>
                            <td className="p-2.5">
                              <span
                                className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                                  req.type === "MUST_HAVE"
                                    ? "border border-red-200 bg-red-50 text-red-700"
                                    : "border border-blue-200 bg-blue-50 text-blue-700"
                                }`}
                              >
                                {req.type === "MUST_HAVE" ? "Must-Have" : "Should-Have"}
                              </span>
                            </td>
                            <td className="p-2.5 text-center">
                              <span
                                className={`inline-block rounded px-2 py-0.5 text-[10px] font-bold ${
                                  req.status === "MATCHED"
                                    ? "bg-emerald-100 text-emerald-800"
                                    : req.status === "PARTIALLY MATCHED" || req.status === "PARTIALLY_MATCHED"
                                    ? "bg-amber-100 text-amber-800"
                                    : "bg-rose-100 text-rose-800"
                                }`}
                              >
                                {req.status.replace(/_/g, " ")}
                              </span>
                            </td>
                            <td className="p-2.5 text-center">
                              {req.validation_status === "VERIFIED" ? (
                                <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                                  <BadgeCheck className="h-3 w-3 text-emerald-600" />
                                  Verified
                                </span>
                              ) : req.validation_status === "PARTIALLY_VERIFIED" ? (
                                <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700 border border-amber-200">
                                  <AlertTriangle className="h-3 w-3 text-amber-600" />
                                  Partial
                                </span>
                              ) : req.validation_status === "UNSUPPORTED" ? (
                                <span className="inline-flex items-center gap-1 rounded bg-rose-50 px-2 py-0.5 text-[10px] font-bold text-rose-700 border border-rose-200">
                                  <AlertCircle className="h-3 w-3 text-rose-600" />
                                  Unsupported
                                </span>
                              ) : (
                                <span className="text-[10px] text-gray-400">N/A</span>
                              )}
                            </td>
                            <td className="bg-slate-50/40 p-2.5 text-[11px] italic leading-relaxed text-gray-600">
                              "{req.evidence}"
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Skills Analysis */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs font-bold text-emerald-800">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    Matched Required Skills ({data.matched_skills.length})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.matched_skills.length > 0 ? (
                      data.matched_skills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-md border border-emerald-200 bg-emerald-100/70 px-2 py-0.5 text-xs font-medium text-emerald-800"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400">None detected</span>
                    )}
                  </div>
                </div>

                <div className="rounded-xl border border-rose-100 bg-rose-50/40 p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs font-bold text-rose-800">
                    <AlertTriangle className="h-4 w-4 text-rose-600" />
                    Missing Required Skills ({data.missing_skills.length})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.missing_skills.length > 0 ? (
                      data.missing_skills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-md border border-rose-200 bg-rose-100/70 px-2 py-0.5 text-xs font-medium text-rose-800"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-emerald-600">All required skills satisfied!</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Experience and Qualification Deltas if available */}
              {data.experience_comparison && data.qualification_comparison && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-gray-200 bg-white p-4">
                    <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-gray-500">
                      <Briefcase className="h-4 w-4 text-gray-400" />
                      Experience Comparison
                    </div>
                    <div className="mt-2 text-sm text-gray-800">
                      <div>Candidate: <span className="font-semibold">{data.experience_comparison.candidate_years} yrs</span></div>
                      <div>Required: <span className="font-semibold">{data.experience_comparison.required_years} yrs</span></div>
                      <div className="mt-1 text-xs font-medium">
                        Delta:{" "}
                        <span
                          className={
                            data.experience_comparison.delta_years >= 0
                              ? "text-emerald-600"
                              : "text-rose-600"
                          }
                        >
                          {data.experience_comparison.delta_years >= 0 ? "+" : ""}
                          {data.experience_comparison.delta_years} yrs
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-gray-200 bg-white p-4">
                    <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-gray-500">
                      <GraduationCap className="h-4 w-4 text-gray-400" />
                      Qualification Match
                    </div>
                    <div className="mt-2 text-sm text-gray-800">
                      <div>Candidate: <span className="font-semibold">{data.qualification_comparison.candidate_degree}</span></div>
                      <div>Required: <span className="font-semibold">{data.qualification_comparison.required_degree}</span></div>
                      <div className="mt-1">
                        <span
                          className={`rounded px-1.5 py-0.5 text-xs font-bold ${
                            data.qualification_comparison.status === "MEETS"
                              ? "bg-emerald-100 text-emerald-800"
                              : data.qualification_comparison.status === "EQUIVALENT"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {data.qualification_comparison.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Strengths and Gaps */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Key Strengths & Competencies
                </h4>
                <ul className="space-y-1.5">
                  {data.strengths.map((str, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
                      <span>{str}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {data.skill_gaps.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Identified Gaps & Considerations
                  </h4>
                  <ul className="space-y-1.5">
                    {data.skill_gaps.map((gap, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Missing Skills & Verification Analysis */}
              {data.missing_skills_analysis && data.missing_skills_analysis.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">
                      Missing Skills &amp; Verification Classification
                    </h4>
                    <span className="text-[11px] text-gray-400">
                      {data.missing_skills_analysis.length} skill(s) evaluated
                    </span>
                  </div>
                  <div className="grid gap-2.5 sm:grid-cols-2">
                    {data.missing_skills_analysis.map((item, idx) => (
                      <div key={idx} className="rounded-xl border border-gray-200 bg-white p-3 space-y-1.5 shadow-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xs text-gray-900">{item.skill}</span>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                              item.classification === "Equivalent Skill"
                                ? "bg-blue-100 text-blue-800"
                                : item.classification === "Partially Evidenced"
                                ? "bg-amber-100 text-amber-800"
                                : item.classification === "Not Evidenced"
                                ? "bg-purple-100 text-purple-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {item.classification}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-600">{item.evidence_notes}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recruiter Verification Questions */}
              {data.recruiter_verification_questions && data.recruiter_verification_questions.length > 0 && (
                <div className="space-y-3 rounded-xl border border-blue-200 bg-blue-50/50 p-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-blue-900">
                    <Sparkles className="h-4 w-4 text-blue-600" />
                    <span>Recruiter Verification &amp; Interview Questions</span>
                  </div>
                  <ol className="list-decimal list-inside space-y-2 text-xs text-gray-800">
                    {data.recruiter_verification_questions.map((q, idx) => (
                      <li key={idx} className="leading-relaxed">
                        <span className="font-medium text-gray-900">{q}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Score Consistency Review */}
              {data.score_consistency && (
                <div className="rounded-xl border border-gray-200 bg-white p-4 space-y-2 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-700 flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-emerald-600" />
                      Score Consistency Review Audit
                    </span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                        data.score_consistency.status === "CONSISTENT"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {data.score_consistency.status}
                    </span>
                  </div>
                  {data.score_consistency.flags && data.score_consistency.flags.length > 0 ? (
                    <ul className="space-y-1 text-xs text-amber-900 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                      {data.score_consistency.flags.map((f, idx) => (
                        <li key={idx}>• {f}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-[11px] text-gray-500">
                      AI fitment score aligns consistently with grounded evidence, requirement coverage, and verified experience tenure.
                    </p>
                  )}
                </div>
              )}

              {/* Risk Flags & Uncertainty Flags */}
              {((data.risk_flags && data.risk_flags.length > 0) ||
                (data.uncertainty_flags && data.uncertainty_flags.length > 0)) && (
                <div className="grid gap-4 sm:grid-cols-2">
                  {data.risk_flags && data.risk_flags.length > 0 && (
                    <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4">
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-bold text-rose-800">
                        <AlertCircle className="h-4 w-4 text-rose-600" />
                        Risk Flags
                      </div>
                      <ul className="space-y-1 text-xs text-rose-900">
                        {data.risk_flags.map((rf, idx) => (
                          <li key={idx}>• {rf}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {data.uncertainty_flags && data.uncertainty_flags.length > 0 && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-bold text-amber-800">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        Uncertainty Flags
                      </div>
                      <ul className="space-y-1 text-xs text-amber-900">
                        {data.uncertainty_flags.map((uf, idx) => (
                          <li key={idx}>• {uf}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 bg-gray-50/50 p-4 text-right">
          <button
            onClick={onClose}
            className="rounded-lg bg-gray-900 px-5 py-2 text-xs font-semibold text-white hover:bg-gray-800 transition shadow-xs"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};
