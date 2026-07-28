"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Area, AreaChart,
} from "recharts";
import {
  Users, TrendingUp, Target, MessageSquare, Layers,
  Shield, Crown, Trash2, Eye, ChevronDown, ChevronUp,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";

type Tab = "overview" | "users" | "moderation";

type AdminUser = {
  id: string;
  email: string;
  is_admin: boolean;
  [key: string]: unknown;
};

export default function AdminPage() {
  const { user } = useAuthStore();
  const [tab, setTab] = useState<Tab>("overview");

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-gray-400">Admin access required.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="mb-6 flex items-center gap-3">
          <Shield className="h-6 w-6 text-[#00D4AA]" />
          <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-1 rounded-lg bg-[#0A1628] p-1 border border-gray-800 w-fit">
          {(["overview", "users", "moderation"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                tab === t ? "bg-[#1A2942] text-white" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {tab === "overview" && <OverviewTab />}
        {tab === "users" && <UsersTab />}
        {tab === "moderation" && <ModerationTab />}
      </motion.div>
    </div>
  );
}

// ============================================================================
// Overview Tab
// ============================================================================

function OverviewTab() {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["admin-overview"],
    queryFn: () => api.get<Record<string, unknown>>("/admin/dashboard/overview"),
  });

  const { data: growth } = useQuery({
    queryKey: ["admin-growth"],
    queryFn: () => api.get<{ date: string; new: number; total: number }[]>("/admin/dashboard/charts/user-growth?days=90"),
  });

  const { data: predictions } = useQuery({
    queryKey: ["admin-predictions"],
    queryFn: () => api.get<{ date: string; count: number }[]>("/admin/dashboard/charts/prediction-activity?days=30"),
  });

  const { data: featureUsage } = useQuery({
    queryKey: ["admin-features"],
    queryFn: () => api.get<{ event: string; count: number }[]>("/admin/dashboard/charts/feature-usage?days=30"),
  });

  const { data: calibrationDist } = useQuery({
    queryKey: ["admin-calibration-dist"],
    queryFn: () => api.get<{ range: string; count: number }[]>("/admin/dashboard/charts/calibration-distribution"),
  });

  const { data: funnel } = useQuery({
    queryKey: ["admin-funnel"],
    queryFn: () => api.get<{ stage: string; count: number }[]>("/admin/dashboard/charts/conversion-funnel"),
  });

  const o = overview as Record<string, unknown> | undefined;
  const activity = o?.activity_30d as Record<string, number> | undefined;

  if (overviewLoading) {
    return <div className="space-y-4">{[1, 2, 3].map(i => <div key={i} className="h-24 skeleton-shimmer rounded-xl" />)}</div>;
  }

  const stats = [
    { label: "Total Users", value: o?.total_users ?? 0, icon: Users },
    { label: "Pro Users", value: o?.pro_users ?? 0, icon: Crown },
    { label: "This Week", value: `+${o?.signups_7d ?? 0}`, icon: TrendingUp },
    { label: "Onboarding Rate", value: `${o?.onboarding_completion_rate ?? 0}%`, icon: Target },
    { label: "Predictions (30d)", value: activity?.predictions ?? 0, icon: Target },
    { label: "Chat Messages (30d)", value: activity?.chat_messages ?? 0, icon: MessageSquare },
  ];

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-xl border border-gray-800 bg-[#111827] p-4"
          >
            <div className="flex items-center gap-2 mb-1">
              <s.icon className="h-4 w-4 text-gray-400" />
              <p className="text-xs text-gray-400">{s.label}</p>
            </div>
            <p className="text-2xl font-bold font-mono-nums text-white">{String(s.value)}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* User Growth */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <h3 className="mb-4 font-semibold text-white">User Growth (90 days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={growth || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="date" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 10 }} tickLine={false} interval={14} />
                <YAxis stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={({ active, payload }) => {
                  if (active && payload?.length) {
                    return (
                      <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                        <p className="text-gray-400">{payload[0]?.payload?.date}</p>
                        <p className="text-[#00D4AA]">Total: {payload[0]?.payload?.total}</p>
                        <p className="text-[#3B82F6]">New: +{payload[0]?.payload?.new}</p>
                      </div>
                    );
                  }
                  return null;
                }} />
                <Area type="monotone" dataKey="total" stroke="#00D4AA" fill="#00D4AA" fillOpacity={0.1} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Prediction Activity */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <h3 className="mb-4 font-semibold text-white">Prediction Activity (30 days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={predictions || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="date" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 10 }} tickLine={false} interval={6} />
                <YAxis stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={({ active, payload }) => {
                  if (active && payload?.length) {
                    return (
                      <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                        <p className="text-[#00D4AA]">{payload[0]?.value} predictions</p>
                      </div>
                    );
                  }
                  return null;
                }} />
                <Bar dataKey="count" fill="#00D4AA" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Feature Usage */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <h3 className="mb-4 font-semibold text-white">Feature Usage (30 days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureUsage || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis type="number" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="event" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 11 }} tickLine={false} axisLine={false} width={100} />
                <Tooltip content={({ active, payload }) => {
                  if (active && payload?.length) {
                    return (
                      <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                        <p className="text-[#00D4AA]">{payload[0]?.value} events</p>
                      </div>
                    );
                  }
                  return null;
                }} />
                <Bar dataKey="count" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Conversion Funnel */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <h3 className="mb-4 font-semibold text-white">Conversion Funnel</h3>
          <div className="space-y-3">
            {(funnel || []).map((stage, i) => {
              const maxCount = funnel?.[0]?.count || 1;
              const pct = Math.round((stage.count / maxCount) * 100);
              return (
                <div key={stage.stage}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-300">{stage.stage}</span>
                    <span className="text-sm font-mono-nums text-[#00D4AA]">{stage.count}</span>
                  </div>
                  <div className="h-3 rounded-full bg-gray-800">
                    <div
                      className="h-3 rounded-full bg-[#00D4AA] transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Calibration Distribution */}
      {calibrationDist && calibrationDist.some((d: { count: number }) => d.count > 0) && (
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <h3 className="mb-4 font-semibold text-white">Calibration Score Distribution</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={calibrationDist}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="range" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} />
                <YAxis stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                <Bar dataKey="count" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Users Tab
// ============================================================================

function UsersTab() {
  const queryClient = useQueryClient();
  const { data: users, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get<AdminUser[]>("/admin/dashboard/users"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.patch(`/admin/dashboard/users/${id}`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/dashboard/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-overview"] });
    },
  });

  if (isLoading) return <div className="h-64 skeleton-shimmer rounded-xl" />;

  return (
    <div className="rounded-xl border border-gray-800 bg-[#111827] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              <th className="p-4 text-left font-medium">Email</th>
              <th className="p-4 text-left font-medium">Tier</th>
              <th className="p-4 text-left font-medium">Persona</th>
              <th className="p-4 text-right font-medium">Predictions</th>
              <th className="p-4 text-right font-medium">Cal. Score</th>
              <th className="p-4 text-right font-medium">Joined</th>
              <th className="p-4 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(users || []).map((u) => (
              <tr key={u.id as string} className="border-b border-gray-800/50 hover:bg-[#1A2942]/30">
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <span className="text-white">{u.email}</span>
                    {u.is_admin && (
                      <span className="rounded-full bg-[#00D4AA]/20 px-1.5 py-0.5 text-[10px] font-semibold text-[#00D4AA]">ADMIN</span>
                    )}
                  </div>
                </td>
                <td className="p-4">
                  <button
                    onClick={() => updateMutation.mutate({
                      id: u.id as string,
                      data: { tier: u.tier === "pro" ? "free" : "pro" },
                    })}
                    className={`rounded-md px-2 py-0.5 text-xs font-medium border ${
                      u.tier === "pro"
                        ? "bg-[#00D4AA]/20 text-[#00D4AA] border-[#00D4AA]/30"
                        : "bg-gray-800 text-gray-400 border-gray-700"
                    } hover:opacity-80 transition-opacity`}
                  >
                    {(u.tier as string).toUpperCase()}
                  </button>
                </td>
                <td className="p-4 text-gray-400">{(u.persona as string) || "—"}</td>
                <td className="p-4 text-right font-mono-nums text-white">{u.prediction_count as number}</td>
                <td className="p-4 text-right font-mono-nums text-[#00D4AA]">
                  {u.calibration_score !== null ? u.calibration_score as number : "—"}
                </td>
                <td className="p-4 text-right text-gray-400">
                  {u.created_at ? new Date(u.created_at as string).toLocaleDateString() : "—"}
                </td>
                <td className="p-4 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => updateMutation.mutate({
                        id: u.id as string,
                        data: { is_admin: !u.is_admin },
                      })}
                      title={u.is_admin ? "Remove admin" : "Make admin"}
                      className="rounded p-1.5 text-gray-400 hover:bg-[#1A2942] hover:text-white"
                    >
                      <Shield className="h-3.5 w-3.5" />
                    </button>
                    {!u.is_admin && (
                      <button
                        onClick={() => {
                          if (confirm(`Delete ${u.email}? This cannot be undone.`)) {
                            deleteMutation.mutate(u.id as string);
                          }
                        }}
                        title="Delete user"
                        className="rounded p-1.5 text-gray-400 hover:bg-red-500/10 hover:text-red-400"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// Moderation Tab
// ============================================================================

function ModerationTab() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);

  const { data: users } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get<Record<string, unknown>[]>("/admin/dashboard/users"),
  });

  const { data: conversations } = useQuery({
    queryKey: ["admin-convs", selectedUserId],
    queryFn: () => api.get<Record<string, unknown>[]>(`/admin/dashboard/users/${selectedUserId}/conversations`),
    enabled: !!selectedUserId,
  });

  const { data: messages } = useQuery({
    queryKey: ["admin-messages", selectedConvId],
    queryFn: () => api.get<Record<string, unknown>[]>(`/admin/dashboard/conversations/${selectedConvId}/messages`),
    enabled: !!selectedConvId,
  });

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* User list */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-4">
        <h3 className="mb-3 font-semibold text-white text-sm">Users</h3>
        <div className="space-y-1 max-h-[500px] overflow-y-auto">
          {(users || []).filter((u) => (u.conversation_count as number) > 0).map((u) => (
            <button
              key={u.id as string}
              onClick={() => { setSelectedUserId(u.id as string); setSelectedConvId(null); }}
              className={`w-full rounded-lg p-2 text-left text-sm transition-colors ${
                selectedUserId === u.id ? "bg-[#1A2942] text-white" : "text-gray-400 hover:bg-[#1A2942]/50"
              }`}
            >
              <p className="truncate">{u.email as string}</p>
              <p className="text-xs text-gray-500">{u.conversation_count as number} conversations</p>
            </button>
          ))}
        </div>
      </div>

      {/* Conversations */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-4">
        <h3 className="mb-3 font-semibold text-white text-sm">Conversations</h3>
        {selectedUserId ? (
          <div className="space-y-1 max-h-[500px] overflow-y-auto">
            {(conversations || []).map((c) => (
              <button
                key={c.id as string}
                onClick={() => setSelectedConvId(c.id as string)}
                className={`w-full rounded-lg p-2 text-left text-sm transition-colors ${
                  selectedConvId === c.id ? "bg-[#1A2942] text-white" : "text-gray-400 hover:bg-[#1A2942]/50"
                }`}
              >
                <p className="truncate">{(c.title as string) || "Untitled"}</p>
                <p className="text-xs text-gray-500">{c.message_count as number} messages</p>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Select a user</p>
        )}
      </div>

      {/* Messages */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-4">
        <h3 className="mb-3 font-semibold text-white text-sm">Messages</h3>
        {selectedConvId ? (
          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {(messages || []).map((m) => (
              <div
                key={m.id as string}
                className={`rounded-lg p-3 text-sm ${
                  m.role === "user" ? "bg-[#00D4AA]/10 text-gray-200" : "bg-[#1A2942] text-gray-300"
                }`}
              >
                <p className="text-xs font-medium text-gray-500 mb-1">
                  {m.role === "user" ? "User" : "AI Tutor"}
                </p>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{m.content as string}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Select a conversation</p>
        )}
      </div>
    </div>
  );
}
