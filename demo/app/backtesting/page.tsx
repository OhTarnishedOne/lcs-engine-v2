"use client";

import { useState, useMemo } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import { strategies, backtestDefaults, generateGrowthChart, monthlyReturns } from "@/lib/mock-data";
import { formatPercent } from "@/lib/utils";

const timeframes = ["1Y", "2Y", "3Y", "5Y"];

export default function BacktestingPage() {
  const [selectedStrategy, setSelectedStrategy] = useState(backtestDefaults.strategyName);
  const [timeframe, setTimeframe] = useState(backtestDefaults.timeframe);

  const years = parseInt(timeframe);
  const chartData = useMemo(() => generateGrowthChart(years), [years]);

  const stats = [
    { label: "Total Return", value: formatPercent(backtestDefaults.totalReturn) },
    { label: "Alpha vs SPY", value: formatPercent(backtestDefaults.alphaVsSPY) },
    { label: "Win Rate", value: `${backtestDefaults.winRate}%` },
    { label: "Max Drawdown", value: formatPercent(backtestDefaults.maxDrawdown) },
    { label: "SPY Return", value: formatPercent(backtestDefaults.spyReturn) },
    { label: "Sharpe Ratio", value: backtestDefaults.sharpeRatio.toFixed(2) },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Backtesting</h1>
        <p className="mt-1 text-gray-400">Test strategies against historical market data</p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4">
        <select
          value={selectedStrategy}
          onChange={(e) => setSelectedStrategy(e.target.value)}
          className="rounded-lg border border-gray-700 bg-[#1A2942] px-4 py-2 text-sm text-white min-w-[220px]"
        >
          {strategies.map((s) => (
            <option key={s.id} value={s.name}>{s.name}</option>
          ))}
        </select>
        <div className="flex gap-1 rounded-lg bg-[#0A1628] p-1 border border-gray-800">
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`rounded-md px-4 py-1.5 text-xs font-medium transition-colors ${timeframe === tf ? "bg-[#00D4AA] text-[#0A1628]" : "text-gray-400 hover:text-white"}`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border border-gray-800 bg-[#111827] p-4">
            <p className="text-xs text-gray-400">{stat.label}</p>
            <p className="mt-1 text-lg font-bold font-mono-nums text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Growth Chart */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
        <h2 className="mb-4 font-semibold text-white">
          Growth of $10,000 — {selectedStrategy} vs SPY ({timeframe})
        </h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="month" stroke="#6B7280" tick={false} axisLine={false} />
              <YAxis
                stroke="#6B7280"
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload?.length) {
                    return (
                      <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                        <p className="text-[#00D4AA]">Strategy: ${(payload[0].value as number).toLocaleString()}</p>
                        <p className="text-[#3B82F6]">SPY: ${(payload[1].value as number).toLocaleString()}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                formatter={(value) => <span className="text-xs text-gray-400">{value === "strategy" ? selectedStrategy : "SPY"}</span>}
              />
              <Line type="monotone" dataKey="strategy" stroke="#00D4AA" strokeWidth={2} dot={false} name="strategy" />
              <Line type="monotone" dataKey="spy" stroke="#3B82F6" strokeWidth={2} dot={false} name="spy" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Returns */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
        <h2 className="mb-4 font-semibold text-white">Monthly Returns Distribution</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyReturns}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="month" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
              <YAxis
                stroke="#6B7280"
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload?.length) {
                    const val = payload[0].value as number;
                    return (
                      <div className="rounded-lg border border-gray-700 bg-[#1F2937] px-3 py-2 text-sm">
                        <p className={val >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}>{formatPercent(val)}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar
                dataKey="return"
                radius={[4, 4, 0, 0]}
                fill="#00D4AA"
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                shape={(props: any) => {
                  const { x, y, width, height, payload } = props;
                  const fill = payload.return >= 0 ? "#00D4AA" : "#EF4444";
                  return <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} />;
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Strategy Comparison Table */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
        <h2 className="mb-4 font-semibold text-white">Strategy Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                <th className="pb-3 text-left font-medium">Strategy</th>
                <th className="pb-3 text-right font-medium">Return</th>
                <th className="pb-3 text-right font-medium">Risk</th>
                <th className="pb-3 text-right font-medium">Category</th>
              </tr>
            </thead>
            <tbody>
              {strategies.slice(0, 8).map((s) => (
                <tr key={s.id} className={`border-b border-gray-800/50 ${s.name === selectedStrategy ? "bg-[#00D4AA]/5" : ""}`}>
                  <td className="py-3 font-medium text-white">{s.name}</td>
                  <td className="py-3 text-right font-mono-nums text-[#00D4AA]">{s.expectedReturn}</td>
                  <td className="py-3 text-right">
                    <span className={`rounded-md border px-2 py-0.5 text-xs font-medium ${s.riskLevel === "Low" ? "bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30" : s.riskLevel === "Medium" ? "bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30" : "bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30"}`}>
                      {s.riskLevel}
                    </span>
                  </td>
                  <td className="py-3 text-right text-gray-400">{s.category}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
