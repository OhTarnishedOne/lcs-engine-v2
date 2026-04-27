"use client";

import { User, Shield, Target, BookOpen, Heart, TrendingUp } from "lucide-react";
import { riskProfile } from "@/lib/mock-data";

export default function RiskProfilePage() {
  const p = riskProfile;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Your Investor Profile</h1>
        <p className="mt-1 text-gray-400">Personalized based on your risk assessment</p>
      </div>

      {/* Archetype Card */}
      <div className="rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#00D4AA]/20">
            <User className="h-6 w-6 text-[#00D4AA]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[#00D4AA]">{p.archetype}</h3>
            <p className="mt-1 text-gray-300">{p.archetypeDescription}</p>
          </div>
        </div>
      </div>

      {/* Risk & Experience */}
      <div className="grid gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
          <div className="mb-3 flex items-center gap-2">
            <Shield className="h-5 w-5 text-[#00D4AA]" />
            <h3 className="font-semibold text-white">Risk Tolerance</h3>
          </div>
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-400">Level</span>
              <span className="text-sm font-medium text-[#F59E0B]">{p.riskTolerance}</span>
            </div>
            <div className="h-2 rounded-full bg-gray-800">
              <div className="h-2 rounded-full bg-[#F59E0B]" style={{ width: "50%" }} />
            </div>
          </div>
          <p className="text-sm text-gray-400">Time Horizon: {p.timeHorizon}</p>
        </div>

        <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-[#00D4AA]" />
            <h3 className="font-semibold text-white">Experience</h3>
          </div>
          <p className="text-sm text-gray-300">{p.experienceLevel}</p>
          <p className="mt-2 text-sm text-gray-400">{p.primaryGoal}</p>
        </div>
      </div>

      {/* Goals */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-3 flex items-center gap-2">
          <Target className="h-5 w-5 text-[#00D4AA]" />
          <h3 className="font-semibold text-white">Primary Goal</h3>
        </div>
        <p className="text-gray-300">{p.primaryGoal}</p>
      </div>

      {/* Interests */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-3 flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-[#00D4AA]" />
          <h3 className="font-semibold text-white">Investment Interests</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {p.interests.map((interest) => (
            <span key={interest} className="rounded-full bg-[#1A2942] px-3 py-1 text-sm text-gray-200">
              {interest}
            </span>
          ))}
        </div>
      </div>

      {/* Barriers */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-3 flex items-center gap-2">
          <Heart className="h-5 w-5 text-[#00D4AA]" />
          <h3 className="font-semibold text-white">What We&apos;re Working On</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {p.barriers.map((barrier) => (
            <span key={barrier} className="rounded-full bg-[#F59E0B]/10 border border-[#F59E0B]/30 px-3 py-1 text-sm text-[#F59E0B]">
              {barrier}
            </span>
          ))}
        </div>
      </div>

      {/* Learning Style */}
      <div className="rounded-xl border border-gray-800 bg-[#111827] p-6">
        <div className="mb-3 flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-[#00D4AA]" />
          <h3 className="font-semibold text-white">Learning Style</h3>
        </div>
        <p className="text-gray-300">{p.learningStyle}</p>
      </div>
    </div>
  );
}
