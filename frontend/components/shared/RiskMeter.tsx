"use client";

import { cn } from "@/lib/utils";

interface RiskMeterProps {
  level: number; // 1-5
  className?: string;
  showLabel?: boolean;
}

const riskLabels = ["Very Low", "Low", "Moderate", "High", "Very High"];
const riskColors = [
  "bg-[#10B981]", // green
  "bg-[#34D399]", // lighter green
  "bg-[#F59E0B]", // amber
  "bg-[#F97316]", // orange
  "bg-[#EF4444]", // red
];

export function RiskMeter({ level, className, showLabel = false }: RiskMeterProps) {
  const safeLevel = Math.max(1, Math.min(5, level));

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex gap-1">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-2 w-2 rounded-full transition-colors",
              i < safeLevel ? riskColors[safeLevel - 1] : "bg-gray-700"
            )}
          />
        ))}
      </div>
      {showLabel && (
        <span className="text-xs text-gray-400">{riskLabels[safeLevel - 1]}</span>
      )}
    </div>
  );
}
