"use client";

import { useState, useMemo } from "react";
import { Shield, Search, Layers } from "lucide-react";
import { strategies, type Strategy } from "@/lib/mock-data";

const RISK_COLORS: Record<string, string> = {
  Low: "bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30",
  Medium: "bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30",
  High: "bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30",
};

const categories = ["All", ...Array.from(new Set(strategies.map((s) => s.category)))];
const assetClasses = ["All", ...Array.from(new Set(strategies.map((s) => s.assetClass)))];
const riskLevels = ["All", "Low", "Medium", "High"];
const explainLevels = ["Conservative", "Moderate", "Aggressive"];

export default function StrategiesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [assetClass, setAssetClass] = useState("All");
  const [risk, setRisk] = useState("All");
  const [explain, setExplain] = useState("Moderate");

  const filtered = useMemo(() => {
    return strategies.filter((s) => {
      if (search && !s.name.toLowerCase().includes(search.toLowerCase()) && !s.description.toLowerCase().includes(search.toLowerCase())) return false;
      if (category !== "All" && s.category !== category) return false;
      if (assetClass !== "All" && s.assetClass !== assetClass) return false;
      if (risk !== "All" && s.riskLevel !== risk) return false;
      return true;
    });
  }, [search, category, assetClass, risk]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Investment Strategies</h1>
          <p className="mt-1 text-gray-400">{strategies.length} strategies · Explain for: {explain}</p>
        </div>
        <select
          value={explain}
          onChange={(e) => setExplain(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#1A2942] px-3 py-2 text-sm text-white"
        >
          {explainLevels.map((l) => (
            <option key={l} value={l}>Explain for: {l}</option>
          ))}
        </select>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search strategies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-[#1A2942] pl-10 pr-4 py-2 text-sm text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:outline-none"
          />
        </div>
        <select value={category} onChange={(e) => setCategory(e.target.value)} className="rounded-lg border border-gray-700 bg-[#1A2942] px-3 py-2 text-sm text-white">
          {categories.map((c) => <option key={c} value={c}>{c === "All" ? "All Categories" : c}</option>)}
        </select>
        <select value={assetClass} onChange={(e) => setAssetClass(e.target.value)} className="rounded-lg border border-gray-700 bg-[#1A2942] px-3 py-2 text-sm text-white">
          {assetClasses.map((a) => <option key={a} value={a}>{a === "All" ? "All Asset Classes" : a}</option>)}
        </select>
        <select value={risk} onChange={(e) => setRisk(e.target.value)} className="rounded-lg border border-gray-700 bg-[#1A2942] px-3 py-2 text-sm text-white">
          {riskLevels.map((r) => <option key={r} value={r}>{r === "All" ? "All Risk Levels" : r}</option>)}
        </select>
      </div>

      {/* Results */}
      <p className="text-sm text-gray-500">{filtered.length} {filtered.length === 1 ? "strategy" : "strategies"} found</p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((strategy) => (
          <StrategyCard key={strategy.id} strategy={strategy} />
        ))}
      </div>
    </div>
  );
}

function StrategyCard({ strategy }: { strategy: Strategy }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#111827] p-5 card-hover-lift">
      <div className="mb-3 flex items-center gap-2">
        <span className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${RISK_COLORS[strategy.riskLevel]}`}>
          {strategy.riskLevel}
        </span>
        <span className="rounded-md bg-[#1A2942] px-2 py-0.5 text-xs text-gray-400">
          {strategy.category}
        </span>
      </div>
      <h3 className="mb-2 font-semibold text-white">{strategy.name}</h3>
      <p className="mb-4 text-sm text-gray-400 line-clamp-2">{strategy.description}</p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{strategy.assetClass}</span>
        <span className="font-mono-nums text-[#00D4AA]">{strategy.expectedReturn}</span>
      </div>
      <div className="mt-2 text-xs text-gray-500">
        <span>Horizon: {strategy.timeHorizon}</span>
      </div>
    </div>
  );
}
