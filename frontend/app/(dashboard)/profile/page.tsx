"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";

export default function ProfilePage() {
  const { user } = useAuthStore();

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
