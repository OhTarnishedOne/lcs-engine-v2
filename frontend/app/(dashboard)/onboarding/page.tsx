"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ChevronRight, Sparkles, ArrowRight } from "lucide-react";

import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { SkeletonCard } from "@/components/shared";
import type { OnboardingSection, OnboardingQuestion } from "@/lib/api/types";

export default function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [sectionResponses, setSectionResponses] = useState<Record<string, string>>({});
  const [showWelcome, setShowWelcome] = useState(false);

  // Fetch questions
  const { data: sections, isLoading } = useQuery({
    queryKey: ["onboarding-questions"],
    queryFn: () => api.getOnboardingQuestions(),
  });

  // Fetch welcome message (after completion)
  const { data: welcome } = useQuery({
    queryKey: ["onboarding-welcome"],
    queryFn: () => api.getWelcome(),
    enabled: showWelcome,
  });

  // Submit section responses
  const submitMutation = useMutation({
    mutationFn: ({ section, responses }: { section: string; responses: Record<string, string> }) =>
      api.submitOnboardingResponses(section, responses),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["onboarding-progress"] });
      if (data.is_complete) {
        completeMutation.mutate();
      } else if (sections && currentSectionIndex < sections.length - 1) {
        setCurrentSectionIndex((prev) => prev + 1);
        setCurrentQuestionIndex(0);
        setSectionResponses({});
      }
    },
  });

  // Complete onboarding
  const completeMutation = useMutation({
    mutationFn: () => api.completeOnboarding(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding-progress"] });
      setShowWelcome(true);
    },
  });

  const currentSection = sections?.[currentSectionIndex];
  const currentQuestion = currentSection?.questions[currentQuestionIndex];
  const totalQuestions = sections?.reduce((acc, s) => acc + s.questions.length, 0) || 0;
  const answeredQuestions = sections?.slice(0, currentSectionIndex).reduce((acc, s) => acc + s.questions.length, 0) || 0;
  const progress = totalQuestions > 0 ? (answeredQuestions + currentQuestionIndex) / totalQuestions : 0;

  const handleSelectOption = (questionId: string, value: string) => {
    setSectionResponses((prev) => ({ ...prev, [questionId]: value }));
    setResponses((prev) => ({ ...prev, [questionId]: value }));

    // Auto-advance after a short delay
    setTimeout(() => {
      if (currentSection && currentQuestionIndex < currentSection.questions.length - 1) {
        setCurrentQuestionIndex((prev) => prev + 1);
      } else if (currentSection) {
        // Submit section
        submitMutation.mutate({
          section: currentSection.id,
          responses: { ...sectionResponses, [questionId]: value },
        });
      }
    }, 300);
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <SkeletonCard lines={5} />
      </div>
    );
  }

  // Welcome screen after completion
  if (showWelcome) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mx-auto max-w-2xl"
      >
        <div className="rounded-xl border border-gray-800 bg-[#111827] p-8 text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", delay: 0.2 }}
            className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-[#00D4AA]/20"
          >
            <Sparkles className="h-8 w-8 text-[#00D4AA]" />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-2 text-2xl font-bold text-white"
          >
            Welcome, {welcome?.name || "Learner"}!
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mb-6 text-gray-400"
          >
            {welcome?.welcome_message || "Your personalized learning journey begins now."}
          </motion.p>

          {welcome?.suggested_first_steps && welcome.suggested_first_steps.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mb-6 rounded-lg bg-[#1A2942]/50 p-4 text-left"
            >
              <p className="mb-3 text-sm font-medium text-gray-300">
                Suggested first steps:
              </p>
              <ul className="space-y-2">
                {welcome.suggested_first_steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                    <Check className="mt-0.5 h-4 w-4 text-[#00D4AA]" />
                    {step}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Button
              onClick={() => router.push("/dashboard")}
              className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] btn-accent-glow"
            >
              Start Learning
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </motion.div>
        </div>
      </motion.div>
    );
  }

  if (!currentSection || !currentQuestion) {
    return null;
  }

  return (
    <div className="mx-auto max-w-2xl">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Section {currentSectionIndex + 1} of {sections?.length}
          </span>
          <span className="text-gray-400">
            {Math.round(progress * 100)}% complete
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-gray-800">
          <motion.div
            className="h-full bg-[#00D4AA]"
            initial={{ width: 0 }}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Section indicators */}
        <div className="mt-4 flex justify-center gap-2">
          {sections?.map((section, i) => (
            <div
              key={section.id}
              className={`h-2 w-8 rounded-full transition-colors ${
                i < currentSectionIndex
                  ? "bg-[#00D4AA]"
                  : i === currentSectionIndex
                  ? "bg-[#00D4AA]/50"
                  : "bg-gray-700"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Section title */}
      <motion.div
        key={currentSection.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 text-center"
      >
        <h2 className="text-xl font-semibold text-white">{currentSection.title}</h2>
        <p className="mt-1 text-sm text-gray-400">{currentSection.description}</p>
      </motion.div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion.id}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          className="rounded-xl border border-gray-800 bg-[#111827] p-6"
        >
          <h3 className="mb-6 text-lg font-medium text-white">
            {currentQuestion.text}
          </h3>

          <div className="space-y-3">
            {currentQuestion.options.map((option) => {
              const isSelected = sectionResponses[currentQuestion.id] === option.value;
              return (
                <motion.button
                  key={option.value}
                  onClick={() => handleSelectOption(currentQuestion.id, option.value)}
                  className={`w-full rounded-lg border p-4 text-left transition-all ${
                    isSelected
                      ? "border-[#00D4AA] bg-[#00D4AA]/10 shadow-[0_0_20px_rgba(0,212,170,0.15)]"
                      : "border-gray-700 bg-[#1A2942]/30 hover:border-gray-600 hover:bg-[#1A2942]/50"
                  }`}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className={`font-medium ${isSelected ? "text-[#00D4AA]" : "text-gray-200"}`}>
                        {option.label}
                      </p>
                      {option.description && (
                        <p className="mt-1 text-sm text-gray-500">{option.description}</p>
                      )}
                    </div>
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="flex h-5 w-5 items-center justify-center rounded-full bg-[#00D4AA]"
                      >
                        <Check className="h-3 w-3 text-[#0A1628]" />
                      </motion.div>
                    )}
                  </div>
                </motion.button>
              );
            })}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation hint */}
      <p className="mt-4 text-center text-xs text-gray-500">
        Select an option to continue
      </p>
    </div>
  );
}
