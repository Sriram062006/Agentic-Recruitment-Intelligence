import React from "react";
import { ExplainabilityPayload } from "@/types/evaluation.types";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  Briefcase,
  GraduationCap,
  Sparkles,
} from "lucide-react";

interface FitmentModalProps {
  isOpen: boolean;
  onClose: () => void;
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
  candidateName,
  jobTitle,
  compositeScore,
  rankInRole,
  data,
  loading,
}) => {
  if (!isOpen) return null;

  const scorePct = Math.round(compositeScore * 100);
  const scoreColor =
    scorePct >= 75
      ? "text-emerald-700 bg-emerald-50 border-emerald-200"
      : scorePct >= 50
      ? "text-amber-700 bg-amber-50 border-amber-200"
      : "text-rose-700 bg-rose-50 border-rose-200";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 p-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
                Explainable Fitment Report
              </span>
              {rankInRole && (
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                  Role Rank #{rankInRole}
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-gray-900">{candidateName}</h2>
            <p className="text-sm text-gray-500">Evaluated against: <span className="font-semibold text-gray-800">{jobTitle}</span></p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`rounded-xl border px-4 py-2 text-center ${scoreColor}`}>
              <div className="text-2xl font-black">{scorePct}%</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider">Composite Fit</div>
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
              <span>Synthesizing grounded fitment evidence...</span>
            </div>
          ) : !data ? (
            <div className="py-12 text-center text-gray-500">No explanation payload available.</div>
          ) : (
            <div className="space-y-6">
              {/* Recommendation Rationale */}
              <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-5">
                <div className="mb-2 flex items-center gap-2 text-sm font-bold text-blue-900">
                  <Sparkles className="h-4 w-4 text-blue-600" />
                  Recommendation Rationale
                </div>
                <p className="text-sm leading-relaxed text-blue-950">
                  {data.recommendation_rationale}
                </p>
              </div>

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

              {/* Experience and Qualification Deltas */}
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
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 bg-gray-50/50 p-4 text-right">
          <button
            onClick={onClose}
            className="rounded-lg bg-gray-900 px-4 py-2 text-xs font-semibold text-white hover:bg-gray-800"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};
