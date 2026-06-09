"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  Brain,
  CheckCircle,
  HelpCircle,
  Target,
} from "lucide-react";

import type {
  CalibrationEngineInsight,
  CalibrationNextAction,
  CalibrationRecentReview,
} from "@/hooks/useCalibrationScore";

interface CalibrationEngineLoopProps {
  score: number | null;
  predictionCount: number;
  resolvedCount: number;
  nextAction: CalibrationNextAction | null;
  insights: CalibrationEngineInsight[];
  recentReviews: CalibrationRecentReview[];
  onShowMethodology?: () => void;
}

const severityStyles: Record<CalibrationEngineInsight["severity"], string> = {
  info: "border-blue-500/20 bg-blue-500/10 text-blue-300",
  positive: "border-[#00D4AA]/20 bg-[#00D4AA]/10 text-[#00D4AA]",
  warning: "border-amber-500/20 bg-amber-500/10 text-amber-300",
};

function loopStatus(isComplete: boolean, isActive: boolean) {
  if (isComplete) return "complete";
  if (isActive) return "active";
  return "waiting";
}

export function CalibrationEngineLoop({
  score,
  predictionCount,
  resolvedCount,
  nextAction,
  insights,
  recentReviews,
  onShowMethodology,
}: CalibrationEngineLoopProps) {
  const hasScore = score !== null;
  const loopSteps = [
    {
      title: "Decide",
      description: "Make a probability call before seeing consensus.",
      status: loopStatus(predictionCount > 0, predictionCount === 0),
    },
    {
      title: "Score",
      description: "Resolved outcomes turn confidence into a decision score.",
      status: loopStatus(resolvedCount >= 5, predictionCount > 0 && resolvedCount < 5),
    },
    {
      title: "Diagnose",
      description: "Find where confidence, base rates, or direction broke down.",
      status: loopStatus(hasScore && insights.length > 0, hasScore),
    },
    {
      title: "Improve",
      description: "Use the next call to pressure-test the weak pattern.",
      status: loopStatus(false, hasScore),
    },
  ];

  return (
    <div className="rounded-xl border border-[#00D4AA]/20 bg-gradient-to-br from-[#111827] to-[#0A1628] p-6">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-[#00D4AA]/20 bg-[#00D4AA]/10 px-3 py-1 text-xs font-medium text-[#00D4AA]">
            <Brain className="h-3.5 w-3.5" />
            Decision Intelligence Engine
          </div>
          <h2 className="text-xl font-semibold text-white">
            Calibration is the product loop
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-gray-400">
            You decide, the market resolves, LCS scores the quality of your
            judgment, then shows the pattern to improve on the next decision.
          </p>
          {onShowMethodology && (
            <button
              onClick={onShowMethodology}
              className="mt-3 inline-flex items-center gap-1 text-xs text-gray-400 transition-colors hover:text-[#00D4AA]"
            >
              <HelpCircle className="h-3.5 w-3.5" />
              How the score works
            </button>
          )}
        </div>

        {nextAction && (
          <div className="rounded-lg border border-gray-800 bg-[#111827]/80 p-4 lg:w-80">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#00D4AA]">
              Next best action
            </p>
            <h3 className="mt-2 font-semibold text-white">{nextAction.title}</h3>
            <p className="mt-1 text-sm text-gray-400">{nextAction.description}</p>
            <Link
              href={nextAction.href}
              className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[#00D4AA]"
            >
              {nextAction.cta}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {loopSteps.map((step, index) => {
          const isComplete = step.status === "complete";
          const isActive = step.status === "active";
          return (
            <div
              key={step.title}
              className={`rounded-lg border p-4 ${
                isComplete
                  ? "border-[#00D4AA]/30 bg-[#00D4AA]/10"
                  : isActive
                  ? "border-amber-500/30 bg-amber-500/10"
                  : "border-gray-800 bg-[#111827]/70"
              }`}
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#1A2942] text-xs font-bold text-gray-300">
                  {index + 1}
                </span>
                {isComplete ? (
                  <CheckCircle className="h-4 w-4 text-[#00D4AA]" />
                ) : isActive ? (
                  <Target className="h-4 w-4 text-amber-300" />
                ) : (
                  <div className="h-2 w-2 rounded-full bg-gray-700" />
                )}
              </div>
              <h3 className="font-semibold text-white">{step.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-gray-400">
                {step.description}
              </p>
            </div>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <div className="mb-3 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-[#00D4AA]" />
            <h3 className="font-semibold text-white">Engine insights</h3>
          </div>
          <div className="space-y-3">
            {insights.length > 0 ? (
              insights.map((insight) => (
                <div
                  key={`${insight.type}-${insight.title}`}
                  className={`rounded-lg border p-4 ${severityStyles[insight.severity]}`}
                >
                  <p className="font-medium text-white">{insight.title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-gray-300">
                    {insight.description}
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-gray-800 bg-[#111827]/70 p-4">
                <p className="text-sm text-gray-400">
                  Make predictions and wait for resolutions to generate coaching
                  insights.
                </p>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold text-white">Recent decision reviews</h3>
            <span className="text-xs text-gray-500">
              {resolvedCount} resolved
            </span>
          </div>
          <div className="space-y-3">
            {recentReviews.length > 0 ? (
              recentReviews.map((review) => (
                <div
                  key={`${review.market_title}-${review.created_at}`}
                  className="rounded-lg border border-gray-800 bg-[#111827]/80 p-4"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p className="line-clamp-2 text-sm font-medium text-white">
                        {review.market_title}
                      </p>
                      <p className="mt-1 text-xs uppercase tracking-wider text-gray-500">
                        {review.category}
                      </p>
                    </div>
                    <div className="shrink-0 rounded-lg bg-[#1A2942] px-3 py-2 text-center">
                      <p className="text-xs text-gray-500">Decision score</p>
                      <p className="font-mono-nums text-lg font-bold text-[#00D4AA]">
                        {review.decision_score}
                      </p>
                    </div>
                  </div>
                  <div className="mb-3 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full bg-[#1A2942] px-2 py-1 text-gray-300">
                      You: {Math.round(review.predicted_probability * 100)}%
                    </span>
                    <span className="rounded-full bg-[#1A2942] px-2 py-1 text-gray-300">
                      Outcome: {review.outcome.toUpperCase()}
                    </span>
                    <span className="rounded-full bg-[#00D4AA]/10 px-2 py-1 text-[#00D4AA]">
                      {review.verdict}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed text-gray-400">
                    {review.diagnosis}
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-gray-800 bg-[#111827]/70 p-4 text-center">
                <p className="text-sm text-gray-400">
                  Decision reviews appear after markets resolve.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
