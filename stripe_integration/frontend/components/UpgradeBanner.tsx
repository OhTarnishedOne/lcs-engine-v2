"use client";

/**
 * UpgradeBanner — inline upgrade prompt for gated features.
 *
 * Usage:
 *   <UpgradeBanner feature="Unlimited AI Tutor sessions" />
 */

import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUpgrade } from "@/hooks/useUpgrade";

interface UpgradeBannerProps {
  feature?: string;
  className?: string;
}

export function UpgradeBanner({
  feature = "this feature",
  className = "",
}: UpgradeBannerProps) {
  const { upgrade, isLoading } = useUpgrade();

  return (
    <div
      className={`rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-6 text-center ${className}`}
    >
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[#00D4AA]/20">
        <Sparkles className="h-5 w-5 text-[#00D4AA]" />
      </div>
      <h3 className="text-base font-semibold text-white">
        Upgrade to Pro
      </h3>
      <p className="mt-1 text-sm text-gray-400">
        Unlock {feature} and everything else in Pro for $20/month.
      </p>
      <Button
        onClick={upgrade}
        disabled={isLoading}
        className="mt-4 bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-60"
      >
        {isLoading ? "Redirecting…" : "Upgrade to Pro — $20/mo"}
      </Button>
    </div>
  );
}
