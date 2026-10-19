import React, { createContext, useContext, useEffect, useState } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { fetchRecruiterProfile } from "../lib/api-client";
import { RecruiterProfile, UserRole } from "../types/admin.types";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: RecruiterProfile | null;
  role: UserRole;
  isActive: boolean;
  isAdmin: boolean;
  isRecruiter: boolean;
  isViewer: boolean;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName: string) => Promise<{ requiresVerification: boolean }>;
  signOut: () => Promise<void>;
  resetPasswordForEmail: (email: string) => Promise<void>;
  updatePassword: (newPassword: string) => Promise<void>;
  refreshProfile: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<RecruiterProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadUserProfile = async (sess: Session | null) => {
    if (!sess) {
      setProfile(null);
      return;
    }
    try {
      const p = await fetchRecruiterProfile();
      setProfile(p);
    } catch (err: unknown) {
      console.warn("Could not fetch recruiter profile from backend:", err);
      // Fallback from JWT metadata if backend not yet reached
      const meta = sess.user.user_metadata || {};
      const fallbackRole: UserRole = (meta.role as UserRole) || "recruiter";
      setProfile({
        user_id: sess.user.id,
        full_name: meta.full_name || sess.user.email?.split("@")[0] || "User",
        email: sess.user.email,
        role: fallbackRole,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
  };

  useEffect(() => {
    // 1. Initial session check & restore
    supabase.auth.getSession().then(async ({ data: { session }, error: sessionError }) => {
      if (sessionError) {
        setError(sessionError.message);
      }
      setSession(session);
      setUser(session?.user ?? null);
      if (session) {
        await loadUserProfile(session);
      }
      setLoading(false);
    });

    // 2. Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session) {
        await loadUserProfile(session);
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const refreshProfile = async () => {
    if (session) {
      await loadUserProfile(session);
    }
  };

  const signIn = async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      if (data.session) {
        await loadUserProfile(data.session);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to sign in";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string, fullName: string) => {
    setError(null);
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            role: "recruiter",
          },
        },
      });
      if (error) throw error;
      const requiresVerification = !data.session;
      if (data.session) {
        await loadUserProfile(data.session);
      }
      return { requiresVerification };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to register account";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setError(null);
    setLoading(true);
    try {
      await supabase.auth.signOut();
      setSession(null);
      setUser(null);
      setProfile(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to sign out";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const resetPasswordForEmail = async (email: string) => {
    setError(null);
    setLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      if (error) throw error;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to send reset email";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updatePassword = async (newPassword: string) => {
    setError(null);
    setLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw error;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update password";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  // Derive roles
  const role: UserRole = profile?.role || (user?.user_metadata?.role as UserRole) || "recruiter";
  const isActive: boolean = profile ? profile.is_active : true;
  const isAdmin = role === "admin";
  const isRecruiter = role === "recruiter";
  const isViewer = role === "viewer";

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        role,
        isActive,
        isAdmin,
        isRecruiter,
        isViewer,
        loading,
        error,
        signIn,
        signUp,
        signOut,
        resetPasswordForEmail,
        updatePassword,
        refreshProfile,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
