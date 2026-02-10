"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import {
  Brain,
  TrendingUp,
  Target,
  ArrowRight,
  Sparkles,
  Shield,
  BarChart3,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Learn with AI",
    description:
      "A personalized AI tutor that adapts to your knowledge level and learning style.",
  },
  {
    icon: TrendingUp,
    title: "Practice Trading",
    description:
      "Paper trade with real market data. No risk, real learning experience.",
  },
  {
    icon: Target,
    title: "Predict Markets",
    description:
      "Calibrate your judgment by predicting economic events and tracking accuracy.",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    // If authenticated and this is not a deliberate visit, redirect to dashboard
    if (!isLoading && isAuthenticated && typeof window !== "undefined") {
      const intentionalLanding = sessionStorage.getItem("intentional_landing");
      if (!intentionalLanding) {
        router.push("/dashboard");
      }
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A1628]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#00D4AA] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A1628]">
      {/* Hero Section */}
      <section className="gradient-mesh relative overflow-hidden">
        {/* Navigation */}
        <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#00D4AA]">
              <BarChart3 className="h-5 w-5 text-[#0A1628]" />
            </div>
            <span className="text-xl font-bold text-white">LCS Engine</span>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <Link href="/dashboard">
                <Button className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]">
                  Go to Dashboard
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" className="text-gray-300 hover:text-white hover:bg-white/10">
                    Log in
                  </Button>
                </Link>
                <Link href="/register">
                  <Button className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] btn-accent-glow">
                    Get Started Free
                  </Button>
                </Link>
              </>
            )}
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 mx-auto max-w-4xl px-6 py-24 text-center sm:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#00D4AA]/30 bg-[#00D4AA]/10 px-4 py-2">
              <Sparkles className="h-4 w-4 text-[#00D4AA]" />
              <span className="text-sm text-[#00D4AA]">AI-Powered Learning</span>
            </div>

            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
              Learn to invest.
              <br />
              <span className="text-[#00D4AA]">Without the fear.</span>
            </h1>

            <p className="mx-auto mb-10 max-w-2xl text-lg text-gray-400 sm:text-xl">
              AI-powered financial education that meets you where you are.
              Practice trading, predict markets, and build confidence—all in one place.
            </p>

            <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link href="/register">
                <Button
                  size="lg"
                  className="h-14 px-8 text-lg bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] btn-accent-glow"
                >
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="h-14 px-8 text-lg border-gray-700 text-gray-300 hover:bg-white/5 hover:text-white"
                >
                  I have an account
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Gradient fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0A1628] to-transparent" />
      </section>

      {/* Features Section */}
      <section className="relative py-24">
        <div className="mx-auto max-w-7xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="mb-16 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
              Everything you need to become a confident investor
            </h2>
            <p className="text-lg text-gray-400">
              Three powerful tools, one platform.
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="group rounded-2xl border border-gray-800 bg-[#111827] p-8 card-hover-lift"
              >
                <div className="mb-5 inline-flex rounded-xl bg-[#1A2942] p-3">
                  <feature.icon className="h-6 w-6 text-[#00D4AA]" />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="border-t border-gray-800 py-16">
        <div className="mx-auto max-w-7xl px-6">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="flex flex-col items-center justify-center gap-8 sm:flex-row sm:gap-16"
          >
            <div className="text-center">
              <div className="text-3xl font-bold text-white font-mono">102+</div>
              <div className="text-sm text-gray-400">Active learners</div>
            </div>
            <div className="hidden h-12 w-px bg-gray-800 sm:block" />
            <div className="text-center">
              <div className="text-3xl font-bold text-[#00D4AA] font-mono">69%</div>
              <div className="text-sm text-gray-400">Rated "very valuable"</div>
            </div>
            <div className="hidden h-12 w-px bg-gray-800 sm:block" />
            <div className="flex items-center gap-2 text-center">
              <Shield className="h-5 w-5 text-[#00D4AA]" />
              <span className="text-sm text-gray-400">Paper trading only—no real money at risk</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <h2 className="mb-6 text-3xl font-bold text-white sm:text-4xl">
              Start your investing journey today
            </h2>
            <p className="mb-8 text-lg text-gray-400">
              No credit card required. No hidden fees. Just learning.
            </p>
            <Link href="/register">
              <Button
                size="lg"
                className="h-14 px-10 text-lg bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] btn-accent-glow"
              >
                Create Free Account
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#00D4AA]">
                <BarChart3 className="h-4 w-4 text-[#0A1628]" />
              </div>
              <span className="font-semibold text-white">LCS Engine</span>
            </div>
            <p className="text-sm text-gray-500">
              Built for learning. Not financial advice.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
