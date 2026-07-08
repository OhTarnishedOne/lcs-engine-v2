"use client";

/**
 * useBillingStatus — fetches the current user's tier from the backend.
 * Used to gate Pro features and show upgrade prompts.
 *
 * Usage:
 *   const { tier, isPro, isLoading } = useBillingStatus();
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

export function useBillingStatus() {
  const { isAuthenticated } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ["billing-status"],
    queryFn: () => api.getBillingStatus(),
    enabled: isAuthenticated,
    // Tier doesn't change often — 5 min stale time is fine
    staleTime: 5 * 60 * 1000,
  });

  return {
    tier: data?.tier ?? "free",
    isPro: data?.is_pro ?? false,
    isLoading,
  };
}
