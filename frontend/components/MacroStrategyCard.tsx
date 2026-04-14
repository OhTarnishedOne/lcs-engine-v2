"use client";

import { useState } from "react";
import { Sparkles, Loader2, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";

interface MacroStrategyCardProps {
  marketId: string;
  marketTitle: string;
  userPrediction: number;
}

interface StrategyAsset {
  name: string;
  allocation: number;
  rationale: string;
}

interface MacroStrategy {
  thesis: string;
  assets: StrategyAsset[];
  risk_note: string;
  learning_point: string;
}

export function MacroStrategyCard({
  marketId,
  marketTitle,
  userPrediction,
}: MacroStrategyCardProps) {
  const [strategy, setStrategy] = useState<MacroStrategy | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStrategy = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.post<{ strategy: string }>(
        "/probability/macro-strategy",
        { market_id: marketId, market_title: marketTitle, user_prediction: userPrediction }
      );
      const parsed: MacroStrategy = JSON.parse(res.strategy);
      setStrategy(parsed);
    } catch {
      setError("Couldn't generate strategy. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // CTA before user clicks
  if (!strategy && !isLoading) {
    return (
      <div className="mt-4 rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-5 w-5 text-[#00D4AA] shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">
              See how your macro view affects a portfolio
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              Based on your CPI prediction + your investor profile
            </p>
          </div>
          <Button
            onClick={fetchStrategy}
            className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] text-xs px-3 py-1.5 h-auto"
          >
            Generate
          </Button>
        </div>
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="mt-4 rounded-xl border border-gray-800 bg-[#111827] p-4 flex items-center gap-3">
        <Loader2 className="h-4 w-4 text-[#00D4AA] animate-spin" />
        <p className="text-sm text-gray-400">Building your macro strategy...</p>
      </div>
    );
  }

  if (!strategy) return null;

  return (
    <div className="mt-4 rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-5 space-y-4">
      {/* Thesis */}
      <div className="flex items-start gap-2">
        <Sparkles className="h-4 w-4 text-[#00D4AA] shrink-0 mt-0.5" />
        <p className="text-sm text-white font-medium">{strategy.thesis}</p>
      </div>

      {/* Allocation bars */}
      <div className="space-y-2">
        {strategy.assets.map((asset) => (
          <div key={asset.name}>
            <div className="flex justify-between mb-1">
              <span className="text-xs text-gray-300">{asset.name}</span>
              <span className="text-xs text-[#00D4AA] font-medium">{asset.allocation}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-gray-800">
              <div
                className="h-1.5 rounded-full bg-[#00D4AA]"
                style={{ width: `${asset.allocation}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{asset.rationale}</p>
          </div>
        ))}
      </div>

      {/* Risk note + learning point */}
      <div className="border-t border-gray-800 pt-3 space-y-1.5">
        <p className="text-xs text-amber-400">
          <span className="font-medium">Risk: </span>{strategy.risk_note}
        </p>
        <p className="text-xs text-gray-400">
          <span className="font-medium text-gray-300">Learn: </span>
          {strategy.learning_point}
        </p>
      </div>
    </div>
  );
}
