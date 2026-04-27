"use client";

import { useState } from "react";
import { DollarSign, TrendingUp, Wallet, BarChart3 } from "lucide-react";
import { portfolio, positions, tradeHistory, marketWatch } from "@/lib/mock-data";
import { formatCurrency, formatPercent } from "@/lib/utils";

type Tab = "positions" | "history" | "market";

export default function PaperTradingPage() {
  const [tab, setTab] = useState<Tab>("positions");
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [qty, setQty] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handlePlaceOrder = () => {
    if (!symbol || !qty) return;
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 2000);
  };

  const stats = [
    { label: "Total Value", value: formatCurrency(portfolio.totalValue), icon: DollarSign },
    { label: "Cash", value: formatCurrency(portfolio.cash), icon: Wallet },
    { label: "Holdings", value: formatCurrency(portfolio.holdings), icon: BarChart3 },
    { label: "P&L", value: formatCurrency(portfolio.totalPL), icon: TrendingUp, positive: true },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Paper Trading</h1>
        <p className="mt-1 text-gray-400">Practice trading with $100K virtual capital</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border border-gray-800 bg-[#111827] p-4">
            <div className="mb-1 flex items-center gap-2">
              <stat.icon className="h-4 w-4 text-gray-400" />
              <p className="text-xs text-gray-400">{stat.label}</p>
            </div>
            <p className={`text-lg font-bold font-mono-nums ${stat.positive ? "text-[#10B981]" : "text-white"}`}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Order Panel */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
          <h2 className="mb-4 font-semibold text-white">Place Order</h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs text-gray-400">Symbol</label>
              <input
                type="text"
                placeholder="e.g. AAPL"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full rounded-lg border border-gray-700 bg-[#1A2942] px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Side</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setSide("BUY")}
                  className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${side === "BUY" ? "bg-[#10B981] text-white" : "border border-gray-700 text-gray-400 hover:text-white"}`}
                >
                  BUY
                </button>
                <button
                  onClick={() => setSide("SELL")}
                  className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${side === "SELL" ? "bg-[#EF4444] text-white" : "border border-gray-700 text-gray-400 hover:text-white"}`}
                >
                  SELL
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Quantity</label>
              <input
                type="number"
                placeholder="0"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-[#1A2942] px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:outline-none"
              />
            </div>
            <button
              onClick={handlePlaceOrder}
              className="w-full rounded-lg bg-[#00D4AA] py-2.5 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
            >
              {submitted ? "Order Placed ✓" : `${side} ${symbol || "..."}`}
            </button>
          </div>
        </div>

        {/* Data Tables */}
        <div className="lg:col-span-2 rounded-xl border border-gray-800 bg-[#111827] p-5">
          {/* Tabs */}
          <div className="mb-4 flex gap-1 rounded-lg bg-[#0A1628] p-1">
            {(["positions", "history", "market"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${tab === t ? "bg-[#1A2942] text-white" : "text-gray-400 hover:text-gray-200"}`}
              >
                {t === "positions" ? "Positions" : t === "history" ? "Trade History" : "Market Watch"}
              </button>
            ))}
          </div>

          {tab === "positions" && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-400">
                    <th className="pb-3 text-left font-medium">Symbol</th>
                    <th className="pb-3 text-right font-medium">Shares</th>
                    <th className="pb-3 text-right font-medium">Price</th>
                    <th className="pb-3 text-right font-medium">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.symbol} className="border-b border-gray-800/50">
                      <td className="py-3">
                        <span className="font-semibold text-white">{pos.symbol}</span>
                        <span className="ml-2 text-xs text-gray-500">{pos.name}</span>
                      </td>
                      <td className="py-3 text-right text-white font-mono-nums">{pos.shares}</td>
                      <td className="py-3 text-right text-white font-mono-nums">${pos.currentPrice.toFixed(2)}</td>
                      <td className={`py-3 text-right font-mono-nums ${pos.pl >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                        {formatPercent(pos.plPct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "history" && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-400">
                    <th className="pb-3 text-left font-medium">Date</th>
                    <th className="pb-3 text-left font-medium">Symbol</th>
                    <th className="pb-3 text-left font-medium">Side</th>
                    <th className="pb-3 text-right font-medium">Qty</th>
                    <th className="pb-3 text-right font-medium">Price</th>
                    <th className="pb-3 text-right font-medium">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {tradeHistory.map((trade) => (
                    <tr key={trade.id} className="border-b border-gray-800/50">
                      <td className="py-3 text-gray-400">{trade.date}</td>
                      <td className="py-3 font-semibold text-white">{trade.symbol}</td>
                      <td className="py-3">
                        <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${trade.side === "BUY" ? "bg-[#10B981]/20 text-[#10B981]" : "bg-[#EF4444]/20 text-[#EF4444]"}`}>
                          {trade.side}
                        </span>
                      </td>
                      <td className="py-3 text-right text-white font-mono-nums">{trade.qty}</td>
                      <td className="py-3 text-right text-white font-mono-nums">${trade.price.toFixed(2)}</td>
                      <td className="py-3 text-right text-white font-mono-nums">{formatCurrency(trade.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "market" && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-400">
                    <th className="pb-3 text-left font-medium">Symbol</th>
                    <th className="pb-3 text-left font-medium">Name</th>
                    <th className="pb-3 text-right font-medium">Price</th>
                    <th className="pb-3 text-right font-medium">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {marketWatch.map((stock) => (
                    <tr key={stock.symbol} className="border-b border-gray-800/50">
                      <td className="py-3 font-semibold text-[#00D4AA]">{stock.symbol}</td>
                      <td className="py-3 text-gray-300">{stock.name}</td>
                      <td className="py-3 text-right text-white font-mono-nums">${stock.price.toFixed(2)}</td>
                      <td className={`py-3 text-right font-mono-nums ${stock.change >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                        {stock.change >= 0 ? "+" : ""}{stock.change.toFixed(2)} ({formatPercent(stock.changePct)})
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
