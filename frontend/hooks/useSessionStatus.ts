"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

export function useSessionStatus() {
  const { isAuthenticated } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ["session-status"],
    queryFn: () => api.getSessionStatus(),
    enabled: isAuthenticated,
    // Refetch when conversations change
    staleTime: 0,
  });

  return {
    conversationCount: data?.conversation_count ?? 0,
    limitReached: data?.limit_reached ?? false,
    isPro: data?.is_pro ?? false,
    isLoading,
  };
}
