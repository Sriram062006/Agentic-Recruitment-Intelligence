import React, { useEffect, useState } from "react";
import {
  createEvaluationRun,
  fetchCandidates,
  fetchJobs,
  getEvaluationMatrix,
  getExplainability,
  getRoleLeaderboard,
} from "@/lib/api-client";
import { FitmentModal } from "@/components/explainability/FitmentModal";
import { CandidateResponse } from "@/types/candidate.types";
import {
  EvaluationMatrixResponse,
  ExplainabilityPayload,
  LeaderboardEntry,
} from "@/types/evaluation.types";
import { JobResponse } from "@/types/job.types";
import {
  PlayCircle,
  Grid3X3,
  ListOrdered,
  AlertCircle,
  ChevronRight,
  Eye,
  CheckSquare,
  Square,
  Users,
  Briefcase,
  HelpCircle,
  X,
  Sparkles,
  Trophy,
  Filter,
  CheckCircle2,
  Cpu,
  BarChart2,
  ShieldCheck,
  Award,
  Sliders,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export const EvaluationView: React.FC = () => {
  const { isViewer } = useAuth();
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [candidates, setCandidates] = useState<CandidateResponse[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [matrixData, setMatrixData] = useState<EvaluationMatrixResponse | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);

  // Subset Selection State
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [isConfirmOpen, setIsConfirmOpen] = useState<boolean>(false);

  // Engine & Scoring Mode
  const [evaluationEngine, setEvaluationEngine] = useState<"ai_fitment" | "deterministic">("ai_fitment");
  const [showAdvancedWeights, setShowAdvancedWeights] = useState<boolean>(false);

  // Fallback / Advanced Weights & Heuristics
  const [semWeight, setSemWeight] = useState<number>(0.35);
  const [skillWeight, setSkillWeight] = useState<number>(0.35);
  const [expWeight, setExpWeight] = useState<number>(0.20);
  const [qualWeight, setQualWeight] = useState<number>(0.10);
  const alphaSkill = 0.80;
  const betaExp = 1.50;

  // Leaderboard Filtering & Score Slider
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string | null>(null);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fitment Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [modalCandidateId, setModalCandidateId] = useState<string>("");
  const [modalJobId, setModalJobId] = useState<string>("");
  const [modalCandidateName, setModalCandidateName] = useState<string>("");
  const [modalJobTitle, setModalJobTitle] = useState<string>("");
  const [modalCompositeScore, setModalCompositeScore] = useState<number>(0);
  const [modalRank, setModalRank] = useState<number | undefined>(undefined);
  const [modalData, setModalData] = useState<ExplainabilityPayload | null>(null);
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  const loadInitialData = async () => {
    try {
      const [jList, cList] = await Promise.all([fetchJobs(), fetchCandidates()]);
      setJobs(jList);
      setCandidates(cList);
      setSelectedJobIds(jList.map((j) => j.id));
      setSelectedCandidateIds(cList.map((c) => c.id));
      if (jList.length > 0 && !selectedJobId) {
        setSelectedJobId(jList[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const totalEvaluationsExpected = selectedCandidateIds.length * selectedJobIds.length;

  const handleOpenConfirm = () => {
    if (selectedJobIds.length === 0) {
      setErrorMsg("Please select at least 1 Job Role for evaluation.");
      return;
    }
    if (selectedCandidateIds.length === 0) {
      setErrorMsg("Please select at least 1 Candidate for evaluation.");
      return;
    }

    if (evaluationEngine === "deterministic") {
      const totalWeight = Number((semWeight + skillWeight + expWeight + qualWeight).toFixed(3));
      if (Math.abs(totalWeight - 1.0) > 0.01) {
        setErrorMsg(`Fitment weights must sum to 1.0 (Current sum: ${totalWeight}).`);
        return;
      }
    }

    setErrorMsg(null);
    setIsConfirmOpen(true);
  };

  const handleExecuteEvaluation = async () => {
    setIsConfirmOpen(false);
    setIsRunning(true);
    setErrorMsg(null);

    try {
      const run = await createEvaluationRun({
        job_ids: selectedJobIds,
        candidate_ids: selectedCandidateIds,
        evaluation_engine: evaluationEngine,
        weights: {
          semantic_weight: semWeight,
          skill_weight: skillWeight,
          experience_weight: expWeight,
          qualification_weight: qualWeight,
        },
        heuristics: {
          alpha_skill_weight: alphaSkill,
          beta_experience_penalty: betaExp,
          fitment_strong_threshold: 0.75,
          fitment_moderate_threshold: 0.50,
        },
      });

      setActiveRunId(run.id);

      // Fetch matrix
      const matrix = await getEvaluationMatrix(run.id);
      setMatrixData(matrix);

      // Fetch leaderboard for first selected role
      const targetJob = selectedJobIds[0] || (jobs.length > 0 ? jobs[0].id : "");
      if (targetJob) {
        setSelectedJobId(targetJob);
        const lb = await getRoleLeaderboard(run.id, targetJob);
        setLeaderboard(lb);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute evaluation");
    } finally {
      setIsRunning(false);
    }
  };

  const handleJobSelect = async (jobId: string) => {
    setSelectedJobId(jobId);
    if (activeRunId) {
      try {
        const lb = await getRoleLeaderboard(activeRunId, jobId);
        setLeaderboard(lb);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const openExplainability = async (
    candidateId: string,
    candidateName: string,
    jobId: string,
    jobTitle: string,
    compositeScore: number,
    rank?: number
  ) => {
    if (!activeRunId) return;

    setModalCandidateId(candidateId);
    setModalJobId(jobId);
    setModalCandidateName(candidateName);
    setModalJobTitle(jobTitle);
    setModalCompositeScore(compositeScore);
    setModalRank(rank);
    setIsModalOpen(true);
    setModalLoading(true);

    try {
      const expl = await getExplainability(activeRunId, candidateId, jobId);
      setModalData(expl);
    } catch (err) {
      console.error(err);
    } finally {
      setModalLoading(false);
    }
  };

  const toggleJob = (id: string) => {
    setSelectedJobIds((prev) =>
      prev.includes(id) ? prev.filter((jId) => jId !== id) : [...prev, id]
    );
  };

  const toggleCandidate = (id: string) => {
    setSelectedCandidateIds((prev) =>
      prev.includes(id) ? prev.filter((cId) => cId !== id) : [...prev, id]
    );
  };

  // Helper functions for scoring and categories
  const getScoreVal = (entry: LeaderboardEntry) =>
    entry.composite_score <= 1.0
      ? Math.round(entry.composite_score * 100)
      : Math.round(entry.composite_score);

  const getCategory = (entry: LeaderboardEntry): string => {
    if (entry.fitment_category) return entry.fitment_category;
    const score = getScoreVal(entry);
    if (score >= 85) return "EXCELLENT_FIT";
    if (score >= 70) return "STRONG_FIT";
    if (score >= 55) return "GOOD_FIT";
    if (score >= 40) return "PARTIAL_FIT";
    if (score >= 25) return "WEAK_FIT";
    return "POOR_FIT";
  };

  const getCategoryLabel = (cat: string) => {
    switch (cat) {
      case "EXCELLENT_FIT":
        return "Excellent Fit";
      case "STRONG_FIT":
        return "Strong Fit";
      case "GOOD_FIT":
        return "Good Fit";
      case "PARTIAL_FIT":
        return "Partial Fit";
      case "WEAK_FIT":
        return "Weak Fit";
      case "POOR_FIT":
        return "Poor Fit";
      default:
        return cat.replace("_", " ");
    }
  };

  const getCategoryBadgeClass = (cat: string) => {
    switch (cat) {
      case "EXCELLENT_FIT":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "STRONG_FIT":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "GOOD_FIT":
        return "bg-cyan-100 text-cyan-800 border-cyan-300";
      case "PARTIAL_FIT":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "WEAK_FIT":
      case "POOR_FIT":
      default:
        return "bg-rose-100 text-rose-800 border-rose-300";
    }
  };

  // Distribution Counts for Selected Role Leaderboard
  const distributionCounts = {
    all: leaderboard.length,
    excellent: leaderboard.filter((e) => getScoreVal(e) >= 85).length,
    strong: leaderboard.filter((e) => getScoreVal(e) >= 70 && getScoreVal(e) < 85).length,
    good: leaderboard.filter((e) => getScoreVal(e) >= 55 && getScoreVal(e) < 70).length,
    partial: leaderboard.filter((e) => getScoreVal(e) >= 40 && getScoreVal(e) < 55).length,
    low: leaderboard.filter((e) => getScoreVal(e) < 40).length,
  };

  // Filtered Leaderboard
  const filteredLeaderboard = leaderboard.filter((entry) => {
    const score = getScoreVal(entry);
    if (score < minScoreFilter) return false;
    if (selectedCategoryFilter) {
      const cat = getCategory(entry);
      if (selectedCategoryFilter === "LOW_FIT") {
        if (cat !== "WEAK_FIT" && cat !== "POOR_FIT") return false;
      } else if (cat !== selectedCategoryFilter) {
        return false;
      }
    }
    return true;
  });

  // Top Fit Candidates Showcase (Top 3 with score >= 60, or top 3 ranked)
  const topFitCandidates = leaderboard
    .filter((e) => getScoreVal(e) >= 60)
    .slice(0, 3);
  const displayTopFit = topFitCandidates.length > 0 ? topFitCandidates : leaderboard.slice(0, 3);

  const selectedJob = jobs.find((j) => j.id === selectedJobId);

  return (
    <div className="space-y-8">
      {/* Configuration & Action Card */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-gray-900">Multi-Role Evaluation Setup</h2>
              <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-[11px] font-bold text-blue-700 border border-blue-200">
                <Sparkles className="h-3 w-3 text-blue-600" />
                AI Contextual Engine Active
              </span>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-md bg-blue-50 px-2 py-0.5 font-semibold text-blue-700">
                Selected Candidates: {selectedCandidateIds.length} / {candidates.length}
              </span>
              <span className="text-gray-400">•</span>
              <span className="rounded-md bg-indigo-50 px-2 py-0.5 font-semibold text-indigo-700">
                Selected Roles: {selectedJobIds.length} / {jobs.length}
              </span>
              <span className="text-gray-400">•</span>
              <span className="rounded-md bg-emerald-50 px-2.5 py-0.5 font-bold text-emerald-800">
                Expected Evaluations: {totalEvaluationsExpected} ({selectedCandidateIds.length} × {selectedJobIds.length})
              </span>
            </div>
          </div>

          <button
            onClick={handleOpenConfirm}
            disabled={
              isRunning ||
              selectedJobIds.length === 0 ||
              selectedCandidateIds.length === 0 ||
              isViewer
            }
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isViewer ? (
              <Eye className="h-4 w-4 text-white" />
            ) : (
              <PlayCircle className={`h-4 w-4 ${isRunning ? "animate-spin" : ""}`} />
            )}
            <span>
              {isRunning
                ? "Evaluating Matrix with AI Engine..."
                : isViewer
                ? "Read-Only (Viewer Role)"
                : `Run Multi-Role Evaluation (${totalEvaluationsExpected})`}
            </span>
          </button>
        </div>

        {isViewer && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            <Eye className="h-4 w-4 shrink-0 text-amber-600" />
            <span>
              Viewer Mode: You have read-only access. Creating new evaluation runs is restricted to Recruiters and Administrators. You can inspect previous evaluation runs in the Evaluation History tab.
            </span>
          </div>
        )}

        {errorMsg && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4" />
            {errorMsg}
          </div>
        )}

        {/* Subset Selection Pickers */}
        <div className="mt-6 grid gap-6 border-t pt-5 md:grid-cols-2">
          {/* Role Subset Picker */}
          <div className="rounded-lg border border-gray-100 bg-slate-50/60 p-4">
            <div className="mb-2.5 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-gray-800">
                <Briefcase className="h-4 w-4 text-indigo-600" />
                Select Target Roles ({selectedJobIds.length}/{jobs.length})
              </div>
              <div className="flex gap-2 text-[11px]">
                <button
                  type="button"
                  onClick={() => setSelectedJobIds(jobs.map((j) => j.id))}
                  className="font-medium text-blue-600 hover:underline"
                >
                  Select All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  type="button"
                  onClick={() => setSelectedJobIds([])}
                  className="font-medium text-gray-500 hover:underline"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="max-h-40 space-y-1.5 overflow-y-auto pr-1">
              {jobs.map((job) => {
                const isSelected = selectedJobIds.includes(job.id);
                return (
                  <div
                    key={job.id}
                    onClick={() => toggleJob(job.id)}
                    className={`flex cursor-pointer items-center justify-between rounded-md border p-2 text-xs transition ${
                      isSelected
                        ? "border-indigo-300 bg-indigo-50/70 text-indigo-950 font-semibold"
                        : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {isSelected ? (
                        <CheckSquare className="h-3.5 w-3.5 text-indigo-600 shrink-0" />
                      ) : (
                        <Square className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                      )}
                      <span className="truncate">{job.structured_profile.title}</span>
                    </div>
                    <span className="text-[10px] text-gray-400 shrink-0 ml-2">
                      {job.structured_profile.min_experience_years}+ yrs
                    </span>
                  </div>
                );
              })}
              {jobs.length === 0 && (
                <div className="py-4 text-center text-xs text-gray-400">No jobs uploaded yet.</div>
              )}
            </div>
          </div>

          {/* Candidate Subset Picker */}
          <div className="rounded-lg border border-gray-100 bg-slate-50/60 p-4">
            <div className="mb-2.5 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-gray-800">
                <Users className="h-4 w-4 text-blue-600" />
                Select Candidates ({selectedCandidateIds.length}/{candidates.length})
              </div>
              <div className="flex gap-2 text-[11px]">
                <button
                  type="button"
                  onClick={() => setSelectedCandidateIds(candidates.map((c) => c.id))}
                  className="font-medium text-blue-600 hover:underline"
                >
                  Select All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  type="button"
                  onClick={() => setSelectedCandidateIds([])}
                  className="font-medium text-gray-500 hover:underline"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="max-h-40 space-y-1.5 overflow-y-auto pr-1">
              {candidates.map((cand) => {
                const isSelected = selectedCandidateIds.includes(cand.id);
                return (
                  <div
                    key={cand.id}
                    onClick={() => toggleCandidate(cand.id)}
                    className={`flex cursor-pointer items-center justify-between rounded-md border p-2 text-xs transition ${
                      isSelected
                        ? "border-blue-300 bg-blue-50/70 text-blue-950 font-semibold"
                        : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {isSelected ? (
                        <CheckSquare className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                      ) : (
                        <Square className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                      )}
                      <span className="truncate">{cand.structured_profile.full_name}</span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0 ml-2">
                      <span className="text-[10px] text-gray-500 font-medium">
                        {cand.structured_profile.total_experience_years}{" "}
                        {cand.structured_profile.total_experience_years === 1 ? "yr" : "yrs"}
                      </span>
                    </div>
                  </div>
                );
              })}
              {candidates.length === 0 && (
                <div className="py-4 text-center text-xs text-gray-400">No candidates in pool yet.</div>
              )}
            </div>
          </div>
        </div>

        {/* AI Fitment Engine Panel */}
        <div className="mt-6 border-t pt-5">
          <div className="rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-slate-50/60 p-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-blue-600 p-2 text-white shadow-xs">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-gray-900">AI Contextual Fitment Engine</h3>
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-200">
                      Active Default
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-gray-600">
                    Evaluates the complete candidate profile (career history, verified skills, tools, qualifications, projects) against the complete Job Description. Generates an evidence-grounded 0–100 score with post-LLM citation verification.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                <select
                  value={evaluationEngine}
                  onChange={(e) => setEvaluationEngine(e.target.value as any)}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-800 outline-none focus:border-blue-500 shadow-xs"
                >
                  <option value="ai_fitment">AI Fitment Engine (0–100)</option>
                  <option value="deterministic">Legacy Deterministic Baseline</option>
                </select>
              </div>
            </div>

            <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-blue-200/50 text-[11px] text-gray-700">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                <span>Full-Document Contextual Evaluation</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                <span>Post-LLM Citation Verification</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5 text-indigo-600 shrink-0" />
                <span>Semantic Embeddings & FAISS Anchors</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Award className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                <span>Role-Wise Ranked Fitment Tiers</span>
              </div>
            </div>

            {evaluationEngine === "deterministic" && (
              <div className="mt-3 border-t border-amber-200 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAdvancedWeights(!showAdvancedWeights)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-amber-800 hover:text-amber-900"
                >
                  <Sliders className="h-3.5 w-3.5" />
                  <span>{showAdvancedWeights ? "Hide" : "Show"} Deterministic Weight Adjustments</span>
                </button>

                {showAdvancedWeights && (
                  <div className="mt-3 grid gap-3 sm:grid-cols-4 bg-white/80 p-3 rounded-lg border border-amber-200">
                    <div>
                      <label className="text-[11px] font-semibold text-gray-700">
                        Semantic: {semWeight}
                      </label>
                      <input
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={semWeight}
                        onChange={(e) => setSemWeight(parseFloat(e.target.value))}
                        className="mt-1 w-full"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-gray-700">
                        Skill: {skillWeight}
                      </label>
                      <input
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={skillWeight}
                        onChange={(e) => setSkillWeight(parseFloat(e.target.value))}
                        className="mt-1 w-full"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-gray-700">
                        Experience: {expWeight}
                      </label>
                      <input
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={expWeight}
                        onChange={(e) => setExpWeight(parseFloat(e.target.value))}
                        className="mt-1 w-full"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-gray-700">
                        Qualification: {qualWeight}
                      </label>
                      <input
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={qualWeight}
                        onChange={(e) => setQualWeight(parseFloat(e.target.value))}
                        className="mt-1 w-full"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {isConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-4">
              <div className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5 text-blue-600" />
                <h3 className="text-base font-bold text-gray-900">
                  Confirm Multi-Role Evaluation Run
                </h3>
              </div>
              <button
                onClick={() => setIsConfirmOpen(false)}
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 py-4 text-xs text-gray-600">
              <p>
                You are about to launch a multi-role AI evaluation across the selected candidate and job pools:
              </p>

              <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4 space-y-2">
                <div className="flex justify-between font-medium">
                  <span>Selected Candidates:</span>
                  <span className="font-bold text-blue-900">{selectedCandidateIds.length} candidate(s)</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Selected Target Roles:</span>
                  <span className="font-bold text-indigo-900">{selectedJobIds.length} role(s)</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Evaluation Engine:</span>
                  <span className="font-bold text-blue-800">
                    {evaluationEngine === "ai_fitment" ? "AI Contextual Fitment (0–100)" : "Deterministic Baseline"}
                  </span>
                </div>
                <div className="flex justify-between border-t border-blue-200/60 pt-2 text-sm font-bold text-emerald-800">
                  <span>Total Generated Evaluations (N × M):</span>
                  <span>{totalEvaluationsExpected}</span>
                </div>
              </div>

              <div className="text-[11px] text-gray-500">
                Candidate evaluation results will be stored immutably in Supabase PostgreSQL with complete evidence citations, confidence metrics, and post-LLM verification.
              </div>
            </div>

            <div className="flex justify-end gap-3 border-t pt-4">
              <button
                onClick={() => setIsConfirmOpen(false)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteEvaluation}
                className="rounded-lg bg-blue-600 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-blue-700"
              >
                Confirm & Launch Run ({totalEvaluationsExpected})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* N x M Cross-Role Evaluation Matrix */}
      {matrixData && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Grid3X3 className="h-4 w-4 text-blue-600" />
                <h3 className="text-base font-bold text-gray-900">Multi-Role Evaluation Matrix</h3>
              </div>
              <p className="text-xs text-gray-500">
                Cross-comparison of all candidates against every job. Click any score cell to open full grounded evidence & audit.
              </p>
            </div>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
              {matrixData.total_evaluations} Pair Evaluations Generated
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="border-b bg-gray-50/80">
                  <th className="p-3 text-left font-bold text-gray-700">Candidate</th>
                  {matrixData.jobs.map((j) => (
                    <th key={j.id} className="p-3 text-center font-bold text-gray-700">
                      {j.title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {matrixData.candidates.map((cand) => (
                  <tr key={cand.id} className="hover:bg-slate-50/50">
                    <td className="p-3 font-semibold text-gray-900">{cand.name}</td>
                    {matrixData.jobs.map((job) => {
                      const cell = matrixData.cells.find(
                        (c) => c.candidate_id === cand.id && c.job_id === job.id
                      );
                      if (!cell) return <td key={job.id} className="p-3 text-center text-gray-300">-</td>;

                      const scoreVal =
                        cell.composite_score <= 1.0
                          ? Math.round(cell.composite_score * 100)
                          : Math.round(cell.composite_score);

                      const bgClass =
                        scoreVal >= 85
                          ? "bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100"
                          : scoreVal >= 70
                          ? "bg-blue-50 text-blue-800 border-blue-200 hover:bg-blue-100"
                          : scoreVal >= 55
                          ? "bg-cyan-50 text-cyan-800 border-cyan-200 hover:bg-cyan-100"
                          : scoreVal >= 40
                          ? "bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100"
                          : "bg-rose-50 text-rose-800 border-rose-200 hover:bg-rose-100";

                      return (
                        <td key={job.id} className="p-2 text-center">
                          <button
                            onClick={() =>
                              openExplainability(
                                cand.id,
                                cand.name,
                                job.id,
                                job.title,
                                scoreVal,
                                cell.rank_in_role
                              )
                            }
                            className={`w-16 rounded-lg border py-1.5 text-xs font-bold shadow-xs transition ${bgClass}`}
                            title={`Click to inspect explainable fitment for ${cand.name} in ${job.title}`}
                          >
                            {scoreVal}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Role-Wise Ranked Leaderboard & Showcase */}
      {activeRunId && jobs.length > 0 && (
        <div className="space-y-6">
          {/* TOP FIT CANDIDATES PROMINENT SECTION */}
          <div className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50/80 via-white to-indigo-50/50 p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-blue-100 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="rounded-lg bg-amber-500 p-2 text-white shadow-xs">
                  <Trophy className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">Top Fit Candidates</h3>
                  <p className="text-xs text-gray-600">
                    Highest-ranking candidates for{" "}
                    <span className="font-semibold text-blue-800">
                      {selectedJob?.structured_profile.title || "Selected Role"}
                    </span>
                  </p>
                </div>
              </div>

              {/* Role Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-gray-600">Role:</span>
                <select
                  value={selectedJobId}
                  onChange={(e) => handleJobSelect(e.target.value)}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-bold text-gray-800 outline-none focus:border-blue-500 shadow-xs"
                >
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.structured_profile.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {displayTopFit.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-500">
                No evaluated candidates available for this role yet.
              </div>
            ) : (
              <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
                {displayTopFit.map((entry, idx) => {
                  const scoreVal = getScoreVal(entry);
                  const cat = getCategory(entry);
                  const currentJobTitle =
                    jobs.find((j) => j.id === selectedJobId)?.structured_profile.title || "Job";

                  return (
                    <div
                      key={entry.candidate_id}
                      className="relative rounded-xl border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between"
                    >
                      {/* Rank ribbon */}
                      <div className="flex items-center justify-between mb-3">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                            idx === 0
                              ? "bg-amber-100 text-amber-900 border border-amber-300"
                              : idx === 1
                              ? "bg-slate-200 text-slate-800 border border-slate-300"
                              : "bg-orange-100 text-orange-900 border border-orange-300"
                          }`}
                        >
                          <Award className="h-3.5 w-3.5" />
                          Rank #{entry.rank}
                        </span>

                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${getCategoryBadgeClass(
                            cat
                          )}`}
                        >
                          {getCategoryLabel(cat)}
                        </span>
                      </div>

                      <div className="space-y-1 mb-3">
                        <h4 className="text-sm font-bold text-gray-900 truncate">
                          {entry.candidate_name}
                        </h4>
                        <p className="text-xs text-gray-500">
                          {entry.total_experience_years} yrs exp • {entry.highest_qualification}
                        </p>
                      </div>

                      {/* Score Meter */}
                      <div className="mb-4 space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-gray-600">AI Fitment Score</span>
                          <span className="text-sm font-extrabold text-blue-700">{scoreVal} / 100</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              scoreVal >= 85
                                ? "bg-emerald-500"
                                : scoreVal >= 70
                                ? "bg-blue-600"
                                : scoreVal >= 55
                                ? "bg-cyan-500"
                                : "bg-amber-500"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(5, scoreVal))}%` }}
                          />
                        </div>
                      </div>

                      {entry.recruiter_recommendation && (
                        <div className="mb-3 text-[11px] text-gray-600">
                          <span className="font-semibold text-gray-700">Recommendation: </span>
                          <span className="font-bold text-blue-900">{entry.recruiter_recommendation}</span>
                        </div>
                      )}

                      <button
                        onClick={() =>
                          openExplainability(
                            entry.candidate_id,
                            entry.candidate_name,
                            selectedJobId,
                            currentJobTitle,
                            scoreVal,
                            entry.rank
                          )
                        }
                        className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-3 py-2 text-xs font-bold text-blue-700 hover:bg-blue-100 transition shadow-xs"
                      >
                        <span>Inspect Fitment Report</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Leaderboard Table with Score Range Slider and Distribution Breakdown */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-6 flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <ListOrdered className="h-4 w-4 text-blue-600" />
                    <h3 className="text-base font-bold text-gray-900">
                      Role-Wise Ranked Leaderboard ({selectedJob?.structured_profile.title})
                    </h3>
                  </div>
                  <p className="text-xs text-gray-500">
                    Full ranking of candidates evaluated against this job role. Use the slider or category filters below to refine the list.
                  </p>
                </div>

                <div className="text-xs font-semibold text-gray-500">
                  Showing <span className="font-bold text-gray-900">{filteredLeaderboard.length}</span> of{" "}
                  <span className="font-bold text-gray-900">{leaderboard.length}</span> Candidates
                </div>
              </div>

              {/* 0-100 Fitment Score Range Slider & Category Filters */}
              <div className="rounded-xl border border-gray-200 bg-slate-50/60 p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                  {/* Slider */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-bold text-gray-700 flex items-center gap-1.5">
                        <Filter className="h-3.5 w-3.5 text-blue-600" />
                        Minimum AI Fitment Score Filter
                      </span>
                      <span className="font-mono font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-gray-200 shadow-xs">
                        &ge; {minScoreFilter} / 100
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={minScoreFilter}
                      onChange={(e) => setMinScoreFilter(parseInt(e.target.value, 10))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                    <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                      <span>0 (All)</span>
                      <span>25</span>
                      <span>50</span>
                      <span>75</span>
                      <span>100</span>
                    </div>
                  </div>

                  {/* Distribution breakdown pills */}
                  <div>
                    <div className="text-xs font-bold text-gray-700 mb-1.5 flex items-center gap-1.5">
                      <BarChart2 className="h-3.5 w-3.5 text-indigo-600" />
                      Score Distribution Breakdown (Click to filter)
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      <button
                        onClick={() => setSelectedCategoryFilter(null)}
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          selectedCategoryFilter === null
                            ? "bg-gray-900 text-white shadow-xs"
                            : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-100"
                        }`}
                      >
                        All ({distributionCounts.all})
                      </button>
                      <button
                        onClick={() =>
                          setSelectedCategoryFilter(
                            selectedCategoryFilter === "EXCELLENT_FIT" ? null : "EXCELLENT_FIT"
                          )
                        }
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          selectedCategoryFilter === "EXCELLENT_FIT"
                            ? "bg-emerald-600 text-white shadow-xs"
                            : "bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                        }`}
                      >
                        Excellent ({distributionCounts.excellent})
                      </button>
                      <button
                        onClick={() =>
                          setSelectedCategoryFilter(
                            selectedCategoryFilter === "STRONG_FIT" ? null : "STRONG_FIT"
                          )
                        }
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          selectedCategoryFilter === "STRONG_FIT"
                            ? "bg-blue-600 text-white shadow-xs"
                            : "bg-blue-50 text-blue-800 border border-blue-200 hover:bg-blue-100"
                        }`}
                      >
                        Strong ({distributionCounts.strong})
                      </button>
                      <button
                        onClick={() =>
                          setSelectedCategoryFilter(
                            selectedCategoryFilter === "GOOD_FIT" ? null : "GOOD_FIT"
                          )
                        }
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          selectedCategoryFilter === "GOOD_FIT"
                            ? "bg-cyan-600 text-white shadow-xs"
                            : "bg-cyan-50 text-cyan-800 border border-cyan-200 hover:bg-cyan-100"
                        }`}
                      >
                        Good ({distributionCounts.good})
                      </button>
                      <button
                        onClick={() =>
                          setSelectedCategoryFilter(
                            selectedCategoryFilter === "PARTIAL_FIT" ? null : "PARTIAL_FIT"
                          )
                        }
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          selectedCategoryFilter === "PARTIAL_FIT"
                            ? "bg-amber-600 text-white shadow-xs"
                            : "bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100"
                        }`}
                      >
                        Partial ({distributionCounts.partial})
                      </button>
                      <button
                        onClick={() =>
                          setSelectedCategoryFilter(
                            selectedCategoryFilter === "LOW_FIT" ? null : "LOW_FIT"
                          )
                        }
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          selectedCategoryFilter === "LOW_FIT"
                            ? "bg-rose-600 text-white shadow-xs"
                            : "bg-rose-50 text-rose-800 border border-rose-200 hover:bg-rose-100"
                        }`}
                      >
                        Low ({distributionCounts.low})
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {filteredLeaderboard.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-500 bg-gray-50 rounded-xl border border-gray-100">
                No candidates match the selected filters (Minimum Score &ge; {minScoreFilter}
                {selectedCategoryFilter ? `, Category: ${selectedCategoryFilter}` : ""}).
                <div className="mt-2">
                  <button
                    onClick={() => {
                      setMinScoreFilter(0);
                      setSelectedCategoryFilter(null);
                    }}
                    className="text-xs font-semibold text-blue-600 hover:underline"
                  >
                    Reset filters
                  </button>
                </div>
              </div>
            ) : (
              <div className="overflow-hidden rounded-xl border border-gray-200">
                <table className="w-full border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b bg-gray-50/80 font-bold text-gray-600">
                      <th className="p-3 pl-6">Rank</th>
                      <th className="p-3">Candidate</th>
                      <th className="p-3">Verified Tenure</th>
                      <th className="p-3">AI Fitment Score</th>
                      <th className="p-3">Fitment Tier</th>
                      <th className="p-3">Recommendation</th>
                      <th className="p-3 pr-6 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {filteredLeaderboard.map((entry) => {
                      const scoreVal = getScoreVal(entry);
                      const cat = getCategory(entry);
                      const currentJobTitle =
                        jobs.find((j) => j.id === selectedJobId)?.structured_profile.title || "Job";

                      return (
                        <tr key={entry.candidate_id} className="hover:bg-slate-50/50 transition">
                          <td className="p-3 pl-6 font-bold text-gray-900">
                            <span
                              className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
                                entry.rank === 1
                                  ? "bg-amber-100 text-amber-800 ring-1 ring-amber-300"
                                  : entry.rank === 2
                                  ? "bg-slate-200 text-slate-700 ring-1 ring-slate-300"
                                  : entry.rank === 3
                                  ? "bg-orange-100 text-orange-800 ring-1 ring-orange-300"
                                  : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              #{entry.rank}
                            </span>
                          </td>
                          <td className="p-3 font-semibold text-gray-900">
                            <div>{entry.candidate_name}</div>
                          </td>
                          <td className="p-3 text-gray-600">
                            {entry.total_experience_years} yrs • {entry.highest_qualification}
                          </td>
                          <td className="p-3">
                            <span
                              className={`rounded-md px-2.5 py-1 text-xs font-extrabold ${
                                scoreVal >= 85
                                  ? "bg-emerald-100 text-emerald-800"
                                  : scoreVal >= 70
                                  ? "bg-blue-100 text-blue-800"
                                  : scoreVal >= 55
                                  ? "bg-cyan-100 text-cyan-800"
                                  : scoreVal >= 40
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-rose-100 text-rose-800"
                              }`}
                            >
                              {scoreVal} / 100
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${getCategoryBadgeClass(
                                cat
                              )}`}
                            >
                              {getCategoryLabel(cat)}
                            </span>
                          </td>
                          <td className="p-3 text-gray-700 font-medium text-[11px]">
                            {entry.recruiter_recommendation ? (
                              <span className="rounded bg-slate-100 px-2 py-0.5 text-gray-800 font-semibold border border-gray-200">
                                {entry.recruiter_recommendation}
                              </span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="p-3 pr-6 text-right">
                            <button
                              onClick={() =>
                                openExplainability(
                                  entry.candidate_id,
                                  entry.candidate_name,
                                  selectedJobId,
                                  currentJobTitle,
                                  scoreVal,
                                  entry.rank
                                )
                              }
                              className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold text-gray-800 hover:bg-gray-50 shadow-2xs transition"
                            >
                              <span>Inspect</span>
                              <ChevronRight className="h-3 w-3 text-gray-400" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Grounded Evidence Explainability Modal */}
      <FitmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        candidateId={modalCandidateId}
        jobId={modalJobId}
        candidateName={modalCandidateName}
        jobTitle={modalJobTitle}
        compositeScore={modalCompositeScore}
        rankInRole={modalRank}
        data={modalData}
        loading={modalLoading}
      />
    </div>
  );
};
