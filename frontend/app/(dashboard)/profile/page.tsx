"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";

export default function ProfilePage() {
  const { user } = useAuthStore();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Profile</h1>
        <p className="text-slate-600">Manage your account settings.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
          <CardDescription>Your account details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-500">Email</label>
            <p className="text-slate-900">{user?.email}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-500">Member since</label>
            <p className="text-slate-900">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
