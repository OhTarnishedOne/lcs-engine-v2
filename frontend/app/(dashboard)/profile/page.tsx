"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";

export default function ProfilePage() {
  const { user, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <div className="h-8 w-32 rounded skeleton-shimmer" />
          <div className="mt-2 h-5 w-56 rounded skeleton-shimmer" />
        </div>
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-6 space-y-4">
          <div className="h-6 w-48 rounded skeleton-shimmer" />
          <div className="h-4 w-36 rounded skeleton-shimmer" />
          <div className="space-y-3 pt-2">
            <div className="h-4 w-20 rounded skeleton-shimmer" />
            <div className="h-5 w-52 rounded skeleton-shimmer" />
            <div className="h-4 w-24 rounded skeleton-shimmer" />
            <div className="h-5 w-36 rounded skeleton-shimmer" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Profile</h1>
        <p className="text-gray-400">Manage your account settings.</p>
      </div>
      <Card className="border-gray-800 bg-[#111827]">
        <CardHeader>
          <CardTitle className="text-white">Account Information</CardTitle>
          <CardDescription className="text-gray-400">Your account details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-400">Email</label>
            <p className="text-white">{user?.email}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-400">Member since</label>
            <p className="text-white">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
