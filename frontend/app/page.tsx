"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  Brain,
  TrendingUp,
  Target,
  Lock,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

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
  const [phase, setPhase] = useState<"user" | "pause" | "ai" | "done">(
    "user"
  );
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
    <div className="rounded-xl border border-gray-700/50 bg-[#0D1B2A] p-4">
      <div className="mb-3 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-[#00D4AA]" />
        <span className="text-xs font-medium text-gray-500">LCS AI Tutor</span>
      </div>
      <div className="min-h-[7rem] space-y-3">
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
                <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-[#00D4AA] align-middle" />
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#0A1628]">
      {/* Subtle radial glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-32 top-1/3 h-[500px] w-[500px] rounded-full bg-[#00D4AA]/[0.07] blur-[120px]" />
        <div className="absolute -right-32 top-2/3 h-[400px] w-[400px] rounded-full bg-[#00D4AA]/[0.04] blur-[120px]" />
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10 lg:px-16">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#00D4AA]">
            <BarChart3 className="h-5 w-5 text-[#0A1628]" />
          </div>
          <span className="text-xl font-bold text-white">LCS Engine</span>
        </div>
        <div className="flex items-center gap-3">
          <a href="https://demo.lcsengine.com" target="_blank" rel="noopener noreferrer">
            <Button
              variant="ghost"
              className="text-sm text-gray-300 hover:text-white hover:bg-white/5"
            >
              Try Demo
            </Button>
          </a>
          <Link href="/pricing">
            <Button
              variant="ghost"
              className="text-sm text-gray-300 hover:text-white hover:bg-white/5"
            >
              Pricing
            </Button>
          </Link>
          <Link href="/login">
            <Button
              variant="ghost"
              className="text-sm text-gray-300 hover:text-white hover:bg-white/5"
            >
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button className="text-sm font-semibold bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]">
              Get Started For Free
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="relative z-10 mx-auto max-w-6xl px-6 pt-16 pb-20 sm:px-10 lg:px-16">
        <div className="grid gap-16 lg:grid-cols-2 lg:items-center">
          {/* Left — copy */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="mb-5 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
              Learn to invest.{" "}
              <span className="text-[#00D4AA]">Without the fear.</span>
            </h1>

            <p className="mb-10 max-w-xl text-lg text-gray-400">
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
                  className="flex items-center gap-4"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1A2942]">
                    <h.icon className="h-5 w-5 text-[#00D4AA]" />
                  </div>
                  <span className="text-base text-gray-300">{h.text}</span>
                </motion.div>
              ))}
            </div>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex flex-col gap-4 sm:flex-row sm:items-center"
            >
              <Link href="/register">
                <Button className="h-12 px-8 text-base font-semibold bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] hover:-translate-y-0.5 transition-all">
                  Get Started For Free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <span className="text-sm text-gray-500">
                Free. No credit card required.
              </span>
              <Link href="/pricing" className="text-sm text-gray-500 hover:text-gray-400 transition-colors">
                See pricing →
              </Link>
            </motion.div>
          </motion.div>

          {/* Right — chat preview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="flex justify-center lg:justify-end"
          >
            <div className="w-full max-w-md">
              <AIChatPreview />
            </div>
          </motion.div>
        </div>

        {/* Social proof + trust */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-20 border-t border-gray-800 pt-10"
        >
          <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:justify-center sm:gap-8 sm:text-left">
            <span className="text-sm text-gray-400">
              6 active learners &middot; 83% onboarding completion &middot; Institutional pilots in progress
            </span>
            <span className="hidden h-4 w-px bg-gray-700 sm:block" />
            <span className="text-sm text-gray-400">
              Built by a Columbia MBA. Backed by real market data.
            </span>
          </div>
          <div className="mt-6 flex items-center justify-center gap-1.5 text-xs text-gray-500">
            <Lock className="h-3 w-3" />
            <span>
              Secure authentication &middot; Real-time data powered by Alpaca
              &amp; Polygon
            </span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
