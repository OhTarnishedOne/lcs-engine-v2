"use client";

import { cn } from "@/lib/utils";

interface SkeletonCardProps {
  className?: string;
  lines?: number;
  showHeader?: boolean;
}

export function SkeletonCard({ className, lines = 3, showHeader = true }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-800 bg-[#111827] p-6",
        className
      )}
    >
      {showHeader && (
        <div className="mb-4">
          <div className="h-6 w-1/3 rounded skeleton-shimmer" />
        </div>
      )}
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-4 rounded skeleton-shimmer"
            style={{ width: `${Math.max(40, 100 - i * 15)}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export function SkeletonText({ className, width = "100%" }: { className?: string; width?: string }) {
  return (
    <div
      className={cn("h-4 rounded skeleton-shimmer", className)}
      style={{ width }}
    />
  );
}

export function SkeletonAvatar({ className, size = "md" }: { className?: string; size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
  };

  return (
    <div
      className={cn(
        "rounded-full skeleton-shimmer",
        sizeClasses[size],
        className
      )}
    />
  );
}
