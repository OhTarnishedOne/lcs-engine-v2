"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";

interface ScreenOption {
  value: string;
  label: string;
  description?: string;
  emoji: string;
}

interface Screen {
  key: string;
  title: string;
  multiSelect: boolean;
  maxSelect?: number;
  options: ScreenOption[];
}

const SCREENS: Screen[] = [
  {
    key: "experience_level",
    title: "How much investing experience do you have?",
    multiSelect: false,
    options: [
      { value: "none", label: "None yet", emoji: "\u{1F331}" },
      { value: "a_little", label: "A little", emoji: "\u{1F4DA}" },
      { value: "some", label: "Some experience", emoji: "\u{1F4CA}" },
      { value: "regular", label: "I invest regularly", emoji: "\u{1F680}" },
    ],
  },
  {
    key: "goals",
    title: "What are your main goals?",
    multiSelect: true,
    maxSelect: 3,
    options: [
      { value: "learn_basics", label: "Learn the basics", emoji: "\u{1F393}" },
      { value: "grow_wealth", label: "Grow my wealth", emoji: "\u{1F4C8}" },
      { value: "retirement", label: "Retire comfortably", emoji: "\u{1F3D6}\u{FE0F}" },
      { value: "side_income", label: "Earn side income", emoji: "\u{1F4B0}" },
      { value: "support_family", label: "Support my family", emoji: "\u{1F468}\u{200D}\u{1F469}\u{200D}\u{1F467}" },
      { value: "understand_news", label: "Understand the news", emoji: "\u{1F4F0}" },
    ],
  },
  {
    key: "risk_tolerance",
    title: "How do you feel about risk?",
    multiSelect: false,
    options: [
      {
        value: "conservative",
        label: "Keep it steady",
        description: "I'd rather grow slowly than risk losing money",
        emoji: "\u{1F6E1}\u{FE0F}",
      },
      {
        value: "moderate",
        label: "Some ups and downs are fine",
        description: "I can handle short-term dips",
        emoji: "\u{2696}\u{FE0F}",
      },
      {
        value: "aggressive",
        label: "Bring it on",
        description: "I'm okay with big swings for bigger potential gains",
        emoji: "\u{1F3AF}",
      },
    ],
  },
  {
    key: "interests",
    title: "What interests you?",
    multiSelect: true,
    maxSelect: 4,
    options: [
      { value: "stocks", label: "Stocks", emoji: "\u{1F4CA}" },
      { value: "etfs", label: "ETFs", emoji: "\u{1F4E6}" },
      { value: "crypto", label: "Crypto", emoji: "\u{1FA99}" },
      { value: "real_estate", label: "Real Estate", emoji: "\u{1F3E0}" },
      { value: "bonds", label: "Bonds", emoji: "\u{1F4C4}" },
      { value: "options", label: "Options", emoji: "\u{1F3B2}" },
      { value: "not_sure", label: "Not sure yet", emoji: "\u{1F937}" },
    ],
  },
  {
    key: "learning_style",
    title: "How do you like to learn?",
    multiSelect: true,
    maxSelect: 2,
    options: [
      { value: "detailed", label: "Step-by-step explanations", emoji: "\u{1F4D6}" },
      { value: "examples", label: "Real-world examples", emoji: "\u{1F30D}" },
      { value: "actionable", label: "Quick actionable tips", emoji: "\u{26A1}" },
      { value: "deep_dive", label: "Deep dives with data", emoji: "\u{1F52C}" },
    ],
  },
];

interface TapScreensProps {
  onComplete: (responses: Record<string, string | string[]>) => void;
  onSkip: () => void;
}

export default function TapScreens({ onComplete, onSkip }: TapScreensProps) {
  const [currentScreen, setCurrentScreen] = useState(0);
  const [responses, setResponses] = useState<Record<string, string | string[]>>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = backward

  const screen = SCREENS[currentScreen];

  const handleSelect = (value: string) => {
    if (screen.multiSelect) {
      setSelected((prev) => {
        if (prev.includes(value)) {
          return prev.filter((v) => v !== value);
        }
        if (screen.maxSelect && prev.length >= screen.maxSelect) {
          return prev;
        }
        return [...prev, value];
      });
    } else {
      setSelected([value]);
    }
  };

  const handleContinue = () => {
    if (selected.length === 0) return;

    const value = screen.multiSelect ? selected : selected[0];
    const newResponses = { ...responses, [screen.key]: value };
    setResponses(newResponses);

    if (currentScreen < SCREENS.length - 1) {
      setDirection(1);
      setCurrentScreen((prev) => prev + 1);
      setSelected([]);
    } else {
      onComplete(newResponses);
    }
  };

  const slideVariants = {
    enter: (dir: number) => ({
      x: dir > 0 ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (dir: number) => ({
      x: dir > 0 ? -300 : 300,
      opacity: 0,
    }),
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-lg flex-col">
      {/* Progress dots */}
      <div className="mb-8 flex justify-center gap-2">
        {SCREENS.map((_, i) => (
          <div
            key={i}
            className={`h-2 w-2 rounded-full transition-colors ${
              i === currentScreen
                ? "bg-[#00D4AA]"
                : i < currentScreen
                ? "bg-[#00D4AA]/50"
                : "bg-gray-700"
            }`}
          />
        ))}
      </div>

      {/* Screen content */}
      <div className="relative flex-1 overflow-hidden">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentScreen}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="absolute inset-0 flex flex-col"
          >
            <h2 className="mb-6 text-center text-xl font-semibold text-white sm:text-2xl">
              {screen.title}
            </h2>

            {screen.multiSelect && screen.maxSelect && (
              <p className="mb-4 text-center text-sm text-gray-400">
                Pick up to {screen.maxSelect}
              </p>
            )}

            <div className="space-y-3">
              {screen.options.map((option) => {
                const isSelected = selected.includes(option.value);
                return (
                  <button
                    key={option.value}
                    onClick={() => handleSelect(option.value)}
                    className={`flex min-h-[4rem] w-full items-center gap-4 rounded-xl border p-4 text-left transition-all ${
                      isSelected
                        ? "border-[#00D4AA] bg-[#00D4AA]/10"
                        : "border-gray-800 bg-[#111827] hover:border-gray-600"
                    }`}
                  >
                    <span className="text-2xl">{option.emoji}</span>
                    <div className="flex-1">
                      <span className="text-base font-medium text-white">
                        {option.label}
                      </span>
                      {option.description && (
                        <p className="mt-0.5 text-sm text-gray-400">
                          {option.description}
                        </p>
                      )}
                    </div>
                    {isSelected && (
                      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#00D4AA]">
                        <svg
                          className="h-3 w-3 text-[#0A1628]"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={3}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Bottom actions */}
      <div className="mt-4 space-y-2 pb-4">
        <Button
          onClick={handleContinue}
          disabled={selected.length === 0}
          className="w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-50 h-12 text-base"
        >
          {currentScreen === SCREENS.length - 1 ? "Continue" : "Continue"}
        </Button>
        <div className="text-center">
          <button
            onClick={onSkip}
            className="text-xs text-gray-500 transition-colors hover:text-gray-400"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
}
