"use client";

import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: {
    value: number;
    isPositive: boolean;
  };
  icon?: LucideIcon;
  className?: string;
  valueClassName?: string;
}

export function StatCard({
  label,
  value,
  change,
  icon: Icon,
  className,
  valueClassName,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-800 bg-[#111827] p-5",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p
            className={cn(
              "mt-1 text-2xl font-bold font-mono tracking-tight",
              valueClassName
            )}
          >
            {value}
          </p>
          {change && (
            <p
              className={cn(
                "mt-1 text-sm font-mono",
                change.isPositive ? "text-[#10B981]" : "text-[#EF4444]"
              )}
            >
              {change.isPositive ? "+" : ""}
              {change.value.toFixed(2)}%
            </p>
          )}
        </div>
        {Icon && (
          <div className="rounded-lg bg-[#1A2942] p-2">
            <Icon className="h-5 w-5 text-[#00D4AA]" />
          </div>
        )}
      </div>
    </div>
  );
}
