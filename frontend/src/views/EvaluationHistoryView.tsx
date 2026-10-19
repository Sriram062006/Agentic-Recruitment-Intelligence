import React, { useState, useEffect } from "react";
import {
  History,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowLeft,
  Grid3X3,
  Award,
  Sliders,
  RefreshCw,
  Copy,
  Check,
} from "lucide-react";
import {
  fetchEvaluationRuns,
  getEvaluationMatrix,
  getRoleLeaderboard,
  getExplainability,
} from "../lib/api-client";
import {
  EvaluationRunResponse,
  EvaluationMatrixResponse,
  LeaderboardEntry,
  ExplainabilityPayload,
  MatrixCell,
} from "../types/evaluation.types";
import { FitmentModal } from "../components/explainability/FitmentModal";

export const EvaluationHistoryView: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Active / Reopened run inspection state
  const [selectedRun, setSelectedRun] = useState<EvaluationRunResponse | null>(null);
  const [matrixData, setMatrixData] = useState<EvaluationMatrixResponse | null>(null);
  const [matrixLoading, setMatrixLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"matrix" | "rankings">("matrix");
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [leaderboardLoading, setLeaderboardLoading] = useState<boolean>(false);

  // Explainability modal state
  const [selectedCandRole, setSelectedCandRole] = useState<{
    candidateId: string;
    candidateName: string;
    jobId: string;
    jobTitle: string;
    compositeScore: number;
    rankInRole?: number;
  } | null>(null);
  const [explainData, setExplainData] = useState<ExplainabilityPayload | null>(null);
  const [explainLoading, setExplainLoading] = useState<boolean>(false);

  const loadRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvaluationRuns(statusFilter || undefined);
      setRuns(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load evaluation runs";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, [statusFilter]);

  const handleCopyId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleOpenRun = async (run: EvaluationRunResponse) => {
    setSelectedRun(run);
    setMatrixLoading(true);
    setError(null);
    try {
      const mData = await getEvaluationMatrix(run.id);
      setMatrixData(mData);
      if (mData.jobs.length > 0) {
        setSelectedJobId(mData.jobs[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load evaluation matrix for run";
      setError(msg);
    } finally {
      setMatrixLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRun && selectedJobId && activeTab === "rankings") {
      setLeaderboardLoading(true);
      getRoleLeaderboard(selectedRun.id, selectedJobId)
        .then((data) => setLeaderboard(data))
        .catch((err) => console.error("Error loading role leaderboard:", err))
        .finally(() => setLeaderboardLoading(false));
    }
  }, [selectedRun, selectedJobId, activeTab]);

  const handleCellClick = async (cell: MatrixCell) => {
    if (!selectedRun || !matrixData) return;
    const cand = matrixData.candidates.find((c) => c.id === cell.candidate_id);
    const job = matrixData.jobs.find((j) => j.id === cell.job_id);
    if (!cand || !job) return;

    setSelectedCandRole({
      candidateId: cell.candidate_id,
      candidateName: cand.name,
      jobId: cell.job_id,
      jobTitle: job.title,
      compositeScore: cell.composite_score,
      rankInRole: cell.rank_in_role,
    });
    setExplainLoading(true);
    try {
      const res = await getExplainability(selectedRun.id, cell.candidate_id, cell.job_id);
      setExplainData(res);
    } catch (err) {
      console.error("Failed to load explainability:", err);
    } finally {
      setExplainLoading(false);
    }
  };

  const handleLeaderboardCandidateClick = async (entry: LeaderboardEntry) => {
    if (!selectedRun || !matrixData || !selectedJobId) return;
    const job = matrixData.jobs.find((j) => j.id === selectedJobId);
    if (!job) return;

    setSelectedCandRole({
      candidateId: entry.candidate_id,
      candidateName: entry.candidate_name,
      jobId: selectedJobId,
      jobTitle: job.title,
      compositeScore: entry.composite_score,
      rankInRole: entry.rank,
    });
    setExplainLoading(true);
    try {
      const res = await getExplainability(selectedRun.id, entry.candidate_id, selectedJobId);
      setExplainData(res);
    } catch (err) {
      console.error("Failed to load explainability:", err);
    } finally {
      setExplainLoading(false);
    }
  };

  const filteredRuns = runs.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.id.toLowerCase().includes(q) ||
      (r.status && r.status.toLowerCase().includes(q))
    );
  });

  // ==========================================
  // DETAIL / REOPENED RUN VIEW
  // ==========================================
  if (selectedRun) {
    const weights = selectedRun.config?.weights || {};
    const heuristics = selectedRun.config?.heuristics || {};

    return (
      <div className="space-y-6">
        {/* Back Navigation Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 pb-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedRun(null)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Run Directory
            </button>
            <div className="h-5 w-px bg-gray-300" />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-gray-900">
                  Run #{selectedRun.id.slice(0, 8)}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                  {selectedRun.status}
                </span>
              </div>
              <p className="text-[11px] text-gray-500">
                Executed: {new Date(selectedRun.started_at).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
            <span className="font-medium text-gray-900">{selectedRun.total_candidates}</span> candidates ×{" "}
            <span className="font-medium text-gray-900">{selectedRun.total_jobs}</span> roles ={" "}
            <span className="font-bold text-indigo-600">{selectedRun.total_evaluations}</span> evaluations
          </div>
        </div>

        {/* Frozen Configuration Snapshot Banner */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            <Sliders className="w-3.5 h-3.5 text-indigo-600" />
            Immutable Scoring Snapshot Parameters
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 text-xs">
            <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <span className="text-[10px] text-gray-500 uppercase block">Semantic Weight</span>
              <span className="font-mono font-bold text-gray-800">
                w_sem = {weights.semantic_weight ?? 0.35}
              </span>
            </div>
            <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <span className="text-[10px] text-gray-500 uppercase block">Skill Weight</span>
              <span className="font-mono font-bold text-gray-800">
                w_skill = {weights.skill_weight ?? 0.35}
              </span>
            </div>
            <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <span className="text-[10px] text-gray-500 uppercase block">Experience Weight</span>
              <span className="font-mono font-bold text-gray-800">
                w_exp = {weights.experience_weight ?? 0.20}
              </span>
            </div>
            <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <span className="text-[10px] text-gray-500 uppercase block">Qualification Weight</span>
              <span className="font-mono font-bold text-gray-800">
                w_qual = {weights.qualification_weight ?? 0.10}
              </span>
            </div>
            <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <span className="text-[10px] text-gray-500 uppercase block">Alpha (Req/Pref)</span>
              <span className="font-mono font-bold text-gray-800">
                α = {heuristics.alpha_skill_weight ?? 0.80}
              </span>
            </div>
            <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <span className="text-[10px] text-gray-500 uppercase block">Beta (Tenure Penalty)</span>
              <span className="font-mono font-bold text-gray-800">
                β = {heuristics.beta_experience_penalty ?? 1.50}
              </span>
            </div>
          </div>
        </div>

        {/* View Selection Tabs */}
        <div className="flex items-center justify-between border-b border-gray-200">
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab("matrix")}
              className={`flex items-center gap-2 border-b-2 py-3 px-1 text-xs font-semibold transition ${
                activeTab === "matrix"
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <Grid3X3 className="w-4 h-4" />
              N × M Multi-Role Matrix Grid
            </button>
            <button
              onClick={() => setActiveTab("rankings")}
              className={`flex items-center gap-2 border-b-2 py-3 px-1 text-xs font-semibold transition ${
                activeTab === "rankings"
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <Award className="w-4 h-4" />
              Role-Wise Ranked Leaderboards
            </button>
          </div>

          {activeTab === "rankings" && matrixData && matrixData.jobs.length > 0 && (
            <div className="flex items-center gap-2 pb-2">
              <span className="text-xs text-gray-500 font-medium">Select Role:</span>
              <select
                value={selectedJobId || ""}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="bg-white border border-gray-300 rounded-lg px-2.5 py-1 text-xs font-semibold text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {matrixData.jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Matrix Tab Content */}
        {activeTab === "matrix" && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden">
            {matrixLoading ? (
              <div className="p-12 text-center text-gray-500">
                <div className="w-8 h-8 border-3 border-indigo-500/20 border-t-indigo-600 rounded-full animate-spin mx-auto mb-3" />
                <p className="text-xs font-medium">Retrieving stored evaluation matrix snapshot...</p>
              </div>
            ) : !matrixData || matrixData.cells.length === 0 ? (
              <div className="p-12 text-center text-gray-500 text-xs">
                No matrix cells stored for this evaluation run.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-xs">
                  <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase font-semibold">
                    <tr>
                      <th className="py-3 px-6 sticky left-0 bg-gray-50 z-10 border-r border-gray-200">
                        Candidate Name
                      </th>
                      {matrixData.jobs.map((job) => (
                        <th key={job.id} className="py-3 px-4 text-center min-w-[140px]">
                          {job.title}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {matrixData.candidates.map((cand) => (
                      <tr key={cand.id} className="hover:bg-gray-50/70 transition">
                        <td className="py-3 px-6 font-semibold text-gray-900 sticky left-0 bg-white border-r border-gray-200">
                          {cand.name}
                        </td>
                        {matrixData.jobs.map((job) => {
                          const cell = matrixData.cells.find(
                            (c) => c.candidate_id === cand.id && c.job_id === job.id
                          );
                          if (!cell) {
                            return (
                              <td key={job.id} className="py-3 px-4 text-center text-gray-300">
                                -
                              </td>
                            );
                          }
                          const scorePct = Math.round(cell.composite_score * 100);
                          const badgeColor =
                            scorePct >= 75
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                              : scorePct >= 50
                              ? "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
                              : "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100";

                          return (
                            <td key={job.id} className="py-2.5 px-3 text-center">
                              <button
                                onClick={() => handleCellClick(cell)}
                                title="Click to view explainable fitment breakdown"
                                className={`inline-flex flex-col items-center justify-center w-full py-1.5 px-2 rounded-lg border text-xs font-semibold transition cursor-pointer shadow-xs ${badgeColor}`}
                              >
                                <span>{scorePct}%</span>
                                <span className="text-[10px] font-normal opacity-80">
                                  Rank #{cell.rank_in_role}
                                </span>
                              </button>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Leaderboard Tab Content */}
        {activeTab === "rankings" && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden">
            {leaderboardLoading ? (
              <div className="p-12 text-center text-gray-500">
                <div className="w-8 h-8 border-3 border-indigo-500/20 border-t-indigo-600 rounded-full animate-spin mx-auto mb-3" />
                <p className="text-xs font-medium">Loading ranked role leaderboard...</p>
              </div>
            ) : leaderboard.length === 0 ? (
              <div className="p-12 text-center text-gray-500 text-xs">
                No candidates evaluated for this role.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase font-semibold">
                    <tr>
                      <th className="py-3 px-6 text-center w-16">Rank</th>
                      <th className="py-3 px-6">Candidate</th>
                      <th className="py-3 px-4 text-center">Composite Fitment</th>
                      <th className="py-3 px-4 text-center">Semantic Sim</th>
                      <th className="py-3 px-4 text-center">Skills Score</th>
                      <th className="py-3 px-4 text-center">Experience Fit</th>
                      <th className="py-3 px-4 text-center">Matched Skills</th>
                      <th className="py-3 px-6 text-right">Inspection</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {leaderboard.map((item) => {
                      const scorePct = Math.round(item.composite_score * 100);
                      return (
                        <tr key={item.candidate_id} className="hover:bg-gray-50/70 transition">
                          <td className="py-3.5 px-6 text-center">
                            <span
                              className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-bold text-xs ${
                                item.rank === 1
                                  ? "bg-amber-100 text-amber-800 border border-amber-300"
                                  : item.rank === 2
                                  ? "bg-slate-200 text-slate-800"
                                  : item.rank === 3
                                  ? "bg-amber-50 text-amber-900"
                                  : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              {item.rank}
                            </span>
                          </td>
                          <td className="py-3.5 px-6">
                            <div className="font-semibold text-gray-900">{item.candidate_name}</div>
                            <div className="text-[11px] text-gray-500">
                              {item.total_experience_years} yrs exp • {item.highest_qualification}
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <span
                              className={`inline-block px-2.5 py-1 rounded-md font-bold text-xs ${
                                scorePct >= 75
                                  ? "bg-emerald-100 text-emerald-800"
                                  : scorePct >= 50
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-rose-100 text-rose-800"
                              }`}
                            >
                              {scorePct}%
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-center font-mono text-gray-700">
                            {item.semantic_score.toFixed(2)}
                          </td>
                          <td className="py-3.5 px-4 text-center font-mono text-gray-700">
                            {item.skill_score.toFixed(2)}
                          </td>
                          <td className="py-3.5 px-4 text-center font-mono text-gray-700">
                            {item.experience_score.toFixed(2)}
                          </td>
                          <td className="py-3.5 px-4 text-center text-gray-700">
                            <span className="text-emerald-700 font-semibold">
                              {item.matched_skills_count}
                            </span>
                            <span className="text-gray-400 mx-1">/</span>
                            <span className="text-rose-600">
                              {item.missing_skills_count}
                            </span>
                          </td>
                          <td className="py-3.5 px-6 text-right">
                            <button
                              onClick={() => handleLeaderboardCandidateClick(item)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-gray-300 text-[11px] font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-xs"
                            >
                              <Eye className="w-3 h-3 text-indigo-600" />
                              Inspect Fitment
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
        )}

        {/* Reused Fitment Modal */}
        {selectedCandRole && (
          <FitmentModal
            isOpen={!!selectedCandRole}
            onClose={() => setSelectedCandRole(null)}
            candidateName={selectedCandRole.candidateName}
            jobTitle={selectedCandRole.jobTitle}
            compositeScore={selectedCandRole.compositeScore}
            rankInRole={selectedCandRole.rankInRole}
            data={explainData}
            loading={explainLoading}
          />
        )}
      </div>
    );
  }

  // ==========================================
  // RUN DIRECTORY VIEW
  // ==========================================
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
              <History className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              Evaluation Runs History
            </h1>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Audit trail of historical multi-role evaluations, frozen scoring snapshots, and reproducible rankings.
          </p>
        </div>

        <button
          onClick={loadRuns}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-xs disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh History
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search and Status Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search Run ID or status..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-3 py-1.5 border border-gray-300 rounded-lg text-xs w-64 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <div className="flex items-center gap-1 bg-gray-50 border border-gray-300 rounded-lg px-2.5 py-1.5 text-xs">
          <Filter className="w-3 h-3 text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-transparent text-gray-700 font-medium focus:outline-none cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Runs Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase font-semibold">
              <tr>
                <th className="py-3 px-6">Run Identifier</th>
                <th className="py-3 px-4">Executed Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-center">Candidates (N)</th>
                <th className="py-3 px-4 text-center">Roles (M)</th>
                <th className="py-3 px-4 text-center">Evaluations (N×M)</th>
                <th className="py-3 px-4">Snapshot Weights</th>
                <th className="py-3 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500">
                    <div className="w-6 h-6 border-2 border-indigo-500/20 border-t-indigo-600 rounded-full animate-spin mx-auto mb-2" />
                    Loading historical evaluation runs...
                  </td>
                </tr>
              ) : filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500">
                    No historical evaluation runs recorded yet.
                  </td>
                </tr>
              ) : (
                filteredRuns.map((run) => {
                  const weights = run.config?.weights || {};
                  return (
                    <tr
                      key={run.id}
                      onClick={() => handleOpenRun(run)}
                      className="hover:bg-indigo-50/40 cursor-pointer transition"
                    >
                      <td className="py-3.5 px-6">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-gray-900">
                            #{run.id.slice(0, 8)}
                          </span>
                          <button
                            onClick={(e) => handleCopyId(run.id, e)}
                            title="Copy full Run UUID"
                            className="p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
                          >
                            {copiedId === run.id ? (
                              <Check className="w-3 h-3 text-emerald-600" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-gray-600">
                        <div className="font-medium text-gray-800">
                          {new Date(run.started_at).toLocaleDateString()}
                        </div>
                        <div className="text-[10px] text-gray-400">
                          {new Date(run.started_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            run.status === "COMPLETED"
                              ? "bg-emerald-100 text-emerald-800"
                              : run.status === "FAILED"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {run.status === "COMPLETED" ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : run.status === "FAILED" ? (
                            <AlertCircle className="w-3 h-3" />
                          ) : (
                            <Clock className="w-3 h-3" />
                          )}
                          {run.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center font-semibold text-gray-800">
                        {run.total_candidates}
                      </td>
                      <td className="py-3.5 px-4 text-center font-semibold text-gray-800">
                        {run.total_jobs}
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold text-indigo-600">
                        {run.total_evaluations}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="text-[11px] font-mono text-gray-600 space-x-1">
                          <span>sem:{weights.semantic_weight ?? 0.35}</span>
                          <span>skl:{weights.skill_weight ?? 0.35}</span>
                          <span>exp:{weights.experience_weight ?? 0.2}</span>
                          <span>ql:{weights.qualification_weight ?? 0.1}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        <button
                          onClick={() => handleOpenRun(run)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-indigo-200 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition shadow-xs"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Open Run
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
