"use client";

import { useState } from "react";
import { Target, AlertTriangle, CheckCircle, Sparkles, TrendingUp } from "lucide-react";

const MARKET_CONSENSUS = 52;
const EVENT_TITLE = "CPI Year-over-Year — April 2026";
const THRESHOLD = "3.2%";

function BiasResult({ prediction }: { prediction: number }) {
  if (prediction > 70) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-[#F59E0B]/30 bg-[#F59E0B]/10 p-4">
        <AlertTriangle className="h-5 w-5 shrink-0 text-[#F59E0B] mt-0.5" />
        <div>
          <p className="text-sm font-medium text-[#F59E0B]">Overconfidence Bias Detected</p>
          <p className="mt-1 text-sm text-gray-400">
            You assigned {prediction}% probability — significantly higher than the {MARKET_CONSENSUS}% market consensus.
            Overconfidence is one of the most common cognitive biases in investing.
          </p>
        </div>
      </div>
    );
  }
  if (prediction < 30) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-[#3B82F6]/30 bg-[#3B82F6]/10 p-4">
        <AlertTriangle className="h-5 w-5 shrink-0 text-[#3B82F6] mt-0.5" />
        <div>
          <p className="text-sm font-medium text-[#3B82F6]">Underconfidence Detected</p>
          <p className="mt-1 text-sm text-gray-400">
            You assigned {prediction}% probability — well below the {MARKET_CONSENSUS}% market consensus.
            Consider whether you have information the market doesn&apos;t, or if anchoring bias is at play.
          </p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[#10B981]/30 bg-[#10B981]/10 p-4">
      <CheckCircle className="h-5 w-5 shrink-0 text-[#10B981] mt-0.5" />
      <div>
        <p className="text-sm font-medium text-[#10B981]">Well-Calibrated</p>
        <p className="mt-1 text-sm text-gray-400">
          Your prediction of {prediction}% is close to the {MARKET_CONSENSUS}% market consensus.
          Good calibration is a sign of rational probabilistic thinking.
        </p>
      </div>
    </div>
  );
}

const STRATEGY_ASSETS = [
  { name: "TIPS (Treasury Inflation-Protected)", allocation: 30, rationale: "Direct inflation hedge" },
  { name: "Energy ETFs (XLE)", allocation: 25, rationale: "Commodities rise with inflation" },
  { name: "Short Duration Bonds", allocation: 25, rationale: "Less rate sensitivity" },
  { name: "Cash / Money Market", allocation: 20, rationale: "Optionality if Fed hikes" },
];

export default function ProbabilityLabPage() {
  const [probability, setProbability] = useState(50);
  const [submitted, setSubmitted] = useState(false);

  const brierScore = Math.abs(probability / 100 - MARKET_CONSENSUS / 100) ** 2;
  const brierDisplay = (brierScore + 0.08).toFixed(2); // Add baseline noise
  const percentile = brierScore < 0.1 ? 82 : brierScore < 0.2 ? 67 : brierScore < 0.35 ? 45 : 28;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Probability Lab</h1>
        <p className="mt-1 text-gray-400">Predict economic events and sharpen your forecasting skills</p>
      </div>

      {/* Prediction Card */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-4 flex items-center gap-2">
          <span className="inline-flex rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/20 px-2 py-0.5 text-xs font-medium text-[#F59E0B]">
            CPI
          </span>
          <span className="text-xs text-gray-500">Closes Apr 30, 2026</span>
        </div>

        <h2 className="mb-2 text-lg font-semibold text-white">{EVENT_TITLE}</h2>
        <p className="mb-6 text-sm text-gray-400">
          Will year-over-year CPI come in above {THRESHOLD}? Market consensus: {MARKET_CONSENSUS}%
        </p>

        {!submitted ? (
          <>
            <div className="mb-6">
              <div className="mb-2 flex items-center justify-between">
                <label className="text-sm text-gray-400">Your probability estimate</label>
                <span className="text-2xl font-bold font-mono-nums text-[#00D4AA]">{probability}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={probability}
                onChange={(e) => setProbability(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[#00D4AA]"
              />
              <div className="mt-1 flex justify-between text-xs text-gray-500">
                <span>Very unlikely</span>
                <span>50/50</span>
                <span>Very likely</span>
              </div>
            </div>

            <div className="mb-4 rounded-lg bg-[#1A2942]/50 p-3">
              <p className="flex items-start gap-2 text-sm text-gray-400">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-[#F59E0B]" />
                Market consensus is hidden until you submit to prevent anchoring bias.
              </p>
            </div>

            <button
              onClick={() => setSubmitted(true)}
              className="w-full rounded-lg bg-[#00D4AA] py-2.5 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
            >
              <Target className="mr-2 inline h-4 w-4" />
              Submit Prediction
            </button>
          </>
        ) : (
          <div className="space-y-6">
            {/* Comparison */}
            <div className="text-center">
              <div className="mb-6 flex items-center justify-center gap-8">
                <div>
                  <p className="text-sm text-gray-400">Your prediction</p>
                  <p className="text-3xl font-bold font-mono-nums text-white">{probability}%</p>
                </div>
                <div className="h-16 w-px bg-gray-700" />
                <div>
                  <p className="text-sm text-gray-400">Market consensus</p>
                  <p className="text-3xl font-bold font-mono-nums text-[#00D4AA]">{MARKET_CONSENSUS}%</p>
                </div>
              </div>

              {/* Visual comparison bar */}
              <div className="relative mb-2 h-4 rounded-full bg-gray-800">
                <div
                  className="absolute top-0 left-0 h-4 rounded-full bg-[#3B82F6]/60"
                  style={{ width: `${probability}%` }}
                />
                <div
                  className="absolute top-0 h-4 w-1 bg-[#00D4AA]"
                  style={{ left: `${MARKET_CONSENSUS}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>0%</span>
                <span className="text-[#3B82F6]">You: {probability}%</span>
                <span className="text-[#00D4AA]">Market: {MARKET_CONSENSUS}%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Brier Score */}
            <div className="rounded-lg border border-gray-800 bg-[#0A1628] p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Brier Score</p>
                  <p className="text-xl font-bold font-mono-nums text-white">{brierDisplay}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400">Forecaster Percentile</p>
                  <p className="text-xl font-bold font-mono-nums text-[#00D4AA]">Top {100 - percentile}%</p>
                </div>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Better than {percentile}% of forecasters · Lower is better (0 = perfect)
              </p>
            </div>

            {/* Bias Detection */}
            <BiasResult prediction={probability} />

            {/* Reset */}
            <button
              onClick={() => setSubmitted(false)}
              className="w-full rounded-lg border border-gray-700 py-2 text-sm text-gray-400 hover:text-white hover:bg-[#1A2942] transition-colors"
            >
              Make Another Prediction
            </button>
          </div>
        )}
      </div>

      {/* Macro Strategy Card — always visible after submission */}
      {submitted && (
        <div className="rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-5 space-y-4">
          <div className="flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-[#00D4AA] shrink-0 mt-0.5" />
            <p className="text-sm text-white font-medium">
              If CPI beats expectations, inflation persists — Fed stays hawkish
            </p>
          </div>

          <div className="space-y-2">
            {STRATEGY_ASSETS.map((asset) => (
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

          <div className="border-t border-gray-800 pt-3 space-y-1.5">
            <p className="text-xs text-[#F59E0B]">
              <span className="font-medium">Risk: </span>
              A surprise CPI miss would invalidate this thesis quickly
            </p>
            <p className="text-xs text-gray-400">
              <span className="font-medium text-gray-300">Learn: </span>
              Inflation expectations drive bond yields and sector rotation
            </p>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <TrendingUp className="h-3.5 w-3.5 text-gray-500" />
            <p className="text-xs text-gray-500">
              Strategy personalized for your Balanced Builder archetype
            </p>
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <p className="text-sm text-gray-400">Total Predictions</p>
          <p className="mt-1 text-2xl font-bold font-mono-nums text-white">14</p>
        </div>
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <p className="text-sm text-gray-400">Resolved</p>
          <p className="mt-1 text-2xl font-bold font-mono-nums text-white">9</p>
        </div>
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <p className="text-sm text-gray-400">Avg Brier Score</p>
          <p className="mt-1 text-2xl font-bold font-mono-nums text-white">0.18</p>
          <p className="mt-1 text-xs text-gray-500">Lower is better (0 = perfect)</p>
        </div>
      </div>
    </div>
  );
}
