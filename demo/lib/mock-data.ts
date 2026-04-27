// =============================================================================
// Mock Data — all demo data lives here. No API calls, no external services.
// =============================================================================

// -- Portfolio ----------------------------------------------------------------

export const portfolio = {
  totalValue: 107240,
  cash: 42500,
  holdings: 64740,
  totalPL: 7240,
  totalPLPct: 7.24,
};

export const positions = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    shares: 50,
    avgCost: 168.5,
    currentPrice: 189.25,
    marketValue: 9462.5,
    pl: 1037.5,
    plPct: 12.3,
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    shares: 20,
    avgCost: 245.0,
    currentPrice: 234.95,
    marketValue: 4699.0,
    pl: -201.0,
    plPct: -4.1,
  },
  {
    symbol: "SPY",
    name: "SPDR S&P 500 ETF",
    shares: 30,
    avgCost: 462.0,
    currentPrice: 502.18,
    marketValue: 15065.4,
    pl: 1205.4,
    plPct: 8.7,
  },
];

export const portfolioChart = Array.from({ length: 180 }, (_, i) => {
  const base = 100000;
  const trend = (i / 180) * 8000;
  const noise = Math.sin(i * 0.15) * 1500 + Math.sin(i * 0.05) * 3000;
  const dip = i > 60 && i < 90 ? -(i - 60) * 80 : 0;
  return {
    day: i,
    value: Math.round(base + trend + noise + dip),
  };
});

// -- Trade History ------------------------------------------------------------

export const tradeHistory = [
  { id: "1", date: "2026-04-10", symbol: "AAPL", side: "BUY", qty: 25, price: 172.50, total: 4312.50, status: "filled" },
  { id: "2", date: "2026-04-08", symbol: "SPY", side: "BUY", qty: 30, price: 462.00, total: 13860.00, status: "filled" },
  { id: "3", date: "2026-04-05", symbol: "TSLA", side: "BUY", qty: 20, price: 245.00, total: 4900.00, status: "filled" },
  { id: "4", date: "2026-03-28", symbol: "AAPL", side: "BUY", qty: 25, price: 164.50, total: 4112.50, status: "filled" },
  { id: "5", date: "2026-03-15", symbol: "NVDA", side: "SELL", qty: 10, price: 875.20, total: 8752.00, status: "filled" },
];

export const marketWatch = [
  { symbol: "AAPL", name: "Apple Inc.", price: 189.25, change: 2.34, changePct: 1.25 },
  { symbol: "TSLA", name: "Tesla Inc.", price: 234.95, change: -3.12, changePct: -1.31 },
  { symbol: "SPY", name: "SPDR S&P 500", price: 502.18, change: 4.56, changePct: 0.92 },
  { symbol: "NVDA", name: "NVIDIA Corp.", price: 892.50, change: 15.30, changePct: 1.74 },
  { symbol: "MSFT", name: "Microsoft", price: 415.80, change: -1.20, changePct: -0.29 },
  { symbol: "AMZN", name: "Amazon", price: 186.40, change: 3.75, changePct: 2.05 },
  { symbol: "GOOGL", name: "Alphabet", price: 157.25, change: 0.85, changePct: 0.54 },
  { symbol: "META", name: "Meta Platforms", price: 498.10, change: 7.90, changePct: 1.61 },
];

// -- Strategies ---------------------------------------------------------------

export interface Strategy {
  id: string;
  name: string;
  description: string;
  riskLevel: "Low" | "Medium" | "High";
  assetClass: string;
  category: string;
  expectedReturn: string;
  timeHorizon: string;
}

export const strategies: Strategy[] = [
  { id: "1", name: "Momentum Breakout", description: "Captures upward price momentum in trending stocks using moving average crossovers and volume confirmation.", riskLevel: "High", assetClass: "Equities", category: "Momentum", expectedReturn: "+18-25%", timeHorizon: "3-6 months" },
  { id: "2", name: "Dividend Aristocrat", description: "Invests in companies with 25+ years of consecutive dividend increases for steady income.", riskLevel: "Low", assetClass: "Equities", category: "Income", expectedReturn: "+6-10%", timeHorizon: "5+ years" },
  { id: "3", name: "Growth at a Reasonable Price", description: "Targets growth companies trading below intrinsic value using PEG ratio screening.", riskLevel: "Medium", assetClass: "Equities", category: "Growth", expectedReturn: "+12-18%", timeHorizon: "1-3 years" },
  { id: "4", name: "Index Core + Satellite", description: "80% low-cost index funds, 20% satellite positions in high-conviction picks.", riskLevel: "Low", assetClass: "Mixed", category: "Balanced", expectedReturn: "+8-12%", timeHorizon: "3-5 years" },
  { id: "5", name: "Value Deep Dive", description: "Screens for undervalued companies with strong fundamentals and margin of safety.", riskLevel: "Medium", assetClass: "Equities", category: "Value", expectedReturn: "+10-15%", timeHorizon: "1-3 years" },
  { id: "6", name: "Bond Ladder", description: "Staggers bond maturities across 1-10 years for predictable income and reduced interest rate risk.", riskLevel: "Low", assetClass: "Fixed Income", category: "Income", expectedReturn: "+4-6%", timeHorizon: "1-10 years" },
  { id: "7", name: "Sector Rotation", description: "Rotates into sectors expected to outperform based on business cycle positioning.", riskLevel: "High", assetClass: "Equities", category: "Tactical", expectedReturn: "+15-22%", timeHorizon: "3-12 months" },
  { id: "8", name: "REIT Income", description: "Invests in diversified REITs for real estate exposure and regular dividend income.", riskLevel: "Medium", assetClass: "Real Estate", category: "Income", expectedReturn: "+7-11%", timeHorizon: "3-5 years" },
  { id: "9", name: "Small Cap Value", description: "Targets undervalued small-cap companies with potential for above-market growth.", riskLevel: "High", assetClass: "Equities", category: "Value", expectedReturn: "+14-20%", timeHorizon: "2-5 years" },
  { id: "10", name: "Risk Parity", description: "Allocates capital to equalize risk contribution across asset classes.", riskLevel: "Low", assetClass: "Mixed", category: "Balanced", expectedReturn: "+7-10%", timeHorizon: "5+ years" },
  { id: "11", name: "ESG Leaders", description: "Invests in companies with top ESG ratings without sacrificing returns.", riskLevel: "Medium", assetClass: "Equities", category: "Growth", expectedReturn: "+9-14%", timeHorizon: "3-5 years" },
  { id: "12", name: "Options Income", description: "Generates income through covered calls and cash-secured puts on quality holdings.", riskLevel: "High", assetClass: "Derivatives", category: "Income", expectedReturn: "+10-18%", timeHorizon: "Ongoing" },
  { id: "13", name: "International Diversifier", description: "Adds developed and emerging market exposure to reduce home country bias.", riskLevel: "Medium", assetClass: "Equities", category: "Balanced", expectedReturn: "+8-13%", timeHorizon: "3-5 years" },
  { id: "14", name: "Treasury Shield", description: "Allocates to treasury bonds and TIPS as a portfolio hedge during uncertainty.", riskLevel: "Low", assetClass: "Fixed Income", category: "Defensive", expectedReturn: "+3-5%", timeHorizon: "1-3 years" },
  { id: "15", name: "Tech Innovation", description: "Concentrates on disruptive technology companies driving long-term secular trends.", riskLevel: "High", assetClass: "Equities", category: "Growth", expectedReturn: "+18-30%", timeHorizon: "3-5 years" },
  { id: "16", name: "Inflation Hedge", description: "Combines TIPS, commodities, and real assets to protect purchasing power.", riskLevel: "Medium", assetClass: "Mixed", category: "Defensive", expectedReturn: "+5-8%", timeHorizon: "2-5 years" },
  { id: "17", name: "Micro-Cap Moonshot", description: "High-risk bets on micro-cap companies with asymmetric upside potential.", riskLevel: "High", assetClass: "Equities", category: "Momentum", expectedReturn: "+25-50%", timeHorizon: "1-3 years" },
  { id: "18", name: "Healthcare Compounder", description: "Invests in healthcare companies with durable competitive advantages and aging population tailwinds.", riskLevel: "Medium", assetClass: "Equities", category: "Growth", expectedReturn: "+11-16%", timeHorizon: "3-5 years" },
  { id: "19", name: "Cash Flow Kings", description: "Targets companies with consistently high free cash flow yields and shareholder-friendly capital allocation.", riskLevel: "Medium", assetClass: "Equities", category: "Value", expectedReturn: "+10-14%", timeHorizon: "2-5 years" },
  { id: "20", name: "All-Weather Portfolio", description: "Ray Dalio-inspired allocation designed to perform across all economic environments.", riskLevel: "Low", assetClass: "Mixed", category: "Balanced", expectedReturn: "+6-9%", timeHorizon: "5+ years" },
  { id: "21", name: "Emerging Markets Growth", description: "Captures growth in developing economies with younger demographics and rising middle class.", riskLevel: "High", assetClass: "Equities", category: "Growth", expectedReturn: "+12-22%", timeHorizon: "3-5 years" },
  { id: "22", name: "Mean Reversion", description: "Buys oversold quality stocks and sells overbought ones based on statistical deviations.", riskLevel: "Medium", assetClass: "Equities", category: "Tactical", expectedReturn: "+12-18%", timeHorizon: "1-6 months" },
];

// -- Backtesting --------------------------------------------------------------

export const backtestDefaults = {
  strategyName: "Momentum Breakout",
  timeframe: "3Y",
  totalReturn: 34.2,
  alphaVsSPY: 11.8,
  winRate: 67,
  maxDrawdown: -12.4,
  spyReturn: 22.4,
  sharpeRatio: 1.42,
  sortinoRatio: 1.87,
  trades: 156,
};

export function generateGrowthChart(years: number) {
  const points = years * 12;
  return Array.from({ length: points + 1 }, (_, i) => {
    const strategyGrowth = 10000 * Math.pow(1 + 0.34 / points, i) + Math.sin(i * 0.3) * 300;
    const spyGrowth = 10000 * Math.pow(1 + 0.224 / points, i) + Math.sin(i * 0.2) * 200;
    return {
      month: i,
      strategy: Math.round(strategyGrowth),
      spy: Math.round(spyGrowth),
    };
  });
}

export const monthlyReturns = [
  { month: "Jan", return: 3.2 }, { month: "Feb", return: -1.5 },
  { month: "Mar", return: 4.8 }, { month: "Apr", return: 2.1 },
  { month: "May", return: -0.8 }, { month: "Jun", return: 5.2 },
  { month: "Jul", return: 1.9 }, { month: "Aug", return: -2.3 },
  { month: "Sep", return: 3.7 }, { month: "Oct", return: 6.1 },
  { month: "Nov", return: 2.4 }, { month: "Dec", return: 4.5 },
];

// -- Risk Profile -------------------------------------------------------------

export const riskProfile = {
  archetype: "Balanced Builder",
  archetypeDescription: "You balance growth with protection. You're willing to take calculated risks, but you want to understand them first. You prefer diversified strategies and are building wealth methodically over time.",
  riskTolerance: "Moderate",
  timeHorizon: "3-5 years",
  experienceLevel: "Intermediate",
  primaryGoal: "Build long-term wealth while managing downside risk",
  interests: ["ETFs & Index Funds", "Individual Stocks", "Retirement Planning"],
  barriers: ["Fear of timing it wrong", "Too many choices"],
  learningStyle: "Visual learner — charts, graphs, and real examples",
};
