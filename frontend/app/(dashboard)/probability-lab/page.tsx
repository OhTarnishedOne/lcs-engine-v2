"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Target,
  Clock,
  ChevronRight,
  Loader2,
  CheckCircle,
  AlertCircle,
  Brain,
  HelpCircle,
  X,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { trackEvent } from "@/lib/analytics";
import { Button } from "@/components/ui/button";
import { SkeletonCard, EmptyState } from "@/components/shared";
import { ProGate } from "@/components/ProGate";
import { MacroStrategyCard } from "@/components/MacroStrategyCard";
import { UpgradeBanner } from "@/components/UpgradeBanner";
import { CalibrationEngineLoop } from "@/components/CalibrationEngineLoop";
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { useCalibrationScore } from "@/hooks/useCalibrationScore";
import { InfoTip } from "@/components/InfoTip";
import type { PredictionMarket } from "@/lib/api/types";

const CATEGORY_COLORS: Record<string, string> = {
  fed: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  cpi: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  gdp: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  jobs: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  default: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const CATEGORY_LABELS: Record<string, string> = {
  cpi: "CPI",
  "fed-funds-rate": "Fed Funds",
  unemployment: "Jobs",
  gdp: "GDP",
  inflation: "Inflation",
  "treasury-yields": "Treasuries",
};

const CATEGORY_TOOLTIPS: Record<string, string> = {
  cpi: "Your calibration on inflation-related predictions.",
  "fed-funds-rate": "Your calibration on Federal Reserve rate decisions.",
  gdp: "Your calibration on US economic growth predictions.",
  unemployment: "Your calibration on labor market predictions.",
  inflation: "Your calibration on broad inflation predictions.",
  "treasury-yields": "Your calibration on bond market predictions.",
  recession: "Your calibration on recession predictions.",
};

const SCORE_TOOLTIP = "A measure of how well your confidence matches reality \u2014 the skill that separates great investors from lucky ones.";
const BIASES_TOOLTIP = "Patterns in your prediction history that suggest systematic biases. Each bias is a place where your reasoning may be consistently off.";

export default function ProbabilityLabPage() {
  const { isPro } = useBillingStatus();
  const {
    score: calibrationScore,
    percentile,
    subScores,
    trend,
    resolvedCount,
    predictionCount,
    isFirstScoreView,
    nextAction,
    engineInsights,
    recentReviews,
  } = useCalibrationScore();
  const isDemo = typeof window !== "undefined" && window.location.hostname.includes("demo.");
  const queryClient = useQueryClient();
  const [selectedMarket, setSelectedMarket] = useState<PredictionMarket | null>(null);
  const [probability, setProbability] = useState(50);
  const [reasoning, setReasoning] = useState("");
  const [showMethodology, setShowMethodology] = useState(false);
  const [showResult, setShowResult] = useState<{
    predicted: number;
    market: number;
  } | null>(null);

  // Fetch markets
  const { data: marketsData, isLoading: marketsLoading } = useQuery({
    queryKey: ["markets"],
    queryFn: () => api.getMarkets(),
  });

  // Fetch user predictions
  const { data: predictionsData } = useQuery({
    queryKey: ["predictions"],
    queryFn: () => api.getPredictions(),
  });

  // Fetch calibration
  const { data: calibration } = useQuery({
    queryKey: ["calibration"],
    queryFn: () => api.getCalibration(),
  });

  // Submit prediction
  const submitMutation = useMutation({
    mutationFn: (data: { market_id: string; probability: number; reasoning?: string }) =>
      api.submitPrediction(data),
    onSuccess: (result) => {
      trackEvent("prediction_submitted");
      queryClient.invalidateQueries({ queryKey: ["predictions"] });
      queryClient.invalidateQueries({ queryKey: ["calibration"] });
      queryClient.invalidateQueries({ queryKey: ["calibration-score"] });
      queryClient.invalidateQueries({ queryKey: ["markets"] });
      setShowResult({
        predicted: result.predicted_probability * 100,
        market: (result.market_probability ?? 0) * 100,
      });
    },
  });

  const markets = marketsData?.markets || [];
  const predictions = predictionsData?.predictions || [];
  const predictedMarketIds = new Set(predictions.map((p) => p.market_id));

  const handleSubmitPrediction = () => {
    if (!selectedMarket) return;
    submitMutation.mutate({
      market_id: selectedMarket.id,
      probability: probability / 100,
      reasoning: reasoning || undefined,
    });
  };

  const closeModal = () => {
    setSelectedMarket(null);
    setProbability(50);
    setReasoning("");
    setShowResult(null);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getCategoryColor = (category: string) => {
    return CATEGORY_COLORS[category.toLowerCase()] || CATEGORY_COLORS.default;
  };

  // Calibration chart data
  const hasCalibrationData = (calibration?.calibration_curve ?? []).length > 0;
  const chartResolvedCount = calibration?.resolved_predictions ?? 0;

  const calibrationData = [
    { predicted: 0, perfect: 0, actual: undefined as number | undefined },
    { predicted: 10, perfect: 10, actual: undefined as number | undefined },
    { predicted: 20, perfect: 20, actual: undefined as number | undefined },
    { predicted: 30, perfect: 30, actual: undefined as number | undefined },
    { predicted: 40, perfect: 40, actual: undefined as number | undefined },
    { predicted: 50, perfect: 50, actual: undefined as number | undefined },
    { predicted: 60, perfect: 60, actual: undefined as number | undefined },
    { predicted: 70, perfect: 70, actual: undefined as number | undefined },
    { predicted: 80, perfect: 80, actual: undefined as number | undefined },
    { predicted: 90, perfect: 90, actual: undefined as number | undefined },
    { predicted: 100, perfect: 100, actual: undefined as number | undefined },
  ];

  if (hasCalibrationData) {
    calibration!.calibration_curve.forEach((bucket) => {
      const index = Math.floor(bucket.predicted_avg * 10);
      if (index >= 0 && index < calibrationData.length) {
        calibrationData[index].actual = bucket.actual_rate * 100;
      }
    });
  }

  if (marketsLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="h-8 w-48 rounded skeleton-shimmer" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} lines={3} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <ProGate feature="the Probability Lab">
    <div className="mx-auto max-w-6xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-white">Probability Lab</h1>
        <p className="mt-1 text-gray-400">
          Train the judgment loop behind your Calibration Score
        </p>
      </motion.div>

      {/* Calibration Score */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        {calibrationScore !== null ? (
          <div className="rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-6">
            {/* Touchpoint 2: First-score celebration */}
            {isFirstScoreView && (
              <div className="mb-4 rounded-lg border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4 text-center">
                <p className="text-sm font-semibold text-[#00D4AA]">You&apos;ve earned your first Calibration Score.</p>
                <p className="text-xs text-gray-400 mt-1">Here&apos;s what it tells us about how you reason.</p>
              </div>
            )}

            {/* Touchpoint 5: Demo guest copy */}
            {isDemo && (
              <p className="mb-4 text-sm text-gray-400 leading-relaxed">
                This is the Calibration Score of a user who&apos;s made ~10 predictions over the past month. It updates as predictions resolve and reasoning sharpens. Your own score builds the same way when you claim your account.
              </p>
            )}

            <div className="flex items-start justify-between mb-4">
              <div>
                <InfoTip content={SCORE_TOOLTIP}>
                  <p className="text-sm text-gray-400 mb-1 cursor-help border-b border-dashed border-gray-600">Calibration Score</p>
                </InfoTip>
                <p className="text-5xl font-bold font-mono-nums text-[#00D4AA]">{calibrationScore}</p>
                <p className="mt-1 text-sm text-gray-300">
                  {calibrationScore >= 80 ? "Excellent calibration" :
                   calibrationScore >= 60 ? "Good calibration" :
                   calibrationScore >= 40 ? "Average — room to grow" :
                   calibrationScore >= 20 ? "Below average — work on confidence" :
                   "Poor calibration — review your reasoning"}
                </p>
                {percentile !== null && (
                  <p className="mt-1 text-sm text-gray-400">
                    Better than {percentile}% of forecasters this month
                  </p>
                )}
              </div>
              {trend.length >= 2 && (
                <div className="text-right">
                  <p className="text-xs text-gray-500 mb-1">30-day trend</p>
                  <svg width={100} height={32}>
                    <polyline
                      points={trend.map((d: { score: number }, i: number) => {
                        const x = (i / (trend.length - 1)) * 100;
                        const max = Math.max(...trend.map((t: { score: number }) => t.score), 100);
                        const min = Math.min(...trend.map((t: { score: number }) => t.score), 0);
                        const y = 32 - ((d.score - min) / (max - min || 1)) * 32;
                        return `${x},${y}`;
                      }).join(" ")}
                      fill="none"
                      stroke="#00D4AA"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              )}
            </div>
            {/* Touchpoint 4: Sub-scores with category tooltips */}
            {subScores.length > 0 && (
              <div className="flex flex-wrap gap-3 mb-4">
                {subScores.map((s: { category: string; score: number; prediction_count: number }) => (
                  <InfoTip key={s.category} content={CATEGORY_TOOLTIPS[s.category] || `Your calibration on ${s.category} predictions.`}>
                    <div className="rounded-lg bg-[#1A2942] px-3 py-1.5 cursor-help">
                      <span className="text-xs text-gray-400">{CATEGORY_LABELS[s.category] || s.category}: </span>
                      <span className="text-xs font-semibold text-[#00D4AA]">{s.score}</span>
                    </div>
                  </InfoTip>
                ))}
              </div>
            )}
            {/* Secondary counters */}
            <div className="flex items-center gap-6 text-xs text-gray-500">
              <span>{predictionCount} predictions made</span>
              <span>{resolvedCount} resolved</span>
              <button
                onClick={() => setShowMethodology(true)}
                className="flex items-center gap-1 text-gray-400 hover:text-[#00D4AA] transition-colors"
              >
                <HelpCircle className="h-3 w-3" />
                How is this calculated?
              </button>
            </div>
          </div>
        ) : (
          /* Touchpoint 1: Empty state with motivating copy */
          <div className="rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-6">
            <div className="flex items-start gap-4">
              <Target className="h-8 w-8 shrink-0 text-[#00D4AA] mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-white">Calibration Score</h3>
                <p className="text-sm text-[#00D4AA] mb-3">Coming after {5 - resolvedCount} more resolved predictions</p>
                <p className="text-sm text-gray-400 leading-relaxed mb-4">
                  Most financial education teaches what to think about markets. The Calibration Score measures <em>how</em> you think under uncertainty — whether your stated confidence matches what actually happens. Make predictions on the markets below. As they resolve, you&apos;ll see where your reasoning is sharp and where it&apos;s biased.
                </p>
                <div className="flex items-center gap-6 text-xs text-gray-500">
                  <span>{resolvedCount} / 5 resolved</span>
                  <span>{predictionCount} active</span>
                  <button
                    onClick={() => setShowMethodology(true)}
                    className="flex items-center gap-1 text-gray-400 hover:text-[#00D4AA] transition-colors"
                  >
                    Why does this matter? →
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Decision Intelligence Engine */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="mb-8"
      >
        <CalibrationEngineLoop
          score={calibrationScore}
          predictionCount={predictionCount}
          resolvedCount={resolvedCount}
          nextAction={nextAction}
          insights={engineInsights}
          recentReviews={recentReviews}
          onShowMethodology={() => setShowMethodology(true)}
        />
      </motion.div>

      {/* Markets Grid */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <h2 className="mb-4 text-lg font-semibold text-white">Active Markets</h2>
        {markets.length === 0 ? (
          <EmptyState
            icon={Target}
            title="No markets available"
            description="Check back later for new prediction markets."
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {markets.map((market, index) => {
              const hasPredicted = predictedMarketIds.has(market.id);
              return (
                <motion.div
                  key={market.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.03 }}
                >
                  <button
                    onClick={() => !hasPredicted && setSelectedMarket(market)}
                    disabled={hasPredicted}
                    className={`w-full rounded-xl border bg-[#111827] p-5 text-left transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00D4AA] ${
                      hasPredicted
                        ? "border-gray-800 opacity-60 cursor-not-allowed"
                        : "border-gray-800 hover:border-[#00D4AA]/50 cursor-pointer card-hover-lift"
                    }`}
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span
                        className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${getCategoryColor(
                          market.category
                        )}`}
                      >
                        {market.category}
                      </span>
                      {hasPredicted ? (
                        <CheckCircle className="h-4 w-4 text-[#00D4AA]" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-500" />
                      )}
                    </div>
                    <h3 className="mb-2 font-medium text-white line-clamp-2">
                      {market.title}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>Closes {formatDate(market.close_date)}</span>
                    </div>
                    {hasPredicted && (
                      <p className="mt-2 text-xs text-[#00D4AA]">
                        Already predicted
                      </p>
                    )}
                  </button>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>

      {/* Calibration Section */}
      {(calibration?.total_predictions ?? 0) > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid gap-6 lg:grid-cols-2"
        >
          {/* Calibration Chart */}
          <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
            <h3 className="mb-4 font-semibold text-white">Calibration Curve</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={calibrationData}>
                  <XAxis
                    dataKey="predicted"
                    stroke="#6B7280"
                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#6B7280"
                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const point = payload[0].payload;
                        return (
                          <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                            <p className="text-gray-400">
                              Predicted: {point.predicted}%
                            </p>
                            {point.actual !== undefined ? (
                              <p className="text-[#00D4AA]">
                                Actual: {point.actual.toFixed(0)}%
                              </p>
                            ) : (
                              <p className="text-gray-500">No data yet</p>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="perfect"
                    stroke="#374151"
                    strokeDasharray="5 5"
                    dot={false}
                  />
                  {hasCalibrationData && (
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="#00D4AA"
                      strokeWidth={2}
                      dot={{ fill: "#00D4AA", r: 4 }}
                      connectNulls
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-center text-xs text-gray-500">
              {hasCalibrationData
                ? "Perfect calibration follows the diagonal line"
                : resolvedCount === 0
                ? "Your calibration curve will appear once markets resolve"
                : "Submit more predictions to build your calibration curve"}
            </p>
          </div>

          {/* Detected Biases */}
          <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
            <InfoTip content={BIASES_TOOLTIP}>
              <h3 className="mb-4 flex items-center gap-2 font-semibold text-white cursor-help border-b border-dashed border-transparent hover:border-gray-600 inline-flex">
                <Brain className="h-5 w-5 text-[#00D4AA]" />
                Detected Biases
              </h3>
            </InfoTip>
            {!calibration?.detected_biases || calibration.detected_biases.length === 0 ? (
              <div className="rounded-lg bg-[#1A2942]/50 p-4 text-center">
                <p className="text-sm text-gray-400">
                  {resolvedCount < 5
                    ? `${resolvedCount === 0 ? "No" : resolvedCount} resolved prediction${resolvedCount !== 1 ? "s" : ""} so far. Bias detection requires at least 5 resolved predictions.`
                    : "No biases detected — your predictions look well-calibrated!"}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {calibration.detected_biases.map((bias, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4"
                  >
                    <h4 className="mb-1 font-medium text-amber-400 capitalize">
                      {bias.name.replace(/_/g, " ")}
                    </h4>
                    <p className="mb-2 text-sm text-gray-300">{bias.description}</p>
                    <p className="mb-1 text-xs text-gray-400">{bias.tip}</p>
                    <p className="text-xs text-gray-500">
                      <span className="text-amber-400">Investing connection:</span>{" "}
                      {bias.investing_connection}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Prediction Modal */}
      <AnimatePresence>
        {selectedMarket && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={closeModal}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="w-full max-w-lg rounded-xl border border-gray-800 bg-[#111827] p-6"
              onClick={(e) => e.stopPropagation()}
            >
              {showResult ? (
                // Result view
                <div className="text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring" }}
                    className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#00D4AA]/20"
                  >
                    <CheckCircle className="h-8 w-8 text-[#00D4AA]" />
                  </motion.div>

                  <h3 className="mb-6 text-lg font-semibold text-white">
                    Prediction Submitted
                  </h3>

                  <div className="mb-6 flex items-center justify-center gap-8">
                    <div className="text-center">
                      <p className="text-sm text-gray-400">Your prediction</p>
                      <p className="text-3xl font-bold font-mono text-white">
                        {showResult.predicted.toFixed(0)}%
                      </p>
                    </div>
                    <div className="h-16 w-px bg-gray-700" />
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 }}
                      className="text-center"
                    >
                      <p className="text-sm text-gray-400">Market consensus</p>
                      <p className="text-3xl font-bold font-mono text-[#00D4AA]">
                        {showResult.market.toFixed(0)}%
                      </p>
                    </motion.div>
                  </div>

                  <div className="mb-6 rounded-lg bg-[#1A2942]/50 p-4">
                    <p className="text-sm text-gray-300">
                      {(() => {
                        const diff = Math.abs(showResult.predicted - showResult.market);
                        if (diff <= 1) {
                          return "Exact match! Your prediction matched the market consensus.";
                        } else if (diff <= 10) {
                          return `Very close! Your prediction was within ${Math.round(diff)} points of the market consensus.`;
                        } else {
                          return showResult.predicted > showResult.market
                            ? `You're ${Math.round(diff)} points more confident than the market. Watch how this one resolves — it's a good learning opportunity.`
                            : `You're ${Math.round(diff)} points less confident than the market. Watch how this one resolves — it's a good learning opportunity.`;
                        }
                      })()}
                    </p>
                  </div>

                  {showResult && selectedMarket && isPro && (
                    <MacroStrategyCard
                      marketId={selectedMarket.id}
                      marketTitle={selectedMarket.title}
                      userPrediction={probability}
                    />
                  )}
                  {showResult && selectedMarket && !isPro && (
                    <div className="mt-4">
                      <UpgradeBanner feature="macro-to-portfolio strategy insights" />
                    </div>
                  )}

                  <Button
                    onClick={closeModal}
                    className="mt-4 w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
                  >
                    Done
                  </Button>
                </div>
              ) : (
                // Prediction form
                <>
                  <div className="mb-4 flex items-center justify-between">
                    <span
                      className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${getCategoryColor(
                        selectedMarket.category
                      )}`}
                    >
                      {selectedMarket.category}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={closeModal}
                      aria-label="Close dialog"
                      className="text-gray-400 hover:text-white"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  <h3 className="mb-2 text-lg font-semibold text-white">
                    {selectedMarket.title}
                  </h3>

                  {selectedMarket.description && (
                    <p className="mb-4 text-sm text-gray-400">
                      {selectedMarket.description}
                    </p>
                  )}

                  <div className="mb-6 flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="h-4 w-4" />
                    <span>Closes {formatDate(selectedMarket.close_date)}</span>
                  </div>

                  {/* Probability slider */}
                  <div className="mb-6">
                    <div className="mb-2 flex items-center justify-between">
                      <label className="text-sm text-gray-400">
                        Your probability estimate
                      </label>
                      <span className="text-2xl font-bold font-mono text-[#00D4AA]">
                        {probability}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      list="probability-ticks"
                      value={probability}
                      onChange={(e) => setProbability(parseInt(e.target.value))}
                      aria-label={`Probability estimate: ${probability}%`}
                      className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[#00D4AA]"
                    />
                    <datalist id="probability-ticks">
                      {[0, 25, 50, 75, 100].map((v) => (
                        <option key={v} value={v} />
                      ))}
                    </datalist>
                    <div className="mt-1 flex justify-between text-xs text-gray-500">
                      <span>Very unlikely</span>
                      <span>50/50</span>
                      <span>Very likely</span>
                    </div>
                  </div>

                  {/* Reasoning (optional) */}
                  <div className="mb-6">
                    <label className="mb-2 block text-sm text-gray-400">
                      Reasoning (optional)
                    </label>
                    <textarea
                      value={reasoning}
                      onChange={(e) => setReasoning(e.target.value)}
                      placeholder="Why do you think this?"
                      rows={3}
                      className="w-full rounded-lg border border-gray-700 bg-[#1A2942] px-4 py-3 text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:outline-none focus:ring-1 focus:ring-[#00D4AA]"
                    />
                  </div>

                  <div className="rounded-lg bg-[#1A2942]/50 p-3 mb-4">
                    <p className="text-sm text-gray-400 flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
                      The market probability is hidden until you submit. This prevents
                      anchoring bias.
                    </p>
                  </div>

                  <Button
                    onClick={handleSubmitPrediction}
                    disabled={submitMutation.isPending}
                    className="w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
                  >
                    {submitMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Target className="mr-2 h-4 w-4" />
                    )}
                    Submit Prediction
                  </Button>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Methodology Modal */}
      <AnimatePresence>
        {showMethodology && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => setShowMethodology(false)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="w-full max-w-lg rounded-xl border border-gray-800 bg-[#111827] p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-semibold text-white">How Your Calibration Score Works</h3>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowMethodology(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="space-y-5 text-sm text-gray-300 leading-relaxed max-h-[70vh] overflow-y-auto">
                {/* Why it matters */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#00D4AA] mb-2">Why it matters</h4>
                  <p>
                    Calibration is the skill of matching your confidence to reality. When a calibrated
                    thinker says something is 70% likely, it happens about 70% of the time. When an
                    overconfident thinker says the same thing, they&apos;re often wrong — but loudly.
                  </p>
                  <p className="mt-2">
                    This skill is what separates great investors, forecasters, and decision-makers from
                    people who are occasionally right by accident. It&apos;s also a skill that almost no
                    education system teaches directly. LCS Engine measures it through deliberate practice
                    on real markets.
                  </p>
                </div>

                {/* How it's measured */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#00D4AA] mb-2">How it&apos;s measured</h4>
                  <p>
                    Your score (0–100) is derived from your resolved predictions over the last 90 days.
                    Recent predictions count more than older ones. We require a minimum of 5 resolved
                    predictions before computing the score — anything less is statistical noise.
                  </p>
                  <p className="mt-2">
                    Sub-scores break the metric down by question category (macro events, inflation,
                    employment, etc.) so you can see where your reasoning is strongest and where it
                    has room to grow.
                  </p>
                </div>

                {/* How to improve */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#00D4AA] mb-2">How to improve it</h4>
                  <p>
                    Make more predictions. The score improves through deliberate practice, not study.
                    Pay attention to your detected biases — they tell you where your reasoning is
                    systematically off.
                  </p>
                </div>

                {/* Technical detail */}
                <div className="rounded-lg bg-[#1A2942]/50 p-3">
                  <p className="text-xs text-gray-400">
                    <span className="font-medium text-gray-300">Technical: </span>
                    Score = 100 × (1 − 2 × weighted mean Brier score), clamped to 0–100.
                    Recency weights: 30d = 1.0, 30–60d = 0.7, 60–90d = 0.4.
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
    </ProGate>
  );
}
