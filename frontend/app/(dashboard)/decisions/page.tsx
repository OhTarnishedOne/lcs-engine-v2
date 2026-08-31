"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  ClipboardList,
  Plus,
  Clock,
  CheckCircle2,
  Award,
  ArrowRight,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";
import { DecisionResolvePanel } from "@/components/DecisionResolvePanel";
import { DecisionReviewPanel } from "@/components/DecisionReviewPanel";
import type { DecisionRecord, JournalEntry, ReviewRecord } from "@/lib/api/types";

function pct(conf: number): string {
  return `${Math.round(conf * 100)}%`;
}

function PendingCard({ decision }: { decision: DecisionRecord }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-white">{decision.question}</p>
          <p className="mt-1 text-xs text-gray-500">
            Confidence{" "}
            <span className="font-mono-nums text-[#00D4AA]">
              {pct(decision.confidence)}
            </span>{" "}
            · {decision.domain} · committed
          </p>
        </div>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="shrink-0 rounded-lg border border-[#00D4AA]/40 px-3 py-1.5 text-xs font-medium text-[#00D4AA] transition-colors hover:bg-[#00D4AA]/10"
        >
          {open ? "Cancel" : "Resolve"}
        </button>
      </div>
      {open && <DecisionResolvePanel decisionId={decision.id} />}
    </div>
  );
}

function ReviewSummary({ review }: { review: ReviewRecord }) {
  const verdicts: string[] = [];
  if (review.triggers_good_loser) verdicts.push("Good Loser");
  if (review.triggers_humble_winner) verdicts.push("Humble Winner");
  return (
    <div className="mt-3 rounded-lg bg-[#1A2942]/50 p-3">
      <p className="text-xs uppercase tracking-wide text-gray-500">Reviewed</p>
      {review.outcome_attribution && (
        <p className="mt-1 text-sm text-gray-200">{review.outcome_attribution}</p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {verdicts.map((v) => (
          <span
            key={v}
            className="inline-flex items-center gap-1 rounded-full border border-[#00D4AA]/30 bg-[#00D4AA]/10 px-2.5 py-0.5 text-xs font-medium text-[#00D4AA]"
          >
            <Award className="h-3 w-3" />
            {v}
          </span>
        ))}
        <span className="text-xs text-gray-500">
          +{review.reflection_points} reflection pts
        </span>
      </div>
    </div>
  );
}

function JournalCard({ entry }: { entry: JournalEntry }) {
  const [open, setOpen] = useState(false);
  const { decision, review } = entry;
  const happened = decision.outcome_binary;
  return (
    <div className="rounded-xl border border-gray-800 bg-[#111827] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-white">{decision.question}</p>
          <p className="mt-1 text-xs text-gray-500">
            Predicted{" "}
            <span className="font-mono-nums text-[#00D4AA]">
              {pct(decision.confidence)}
            </span>{" "}
            ·{" "}
            <span className={happened ? "text-[#00D4AA]" : "text-amber-400"}>
              {happened ? "Happened" : "Didn't happen"}
            </span>
            {decision.brier_score !== null && (
              <>
                {" "}
                · Brier{" "}
                <span className="font-mono-nums text-gray-300">
                  {decision.brier_score}
                </span>
              </>
            )}
          </p>
        </div>
        {!review && (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="shrink-0 rounded-lg border border-[#00D4AA]/40 px-3 py-1.5 text-xs font-medium text-[#00D4AA] transition-colors hover:bg-[#00D4AA]/10"
          >
            {open ? "Cancel" : "Review"}
          </button>
        )}
      </div>
      {review ? (
        <ReviewSummary review={review} />
      ) : (
        open && <DecisionReviewPanel decisionId={decision.id} />
      )}
    </div>
  );
}

export default function DecisionsPage() {
  const { isAuthenticated } = useAuthStore();

  const pending = useQuery({
    queryKey: ["decisions-pending"],
    queryFn: () => api.getDecisions("pending"),
    enabled: isAuthenticated,
  });

  const journal = useQuery({
    queryKey: ["decision-journal"],
    queryFn: () => api.getDecisionJournal(),
    enabled: isAuthenticated,
  });

  const isLoading = pending.isLoading || journal.isLoading;
  const isError = pending.isError || journal.isError;
  const pendingDecisions = pending.data?.decisions ?? [];
  const journalEntries = journal.data?.entries ?? [];
  const isEmpty = pendingDecisions.length === 0 && journalEntries.length === 0;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-6 w-6 text-[#00D4AA]" />
          <h1 className="text-2xl font-bold text-white">Your decisions</h1>
        </div>
        <Link
          href="/decisions/new"
          className="inline-flex items-center gap-2 rounded-lg bg-[#00D4AA] px-3 py-2 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
        >
          <Plus className="h-4 w-4" />
          Log a decision
        </Link>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-20 w-full skeleton-shimmer rounded-xl"
            />
          ))}
        </div>
      )}

      {!isLoading && isError && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6">
          <p className="text-sm font-medium text-white">
            Couldn&apos;t load your decisions
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Something went wrong. Try refreshing.
          </p>
        </div>
      )}

      {!isLoading && !isError && isEmpty && (
        <div className="rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-6 text-center">
          <p className="text-sm text-gray-300">
            No decisions yet. Log your first one to start the loop.
          </p>
          <Link
            href="/decisions/new"
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#00D4AA] px-4 py-2 text-sm font-semibold text-[#0A1628] transition-colors hover:bg-[#00F0C0]"
          >
            Log a decision
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {!isLoading && !isError && !isEmpty && (
        <div className="space-y-8">
          {/* Open decisions */}
          {pendingDecisions.length > 0 && (
            <motion.section
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="mb-3 flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-400" />
                <h2 className="text-sm font-semibold text-white">
                  Open — awaiting resolution ({pendingDecisions.length})
                </h2>
              </div>
              <div className="space-y-3">
                {pendingDecisions.map((d) => (
                  <PendingCard key={d.id} decision={d} />
                ))}
              </div>
            </motion.section>
          )}

          {/* Journal */}
          {journalEntries.length > 0 && (
            <motion.section
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
            >
              <div className="mb-3 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00D4AA]" />
                <h2 className="text-sm font-semibold text-white">
                  Journal — resolved ({journalEntries.length})
                </h2>
              </div>
              <div className="space-y-3">
                {journalEntries.map((entry) => (
                  <JournalCard key={entry.decision.id} entry={entry} />
                ))}
              </div>
            </motion.section>
          )}
        </div>
      )}
    </div>
  );
}
