import React from "react";
import { Sparkles, Terminal } from "lucide-react";

export const Header: React.FC = () => {
  return (
    <header className="border-b border-border bg-white px-6 py-4 shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white shadow-md">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-gray-900">
              Agentic AI Recruitment Intelligence Platform
            </h1>
            <p className="text-xs text-gray-500">
              Academic Research Prototype • Multi-Role Candidate Evaluation
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-600">
          <Terminal className="h-3.5 w-3.5 text-blue-600" />
          <span className="font-medium">Phase 1: Project Foundation</span>
        </div>
      </div>
    </header>
  );
};
