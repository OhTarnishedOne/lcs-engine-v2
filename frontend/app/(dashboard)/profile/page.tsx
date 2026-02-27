"use client";

import { useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  User,
  Sparkles,
  Shield,
  Target,
  BookOpen,
  TrendingUp,
  ChevronRight,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const INTEREST_LABELS: Record<string, string> = {
  stocks: "Individual Stocks",
  etfs: "ETFs & Index Funds",
  bonds: "Bonds & Fixed Income",
  crypto: "Cryptocurrency",
  real_estate: "Real Estate",
  retirement: "Retirement Planning",
  all: "All Topics",
};

const BARRIER_LABELS: Record<string, string> = {
  dont_know_where_to_start: "Don't know where to start",
  fear_of_losing_money: "Afraid of losing money",
  not_enough_money: "Don't have enough to invest",
  too_complicated: "Seems too complicated",
  dont_trust_markets: "Don't trust the market",
  no_time: "Don't have time",
  bad_experience: "Had a bad experience",
  none: "No barriers",
};

function TagList({
  items,
  labelMap,
}: {
  items: string[] | null | undefined;
  labelMap: Record<string, string>;
}) {
  if (!items || items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className="rounded-full bg-[#1A2942] px-3 py-1 text-sm text-gray-200"
        >
          {labelMap[item] || item}
        </span>
      ))}
    </div>
  );
}

export default function ProfilePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const isWelcome = searchParams.get("welcome") === "true";
  const { user } = useAuthStore();

  const {
    data: profile,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["profile"],
    queryFn: () => api.getProfile(),
  });

  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ["onboarding-progress"],
    queryFn: () => api.getOnboardingProgress(),
  });

  const isOnboardingComplete = progress?.is_complete ?? false;

  // Redirect to onboarding if not completed
  useEffect(() => {
    if (!progressLoading && !isOnboardingComplete) {
      router.replace("/onboarding");
    }
  }, [progressLoading, isOnboardingComplete, router]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <div className="h-8 w-48 rounded skeleton-shimmer" />
          <div className="mt-2 h-5 w-72 rounded skeleton-shimmer" />
        </div>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-800 bg-[#111827] p-6 space-y-4"
          >
            <div className="h-6 w-40 rounded skeleton-shimmer" />
            <div className="h-4 w-full rounded skeleton-shimmer" />
            <div className="h-4 w-3/4 rounded skeleton-shimmer" />
          </div>
        ))}
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="mx-auto max-w-3xl">
        <Card className="border-gray-800 bg-[#111827] p-6">
          <CardContent className="p-0 text-center">
            <p className="text-gray-400">
              {error
                ? "Something went wrong loading your profile. Please try again."
                : "Complete onboarding to see your profile."}
            </p>
            <Button
              onClick={() => error ? window.location.reload() : router.push("/onboarding")}
              className="mt-4 bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
            >
              {error ? "Retry" : "Start Onboarding"}
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { raw, derived } = profile;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Welcome banner (only on ?welcome=true) */}
      {isWelcome && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-6 text-center"
        >
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#00D4AA]/20">
            <Sparkles className="h-6 w-6 text-[#00D4AA]" />
          </div>
          <h2 className="text-xl font-bold text-white">
            Here&apos;s Your Investing Profile
          </h2>
          <p className="mt-1 text-gray-400">
            Your AI tutor will use this to personalize your experience.
          </p>
          <Button
            onClick={() => router.push("/dashboard")}
            className="mt-4 bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
          >
            Looks good — let&apos;s get started
            <ChevronRight className="ml-1 h-4 w-4" />
          </Button>
        </motion.div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          {isWelcome ? "Here's Your Investing Profile" : "Your Investing Profile"}
        </h1>
        <p className="text-gray-400">
          {user?.email} &middot; Member since{" "}
          {user?.created_at
            ? new Date(user.created_at).toLocaleDateString()
            : "—"}
        </p>
      </div>

      {/* Persona Card */}
      {derived.persona && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-[#00D4AA]/20 bg-[#111827] p-6">
            <CardContent className="p-0">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#00D4AA]/20">
                  <User className="h-6 w-6 text-[#00D4AA]" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-[#00D4AA]">
                    {derived.persona_label || derived.persona}
                  </h3>
                  {derived.persona_description && (
                    <p className="mt-1 text-gray-300">
                      {derived.persona_description}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Investing Experience */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        <Card className="border-gray-800 bg-[#111827] p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="flex items-center gap-2 text-white">
              <TrendingUp className="h-5 w-5 text-[#00D4AA]" />
              Investing Experience
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-0">
            {derived.experience_summary && (
              <p className="text-gray-300">{derived.experience_summary}</p>
            )}
            <div className="flex gap-8">
              <div>
                <p className="text-sm text-gray-400">Brokerage Account</p>
                <p className="mt-0.5 text-white">
                  {raw.has_investment_account === true
                    ? "Yes"
                    : raw.has_investment_account === false
                    ? "No"
                    : "—"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Retirement Account</p>
                <p className="mt-0.5 text-white">
                  {raw.has_retirement_account === true
                    ? "Yes"
                    : raw.has_retirement_account === false
                    ? "No"
                    : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* What's Holding You Back */}
      {raw.barriers && raw.barriers.length > 0 && raw.barriers[0] !== "none" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-gray-800 bg-[#111827] p-6">
            <CardHeader className="p-0 pb-4">
              <CardTitle className="flex items-center gap-2 text-white">
                <Shield className="h-5 w-5 text-[#00D4AA]" />
                What&apos;s Holding You Back
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-0">
              <TagList items={raw.barriers} labelMap={BARRIER_LABELS} />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Goals */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        <Card className="border-gray-800 bg-[#111827] p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="flex items-center gap-2 text-white">
              <Target className="h-5 w-5 text-[#00D4AA]" />
              Goals
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-0">
            {derived.goals_summary && (
              <p className="text-gray-300">{derived.goals_summary}</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Risk Tolerance */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="border-gray-800 bg-[#111827] p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="flex items-center gap-2 text-white">
              <Shield className="h-5 w-5 text-[#00D4AA]" />
              Risk Tolerance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-0">
            {derived.risk_summary && (
              <p className="text-gray-300">{derived.risk_summary}</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Interests */}
      {raw.interests && raw.interests.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
        >
          <Card className="border-gray-800 bg-[#111827] p-6">
            <CardHeader className="p-0 pb-4">
              <CardTitle className="flex items-center gap-2 text-white">
                <Target className="h-5 w-5 text-[#00D4AA]" />
                Interests
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-0">
              {derived.interests_summary && (
                <p className="mb-3 text-gray-300">{derived.interests_summary}</p>
              )}
              <TagList items={raw.interests} labelMap={INTEREST_LABELS} />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Learning Style */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="border-gray-800 bg-[#111827] p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="flex items-center gap-2 text-white">
              <BookOpen className="h-5 w-5 text-[#00D4AA]" />
              Learning Style
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-0">
            {derived.learning_summary && (
              <p className="text-gray-300">{derived.learning_summary}</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Edit CTA */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="rounded-xl border border-gray-800 bg-[#111827] p-6 text-center"
      >
        <p className="text-sm text-gray-400">
          Want to update your preferences? You can retake onboarding anytime.
        </p>
        <Button
          onClick={() => (window.location.href = "/onboarding")}
          variant="outline"
          className="mt-3 border-gray-700 text-gray-300 hover:bg-[#1A2942] hover:text-white"
        >
          Retake Onboarding
        </Button>
      </motion.div>
    </div>
  );
}
