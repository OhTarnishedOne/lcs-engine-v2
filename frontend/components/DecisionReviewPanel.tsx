"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Award } from "lucide-react";

import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import type { ReviewSubmitResult } from "@/lib/api/types";

function titleizeSlug(slug: string): string {
  return slug
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

const fieldClass =
  "w-full rounded-md border border-gray-700 bg-[#0A1628] px-3 py-2 text-sm text-white placeholder:text-gray-500 outline-none transition-colors focus:border-[#00D4AA]";

export function DecisionReviewPanel({ decisionId }: { decisionId: string }) {
  const queryClient = useQueryClient();
  const [wasProcessSound, setWasProcessSound] = useState<boolean | null>(null);
  const [outcomeAttribution, setOutcomeAttribution] = useState("");
  const [luckVsProcess, setLuckVsProcess] = useState("");
  const [identifiedBias, setIdentifiedBias] = useState("");
  const [thesisRevised, setThesisRevised] = useState(false);
  const [selfFlaggedBias, setSelfFlaggedBias] = useState(false);
  const [result, setResult] = useState<ReviewSubmitResult | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      api.submitReview(decisionId, {
        was_process_sound: wasProcessSound,
        outcome_attribution: outcomeAttribution.trim() || null,
        luck_vs_process: luckVsProcess || null,
        identified_bias: identifiedBias.trim() || null,
        thesis_revised: thesisRevised,
        self_flagged_bias_before_ai: selfFlaggedBias,
      }),
    onSuccess: (res) => {
      setResult(res);
      toast.success("Reflection saved.");
      [
        "decision-journal",
        "decision-calibration",
        "decision-diagnosis",
        "active-intervention",
      ].forEach((key) => queryClient.invalidateQueries({ queryKey: [key] }));
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to save review.");
    },
  });

  if (result) {
    return (
      <div className="mt-3 rounded-lg border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4">
        <p className="text-sm font-semibold text-white">Reflection saved</p>
        {result.reflection_score !== null && (
          <p className="mt-1 text-xs text-gray-300">
            Reflection score{" "}
            <span className="font-mono-nums text-[#00D4AA]">
              {result.reflection_score}
            </span>
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
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-4 rounded-lg bg-[#1A2942]/50 p-4">
      {/* Was your process sound? */}
      <div className="space-y-2">
        <Label className="text-gray-300">Was your process sound?</Label>
        <div className="flex gap-2">
          {[
            { label: "Yes", value: true },
            { label: "No", value: false },
          ].map((opt) => (
            <button
              key={opt.label}
              type="button"
              onClick={() => setWasProcessSound(opt.value)}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                wasProcessSound === opt.value
                  ? "border-[#00D4AA] bg-[#00D4AA]/10 text-[#00D4AA]"
                  : "border-gray-700 text-gray-300 hover:border-gray-600"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500">
          A wrong call with a sound process is still good decision-making.
        </p>
      </div>

      {/* What drove the outcome? */}
      <div className="space-y-2">
        <Label htmlFor="attribution" className="text-gray-300">
          What drove the outcome?
        </Label>
        <textarea
          id="attribution"
          value={outcomeAttribution}
          onChange={(e) => setOutcomeAttribution(e.target.value)}
          rows={2}
          placeholder="Honestly — was it your reasoning, or something you couldn't have known?"
          className={fieldClass}
        />
      </div>

      {/* Luck vs process */}
      <div className="space-y-2">
        <Label htmlFor="luck" className="text-gray-300">
          Luck, process, or both?
        </Label>
        <select
          id="luck"
          value={luckVsProcess}
          onChange={(e) => setLuckVsProcess(e.target.value)}
          className={fieldClass}
        >
          <option value="" className="bg-[#0A1628]">
            Select…
          </option>
          <option value="process" className="bg-[#0A1628]">
            Mostly process
          </option>
          <option value="luck" className="bg-[#0A1628]">
            Mostly luck
          </option>
          <option value="both" className="bg-[#0A1628]">
            Both
          </option>
        </select>
      </div>

      {/* Identified bias */}
      <div className="space-y-2">
        <Label htmlFor="bias" className="text-gray-300">
          Any bias you noticed? <span className="text-gray-500">(optional)</span>
        </Label>
        <Input
          id="bias"
          value={identifiedBias}
          onChange={(e) => setIdentifiedBias(e.target.value)}
          placeholder="e.g. anchoring, overconfidence"
          className="border-gray-700 bg-[#0A1628] text-white placeholder:text-gray-500 focus-visible:border-[#00D4AA]"
        />
      </div>

      {/* Toggles */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={thesisRevised}
            onChange={(e) => setThesisRevised(e.target.checked)}
            className="h-4 w-4 accent-[#00D4AA]"
          />
          I revised my thesis based on the outcome
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={selfFlaggedBias}
            onChange={(e) => setSelfFlaggedBias(e.target.checked)}
            className="h-4 w-4 accent-[#00D4AA]"
          />
          I flagged my own bias before any AI did
        </label>
      </div>

      <Button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-50"
      >
        {mutation.isPending ? "Saving…" : "Save reflection"}
      </Button>
    </div>
  );
}
