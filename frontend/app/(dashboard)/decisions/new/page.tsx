"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Target, Lock, ArrowLeft, ArrowRight, Check } from "lucide-react";

import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { CreateDecisionRequest, DecisionRecord } from "@/lib/api/types";

const DOMAINS: { value: string; label: string }[] = [
  { value: "investing", label: "Investing" },
  { value: "career", label: "Career" },
  { value: "personal_finance", label: "Personal Finance" },
  { value: "business", label: "Business" },
  { value: "life", label: "Life" },
];

const fieldClass =
  "w-full rounded-md border border-gray-700 bg-[#0A1628] px-3 py-2 text-sm text-white placeholder:text-gray-500 outline-none transition-colors focus:border-[#00D4AA]";

export default function DecisionComposerPage() {
  const queryClient = useQueryClient();

  const [question, setQuestion] = useState("");
  const [domain, setDomain] = useState("investing");
  const [confidencePct, setConfidencePct] = useState(60);
  const [reasoning, setReasoning] = useState("");
  const [falsification, setFalsification] = useState("");
  const [resolutionDate, setResolutionDate] = useState("");
  const [committed, setCommitted] = useState<DecisionRecord | null>(null);

  const mutation = useMutation({
    mutationFn: (body: CreateDecisionRequest) => api.createDecision(body),
    onSuccess: (decision) => {
      queryClient.invalidateQueries({ queryKey: ["decision-diagnosis"] });
      queryClient.invalidateQueries({ queryKey: ["active-intervention"] });
      queryClient.invalidateQueries({ queryKey: ["decision-calibration"] });
      setCommitted(decision);
      toast.success("Decision committed and locked.");
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to log decision.");
    },
  });

  const canSubmit = question.trim().length > 0 && !mutation.isPending;

  const handleSubmit = () => {
    if (!canSubmit) return;
    mutation.mutate({
      question: question.trim(),
      confidence: confidencePct / 100,
      domain,
      reasoning: reasoning.trim() || null,
      falsification: falsification.trim() || null,
      resolution_date: resolutionDate ? new Date(resolutionDate).toISOString() : null,
    });
  };

  const resetForm = () => {
    setQuestion("");
    setDomain("investing");
    setConfidencePct(60);
    setReasoning("");
    setFalsification("");
    setResolutionDate("");
    setCommitted(null);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <Link
        href="/dashboard"
        className="mb-6 inline-flex items-center gap-2 text-sm text-gray-400 transition-colors hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to dashboard
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-2">
          <Target className="h-6 w-6 text-[#00D4AA]" />
          <h1 className="text-2xl font-bold text-white">Log a decision</h1>
        </div>
        <p className="mt-2 text-sm text-gray-400">
          Commit your confidence and reasoning before the outcome is known. This
          is where calibration is trained.
        </p>
      </motion.div>

      {committed ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-[#00D4AA]/30 bg-[#00D4AA]/5 p-6"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#00D4AA]/20">
              <Check className="h-5 w-5 text-[#00D4AA]" />
            </div>
            <div>
              <p className="font-semibold text-white">Committed &amp; locked</p>
              <p className="text-xs text-gray-400">
                Confidence, reasoning, and falsification are now immutable.
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-[#1A2942]/50 p-4">
            <p className="text-sm font-medium text-white">{committed.question}</p>
            <p className="mt-2 text-xs text-gray-400">
              Confidence{" "}
              <span className="font-mono-nums text-[#00D4AA]">
                {Math.round(committed.confidence * 100)}%
              </span>{" "}
              · {committed.status} · locked
            </p>
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <Button
              onClick={resetForm}
              className="flex-1 bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
            >
              Log another decision
            </Button>
            <Button
              asChild
              variant="outline"
              className="flex-1 border-gray-700 text-gray-300 hover:bg-[#1A2942] hover:text-white"
            >
              <Link href="/decisions">
                View your decisions
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-xl border border-gray-800 bg-[#111827] p-6"
        >
          <div className="space-y-5">
            {/* Question */}
            <div className="space-y-2">
              <Label htmlFor="question" className="text-gray-300">
                What are you deciding? <span className="text-[#00D4AA]">*</span>
              </Label>
              <Input
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. Will this pilot convert to a paid contract by Q4?"
                className="border-gray-700 bg-[#0A1628] text-white placeholder:text-gray-500 focus-visible:border-[#00D4AA]"
              />
            </div>

            {/* Domain */}
            <div className="space-y-2">
              <Label htmlFor="domain" className="text-gray-300">
                Domain
              </Label>
              <select
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className={fieldClass}
              >
                {DOMAINS.map((d) => (
                  <option key={d.value} value={d.value} className="bg-[#0A1628]">
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Confidence */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="confidence" className="text-gray-300">
                  How confident are you it happens?
                </Label>
                <span className="font-mono-nums text-lg font-bold text-[#00D4AA]">
                  {confidencePct}%
                </span>
              </div>
              <input
                id="confidence"
                type="range"
                min={1}
                max={99}
                step={1}
                value={confidencePct}
                onChange={(e) => setConfidencePct(Number(e.target.value))}
                className="w-full accent-[#00D4AA]"
              />
              <p className="text-xs text-gray-500">
                50% means no opinion. Commit past it when you have evidence.
              </p>
            </div>

            {/* Reasoning */}
            <div className="space-y-2">
              <Label htmlFor="reasoning" className="text-gray-300">
                Why? <span className="text-gray-500">(reasoning)</span>
              </Label>
              <textarea
                id="reasoning"
                value={reasoning}
                onChange={(e) => setReasoning(e.target.value)}
                rows={3}
                placeholder="What's your thesis?"
                className={fieldClass}
              />
            </div>

            {/* Falsification */}
            <div className="space-y-2">
              <Label htmlFor="falsification" className="text-gray-300">
                What would change your mind?{" "}
                <span className="text-gray-500">(falsification)</span>
              </Label>
              <textarea
                id="falsification"
                value={falsification}
                onChange={(e) => setFalsification(e.target.value)}
                rows={2}
                placeholder="Name one condition that would prove you wrong."
                className={fieldClass}
              />
            </div>

            {/* Resolution date */}
            <div className="space-y-2">
              <Label htmlFor="resolution-date" className="text-gray-300">
                When should you know?{" "}
                <span className="text-gray-500">(optional)</span>
              </Label>
              <Input
                id="resolution-date"
                type="date"
                value={resolutionDate}
                onChange={(e) => setResolutionDate(e.target.value)}
                className="border-gray-700 bg-[#0A1628] text-white focus-visible:border-[#00D4AA]"
              />
            </div>

            {/* Lock notice + submit */}
            <div className="flex items-start gap-2 rounded-lg bg-[#1A2942]/50 p-3">
              <Lock className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
              <p className="text-xs text-gray-400">
                Once you commit, your confidence, reasoning, and falsification
                lock — you can&apos;t edit them after the fact. That&apos;s what
                keeps your Calibration Score honest.
              </p>
            </div>

            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-50"
            >
              {mutation.isPending ? "Committing…" : "Commit decision"}
              {!mutation.isPending && <Lock className="ml-2 h-4 w-4" />}
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
