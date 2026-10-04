import React from "react";
import { Header } from "@/components/common/Header";
import { NavigationShell } from "@/components/common/NavigationShell";
import { WorkspaceView } from "@/views/WorkspaceView";

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
      <Header />
      <NavigationShell />
      <main>
        <WorkspaceView />
      </main>
    </div>
  );
};

export default App;
