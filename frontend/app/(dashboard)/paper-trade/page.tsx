"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Wallet,
  TrendingUp,
  DollarSign,
  Search,
  Loader2,
  AlertTriangle,
  X,
  ShoppingCart,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { trackEvent } from "@/lib/analytics";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatCard, SkeletonCard, EmptyState } from "@/components/shared";


export default function PaperTradePage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [orderQty, setOrderQty] = useState("");
  const [orderType, setOrderType] = useState<"market" | "limit">("market");
  const [limitPrice, setLimitPrice] = useState("");
  const [showConfirmDialog, setShowConfirmDialog] = useState<{
    side: "buy" | "sell";
    symbol: string;
    qty: number;
  } | null>(null);

  // Fetch portfolio
  const { data: portfolio, isLoading: portfolioLoading, error: portfolioError } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => api.getPortfolio(),
    retry: false,
  });

  // Fetch positions
  const { data: positionsData, isLoading: positionsLoading } = useQuery({
    queryKey: ["positions"],
    queryFn: () => api.getPositions(),
    retry: false,
  });

  // Search symbols
  const { data: searchResults } = useQuery({
    queryKey: ["search-symbols", searchQuery],
    queryFn: () => api.searchSymbols(searchQuery),
    enabled: searchQuery.length >= 1,
  });

  // Get quote
  const { data: quote, isLoading: quoteLoading } = useQuery({
    queryKey: ["quote", selectedSymbol],
    queryFn: () => api.getQuote(selectedSymbol!),
    enabled: !!selectedSymbol,
    refetchInterval: 30000,
  });

  // Place order
  const orderMutation = useMutation({
    mutationFn: (order: {
      symbol: string;
      qty: number;
      side: "buy" | "sell";
      order_type: "market" | "limit";
      limit_price?: number;
    }) => api.placeOrder(order),
    onSuccess: () => {
      trackEvent("paper_trade_placed");
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["positions"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      setShowConfirmDialog(null);
      setOrderQty("");
      setLimitPrice("");
    },
  });

  const positions = positionsData || [];

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return "$0.00";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined) return "0.00%";
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const handleSelectSymbol = (symbol: string) => {
    setSelectedSymbol(symbol);
    setSearchQuery("");
  };

  const handlePlaceOrder = (side: "buy" | "sell") => {
    if (!selectedSymbol || !orderQty) return;
    const qty = parseFloat(orderQty);
    if (isNaN(qty) || qty <= 0) return;

    setShowConfirmDialog({
      side,
      symbol: selectedSymbol,
      qty,
    });
  };

  const confirmOrder = () => {
    if (!showConfirmDialog) return;

    orderMutation.mutate({
      symbol: showConfirmDialog.symbol,
      qty: showConfirmDialog.qty,
      side: showConfirmDialog.side,
      order_type: orderType,
      limit_price: orderType === "limit" ? parseFloat(limitPrice) : undefined,
    });
  };

  // API not configured state
  if (portfolioError) {
    return (
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-2xl font-bold text-white">Paper Trading</h1>
          <p className="mt-1 text-gray-400">
            Practice trading with simulated money
          </p>
        </motion.div>

        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-8 text-center">
          <AlertTriangle className="mx-auto mb-4 h-12 w-12 text-amber-400" />
          <h3 className="mb-2 text-lg font-semibold text-white">
            Paper Trading Not Configured
          </h3>
          <p className="mb-4 text-gray-400">
            Paper trading requires an Alpaca API connection. Contact your
            administrator to set up paper trading credentials.
          </p>
          <p className="text-sm text-gray-500">
            In the meantime, explore other features like AI Chat or the
            Probability Lab.
          </p>
        </div>
      </div>
    );
  }

  if (portfolioLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="h-8 w-48 rounded skeleton-shimmer" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl skeleton-shimmer" />
          ))}
        </div>
        <SkeletonCard lines={5} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-white">Paper Trading</h1>
        <p className="mt-1 text-gray-400">
          Practice trading with simulated money
        </p>
      </motion.div>

      {/* Portfolio Stats */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        <StatCard
          label="Total Equity"
          value={formatCurrency(portfolio?.equity)}
          icon={Wallet}
          change={
            portfolio?.total_pl_pct
              ? { value: portfolio.total_pl_pct, isPositive: portfolio.total_pl_pct >= 0 }
              : undefined
          }
        />
        <StatCard
          label="Cash"
          value={formatCurrency(portfolio?.cash)}
          icon={DollarSign}
        />
        <StatCard
          label="Buying Power"
          value={formatCurrency(portfolio?.buying_power)}
          icon={ShoppingCart}
        />
        <StatCard
          label="Total P&L"
          value={formatCurrency(portfolio?.total_pl)}
          valueClassName={
            (portfolio?.total_pl ?? 0) >= 0 ? "text-[#10B981]" : "text-[#EF4444]"
          }
          change={
            portfolio?.total_pl_pct
              ? { value: portfolio.total_pl_pct, isPositive: portfolio.total_pl_pct >= 0 }
              : undefined
          }
        />
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trade Panel */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-1"
        >
          <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
            <h3 className="mb-4 font-semibold text-white">Trade</h3>

            {/* Symbol search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
                placeholder="Search symbol (e.g., AAPL)"
                className="border-gray-700 bg-[#1A2942] pl-10 pr-9 text-white placeholder:text-gray-500"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  aria-label="Clear search"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              )}

              {/* Search results dropdown */}
              {searchQuery && searchResults && searchResults.length > 0 && (
                <div className="absolute left-0 right-0 top-full z-10 mt-1 max-h-48 overflow-y-auto rounded-lg border border-gray-700 bg-[#1F2937]">
                  {searchResults.map((result) => (
                    <button
                      key={result.ticker}
                      onClick={() => handleSelectSymbol(result.ticker)}
                      className="flex w-full items-center justify-between px-4 py-2 text-left hover:bg-[#1A2942]"
                    >
                      <div>
                        <span className="font-mono text-white">
                          {result.ticker}
                        </span>
                        <span className="ml-2 text-sm text-gray-400">
                          {result.name}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {result.type}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Selected symbol quote */}
            {selectedSymbol && (
              <div className="mb-4 rounded-lg bg-[#1A2942]/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono text-lg font-bold text-white">
                      {selectedSymbol}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="ml-2 h-6 w-6 text-gray-500 hover:text-white"
                      onClick={() => setSelectedSymbol(null)}
                      aria-label="Clear selected symbol"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                  {quoteLoading ? (
                    <div className="h-6 w-20 rounded skeleton-shimmer" />
                  ) : quote ? (
                    <div className="text-right">
                      <p className="font-mono text-lg font-bold text-white">
                        {formatCurrency(quote.price)}
                      </p>
                      <p
                        className={`font-mono text-sm ${
                          quote.change >= 0 ? "text-[#10B981]" : "text-[#EF4444]"
                        }`}
                      >
                        {quote.change >= 0 ? "+" : ""}
                        {quote.change.toFixed(2)} ({formatPercent(quote.change_pct)})
                      </p>
                    </div>
                  ) : null}
                </div>
              </div>
            )}

            {/* Order form */}
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm text-gray-400">
                  Quantity
                </label>
                <Input
                  type="number"
                  value={orderQty}
                  onChange={(e) => setOrderQty(e.target.value)}
                  placeholder="0"
                  min="1"
                  step="1"
                  className="border-gray-700 bg-[#1A2942] font-mono text-white placeholder:text-gray-500"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setOrderType("market")}
                  className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                    orderType === "market"
                      ? "bg-[#00D4AA]/20 text-[#00D4AA]"
                      : "bg-[#1A2942] text-gray-400 hover:text-white"
                  }`}
                >
                  Market
                </button>
                <button
                  onClick={() => setOrderType("limit")}
                  className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                    orderType === "limit"
                      ? "bg-[#00D4AA]/20 text-[#00D4AA]"
                      : "bg-[#1A2942] text-gray-400 hover:text-white"
                  }`}
                >
                  Limit
                </button>
              </div>

              <AnimatePresence>
                {orderType === "limit" && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div>
                      <label className="mb-1 block text-sm text-gray-400">
                        Limit Price
                      </label>
                      <Input
                        type="number"
                        value={limitPrice}
                        onChange={(e) => setLimitPrice(e.target.value)}
                        placeholder="0.00"
                        step="0.01"
                        className="border-gray-700 bg-[#1A2942] font-mono text-white placeholder:text-gray-500"
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="flex gap-3">
                <Button
                  onClick={() => handlePlaceOrder("buy")}
                  disabled={!selectedSymbol || !orderQty || orderMutation.isPending}
                  className="flex-1 bg-[#10B981] text-white hover:bg-[#059669]"
                >
                  Buy
                </Button>
                <Button
                  onClick={() => handlePlaceOrder("sell")}
                  disabled={!selectedSymbol || !orderQty || orderMutation.isPending}
                  className="flex-1 bg-[#EF4444] text-white hover:bg-[#DC2626]"
                >
                  Sell
                </Button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Positions */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2"
        >
          <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
            <h3 className="mb-4 font-semibold text-white">Positions</h3>

            {positionsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 rounded-lg skeleton-shimmer" />
                ))}
              </div>
            ) : positions.length === 0 ? (
              <EmptyState
                icon={TrendingUp}
                title="No positions yet"
                description="Search for a stock symbol above, then place a buy order to open your first position."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-[#111827]">
                    <tr className="border-b border-gray-800 text-left text-sm text-gray-400">
                      <th className="pb-3 pr-4">Symbol</th>
                      <th className="pb-3 pr-4 text-right">Shares</th>
                      <th className="pb-3 pr-4 text-right">Avg Price</th>
                      <th className="pb-3 pr-4 text-right">Current</th>
                      <th className="pb-3 pr-4 text-right">P&L</th>
                      <th className="pb-3 text-right">P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position) => (
                      <tr
                        key={position.symbol}
                        className="border-b border-gray-800/50"
                      >
                        <td className="py-3 pr-4">
                          <button
                            onClick={() => handleSelectSymbol(position.symbol)}
                            className="font-mono font-medium text-white hover:text-[#00D4AA]"
                          >
                            {position.symbol}
                          </button>
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-gray-300">
                          {position.qty}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-gray-300">
                          {formatCurrency(position.avg_entry_price)}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-white">
                          {formatCurrency(position.current_price)}
                        </td>
                        <td
                          className={`py-3 pr-4 text-right font-mono ${
                            position.unrealized_pl >= 0
                              ? "text-[#10B981]"
                              : "text-[#EF4444]"
                          }`}
                        >
                          {formatCurrency(position.unrealized_pl)}
                        </td>
                        <td
                          className={`py-3 text-right font-mono ${
                            position.unrealized_pl_pct >= 0
                              ? "text-[#10B981]"
                              : "text-[#EF4444]"
                          }`}
                        >
                          {formatPercent(position.unrealized_pl_pct)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Confirmation Dialog */}
      <AnimatePresence>
        {showConfirmDialog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => setShowConfirmDialog(null)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="w-full max-w-sm rounded-xl border border-gray-800 bg-[#111827] p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-lg font-semibold text-white">
                Confirm {showConfirmDialog.side === "buy" ? "Buy" : "Sell"} Order
              </h3>

              <div className="mb-6 space-y-2 rounded-lg bg-[#1A2942]/50 p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Symbol</span>
                  <span className="font-mono text-white">
                    {showConfirmDialog.symbol}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Quantity</span>
                  <span className="font-mono text-white">
                    {showConfirmDialog.qty}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Order Type</span>
                  <span className="text-white capitalize">{orderType}</span>
                </div>
                {orderType === "limit" && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Limit Price</span>
                    <span className="font-mono text-white">
                      {formatCurrency(parseFloat(limitPrice))}
                    </span>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowConfirmDialog(null)}
                  className="flex-1 border-gray-700 text-gray-300"
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmOrder}
                  disabled={orderMutation.isPending}
                  className={`flex-1 ${
                    showConfirmDialog.side === "buy"
                      ? "bg-[#10B981] hover:bg-[#059669]"
                      : "bg-[#EF4444] hover:bg-[#DC2626]"
                  } text-white`}
                >
                  {orderMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Confirm {showConfirmDialog.side === "buy" ? "Buy" : "Sell"}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
