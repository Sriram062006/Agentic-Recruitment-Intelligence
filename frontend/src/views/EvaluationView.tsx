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
  Sliders,
  Grid3X3,
  ListOrdered,
  AlertCircle,
  ChevronRight,
} from "lucide-react";

export const EvaluationView: React.FC = () => {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [candidates, setCandidates] = useState<CandidateResponse[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [matrixData, setMatrixData] = useState<EvaluationMatrixResponse | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);

  // Configurable Weights & Heuristics
  const [semWeight, setSemWeight] = useState<number>(0.35);
  const [skillWeight, setSkillWeight] = useState<number>(0.35);
  const [expWeight, setExpWeight] = useState<number>(0.20);
  const [qualWeight, setQualWeight] = useState<number>(0.10);
  const [alphaSkill, setAlphaSkill] = useState<number>(0.80);
  const [betaExp, setBetaExp] = useState<number>(1.50);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fitment Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
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

  const handleRunEvaluation = async () => {
    if (jobs.length === 0 || candidates.length === 0) {
      setErrorMsg("Please upload at least 1 Job Description and 1 Candidate Resume first.");
      return;
    }

    const totalWeight = Number((semWeight + skillWeight + expWeight + qualWeight).toFixed(3));
    if (Math.abs(totalWeight - 1.0) > 0.01) {
      setErrorMsg(`Fitment weights must sum to 1.0 (Current sum: ${totalWeight}).`);
      return;
    }

    setIsRunning(true);
    setErrorMsg(null);

    try {
      const run = await createEvaluationRun({
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

      // Fetch leaderboard for default or selected role
      const targetJob = selectedJobId || jobs[0].id;
      const lb = await getRoleLeaderboard(run.id, targetJob);
      setLeaderboard(lb);
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

  return (
    <div className="space-y-8">
      {/* Configuration & Action Card */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Multi-Role Evaluation Setup</h2>
            <p className="text-xs text-gray-500">
              Evaluates {candidates.length} Candidate(s) across {jobs.length} Job(s) ={" "}
              <span className="font-semibold text-blue-600">
                {candidates.length * jobs.length} Evaluations
              </span>
            </p>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={isRunning || jobs.length === 0 || candidates.length === 0}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-blue-700 disabled:opacity-50"
          >
            <PlayCircle className={`h-4 w-4 ${isRunning ? "animate-spin" : ""}`} />
            <span>{isRunning ? "Evaluating Matrix..." : "Run Multi-Role Evaluation"}</span>
          </button>
        </div>

        {errorMsg && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4" />
            {errorMsg}
          </div>
        )}

        {/* Configurable Fitment Weights */}
        <div className="mt-6 border-t pt-5">
          <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-500">
            <Sliders className="h-3.5 w-3.5" />
            Configurable Fitment Weights & Baseline Heuristics
          </div>

          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
            <div>
              <label className="text-[11px] font-semibold text-gray-700">
                Semantic Weight: {semWeight}
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
                Skill Weight: {skillWeight}
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
                Experience Weight: {expWeight}
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
                Qualification Weight: {qualWeight}
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

          <div className="mt-4 grid gap-4 border-t pt-4 sm:grid-cols-2">
            <div>
              <label className="text-[11px] font-semibold text-gray-700">
                Skill Alpha (Required vs Preferred Balance): {alphaSkill}
              </label>
              <input
                type="range"
                min="0.5"
                max="1.0"
                step="0.05"
                value={alphaSkill}
                onChange={(e) => setAlphaSkill(parseFloat(e.target.value))}
                className="mt-1 w-full"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-gray-700">
                Experience Shortfall Penalty (Beta): {betaExp}
              </label>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={betaExp}
                onChange={(e) => setBetaExp(parseFloat(e.target.value))}
                className="mt-1 w-full"
              />
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-gray-500">
            <span className="font-mono text-blue-700">
              Total Weight: {(semWeight + skillWeight + expWeight + qualWeight).toFixed(2)} / 1.00
            </span>
          </div>
        </div>
      </div>

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
                Cross-comparison of all candidates against every job. Click any cell to inspect grounded evidence.
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

                      const pct = Math.round(cell.composite_score * 100);
                      const bgClass =
                        pct >= 75
                          ? "bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100"
                          : pct >= 50
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
                                cell.composite_score,
                                cell.rank_in_role
                              )
                            }
                            className={`w-16 rounded-lg border py-1.5 text-xs font-bold shadow-xs transition ${bgClass}`}
                            title={`Click to inspect explainable fitment for ${cand.name} in ${job.title}`}
                          >
                            {pct}%
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

      {/* Role-Wise Ranked Leaderboard */}
      {activeRunId && jobs.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <ListOrdered className="h-4 w-4 text-blue-600" />
                <h3 className="text-base font-bold text-gray-900">Role-Wise Candidate Leaderboard</h3>
              </div>
              <p className="text-xs text-gray-500">
                Sorted ranking and deterministic score breakdowns for a selected job role.
              </p>
            </div>

            {/* Role Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-600">Selected Role:</span>
              <select
                value={selectedJobId}
                onChange={(e) => handleJobSelect(e.target.value)}
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-bold text-gray-800 outline-none focus:border-blue-500"
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.structured_profile.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {leaderboard.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-500">
              No candidates ranked for this role yet.
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-gray-200">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b bg-gray-50/80 font-bold text-gray-600">
                    <th className="p-3 pl-6">Rank</th>
                    <th className="p-3">Candidate</th>
                    <th className="p-3">Verified Tenure</th>
                    <th className="p-3">Composite Score</th>
                    <th className="p-3">Sub-Score Breakdown</th>
                    <th className="p-3 pr-6 text-right">Explainability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-gray-700">
                  {leaderboard.map((entry) => {
                    const pct = Math.round(entry.composite_score * 100);
                    const currentJobTitle =
                      jobs.find((j) => j.id === selectedJobId)?.structured_profile.title || "Job";

                    return (
                      <tr key={entry.candidate_id} className="hover:bg-slate-50/50">
                        <td className="p-3 pl-6 font-bold text-gray-900">
                          <span
                            className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
                              entry.rank === 1
                                ? "bg-amber-100 text-amber-800"
                                : entry.rank === 2
                                ? "bg-slate-200 text-slate-700"
                                : entry.rank === 3
                                ? "bg-orange-100 text-orange-800"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            #{entry.rank}
                          </span>
                        </td>
                        <td className="p-3 font-semibold text-gray-900">
                          {entry.candidate_name}
                        </td>
                        <td className="p-3 text-gray-600">
                          {entry.total_experience_years} yrs • {entry.highest_qualification}
                        </td>
                        <td className="p-3">
                          <span
                            className={`rounded-md px-2 py-0.5 text-xs font-extrabold ${
                              pct >= 75
                                ? "bg-emerald-100 text-emerald-800"
                                : pct >= 50
                                ? "bg-amber-100 text-amber-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {pct}%
                          </span>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-2 text-[10px] text-gray-500">
                            <span>Sem: {Math.round(entry.semantic_score * 100)}%</span>
                            <span>•</span>
                            <span>Skill: {Math.round(entry.skill_score * 100)}%</span>
                            <span>•</span>
                            <span>Exp: {Math.round(entry.experience_score * 100)}%</span>
                            <span>•</span>
                            <span>Qual: {Math.round(entry.qualification_score * 100)}%</span>
                          </div>
                        </td>
                        <td className="p-3 pr-6 text-right">
                          <button
                            onClick={() =>
                              openExplainability(
                                entry.candidate_id,
                                entry.candidate_name,
                                selectedJobId,
                                currentJobTitle,
                                entry.composite_score,
                                entry.rank
                              )
                            }
                            className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold text-gray-800 hover:bg-gray-50"
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
      )}

      {/* Grounded Evidence Explainability Modal */}
      <FitmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
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
