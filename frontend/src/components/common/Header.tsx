import React from "react";
import { Sparkles, Database, User, LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export const Header: React.FC = () => {
  const { user, signOut } = useAuth();
  const recruiterName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Recruiter";
  const role = user?.user_metadata?.role || "recruiter";

  return (
    <header className="border-b border-border bg-white px-6 py-4 shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md">
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

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
            <Database className="h-3.5 w-3.5 text-emerald-600" />
            <span className="font-medium">Supabase PostgreSQL • RLS Active</span>
          </div>

          {user && (
            <div className="flex items-center space-x-3 pl-2 border-l border-gray-200">
              <div className="flex items-center space-x-2 text-xs">
                <div className="w-7 h-7 rounded-full bg-indigo-100 border border-indigo-200 flex items-center justify-center text-indigo-700 font-semibold">
                  <User className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-gray-800 leading-none">{recruiterName}</div>
                  <div className="text-[10px] text-gray-400 capitalize mt-0.5">{role}</div>
                </div>
              </div>

              <button
                onClick={() => signOut()}
                title="Sign Out"
                className="p-1.5 rounded-lg text-gray-400 hover:text-rose-600 hover:bg-rose-50 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
