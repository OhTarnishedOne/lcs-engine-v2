"use client";
import { useState } from "react";
import { api } from "@/lib/api/client";

export function useManageSubscription() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const manage = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { url } = await api.createPortalSession();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setIsLoading(false);
    }
  };
  return { manage, isLoading, error };
}
