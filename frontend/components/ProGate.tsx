"use client";
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { UpgradeBanner } from "@/components/UpgradeBanner";

interface ProGateProps {
  feature?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function ProGate({ feature, children, fallback }: ProGateProps) {
  const { isPro, isLoading } = useBillingStatus();
  if (isLoading) return null;
  if (isPro) return <>{children}</>;
  return <>{fallback ?? <UpgradeBanner feature={feature} />}</>;
}
