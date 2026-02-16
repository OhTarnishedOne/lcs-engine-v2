"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ChevronRight, Sparkles, ArrowRight } from "lucide-react";

import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { SkeletonCard } from "@/components/shared";
import type { OnboardingSection } from "@/lib/api/types";

export default function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [sectionResponses, setSectionResponses] = useState<Record<string, string>>({});
  const [showWelcome, setShowWelcome] = useState(false);
  const [hasResumed, setHasResumed] = useState(false);
  const advanceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch questions
  const { data: questionsData, isLoading } = useQuery({
    queryKey: ["onboarding-questions"],
    queryFn: () => api.getOnboardingQuestions(),
  });
  const sections: OnboardingSection[] | undefined = Array.isArray(questionsData?.sections)
    ? questionsData.sections
    : undefined;

  // Fetch onboarding progress for resumption
  const { data: progressData } = useQuery({
    queryKey: ["onboarding-progress"],
    queryFn: () => api.getOnboardingProgress(),
  });

  // Resume progress on page load
  useEffect(() => {
    if (!progressData || !sections || hasResumed) return;
    setHasResumed(true);
    if (progressData.is_complete) {
      setShowWelcome(true);
      return;
    }
    if (progressData.current_section) {
      const idx = sections.findIndex((s) => s.section === progressData.current_section);
      if (idx >= 0) {
        setCurrentSectionIndex(idx);
        setCurrentQuestionIndex(0);
      }
    }
  }, [progressData, sections, hasResumed]);

  // Fetch welcome message (after completion)
  const { data: welcome } = useQuery({
    queryKey: ["onboarding-welcome"],
    queryFn: () => api.getWelcome(),
    enabled: showWelcome,
  });

  // Submit section responses
  const submitMutation = useMutation({
    mutationFn: ({ section, responses }: { section: number; responses: Record<string, string> }) =>
      api.submitSectionResponses(section, responses),
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

  const advanceQuestion = (questionId: string, value: string) => {
    if (currentSection && currentQuestionIndex < currentSection.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else if (currentSection) {
      // Submit section
      submitMutation.mutate({
        section: currentSection.section,
        responses: { ...sectionResponses, [questionId]: value },
      });
    }
  };

  const handleSelectOption = (questionId: string, value: string) => {
    // Cancel any pending advance so only the latest click takes effect
    if (advanceTimerRef.current) {
      clearTimeout(advanceTimerRef.current);
    }

    // Replace (not accumulate) the value for this question
    setSectionResponses((prev) => ({ ...prev, [questionId]: value }));
    setResponses((prev) => ({ ...prev, [questionId]: value }));

    // Auto-advance after a short delay
    advanceTimerRef.current = setTimeout(() => {
      advanceTimerRef.current = null;
      advanceQuestion(questionId, value);
    }, 300);
  };

  const handleTextSubmit = () => {
    if (!currentQuestion) return;
    const value = (sectionResponses[currentQuestion.key] || "").trim();
    if (currentQuestion.required && !value) return;
    setSectionResponses((prev) => ({ ...prev, [currentQuestion.key]: value }));
    setResponses((prev) => ({ ...prev, [currentQuestion.key]: value }));
    advanceQuestion(currentQuestion.key, value);
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
            {welcome?.greeting || "Welcome! We're glad you're here."}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mb-2 text-gray-300"
          >
            {welcome?.acknowledgment || ""}
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
            className="mb-6 text-gray-400"
          >
            {welcome?.encouragement || "Your personalized learning journey begins now."}
          </motion.p>

          {welcome?.personalized_tips && welcome.personalized_tips.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mb-6 rounded-lg bg-[#1A2942]/50 p-4 text-left"
            >
              <p className="mb-3 text-sm font-medium text-gray-300">
                Personalized tips for you:
              </p>
              <ul className="space-y-3">
                {welcome.personalized_tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#00D4AA]" />
                    <div>
                      <p className="font-medium text-gray-200">{tip.title}</p>
                      <p className="text-gray-400">{tip.description}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {welcome?.recommended_action_label && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.55 }}
              className="mb-6 rounded-lg border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4"
            >
              <p className="text-sm font-medium text-[#00D4AA]">
                {welcome.recommended_action_label}
              </p>
              <p className="mt-1 text-sm text-gray-400">
                {welcome.recommended_action_description}
              </p>
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
              key={section.section}
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
        key={currentSection.section}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 text-center"
      >
        <h2 className="text-xl font-semibold text-white">{currentSection.title}</h2>
        <p className="mt-1 text-sm text-gray-400">{currentSection.subtitle}</p>
      </motion.div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion.key}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          className="rounded-xl border border-gray-800 bg-[#111827] p-6"
        >
          <h3 className="mb-6 text-lg font-medium text-white">
            {currentQuestion.text}
          </h3>

          {currentQuestion.options && currentQuestion.options.length > 0 ? (
            <div className="space-y-3">
              {currentQuestion.options.map((option) => {
                const isSelected = sectionResponses[currentQuestion.key] === option.value;
                return (
                  <motion.button
                    key={option.value}
                    onClick={() => handleSelectOption(currentQuestion.key, option.value)}
                    className={`w-full rounded-lg border px-5 py-4 text-left transition-all ${
                      isSelected
                        ? "border-[#00D4AA] bg-[#00D4AA]/10 shadow-[0_0_20px_rgba(0,212,170,0.15)]"
                        : "border-gray-700 bg-[#1A2942]/30 hover:border-gray-600 hover:bg-[#1A2942]/50"
                    }`}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        {option.emoji && (
                          <span className="text-lg">{option.emoji}</span>
                        )}
                        <p className={`text-base font-medium ${isSelected ? "text-[#00D4AA]" : "text-gray-200"}`}>
                          {option.label}
                        </p>
                      </div>
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#00D4AA]"
                        >
                          <Check className="h-3.5 w-3.5 text-[#0A1628]" />
                        </motion.div>
                      )}
                    </div>
                  </motion.button>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              <textarea
                value={sectionResponses[currentQuestion.key] || ""}
                onChange={(e) => {
                  const v = e.target.value;
                  setSectionResponses((prev) => ({ ...prev, [currentQuestion.key]: v }));
                  setResponses((prev) => ({ ...prev, [currentQuestion.key]: v }));
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleTextSubmit();
                  }
                }}
                placeholder={currentQuestion.placeholder || "Type your answer..."}
                rows={3}
                className="w-full resize-none rounded-lg border border-gray-700 bg-[#1A2942]/30 p-4 text-gray-200 placeholder-gray-500 outline-none transition-colors focus:border-[#00D4AA] focus:ring-1 focus:ring-[#00D4AA]"
              />
              <div className="flex items-center justify-between">
                {!currentQuestion.required && (
                  <span className="text-xs text-gray-500">Optional</span>
                )}
                <Button
                  onClick={handleTextSubmit}
                  disabled={currentQuestion.required && !(sectionResponses[currentQuestion.key] || "").trim()}
                  className="ml-auto bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] btn-accent-glow disabled:opacity-50"
                >
                  Continue
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation hint */}
      <p className="mt-4 text-center text-xs text-gray-500">
        {currentQuestion.options && currentQuestion.options.length > 0
          ? "Select an option to continue"
          : "Press Enter or click Continue"}
      </p>
    </div>
  );
}
