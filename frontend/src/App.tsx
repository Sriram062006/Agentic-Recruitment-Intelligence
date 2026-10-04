import React, { useState } from "react";
import { Header } from "@/components/common/Header";
import { NavigationShell, NavTab } from "@/components/common/NavigationShell";
import { CandidatePoolView } from "@/views/CandidatePoolView";
import { EvaluationView } from "@/views/EvaluationView";
import { JobManagementView } from "@/views/JobManagementView";
import { WorkspaceView } from "@/views/WorkspaceView";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>("workspace");

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
      <Header />
      <NavigationShell activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="mx-auto max-w-7xl p-6 md:p-8">
        {activeTab === "workspace" && <WorkspaceView />}
        {activeTab === "jobs" && <JobManagementView />}
        {activeTab === "candidates" && <CandidatePoolView />}
        {activeTab === "evaluation" && <EvaluationView />}
      </main>
    </div>
  );
};

export default App;
