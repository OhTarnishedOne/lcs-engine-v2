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
  is_first_score_view: boolean;
  engine_state: "building" | "active";
  next_action: CalibrationNextAction | null;
  engine_insights: CalibrationEngineInsight[];
  recent_reviews: CalibrationRecentReview[];
}

export interface CalibrationNextAction {
  title: string;
  description: string;
  cta: string;
  href: string;
}

export interface CalibrationEngineInsight {
  type: string;
  title: string;
  description: string;
  severity: "info" | "positive" | "warning";
}

export interface CalibrationRecentReview {
  market_title: string;
  category: string;
  predicted_probability: number;
  outcome: string;
  brier_score: number;
  decision_score: number;
  verdict: string;
  diagnosis: string;
  created_at: string;
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
    isFirstScoreView: data?.is_first_score_view ?? false,
    engineState: data?.engine_state ?? "building",
    nextAction: data?.next_action ?? null,
    engineInsights: data?.engine_insights ?? [],
    recentReviews: data?.recent_reviews ?? [],
    isLoading,
  };
}
