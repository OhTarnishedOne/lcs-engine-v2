"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Send, Bot, User, Loader2 } from "lucide-react";

import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { trackEvent } from "@/lib/analytics";
import OnboardingFormFallback from "./form-fallback";
import TapScreens from "./tap-screens";

const TAP_SCREEN_KEYS = ["experience_level", "goals", "risk_tolerance", "interests", "learning_style"];

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

type Phase = "tap" | "chat" | "extracting" | "fallback";

function checkRetakeIntent(): boolean {
  if (typeof window === "undefined") return false;
  // Check both sessionStorage (durable) and URL param (initial signal)
  if (sessionStorage.getItem("onboarding_retake") === "true") return true;
  const params = new URLSearchParams(window.location.search);
  if (params.get("retake") === "true") {
    sessionStorage.setItem("onboarding_retake", "true");
    return true;
  }
  return false;
}

export default function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isRetake] = useState(checkRetakeIntent);

  const [phase, setPhase] = useState<Phase>("tap");
  const [tapResponses, setTapResponses] = useState<Record<string, string | string[]>>({});
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [completionStatus, setCompletionStatus] = useState<"continue" | "wrap_up" | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const assistantContentRef = useRef("");
  const rafIdRef = useRef<number>(0);
  const initialGreetingSent = useRef(false);
  const onboardingTrackedRef = useRef(false);

  // Check if already completed — redirect to dashboard
  const { data: progressData } = useQuery({
    queryKey: ["onboarding-progress"],
    queryFn: () => api.getOnboardingProgress(),
  });

  useEffect(() => {
    if (!progressData) return;
    if (progressData.is_complete && !isRetake) {
      router.replace("/dashboard");
      return;
    }

    // On retake, start fresh (don't resume partial tap state)
    if (isRetake) return;

    // Resume from saved tap responses (first-run only)
    const saved = progressData.tap_responses;
    if (saved && Object.keys(saved).length > 0) {
      const allTapsDone = TAP_SCREEN_KEYS.every((k) => k in saved);
      if (allTapsDone) {
        setTapResponses(saved);
        setPhase("chat");
      }
    }
  }, [progressData, router, isRetake]);

  useEffect(() => {
    if (!onboardingTrackedRef.current) {
      onboardingTrackedRef.current = true;
      trackEvent("onboarding_started");
    }
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // SSE stream consumer
  const consumeStream = useCallback(async (response: Response): Promise<string | null> => {
    const reader = response.body?.getReader();
    if (!reader) return null;

    const decoder = new TextDecoder();
    let sseBuffer = "";
    let resultCompletionStatus: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });
      const lines = sseBuffer.split("\n");
      sseBuffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6));

          if (data.type === "token") {
            assistantContentRef.current += data.content;
            if (!rafIdRef.current) {
              rafIdRef.current = requestAnimationFrame(() => {
                rafIdRef.current = 0;
                const content = assistantContentRef.current;
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const last = newMessages[newMessages.length - 1];
                  if (last?.role === "assistant") last.content = content;
                  return newMessages;
                });
              });
            }
          } else if (data.type === "done") {
            resultCompletionStatus = data.completion_status || null;
            if (rafIdRef.current) {
              cancelAnimationFrame(rafIdRef.current);
              rafIdRef.current = 0;
            }
            const finalContent = assistantContentRef.current;
            setMessages((prev) => {
              const newMessages = [...prev];
              const last = newMessages[newMessages.length - 1];
              if (last?.role === "assistant") {
                last.content = finalContent;
                last.isStreaming = false;
              }
              return newMessages;
            });
          } else if (data.type === "error") {
            throw new Error(data.content || "Stream error");
          }
        } catch (e) {
          if (e instanceof Error && e.message !== "Stream error") continue;
          throw e;
        }
      }
    }

    return resultCompletionStatus;
  }, []);

  // Save a single tap screen response to the backend
  const handleSaveTapScreen = async (key: string, value: string | string[]) => {
    await api.saveTapResponse(key, value);
  };

  // Handle tap screens completion
  const handleTapComplete = (responses: Record<string, string | string[]>) => {
    setTapResponses(responses);
    trackEvent("onboarding_taps_completed");
    setPhase("chat");
  };

  // Handle skip during taps
  const handleTapSkip = async () => {
    try {
      await api.skipOnboarding();
      trackEvent("onboarding_skipped", { phase: "tap" });
      queryClient.invalidateQueries({ queryKey: ["onboarding-progress"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      router.replace("/dashboard");
    } catch {
      // Silently fail
    }
  };

  // Send initial greeting when entering chat phase
  useEffect(() => {
    if (phase !== "chat" || initialGreetingSent.current || progressData?.is_complete) return;
    initialGreetingSent.current = true;

    const sendGreeting = async () => {
      setIsStreaming(true);
      assistantContentRef.current = "";

      setMessages([{ role: "assistant", content: "", isStreaming: true }]);

      try {
        const response = await api.sendOnboardingChat([], tapResponses);
        const status = await consumeStream(response);
        if (status) setCompletionStatus(status as "continue" | "wrap_up");
      } catch {
        setMessages([{
          role: "assistant",
          content: "Great choices! Now I'd love to learn a bit more about you. What made you decide to start learning about investing?",
          isStreaming: false,
        }]);
      } finally {
        setIsStreaming(false);
        inputRef.current?.focus();
      }
    };

    sendGreeting();
  }, [phase, progressData?.is_complete, consumeStream, tapResponses]);

  // Handle extraction after wrap_up
  const handleExtraction = useCallback(async (allMessages: ChatMessage[]) => {
    setPhase("extracting");
    trackEvent("onboarding_chat_extracting");

    try {
      const transcript = allMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const result = await api.completeOnboardingConversation(tapResponses, transcript);

      if (result.ok) {
        trackEvent("onboarding_completed", { method: "hybrid" });
        sessionStorage.removeItem("onboarding_retake"); // Clear retake intent
        queryClient.invalidateQueries({ queryKey: ["onboarding-progress"] });
        queryClient.invalidateQueries({ queryKey: ["profile"] });
        router.replace("/profile?welcome=true");
      } else {
        trackEvent("onboarding_extraction_failed");
        setPhase("fallback");
      }
    } catch {
      setPhase("fallback");
    }
  }, [queryClient, router, tapResponses]);

  // Send user message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setIsStreaming(true);
    assistantContentRef.current = "";

    const updatedMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: userMessage },
    ];
    setMessages([...updatedMessages, { role: "assistant", content: "", isStreaming: true }]);

    try {
      const apiMessages = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await api.sendOnboardingChat(apiMessages, tapResponses);
      const status = await consumeStream(response);

      if (status) {
        setCompletionStatus(status as "continue" | "wrap_up");

        if (status === "wrap_up") {
          setTimeout(() => {
            setMessages((currentMessages) => {
              handleExtraction(currentMessages);
              return currentMessages;
            });
          }, 1500);
        }
      }
    } catch {
      setMessages((prev) => {
        const newMessages = [...prev];
        const last = newMessages[newMessages.length - 1];
        if (last?.role === "assistant") {
          last.content = "Sorry, something went wrong. Please try again.";
          last.isStreaming = false;
        }
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  // Handle skip during chat
  const handleChatSkip = async () => {
    try {
      const transcript = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      await api.completeOnboardingConversation(tapResponses, transcript);
      trackEvent("onboarding_skipped", { phase: "chat" });
      sessionStorage.removeItem("onboarding_retake");
      queryClient.invalidateQueries({ queryKey: ["onboarding-progress"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      router.replace("/dashboard");
    } catch {
      // Fallback to basic skip
      try {
        await api.skipOnboarding();
        router.replace("/dashboard");
      } catch {
        // Silently fail
      }
    }
  };

  // TAP PHASE
  if (phase === "tap") {
    return (
      <TapScreens
        onComplete={handleTapComplete}
        onSkip={handleTapSkip}
        initialResponses={progressData?.tap_responses ?? undefined}
        onSaveScreen={handleSaveTapScreen}
      />
    );
  }

  // FALLBACK PHASE
  if (phase === "fallback") {
    return (
      <div>
        <div className="mx-auto mb-4 max-w-2xl rounded-lg border border-yellow-600/30 bg-yellow-900/20 p-3 text-center text-sm text-yellow-300">
          Let&apos;s try the quick form instead — it only takes 30 seconds.
        </div>
        <OnboardingFormFallback />
      </div>
    );
  }

  // EXTRACTING PHASE
  if (phase === "extracting") {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin text-[#00D4AA]" />
          <h2 className="mb-2 text-lg font-semibold text-white">Building your profile...</h2>
          <p className="text-sm text-gray-400">Personalizing your learning experience</p>
        </motion.div>
      </div>
    );
  }

  // CHAT PHASE
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes pulse-dot {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
      ` }} />

      <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-2xl flex-col">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-white">Let&apos;s go a bit deeper...</h1>
            <span
              className="inline-block h-2 w-2 rounded-full bg-[#00D4AA]"
              style={{ animation: "pulse-dot 2s ease-in-out infinite" }}
            />
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto rounded-xl border border-gray-800 bg-[#111827] p-4 lg:p-6">
          <div className="space-y-6">
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-4 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#1A2942]">
                    <Bot className="h-4 w-4 text-[#00D4AA]" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-[#00D4AA]/20 text-gray-100"
                      : "bg-[#1A2942] text-gray-200"
                  }`}
                >
                  <p className="whitespace-pre-wrap text-base leading-relaxed">
                    {message.content}
                    {message.isStreaming && (
                      <span
                        className="ml-0.5 inline-block w-0.5 h-[1.1em] bg-[#00D4AA] align-middle"
                        style={{ animation: "blink 1s steps(2) infinite" }}
                      />
                    )}
                  </p>
                </div>
                {message.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#00D4AA]/20">
                    <User className="h-4 w-4 text-[#00D4AA]" />
                  </div>
                )}
              </motion.div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="mt-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex gap-3"
          >
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your answer..."
              disabled={isStreaming || completionStatus === "wrap_up"}
              className="flex-1 border-gray-700 bg-[#1A2942] text-base text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA]"
            />
            <Button
              type="submit"
              disabled={!inputValue.trim() || isStreaming || completionStatus === "wrap_up"}
              className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-50"
            >
              {isStreaming ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>

          {/* Skip link */}
          <div className="mt-2 text-center">
            <button
              onClick={handleChatSkip}
              className="text-xs text-gray-500 transition-colors hover:text-gray-400"
            >
              Skip for now
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
