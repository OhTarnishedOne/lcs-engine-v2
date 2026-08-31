"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";
import type {
  ActiveIntervention,
  DecisionCalibrationScore,
  DecisionDiagnosis,
} from "@/lib/api/types";

/**
 * Combined data for the Decision Intelligence dashboard card:
 *   - calibration score / tier / trend   (/gamification/calibration-score)
 *   - primary diagnosed weakness         (/decisions/diagnosis)
 *   - active training mission            (/interventions/active, null when none)
 */
export function useDecisionIntelligence() {
  const { isAuthenticated } = useAuthStore();

  const calibration = useQuery<DecisionCalibrationScore>({
    queryKey: ["decision-calibration"],
    queryFn: () => api.getDecisionCalibration(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });

  const diagnosis = useQuery<DecisionDiagnosis>({
    queryKey: ["decision-diagnosis"],
    queryFn: () => api.getDecisionDiagnosis(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });

  const intervention = useQuery<ActiveIntervention | null>({
    queryKey: ["active-intervention"],
    queryFn: () => api.getActiveIntervention(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });

  return {
    calibration: calibration.data ?? null,
    diagnosis: diagnosis.data ?? null,
    intervention: intervention.data ?? null,
    // The two required queries drive loading/error. The mission is optional
    // (null is a valid answer), so it never forces loading or error states.
    isLoading: calibration.isLoading || diagnosis.isLoading,
    isError: calibration.isError || diagnosis.isError,
  };
}
