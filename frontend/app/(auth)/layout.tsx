"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart3, Brain, TrendingUp, Target, Lock } from "lucide-react";

const highlights = [
  {
    icon: Brain,
    text: "Personalized AI investing tutor that knows your learning style",
  },
  {
    icon: TrendingUp,
    text: "Real-time paper trading with $100K virtual capital",
  },
  {
    icon: Target,
    text: "Bias detection + probability forecasting lab",
  },
];

const QA_PAIRS = [
  {
    user: "What is an ETF?",
    ai: "An ETF (exchange-traded fund) is like a sampler platter \u2014 instead of buying one stock, you get a basket of investments in a single purchase. It\u2019s one of the easiest ways to diversify without needing to pick individual winners.",
  },
  {
    user: "What is a dividend?",
    ai: "A dividend is a slice of a company\u2019s profits paid directly to shareholders \u2014 think of it as a thank-you check for being a part-owner. Some investors build entire portfolios around dividends for steady passive income.",
  },
  {
    user: "What is a stock?",
    ai: "A stock is a tiny ownership stake in a company. When you buy a share of Apple, you literally own a piece of the business \u2014 and as the company grows, your slice can become more valuable over time.",
  },
  {
    user: "What is a bond?",
    ai: "A bond is essentially an IOU \u2014 you lend money to a company or government, and they pay you back with interest. Bonds are generally steadier than stocks, which is why they\u2019re a go-to for balancing risk in a portfolio.",
  },
];

function AIChatPreview() {
  const [phase, setPhase] = useState<"user" | "pause" | "ai" | "done">("user");
  const [aiText, setAiText] = useState("");
  const [userVisible, setUserVisible] = useState(false);
  const [qaIndex, setQaIndex] = useState(0);

  useEffect(() => {
    setUserVisible(true);
    const timeout = setTimeout(() => setPhase("pause"), 600);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    let interval: ReturnType<typeof setInterval>;

    const currentAi = QA_PAIRS[qaIndex].ai;

    if (phase === "pause") {
      timeout = setTimeout(() => setPhase("ai"), 1000);
    } else if (phase === "ai") {
      let idx = 0;
      interval = setInterval(() => {
        idx++;
        setAiText(currentAi.slice(0, idx));
        if (idx >= currentAi.length) {
          clearInterval(interval);
          setPhase("done");
        }
      }, 18);
    } else if (phase === "done") {
      timeout = setTimeout(() => {
        setUserVisible(false);
        setAiText("");
        setQaIndex((prev) => (prev + 1) % QA_PAIRS.length);
        setPhase("user");
        setTimeout(() => {
          setUserVisible(true);
          setTimeout(() => setPhase("pause"), 600);
        }, 400);
      }, 3000);
    }

    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, [phase, qaIndex]);

  return (
    <div className="rounded-xl border border-gray-700/50 bg-[#0D1B2A] p-4 max-w-sm">
      <div className="mb-3 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-[#00D4AA]" />
        <span className="text-xs font-medium text-gray-500">LCS AI Tutor</span>
      </div>
      <div className="space-y-3 min-h-[7rem]">
        <AnimatePresence>
          {userVisible && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex justify-end"
            >
              <div className="rounded-xl rounded-br-sm bg-[#00D4AA]/15 px-3 py-2 text-sm text-gray-200">
                {QA_PAIRS[qaIndex].user}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {(phase === "ai" || phase === "done") && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex"
          >
            <div className="rounded-xl rounded-bl-sm bg-[#1A2942] px-3 py-2 text-sm leading-relaxed text-gray-300">
              {aiText}
              {phase === "ai" && (
                <span className="ml-0.5 inline-block h-3.5 w-0.5 bg-[#00D4AA] animate-pulse align-middle" />
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-[#0A1628]">
      {/* Subtle radial glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-32 top-1/3 h-[500px] w-[500px] rounded-full bg-[#00D4AA]/[0.07] blur-[120px]" />
      </div>

      {/* Left branding panel — hidden below lg */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 hidden lg:flex lg:w-[55%] flex-col justify-center px-16 2xl:px-24"
      >
        <div className="max-w-lg">
          {/* Logo */}
          <motion.div
            className="mb-10 flex items-center gap-3 group"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#00D4AA] transition-shadow group-hover:shadow-[0_0_20px_rgba(0,212,170,0.3)]">
              <BarChart3 className="h-6 w-6 text-[#0A1628]" />
            </div>
            <span className="text-2xl font-bold text-white">LCS Engine</span>
          </motion.div>

          {/* Headline */}
          <h2 className="mb-4 text-5xl font-bold leading-tight tracking-tight text-white">
            Learn to invest.{" "}
            <span className="text-[#00D4AA]">Without the fear.</span>
          </h2>

          {/* Subhead */}
          <p className="mb-10 max-w-[32rem] text-lg text-gray-400">
            AI-powered financial education that adapts to your goals, risk
            tolerance, and learning style.
          </p>

          {/* Feature bullets */}
          <div className="mb-10 space-y-5">
            {highlights.map((h, i) => (
              <motion.div
                key={h.text}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="group/item flex items-center gap-4"
                whileHover={{ x: 4 }}
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1A2942] transition-colors group-hover/item:bg-[#1A2942]/80">
                  <h.icon className="h-5 w-5 text-[#00D4AA]" />
                </div>
                <span className="text-base text-gray-300">{h.text}</span>
              </motion.div>
            ))}
          </div>

          {/* Animated chat preview */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="mb-10"
          >
            <AIChatPreview />
          </motion.div>

          {/* Social proof */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="mb-4 text-sm text-gray-400"
          >
            100+ Early Testers &middot; Paper trading only &mdash; no real money at risk
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1 }}
            className="mb-4 text-sm text-gray-400"
          >
            Built by a Columbia MBA. Backed by real market data.
          </motion.div>

          {/* Trust signals */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="flex items-center gap-1.5 text-xs text-gray-500"
          >
            <Lock className="h-3 w-3" />
            <span>
              Secure authentication &middot; Real-time data powered by Alpaca &amp;
              Polygon
            </span>
          </motion.div>
        </div>
      </motion.div>

      {/* Right form panel */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="relative z-10 flex w-full lg:w-[45%] flex-col items-center justify-center px-6 py-12"
      >
        {/* Mobile branding — shown when left panel is hidden */}
        <div className="mb-10 w-full max-w-lg lg:hidden">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#00D4AA]">
              <BarChart3 className="h-6 w-6 text-[#0A1628]" />
            </div>
            <span className="text-2xl font-bold text-white">LCS Engine</span>
          </div>
          <h2 className="mb-3 text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl">
            Learn to invest.{" "}
            <span className="text-[#00D4AA]">Without the fear.</span>
          </h2>
          <p className="mb-6 text-base text-gray-400">
            AI-powered financial education that adapts to your goals, risk
            tolerance, and learning style.
          </p>
          <div className="mb-8 space-y-3">
            {highlights.map((h) => (
              <div key={h.text} className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#1A2942]">
                  <h.icon className="h-4 w-4 text-[#00D4AA]" />
                </div>
                <span className="text-sm text-gray-300">{h.text}</span>
              </div>
            ))}
          </div>
        </div>
        {children}
      </motion.div>
    </div>
  );
}
