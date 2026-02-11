"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Brain,
  Layers,
  TrendingUp,
  Target,
  ArrowRight,
  AlertCircle,
  Sparkles,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";

const quickActions = [
  {
    title: "Ask AI",
    description: "Get personalized answers to your investing questions",
    href: "/chat",
    icon: Brain,
    color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    iconColor: "text-blue-400",
  },
  {
    title: "Generate Strategy",
    description: "Create an AI-powered investment strategy",
    href: "/strategies",
    icon: Layers,
    color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    iconColor: "text-purple-400",
  },
  {
    title: "Paper Trade",
    description: "Practice trading with simulated money",
    href: "/paper-trade",
    icon: TrendingUp,
    color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    iconColor: "text-emerald-400",
  },
  {
    title: "Predict Markets",
    description: "Test your judgment on economic events",
    href: "/probability-lab",
    icon: Target,
    color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    iconColor: "text-amber-400",
  },
];

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [greeting, setGreeting] = useState("Welcome");

  // Fetch profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => api.getProfile(),
  });

  // Fetch onboarding progress
  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ["onboarding-progress"],
    queryFn: () => api.getOnboardingProgress(),
  });

  // Set time-based greeting
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 18) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  const isOnboardingComplete = progress?.is_complete ?? false;
  const userName = profile?.persona
    ? profile.persona.charAt(0).toUpperCase() + profile.persona.slice(1)
    : user?.email?.split("@")[0] || "there";

  return (
    <div className="mx-auto max-w-6xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        {profileLoading ? (
          <div className="h-10 w-64 rounded skeleton-shimmer" />
        ) : (
          <h1 className="text-3xl font-bold text-white">
            {greeting}, {userName}!
          </h1>
        )}
        <p className="mt-2 text-gray-400">
          {isOnboardingComplete
            ? "What would you like to learn today?"
            : "Let's get you set up for success."}
        </p>
      </motion.div>

      {/* Onboarding CTA (if not complete) */}
      {!progressLoading && !isOnboardingComplete && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <Link href="/onboarding">
            <div className="group relative overflow-hidden rounded-xl border border-[#00D4AA]/30 bg-gradient-to-r from-[#00D4AA]/10 to-[#00D4AA]/5 p-6 card-hover-lift cursor-pointer">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="rounded-lg bg-[#00D4AA]/20 p-3">
                    <Sparkles className="h-6 w-6 text-[#00D4AA]" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">
                      Complete Your Profile
                    </h3>
                    <p className="mt-1 text-sm text-gray-400">
                      Tell us about yourself so we can personalize your learning
                      experience.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="h-2 w-32 overflow-hidden rounded-full bg-gray-800">
                        <div
                          className="h-full bg-[#00D4AA] transition-all"
                          style={{
                            width: `${progress?.percent_complete ?? 0}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">
                        {progress?.percent_complete ?? 0}% complete
                      </span>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-[#00D4AA] transition-transform group-hover:translate-x-1" />
              </div>
            </div>
          </Link>
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <h2 className="mb-4 text-lg font-semibold text-white">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action, index) => (
            <motion.div
              key={action.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.05 }}
            >
              <Link href={action.href}>
                <div className="group h-full rounded-xl border border-gray-800 bg-[#111827] p-5 card-hover-lift cursor-pointer">
                  <div
                    className={`mb-4 inline-flex rounded-lg border p-2.5 ${action.color}`}
                  >
                    <action.icon className={`h-5 w-5 ${action.iconColor}`} />
                  </div>
                  <h3 className="font-semibold text-white group-hover:text-[#00D4AA] transition-colors">
                    {action.title}
                  </h3>
                  <p className="mt-1 text-sm text-gray-400">
                    {action.description}
                  </p>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recent Activity & Tips */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid gap-6 lg:grid-cols-2"
      >
        {/* Getting Started */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
          <h3 className="mb-4 font-semibold text-white">Getting Started</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3 rounded-lg bg-[#1A2942]/50 p-3">
              <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#00D4AA]/20">
                <span className="text-xs font-bold text-[#00D4AA]">1</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-200">
                  Complete your profile
                </p>
                <p className="text-xs text-gray-500">
                  Help us understand your goals
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg bg-[#1A2942]/50 p-3">
              <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#00D4AA]/20">
                <span className="text-xs font-bold text-[#00D4AA]">2</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-200">
                  Ask your first question
                </p>
                <p className="text-xs text-gray-500">
                  Chat with your AI tutor
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg bg-[#1A2942]/50 p-3">
              <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#00D4AA]/20">
                <span className="text-xs font-bold text-[#00D4AA]">3</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-200">
                  Generate a strategy
                </p>
                <p className="text-xs text-gray-500">
                  Get a personalized investment plan
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Learning Tip */}
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
          <div className="mb-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-[#00D4AA]" />
            <h3 className="font-semibold text-white">Today's Tip</h3>
          </div>
          <div className="rounded-lg bg-[#1A2942]/50 p-4">
            <p className="text-sm text-gray-300">
              <span className="font-semibold text-[#00D4AA]">
                Diversification
              </span>{" "}
              is one of the most important concepts in investing. It means
              spreading your investments across different asset classes,
              industries, and geographies to reduce risk.
            </p>
            <p className="mt-3 text-xs text-gray-500">
              "Don't put all your eggs in one basket."
            </p>
          </div>
          <Button
            variant="outline"
            className="mt-4 w-full border-gray-700 text-gray-300 hover:bg-[#1A2942] hover:text-white"
            asChild
          >
            <Link href="/chat">
              Ask AI to explain more
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
