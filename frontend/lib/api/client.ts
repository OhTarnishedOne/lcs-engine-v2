/**
 * API client with authentication handling.
 * Automatically adds auth headers and handles token refresh.
 */

import type {
  AuthResponse,
  OnboardingQuestionsResponse,
  OnboardingSubmitResult,
  OnboardingProgress,
  UserProfile,
  OnboardingWelcome,
  ConversationsResponse,
  ConversationDetail,
  StrategiesResponse,
  Strategy,
  GenerateStrategyRequest,
  CompareStrategiesRequest,
  StrategyComparison,
  ExplainStrategyRequest,
  ExplainStrategyResponse,
  PortfolioResponse,
  Position,
  PlaceOrderRequest,
  Order,
  TradeHistory,
  SymbolSearchResult,
  Quote,
  CompanyInfo,
  MarketsResponse,
  PredictionMarket,
  SubmitPredictionRequest,
  UserPrediction,
  PredictionsResponse,
  CalibrationResponse,
  DecisionCalibrationScore,
  DecisionDiagnosis,
  ActiveIntervention,
  CreateDecisionRequest,
  DecisionRecord,
  DecisionListResponse,
  ResolveDecisionRequest,
  DecisionResolveResult,
  CreateReviewRequest,
  ReviewSubmitResult,
  ReviewRecord,
  JournalResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshPromise: Promise<boolean> | null = null;

  constructor() {
    // Load tokens from localStorage on init (client-side only)
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token");
      this.refreshToken = localStorage.getItem("refresh_token");
      // Sync cookie for middleware auth checks
      if (this.accessToken) {
        document.cookie = `access_token=${this.accessToken}; path=/; max-age=604800; SameSite=Lax`;
      }
    }
  }

  /**
   * Set auth tokens after login/register.
   */
  setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
      document.cookie = `access_token=${access}; path=/; max-age=604800; SameSite=Lax`;
    }
  }

  /**
   * Clear auth tokens on logout.
   */
  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      document.cookie = "access_token=; path=/; max-age=0";
    }
  }

  /**
   * Get current access token.
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Check if user is authenticated.
   */
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  /**
   * Refresh the access token using the refresh token.
   */
  async refreshAccessToken(): Promise<boolean> {
    // Deduplicate concurrent refresh requests
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    if (!this.refreshToken) {
      return false;
    }

    this.refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        });

        if (!res.ok) {
          this.clearTokens();
          return false;
        }

        const data: AuthResponse = await res.json();
        this.setTokens(data.access_token, data.refresh_token);
        return true;
      } catch {
        this.clearTokens();
        return false;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  /**
   * Make an authenticated API request.
   */
  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(this.accessToken && { Authorization: `Bearer ${this.accessToken}` }),
      ...options.headers,
    };

    let res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // If unauthorized, try to refresh token and retry
    if (res.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry with new token
        res = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers: {
            ...headers,
            Authorization: `Bearer ${this.accessToken}`,
          },
        });
      }
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || "API request failed");
    }

    return res.json();
  }

  /**
   * GET request.
   */
  async get<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: "GET" });
  }

  /**
   * POST request.
   */
  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT request.
   */
  async put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PATCH request.
   */
  async patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * DELETE request.
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: "DELETE" });
  }

  // ============================================
  // Password Reset API (no auth required)
  // ============================================

  async forgotPassword(email: string): Promise<{ message: string }> {
    return this.post("/auth/forgot-password", { email });
  }

  async resetPassword(token: string, password: string): Promise<{ message: string }> {
    return this.post("/auth/reset-password", { token, password });
  }

  async deleteAccount(password: string): Promise<void> {
    await this.fetch("/auth/me", {
      method: "DELETE",
      body: JSON.stringify({ password }),
    });
  }

  // ============================================
  // Onboarding API
  // ============================================

  async getOnboardingQuestions(): Promise<OnboardingQuestionsResponse> {
    return this.get<OnboardingQuestionsResponse>("/onboarding/questions");
  }

  async submitOnboardingResponses(
    section: number,
    responses: Record<string, string>
  ): Promise<OnboardingSubmitResult> {
    return this.post<OnboardingSubmitResult>("/onboarding/responses", {
      section,
      responses,
    });
  }

  async submitSectionResponses(
    sectionNumber: number,
    responses: Record<string, string>
  ): Promise<OnboardingSubmitResult> {
    return this.post<OnboardingSubmitResult>(`/onboarding/sections/${sectionNumber}`, {
      responses,
    });
  }

  async completeOnboarding(): Promise<{ message: string; profile: unknown }> {
    return this.post("/onboarding/complete");
  }

  async getOnboardingProgress(): Promise<OnboardingProgress> {
    return this.get<OnboardingProgress>("/onboarding/progress");
  }

  async getProfile(): Promise<UserProfile> {
    return this.get<UserProfile>("/onboarding/profile");
  }

  async updateProfile(updates: Partial<Pick<
    import("./types").RawProfile,
    'primary_goal' | 'specific_goal_description' | 'time_horizon' |
    'risk_tolerance' | 'monthly_investable' | 'learning_preference' |
    'time_commitment' | 'interests'
  >>): Promise<UserProfile> {
    return this.patch<UserProfile>("/onboarding/profile", updates);
  }

  async getWelcome(): Promise<OnboardingWelcome> {
    return this.get<OnboardingWelcome>("/onboarding/welcome");
  }

  // ============================================
  // Conversational Onboarding API
  // ============================================

  /**
   * Send messages to the conversational onboarding chat endpoint.
   * Returns a raw Response for SSE streaming (same pattern as sendChatMessage).
   */
  async sendOnboardingChat(
    messages: { role: string; content: string }[],
    tapResponses?: Record<string, string | string[]>
  ): Promise<Response> {
    const body: Record<string, unknown> = { messages };
    if (tapResponses) {
      body.tap_responses = tapResponses;
    }

    const response = await fetch(`${API_URL}/onboarding/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to send onboarding chat");
    }

    return response;
  }

  /**
   * Complete onboarding by extracting profile from conversation transcript.
   */
  async completeOnboardingChat(
    messages: { role: string; content: string }[]
  ): Promise<{ ok: boolean; profile?: Record<string, unknown>; error?: string }> {
    return this.post("/onboarding/chat/complete", { messages });
  }

  /**
   * Complete hybrid onboarding by merging tap responses with conversation data.
   */
  async completeOnboardingConversation(
    tapResponses: Record<string, string | string[]>,
    messages: { role: string; content: string }[]
  ): Promise<{ ok: boolean; profile?: Record<string, unknown>; error?: string }> {
    return this.post("/onboarding/complete-conversation", {
      tap_responses: tapResponses,
      messages,
    });
  }

  /**
   * Save a single tap screen response for persistence across sessions.
   */
  async saveTapResponse(
    key: string,
    value: string | string[]
  ): Promise<{ saved: boolean; completed_screens: number }> {
    return this.post("/onboarding/save-tap-response", { key, value });
  }

  /**
   * Skip onboarding entirely and create profile with defaults.
   */
  async skipOnboarding(): Promise<{ ok: boolean }> {
    return this.post("/onboarding/skip");
  }

  // ============================================
  // Chat API
  // ============================================

  async getConversations(): Promise<ConversationsResponse> {
    return this.get<ConversationsResponse>("/chat/conversations");
  }

  async getConversation(id: string): Promise<ConversationDetail> {
    return this.get<ConversationDetail>(`/chat/conversations/${id}`);
  }

  async deleteConversation(id: string): Promise<{ message: string }> {
    return this.delete(`/chat/conversations/${id}`);
  }

  async renameConversation(id: string, title: string): Promise<{ message: string }> {
    return this.patch(`/chat/conversations/${id}`, { title });
  }

  /**
   * Send a chat message and receive SSE stream.
   * Returns a ReadableStream for processing tokens.
   */
  async sendChatMessage(
    message: string,
    conversationId?: string
  ): Promise<Response> {
    const response = await fetch(`${API_URL}/chat/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to send message");
    }

    return response;
  }

  // ============================================
  // Strategies API
  // ============================================

  async getStrategies(): Promise<StrategiesResponse> {
    return this.get<StrategiesResponse>("/strategies");
  }

  async getStrategy(id: string): Promise<Strategy> {
    return this.get<Strategy>(`/strategies/${id}`);
  }

  async generateStrategy(request?: GenerateStrategyRequest): Promise<Strategy> {
    return this.post<Strategy>("/strategies/generate", request || {});
  }

  async deleteStrategy(id: string): Promise<{ message: string }> {
    return this.delete(`/strategies/${id}`);
  }

  async compareStrategies(request: CompareStrategiesRequest): Promise<StrategyComparison> {
    return this.post<StrategyComparison>("/strategies/compare", request);
  }

  async explainStrategy(
    strategyId: string,
    request: ExplainStrategyRequest
  ): Promise<ExplainStrategyResponse> {
    return this.post<ExplainStrategyResponse>(
      `/strategies/${strategyId}/explain`,
      request
    );
  }

  // ============================================
  // Trading API
  // ============================================

  async getPortfolio(): Promise<PortfolioResponse> {
    return this.get<PortfolioResponse>("/trading/portfolio");
  }

  async getPositions(): Promise<Position[]> {
    return this.get<Position[]>("/trading/positions");
  }

  async placeOrder(request: PlaceOrderRequest): Promise<Order> {
    return this.post<Order>("/trading/orders", request);
  }

  async getOrders(status?: string): Promise<Order[]> {
    const query = status ? `?status=${status}` : "";
    return this.get<Order[]>(`/trading/orders${query}`);
  }

  async cancelOrder(orderId: string): Promise<{ cancelled: boolean; order_id: string }> {
    return this.delete(`/trading/orders/${orderId}`);
  }

  async getTradeHistory(): Promise<TradeHistory[]> {
    return this.get<TradeHistory[]>("/trading/history");
  }

  async searchSymbols(query: string): Promise<SymbolSearchResult[]> {
    return this.get<SymbolSearchResult[]>(`/trading/search?q=${encodeURIComponent(query)}`);
  }

  async getQuote(symbol: string): Promise<Quote> {
    return this.get<Quote>(`/trading/quote/${symbol}`);
  }

  async getCompanyInfo(symbol: string): Promise<CompanyInfo> {
    return this.get<CompanyInfo>(`/trading/company/${symbol}`);
  }

  // ============================================
  // Probability Lab API
  // ============================================

  async getMarkets(): Promise<MarketsResponse> {
    return this.get<MarketsResponse>("/probability/markets");
  }

  async getMarket(id: string): Promise<PredictionMarket> {
    return this.get<PredictionMarket>(`/probability/markets/${id}`);
  }

  async submitPrediction(request: SubmitPredictionRequest): Promise<UserPrediction> {
    return this.post<UserPrediction>("/probability/predictions", request);
  }

  async getPredictions(): Promise<PredictionsResponse> {
    return this.get<PredictionsResponse>("/probability/predictions");
  }

  async getCalibration(): Promise<CalibrationResponse> {
    return this.get<CalibrationResponse>("/probability/calibration");
  }

  async getCalibrationScore(): Promise<{
    overall_score: number | null;
    prediction_count: number;
    resolved_count: number;
    percentile: number | null;
    sub_scores: { category: string; score: number; prediction_count: number }[];
    trend_30d: { date: string; score: number }[];
    is_first_score_view: boolean;
    engine_state: "building" | "active";
    next_action: {
      title: string;
      description: string;
      cta: string;
      href: string;
    };
    engine_insights: {
      type: string;
      title: string;
      description: string;
      severity: "info" | "positive" | "warning";
    }[];
    recent_reviews: {
      market_title: string;
      category: string;
      predicted_probability: number;
      outcome: string;
      brier_score: number;
      decision_score: number;
      verdict: string;
      diagnosis: string;
      created_at: string;
    }[];
  }> {
    return this.get("/auth/me/calibration");
  }

  // ============================================
  // Billing API
  // ============================================

  async createCheckoutSession(): Promise<{ url: string }> {
    return this.post<{ url: string }>("/billing/create-checkout-session");
  }

  async getBillingStatus(): Promise<{ tier: string; is_pro: boolean }> {
    return this.get<{ tier: string; is_pro: boolean }>("/billing/status");
  }

  async createPortalSession(): Promise<{ url: string }> {
    return this.post<{ url: string }>("/billing/portal");
  }

  // ============================================
  // Session Status API
  // ============================================

  async getSessionStatus(): Promise<{
    conversation_count: number;
    limit: number;
    limit_reached: boolean;
    is_pro: boolean;
  }> {
    return this.get("/chat/session-status");
  }

  // ============================================
  // Decision Intelligence API (gamification pipeline)
  // ============================================

  async getDecisionCalibration(): Promise<DecisionCalibrationScore> {
    return this.get<DecisionCalibrationScore>("/gamification/calibration-score");
  }

  async getDecisionDiagnosis(): Promise<DecisionDiagnosis> {
    return this.get<DecisionDiagnosis>("/decisions/diagnosis");
  }

  async createDecision(body: CreateDecisionRequest): Promise<DecisionRecord> {
    return this.post<DecisionRecord>("/decisions", body);
  }

  async getDecisions(status?: string): Promise<DecisionListResponse> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return this.get<DecisionListResponse>(`/decisions${qs}`);
  }

  async getDecisionJournal(): Promise<JournalResponse> {
    return this.get<JournalResponse>("/decisions/journal");
  }

  async resolveDecision(
    id: string,
    body: ResolveDecisionRequest
  ): Promise<DecisionResolveResult> {
    return this.post<DecisionResolveResult>(`/decisions/${id}/resolve`, body);
  }

  async submitReview(
    id: string,
    body: CreateReviewRequest
  ): Promise<ReviewSubmitResult> {
    return this.post<ReviewSubmitResult>(`/decisions/${id}/review`, body);
  }

  async getReview(id: string): Promise<ReviewRecord> {
    return this.get<ReviewRecord>(`/decisions/${id}/review`);
  }

  /**
   * Current active training mission, or null when there is none.
   * `/interventions/active` returns 404 when no mission is active — an
   * expected empty case, not an error — so we degrade to null.
   */
  async getActiveIntervention(): Promise<ActiveIntervention | null> {
    try {
      return await this.get<ActiveIntervention>("/interventions/active");
    } catch {
      return null;
    }
  }
}

// Singleton instance
export const api = new ApiClient();

// Export API URL for direct use in streaming
export { API_URL };
