"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, X, Award } from "lucide-react";

import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import type { DecisionResolveResult } from "@/lib/api/types";

function titleizeSlug(slug: string): string {
  return slug
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

const fieldClass =
  "w-full rounded-md border border-gray-700 bg-[#0A1628] px-3 py-2 text-sm text-white placeholder:text-gray-500 outline-none transition-colors focus:border-[#00D4AA]";

export function DecisionResolvePanel({ decisionId }: { decisionId: string }) {
  const queryClient = useQueryClient();
  const [outcome, setOutcome] = useState<boolean | null>(null);
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<DecisionResolveResult | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      api.resolveDecision(decisionId, {
        outcome_binary: outcome as boolean,
        outcome_notes: notes.trim() || null,
      }),
    onSuccess: (res) => {
      setResult(res);
      toast.success("Decision resolved and scored.");
      [
        "decisions-pending",
        "decision-journal",
        "decision-calibration",
        "decision-diagnosis",
        "active-intervention",
      ].forEach((key) => queryClient.invalidateQueries({ queryKey: [key] }));
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to resolve.");
    },
  });

  if (result) {
    return (
      <div className="mt-3 rounded-lg border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4">
        <p className="text-sm font-semibold text-white">Resolved &amp; scored</p>
        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-300">
          {result.brier_score !== null && (
            <span>
              Brier{" "}
              <span className="font-mono-nums text-white">
                {result.brier_score}
              </span>
            </span>
          )}
          {result.calibration_score !== null && (
            <span>
              Calibration{" "}
              <span className="font-mono-nums text-[#00D4AA]">
                {result.calibration_score}
              </span>
            </span>
          )}
          {result.is_calibrated !== null && (
            <span className={result.is_calibrated ? "text-[#00D4AA]" : "text-amber-400"}>
              {result.is_calibrated ? "Well calibrated" : "Miscalibrated"}
            </span>
          )}
        </div>
        {result.tier_advanced && result.tier && (
          <p className="mt-2 text-xs text-[#00D4AA]">
            Tier advanced to {titleizeSlug(result.tier)}!
          </p>
        )}
        {result.badges_awarded.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {result.badges_awarded.map((slug) => (
              <span
                key={slug}
                className="inline-flex items-center gap-1 rounded-full border border-[#00D4AA]/30 bg-[#00D4AA]/10 px-2.5 py-0.5 text-xs font-medium text-[#00D4AA]"
              >
                <Award className="h-3 w-3" />
                {titleizeSlug(slug)}
              </span>
            ))}
          </div>
        )}
        <p className="mt-3 text-xs text-gray-500">
          Now review it below to close the loop and earn reflection points.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg bg-[#1A2942]/50 p-4">
      <p className="text-xs uppercase tracking-wide text-gray-500">
        What actually happened?
      </p>
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          onClick={() => setOutcome(true)}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
            outcome === true
              ? "border-[#00D4AA] bg-[#00D4AA]/10 text-[#00D4AA]"
              : "border-gray-700 text-gray-300 hover:border-gray-600"
          }`}
        >
          <Check className="h-4 w-4" />
          It happened
        </button>
        <button
          type="button"
          onClick={() => setOutcome(false)}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
            outcome === false
              ? "border-amber-400 bg-amber-400/10 text-amber-400"
              : "border-gray-700 text-gray-300 hover:border-gray-600"
          }`}
        >
          <X className="h-4 w-4" />
          It didn&apos;t
        </button>
      </div>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        rows={2}
        placeholder="Notes on the outcome (optional)"
        className={`mt-3 ${fieldClass}`}
      />
      <Button
        onClick={() => mutation.mutate()}
        disabled={outcome === null || mutation.isPending}
        className="mt-3 w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-50"
      >
        {mutation.isPending ? "Scoring…" : "Resolve & score"}
      </Button>
    </div>
  );
}
