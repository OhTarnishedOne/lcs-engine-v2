"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { DollarSign, TrendingUp, Wallet, BarChart3 } from "lucide-react";
import { portfolio, positions, portfolioChart } from "@/lib/mock-data";
import { formatCurrency, formatPercent } from "@/lib/utils";

const stats = [
  { label: "Total Value", value: formatCurrency(portfolio.totalValue), icon: DollarSign },
  { label: "Cash Balance", value: formatCurrency(portfolio.cash), icon: Wallet },
  { label: "Holdings", value: formatCurrency(portfolio.holdings), icon: BarChart3 },
  { label: "All-Time P&L", value: `${formatCurrency(portfolio.totalPL)} (${formatPercent(portfolio.totalPLPct)})`, icon: TrendingUp, positive: true },
];

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Portfolio Dashboard</h1>
        <p className="mt-1 text-gray-400">Overview of your simulated portfolio</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border border-gray-800 bg-[#111827] p-5">
            <div className="mb-2 flex items-center gap-2">
              <stat.icon className="h-4 w-4 text-gray-400" />
              <p className="text-sm text-gray-400">{stat.label}</p>
            </div>
            <p className={`text-xl font-bold font-mono-nums ${stat.positive ? "text-[#10B981]" : "text-white"}`}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
        <h2 className="mb-4 font-semibold text-white">Portfolio Growth — 6 Months</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={portfolioChart}>
              <XAxis dataKey="day" stroke="#6B7280" tick={false} axisLine={false} />
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
                        <p className="text-[#00D4AA] font-mono-nums">{formatCurrency(payload[0].value as number)}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#00D4AA" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Positions */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
        <h2 className="mb-4 font-semibold text-white">Open Positions</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                <th className="pb-3 text-left font-medium">Symbol</th>
                <th className="pb-3 text-left font-medium">Name</th>
                <th className="pb-3 text-right font-medium">Shares</th>
                <th className="pb-3 text-right font-medium">Price</th>
                <th className="pb-3 text-right font-medium">Market Value</th>
                <th className="pb-3 text-right font-medium">P&L</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.symbol} className="border-b border-gray-800/50">
                  <td className="py-3 font-semibold text-[#00D4AA]">{pos.symbol}</td>
                  <td className="py-3 text-gray-300">{pos.name}</td>
                  <td className="py-3 text-right text-white font-mono-nums">{pos.shares}</td>
                  <td className="py-3 text-right text-white font-mono-nums">${pos.currentPrice.toFixed(2)}</td>
                  <td className="py-3 text-right text-white font-mono-nums">{formatCurrency(pos.marketValue)}</td>
                  <td className={`py-3 text-right font-mono-nums ${pos.pl >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {formatCurrency(pos.pl)} ({formatPercent(pos.plPct)})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
