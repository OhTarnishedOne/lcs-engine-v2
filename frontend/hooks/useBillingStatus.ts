"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

export function useBillingStatus() {
  const { isAuthenticated } = useAuthStore();
  const { data, isLoading } = useQuery({
    queryKey: ["billing-status"],
    queryFn: () => api.getBillingStatus(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
  return {
    tier: data?.tier ?? "free",
    isPro: data?.is_pro ?? false,
    isLoading,
  };
}
