"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Plus,
  Sparkles,
  Loader2,
  Trash2,
  Scale,
  HelpCircle,
  X,
  ChevronDown,
  ChevronUp,
  Lightbulb,
} from "lucide-react";

import { toast } from "sonner";
import { api } from "@/lib/api/client";
import { trackEvent } from "@/lib/analytics";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SkeletonCard, RiskMeter, EmptyState } from "@/components/shared";
import { UpgradeBanner } from "@/components/UpgradeBanner";
import { DisclaimerInline } from "@/components/Disclaimer";
import { useBillingStatus } from "@/hooks/useBillingStatus";
import type { Strategy } from "@/lib/api/types";

const STRATEGY_COLORS: Record<string, string> = {
  value: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  growth: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  income: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  momentum: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  balanced: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  index: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const CHART_COLORS = [
  "#00D4AA",
  "#3B82F6",
  "#F59E0B",
  "#8B5CF6",
  "#EC4899",
  "#10B981",
  "#EF4444",
];

export default function StrategiesPage() {
  const { isPro } = useBillingStatus();
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [showExplainModal, setShowExplainModal] = useState<string | null>(null);
  const [explainQuestion, setExplainQuestion] = useState("");

  // Fetch strategies
  const { data: strategiesData, isLoading } = useQuery({
    queryKey: ["strategies"],
    queryFn: () => api.getStrategies(),
  });

  // Generate strategy
  const generateMutation = useMutation({
    mutationFn: (strategyType?: string) =>
      api.generateStrategy(strategyType ? { strategy_type: strategyType } : undefined),
    onSuccess: () => {
      trackEvent("strategy_generated");
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
      toast.success("Strategy generated successfully");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to generate strategy");
    },
  });

  // Delete strategy
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteStrategy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
      toast.success("Strategy deleted");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to delete strategy");
    },
  });

  // Compare strategies
  const compareMutation = useMutation({
    mutationFn: (strategyIds: string[]) =>
      api.compareStrategies({ strategy_ids: strategyIds }),
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to compare strategies");
    },
  });

  // Explain strategy
  const explainMutation = useMutation({
    mutationFn: ({ id, question }: { id: string; question: string }) =>
      api.explainStrategy(id, { question }),
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to explain strategy");
    },
  });

  const strategies = strategiesData?.strategies || [];

  const toggleCompare = (id: string) => {
    setSelectedForCompare((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : prev.length < 3
        ? [...prev, id]
        : prev
    );
  };

  const handleCompare = async () => {
    if (selectedForCompare.length >= 2) {
      await compareMutation.mutateAsync(selectedForCompare);
    }
  };

  const handleExplain = async (strategyId: string) => {
    if (explainQuestion.trim()) {
      await explainMutation.mutateAsync({
        id: strategyId,
        question: explainQuestion,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 rounded skeleton-shimmer" />
          <div className="h-10 w-40 rounded skeleton-shimmer" />
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Investment Strategies</h1>
          <p className="mt-1 text-gray-400">
            AI-generated strategies personalized for your goals
          </p>
        </div>
        <div className="flex gap-3">
          {strategies.length >= 2 && (
            <Button
              variant="outline"
              onClick={() => {
                setCompareMode(!compareMode);
                setSelectedForCompare([]);
              }}
              className="border-gray-700 text-gray-300 hover:bg-[#1A2942]"
            >
              <Scale className="mr-2 h-4 w-4" />
              {compareMode ? "Cancel" : "Compare"}
            </Button>
          )}
          {isPro ? (
            <Button
              onClick={() => generateMutation.mutate(undefined)}
              disabled={generateMutation.isPending}
              className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
            >
              {generateMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-2 h-4 w-4" />
              )}
              Generate Strategy
            </Button>
          ) : (
            <Button
              onClick={() => window.location.href = "/pricing"}
              className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Upgrade to Generate
            </Button>
          )}
        </div>
      </motion.div>

      {/* Compare bar */}
      <AnimatePresence>
        {compareMode && selectedForCompare.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-6 flex items-center justify-between rounded-lg border border-[#00D4AA]/30 bg-[#00D4AA]/10 p-4"
          >
            <p className="text-sm text-gray-300">
              {selectedForCompare.length} strategies selected
              {selectedForCompare.length < 2 && " (select at least 2)"}
            </p>
            <Button
              onClick={handleCompare}
              disabled={selectedForCompare.length < 2 || compareMutation.isPending}
              className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
            >
              {compareMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Scale className="mr-2 h-4 w-4" />
              )}
              Compare
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Comparison result */}
      <AnimatePresence>
        {compareMutation.data && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mb-6 rounded-xl border border-gray-800 bg-[#111827] p-6"
          >
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold text-white">Comparison Result</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => compareMutation.reset()}
                aria-label="Close comparison"
                className="text-gray-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">
              {compareMutation.data.comparison_text}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Strategies grid */}
      {strategies.length === 0 ? (
        isPro ? (
          <EmptyState
            icon={Sparkles}
            title="No strategies yet"
            description="Generate your first AI-powered investment strategy to get started."
            action={{
              label: "Generate Strategy",
              onClick: () => generateMutation.mutate(undefined),
            }}
          />
        ) : (
          <UpgradeBanner feature="AI-generated investment strategies" />
        )
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {strategies.map((strategy, index) => (
            <motion.div
              key={strategy.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <StrategyCard
                strategy={strategy}
                isExpanded={expandedId === strategy.id}
                onToggleExpand={() => {
                  const expanding = expandedId !== strategy.id;
                  setExpandedId(expanding ? strategy.id : null);
                  if (expanding) trackEvent("strategy_viewed");
                }}
                compareMode={compareMode}
                isSelected={selectedForCompare.includes(strategy.id)}
                onToggleCompare={() => toggleCompare(strategy.id)}
                onDelete={() => deleteMutation.mutate(strategy.id)}
                onExplain={() => setShowExplainModal(strategy.id)}
                chartColors={CHART_COLORS}
              />
            </motion.div>
          ))}
        </div>
      )}

      {/* Explain Modal */}
      <AnimatePresence>
        {showExplainModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => {
              setShowExplainModal(null);
              setExplainQuestion("");
              explainMutation.reset();
            }}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="w-full max-w-lg rounded-xl border border-gray-800 bg-[#111827] p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-semibold text-white">Ask about this strategy</h3>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setShowExplainModal(null);
                    setExplainQuestion("");
                    explainMutation.reset();
                  }}
                  aria-label="Close dialog"
                  className="text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="mb-4">
                <Input
                  value={explainQuestion}
                  onChange={(e) => setExplainQuestion(e.target.value)}
                  placeholder="e.g., Why does this strategy include bonds?"
                  className="border-gray-700 bg-[#1A2942] text-white placeholder:text-gray-500"
                />
              </div>

              <Button
                onClick={() => handleExplain(showExplainModal)}
                disabled={!explainQuestion.trim() || explainMutation.isPending}
                className="mb-4 w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
              >
                {explainMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <HelpCircle className="mr-2 h-4 w-4" />
                )}
                Ask
              </Button>

              {explainMutation.data && (
                <div className="rounded-lg bg-[#1A2942]/50 p-4">
                  <p className="text-sm text-gray-300 whitespace-pre-wrap">
                    {explainMutation.data.explanation}
                  </p>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <DisclaimerInline className="mt-8" />
    </div>
  );
}

interface StrategyCardProps {
  strategy: Strategy;
  isExpanded: boolean;
  onToggleExpand: () => void;
  compareMode: boolean;
  isSelected: boolean;
  onToggleCompare: () => void;
  onDelete: () => void;
  onExplain: () => void;
  chartColors: string[];
}

function StrategyCard({
  strategy,
  isExpanded,
  onToggleExpand,
  compareMode,
  isSelected,
  onToggleCompare,
  onDelete,
  onExplain,
  chartColors,
}: StrategyCardProps) {
  const chartData = (strategy.assets || []).map((asset) => ({
    name: `${asset.ticker} - ${asset.name}`,
    value: Math.round(asset.allocation_pct),
  }));

  const typeColor =
    STRATEGY_COLORS[strategy.strategy_type.toLowerCase()] ||
    STRATEGY_COLORS.balanced;

  return (
    <div
      className={`rounded-xl border bg-[#111827] transition-all ${
        isSelected
          ? "border-[#00D4AA] shadow-[0_0_20px_rgba(0,212,170,0.15)]"
          : "border-gray-800"
      }`}
    >
      {/* Header */}
      <div className="p-5">
        <div className="mb-3 flex items-start justify-between">
          <div className="flex-1">
            <div className="mb-2 flex items-center gap-2">
              <span
                className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${typeColor}`}
              >
                {strategy.strategy_type}
              </span>
              <RiskMeter level={strategy.risk_level} />
            </div>
            <h3 className="font-semibold text-white">{strategy.name}</h3>
          </div>
          {compareMode && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={onToggleCompare}
              aria-label={`Select ${strategy.name} for comparison`}
              className="mt-1 h-5 w-5 rounded border-gray-600 bg-[#1A2942] text-[#00D4AA] focus:ring-[#00D4AA]"
            />
          )}
        </div>

        <p className="text-sm text-gray-400 line-clamp-2">
          {strategy.description}
        </p>

        {/* Mini chart */}
        <div className="mt-4 h-32">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={30}
                outerRadius={50}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={chartColors[index % chartColors.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                        <p className="text-white">{payload[0].name}</p>
                        <p className="font-mono text-[#00D4AA]">
                          {payload[0].value}%
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Expand button */}
        <button
          onClick={onToggleExpand}
          className="mt-3 flex w-full items-center justify-center gap-1 text-sm text-gray-400 hover:text-white"
        >
          {isExpanded ? (
            <>
              Less details <ChevronUp className="h-4 w-4" />
            </>
          ) : (
            <>
              More details <ChevronDown className="h-4 w-4" />
            </>
          )}
        </button>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-gray-800"
          >
            <div className="space-y-4 p-5">
              {/* Allocation breakdown */}
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-300">
                  Asset Allocation
                </h4>
                <div className="space-y-2">
                  {chartData.map((item, index) => (
                    <div key={item.name} className="flex items-center gap-3">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{
                          backgroundColor:
                            chartColors[index % chartColors.length],
                        }}
                      />
                      <span className="flex-1 text-sm text-gray-400">
                        {item.name}
                      </span>
                      <span className="font-mono text-sm text-white">
                        {item.value}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Rationale */}
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-300">
                  Rationale
                </h4>
                <p className="text-sm text-gray-400">{strategy.rationale}</p>
              </div>

              {/* Risks */}
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-300">
                  Risks
                </h4>
                <p className="text-sm text-gray-400">
                  {strategy.risks}
                </p>
              </div>

              {/* Learning Points */}
              {strategy.learning_points.length > 0 && (
                <div>
                  <h4 className="mb-2 flex items-center gap-2 text-sm font-medium text-gray-300">
                    <Lightbulb className="h-4 w-4 text-[#00D4AA]" />
                    Learning Points
                  </h4>
                  <ul className="space-y-2">
                    {strategy.learning_points.map((point, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-gray-400"
                      >
                        <span className="text-[#00D4AA]">•</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onExplain}
                  className="flex-1 border-gray-700 text-gray-300 hover:bg-[#1A2942]"
                >
                  <HelpCircle className="mr-2 h-4 w-4" />
                  Explain
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onDelete}
                  className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
