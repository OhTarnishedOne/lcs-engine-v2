/**
 * API client with authentication handling.
 * Automatically adds auth headers and handles token refresh.
 */

import type {
  AuthResponse,
  OnboardingSection,
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
  PositionsResponse,
  PlaceOrderRequest,
  Order,
  OrdersResponse,
  TradeHistoryResponse,
  SymbolSearchResult,
  Quote,
  CompanyInfo,
  MarketsResponse,
  PredictionMarket,
  SubmitPredictionRequest,
  UserPrediction,
  PredictionsResponse,
  CalibrationResponse,
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
  // Onboarding API
  // ============================================

  async getOnboardingQuestions(): Promise<OnboardingSection[]> {
    return this.get<OnboardingSection[]>("/onboarding/questions");
  }

  async submitOnboardingResponses(
    section: string,
    responses: Record<string, string>
  ): Promise<OnboardingProgress> {
    return this.post<OnboardingProgress>("/onboarding/responses", {
      section,
      responses,
    });
  }

  async completeOnboarding(): Promise<{ message: string; profile: UserProfile }> {
    return this.post("/onboarding/complete");
  }

  async getOnboardingProgress(): Promise<OnboardingProgress> {
    return this.get<OnboardingProgress>("/onboarding/progress");
  }

  async getProfile(): Promise<UserProfile> {
    return this.get<UserProfile>("/onboarding/profile");
  }

  async getWelcome(): Promise<OnboardingWelcome> {
    return this.get<OnboardingWelcome>("/onboarding/welcome");
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

  async getPositions(): Promise<PositionsResponse> {
    return this.get<PositionsResponse>("/trading/positions");
  }

  async placeOrder(request: PlaceOrderRequest): Promise<Order> {
    return this.post<Order>("/trading/orders", request);
  }

  async getOrders(status?: string): Promise<OrdersResponse> {
    const query = status ? `?status=${status}` : "";
    return this.get<OrdersResponse>(`/trading/orders${query}`);
  }

  async cancelOrder(orderId: string): Promise<{ cancelled: boolean; order_id: string }> {
    return this.delete(`/trading/orders/${orderId}`);
  }

  async getTradeHistory(): Promise<TradeHistoryResponse> {
    return this.get<TradeHistoryResponse>("/trading/history");
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
}

// Singleton instance
export const api = new ApiClient();

// Export API URL for direct use in streaming
export { API_URL };
