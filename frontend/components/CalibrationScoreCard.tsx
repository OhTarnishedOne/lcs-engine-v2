"use client";

import Link from "next/link";
import { Target, ArrowRight } from "lucide-react";
import { useCalibrationScore } from "@/hooks/useCalibrationScore";
import { InfoTip } from "@/components/InfoTip";

const SCORE_TOOLTIP = "The feedback loop behind LCS Engine: make a decision, get scored, diagnose the pattern, then improve the next call.";

function MiniSparkline({ data }: { data: { score: number }[] }) {
  if (data.length < 2) return null;

  const max = Math.max(...data.map((d) => d.score), 100);
  const min = Math.min(...data.map((d) => d.score), 0);
  const range = max - min || 1;
  const w = 80;
  const h = 24;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((d.score - min) / range) * h;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg width={w} height={h} className="inline-block">
      <polyline
        points={points}
        fill="none"
        stroke="#00D4AA"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface Props {
  compact?: boolean;
}

export function CalibrationScoreCard({ compact = false }: Props) {
  const { score, percentile, trend, resolvedCount, predictionCount, isLoading } = useCalibrationScore();

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
        <div className="h-16 skeleton-shimmer rounded" />
      </div>
    );
  }

  // Empty state — not enough data
  if (score === null) {
    return (
      <Link href="/probability-lab">
        <div className="group rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-5 card-hover-lift cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#00D4AA]/20">
              <Target className="h-5 w-5 text-[#00D4AA]" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">Start the Decision Intelligence Engine</p>
              <p className="text-xs text-gray-400 mt-0.5">
                {resolvedCount < 5
                  ? `${5 - resolvedCount} more resolved predictions unlock scoring`
                  : "Make predictions to start the feedback loop"}
              </p>
            </div>
            <ArrowRight className="h-4 w-4 text-[#00D4AA] transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </Link>
    );
  }

  if (compact) {
    return (
      <Link href="/probability-lab">
        <div className="group rounded-xl border border-gray-800 bg-[#111827] p-4 card-hover-lift cursor-pointer">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#00D4AA]/20">
                <Target className="h-4 w-4 text-[#00D4AA]" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Decision Engine</p>
                <p className="text-xl font-bold font-mono-nums text-[#00D4AA]">{score}</p>
              </div>
            </div>
            <MiniSparkline data={trend} />
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link href="/probability-lab">
      <div className="group rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-6 card-hover-lift cursor-pointer">
        <div className="flex items-start justify-between">
          <div>
            <InfoTip content={SCORE_TOOLTIP}>
              <div className="flex items-center gap-2 mb-1 cursor-help">
                <Target className="h-5 w-5 text-[#00D4AA]" />
                <p className="text-sm text-gray-400 border-b border-dashed border-gray-600">Decision Intelligence Engine</p>
              </div>
            </InfoTip>
            <p className="text-4xl font-bold font-mono-nums text-[#00D4AA]">{score}</p>
            {percentile !== null && (
              <p className="mt-1 text-xs text-gray-400">
                Better than {percentile}% of forecasters this month
              </p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              Calibration Score from {resolvedCount} resolved decisions · {predictionCount} total predictions
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <MiniSparkline data={trend} />
            <ArrowRight className="h-4 w-4 text-gray-600 transition-transform group-hover:translate-x-1 group-hover:text-[#00D4AA]" />
          </div>
        </div>
      </div>
    </Link>
  );
}
