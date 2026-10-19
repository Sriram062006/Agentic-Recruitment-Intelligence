import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Header } from "@/components/common/Header";
import { NavigationShell, NavTab } from "@/components/common/NavigationShell";
import { CandidatePoolView } from "@/views/CandidatePoolView";
import { EvaluationView } from "@/views/EvaluationView";
import { JobManagementView } from "@/views/JobManagementView";
import { WorkspaceView } from "@/views/WorkspaceView";
import { EvaluationHistoryView } from "@/views/EvaluationHistoryView";
import { AdminView } from "@/views/AdminView";
import { LoginView } from "@/views/auth/LoginView";
import { RegisterView } from "@/views/auth/RegisterView";
import { ForgotPasswordView } from "@/views/auth/ForgotPasswordView";
import { ResetPasswordView } from "@/views/auth/ResetPasswordView";
import { AlertTriangle, LogOut } from "lucide-react";

type AuthScreen = "login" | "register" | "forgot_password" | "reset_password";

const MainApp: React.FC = () => {
  const { user, isActive, loading, signOut } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>("candidates");
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
        <p className="text-sm font-medium text-slate-400">Restoring Platform Session...</p>
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

  // Handle deactivated account state
  if (!isActive) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
        <div className="bg-white max-w-md w-full rounded-2xl p-8 border border-rose-200 shadow-xl text-center">
          <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Account Deactivated</h2>
          <p className="text-sm text-gray-600 mb-6">
            Your platform access has been suspended by an administrator. Please reach out to your system administrator for assistance.
          </p>
          <button
            onClick={() => signOut()}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs text-white bg-gray-900 hover:bg-gray-800 transition"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  // Authenticated Recruiter / Admin / Viewer Workspace
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
      <Header />
      <NavigationShell activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="mx-auto max-w-7xl p-6 md:p-8">
        {activeTab === "workspace" && <WorkspaceView />}
        {activeTab === "jobs" && <JobManagementView />}
        {activeTab === "candidates" && <CandidatePoolView />}
        {activeTab === "evaluation" && <EvaluationView />}
        {activeTab === "history" && <EvaluationHistoryView />}
        {activeTab === "admin" && <AdminView />}
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
