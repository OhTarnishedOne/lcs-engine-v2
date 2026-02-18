"use client";

import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-6 text-center",
        className
      )}
    >
      <div className="mb-4 rounded-full bg-[#1A2942] p-4">
        <Icon className="h-8 w-8 text-[#00D4AA]" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-gray-100">{title}</h3>
      <p className="mb-6 max-w-sm text-base text-gray-400">{description}</p>
      {action && (
        <Button
          onClick={action.onClick}
          className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] btn-accent-glow"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}
