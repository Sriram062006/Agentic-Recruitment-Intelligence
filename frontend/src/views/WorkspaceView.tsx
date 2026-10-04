import React, { useEffect, useState } from "react";
import { checkBackendHealth } from "@/lib/api-client";
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Server,
  Cpu,
  Database,
  ShieldCheck,
} from "lucide-react";

export const WorkspaceView: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<string>("");

  const verifyConnection = async () => {
    setIsLoading(true);
    const result = await checkBackendHealth();
    setIsConnected(result.connected);
    setBackendStatus(result.statusText);
    setLastChecked(new Date().toLocaleTimeString());
    setIsLoading(false);
  };

  useEffect(() => {
    verifyConnection();
  }, []);

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Foundation Notification Banner */}
        <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
                <ShieldCheck className="h-3.5 w-3.5" />
                Phase 1 Foundation Active
              </div>
              <h2 className="text-xl font-bold text-gray-900">
                Agentic AI Recruitment Intelligence Platform
              </h2>
              <p className="text-sm text-gray-600">
                Core repository structure, backend services, and frontend application shell are initialized and operational.
              </p>
            </div>

            {/* Live Backend Status Badge */}
            <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
              <Server className="h-5 w-5 text-gray-500" />
              <div className="text-left">
                <div className="text-xs font-medium text-gray-500">Backend Status</div>
                <div className="flex items-center gap-1.5 text-sm font-bold">
                  {isLoading ? (
                    <span className="flex items-center gap-1 text-gray-500">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Testing...
                    </span>
                  ) : isConnected ? (
                    <span className="flex items-center gap-1 text-emerald-600">
                      <CheckCircle2 className="h-4 w-4" />
                      Connected
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-rose-600">
                      <XCircle className="h-4 w-4" />
                      {backendStatus}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={verifyConnection}
                disabled={isLoading}
                title="Refresh Backend Health"
                className="ml-2 inline-flex h-8 w-8 items-center justify-center rounded-md border border-gray-200 bg-gray-50 text-gray-600 hover:bg-gray-100 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>
          {lastChecked && (
            <p className="mt-2 text-xs text-gray-400">
              Last health check queried at: {lastChecked} via <code className="text-blue-700">GET /api/health</code>
            </p>
          )}
        </div>

        {/* Foundation Modules Status */}
        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-indigo-50 p-2.5 text-indigo-600">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">FastAPI Backend</h3>
                <p className="text-xs text-gray-500">REST API & App Factory</p>
              </div>
            </div>
            <div className="mt-4 space-y-2 text-xs text-gray-600">
              <div className="flex justify-between border-b pb-1">
                <span>Health Endpoint</span>
                <span className="font-mono text-emerald-600">/api/health (200 OK)</span>
              </div>
              <div className="flex justify-between border-b pb-1">
                <span>OpenAPI Docs</span>
                <span className="font-mono text-gray-700">/docs</span>
              </div>
              <div className="flex justify-between">
                <span>CORS Policy</span>
                <span className="text-gray-700">Local Dev Whitelist</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-50 p-2.5 text-blue-600">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Config & Parameters</h3>
                <p className="text-xs text-gray-500">Pydantic BaseSettings</p>
              </div>
            </div>
            <div className="mt-4 space-y-2 text-xs text-gray-600">
              <div className="flex justify-between border-b pb-1">
                <span>Baseline Weights</span>
                <span className="text-gray-700">35 / 35 / 20 / 10</span>
              </div>
              <div className="flex justify-between border-b pb-1">
                <span>Heuristics (α, β)</span>
                <span className="text-gray-700">0.80 / 1.50 (Configurable)</span>
              </div>
              <div className="flex justify-between">
                <span>Classification Cuts</span>
                <span className="text-gray-700">0.75 / 0.50 (Experimental)</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-teal-50 p-2.5 text-teal-600">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Target Pipeline</h3>
                <p className="text-xs text-gray-500">Multi-Role Research Model</p>
              </div>
            </div>
            <div className="mt-4 space-y-2 text-xs text-gray-600">
              <div className="flex justify-between border-b pb-1">
                <span>Resume Processing</span>
                <span className="text-gray-700">Single Profile / Candidate</span>
              </div>
              <div className="flex justify-between border-b pb-1">
                <span>Multi-Role Eval</span>
                <span className="text-gray-700">Independent Matrix (N × M)</span>
              </div>
              <div className="flex justify-between">
                <span>Numerical Scoring</span>
                <span className="font-medium text-emerald-600">100% Deterministic</span>
              </div>
            </div>
          </div>
        </div>

        {/* Phase Roadmap Progression View */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Implementation Progression</h3>
              <p className="text-xs text-gray-500">Phased research architecture sequence</p>
            </div>
            <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
              Phase 1 of 17
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            <div className="rounded-lg border-2 border-emerald-500 bg-emerald-50/50 p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-900">Phase 1: Project Foundation</span>
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              </div>
              <p className="mt-1 text-xs text-emerald-700">Repository, FastAPI, config, logging, test suite, and Vite shell.</p>
            </div>

            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 opacity-75">
              <span className="text-xs font-bold text-gray-700">Phase 2: Supabase DB + Storage</span>
              <p className="mt-1 text-xs text-gray-500">PostgreSQL DDL, tables, constraints, bucket storage setup.</p>
            </div>

            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 opacity-75">
              <span className="text-xs font-bold text-gray-700">Phase 3: Document Parsing</span>
              <p className="mt-1 text-xs text-gray-500">PyMuPDF and python-docx text extraction engines.</p>
            </div>

            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 opacity-75">
              <span className="text-xs font-bold text-gray-700">Phase 4: LLM Structured Extraction</span>
              <p className="mt-1 text-xs text-gray-500">Gemini Pydantic schema normalization for JDs and resumes.</p>
            </div>

            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 opacity-75">
              <span className="text-xs font-bold text-gray-700">Phase 5: Embeddings & Vector Index</span>
              <p className="mt-1 text-xs text-gray-500">Sentence Transformers (all-MiniLM-L6-v2) & FAISS IndexFlatIP.</p>
            </div>

            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 opacity-75">
              <span className="text-xs font-bold text-gray-700">Phases 6–17: Fitment & Frontend</span>
              <p className="mt-1 text-xs text-gray-500">Multi-role scoring, explainability, matrix views, benchmarks.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
