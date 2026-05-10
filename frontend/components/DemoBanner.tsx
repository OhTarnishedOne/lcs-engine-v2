"use client";

import { ArrowRight } from "lucide-react";

export function DemoBanner() {
  if (typeof window === "undefined") return null;
  if (!window.location.hostname.includes("demo.")) return null;

  return (
    <div className="sticky top-0 z-[60] flex items-center justify-center gap-3 bg-[#1A2942] px-4 py-2 border-b border-[#00D4AA]/20">
      <p className="text-xs text-gray-300">
        You&apos;re viewing the LCS Engine demo. Create your account to start building your Calibration Score.
      </p>
      <a
        href="https://www.lcsengine.com/register"
        className="inline-flex items-center gap-1 rounded-md bg-[#00D4AA] px-3 py-1 text-xs font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
      >
        Get Started
        <ArrowRight className="h-3 w-3" />
      </a>
    </div>
  );
}
