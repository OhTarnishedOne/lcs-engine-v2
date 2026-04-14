"use client";
import { useState } from "react";
import { api } from "@/lib/api/client";

export function useUpgrade() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const upgrade = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { url } = await api.createCheckoutSession();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setIsLoading(false);
    }
  };
  return { upgrade, isLoading, error };
}
