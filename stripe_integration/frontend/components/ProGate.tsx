"use client";

/**
 * ProGate — wraps any feature that requires Pro.
 * Shows the feature if isPro, otherwise shows UpgradeBanner.
 *
 * Usage:
 *   <ProGate feature="unlimited AI tutor sessions">
 *     <ChatInterface />
 *   </ProGate>
 */

import { useBillingStatus } from "@/hooks/useBillingStatus";
import { UpgradeBanner } from "@/components/UpgradeBanner";

interface ProGateProps {
  feature?: string;
  children: React.ReactNode;
  /** Optional: render children but in a degraded state (e.g. limited) */
  fallback?: React.ReactNode;
}

export function ProGate({ feature, children, fallback }: ProGateProps) {
  const { isPro, isLoading } = useBillingStatus();

  // While loading, render nothing — avoids flash of upgrade prompt
  if (isLoading) return null;

  if (isPro) return <>{children}</>;

  // Use provided fallback or default banner
  return <>{fallback ?? <UpgradeBanner feature={feature} />}</>;
}
