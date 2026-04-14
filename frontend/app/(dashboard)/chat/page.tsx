"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Plus,
  MessageSquare,
  Trash2,
  MoreVertical,
  Loader2,
  Bot,
  User,
  X,
  Menu,
} from "lucide-react";

import { api, API_URL } from "@/lib/api/client";
import { trackEvent } from "@/lib/analytics";
import type { Strategy } from "@/lib/api/types";
import { useSessionStatus } from "@/hooks/useSessionStatus";
import { UpgradeBanner } from "@/components/UpgradeBanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface StreamingMessage {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function ChatPage() {
  const queryClient = useQueryClient();
  const { limitReached } = useSessionStatus();
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<StreamingMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const assistantContentRef = useRef("");
  const rafIdRef = useRef<number>(0);

  // Fetch user strategies for context injection
  const { data: strategiesData } = useQuery({
    queryKey: ["strategies"],
    queryFn: () => api.getStrategies(),
    staleTime: 5 * 60 * 1000,
  });

  const buildStrategyContext = useCallback((strategies: Strategy[]): string => {
    return strategies
      .map((s, i) => {
        const assets = s.assets
          .map((a) => `${a.ticker} ${a.allocation_pct}%`)
          .join(", ");
        return `Strategy ${i + 1}: "${s.name}" (${s.strategy_type}, risk ${s.risk_level}, ${s.time_horizon}) — ${assets}`;
      })
      .join("; ");
  }, []);

  // Fetch conversations
  const { data: conversationsData, isLoading: conversationsLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.getConversations(),
  });

  // Fetch selected conversation
  const { data: conversationDetail } = useQuery({
    queryKey: ["conversation", selectedConversationId],
    queryFn: () => api.getConversation(selectedConversationId!),
    enabled: !!selectedConversationId,
  });

  // Delete conversation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      if (selectedConversationId) {
        setSelectedConversationId(null);
        setMessages([]);
      }
    },
  });

  // Update messages when conversation changes
  useEffect(() => {
    if (conversationDetail?.messages) {
      setMessages(conversationDetail.messages.map((m) => ({ ...m })));
    }
  }, [conversationDetail]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage = inputValue.trim();
    trackEvent("chat_message_sent");
    setInputValue("");
    setIsStreaming(true);
    assistantContentRef.current = "";

    // Build message with optional strategy context
    let messageToSend = userMessage;
    const strategies = strategiesData?.strategies;
    if (
      strategies &&
      strategies.length > 0 &&
      /strateg|portfolio|my investment|my stock|my holding|allocation/i.test(userMessage)
    ) {
      const context = buildStrategyContext(strategies);
      messageToSend = `${userMessage}\n\n[Context for AI — not from the user: The user has these saved strategies: ${context}]`;
    }

    // Add user message (display original without context)
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    // Add placeholder for assistant
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", isStreaming: true },
    ]);

    try {
      const token = api.getAccessToken();
      const response = await fetch(`${API_URL}/chat/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: messageToSend,
          conversation_id: selectedConversationId,
        }),
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let newConversationId = selectedConversationId;
      let sseBuffer = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        sseBuffer += decoder.decode(value, { stream: true });
        const lines = sseBuffer.split("\n");
        sseBuffer = lines.pop() || ""; // Keep incomplete last line in buffer

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "start") {
              newConversationId = data.conversation_id;
              if (!selectedConversationId) {
                setSelectedConversationId(newConversationId);
                queryClient.invalidateQueries({ queryKey: ["session-status"] });
              }
            } else if (data.type === "token") {
              assistantContentRef.current += data.content;
              if (!rafIdRef.current) {
                rafIdRef.current = requestAnimationFrame(() => {
                  rafIdRef.current = 0;
                  const content = assistantContentRef.current;
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const last = newMessages[newMessages.length - 1];
                    if (last.role === "assistant") last.content = content;
                    return newMessages;
                  });
                });
              }
            } else if (data.type === "done") {
              if (rafIdRef.current) {
                cancelAnimationFrame(rafIdRef.current);
                rafIdRef.current = 0;
              }
              const finalContent = assistantContentRef.current;
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage.role === "assistant") {
                  lastMessage.content = finalContent;
                  lastMessage.isStreaming = false;
                }
                return newMessages;
              });
            } else if (data.type === "error") {
              throw new Error(data.message || "Stream error");
            }
          } catch (e) {
            if (e instanceof Error && e.message !== "Stream error") continue;
            throw e;
          }
        }
      }

      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    } catch {
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage.role === "assistant") {
          lastMessage.content = "Sorry, something went wrong. Please try again.";
          lastMessage.isStreaming = false;
        }
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleNewChat = () => {
    setSelectedConversationId(null);
    setMessages([]);
    setMobileSidebarOpen(false);
    inputRef.current?.focus();
  };

  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
    setMobileSidebarOpen(false);
  };

  const conversations = conversationsData?.conversations || [];

  return (
    <>
    <style dangerouslySetInnerHTML={{ __html: `
      @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }
    ` }} />
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden rounded-xl border border-gray-800 bg-[#111827]">
      {/* Mobile sidebar toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-4 top-4 z-20 lg:hidden text-gray-400"
        onClick={() => setMobileSidebarOpen(true)}
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Conversation sidebar */}
      <AnimatePresence>
        {(mobileSidebarOpen || true) && (
          <motion.div
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            className={`${
              mobileSidebarOpen
                ? "fixed inset-0 z-30 lg:relative lg:inset-auto"
                : "hidden lg:block"
            } w-72 border-r border-gray-800 bg-[#0A1628] lg:bg-transparent`}
          >
            {/* Mobile close button */}
            {mobileSidebarOpen && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 lg:hidden text-gray-400"
                onClick={() => setMobileSidebarOpen(false)}
                aria-label="Close sidebar"
              >
                <X className="h-5 w-5" />
              </Button>
            )}

            <div className="flex h-full flex-col p-4">
              {limitReached ? (
                <div className="mb-4">
                  <UpgradeBanner feature="unlimited AI tutor sessions" />
                </div>
              ) : (
                <Button
                  onClick={handleNewChat}
                  className="mb-4 w-full bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  New Chat
                </Button>
              )}

              <div className="flex-1 overflow-y-auto">
                {conversationsLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className="h-12 rounded-lg skeleton-shimmer"
                      />
                    ))}
                  </div>
                ) : conversations.length === 0 ? (
                  <div className="flex flex-col items-center py-8 text-center">
                    <div className="mb-3 rounded-full bg-[#1A2942] p-3">
                      <MessageSquare className="h-5 w-5 text-[#00D4AA]" />
                    </div>
                    <p className="text-sm font-medium text-gray-300">
                      No conversations yet
                    </p>
                    <p className="mt-1 text-sm text-gray-500">
                      Start a new chat to get going
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {conversations.map((conv) => (
                      <div
                        key={conv.id}
                        className={`group flex items-center justify-between rounded-lg p-3 cursor-pointer transition-colors ${
                          selectedConversationId === conv.id
                            ? "bg-[#1A2942] text-white"
                            : "text-gray-400 hover:bg-[#1A2942]/50 hover:text-gray-200"
                        }`}
                        onClick={() => handleSelectConversation(conv.id)}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <MessageSquare className="h-4 w-4 shrink-0" />
                          <span className="truncate text-sm">{conv.title}</span>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                              onClick={(e) => e.stopPropagation()}
                              aria-label="Conversation options"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent
                            align="end"
                            className="border-gray-800 bg-[#1F2937]"
                          >
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteMutation.mutate(conv.id);
                              }}
                              className="text-red-400 focus:bg-red-500/10 focus:text-red-400"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Chat area */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-6">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-[#1A2942]">
                  <Bot className="h-8 w-8 text-[#00D4AA]" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">
                  Start a conversation
                </h3>
                <p className="max-w-sm text-base text-gray-400">
                  Ask me anything about investing, markets, or financial concepts.
                  I&apos;m here to help you learn.
                </p>
              </div>
            </div>
          ) : (
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
          )}
        </div>

        {/* Input */}
        {limitReached && !selectedConversationId ? (
          <div className="border-t border-gray-800 p-4">
            <UpgradeBanner feature="unlimited AI tutor sessions" />
          </div>
        ) : (
          <div className="border-t border-gray-800 p-4">
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
                placeholder="Ask about investing, markets, strategies..."
                disabled={isStreaming}
                className="flex-1 border-gray-700 bg-[#1A2942] text-base text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA]"
              />
              <Button
                type="submit"
                disabled={!inputValue.trim() || isStreaming}
                className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-50"
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
    </>
  );
}
