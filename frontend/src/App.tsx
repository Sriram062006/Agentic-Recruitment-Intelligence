import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Header } from "@/components/common/Header";
import { NavigationShell, NavTab } from "@/components/common/NavigationShell";
import { CandidatePoolView } from "@/views/CandidatePoolView";
import { EvaluationView } from "@/views/EvaluationView";
import { JobManagementView } from "@/views/JobManagementView";
import { WorkspaceView } from "@/views/WorkspaceView";
import { LoginView } from "@/views/auth/LoginView";
import { RegisterView } from "@/views/auth/RegisterView";
import { ForgotPasswordView } from "@/views/auth/ForgotPasswordView";
import { ResetPasswordView } from "@/views/auth/ResetPasswordView";

type AuthScreen = "login" | "register" | "forgot_password" | "reset_password";

const MainApp: React.FC = () => {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>("workspace");
  const [authScreen, setAuthScreen] = useState<AuthScreen>("login");

  // Detect password reset flow from URL hash
  useEffect(() => {
    if (window.location.hash.includes("type=recovery") || window.location.pathname === "/reset-password") {
      setAuthScreen("reset_password");
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100">
        <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-400">Restoring Recruiter Session...</p>
      </div>
    );
  }

  // Handle unauthenticated state with dedicated auth flows
  if (!user) {
    if (authScreen === "register") {
      return <RegisterView onNavigateToLogin={() => setAuthScreen("login")} />;
    }
    if (authScreen === "forgot_password") {
      return <ForgotPasswordView onNavigateToLogin={() => setAuthScreen("login")} />;
    }
    if (authScreen === "reset_password") {
      return <ResetPasswordView onSuccess={() => setAuthScreen("login")} />;
    }
    return (
      <LoginView
        onNavigateToRegister={() => setAuthScreen("register")}
        onNavigateToForgotPassword={() => setAuthScreen("forgot_password")}
      />
    );
  }

  // Authenticated Recruiter Workspace
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

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};

export default App;
