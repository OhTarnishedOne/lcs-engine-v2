/**
 * Shared API types matching backend schemas.
 */

// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

// Profile
export interface UserProfile {
  id: string;
  user_id: string;
  persona: string | null;
  experience_level: string | null;
  biggest_barrier: string | null;
  primary_goal: string | null;
  risk_tolerance: string | null;
  learning_preference: string | null;
  recommended_path: string | null;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

// Onboarding
export interface OnboardingQuestion {
  key: string;
  text: string;
  type: string;
  required: boolean;
  order: number;
  options: OnboardingOption[];
  placeholder: string | null;
  conditional: Record<string, unknown> | null;
}

export interface OnboardingOption {
  value: string;
  label: string;
  emoji?: string;
}

export interface OnboardingSection {
  section: number;
  title: string;
  subtitle: string;
  questions: OnboardingQuestion[];
}

export interface OnboardingQuestionsResponse {
  sections: OnboardingSection[];
  total_questions: number;
}

export interface OnboardingSubmitResult {
  section: number;
  saved_count: number;
  is_complete: boolean;
  next_section: number | null;
}

export interface OnboardingProgress {
  sections_completed: number[];
  current_section: number | null;
  questions_answered: number;
  total_questions: number;
  percent_complete: number;
  is_complete: boolean;
}

export interface PersonalizedTip {
  title: string;
  description: string;
  action?: string;
}

export interface OnboardingWelcome {
  greeting: string;
  acknowledgment: string;
  encouragement: string;
  recommended_action: string;
  recommended_action_label: string;
  recommended_action_description: string;
  personalized_tips: PersonalizedTip[];
  persona: string | null;
  persona_description: string | null;
}

// Chat
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message_preview?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
}

// Strategies
export interface AssetAllocation {
  ticker: string;
  name: string;
  allocation_pct: number;
  rationale: string;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  strategy_type: string;
  risk_level: number;
  time_horizon: string;
  assets: AssetAllocation[];
  rationale: string;
  risks: string;
  learning_points: string[];
  created_at: string;
}

export interface GenerateStrategyRequest {
  strategy_type?: string;
  preferences?: Record<string, unknown>;
}

export interface StrategiesResponse {
  strategies: Strategy[];
  total: number;
}

export interface CompareStrategiesRequest {
  strategy_ids: string[];
}

export interface StrategyComparison {
  id: string;
  strategies: Strategy[];
  comparison_text: string;
  created_at: string;
}

export interface ExplainStrategyRequest {
  question: string;
}

export interface ExplainStrategyResponse {
  strategy_id: string;
  question: string;
  explanation: string;
}

// Trading
export interface Position {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_pl_pct: number;
}

export interface PortfolioResponse {
  equity: number;
  cash: number;
  buying_power: number;
  total_pl: number;
  total_pl_pct: number;
  positions: Position[];
}

export interface PlaceOrderRequest {
  symbol: string;
  qty: number;
  side: "buy" | "sell";
  order_type: "market" | "limit";
  limit_price?: number;
  strategy_id?: string;
  reasoning?: string;
}

export interface Order {
  id: string;
  alpaca_order_id: string | null;
  symbol: string;
  side: string;
  qty: number;
  order_type: string;
  status: string;
  limit_price: number | null;
  filled_price: number | null;
  created_at: string;
}

export interface TradeHistory {
  id: string;
  symbol: string;
  side: string;
  qty: number;
  order_type: string;
  status: string;
  filled_price: number | null;
  strategy_id: string | null;
  reasoning: string | null;
  created_at: string;
}

export interface SymbolSearchResult {
  ticker: string;
  name: string;
  type: string;
}

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

export interface CompanyInfo {
  ticker: string;
  name: string;
  description: string | null;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  homepage_url: string | null;
}

export interface PortfolioHistoryResponse {
  timestamps: string[];
  equity: number[];
  profit_loss: number[];
  profit_loss_pct: number[];
}

// Probability Lab
export interface PredictionMarket {
  id: string;
  title: string;
  description: string | null;
  category: string;
  market_probability: number | null;
  close_date: string;
  is_resolved: boolean;
  resolution: string | null;
  explainer: string | null;
  investing_connection: string | null;
}

export interface MarketsResponse {
  markets: PredictionMarket[];
  total: number;
}

export interface SubmitPredictionRequest {
  market_id: string;
  probability: number;
  reasoning?: string;
}

export interface UserPrediction {
  id: string;
  market_id: string;
  market_title: string;
  predicted_probability: number;
  market_probability: number;
  reasoning: string | null;
  brier_score: number | null;
  is_resolved: boolean;
  resolution: string | null;
  created_at: string;
}

export interface PredictionsResponse {
  predictions: UserPrediction[];
  total: number;
}

export interface CalibrationBucket {
  bucket_start: number;
  bucket_end: number;
  predicted_avg: number;
  actual_rate: number;
  count: number;
}

export interface BiasInfo {
  name: string;
  description: string;
  tip: string;
  investing_connection: string;
}

export interface CalibrationResponse {
  total_predictions: number;
  resolved_predictions: number;
  average_brier_score: number | null;
  calibration_curve: CalibrationBucket[];
  detected_biases: BiasInfo[];
}

// API Error
export interface ApiError {
  detail: string;
}
