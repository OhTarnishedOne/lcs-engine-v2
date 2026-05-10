"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/api/client";

function isDemo(): boolean {
  if (typeof window === "undefined") return false;
  return window.location.hostname.includes("demo.");
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const initialize = useAuthStore((state) => state.initialize);
  const fetchUser = useAuthStore((state) => state.fetchUser);

  useEffect(() => {
    async function init() {
      if (isDemo() && !api.isAuthenticated()) {
        // Auto-login as demo user
        try {
          const res = await api.post<{ access_token: string; refresh_token: string }>(
            "/auth/demo"
          );
          api.setTokens(res.access_token, res.refresh_token);
          await fetchUser();
        } catch (e) {
          console.error("Demo auto-login failed:", e);
        }
      } else {
        await initialize();
      }
    }
    init();
  }, [initialize, fetchUser]);

  return <>{children}</>;
}
