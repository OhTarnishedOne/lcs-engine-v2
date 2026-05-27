"use client";

/**
 * Pricing page — /pricing
 * Shows Free vs Pro tiers with a direct upgrade CTA.
 */

import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUpgrade } from "@/hooks/useUpgrade";
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { DISCLAIMER_FOOTER } from "@/components/Disclaimer";
import { useAuthStore } from "@/stores/auth-store";
import { useRouter } from "next/navigation";

const FREE_FEATURES = [
  "Investor archetype + profile",
  "3 AI tutor sessions",
  "3 Probability Lab predictions",
];

const PRO_FEATURES = [
  "Everything in Free",
  "Unlimited AI tutor sessions",
  "Unlimited Probability Lab predictions",
  "Paper trading \u2014 $100K virtual account",
  "AI-generated investment strategies",
  "Cognitive bias tracking",
];

function PricingCard({
  tier,
  price,
  features,
  isCurrent,
  isHighlighted,
  cta,
  onCta,
  ctaDisabled,
}: {
  tier: string;
  price: string;
  features: string[];
  isCurrent?: boolean;
  isHighlighted?: boolean;
  cta: string;
  onCta: () => void;
  ctaDisabled?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-8 ${
        isHighlighted
          ? "border-[#00D4AA]/40 bg-[#111827]"
          : "border-gray-800 bg-[#0D1B2E]"
      }`}
    >
      {isHighlighted && (
        <div className="mb-4 inline-block rounded-full bg-[#00D4AA]/20 px-3 py-1 text-xs font-semibold text-[#00D4AA]">
          Most popular
        </div>
      )}
      <h2 className="text-xl font-bold text-white">{tier}</h2>
      <p className="mt-2 text-3xl font-bold text-white">
        {price}
        {price !== "Free" && (
          <span className="text-base font-normal text-gray-400">/month</span>
        )}
      </p>
      {isCurrent && (
        <p className="mt-1 text-sm text-[#00D4AA]">Your current plan</p>
      )}
      <ul className="mt-6 space-y-3">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#00D4AA]" />
            {f}
          </li>
        ))}
      </ul>
      <Button
        onClick={onCta}
        disabled={ctaDisabled}
        className={`mt-8 w-full ${
          isHighlighted
            ? "bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-60"
            : "border border-gray-700 bg-transparent text-gray-300 hover:bg-[#1A2942]"
        }`}
      >
        {cta}
      </Button>
    </div>
  );
}

export default function PricingPage() {
  const { upgrade, isLoading } = useUpgrade();
  const { isPro } = useBillingStatus();
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  const handleFreeAction = () => {
    if (!isAuthenticated) router.push("/register");
    else router.push("/dashboard");
  };

  const handleProAction = () => {
    if (!isAuthenticated) router.push("/register?next=upgrade");
    else upgrade();
  };

  return (
    <div className="min-h-screen bg-[#0A1628] px-6 py-20">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-white">
            Learn how to invest. For real.
          </h1>
          <p className="mt-4 text-lg text-gray-400">
            Start free. Upgrade when you're ready for the full experience.
          </p>
        </div>

        {/* Cards */}
        <div className="grid gap-6 md:grid-cols-2">
          <PricingCard
            tier="Free"
            price="Free"
            features={FREE_FEATURES}
            isCurrent={isAuthenticated && !isPro}
            isHighlighted={false}
            cta={isAuthenticated ? "Go to dashboard" : "Get started free"}
            onCta={handleFreeAction}
          />
          <PricingCard
            tier="Pro"
            price="$20"
            features={PRO_FEATURES}
            isCurrent={isPro}
            isHighlighted={true}
            cta={
              isPro
                ? "You're on Pro"
                : isLoading
                ? "Redirecting\u2026"
                : "Upgrade to Pro"
            }
            onCta={handleProAction}
            ctaDisabled={isPro || isLoading}
          />
        </div>

        {/* Institution note */}
        <p className="mt-10 text-center text-sm text-gray-500">
          Running a credit union, HBCU, or workforce program?{" "}
          <a
            href="mailto:rico@lcsengine.com"
            className="text-[#00D4AA] hover:underline"
          >
            Contact us about Institution pricing.
          </a>
        </p>
        <p className="mt-6 text-center text-xs text-gray-600 max-w-2xl mx-auto">
          {DISCLAIMER_FOOTER}
        </p>
      </div>
    </div>
  );
}
