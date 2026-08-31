"use client";

import Link from "next/link";
import {
  Target,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Flag,
} from "lucide-react";

import { useDecisionIntelligence } from "@/hooks/useDecisionIntelligence";
import { InfoTip } from "@/components/InfoTip";
import type { ActiveIntervention, ScoreTrend } from "@/lib/api/types";

const HEADER_TOOLTIP =
  "The engine behind LCS: make a decision, get scored, diagnose the pattern that's costing you, train it, then decide again.";

// Mission type drives the next action: decision-composing missions
// (premortem / falsification / commit) go to the Decision Composer;
// reflection missions go to the Probability Lab to review a resolved call.
function ctaFor(intervention: ActiveIntervention | null): {
  label: string;
  href: string;
} {
  if (!intervention) {
    return { label: "Make a prediction", href: "/probability-lab" };
  }
  if (intervention.intervention_type === "reflection") {
    return { label: "Review a resolved prediction", href: "/probability-lab" };
  }
  return { label: "Log your next decision", href: "/decisions/new" };
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function TrendBadge({ trend }: { trend: ScoreTrend | null }) {
  if (!trend) return null;
  const map = {
    improving: { Icon: TrendingUp, color: "text-[#00D4AA]", label: "Improving" },
    stable: { Icon: Minus, color: "text-gray-400", label: "Stable" },
    declining: { Icon: TrendingDown, color: "text-red-400", label: "Declining" },
  } as const;
  const { Icon, color, label } = map[trend];
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${color}`}>
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}

function CardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-6">
      <InfoTip content={HEADER_TOOLTIP}>
        <div className="mb-4 flex items-center gap-2 cursor-help">
          <Target className="h-5 w-5 text-[#00D4AA]" />
          <p className="text-sm text-gray-400 border-b border-dashed border-gray-600">
            Decision Intelligence Engine
          </p>
        </div>
      </InfoTip>
      {children}
    </div>
  );
}

function CtaButton({ label, href }: { label: string; href: string }) {
  return (
    <Link
      href={href}
      className="group mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#00D4AA] px-4 py-2.5 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
    >
      {label}
      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
    </Link>
  );
}

export function DecisionIntelligenceCard() {
  const { calibration, diagnosis, intervention, isLoading, isError } =
    useDecisionIntelligence();

  // 1. Loading
  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <div className="h-6 w-48 skeleton-shimmer rounded" />
        <div className="mt-4 h-16 w-full skeleton-shimmer rounded" />
        <div className="mt-4 h-10 w-full skeleton-shimmer rounded" />
      </div>
    );
  }

  // 2. Error
  if (isError || !calibration) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <p className="text-sm font-medium text-white">
            Couldn&apos;t load your Decision Intelligence Engine
          </p>
        </div>
        <p className="mt-1 text-xs text-gray-400">
          Something went wrong fetching your score. Try refreshing.
        </p>
      </div>
    );
  }

  // 3. Empty — no resolved decisions yet
  if (calibration.resolved_predictions === 0) {
    return (
      <CardShell>
        <p className="text-sm text-gray-300">
          Make your first prediction to unlock your Calibration Score.
        </p>
        <CtaButton label="Make your first prediction" href="/probability-lab" />
      </CardShell>
    );
  }

  const hasScore = calibration.calibration_score !== null;
  const tier = calibration.score_family;
  const primarySignal = diagnosis?.signals?.[0] ?? null;
  const cta = ctaFor(intervention);
  const remainingToUnlock = Math.max(0, 5 - calibration.resolved_predictions);

  return (
    <CardShell>
      {/* 1. Calibration Score — score, tier, trend */}
      <div className="flex items-start justify-between">
        <div>
          {hasScore ? (
            <>
              <p className="text-4xl font-bold font-mono-nums text-[#00D4AA]">
                {calibration.calibration_score}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Calibration Score · {calibration.resolved_predictions} resolved
              </p>
            </>
          ) : (
            <>
              <p className="text-3xl font-bold font-mono-nums text-gray-500">—</p>
              <p className="mt-1 text-xs text-gray-500">
                {remainingToUnlock} more resolved{" "}
                {remainingToUnlock === 1 ? "decision" : "decisions"} to unlock
                your score
              </p>
            </>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          {tier && (
            <span className="rounded-full border border-[#00D4AA]/30 bg-[#00D4AA]/10 px-2.5 py-0.5 text-xs font-medium text-[#00D4AA]">
              {titleCase(tier)}
            </span>
          )}
          <TrendBadge trend={calibration.trend} />
        </div>
      </div>

      {/* 2. Primary Weakness */}
      {primarySignal && (
        <div className="mt-4 rounded-lg bg-[#1A2942]/50 p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
            <p className="text-xs uppercase tracking-wide text-gray-500">
              Primary weakness
            </p>
          </div>
          <p className="mt-1 text-sm font-medium text-white">
            {primarySignal.title}
          </p>
        </div>
      )}

      {/* 3. Active Mission */}
      {intervention && (
        <div className="mt-3 rounded-lg bg-[#1A2942]/50 p-3">
          <div className="flex items-center gap-2">
            <Flag className="h-4 w-4 shrink-0 text-[#00D4AA]" />
            <p className="text-xs uppercase tracking-wide text-gray-500">
              Active mission
            </p>
          </div>
          <p className="mt-1 text-sm font-medium text-white">
            {intervention.title}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-800">
              <div
                className="h-full bg-[#00D4AA] transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    (intervention.progress_count / intervention.target_count) *
                      100
                  )}%`,
                }}
              />
            </div>
            <span className="font-mono-nums text-xs text-gray-400">
              {intervention.progress_count} / {intervention.target_count}
            </span>
          </div>
        </div>
      )}

      {/* 4. Next Action CTA */}
      <CtaButton label={cta.label} href={cta.href} />
    </CardShell>
  );
}
