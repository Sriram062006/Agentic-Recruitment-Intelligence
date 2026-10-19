import React, { useState, useEffect } from "react";
import {
  Shield,
  Users,
  Briefcase,
  FileText,
  PlayCircle,
  CheckCircle2,
  AlertTriangle,
  Search,
  Filter,
  UserCheck,
  UserX,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import {
  fetchAdminStats,
  fetchAdminUsers,
  updateUserRole,
  updateUserStatus,
} from "../lib/api-client";
import { AdminStatsResponse, AdminUserListItem, UserRole } from "../types/admin.types";

export const AdminView: React.FC = () => {
  const { user, isAdmin, refreshProfile } = useAuth();
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [search, setSearch] = useState<string>("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const loadData = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const [statsData, usersData] = await Promise.all([
        fetchAdminStats(),
        fetchAdminUsers(search || undefined, roleFilter || undefined),
      ]);
      setStats(statsData);
      setUsers(usersData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load admin data";
      setMessage({ text: msg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin, roleFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    setActionLoading(userId);
    setMessage(null);
    try {
      await updateUserRole(userId, newRole);
      setMessage({ text: `Successfully updated user role to ${newRole.toUpperCase()}`, type: "success" });
      await loadData();
      if (userId === user?.id) {
        await refreshProfile();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update role";
      setMessage({ text: msg, type: "error" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: boolean) => {
    const targetStatus = !currentStatus;
    const confirmMsg = targetStatus
      ? "Are you sure you want to reactivate this user account?"
      : "Are you sure you want to deactivate this user account? The user will be blocked from accessing the platform.";
    
    if (!window.confirm(confirmMsg)) return;

    setActionLoading(userId);
    setMessage(null);
    try {
      await updateUserStatus(userId, targetStatus);
      setMessage({
        text: `User account successfully ${targetStatus ? "reactivated" : "deactivated"}`,
        type: "success",
      });
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update account status";
      setMessage({ text: msg, type: "error" });
    } finally {
      setActionLoading(null);
    }
  };

  if (!isAdmin) {
    return (
      <div className="bg-white rounded-xl shadow-xs border border-rose-200 p-8 text-center max-w-2xl mx-auto my-12">
        <div className="w-12 h-12 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-4 text-rose-600">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Access Restricted</h2>
        <p className="text-sm text-gray-600">
          The Administration Panel is strictly reserved for users with the <strong>ADMIN</strong> role. Your current account does not have sufficient permissions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-purple-100 text-purple-700 rounded-lg">
              <Shield className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              System Administration Panel
            </h1>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Platform governance, real-time operational telemetry, and user authorization management.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-xs disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Telemetry
        </button>
      </div>

      {/* Status Messages */}
      {message && (
        <div
          className={`p-4 rounded-lg text-sm flex items-center justify-between border ${
            message.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          <span>{message.text}</span>
          <button
            onClick={() => setMessage(null)}
            className="text-xs underline ml-4 hover:opacity-80"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Platform Overview Metrics */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Platform Operational Metrics
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex items-center justify-between text-gray-500 mb-2">
              <span className="text-xs font-medium">Total Users</span>
              <Users className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats ? stats.total_users : "-"}
            </div>
            <p className="text-[11px] text-gray-500 mt-1">Registered accounts</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex items-center justify-between text-gray-500 mb-2">
              <span className="text-xs font-medium">Active Accounts</span>
              <UserCheck className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats ? stats.active_recruiters : "-"}
            </div>
            <p className="text-[11px] text-emerald-600 font-medium mt-1">Authorized access</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex items-center justify-between text-gray-500 mb-2">
              <span className="text-xs font-medium">Candidate Resumes</span>
              <FileText className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats ? stats.total_candidates : "-"}
            </div>
            <p className="text-[11px] text-gray-500 mt-1">Ingested into pool</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex items-center justify-between text-gray-500 mb-2">
              <span className="text-xs font-medium">Job Descriptions</span>
              <Briefcase className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats ? stats.total_jobs : "-"}
            </div>
            <p className="text-[11px] text-gray-500 mt-1">Active benchmark roles</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex items-center justify-between text-gray-500 mb-2">
              <span className="text-xs font-medium">Evaluation Runs</span>
              <PlayCircle className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats ? stats.total_runs : "-"}
            </div>
            <p className="text-[11px] text-gray-500 mt-1">Historical batch runs</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex items-center justify-between text-gray-500 mb-2">
              <span className="text-xs font-medium">Total Evaluations</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats ? stats.total_evaluations : "-"}
            </div>
            <p className="text-[11px] text-gray-500 mt-1">N × M fitment pairs</p>
          </div>
        </div>
      </div>

      {/* User Management Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-gray-900">User Authorization & Roles</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Manage roles (Admin, Recruiter, Viewer) and activate or suspend platform access.
              </p>
            </div>

            {/* Search and Filters */}
            <div className="flex items-center gap-3">
              <form onSubmit={handleSearchSubmit} className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search name or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 pr-3 py-1.5 border border-gray-300 rounded-lg text-xs w-48 sm:w-64 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </form>

              <div className="flex items-center gap-1 bg-gray-50 border border-gray-300 rounded-lg px-2 py-1.5 text-xs">
                <Filter className="w-3 h-3 text-gray-500" />
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="bg-transparent text-gray-700 font-medium focus:outline-none cursor-pointer"
                >
                  <option value="">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="recruiter">Recruiter</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase font-semibold">
              <tr>
                <th className="py-3 px-6">User / Email</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-center">Candidates</th>
                <th className="py-3 px-4 text-center">Jobs</th>
                <th className="py-3 px-4 text-center">Runs</th>
                <th className="py-3 px-4">Created Date</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500">
                    <div className="w-6 h-6 border-2 border-purple-500/20 border-t-purple-600 rounded-full animate-spin mx-auto mb-2" />
                    Loading system users...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500">
                    No users matching criteria.
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const isSelf = u.user_id === user?.id;
                  const isBusy = actionLoading === u.user_id;

                  return (
                    <tr key={u.user_id} className="hover:bg-gray-50/70 transition">
                      <td className="py-3.5 px-6">
                        <div className="font-semibold text-gray-900">{u.full_name}</div>
                        <div className="text-[11px] text-gray-500">{u.email || "No email"}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <select
                          value={u.role}
                          disabled={isBusy || (isSelf && u.role === "admin")}
                          onChange={(e) => handleRoleChange(u.user_id, e.target.value as UserRole)}
                          className={`font-semibold rounded-md px-2 py-1 text-xs border cursor-pointer focus:outline-none transition ${
                            u.role === "admin"
                              ? "bg-purple-50 text-purple-700 border-purple-200"
                              : u.role === "viewer"
                              ? "bg-amber-50 text-amber-700 border-amber-200"
                              : "bg-indigo-50 text-indigo-700 border-indigo-200"
                          } disabled:opacity-50`}
                        >
                          <option value="admin">Admin</option>
                          <option value="recruiter">Recruiter</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      </td>
                      <td className="py-3.5 px-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-100 text-emerald-800">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-100 text-rose-800">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
                            Deactivated
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-center font-medium text-gray-700">
                        {u.candidates_count ?? 0}
                      </td>
                      <td className="py-3.5 px-4 text-center font-medium text-gray-700">
                        {u.jobs_count ?? 0}
                      </td>
                      <td className="py-3.5 px-4 text-center font-medium text-gray-700">
                        {u.runs_count ?? 0}
                      </td>
                      <td className="py-3.5 px-4 text-gray-500 text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        {isSelf ? (
                          <span className="text-[11px] font-medium text-gray-400 italic">
                            Current Session
                          </span>
                        ) : (
                          <button
                            onClick={() => handleStatusToggle(u.user_id, u.is_active)}
                            disabled={isBusy}
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold transition border ${
                              u.is_active
                                ? "border-rose-200 text-rose-700 bg-rose-50 hover:bg-rose-100"
                                : "border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100"
                            } disabled:opacity-50`}
                          >
                            {u.is_active ? (
                              <>
                                <UserX className="w-3 h-3" />
                                Deactivate
                              </>
                            ) : (
                              <>
                                <UserCheck className="w-3 h-3" />
                                Reactivate
                              </>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
