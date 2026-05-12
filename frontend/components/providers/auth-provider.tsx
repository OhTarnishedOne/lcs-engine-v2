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
      if (isDemo()) {
        const savedGuestId = localStorage.getItem("demo_guest_id");

        if (api.isAuthenticated()) {
          await fetchUser();
          useAuthStore.setState({ isLoading: false });
          return;
        }

        try {
          const body = savedGuestId ? { guest_id: savedGuestId } : {};
          const res = await api.post<{
            access_token: string;
            refresh_token: string;
            guest_id: string;
            guest_expires_at: string | null;
            days_remaining: number;
          }>("/auth/demo", body);

          api.setTokens(res.access_token, res.refresh_token);
          localStorage.setItem("demo_guest_id", res.guest_id);
          await fetchUser();
        } catch (e) {
          console.error("Demo auto-login failed:", e);
          localStorage.removeItem("demo_guest_id");
        } finally {
          useAuthStore.setState({ isLoading: false });
        }
      } else {
        await initialize();
      }
    }
    init();
  }, [initialize, fetchUser]);

  return <>{children}</>;
}
