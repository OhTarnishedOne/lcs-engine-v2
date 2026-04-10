"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2,
  Users,
  TrendingUp,
  BookOpen,
  Shield,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  ChevronDown,
  GraduationCap,
  Briefcase,
  HeartHandshake,
  Star,
} from "lucide-react";

const segments = [
  {
    id: "credit-unions",
    icon: Building2,
    label: "Credit Unions",
    headline: "Turn members into confident investors",
    body: "Your members trust you with their money. LCS Engine gives them the financial education to grow it. Embed our AI-powered platform under your brand and deepen member relationships while reducing financial anxiety — the #1 churn driver.",
    stats: [
      { value: "83%", label: "Onboarding completion rate" },
      { value: "5", label: "Investor archetypes matched" },
      { value: "AI", label: "Personalized to each member" },
    ],
  },
  {
    id: "hbcus",
    icon: GraduationCap,
    label: "HBCUs",
    headline: "Close the wealth gap, one student at a time",
    body: "First-generation investors need more than a textbook. LCS Engine meets students where they are — matching their risk profile, speaking their language, and building the investing fluency that compounds over a lifetime.",
    stats: [
      { value: "100%", label: "Survey respondents saw value" },
      { value: "5", label: "Literacy levels, personalized" },
      { value: "Live", label: "Paper trading simulator" },
    ],
  },
  {
    id: "workforce",
    icon: HeartHandshake,
    label: "Workforce Development",
    headline: "Financial wellness as a workforce benefit",
    body: "Workers who understand money make better decisions, stay longer, and perform better. LCS Engine integrates into your financial wellness programs as a white-labeled AI tutor that scales to any cohort size.",
    stats: [
      { value: "B2B2C", label: "White-label ready" },
      { value: "API", label: "Integrates with your stack" },
      { value: "Track", label: "Progress dashboards included" },
    ],
  },
  {
    id: "employers",
    icon: Briefcase,
    label: "Employer Benefits",
    headline: "Differentiate your benefits package",
    body: "Financial stress costs employers $250B/year in lost productivity. Offer LCS Engine as a financial literacy benefit and give employees an AI coach that adapts to their investor profile — not generic budgeting tips.",
    stats: [
      { value: "$250B", label: "Annual employer cost of financial stress" },
      { value: "AI", label: "Tutor adapts to each employee" },
      { value: "ROI", label: "Measurable literacy outcomes" },
    ],
  },
];

const features = [
  { icon: BookOpen, title: "Personalized AI Tutor", description: "Claude-powered AI that adapts explanations to each learner's archetype — from Conservative Saver to Aggressive Investor." },
  { icon: BarChart3, title: "Probability Lab", description: "Real-world market scenarios using live Kalshi and Metaculus data. Builds probabilistic thinking, not just vocabulary." },
  { icon: TrendingUp, title: "Paper Trading Simulator", description: "Risk-free investing practice via Alpaca and Polygon. Members build muscle memory before real money is on the line." },
  { icon: Users, title: "Investor Archetype Engine", description: "Proprietary onboarding that maps each user to one of five investor profiles, then personalizes every module accordingly." },
  { icon: Shield, title: "White-Label Ready", description: "Deploy under your brand. Custom domain, your logo, your colors. Your members never leave your ecosystem." },
  { icon: BarChart3, title: "Progress Analytics", description: "Admin dashboards track cohort engagement, module completion, and literacy milestones — reportable to leadership." },
];

const faqs = [
  { q: "How is LCS Engine different from generic financial literacy tools?", a: "Most tools deliver static content. LCS Engine uses a proprietary archetype engine to profile each learner first, then adapts every lesson, example, and AI response to their specific investor psychology. It's the difference between a pamphlet and a coach." },
  { q: "How does the white-label licensing work?", a: "We license the platform under a B2B2C model. You get a branded instance on your domain, admin access to your cohort's analytics, and a dedicated onboarding. Pricing is per-seat annually with volume tiers." },
  { q: "What does integration look like technically?", a: "LCS Engine is a fully hosted web application. No engineering required on your end. For deeper integrations (SSO, LMS embedding, API access), we scope that in the pilot agreement." },
  { q: "Is there a minimum cohort size for a pilot?", a: "No minimum. We design pilots to fit your context — from 25-student HBCU cohorts to 5,000-member credit union rollouts. We'd rather start right than start big." },
];

function SegmentTab({ segment, active, onClick }: { segment: typeof segments[0]; active: boolean; onClick: () => void }) {
  const Icon = segment.icon;
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 border ${active ? "bg-[#00D4AA] text-[#0A1628] border-[#00D4AA]" : "bg-transparent text-[#9CA3AF] border-[#374151] hover:border-[#00D4AA] hover:text-[#F9FAFB]"}`}>
      <Icon size={15} />
      {segment.label}
    </button>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-[#374151]">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between py-5 text-left gap-4">
        <span className="text-[#F9FAFB] font-medium text-sm">{q}</span>
        <ChevronDown size={16} className={`text-[#9CA3AF] shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <p className="text-[#9CA3AF] text-sm leading-relaxed pb-5">{a}</p>}
    </div>
  );
}

export default function OrganizationsPage() {
  const [activeSegment, setActiveSegment] = useState(0);
  const segment = segments[activeSegment];
  const SegmentIcon = segment.icon;

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--lcs-primary)", color: "var(--lcs-text-primary)" }}>
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-[#374151] backdrop-blur-sm bg-[#0A1628]/90">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#00D4AA]">
              <BarChart3 className="h-4 w-4 text-[#0A1628]" />
            </div>
            <span className="text-lg font-bold text-white">LCS Engine</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="hidden sm:inline text-sm text-[#9CA3AF] hover:text-white"
            >
              For Individuals
            </Link>
            <a
              href="mailto:rico@lcsengine.com?subject=LCS%20Engine%20for%20Organizations"
              className="inline-flex items-center gap-2 rounded-lg bg-[#00D4AA] px-4 py-2 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
            >
              Contact Sales
              <ArrowRight size={14} />
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#374151] bg-[#1A2942] px-3 py-1 text-xs font-medium text-[#00D4AA]">
          <Star size={12} />
          For Organizations
        </div>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
          Financial literacy,{" "}
          <span className="text-[#00D4AA]">personalized at scale.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-[#9CA3AF]">
          LCS Engine is a white-label AI investing platform for credit unions,
          HBCUs, workforce development programs, and employer benefits teams.
          Deploy a branded instance, onboard your cohort, and track outcomes.
        </p>
      </section>

      {/* Segments */}
      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="mb-8 flex flex-wrap gap-2">
          {segments.map((s, i) => (
            <SegmentTab
              key={s.id}
              segment={s}
              active={activeSegment === i}
              onClick={() => setActiveSegment(i)}
            />
          ))}
        </div>

        <div className="grid gap-10 rounded-2xl border border-[#374151] bg-[#111827] p-8 lg:grid-cols-2 lg:p-12">
          <div>
            <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[#1A2942]">
              <SegmentIcon className="h-6 w-6 text-[#00D4AA]" />
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white">
              {segment.headline}
            </h2>
            <p className="mb-8 text-[#9CA3AF] leading-relaxed">{segment.body}</p>
            <a
              href={`mailto:rico@lcsengine.com?subject=LCS%20Engine%20Pilot%20-%20${encodeURIComponent(segment.label)}`}
              className="inline-flex items-center gap-2 rounded-lg bg-[#00D4AA] px-5 py-2.5 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
            >
              Request a pilot
              <ArrowRight size={14} />
            </a>
          </div>
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            {segment.stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-[#374151] bg-[#0A1628] p-5"
              >
                <div className="font-mono-nums text-3xl font-bold text-[#00D4AA]">
                  {stat.value}
                </div>
                <div className="mt-1 text-xs text-[#9CA3AF]">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="mb-12 max-w-2xl">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Built for organizations that care about outcomes
          </h2>
          <p className="mt-4 text-[#9CA3AF]">
            Every feature is designed for measurable impact — not vanity
            metrics.
          </p>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="rounded-xl border border-[#374151] bg-[#111827] p-6 transition-colors hover:border-[#00D4AA]/40"
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[#1A2942]">
                  <Icon className="h-5 w-5 text-[#00D4AA]" />
                </div>
                <h3 className="mb-2 text-base font-semibold text-white">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-[#9CA3AF]">
                  {f.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* How pilots work */}
      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="rounded-2xl border border-[#374151] bg-[#111827] p-8 lg:p-12">
          <h2 className="mb-10 text-3xl font-bold text-white">
            How a pilot works
          </h2>
          <div className="grid gap-8 sm:grid-cols-3">
            {[
              {
                n: "1",
                title: "Discovery call",
                body: "30-minute intro to understand your cohort, goals, and success metrics.",
              },
              {
                n: "2",
                title: "Branded deployment",
                body: "We spin up a white-labeled instance on your subdomain. No engineering needed.",
              },
              {
                n: "3",
                title: "Launch & measure",
                body: "Onboard your cohort. Weekly reports on engagement, completion, and literacy gains.",
              },
            ].map((step) => (
              <div key={step.n}>
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#00D4AA] font-mono-nums text-base font-bold text-[#0A1628]">
                  {step.n}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">
                  {step.title}
                </h3>
                <p className="text-sm leading-relaxed text-[#9CA3AF]">
                  {step.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-3xl px-6 pb-20">
        <h2 className="mb-8 text-3xl font-bold text-white">
          Frequently asked questions
        </h2>
        <div>
          {faqs.map((f) => (
            <FAQItem key={f.q} q={f.q} a={f.a} />
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="overflow-hidden rounded-2xl border border-[#00D4AA]/30 bg-gradient-to-br from-[#111827] to-[#1A2942] p-10 text-center lg:p-16">
          <div className="mb-4 inline-flex items-center gap-2 text-xs font-medium text-[#00D4AA]">
            <CheckCircle2 size={14} />
            Accepting pilot partners now
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Let's build something real.
          </h2>
          <p className="mx-auto mb-8 max-w-2xl text-[#9CA3AF]">
            Every pilot starts with a conversation. Tell us about your cohort,
            your goals, and what success looks like — we'll take it from there.
          </p>
          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a
              href="mailto:rico@lcsengine.com?subject=LCS%20Engine%20Pilot%20Inquiry"
              className="inline-flex items-center gap-2 rounded-lg bg-[#00D4AA] px-6 py-3 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
            >
              Email rico@lcsengine.com
              <ArrowRight size={14} />
            </a>
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-lg border border-[#374151] bg-transparent px-6 py-3 text-sm font-semibold text-[#F9FAFB] transition-colors hover:border-[#00D4AA]"
            >
              See the product
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#374151]">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
              <BarChart3 className="h-4 w-4 text-[#0A1628]" />
            </div>
            <span className="text-sm font-semibold text-white">LCS Engine</span>
          </div>
          <div className="text-xs text-[#6B7280]">
            © {new Date().getFullYear()} LCS Engine. Built in NYC.
          </div>
        </div>
      </footer>
    </div>
  );
}
