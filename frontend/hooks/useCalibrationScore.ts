"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

export interface CalibrationData {
  overall_score: number | null;
  prediction_count: number;
  resolved_count: number;
  percentile: number | null;
  sub_scores: { category: string; score: number; prediction_count: number }[];
  trend_30d: { date: string; score: number }[];
}

export function useCalibrationScore() {
  const { isAuthenticated } = useAuthStore();

  const { data, isLoading } = useQuery<CalibrationData>({
    queryKey: ["calibration-score"],
    queryFn: () => api.getCalibrationScore(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });

  return {
    score: data?.overall_score ?? null,
    predictionCount: data?.prediction_count ?? 0,
    resolvedCount: data?.resolved_count ?? 0,
    percentile: data?.percentile ?? null,
    subScores: data?.sub_scores ?? [],
    trend: data?.trend_30d ?? [],
    isLoading,
  };
}
