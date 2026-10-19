import React, { useEffect, useState } from "react";
import { checkBackendHealth, fetchCandidates, fetchJobs, fetchEvaluationRuns } from "@/lib/api-client";
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Server,
  Users,
  Briefcase,
  Grid3X3,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

export const WorkspaceView: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [candidateCount, setCandidateCount] = useState<number>(0);
  const [jobCount, setJobCount] = useState<number>(0);
  const [runsCount, setRunsCount] = useState<number>(0);
  const [totalEvals, setTotalEvals] = useState<number>(0);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [health, cands, jobs, runs] = await Promise.all([
        checkBackendHealth(),
        fetchCandidates().catch(() => []),
        fetchJobs().catch(() => []),
        fetchEvaluationRuns().catch(() => []),
      ]);

      setIsConnected(health.connected);
      setBackendStatus(health.statusText);

      setCandidateCount(cands.length);
      setJobCount(jobs.length);
      setRunsCount(runs.length);

      const evalsSum = runs.reduce((acc, r) => acc + (r.total_evaluations || 0), 0);
      setTotalEvals(evalsSum);
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Executive Banner */}
        <div className="rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50/90 via-indigo-50/70 to-slate-50 p-6 sm:p-8 shadow-xs">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-800">
                <ShieldCheck className="h-3.5 w-3.5" />
                Enterprise Recruitment Intelligence
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
                Recruitment Intelligence Workspace
              </h1>
              <p className="max-w-2xl text-xs sm:text-sm text-gray-600 leading-relaxed">
                Autonomous talent fitment and multi-role evaluation platform. Grounded, explainable AI matching candidates to requisitions with full source document fidelity.
              </p>
            </div>

            {/* Health & Live Indicator */}
            <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-3.5 shadow-xs">
              <Server className="h-5 w-5 text-gray-400" />
              <div>
                <div className="text-[11px] font-medium text-gray-500">Platform Services</div>
                <div className="flex items-center gap-1.5 text-xs font-bold">
                  {isLoading ? (
                    <span className="flex items-center gap-1 text-gray-400">
                      <RefreshCw className="h-3 w-3 animate-spin" />
                      Checking...
                    </span>
                  ) : isConnected ? (
                    <span className="flex items-center gap-1 text-emerald-600">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Operational
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-rose-600">
                      <XCircle className="h-3.5 w-3.5" />
                      {backendStatus}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={loadDashboardData}
                disabled={isLoading}
                title="Refresh Metrics"
                className="ml-2 inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-600 hover:bg-gray-100 disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Executive Metric Cards */}
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">Candidate Pool</span>
              <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
                <Users className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 text-2xl font-bold text-gray-900">{candidateCount}</div>
            <div className="mt-1 text-[11px] text-gray-500">
              Active profiles indexed for evaluation
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">Job Requisitions</span>
              <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
                <Briefcase className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 text-2xl font-bold text-gray-900">{jobCount}</div>
            <div className="mt-1 text-[11px] text-gray-500">
              Active structured role specifications
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">Evaluation Runs</span>
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
                <Grid3X3 className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 text-2xl font-bold text-gray-900">{runsCount}</div>
            <div className="mt-1 text-[11px] text-gray-500">
              Persistent multi-role evaluation batches
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">Total Evaluations</span>
              <div className="rounded-lg bg-amber-50 p-2 text-amber-600">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 text-2xl font-bold text-gray-900">{totalEvals}</div>
            <div className="mt-1 text-[11px] text-gray-500">
              Evidence-validated fitment assessments
            </div>
          </div>
        </div>

        {/* Intelligence Workflow Highlights */}
        <div className="rounded-2xl border border-gray-200 bg-white p-6 sm:p-8 shadow-xs">
          <div className="mb-6">
            <h2 className="text-base font-bold text-gray-900">Recruitment Intelligence Pipeline</h2>
            <p className="text-xs text-gray-500">End-to-end evidence-grounded candidate evaluation process</p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-4 space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-[11px] font-bold text-white">1</div>
                <span className="text-xs font-bold text-gray-900">Ingest & Structure</span>
              </div>
              <p className="text-[11px] text-gray-600 leading-relaxed">
                Full-fidelity resume extraction preserving career history, verified tenures, overlapping interval normalization, and skills.
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-4 space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-[11px] font-bold text-white">2</div>
                <span className="text-xs font-bold text-gray-900">Define Criteria</span>
              </div>
              <p className="text-[11px] text-gray-600 leading-relaxed">
                Structured Job Descriptions with explicit must-have and should-have competencies, minimum seniority, and key responsibilities.
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-4 space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-600 text-[11px] font-bold text-white">3</div>
                <span className="text-xs font-bold text-gray-900">AI Contextual Fitment</span>
              </div>
              <p className="text-[11px] text-gray-600 leading-relaxed">
                Google Gemini reasoning models evaluate actual candidate profiles against complete requirements with internal score consistency review.
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-4 space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-[11px] font-bold text-white">4</div>
                <span className="text-xs font-bold text-gray-900">Decision Support</span>
              </div>
              <p className="text-[11px] text-gray-600 leading-relaxed">
                Post-LLM evidence validation, missing skills classification, targeted interview verification questions, and persistent audit logs.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
